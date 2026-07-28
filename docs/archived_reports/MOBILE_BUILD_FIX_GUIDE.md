# SupremeAI Mobile - Build Fix Guide

## Issue Description
The build is failing with the following error:
```
lib/screens/home_screen.dart:2:8: Error: Not found: 'package:supreme_ai/screens/chat_screen.dart'
import 'package:supreme_ai/screens/chat_screen.dart';
...
FileSystemException(uri=org-dartlang-untranslatable-uri:package%3Asupreme_ai%2Fscreens%2Fchat_screen.dart; message=StandardFileSystem only supports file:* and data:* URIs)
```

## Root Cause
The error indicates that:
1. The build system is looking for `package:supreme_ai/` imports
2. But the actual package name is `supremeai_mobile`
3. During compilation, package names are getting URL-encoded incorrectly

## Solution

### Step 1: Verify Package Name in pubspec.yaml
Ensure your `apps/mobile/pubspec.yaml` contains:
```yaml
name: supremeai_mobile
description: A new Flutter project for SupremeAI Mobile App.
```

### Step 2: Verify All Imports Use Correct Package Name
All imports in the mobile app should use `package:supremeai_mobile/`:
```dart
import 'package:supremeai_mobile/screens/chat_screen.dart';
import 'package:supremeai_mobile/widgets/chat_message_widget.dart';
// etc.
```

### Step 3: Clean Build Artifacts (Critical)
This is the most important step. The build cache contains incorrect references.

From the `apps/mobile` directory, run:
```bash
# Clean all build artifacts
flutter clean

# Remove build directory
rm -rf build/

# Remove .dart_tool directory (contains cached module maps)
rm -rf .dart_tool/

# Remove Android and iOS build caches
rm -rf android/.gradle/
rm -rf ios/.symlinks/

# Remove potential cache files
rm -f .packages
rm -f .flutter-plugins
rm -f .flutter-plugins-dependencies
```

### Step 4: Reinstall Dependencies
```bash
flutter pub get
flutter pub upgrade
```

### Step 5: Regenerate Build Files
```bash
flutter packages get
flutter clean
flutter pub get
```

### Step 6: Build Again
```bash
# Try debug build first
flutter build apk --debug

# If debug works, try release
flutter build apk --release
```

## Additional Checks

### Check for Any Remaining Incorrect References
Search your codebase for any remaining incorrect references:
```bash
grep -r "package:supreme_ai" apps/mobile/
```

### Verify Import Structure
Ensure all files under `lib/` follow the correct import pattern:
- `import 'package:supremeai_mobile/screens/screen_name.dart';`
- `import 'package:supremeai_mobile/widgets/widget_name.dart';`
- `import 'package:supremeai_mobile/models/model_name.dart';`
- etc.

## CI/CD Specific Instructions

For CI/CD environments (like the one that produced the error):

1. **Always start with a clean checkout** - don't reuse build artifacts
2. **Clean before building**:
   ```bash
   cd apps/mobile
   flutter clean
   flutter pub get
   ```
3. **Use fresh dependencies** - don't rely on cached packages when package name has changed

## Why This Happens

This issue occurs when:
- Package name was changed but build cache wasn't cleared
- Flutter tools cached old module maps with incorrect names
- Build environment has stale artifacts from previous builds
- URL encoding during compilation creates malformed URIs

## Prevention

To prevent this in the future:
1. Always run `flutter clean` when changing package names
2. Don't commit build artifacts to version control
3. Ensure CI/CD starts with clean checkouts
4. Use `.gitignore` to exclude `build/`, `.dart_tool/`, and similar directories

## Troubleshooting

If the issue persists:

1. **Delete entire Flutter cache**:
   ```bash
   flutter pub cache repair
   ```

2. **Verify Flutter installation**:
   ```bash
   flutter doctor -v
   ```

3. **Check for hidden files**:
   ```bash
   find . -name "*supreme_ai*" -type f
   ```

4. **Manual verification**:
   - Double-check `pubspec.yaml` name field
   - Verify all import statements in `lib/` directory
   - Ensure no symbolic links point to incorrect locations

## Success Verification

After applying fixes, you should be able to:
- Run `flutter pub get` without errors
- Run `flutter analyze` without import errors
- Build APK successfully

The build should no longer show errors about missing `package:supreme_ai/` imports.
