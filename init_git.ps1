$gitExe = "C:\Users\madea\AppData\Local\Microsoft\WinGet\Packages\Git.MinGit_Microsoft.Winget.Source_8wekyb3d8bbwe\cmd\git.exe"
$gitCmdDir = "C:\Users\madea\AppData\Local\Microsoft\WinGet\Packages\Git.MinGit_Microsoft.Winget.Source_8wekyb3d8bbwe\cmd"

# Add to user PATH permanently
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$gitCmdDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$userPath;$gitCmdDir", "User")
}

Set-Location $PSScriptRoot

& $gitExe init
& $gitExe config user.name "Developer"
& $gitExe config user.email "developer@sports-ai.local"
& $gitExe add .
& $gitExe commit -m "Initial commit: Sports AI Analytics modular architecture"
& $gitExe log --oneline -n 5
