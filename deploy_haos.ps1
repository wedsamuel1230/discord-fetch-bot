param(
    [string]$HostName = "root@homeassistant.local",
    [string]$LocalPath = "D:\projects\dc-bot\fetch",
    [string]$RemotePath = "/mnt/data/supervisor/share/dc-bot",
    [string]$ImageTag = "discord-bot"
)

$ErrorActionPreference = "Stop"

function Assert-LastExitCode {
    param(
        [string]$Step
    )
    if ($LASTEXITCODE -ne 0) {
        throw "$Step failed with exit code $LASTEXITCODE"
    }
}

Write-Host "[1/6] Create remote directories..."
ssh $HostName "mkdir -p $RemotePath/data"
Assert-LastExitCode "Step 1 (mkdir)"

Write-Host "[2/6] Upload project files..."
scp -P 22 -r "$LocalPath\*" "${HostName}:$RemotePath/"
Assert-LastExitCode "Step 2a (scp project files)"
scp -P 22 "$LocalPath\.env" "${HostName}:$RemotePath/.env"
Assert-LastExitCode "Step 2b (scp .env)"

Write-Host "[3/6] Build Docker image on HAOS host..."
ssh $HostName "cd $RemotePath; docker build --pull -t $ImageTag ."
Assert-LastExitCode "Step 3 (docker build)"

Write-Host "[4/6] Restart container..."
ssh $HostName "docker rm -f discord-bot 2>/dev/null || true; docker run -d --name discord-bot --restart unless-stopped -v $RemotePath/data:/app/data --env-file $RemotePath/.env $ImageTag"
Assert-LastExitCode "Step 4 (docker run)"

Write-Host "[5/6] Verify running container..."
ssh $HostName "docker ps --filter name=discord-bot"
Assert-LastExitCode "Step 5 (docker ps)"

Write-Host "[6/6] Tail recent logs..."
ssh $HostName "docker logs --tail=120 discord-bot"
Assert-LastExitCode "Step 6 (docker logs)"

Write-Host "Deployment complete."
