$ErrorActionPreference = 'Stop'
$projectDirectory = Split-Path -Parent $PSScriptRoot
Set-Location $projectDirectory
$pythonExecutable = Join-Path $projectDirectory '.venv/Scripts/python.exe'
if (-not (Test-Path $pythonExecutable)) { throw 'Run scripts/setup.ps1 first.' }
if (-not (Test-Path 'frontend/node_modules')) { throw 'Run scripts/setup.ps1 first.' }
# Hidden helper processes; their output is written to ignored log files.
$backendProcess = Start-Process -FilePath $pythonExecutable -ArgumentList '-m','uvicorn','backend.app.main:app','--host','127.0.0.1','--port','8000' -WorkingDirectory $projectDirectory -WindowStyle Hidden -RedirectStandardOutput 'backend/server.log' -RedirectStandardError 'backend/server-error.log' -PassThru
try {
    Start-Sleep -Seconds 2
    if ($backendProcess.HasExited) { throw 'Backend could not start. Check backend/server-error.log (port 8000 may already be in use).' }
    Write-Host 'App: http://localhost:5173 | API docs: http://localhost:8000/docs'
    Write-Host 'Press Ctrl+C to stop. Backend logs: backend/server-error.log'
    Push-Location frontend
    try { npm.cmd run dev -- --port 5173 --strictPort } finally { Pop-Location }
} finally {
    if (-not $backendProcess.HasExited) { Stop-Process -Id $backendProcess.Id }
}
