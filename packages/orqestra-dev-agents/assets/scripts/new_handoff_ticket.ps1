param(
	[Parameter(Mandatory = $true)]
	[string]$From,

	[Parameter(Mandatory = $true)]
	[string]$To,

	[Parameter(Mandatory = $true)]
	[string]$Epic,

	[ValidateSet("P0", "P1", "P2")]
	[string]$Priority = "P1"
)

$repoRoot = Split-Path -Parent $PSScriptRoot
$templatePath = Join-Path $repoRoot "templates/handoff-ticket.template.md"
$outDir = Join-Path $repoRoot "agents/contracts/tickets"

if (-not (Test-Path $templatePath)) {
	throw "Template not found at $templatePath"
}

if (-not (Test-Path $outDir)) {
	New-Item -ItemType Directory -Path $outDir | Out-Null
}

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$ticketId = "T-$stamp"
$outPath = Join-Path $outDir "$ticketId-$($To.ToLower()).md"

$content = Get-Content -Raw -Path $templatePath
$content = $content.Replace("<TICKET_ID>", $ticketId)
$content = $content.Replace("<AGENT_NAME>", $From)
$content = $content.Replace("<P0|P1|P2>", $Priority)
$content = $content.Replace("<DATE/TIME>", (Get-Date).ToString("yyyy-MM-dd HH:mm:ss"))
$content = $content.Replace("<EPIC_NAME>", $Epic)

# Replace the first agent placeholder occurrence with the target agent name.
$content = $content -replace [regex]::Escape("- To: $From"), "- To: $To"

Set-Content -Path $outPath -Value $content -Encoding UTF8

Write-Output "Created handoff ticket: $outPath"
