<#
.SYNOPSIS
    Registers Windows Scheduled Tasks for the PakMart OneLake upload pipeline.

.DESCRIPTION
    Creates three scheduled tasks:
      1. PakMart-FullLoad       – runs once a week (Sunday 01:00)
      2. PakMart-Incremental    – runs daily (02:00)
      3. PakMart-DimensionsOnly – runs every 6 hours (for master data sync)

    Run this script once from an elevated PowerShell prompt.
    Edit the variables in the CONFIGURATION block before running.

.NOTES
    Requirements:
      - PowerShell 5.1+
      - Windows Task Scheduler
      - Python on PATH
      - .env file configured in the onelake_upload folder
#>

#Requires -RunAsAdministrator

# ── CONFIGURATION ─────────────────────────────────────────────────────────────
$PipelineDir    = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonExe      = "python"          # or full path: "C:\Python311\python.exe"
$LogDir         = Join-Path $PipelineDir "logs"
$TaskAuthor     = "PakMart Pipeline"

# ── Ensure log directory exists ───────────────────────────────────────────────
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null
    Write-Host "[setup] Created log directory: $LogDir"
}

# ── Helper: register one task ─────────────────────────────────────────────────
function Register-PipelineTask {
    param(
        [string]$TaskName,
        [string]$Mode,
        [string]$ExtraArgs = "",
        [string]$TriggerDescription,
        $Trigger
    )

    $LogFile    = Join-Path $LogDir "$TaskName.log"
    $ScriptArgs = "--mode $Mode $ExtraArgs --log-level INFO"
    $Command    = "$PythonExe main.py $ScriptArgs >> `"$LogFile`" 2>&1"

    # Wrap in cmd /c so stdout/stderr redirection works inside the task
    $Action = New-ScheduledTaskAction `
        -Execute  "cmd.exe" `
        -Argument "/c $Command" `
        -WorkingDirectory $PipelineDir

    $Settings = New-ScheduledTaskSettingsSet `
        -ExecutionTimeLimit  (New-TimeSpan -Hours 2) `
        -RestartCount        3 `
        -RestartInterval     (New-TimeSpan -Minutes 5) `
        -StartWhenAvailable

    # Run as SYSTEM so no interactive session is needed
    $Principal = New-ScheduledTaskPrincipal `
        -UserId    "SYSTEM" `
        -LogonType ServiceAccount `
        -RunLevel  Highest

    # Unregister if already exists
    if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "[setup] Removed existing task: $TaskName"
    }

    Register-ScheduledTask `
        -TaskName   $TaskName `
        -Action     $Action `
        -Trigger    $Trigger `
        -Settings   $Settings `
        -Principal  $Principal `
        -Description "PakMart → OneLake: $TriggerDescription" | Out-Null

    Write-Host "[setup] Registered task: $TaskName  ($TriggerDescription)"
}

# ── Task 1: Full load – every Sunday at 01:00 ─────────────────────────────────
$TriggerFull = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At "01:00"
Register-PipelineTask `
    -TaskName           "PakMart-FullLoad" `
    -Mode               "full" `
    -ExtraArgs          "" `
    -TriggerDescription "Full load every Sunday 01:00" `
    -Trigger            $TriggerFull

# ── Task 2: Incremental – every day at 02:00 ──────────────────────────────────
$TriggerIncr = New-ScheduledTaskTrigger -Daily -At "02:00"
Register-PipelineTask `
    -TaskName           "PakMart-Incremental" `
    -Mode               "incremental" `
    -ExtraArgs          "" `
    -TriggerDescription "Incremental load daily 02:00" `
    -Trigger            $TriggerIncr

# ── Task 3: Dimensions only – every 6 hours (master data refresh) ─────────────
$TriggerDim = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Hours 6) `
    -Once -At (Get-Date).Date   # starts today midnight, repeats every 6h
Register-PipelineTask `
    -TaskName           "PakMart-DimensionsOnly" `
    -Mode               "dimensions" `
    -ExtraArgs          "" `
    -TriggerDescription "Dimensions-only refresh every 6 hours" `
    -Trigger            $TriggerDim

Write-Host ""
Write-Host "============================================================"
Write-Host "  Scheduled tasks registered successfully."
Write-Host "  Log files will be written to: $LogDir"
Write-Host "============================================================"
Write-Host ""
Write-Host "  To run a task immediately (for testing):"
Write-Host "    Start-ScheduledTask -TaskName 'PakMart-FullLoad'"
Write-Host "    Start-ScheduledTask -TaskName 'PakMart-Incremental'"
Write-Host "    Start-ScheduledTask -TaskName 'PakMart-DimensionsOnly'"
Write-Host ""
Write-Host "  To view task status:"
Write-Host "    Get-ScheduledTask -TaskName 'PakMart-*' | Select TaskName, State"
Write-Host ""
Write-Host "  To remove all tasks:"
Write-Host "    Get-ScheduledTask -TaskName 'PakMart-*' | Unregister-ScheduledTask -Confirm:`$false"
