$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$NodeDir = Join-Path $Root ".tools\node-v22.23.1-win-x64"

if (-not (Test-Path (Join-Path $NodeDir "node.exe"))) {
    throw "Local Node.js not found. Run scripts\Install-LocalDev.ps1 first."
}

$env:Path = "$NodeDir;$env:Path"

Set-Location (Join-Path $Root "clawhunt")
npm run dev
