$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot
$LogDir = Join-Path $ProjectRoot "build-logs"
New-Item -ItemType Directory -Force $LogDir | Out-Null
$LogFile = Join-Path $LogDir ("build-" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".log")
Start-Transcript -Path $LogFile
try {
    function Find-RealPython {
        $Candidates = @()
        try {
            $FromLauncher = (& py -3.11 -c "import sys; print(sys.executable)" 2>$null | Select-Object -Last 1)
            if ($LASTEXITCODE -eq 0 -and $FromLauncher) { $Candidates += $FromLauncher.Trim() }
        } catch {}
        $Commands = @(Get-Command python.exe -All -ErrorAction SilentlyContinue)
        foreach ($Command in $Commands) {
            if ($Command.Source -and $Command.Source -notlike "*WindowsApps*") { $Candidates += $Command.Source }
        }
        $Candidates += @(
            "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
            "$env:ProgramFiles\Python311\python.exe"
        )
        $Found = Get-ChildItem "$env:LOCALAPPDATA\Programs\Python" -Filter python.exe -Recurse -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -match "Python311" } | Select-Object -First 1
        if ($Found) { $Candidates += $Found.FullName }
        foreach ($Candidate in ($Candidates | Select-Object -Unique)) {
            if ($Candidate -and (Test-Path $Candidate)) {
                & $Candidate -c "import sys; assert sys.version_info[:2] == (3, 11)" 2>$null
                if ($LASTEXITCODE -eq 0) { return $Candidate }
            }
        }
        return $null
    }

    $PythonExe = Find-RealPython
    if (-not $PythonExe) {
        Write-Host "Khong tim thay Python 3.11 that. Dang tu dong cai dat..."
        $Winget = Get-Command winget.exe -ErrorAction SilentlyContinue
        if ($Winget) {
            & $Winget.Source install --id Python.Python.3.11 --exact --source winget --silent --scope user --accept-package-agreements --accept-source-agreements
        }
        $PythonExe = Find-RealPython
    }
    if (-not $PythonExe) {
        Write-Host "Winget khong san sang hoac cai dat that bai. Dang dung bo cai Python chinh thuc..."
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        $PythonInstaller = Join-Path $env:TEMP "blebig-python-3.11.9-amd64.exe"
        Invoke-WebRequest "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe" -OutFile $PythonInstaller -UseBasicParsing
        $Install = Start-Process -FilePath $PythonInstaller -ArgumentList "/quiet InstallAllUsers=0 PrependPath=1 Include_launcher=1 Include_test=0" -Wait -PassThru
        if ($Install.ExitCode -ne 0) { throw "Bo cai Python tra ve ma loi $($Install.ExitCode)." }
        $PythonExe = Find-RealPython
    }
    if (-not $PythonExe) { throw "Khong the cai hoac xac minh Python 3.11." }
    Write-Host "Python: $PythonExe"

    if (-not (Test-Path ".venv\Scripts\python.exe")) {
        & $PythonExe -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw "Khong tao duoc moi truong .venv." }
    }
    $Vpy = ".venv\Scripts\python.exe"
    # pip 24.0 dùng bundle CA riêng theo mặc định. --use-feature=truststore cho phép
    # dùng Windows Certificate Store, cần thiết khi antivirus/proxy kiểm tra HTTPS.
    & $Vpy -m pip install --use-feature=truststore --disable-pip-version-check wheel
    if ($LASTEXITCODE -ne 0) { throw "Khong ket noi duoc PyPI bang kho chung chi Windows." }
    & $Vpy -m pip install --use-feature=truststore --disable-pip-version-check -r requirements.txt -r requirements-build.txt
    if ($LASTEXITCODE -ne 0) { throw "Khong cai duoc thu vien BleBig. Kiem tra antivirus/proxy HTTPS va file log." }
    & $Vpy -m PyInstaller --noconfirm --clean BleBig.spec
    if ($LASTEXITCODE -ne 0) { throw "Dong goi BleBig that bai." }
    & $Vpy -m PyInstaller --noconfirm --clean BleBigUpdater.spec
    if ($LASTEXITCODE -ne 0) { throw "Dong goi BleBigUpdater that bai." }

    function Find-InnoCompiler {
        $Candidates = @(
            "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
            "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
            "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
        )
        $Command = Get-Command ISCC.exe -ErrorAction SilentlyContinue
        if ($Command -and $Command.Source) { $Candidates += $Command.Source }
        $SearchRoots = @(
            "$env:LOCALAPPDATA\Programs",
            "${env:ProgramFiles(x86)}",
            "$env:ProgramFiles"
        )
        foreach ($SearchRoot in $SearchRoots) {
            if (Test-Path $SearchRoot) {
                $Found = Get-ChildItem $SearchRoot -Filter ISCC.exe -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
                if ($Found) { $Candidates += $Found.FullName }
            }
        }
        foreach ($Candidate in ($Candidates | Select-Object -Unique)) {
            if ($Candidate -and (Test-Path $Candidate)) { return $Candidate }
        }
        return $null
    }

    $Iscc = Find-InnoCompiler
    if (-not $Iscc) {
        $Winget = Get-Command winget.exe -ErrorAction SilentlyContinue
        if ($Winget) {
            & $Winget.Source install --id JRSoftware.InnoSetup --exact --source winget --silent --accept-package-agreements --accept-source-agreements
        }
        $Iscc = Find-InnoCompiler
    }
    if (-not $Iscc) {
        Write-Host "Dang tai bo cai Inno Setup chinh thuc..."
        $InnoInstaller = Join-Path $env:TEMP "blebig-innosetup.exe"
        Invoke-WebRequest "https://jrsoftware.org/download.php/is.exe" -OutFile $InnoInstaller -UseBasicParsing
        $InnoInstall = Start-Process -FilePath $InnoInstaller -ArgumentList "/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-" -Wait -PassThru
        if ($InnoInstall.ExitCode -ne 0) { throw "Bo cai Inno Setup tra ve ma loi $($InnoInstall.ExitCode)." }
        $Iscc = Find-InnoCompiler
    }
    if (-not $Iscc) { throw "Khong tim thay ISCC.exe sau khi cai Inno Setup." }
    Write-Host "Inno Setup: $Iscc"
    & $Iscc "installer\BleBig.iss"
    if ($LASTEXITCODE -ne 0) { throw "Tao BleBig-Setup.exe that bai." }
    Write-Host "HOÀN TẤT: $ProjectRoot\release\BleBig-Setup.exe"
}
catch {
    Write-Error $_
    Write-Host "Xem log build tại: $LogFile"
    exit 1
}
finally { Stop-Transcript }
