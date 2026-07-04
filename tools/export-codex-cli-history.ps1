param(
    [string]$SessionRoot = (Join-Path $env:USERPROFILE '.codex\sessions'),
    [string]$OutFile = (Join-Path (Get-Location) 'docs\codex-cli-history.md'),
    [int]$MaxSessions = 40,
    [int]$SinceDays = 120,
    [switch]$ProjectOnly,
    [switch]$AllProjects,
    [switch]$IncludeAssistant
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function ConvertTo-PlainText {
    param([object]$Value)

    if ($null -eq $Value) { return '' }
    if ($Value -is [string]) { return $Value }

    $parts = New-Object System.Collections.Generic.List[string]

    if ($Value -is [System.Collections.IEnumerable] -and -not ($Value -is [string])) {
        foreach ($item in $Value) {
            if ($null -eq $item) { continue }
            if ($item -is [string]) {
                $parts.Add($item)
                continue
            }
            $props = $item.PSObject.Properties.Name
            if ($props -contains 'text') { $parts.Add([string]$item.text); continue }
            if ($props -contains 'message') { $parts.Add([string]$item.message); continue }
            if ($props -contains 'content') { $parts.Add((ConvertTo-PlainText $item.content)); continue }
        }
        return (($parts | Where-Object { $_ }) -join "`n")
    }

    $names = $Value.PSObject.Properties.Name
    if ($names -contains 'text') { return [string]$Value.text }
    if ($names -contains 'message') { return [string]$Value.message }
    if ($names -contains 'content') { return ConvertTo-PlainText $Value.content }

    return ''
}

function Limit-Text {
    param([string]$Text, [int]$Max = 1200)
    if ([string]::IsNullOrWhiteSpace($Text)) { return '' }
    $normalized = ($Text -replace "`r`n", "`n").Trim()
    if ($normalized.Length -le $Max) { return $normalized }
    return $normalized.Substring(0, $Max).TrimEnd() + "`n..."
}

function Escape-CodeFence {
    param([string]$Text)
    if ($null -eq $Text) { return '' }
    return $Text -replace '```', '``\`'
}

function Add-UniqueMessage {
    param(
        [System.Collections.Generic.List[string]]$List,
        [string]$Text
    )
    if ([string]::IsNullOrWhiteSpace($Text)) { return }
    if ($List.Count -gt 0 -and $List[$List.Count - 1] -eq $Text) { return }
    $List.Add($Text)
}

function Read-CodexSessionSummary {
    param([System.IO.FileInfo]$File)

    $sessionId = $File.BaseName
    $sessionTimestamp = $null
    $cwd = ''
    $source = ''
    $userMessages = New-Object System.Collections.Generic.List[string]
    $assistantMessages = New-Object System.Collections.Generic.List[string]

    $stream = $null
    $reader = $null
    try {
        $stream = [System.IO.FileStream]::new($File.FullName, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
        $reader = [System.IO.StreamReader]::new($stream, [System.Text.Encoding]::UTF8)
        while (-not $reader.EndOfStream) {
            $line = $reader.ReadLine()
            if ([string]::IsNullOrWhiteSpace($line)) { continue }
            try { $obj = $line | ConvertFrom-Json -ErrorAction Stop } catch { continue }

            if ($null -eq $sessionTimestamp -and $obj.PSObject.Properties.Name -contains 'timestamp') {
                $sessionTimestamp = [string]$obj.timestamp
            }

            $type = if ($obj.PSObject.Properties.Name -contains 'type') { [string]$obj.type } else { '' }
            $payload = if ($obj.PSObject.Properties.Name -contains 'payload') { $obj.payload } else { $null }
            if ($null -eq $payload) { continue }
            $payloadNames = $payload.PSObject.Properties.Name

            if ($type -eq 'session_meta') {
                if ($payloadNames -contains 'id') { $sessionId = [string]$payload.id }
                if ($payloadNames -contains 'cwd') { $cwd = [string]$payload.cwd }
                if ($payloadNames -contains 'source') { $source = [string]$payload.source }
                if ($payloadNames -contains 'timestamp') { $sessionTimestamp = [string]$payload.timestamp }
                continue
            }

            if ($type -eq 'turn_context') {
                if (($payloadNames -contains 'cwd') -and [string]::IsNullOrWhiteSpace($cwd)) { $cwd = [string]$payload.cwd }
                continue
            }

            if ($type -eq 'event_msg') {
                $eventType = if ($payloadNames -contains 'type') { [string]$payload.type } else { '' }
                if ($eventType -eq 'user_message' -and ($payloadNames -contains 'message')) {
                    $text = Limit-Text ([string]$payload.message) 1800
                    Add-UniqueMessage -List $userMessages -Text $text
                }
                elseif ($IncludeAssistant -and ($eventType -in @('agent_message','agent_reasoning')) -and ($payloadNames -contains 'text')) {
                    $text = Limit-Text ([string]$payload.text) 1000
                    Add-UniqueMessage -List $assistantMessages -Text $text
                }
                continue
            }

            if ($type -eq 'response_item') {
                $role = if ($payloadNames -contains 'role') { [string]$payload.role } else { '' }
                $itemType = if ($payloadNames -contains 'type') { [string]$payload.type } else { '' }
                if ($itemType -eq 'message' -and $role -eq 'user' -and ($payloadNames -contains 'content')) {
                    $text = Limit-Text (ConvertTo-PlainText $payload.content) 1800
                    if ($text -and $text -notlike '<environment_context>*') { Add-UniqueMessage -List $userMessages -Text $text }
                }
                elseif ($IncludeAssistant -and $itemType -eq 'message' -and $role -eq 'assistant' -and ($payloadNames -contains 'content')) {
                    $text = Limit-Text (ConvertTo-PlainText $payload.content) 1000
                    Add-UniqueMessage -List $assistantMessages -Text $text
                }
            }
        }
    }
    finally {
        if ($null -ne $reader) { $reader.Dispose() }
        if ($null -ne $stream) { $stream.Dispose() }
    }

    [pscustomobject]@{
        File = $File.FullName
        Id = $sessionId
        Timestamp = $sessionTimestamp
        LastWriteTime = $File.LastWriteTime
        Cwd = $cwd
        Source = $source
        UserMessages = $userMessages
        AssistantMessages = $assistantMessages
    }
}

if (-not (Test-Path -LiteralPath $SessionRoot)) {
    throw "Codex CLI session directory not found: $SessionRoot"
}

if ($ProjectOnly -and $AllProjects) {
    throw 'Use only one of -ProjectOnly or -AllProjects.'
}

$repoRoot = (Get-Location).Path
$outDir = Split-Path -Parent $OutFile
if ($outDir -and -not (Test-Path -LiteralPath $outDir)) {
    New-Item -ItemType Directory -Force -Path $outDir | Out-Null
}

$cutoff = (Get-Date).AddDays(-1 * $SinceDays)
$files = Get-ChildItem -LiteralPath $SessionRoot -Recurse -File -Filter '*.jsonl' |
    Where-Object { $_.LastWriteTime -ge $cutoff } |
    Sort-Object LastWriteTime -Descending

$summaries = New-Object System.Collections.Generic.List[object]
foreach ($file in $files) {
    if ($summaries.Count -ge $MaxSessions) { break }
    $summary = Read-CodexSessionSummary -File $file

    if ($ProjectOnly -and -not $AllProjects) {
        $cwdValue = [string]$summary.Cwd
        if ([string]::IsNullOrWhiteSpace($cwdValue)) { continue }
        $sameProject = $cwdValue.StartsWith($repoRoot, [System.StringComparison]::OrdinalIgnoreCase)
        if (-not $sameProject) { continue }
    }

    if ($summary.UserMessages.Count -eq 0 -and $summary.AssistantMessages.Count -eq 0) { continue }
    $summaries.Add($summary)
}

$lines = New-Object System.Collections.Generic.List[string]
$lines.Add('# Codex CLI History Export')
$lines.Add('')
$lines.Add("Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz')")
$lines.Add('')
$lines.Add('Session root: `' + $SessionRoot + '`')
$lines.Add('Repository root: `' + $repoRoot + '`')
$filterLabel = if ($ProjectOnly) { 'current project only' } elseif ($AllProjects) { 'all projects' } else { 'all recent sessions' }
$lines.Add('Filter: ' + $filterLabel)
$lines.Add("Max sessions: $MaxSessions; since days: $SinceDays")
$lines.Add('')
$lines.Add('> This is a generated, read-only summary for Codex App/CLI continuity. Regenerate it instead of hand-editing.')
$lines.Add('')

if ($summaries.Count -eq 0) {
    $lines.Add('No matching Codex CLI sessions found.')
} else {
    foreach ($s in $summaries) {
        $titleTime = if ($s.Timestamp) { $s.Timestamp } else { $s.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss') }
        $lines.Add("## $titleTime — $($s.Id)")
        $lines.Add('')
        $lines.Add('- CWD: `' + $s.Cwd + '`')
        $lines.Add('- Source: `' + $s.Source + '`')
        $lines.Add('- File: `' + $s.File + '`')
        $lines.Add('')
        $lines.Add('### User prompts')
        $lines.Add('')
        $idx = 0
        foreach ($msg in $s.UserMessages | Select-Object -First 6) {
            $idx++
            $lines.Add("#### Prompt $idx")
            $lines.Add('')
            $lines.Add('```text')
            $lines.Add((Escape-CodeFence $msg))
            $lines.Add('```')
            $lines.Add('')
        }
        if ($IncludeAssistant -and $s.AssistantMessages.Count -gt 0) {
            $lines.Add('### Assistant excerpts')
            $lines.Add('')
            $aidx = 0
            foreach ($msg in $s.AssistantMessages | Select-Object -First 4) {
                $aidx++
                $lines.Add("#### Assistant excerpt $aidx")
                $lines.Add('')
                $lines.Add('```text')
                $lines.Add((Escape-CodeFence $msg))
                $lines.Add('```')
                $lines.Add('')
            }
        }
    }
}

[System.IO.File]::WriteAllText((Resolve-Path -LiteralPath $outDir).Path + [System.IO.Path]::DirectorySeparatorChar + (Split-Path -Leaf $OutFile), ($lines -join "`r`n"), [System.Text.UTF8Encoding]::new($true))
Write-Host "Exported $($summaries.Count) Codex CLI session summaries to $OutFile"
