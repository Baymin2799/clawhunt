$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$PythonExe = Join-Path $Root "backend\.venv\Scripts\python.exe"
$EnvFile = Join-Path $Root ".env.local"

if (-not (Test-Path $PythonExe)) {
    throw "Backend virtual environment not found. Run scripts\Install-LocalDev.ps1 first."
}

if (Test-Path $EnvFile) {
    Get-Content -LiteralPath $EnvFile | ForEach-Object {
        $Line = $_.Trim()
        if ($Line -eq "" -or $Line.StartsWith("#")) {
            return
        }

        $Parts = $Line -split "=", 2
        if ($Parts.Length -eq 2) {
            [Environment]::SetEnvironmentVariable($Parts[0], $Parts[1], "Process")
        }
    }
}

Set-Location (Join-Path $Root "backend")
& $PythonExe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
