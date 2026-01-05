# Building App Variants

Phase 8.2.2: How to build and test the three app variants (Lite, Standard, Full)

## Overview

Data20 mobile app comes in **3 variants**:

| Variant | Size | Tools | Target |
|---------|------|-------|--------|
| **Lite** | ~45 MB | 12 | Budget devices, limited storage |
| **Standard** | ~65 MB | 35 | Most users |
| **Full** | ~95 MB | 57 | Power users, complete feature set |

## Prerequisites

```bash
# Install dependencies
flutter pub get

# Ensure you're using build-optimized.gradle
cd android/app
# Use build-optimized.gradle instead of build.gradle
```

## Building Variants

### 1. Build Lite Variant

```bash
# Debug build
flutter build apk --flavor lite --debug \
  --dart-define=APP_VARIANT=lite

# Release build
flutter build apk --flavor lite --release \
  --dart-define=APP_VARIANT=lite

# App Bundle (for Play Store)
flutter build appbundle --flavor lite --release \
  --dart-define=APP_VARIANT=lite
```

**Expected output:**
- APK size: ~40-50 MB
- Package: `com.data20.mobile_app.lite`
- App name: "Data20 Lite"
- Tools: 12 core tools

### 2. Build Standard Variant

```bash
# Debug build
flutter build apk --flavor standard --debug \
  --dart-define=APP_VARIANT=standard

# Release build
flutter build apk --flavor standard --release \
  --dart-define=APP_VARIANT=standard

# App Bundle (for Play Store)
flutter build appbundle --flavor standard --release \
  --dart-define=APP_VARIANT=standard
```

**Expected output:**
- APK size: ~60-70 MB
- Package: `com.data20.mobile_app.standard`
- App name: "Data20 Standard"
- Tools: 35 essential tools

### 3. Build Full Variant

```bash
# Debug build
flutter build apk --flavor full --debug \
  --dart-define=APP_VARIANT=full

# Release build
flutter build apk --flavor full --release \
  --dart-define=APP_VARIANT=full

# App Bundle (for Play Store)
flutter build appbundle --flavor full --release \
  --dart-define=APP_VARIANT=full
```

**Expected output:**
- APK size: ~90-100 MB
- Package: `com.data20.mobile_app`
- App name: "Data20"
- Tools: 57 all tools

## Build All Variants at Once

```bash
#!/bin/bash
# build_all_variants.sh

echo "Building all variants..."

# Lite
echo "📱 Building Lite variant..."
flutter build apk --flavor lite --release \
  --dart-define=APP_VARIANT=lite

# Standard
echo "📱 Building Standard variant..."
flutter build apk --flavor standard --release \
  --dart-define=APP_VARIANT=standard

# Full
echo "📱 Building Full variant..."
flutter build apk --flavor full --release \
  --dart-define=APP_VARIANT=full

echo "✅ All variants built successfully!"

# Show sizes
echo ""
echo "APK Sizes:"
cd build/app/outputs/flutter-apk
ls -lh *.apk | awk '{print $9, $5}'
```

## Testing Variants

### 1. Install on Device

```bash
# Install Lite
flutter install --flavor lite --dart-define=APP_VARIANT=lite

# Install Standard
flutter install --flavor standard --dart-define=APP_VARIANT=standard

# Install Full
flutter install --flavor full --dart-define=APP_VARIANT=full
```

**Note:** All three variants can be installed side-by-side because they have different package names.

### 2. Verify Variant Detection

After installing, check that the correct variant is detected:

1. Open the app
2. Check the banner at the top of the home screen:
   - **Lite**: ⚡ Purple banner with "Lite Edition"
   - **Standard**: ⭐ Blue banner with "Standard Edition"
   - **Full**: 💎 Green banner with "Full Edition"

3. Check tool count in the backend logs:
   ```bash
   adb logcat | grep "Loaded.*tools"
   # Should show:
   # Lite: "Loaded 12 tools"
   # Standard: "Loaded 35 tools"
   # Full: "Loaded 57 tools"
   ```

### 3. Verify Tool Filtering

**Lite variant** should only show:
- calculate_reading_time
- validate
- metadata_validator
- search_index
- advanced_search
- faceted_search
- find_duplicates
- find_orphans
- find_related
- backlinks_generator
- export_manager
- tags_cloud

**Standard variant** should show all Lite tools plus:
- generate_statistics
- quality_metrics
- build_concordance
- build_glossary
- auto_tagger
- ... (23 more tools)

**Full variant** should show all 57 tools.

## Checking APK Sizes

### Method 1: Using Gradle Task

```bash
cd android
./gradlew showApkSizes
```

### Method 2: Manual Check

```bash
cd build/app/outputs/flutter-apk
ls -lh *.apk

# Expected:
# app-lite-release.apk      ~45 MB
# app-standard-release.apk  ~65 MB
# app-full-release.apk      ~95 MB
```

### Method 3: APK Analyzer

