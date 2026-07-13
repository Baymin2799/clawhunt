$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

Set-Location $Root
docker compose up -d postgres redis
docker compose stop backend frontend

Write-Host "Local infra is running:"
docker compose ps postgres redis
