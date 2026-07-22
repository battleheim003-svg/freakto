[CmdletBinding()]
param([string]$TaskName = "FreaktoPaperCampaign")

$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
try {
    $task = Get-ScheduledTask -TaskName $TaskName
    $info = Get-ScheduledTaskInfo -TaskName $TaskName
    [pscustomobject]@{
        TaskName = $task.TaskName
        TaskState = $task.State
        LastRunTime = $info.LastRunTime
        LastTaskResult = $info.LastTaskResult
    }
} catch {
    [pscustomobject]@{
        TaskName = $TaskName
        TaskState = "UNAVAILABLE"
        LastRunTime = $null
        LastTaskResult = "Task Scheduler status unavailable: $($_.Exception.Message)"
    }
}

& (Join-Path $root ".venv\Scripts\python.exe") -X utf8 -c "import json; from freakto.paper.campaign import campaign_status; print(json.dumps(campaign_status(), ensure_ascii=False, indent=2))"
