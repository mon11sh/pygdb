# ================================================================
# GDB - Set up every microservice venv (PowerShell, with ACTIVATION)
#
# For each backend service, this does exactly:
#   1. venv not created  -> create it
#   2. ACTIVATE the venv
#   3. check if requirements.txt is already installed
#         satisfied     -> skip
#         not satisfied -> pip install (only what's missing)
#   4. DEACTIVATE before moving to the next service
# Frontend: npm install only if node_modules is missing.
#
# Run from the gdb-service folder:
#     .\setup_venvs.ps1
#     .\setup_venvs.ps1 -Force     # reinstall even if already satisfied
#
# If activation is blocked, first run (only affects this window):
#     Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
# ================================================================

param([switch]$Force)

$ErrorActionPreference = "Continue"
$root = $PSScriptRoot

$services = @(
    "accounts_service", "transactions_service", "users_service", "auth_service",
    "aadhar_service", "company_crv_service", "notification_service",
    "central_payment_gateway_service",
    "registry_service", "central_gateway_service"   # microservice-pattern services
)

Write-Host "==============================================================="
Write-Host " GDB - venvs + requirements (with activation per service)"
Write-Host "==============================================================="

foreach ($svc in $services) {
    $svcPath  = Join-Path $root $svc
    $req      = Join-Path $svcPath "requirements.txt"
    $venv     = Join-Path $svcPath "venv"
    $venvPy   = Join-Path $venv "Scripts\python.exe"
    $activate = Join-Path $venv "Scripts\Activate.ps1"

    if (-not (Test-Path $req)) { Write-Host "[skip] $svc (no requirements.txt)"; continue }

    # 1) CREATE the venv if it does not exist yet
    if (-not (Test-Path $venvPy)) {
        Write-Host ""
        Write-Host "[$svc] creating virtual environment ..."
        python -m venv $venv
    }

    # 2) ACTIVATE this service's venv (now 'python'/'pip' point at it)
    & $activate

    # 3) CHECK, then install only if needed
    python "$root\check_requirements.py" $req | Out-Null
    $satisfied = ($LASTEXITCODE -eq 0)

    if ($satisfied -and -not $Force) {
        Write-Host "[$svc] requirements already installed - skipping"
    } else {
        if ($Force) { Write-Host "[$svc] installing requirements (forced) ..." }
        else        { Write-Host "[$svc] installing missing requirements ..." }
        python "$root\check_requirements.py" $req   # show what's missing
        python -m pip install --upgrade pip --quiet
        python -m pip install -r $req
        Write-Host "[$svc] ready"
    }

    # 4) DEACTIVATE before the next service
    if (Get-Command deactivate -ErrorAction SilentlyContinue) { deactivate }
}

# ---- Frontend (Node, not Python - no venv) ----
$frontend = Join-Path $root "frontend"
if (Test-Path (Join-Path $frontend "package.json")) {
    if ((Test-Path (Join-Path $frontend "node_modules")) -and -not $Force) {
        Write-Host ""
        Write-Host "[frontend] node_modules present - skipping"
    } else {
        Write-Host ""
        Write-Host "[frontend] npm install ..."
        Push-Location $frontend
        npm install
        Pop-Location
    }
}

Write-Host ""
Write-Host "==============================================================="
Write-Host " Done. Next:  python run_all.py"
Write-Host "==============================================================="
