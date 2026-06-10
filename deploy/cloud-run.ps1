param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,

    [string]$Region = "us-central1",
    [string]$ServiceName = "google-ads-mcp",
    [string]$ArtifactRepo = "mcp-servers",
    [string]$McpMode = "safe_read_only",
    [string]$McpAuthMode = "bearer",
    [string]$GoogleAdsAuthMode = "shared_refresh_token",
    [string]$McpBaseUrl = "",
    [string]$GoogleAdsClientId = "",
    [string]$GoogleAdsLoginCustomerId = "",
    [string]$McpOAuthClientId = "",
    [string]$McpAllowedEmails = "",
    [string]$McpAllowedDomains = "",
    [string]$McpTokenStorage = "local",
    [string]$McpFirestoreDatabase = "",
    [int]$MinInstances = 0,
    [int]$MaxInstances = 1,
    [string]$Memory = "512Mi",
    [string]$Cpu = "1",
    [switch]$McpAllowAllGoogleUsers,
    [switch]$EnableGenericServiceBridge
)

$ErrorActionPreference = "Stop"

if ($McpAuthMode -eq "oauth_proxy" -and -not $McpBaseUrl) {
    throw "-McpBaseUrl is required when -McpAuthMode oauth_proxy."
}
if ($McpAuthMode -eq "oauth_proxy" -and -not $McpOAuthClientId) {
    throw "-McpOAuthClientId is required when -McpAuthMode oauth_proxy."
}
if (
    $McpAuthMode -eq "oauth_proxy" `
    -and -not $McpAllowedEmails `
    -and -not $McpAllowedDomains `
    -and -not ($GoogleAdsAuthMode -eq "per_user_oauth" -and $McpAllowAllGoogleUsers.IsPresent)
) {
    throw "-McpAllowedEmails or -McpAllowedDomains is required when -McpAuthMode oauth_proxy unless -GoogleAdsAuthMode per_user_oauth and -McpAllowAllGoogleUsers are both set."
}
if ($GoogleAdsAuthMode -notin @("shared_refresh_token", "per_user_oauth")) {
    throw "-GoogleAdsAuthMode must be shared_refresh_token or per_user_oauth."
}
if ($McpTokenStorage -notin @("local", "firestore")) {
    throw "-McpTokenStorage must be local or firestore."
}
if ($McpTokenStorage -eq "firestore" -and $McpAuthMode -ne "oauth_proxy") {
    throw "-McpTokenStorage firestore is only supported with -McpAuthMode oauth_proxy."
}

function ConvertTo-GcloudMapArg {
    param([string[]]$Items)
    return "^@^" + ($Items -join "@")
}

function Get-SecretNamesFromMappings {
    param([string[]]$Mappings)
    $names = @()
    foreach ($mapping in $Mappings) {
        $parts = $mapping -split "=", 2
        if ($parts.Count -lt 2) {
            continue
        }
        $secretRef = ($parts[1] -split ":", 2)[0]
        if ($secretRef) {
            $names += $secretRef
        }
    }
    return $names | Select-Object -Unique
}

function Remove-OldSecretVersions {
    param([string[]]$SecretNames)
    foreach ($secretName in ($SecretNames | Select-Object -Unique)) {
        $versions = @(gcloud secrets versions list $secretName `
            --project $ProjectId `
            --filter "state=enabled OR state=disabled" `
            --sort-by "~createTime" `
            --format "value(name)" 2>$null)
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Could not list versions for $secretName. Leaving versions unchanged."
            continue
        }
        foreach ($version in ($versions | Select-Object -Skip 1)) {
            $versionId = ($version -split "/")[-1]
            gcloud secrets versions destroy $versionId `
                --secret $secretName `
                --project $ProjectId `
                --quiet 1>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "Destroyed old active secret version $secretName/$versionId."
            } else {
                Write-Warning "Could not destroy old secret version $secretName/$versionId."
            }
        }
    }
}

