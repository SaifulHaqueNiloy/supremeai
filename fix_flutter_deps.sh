#!/bin/bash

# Bash script to fix common Flutter dependency issues for SupremeAI Mobile

echo "🔧 SupremeAI Mobile - Flutter Dependency Fix Script"
echo "================================================="

# Check if in the right directory
if [ ! -d "apps/mobile" ]; then
    echo "❌ Error: apps/mobile directory not found!"
    echo "Please run this script from the project root directory."
    exit 1
fi

# Navigate to mobile directory
cd apps/mobile

echo ""
echo "1. Cleaning Flutter project..."
flutter clean
if [ $? -ne 0 ]; then
    echo "❌ Flutter clean failed!"
    exit 1
fi

echo ""
echo "2. Getting dependencies..."
flutter pub get
if [ $? -ne 0 ]; then
    echo "❌ Flutter pub get failed!"
    exit 1
fi

echo ""
echo "3. Running pub upgrade with safer options..."
# Try upgrading with safer options first
flutter pub upgrade --major-versions
if [ $? -ne 0 ]; then
    echo "⚠️  Major version upgrade failed, trying selective upgrades..."
    
    # Backup original pubspec
    cp pubspec.yaml pubspec.yaml.backup
    
    # Use sed to update to known good versions
    sed -i.bak 's/firebase_core: \^.*/firebase_core: ^4.11.0/' pubspec.yaml
    sed -i.bak 's/firebase_auth: \^.*/firebase_auth: ^6.5.4/' pubspec.yaml
    sed -i.bak 's/firebase_messaging: \^.*/firebase_messaging: ^16.4.1/' pubspec.yaml
    sed -i.bak 's/provider: \^.*/provider: ^6.0.5/' pubspec.yaml
    sed -i.bak 's/http: \^.*/http: ^1.1.0/' pubspec.yaml
    sed -i.bak 's/web_socket_channel: \^.*/web_socket_channel: ^2.4.0/' pubspec.yaml
    sed -i.bak 's/shared_preferences: \^.*/shared_preferences: ^2.2.2/' pubspec.yaml
    sed -i.bak 's/flutter_svg: \^.*/flutter_svg: ^2.0.7/' pubspec.yaml
    sed -i.bak 's/cached_network_image: \^.*/cached_network_image: ^3.3.0/' pubspec.yaml
    
    # Remove backup files created by sed
    rm -f pubspec.yaml.bak
    
    echo "✏️  Updated pubspec.yaml with known good versions"
    
    # Try getting dependencies again
    flutter pub get
    if [ $? -ne 0 ]; then
        echo "❌ Failed to get dependencies after manual fix!"
        exit 1
    fi
fi

echo ""
echo "4. Analyzing project..."
flutter analyze
if [ $? -eq 0 ]; then
    echo "✅ Analysis passed!"
else
    echo "⚠️  Analysis had issues, but continuing..."
fi

echo ""
echo "5. Running tests..."
flutter test
if [ $? -eq 0 ]; then
    echo "✅ Tests passed!"
else
    echo "⚠️  Tests had failures, but continuing..."
fi

# Go back to root directory
cd ../..

echo ""
echo "✅ Dependency fix process completed!"
echo "You can now try building the APK:"
echo "  cd apps/mobile"
echo "  flutter build apk --debug"

echo ""
echo "For release build:"
echo "  flutter build apk --release"