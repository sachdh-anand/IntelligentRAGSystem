# Enhanced Windows PowerShell run script with full process management
Write-Host "Starting Intelligent RAG System with Process Management..." -ForegroundColor Green
Write-Host "=" * 60

# Function to check running Ollama processes
function Get-OllamaProcesses {
    return Get-Process -Name "ollama" -ErrorAction SilentlyContinue
}

# Function to stop Ollama processes
function Stop-OllamaProcesses {
    $processes = Get-OllamaProcesses
    if ($processes) {
        Write-Host "Found running Ollama processes:" -ForegroundColor Yellow
        foreach ($proc in $processes) {
            Write-Host "   • PID: $($proc.Id) | CPU: $($proc.CPU) | Memory: $([math]::Round($proc.WorkingSet64/1MB, 1))MB" -ForegroundColor Cyan
        }
        
        Write-Host "Stopping all Ollama processes..." -ForegroundColor Yellow
        try {
            Stop-Process -Name "ollama" -Force -ErrorAction Stop
            Start-Sleep 2
            
            # Verify they're stopped
            $remainingProcesses = Get-OllamaProcesses
            if ($remainingProcesses) {
                Write-Host "Some processes still running. Force killing..." -ForegroundColor Red
                $remainingProcesses | Stop-Process -Force
                Start-Sleep 1
            }
            
            Write-Host "All Ollama processes stopped" -ForegroundColor Green
        }
        catch {
            Write-Host "Error stopping processes: $($_.Exception.Message)" -ForegroundColor Red
            exit 1
        }
    }
    else {
        Write-Host "No Ollama processes currently running" -ForegroundColor Blue
    }
}

