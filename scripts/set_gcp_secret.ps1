param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,

    [Parameter(Mandatory = $true)]
    [string]$Name,

    [string]$Value
)

$ErrorActionPreference = "Stop"

if (-not $Value) {
    $secure = Read-Host "Paste value for $Name" -AsSecureString
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try {
        $Value = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
    } finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
    }
}

$tmp = [System.IO.Path]::GetTempFileName()
try {
    [System.IO.File]::WriteAllText($tmp, $Value, [System.Text.Encoding]::UTF8)
    gcloud secrets describe $Name --project $ProjectId 1>$null 2>$null
    if ($LASTEXITCODE -eq 0) {
        gcloud secrets versions add $Name --data-file=$tmp --project $ProjectId
    } else {
        gcloud secrets create $Name --data-file=$tmp --project $ProjectId
    }
} finally {
    if (Test-Path -LiteralPath $tmp) {
        Remove-Item -LiteralPath $tmp -Force
    }
}
