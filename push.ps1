# 把本地仓库推到 GitHub（wnagchangyu/Jason）
# 用法：右键本文件 →「使用 PowerShell 运行」，或在 PowerShell 里执行 .\push.ps1
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)

$user = 'wnagchangyu'
$name = 'Jason'
$url  = "https://github.com/$user/$name.git"

Write-Host "目标仓库：$url" -ForegroundColor Cyan

git remote remove origin 2>$null | Out-Null
git remote add origin $url

Write-Host '开始推送（如果弹浏览器，登录后会自动继续）...' -ForegroundColor Yellow
git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ''
    Write-Host "搞定：https://github.com/$user/$name" -ForegroundColor Green
} else {
    Write-Host ''
    Write-Host '推送失败，把上面的红字发给 AI 看看。' -ForegroundColor Red
}
