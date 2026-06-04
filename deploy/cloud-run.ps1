param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,

    [string]$Region = "us-central1",
    [string]$ServiceName = "google-ads-mcp",
    [string]$ArtifactRepo = "mcp-servers"
)

$ErrorActionPreference = "Stop"

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

$secretMappings = @(
    "MCP_BEARER_TOKEN=MCP_BEARER_TOKEN:latest",
    "GOOGLE_ADS_DEVELOPER_TOKEN=GOOGLE_ADS_DEVELOPER_TOKEN:latest",
    "GOOGLE_ADS_CLIENT_ID=GOOGLE_ADS_CLIENT_ID:latest",
    "GOOGLE_ADS_CLIENT_SECRET=GOOGLE_ADS_CLIENT_SECRET:latest",
    "GOOGLE_ADS_REFRESH_TOKEN=GOOGLE_ADS_REFRESH_TOKEN:latest"
)

gcloud secrets describe GOOGLE_ADS_LOGIN_CUSTOMER_ID 1>$null 2>$null
if ($LASTEXITCODE -eq 0) {
    $secretMappings += "GOOGLE_ADS_LOGIN_CUSTOMER_ID=GOOGLE_ADS_LOGIN_CUSTOMER_ID:latest"
} else {
    Write-Host "Optional secret GOOGLE_ADS_LOGIN_CUSTOMER_ID not found. Deploying without MCC login_customer_id."
}

gcloud run deploy $ServiceName `
    --image $image `
    --region $Region `
    --platform managed `
    --allow-unauthenticated `
    --port 8080 `
    --set-env-vars "GOOGLE_ADS_API_VERSION=v24,GOOGLE_PROJECT_ID=$ProjectId" `
    --set-secrets ($secretMappings -join ",")

gcloud run services describe $ServiceName `
    --region $Region `
    --format "value(status.url)"
