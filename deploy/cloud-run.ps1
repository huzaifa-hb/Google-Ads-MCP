param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,

    [string]$Region = "us-central1",
    [string]$ServiceName = "google-ads-mcp",
    [string]$ArtifactRepo = "mcp-servers",
    [string]$McpMode = "safe_read_only",
    [string]$McpAuthMode = "bearer",
    [string]$McpBaseUrl = "",
    [string]$GoogleAdsClientId = "",
    [string]$GoogleAdsLoginCustomerId = "",
    [string]$McpOAuthClientId = "",
    [string]$McpAllowedDomains = "",
    [int]$MinInstances = 0,
    [int]$MaxInstances = 1,
    [string]$Memory = "512Mi",
    [string]$Cpu = "1",
    [switch]$EnableGenericServiceBridge
)

$ErrorActionPreference = "Stop"

if ($McpAuthMode -eq "oauth_proxy" -and -not $McpBaseUrl) {
    throw "-McpBaseUrl is required when -McpAuthMode oauth_proxy."
}
if ($McpAuthMode -eq "oauth_proxy" -and -not $McpOAuthClientId) {
    throw "-McpOAuthClientId is required when -McpAuthMode oauth_proxy."
}
if ($McpAuthMode -eq "oauth_proxy" -and -not $McpAllowedDomains) {
    throw "-McpAllowedDomains is required when -McpAuthMode oauth_proxy."
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
    $imagesJson = gcloud artifacts docker images list $imagePath `
        --sort-by "~updateTime" `
        --format "json" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Could not list Artifact Registry images. Leaving image versions unchanged."
        return
    }
    $images = @($imagesJson | ConvertFrom-Json)
    foreach ($image in ($images | Select-Object -Skip 1)) {
        if (-not $image.package -or -not $image.version) {
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

gcloud services enable `
    run.googleapis.com `
    cloudbuild.googleapis.com `
    artifactregistry.googleapis.com `
    secretmanager.googleapis.com `
    googleads.googleapis.com

$projectNumber = gcloud projects describe $ProjectId --format "value(projectNumber)"
$serviceAccount = "$projectNumber-compute@developer.gserviceaccount.com"
gcloud projects add-iam-policy-binding $ProjectId `
    --member "serviceAccount:$serviceAccount" `
    --role "roles/secretmanager.secretAccessor" `
    --quiet
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
    "GOOGLE_ADS_MCP_MODE=$McpMode",
    "GOOGLE_ADS_MCP_AUTH_MODE=$McpAuthMode",
    "GOOGLE_ADS_MCP_ENABLE_GENERIC_SERVICE_BRIDGE=$genericServiceBridge"
)
if ($McpAuthMode -eq "oauth_proxy") {
    $envMappings += "GOOGLE_ADS_MCP_BASE_URL=$McpBaseUrl"
    $envMappings += "GOOGLE_ADS_MCP_OAUTH_CLIENT_ID=$McpOAuthClientId"
    $envMappings += "GOOGLE_ADS_MCP_ALLOWED_DOMAINS=$McpAllowedDomains"
}
if ($GoogleAdsClientId) {
    $envMappings += "GOOGLE_ADS_CLIENT_ID=$GoogleAdsClientId"
}
if ($GoogleAdsLoginCustomerId) {
    $envMappings += "GOOGLE_ADS_LOGIN_CUSTOMER_ID=$GoogleAdsLoginCustomerId"
}

$secretMappings = @(
    "GOOGLE_ADS_DEVELOPER_TOKEN=GOOGLE_ADS_DEVELOPER_TOKEN:latest",
    "GOOGLE_ADS_CLIENT_SECRET=GOOGLE_ADS_CLIENT_SECRET:latest",
    "GOOGLE_ADS_REFRESH_TOKEN=GOOGLE_ADS_REFRESH_TOKEN:latest"
)
if (-not $GoogleAdsClientId) {
    $secretMappings += "GOOGLE_ADS_CLIENT_ID=GOOGLE_ADS_CLIENT_ID:latest"
}
if ($McpAuthMode -eq "bearer") {
    $secretMappings += "MCP_BEARER_TOKEN=MCP_BEARER_TOKEN:latest"
}
if ($McpAuthMode -eq "oauth_proxy") {
    $secretMappings += "GOOGLE_ADS_MCP_OAUTH_CLIENT_SECRET=GOOGLE_ADS_MCP_OAUTH_CLIENT_SECRET:latest"
}

gcloud secrets describe GOOGLE_ADS_LOGIN_CUSTOMER_ID 1>$null 2>$null
if ($LASTEXITCODE -eq 0 -and -not $GoogleAdsLoginCustomerId) {
    $secretMappings += "GOOGLE_ADS_LOGIN_CUSTOMER_ID=GOOGLE_ADS_LOGIN_CUSTOMER_ID:latest"
} elseif (-not $GoogleAdsLoginCustomerId) {
    Write-Host "Optional secret GOOGLE_ADS_LOGIN_CUSTOMER_ID not found. Deploying without MCC login_customer_id."
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
