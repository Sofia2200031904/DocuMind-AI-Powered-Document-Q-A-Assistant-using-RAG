# Start the project-local Ollama runtime without opening another terminal window.
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$runtime = Join-Path $projectRoot '.local/ollama/ollama.exe'
if (-not (Test-Path -LiteralPath $runtime)) {
    throw 'Portable Ollama is missing. See docs/phase-2.md for setup instructions.'
}
$env:OLLAMA_HOST = '127.0.0.1:11434'
$env:OLLAMA_MODELS = Join-Path $projectRoot '.local/models'
try {
    $null = Invoke-RestMethod 'http://127.0.0.1:11434/api/tags' -TimeoutSec 2
    Write-Output 'Ollama is already running on port 11434.'
    return
} catch { }
$server = Start-Process -FilePath $runtime -ArgumentList 'serve' -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput (Join-Path $projectRoot '.local/ollama.stdout.log') `
    -RedirectStandardError (Join-Path $projectRoot '.local/ollama.stderr.log')
for ($attempt = 0; $attempt -lt 20; $attempt++) {
    Start-Sleep -Milliseconds 500
    if ($server.HasExited) { throw 'Ollama exited. Check .local/ollama.stderr.log.' }
    try {
        $null = Invoke-RestMethod 'http://127.0.0.1:11434/api/tags' -TimeoutSec 1
        Write-Output "Ollama is ready on localhost:11434 (process $($server.Id))."
        return
    } catch { }
}
throw 'Ollama is still starting. Check .local/ollama.stderr.log.'