# Function to start Ollama service
function Start-OllamaService {
    Write-Host "Starting fresh Ollama service..." -ForegroundColor Green
    
    try {
        # Start Ollama serve in background
        $ollamaProcess = Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden -PassThru
        Write-Host "   • Started Ollama service (PID: $($ollamaProcess.Id))" -ForegroundColor Cyan
        
        # Wait for service to be ready
        Write-Host "Waiting for Ollama service to initialize..." -ForegroundColor Yellow
        $maxAttempts = 10
        $attempt = 0
        
        do {
            Start-Sleep 2
            $attempt++
            Write-Host "   • Attempt $attempt/$maxAttempts..." -ForegroundColor Gray
            
            try {
                $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -UseBasicParsing -TimeoutSec 3
                Write-Host "Ollama service is ready!" -ForegroundColor Green
                return $true
            }
            catch {
                # Continue waiting
            }
        } while ($attempt -lt $maxAttempts)
        
        Write-Host "Ollama service failed to start after $maxAttempts attempts" -ForegroundColor Red
        return $false
    }
    catch {
        Write-Host "Error starting Ollama: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Function to display system status
function Show-SystemStatus {
    Write-Host ""
    Write-Host "System Status Report:" -ForegroundColor Cyan
    Write-Host "-" * 40
    
    # Ollama processes
    $processes = Get-OllamaProcesses
    if ($processes) {
        Write-Host "Ollama Processes: $($processes.Count) running" -ForegroundColor Green
        foreach ($proc in $processes) {
            $uptime = (Get-Date) - $proc.StartTime
            Write-Host "   • PID $($proc.Id): Running for $([math]::Round($uptime.TotalMinutes, 1)) minutes" -ForegroundColor Gray
        }
    }
    else {
        Write-Host "Ollama Processes: None" -ForegroundColor Red
    }
    
    # Check service endpoint
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -UseBasicParsing -TimeoutSec 3
        Write-Host "Ollama API: Responsive" -ForegroundColor Green
    }
    catch {
        Write-Host "Ollama API: Not responding" -ForegroundColor Red
    }
    
    Write-Host ""
}

# Function to display detailed model information
function Show-ModelStatus {
    Write-Host "Ollama Models Status:" -ForegroundColor Cyan
    Write-Host "-" * 40
    
    try {
        # Get model list in readable format
        Write-Host "All Available Models:" -ForegroundColor Green
        $modelOutput = ollama list 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host $modelOutput -ForegroundColor Gray
        }
        
        Write-Host ""
        Write-Host "Required Models Analysis:" -ForegroundColor Yellow
        
        $phi3Found = $false
        $embedFound = $false
        
        # Try to get detailed model info
        try {
            $modelsText = ollama list 2>$null
            if ($modelsText -match "phi3:mini") {
                Write-Host "   [OK] phi3:mini (Language Model)" -ForegroundColor Green
                Write-Host "      • Role: Generates answers and responses" -ForegroundColor Gray
                Write-Host "      • Used: When answering your questions" -ForegroundColor Gray
                $phi3Found = $true
            }
            if ($modelsText -match "nomic-embed-text") {
                Write-Host "   [OK] nomic-embed-text (Embedding Model)" -ForegroundColor Green
                Write-Host "      • Role: Converts text to vectors for similarity search" -ForegroundColor Gray
                Write-Host "      • Used: Finding relevant document chunks" -ForegroundColor Gray
                $embedFound = $true
            }
        }
        catch {
            Write-Host "   Checking models with simple test..." -ForegroundColor Gray
        }
        
        # Check for missing models
        if (-not $phi3Found) {
            Write-Host "   [MISSING] phi3:mini - Language Model" -ForegroundColor Red
            Write-Host "      • This model generates your answers" -ForegroundColor Red
        }
        if (-not $embedFound) {
            Write-Host "   [MISSING] nomic-embed-text - Embedding Model" -ForegroundColor Red
            Write-Host "      • This model finds relevant document chunks" -ForegroundColor Red
        }
        
        Write-Host ""
        Write-Host "Two-Model RAG Architecture:" -ForegroundColor Cyan
        Write-Host "   1. nomic-embed-text converts your question to vector" -ForegroundColor Gray
        Write-Host "   2. ChromaDB finds similar document chunks using vectors" -ForegroundColor Gray
        Write-Host "   3. phi3:mini reads chunks and generates your answer" -ForegroundColor Gray
        Write-Host "   4. You see the final answer (phi3:mini is the 'talking' model)" -ForegroundColor Gray
        
        return ($phi3Found -and $embedFound)
    }
    catch {
        Write-Host "Error checking models: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Main execution flow
Write-Host "Step 1: Current System Status" -ForegroundColor Magenta
Show-SystemStatus

Write-Host "Step 2: Process Management" -ForegroundColor Magenta
Stop-OllamaProcesses

Write-Host "Step 3: Fresh Service Start" -ForegroundColor Magenta
if (-not (Start-OllamaService)) {
    Write-Host "Failed to start Ollama service. Exiting..." -ForegroundColor Red
    exit 1
}

Write-Host "Step 4: Model Status Check" -ForegroundColor Magenta
$modelsReady = Show-ModelStatus

if (-not $modelsReady) {
    Write-Host "Downloading missing models..." -ForegroundColor Yellow
    ollama pull phi3:mini
    ollama pull nomic-embed-text
    
    # Recheck models
    Write-Host "Rechecking models after download..." -ForegroundColor Cyan
    $modelsReady = Show-ModelStatus
}

Write-Host "Step 5: System Health Check" -ForegroundColor Magenta
try {
    Write-Host "Running comprehensive health check..." -ForegroundColor Cyan
    
    # Fixed Python code without Unicode emojis
    $testResult = uv run python -c "
import ollama
try:
    models = ollama.list()
    print('OK: Ollama connection working')
    
    # Test phi3:mini
    response = ollama.chat(model='phi3:mini', messages=[{'role': 'user', 'content': 'test'}])
    print('OK: phi3:mini model working')
    
    # Test embedding model
    response = ollama.embeddings(model='nomic-embed-text', prompt='test')
    print('OK: nomic-embed-text model working')
    
    print('SUCCESS: All health checks passed!')
except Exception as e:
    print(f'ERROR: Health check failed - {e}')
    exit(1)
" 2>&1
    
    Write-Host $testResult
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "System health check passed!" -ForegroundColor Green
    }
    else {
        Write-Host "System health check failed!" -ForegroundColor Red
        Write-Host "Attempting auto-repair..." -ForegroundColor Yellow
        
        # Try to pull missing models
        Write-Host "Ensuring required models are available..." -ForegroundColor Cyan
        ollama pull phi3:mini
        ollama pull nomic-embed-text
        
        # Retry health check with fixed Python code
        $retryResult = uv run python -c "
import ollama
try:
    ollama.chat(model='phi3:mini', messages=[{'role': 'user', 'content': 'test'}])
    ollama.embeddings(model='nomic-embed-text', prompt='test')
    print('SUCCESS: Auto-repair successful!')
except Exception as e:
    print(f'ERROR: Auto-repair failed - {e}')
    exit(1)
" 2>&1
        
        Write-Host $retryResult
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Auto-repair failed. Please check manually." -ForegroundColor Red
            exit 1
        }
    }
}
catch {
    Write-Host "Health check error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host "Step 6: Final System Status" -ForegroundColor Magenta
Show-SystemStatus

Write-Host "Step 7: Launching Application" -ForegroundColor Magenta
Write-Host "Starting Streamlit application..." -ForegroundColor Green
Write-Host "Local URL: http://localhost:8501" -ForegroundColor Cyan
Write-Host "Network URL: http://$($(Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -ne '127.0.0.1' -and $_.PrefixOrigin -eq 'Dhcp'})[0].IPAddress):8501" -ForegroundColor Cyan
Write-Host ""
Write-Host "Tip: Press Ctrl+C to stop the application" -ForegroundColor Yellow
Write-Host "=" * 60

# Launch Streamlit
uv run streamlit run src/chat_interface.py

# Cleanup on exit
Write-Host ""
Write-Host "Cleaning up..." -ForegroundColor Yellow
Stop-OllamaProcesses
Write-Host "Cleanup complete. Goodbye!" -ForegroundColor Green