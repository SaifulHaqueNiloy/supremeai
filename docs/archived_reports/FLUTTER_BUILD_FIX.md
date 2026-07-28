# SupremeAI Mobile - Flutter Build Fix Guide

## Problem Description
The build is failing with the following error:
```
FileSystemException(uri=org-dartlang-untranslatable-uri:package%3Asupreme_ai%2Fscreens%2Fchat_screen.dart; message=StandardFileSystem only supports file:* and data:* URIs)
```

This error indicates URI encoding issues in the Flutter build process, likely related to package imports or file paths.

## Root Cause Analysis
The error contains `%3A` (encoded colon) and `%2F` (encoded forward slash), suggesting that package URIs are being incorrectly encoded during the compilation process. This typically happens due to:

1. Incorrect package name references
2. Special characters in file paths
3. Cached build artifacts with incorrect encodings
4. Gradle configuration issues

## Solution Steps

### 1. Clean Build Artifacts
```bash
cd apps/mobile
flutter clean
rm -rf .dart_tool/
rm -rf build/
```

### 2. Verify Package Name Consistency
Ensure all imports use the correct package name `supremeai_mobile`:

```bash
# Find all Dart files
find lib/ -name "*.dart" -exec grep -l "package:" {} \;
```

Verify that all imports follow the pattern:
```dart
import 'package:supremeai_mobile/screens/chat_screen.dart';
import 'package:supremeai_mobile/widgets/widget_name.dart';
```

### 3. Fix Pubspec Format
Ensure pubspec.yaml uses proper formatting:

```bash
# Verify package name in pubspec.yaml
grep -A 5 "^name:" pubspec.yaml
```

### 4. Regenerate Build Files
```bash
flutter pub get
flutter pub cache repair
```

### 5. Android-Specific Fixes
If building for Android, ensure proper configuration:

#### Update `android/gradle.properties`:
```properties
org.gradle.jvmargs=-Xmx4096m -XX:+HeapDumpOnOutOfMemoryError
android.useAndroidX=true
android.enableJetifier=true
org.gradle.configureondemand=false
org.gradle.parallel=true
```

#### Update `android/app/build.gradle` (already done)

### 6. Build with Verbose Output
```bash
flutter build apk --release --verbose
```

## Automated Fix Script

Run the automated fix script:

```bash
dart scripts/fix_uri_encoding.dart
```

Or use the PowerShell script:

```bash
powershell -ExecutionPolicy Bypass -File fix_flutter_deps.ps1
```

## Alternative Build Approaches

### Option 1: Debug Build First
```bash
flutter build apk --debug
```

### Option 2: Split Per ABI
```bash
flutter build apk --split-per-abi --release
```

### Option 3: Use Different Flutter Channel
```bash
flutter channel stable
flutter upgrade
```

## Verification Steps

1. Check that all imports use the correct package name:
   ```bash
   grep -r "package:" lib/ | grep -v ".g.dart"
   ```

2. Verify no special characters in file paths:
   ```bash
   find . -name "*[^a-zA-Z0-9_.-]*" 2>/dev/null || echo "No special characters found"
   ```

3. Confirm pubspec.yaml format:
   ```bash
   cat pubspec.yaml | head -20
   ```

## Prevention

1. Always use consistent package names in imports
2. Avoid special characters in file/directory names
3. Regularly clean build artifacts before major builds
4. Use the automated scripts provided in this repository

## Troubleshooting

If issues persist:

1. Delete the entire `.dart_tool` folder
2. Clear Flutter cache: `flutter clean` followed by `flutter pub cache repair`
3. Check Flutter doctor: `flutter doctor -v`
4. Ensure all dependencies are compatible with each other

## Success Criteria

After applying fixes, you should be able to:
- Run `flutter pub get` without errors
- Execute `flutter analyze` without errors
- Build APK successfully with `flutter build apk --release`

The build should complete without URI encoding errors and produce a functional APK.