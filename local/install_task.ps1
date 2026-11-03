param(
    [string]$Time = "03:00",
    [string]$TaskName = "FGODailyBonus"
)

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Split-Path -Parent $here
$pyw  = Join-Path $root ".venv\Scripts\pythonw.exe"
$task = Join-Path $here "daily_task.py"

Write-Output "仓库根目录 : $root"
Write-Output "执行脚本   : $task"

if (-not (Test-Path $pyw))  { throw "找不到 pythonw.exe，请先创建虚拟环境：$pyw" }
if (-not (Test-Path $task)) { throw "找不到 daily_task.py：$task" }
if (-not (Test-Path (Join-Path $here "env.txt"))) {
    Write-Output "警告：local\env.txt 不存在，请先按 env.example 填好凭证"
}

$old = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($old) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Output "已移除旧任务: $TaskName"
}

$action = New-ScheduledTaskAction -Execute $pyw -Argument "`"$task`"" -WorkingDirectory $here
$trigger = New-ScheduledTaskTrigger -Daily -At $Time
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 20)

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
    -Settings $settings -Description "FGODailyBonus 每日自动触发签到" | Out-Null

$info = Get-ScheduledTaskInfo -TaskName $TaskName
Write-Output ""
Write-Output "已注册计划任务: $TaskName"
Write-Output ("  状态    : " + (Get-ScheduledTask -TaskName $TaskName).State)
Write-Output ("  触发时间: 每天 " + $Time)
Write-Output ("  下次运行: " + $info.NextRunTime)
Write-Output ""
Write-Output "改时间：.\install_task.ps1 -Time 07:30"
Write-Output "删除  ：Unregister-ScheduledTask -TaskName $TaskName -Confirm:`$false"