function Remove-OldArtifactImages {
    $imagePath = "$Region-docker.pkg.dev/$ProjectId/$ArtifactRepo/$ServiceName"
    $latestVersions = @(gcloud artifacts docker tags list $imagePath `
        --project $ProjectId `
        --filter "tag:latest" `
        --format "value(version)" 2>$null)
    if ($LASTEXITCODE -ne 0 -or $latestVersions.Count -eq 0) {
        Write-Warning "Could not resolve latest Artifact Registry image. Leaving image versions unchanged."
        return
    }
    $latestVersion = $latestVersions[0]
    $imagesJson = gcloud artifacts docker images list $imagePath `
        --project $ProjectId `
        --include-tags `
        --sort-by "~updateTime" `
        --format "json" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Could not list Artifact Registry images. Leaving image versions unchanged."
        return
    }
    $images = @($imagesJson | ConvertFrom-Json)
    foreach ($image in $images) {
        if (-not $image.package -or -not $image.version) {
            continue
        }
        if ($image.version -eq $latestVersion) {
            continue
        }
        $imageRef = "$($image.package)@$($image.version)"
        gcloud artifacts docker images delete $imageRef --delete-tags --quiet 1>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Deleted old Artifact Registry image $imageRef."
        } else {
            Write-Warning "Could not delete old Artifact Registry image $imageRef."
        }
    }
}

gcloud config set project $ProjectId

$services = @(
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
    "secretmanager.googleapis.com",
    "googleads.googleapis.com"
)
if ($McpTokenStorage -eq "firestore") {
    $services += "firestore.googleapis.com"
}
gcloud services enable $services --project $ProjectId

$projectNumber = gcloud projects describe $ProjectId --format "value(projectNumber)"
$serviceAccount = "$projectNumber-compute@developer.gserviceaccount.com"
gcloud projects add-iam-policy-binding $ProjectId `
    --member "serviceAccount:$serviceAccount" `
    --role "roles/secretmanager.secretAccessor" `
    --quiet
if ($McpTokenStorage -eq "firestore") {
    gcloud projects add-iam-policy-binding $ProjectId `
        --member "serviceAccount:$serviceAccount" `
        --role "roles/datastore.user" `
        --quiet
}
Write-Host "Granted Secret Manager access to $serviceAccount. Waiting for IAM propagation..."
Start-Sleep -Seconds 45

gcloud artifacts repositories describe $ArtifactRepo --location $Region 2>$null
if ($LASTEXITCODE -ne 0) {
    gcloud artifacts repositories create $ArtifactRepo `
        --repository-format=docker `
        --location=$Region
}

$image = "$Region-docker.pkg.dev/$ProjectId/$ArtifactRepo/$ServiceName`:latest"
gcloud builds submit --tag $image .

$genericServiceBridge = if ($EnableGenericServiceBridge.IsPresent) { "true" } else { "false" }
$envMappings = @(
    "GOOGLE_ADS_API_VERSION=v24",
    "GOOGLE_PROJECT_ID=$ProjectId",
    "GOOGLE_ADS_AUTH_MODE=$GoogleAdsAuthMode",
    "GOOGLE_ADS_MCP_MODE=$McpMode",
    "GOOGLE_ADS_MCP_AUTH_MODE=$McpAuthMode",
    "GOOGLE_ADS_MCP_TOKEN_STORAGE=$McpTokenStorage",
    "GOOGLE_ADS_MCP_ENABLE_GENERIC_SERVICE_BRIDGE=$genericServiceBridge"
)
if ($McpAuthMode -eq "oauth_proxy") {
    $envMappings += "GOOGLE_ADS_MCP_BASE_URL=$McpBaseUrl"
    $envMappings += "GOOGLE_ADS_MCP_OAUTH_CLIENT_ID=$McpOAuthClientId"
    if ($McpAllowedEmails) {
        $envMappings += "GOOGLE_ADS_MCP_ALLOWED_EMAILS=$McpAllowedEmails"
    }
    if ($McpAllowedDomains) {
        $envMappings += "GOOGLE_ADS_MCP_ALLOWED_DOMAINS=$McpAllowedDomains"
    }
    if ($McpAllowAllGoogleUsers.IsPresent) {
        $envMappings += "GOOGLE_ADS_MCP_ALLOW_ALL_GOOGLE_USERS=true"
    }
    if ($McpFirestoreDatabase) {
        $envMappings += "GOOGLE_ADS_MCP_FIRESTORE_DATABASE=$McpFirestoreDatabase"
    }
}
if ($GoogleAdsClientId -and $GoogleAdsAuthMode -eq "shared_refresh_token") {
    $envMappings += "GOOGLE_ADS_CLIENT_ID=$GoogleAdsClientId"
}
if ($GoogleAdsLoginCustomerId) {
    $envMappings += "GOOGLE_ADS_LOGIN_CUSTOMER_ID=$GoogleAdsLoginCustomerId"
}

$secretMappings = @("GOOGLE_ADS_DEVELOPER_TOKEN=GOOGLE_ADS_DEVELOPER_TOKEN:latest")
if ($GoogleAdsAuthMode -eq "shared_refresh_token") {
    $secretMappings += "GOOGLE_ADS_CLIENT_SECRET=GOOGLE_ADS_CLIENT_SECRET:latest"
    $secretMappings += "GOOGLE_ADS_REFRESH_TOKEN=GOOGLE_ADS_REFRESH_TOKEN:latest"
}
if ($GoogleAdsAuthMode -eq "shared_refresh_token" -and -not $GoogleAdsClientId) {
    $secretMappings += "GOOGLE_ADS_CLIENT_ID=GOOGLE_ADS_CLIENT_ID:latest"
}
if ($McpAuthMode -eq "bearer") {
    $secretMappings += "MCP_BEARER_TOKEN=MCP_BEARER_TOKEN:latest"
}
if ($McpAuthMode -eq "oauth_proxy") {
    $secretMappings += "GOOGLE_ADS_MCP_OAUTH_CLIENT_SECRET=GOOGLE_ADS_MCP_OAUTH_CLIENT_SECRET:latest"
}

if (-not $GoogleAdsLoginCustomerId) {
    Write-Host "Deploying without a default GOOGLE_ADS_LOGIN_CUSTOMER_ID. Child-account calls can auto-resolve or pass login_customer_id per request."
}

$envArg = ConvertTo-GcloudMapArg $envMappings
$secretArg = ConvertTo-GcloudMapArg $secretMappings

gcloud run deploy $ServiceName `
    --image $image `
    --region $Region `
    --platform managed `
    --allow-unauthenticated `
    --port 8080 `
    --min-instances $MinInstances `
    --max-instances $MaxInstances `
    --memory $Memory `
    --cpu $Cpu `
    --cpu-throttling `
    --no-cpu-boost `
    --set-env-vars $envArg `
    --set-secrets $secretArg

Remove-OldSecretVersions (Get-SecretNamesFromMappings $secretMappings)
Remove-OldArtifactImages

gcloud run services describe $ServiceName `
    --region $Region `
    --format "value(status.url)"
