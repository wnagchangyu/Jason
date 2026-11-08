# 创建「大肥鱼桌宠」快捷方式（可选：加 -Startup 参数则同时设为开机自启）
# 用法：右键本文件 →「使用 PowerShell 运行」
param([switch]$Startup)

$ErrorActionPreference = 'Stop'
$base = Split-Path -Parent $MyInvocation.MyCommand.Path
$icon = Join-Path $base 'assets\icon.ico'
$script = Join-Path $base 'pet.py'

# 找一个可用的 pythonw（无控制台窗口）
$cands = @(
    'D:\dsh-home\dsh-runtimes\dsh-primary-runtime\dependencies\python\pythonw.exe',
    (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python313\pythonw.exe'),
    (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\pythonw.exe'),
    (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python311\pythonw.exe'),
    'C:\Python313\pythonw.exe',
    'C:\Python312\pythonw.exe'
)
$py = $cands | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $py) {
    $cmd = Get-Command pythonw.exe -ErrorAction SilentlyContinue
    if ($cmd) { $py = $cmd.Source }
}
if (-not $py) {
    Write-Host '没找到 pythonw.exe。请安装 Python 3，或把 pythonw.exe 的完整路径填进本脚本的 $cands。' -ForegroundColor Yellow
    exit 1
}

$ws = New-Object -ComObject WScript.Shell

function New-PetShortcut([string]$dir) {
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    $lnk = Join-Path $dir '大肥鱼桌宠.lnk'
    $sc = $ws.CreateShortcut($lnk)
    $sc.TargetPath = $py
    $sc.Arguments = '"' + $script + '"'
    $sc.WorkingDirectory = $base
    $sc.IconLocation = $icon
    $sc.Description = '大肥鱼桌宠 · 点一下叫她出来'
    $sc.WindowStyle = 7
    $sc.Save()
    Write-Host "已创建：$lnk"
}

New-PetShortcut $base
New-PetShortcut ([Environment]::GetFolderPath('Desktop'))

if ($Startup) {
    New-PetShortcut ([Environment]::GetFolderPath('Startup'))
    Write-Host '已设为开机自启。'
}

Write-Host ''
Write-Host '完成！双击桌面或本文件夹里的「大肥鱼桌宠」即可。' -ForegroundColor Green
