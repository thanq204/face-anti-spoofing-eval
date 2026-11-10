param(
    [Parameter(Mandatory = $true)]
    [string] $Source,
    [switch] $IncludeKeras,
    [switch] $Force
)

$ErrorActionPreference = 'Stop'
$sourceRoot = (Resolve-Path -LiteralPath $Source).Path
$repoRoot = Split-Path -Parent $PSScriptRoot
$files = @('web_models/liveness.tflite', 'web_models/liveness_cam4k.tflite')
if ($IncludeKeras) {
    $files += @('liveness.h5', 'liveness_cam4k.h5', 'le.pickle', 'le_cam4k.pickle')
}

$copies = foreach ($name in $files) {
    $from = Join-Path $sourceRoot $name
    $to = Join-Path $repoRoot $name
    if (-not (Test-Path -LiteralPath $from -PathType Leaf)) {
        throw "Missing source artifact: $name"
    }
    if (Test-Path -LiteralPath $to -PathType Leaf) {
        if ((Get-FileHash -LiteralPath $from).Hash -eq (Get-FileHash -LiteralPath $to).Hash) {
            continue
        }
        if (-not $Force) {
            throw "Different artifact already exists: $name. Use -Force to replace it."
        }
    }
    [pscustomobject]@{ From = $from; To = $to; Name = $name }
}

foreach ($file in $copies) {
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $file.To) | Out-Null
    Copy-Item -LiteralPath $file.From -Destination $file.To -Force
    Write-Output "Installed local model artifact: $($file.Name)"
}
Write-Output 'Local model artifacts are ready.'
