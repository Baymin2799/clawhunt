$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$ToolsDir = Join-Path $Root ".tools"
$CacheDir = Join-Path $ToolsDir "cache"
$NodeVersion = "22.23.1"
$NodeArchiveName = "node-v$NodeVersion-win-x64"
$NodeDir = Join-Path $ToolsDir $NodeArchiveName
$NodeZip = Join-Path $CacheDir "$NodeArchiveName.zip"
$PythonVersion = "3.12.13"
$VenvDir = Join-Path $Root "backend\.venv"

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)]
        [scriptblock] $Command
    )

    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code $LASTEXITCODE"
    }
}

New-Item -ItemType Directory -Force -Path $ToolsDir, $CacheDir | Out-Null

if (-not (Test-Path (Join-Path $NodeDir "node.exe"))) {
    $NodeUrl = "https://nodejs.org/dist/v$NodeVersion/$NodeArchiveName.zip"
    Write-Host "Downloading Node.js $NodeVersion..."
    Invoke-WebRequest -Uri $NodeUrl -OutFile $NodeZip
    Write-Host "Extracting Node.js $NodeVersion..."
    Expand-Archive -LiteralPath $NodeZip -DestinationPath $ToolsDir -Force
}

$env:Path = "$NodeDir;$env:Path"

Write-Host "Installing Python $PythonVersion with uv..."
Invoke-Checked { uv python install $PythonVersion }

Write-Host "Creating backend virtual environment..."
if (-not (Test-Path (Join-Path $VenvDir "Scripts\python.exe"))) {
    Invoke-Checked { uv venv $VenvDir --python $PythonVersion }
}
else {
    Write-Host "Backend virtual environment already exists."
}
$PythonExe = Join-Path $VenvDir "Scripts\python.exe"

Write-Host "Installing backend dependencies..."
Invoke-Checked { uv pip install --python $PythonExe "pip==25.0.1" }
Invoke-Checked { uv pip install --python $PythonExe -r (Join-Path $Root "backend\requirements.txt") }

Write-Host "Installing frontend dependencies..."
Push-Location (Join-Path $Root "clawhunt")
try {
    Invoke-Checked { npm ci }
}
finally {
    Pop-Location
}

Write-Host ""
Write-Host "Local development environment installed."
Write-Host "Node:   $(& (Join-Path $NodeDir "node.exe") --version)"
Write-Host "npm:    $(& (Join-Path $NodeDir "npm.cmd") --version)"
Write-Host "Python: $(& $PythonExe --version)"
Write-Host "pip:    $(& $PythonExe -m pip --version)"
