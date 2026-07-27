# PowerShell script to fix common Flutter dependency issues for SupremeAI Mobile
Write-Host "🔧 SupremeAI Mobile - Flutter Dependency Fix Script" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green

# Check if in the right directory
if (-not (Test-Path "apps\mobile")) {
    Write-Host "❌ Error: apps\mobile directory not found!" -ForegroundColor Red
    Write-Host "Please run this script from the project root directory." -ForegroundColor Yellow
    exit 1
}

# Navigate to mobile directory
Set-Location apps\mobile

Write-Host "`n1. Cleaning Flutter project..." -ForegroundColor Cyan
flutter clean
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Flutter clean failed!" -ForegroundColor Red
    exit 1
}

Write-Host "`n2. Getting dependencies..." -ForegroundColor Cyan
flutter pub get
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Flutter pub get failed!" -ForegroundColor Red
    exit 1
}

Write-Host "`n3. Running pub upgrade with safer options..." -ForegroundColor Cyan
# Try upgrading with safer options first
flutter pub upgrade --major-versions
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Major version upgrade failed, trying selective upgrades..." -ForegroundColor Yellow

    # Get the pubspec.yaml content
    $pubspec = Get-Content pubspec.yaml -Raw

    # Define known good versions
    $replacements = @{
        "firebase_core: \^[^`n]+" = "firebase_core: ^4.11.0";
        "firebase_auth: \^[^`n]+" = "firebase_auth: ^6.5.4";
        "firebase_messaging: \^[^`n]+" = "firebase_messaging: ^16.4.1";
        "provider: \^[^`n]+" = "provider: ^6.0.5";
        "http: \^[^`n]+" = "http: ^1.1.0";
        "web_socket_channel: \^[^`n]+" = "web_socket_channel: ^2.4.0";
        "shared_preferences: \^[^`n]+" = "shared_preferences: ^2.2.2";
        "flutter_svg: \^[^`n]+" = "flutter_svg: ^2.0.7";
        "cached_network_image: \^[^`n]+" = "cached_network_image: ^3.3.0";
    }

    # Perform replacements
    foreach ($pattern in $replacements.GetEnumerator()) {
        $pubspec = $pubspec -replace $pattern.Key, $pattern.Value
    }

    # Write updated pubspec
    $pubspec | Out-File -FilePath pubspec.yaml -Encoding UTF8

    Write-Host "✏️  Updated pubspec.yaml with known good versions" -ForegroundColor Green

    # Try getting dependencies again
    flutter pub get
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to get dependencies after manual fix!" -ForegroundColor Red
        exit 1
    }
}

Write-Host "`n4. Analyzing project..." -ForegroundColor Cyan
flutter analyze
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Analysis passed!" -ForegroundColor Green
} else {
    Write-Host "⚠️  Analysis had issues, but continuing..." -ForegroundColor Yellow
}

Write-Host "`n5. Running tests..." -ForegroundColor Cyan
flutter test
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Tests passed!" -ForegroundColor Green
} else {
    Write-Host "⚠️  Tests had failures, but continuing..." -ForegroundColor Yellow
}

# Go back to root directory
Set-Location ..\..

Write-Host "`n✅ Dependency fix process completed!" -ForegroundColor Green
Write-Host "You can now try building the APK:" -ForegroundColor Yellow
Write-Host "  cd apps\mobile" -ForegroundColor Yellow
Write-Host "  flutter build apk --debug" -ForegroundColor Yellow

Write-Host "`nFor release build:" -ForegroundColor Yellow
Write-Host "  flutter build apk --release" -ForegroundColor Yellow
