$ErrorActionPreference = 'Stop'

$output = if ($env:DISCOVERY_OUTPUT_PATH) {
    $env:DISCOVERY_OUTPUT_PATH
} else {
    'data\discovered-storage-accounts.json'
}

python -m storage_intelligence.discovery --output $output
if ($LASTEXITCODE -ne 0) {
    throw 'Tenant-wide storage discovery failed.'
}
