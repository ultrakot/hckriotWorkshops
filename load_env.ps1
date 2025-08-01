# PowerShell script to load .env file
# Usage: .\load_env.ps1

if (Test-Path ".env") {
    Write-Host "Loading environment variables from .env file..."
    
    Get-Content ".env" | ForEach-Object {
        if ($_ -match "^\s*([^#][^=]*)\s*=\s*(.*)\s*$") {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            
            # Remove quotes if present
            if ($value -match '^"(.*)"$') { $value = $matches[1] }
            if ($value -match "^'(.*)'$") { $value = $matches[1] }
            
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
            Write-Host "✅ $name = $value"
        }
    }
    
    Write-Host "`n🚀 Environment loaded! You can now run: python app.py"
} else {
    Write-Host "❌ .env file not found!"
    Write-Host "💡 Create one by copying: Copy-Item env.template .env"
}