# SupremeAI Mobile App - APK Build Guide

## Overview
This guide provides step-by-step instructions for safely updating Flutter dependencies and building the APK for the SupremeAI mobile application.

## Current Issue
The build is failing due to 38 packages having newer versions that are incompatible with current dependency constraints. This document outlines how to address these safely.

## Prerequisites
- Flutter SDK installed and in PATH
- Android SDK configured
- Valid Android keystore for release builds

## Safe Dependency Update Process

### Step 1: Analyze Current Dependencies
```bash
cd apps/mobile
flutter pub deps
```

### Step 2: Clean Current Dependencies
```bash
cd apps/mobile
flutter clean
flutter pub cache repair  # Optional: only if needed
```

### Step 3: Update Dependencies Safely
1. **Minor Updates First**: Run this command to update only minor versions:
```bash
flutter pub upgrade --major-versions
```

2. **Selective Updates**: If the above fails, update specific packages individually:
```bash
flutter pub upgrade firebase_core
flutter pub upgrade firebase_auth
flutter pub upgrade firebase_messaging
```

3. **Check Compatibility**: After each update, run:
```bash
flutter pub get
flutter analyze
```

### Step 4: Verify Code Compatibility
```bash
flutter test
```

## Recommended Dependency Versions

Based on the current codebase, these versions are known to work together:

### Core Dependencies
```yaml
dependencies:
  flutter:
    sdk: flutter
  firebase_core: ^4.11.0
  firebase_auth: ^6.5.4
  firebase_messaging: ^16.4.1
  provider: ^6.0.5
  http: ^1.1.0
  web_socket_channel: ^2.4.0
  shared_preferences: ^2.2.2
  flutter_svg: ^2.0.7
  cached_network_image: ^3.3.0
```

### Development Dependencies
```yaml
dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^3.0.0
```

## APK Build Commands

### Debug Build (for testing)
```bash
cd apps/mobile
flutter build apk --debug
```

### Profile Build (for performance testing)
```bash
flutter build apk --profile
```

### Release Build (for distribution)
```bash
flutter build apk --release
```

### Split APKs by ABI (smaller download sizes)
```bash
flutter build apk --split-per-abi --release
```

## Troubleshooting Common Issues

### 1. Version Conflicts
If you encounter version conflicts:
1. Check `pubspec.lock` for conflicting versions
2. Update your `pubspec.yaml` to specify compatible versions
3. Run `flutter clean && flutter pub get`

### 2. Missing Dependencies
If dependencies are missing:
```bash
flutter pub get
flutter packages get
```

### 3. Build Failures
For Android build failures:
1. Check `android/app/build.gradle` for version conflicts
2. Verify Android SDK and NDK versions
3. Clean and rebuild:
```bash
cd android
./gradlew clean
cd ..
flutter clean
flutter build apk
```

### 4. iOS Build Issues (if applicable)
```bash
cd ios
rm -rf Pods Podfile.lock
pod install
cd ..
flutter build ios
```

## Automated Update Script

Run the automated dependency update script:
```bash
dart scripts/update_flutter_deps.dart
```

This script will:
- Create a backup of your current `pubspec.yaml`
- Update dependency versions to known compatible ranges
- Provide next steps for building

## Gradle Configuration (Android)

Ensure your `android/app/build.gradle` has compatible versions:

```gradle
android {
    compileSdkVersion 34
    ndkVersion flutter.ndkVersion

    compileOptions {
        sourceCompatibility JavaVersion.VERSION_1_8
        targetCompatibility JavaVersion.VERSION_1_8
    }

    kotlinOptions {
        jvmTarget = '1.8'
    }

    sourceSets {
        main.java.srcDirs += 'src/main/kotlin'
    }

    defaultConfig {
        // TODO: Specify your own unique Application ID (https://developer.android.com/studio/build/application-id.html).
        applicationId "com.supremeai.mobile"
        minSdkVersion flutter.minSdkVersion
        targetSdkVersion flutter.targetSdkVersion
        versionCode flutterVersionCode.toInteger()
        versionName flutterVersionName
    }

    buildTypes {
        release {
            signingConfig signingConfigs.debug
        }
    }
}
```

## Environment Setup Verification

Before building, verify your environment:
```bash
flutter doctor
```

Ensure all checks pass, especially:
- [√] Flutter (Channel stable)
- [√] Android toolchain
- [√] Android Studio (or VS Code with Flutter plugin)
- [√] Connected device (if testing on device)

## Post-Build Verification

After building the APK:
1. Install on test device/emulator
2. Verify all features work as expected
3. Check for any runtime errors
4. Test core functionality (authentication, API calls, etc.)

## Rollback Plan

If updates cause issues:
1. Restore from backup: `cp pubspec.yaml.backup pubspec.yaml`
2. Run: `flutter clean && flutter pub get`
3. Test functionality

## Continuous Integration Notes

For CI/CD pipelines, consider:
- Pinning dependency versions in `pubspec.lock`
- Running `flutter analyze` and tests before building
- Using `--release` flag for production builds
- Implementing proper signing configurations for release builds

## Conclusion

Following this guide should resolve the dependency compatibility issues and allow successful APK builds. Remember to test thoroughly after any dependency updates.