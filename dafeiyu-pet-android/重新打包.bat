@echo off
chcp 65001 >nul
setlocal
set "JAVA_HOME=C:\Program Files\Java\jdk-21"
set "GRADLE=C:\Users\31486\.gradle\wrapper\dists\gradle-8.8-bin\dl7vupf4psengwqhwktix4v1\gradle-8.8\bin\gradle.bat"
set "GH=D:\Users\31486\Documents\deepseek-harness\default-workspace\android-build\gradle-home"

echo 正在打包大肥鱼桌宠...
call "%GRADLE%" -p "%~dp0" -g "%GH%" assembleDebug --console=plain
if errorlevel 1 (
  echo.
  echo 打包失败，把上面的红字发给我。
  pause
  exit /b 1
)

copy /Y "%~dp0app\build\outputs\apk\debug\app-debug.apk" "%~dp0大肥鱼桌宠-最新.apk" >nul
echo.
echo 打包完成：%~dp0大肥鱼桌宠-最新.apk
pause
