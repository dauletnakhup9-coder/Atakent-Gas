$ErrorActionPreference = 'Stop'
$projectRoot = 'C:\Users\asus\Desktop\Kaz\Atakent-Gas'
$runtimeRoot = 'C:\Users\asus\Desktop\Kaz\.task-runtime'
$pythonPath = 'C:\Users\asus\Desktop\Kaz\2026-09-15\production-ready-telegram-1-1-telegram\work\venv\Scripts\python.exe'
$env:ENVIRONMENT = 'test'
$env:COOKIE_SECURE = 'false'
$env:BOT_API_KEY = 'registry-test-only-service-key-000000000000'
$env:DATABASE_URL = 'postgresql+asyncpg://utility:registry-test-only@127.0.0.1:55433/utility_e2e_registry_verify'
$env:REDIS_URL = 'redis://127.0.0.1:56380/0'
$env:ALLOWED_ORIGINS = 'http://127.0.0.1:58102'
$env:PYTHONPATH = Join-Path $projectRoot 'apps\backend'
$env:UPLOAD_DIR = Join-Path $runtimeRoot 'uploads'
Set-Location $projectRoot
& $pythonPath tests/bootstrap_e2e.py
if ($LASTEXITCODE -ne 0) { throw 'Test bootstrap failed' }
$backendProcess = Start-Process -FilePath $pythonPath -ArgumentList '-m','uvicorn','app.main:app','--host','127.0.0.1','--port','58101' -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $runtimeRoot 'backend.log') -RedirectStandardError (Join-Path $runtimeRoot 'backend-error.log') -PassThru
$env:INTERNAL_API_URL = 'http://127.0.0.1:58101'
$env:NEXT_TELEMETRY_DISABLED = '1'
$frontendRoot = Join-Path $projectRoot 'apps\admin-web'
$frontendProcess = Start-Process -FilePath 'C:\Program Files\nodejs\node.exe' -ArgumentList (Join-Path $frontendRoot 'node_modules\next\dist\bin\next'),'dev','--webpack','--hostname','127.0.0.1','--port','58102' -WorkingDirectory $frontendRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $runtimeRoot 'frontend.log') -RedirectStandardError (Join-Path $runtimeRoot 'frontend-error.log') -PassThru
@{ backend = $backendProcess.Id; frontend = $frontendProcess.Id } | ConvertTo-Json | Set-Content (Join-Path $runtimeRoot 'test-processes.json')
Write-Output "Isolated backend PID: $($backendProcess.Id); frontend PID: $($frontendProcess.Id)"