```bash
# Install APK Analyzer
$ANDROID_HOME/tools/bin/apkanalyzer -h

# Analyze APK
apkanalyzer apk summary build/app/outputs/flutter-apk/app-lite-release.apk
apkanalyzer apk summary build/app/outputs/flutter-apk/app-standard-release.apk
apkanalyzer apk summary build/app/outputs/flutter-apk/app-full-release.apk
```

## Understanding the Build Process

### 1. Gradle Product Flavors

The `build-optimized.gradle` file defines three product flavors:

```gradle
productFlavors {
    lite {
        applicationIdSuffix ".lite"
        buildConfigField "String", "APP_VARIANT", '"lite"'
        ndk { abiFilters "arm64-v8a" }
    }
    standard {
        applicationIdSuffix ".standard"
        buildConfigField "String", "APP_VARIANT", '"standard"'
        ndk { abiFilters "arm64-v8a", "armeabi-v7a" }
    }
    full {
        // No suffix - original package
        buildConfigField "String", "APP_VARIANT", '"full"'
        ndk { abiFilters "arm64-v8a", "armeabi-v7a" }
    }
}
```

### 2. Conditional Python Dependencies

Each flavor loads different Python packages:

**Lite:**
- FastAPI, uvicorn, pydantic (core backend)
- Basic utilities (PyYAML, markdown, requests)
- **Size saved:** ~50 MB

**Standard:**
- Lite packages +
- numpy, openpyxl, lxml
- **Size added:** ~25 MB

**Full:**
- Standard packages +
- pandas, Pillow, httpx
- **Size added:** ~20 MB

### 3. Tool Registry Filtering

The Python backend (`variant_config.py`) defines which tools are available:

```python
TOOL_DEPENDENCIES = {
    "calculate_reading_time": DependencyLevel.CORE,    # Lite+
    "generate_statistics": DependencyLevel.LIGHT,      # Standard+
    "build_graph": DependencyLevel.HEAVY,              # Full only
}
```

### 4. Flutter Variant Detection

Flutter detects the variant via `--dart-define`:

```dart
const String variantName = String.fromEnvironment(
  'APP_VARIANT',
  defaultValue: 'full',
);
```

## Troubleshooting

### Build Fails with "Flavor not found"

**Solution:** Ensure you're using `build-optimized.gradle`:

```bash
cd android/app
mv build.gradle build.gradle.bak
mv build-optimized.gradle build.gradle
```

### APK Size Too Large

**Check:**
1. Are you building in release mode?
   ```bash
   flutter build apk --flavor lite --release
   ```

2. Is ProGuard enabled?
   ```gradle
   release {
       minifyEnabled true
       shrinkResources true
   }
   ```

3. Check ABI filters:
   ```bash
   apkanalyzer apk file-size build/app/outputs/flutter-apk/app-lite-release.apk
   ```

### Tools Not Filtered Correctly

**Check backend logs:**
```bash
adb logcat | grep PyodideService
adb logcat | grep "Tool Registry"
```

**Verify variant detection:**
```bash
adb logcat | grep "APP_VARIANT"
```

### Variant Banner Not Showing

**Check Flutter configuration:**
```dart
// lib/config/app_variant.dart
print('Detected variant: ${AppVariantConfig.variant}');
```

## Publishing to Play Store

### 1. Build App Bundles

```bash
# Build all bundles
flutter build appbundle --flavor lite --release --dart-define=APP_VARIANT=lite
flutter build appbundle --flavor standard --release --dart-define=APP_VARIANT=standard
flutter build appbundle --flavor full --release --dart-define=APP_VARIANT=full
```

### 2. Configure Play Console

Create **3 separate apps** in Google Play Console:

1. **Data20 Lite**
   - Package: `com.data20.mobile_app.lite`
   - Target: Budget users, emerging markets
   - Description: "Lightweight version with 12 core tools"

2. **Data20 Standard**
   - Package: `com.data20.mobile_app.standard`
   - Target: Most users
   - Description: "Essential version with 35 tools"

3. **Data20** (Full)
   - Package: `com.data20.mobile_app`
   - Target: Power users
   - Description: "Complete version with all 57 tools"

### 3. Add Upgrade Prompts

The app automatically shows upgrade prompts in Lite/Standard variants:
- Lite → Standard: "Upgrade for 35 tools"
- Standard → Full: "Upgrade for 57 tools"

## Performance Optimization

See [APK_OPTIMIZATION_PLAN.md](APK_OPTIMIZATION_PLAN.md) for:
- Dependency analysis
- Size reduction strategies
- Further optimization opportunities

## Next Steps

- [ ] Test all 3 variants on physical devices
- [ ] Verify tool filtering works correctly
- [ ] Measure actual APK sizes
- [ ] Test upgrade prompts
- [ ] Create Play Store listings
- [ ] Submit for review

## Related Documentation

- [APK_OPTIMIZATION_PLAN.md](APK_OPTIMIZATION_PLAN.md) - Optimization strategy
- [../docs/PHASES_1-7.md](../docs/PHASES_1-7.md) - Project history
- [../docs/NEXT_PHASES_ROADMAP.md](../docs/NEXT_PHASES_ROADMAP.md) - Future phases
