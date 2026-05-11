Write-Host "Installing Employee Observations Feature..." -ForegroundColor Cyan

# Step 1: Create static folder
if (!(Test-Path "static")) {
    New-Item -ItemType Directory -Name "static" -Force | Out-Null
    Write-Host "✅ Created static/" -ForegroundColor Green
}

# Step 2: Copy HTML file (you'll paste this from the downloads)
# Download employee_observations.html from outputs and save to static/employee_observations.html
Write-Host "⚠️  Next: Manually copy employee_observations.html to static/ folder" -ForegroundColor Yellow

# Step 3: Copy Python router
# Download employee_observations.py from outputs and save to app/routers/employee_observations.py
Write-Host "⚠️  Next: Manually copy employee_observations.py to app/routers/" -ForegroundColor Yellow

# Step 4: Git push
Write-Host "Pushing to Railway..." -ForegroundColor Cyan
git add .
git commit -m "Add employee observations feature with photo/video upload"
git push

Write-Host "✅ Installation complete!" -ForegroundColor Green
Write-Host "Visit: https://safety-observations-production.up.railway.app/setup" -ForegroundColor Cyan
