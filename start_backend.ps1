$port = 8000
$process = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue

if ($process) {
    echo "Killing process on port $port..."
    Stop-Process -Id $process.OwningProcess -Force
    Start-Sleep -Seconds 1
}

echo "Starting Adorix Backend..."
$env:PYTHONPATH = "$PWD"
python backend/main.py
