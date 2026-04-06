param(
    [switch]$Source,
    [string]$InputHtml,
    [string]$OutputPdf,
    [string]$BrowserPath
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $root ".venv\Scripts\python.exe"
$exporter = Join-Path $root "export_pdf_with_mathjax.py"

if (-not (Test-Path $python)) {
    throw "Python venv executable not found: $python"
}
if (-not (Test-Path $exporter)) {
    throw "Exporter script not found: $exporter"
}

if (-not $InputHtml) {
    if ($Source) {
        $InputHtml = Join-Path $root "Python_for_Introductory_Statistics_V2.html"
    }
    else {
        $InputHtml = Join-Path $root "Python_for_Introductory_Statistics_V2_published.html"
    }
}

if (-not $OutputPdf) {
    if ($Source) {
        $OutputPdf = Join-Path $root "Python_for_Introductory_Statistics_V2_mathfixed.pdf"
    }
    else {
        $OutputPdf = Join-Path $root "Python_for_Introductory_Statistics_V2_published_mathfixed.pdf"
    }
}

if (-not (Test-Path $InputHtml)) {
    throw "Input HTML not found: $InputHtml"
}

if (-not $BrowserPath) {
    $candidates = @(
        "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        "C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        "C:\Program Files\Google\Chrome\Application\chrome.exe"
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            $BrowserPath = $candidate
            break
        }
    }
}

if (-not $BrowserPath) {
    throw "Could not auto-detect Edge/Chrome. Pass -BrowserPath explicitly."
}

Write-Host "Using browser:" $BrowserPath
Write-Host "Input HTML   :" $InputHtml
Write-Host "Output PDF   :" $OutputPdf

& $python $exporter $InputHtml $OutputPdf --browser-path $BrowserPath

if (-not (Test-Path $OutputPdf)) {
    throw "PDF was not created: $OutputPdf"
}

$file = Get-Item $OutputPdf
Write-Host "Done. Created:" $file.FullName
Write-Host "Size (bytes):" $file.Length
Write-Host "Modified    :" $file.LastWriteTime
