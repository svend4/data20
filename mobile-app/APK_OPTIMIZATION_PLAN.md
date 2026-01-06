# APK Size Optimization Plan
## Phase 8.2: Mobile App Optimization

**Created**: 2026-01-05
**Current APK Size**: ~100MB
**Target**: 3 optimized variants (Lite/Standard/Full)

---

## 📊 Current Size Analysis

### Size Breakdown (Estimated)
| Component | Size | % of Total |
|-----------|------|------------|
| Python Runtime (Chaquopy) | ~15MB | 15% |
| pandas + numpy | ~30MB | 30% |
| FastAPI + dependencies | ~10MB | 10% |
| lxml | ~8MB | 8% |
| Pillow | ~5MB | 5% |
| Other Python packages | ~12MB | 12% |
| Native libraries (4 ABIs) | ~15MB | 15% |
| Flutter framework | ~8MB | 8% |
| App code & assets | ~7MB | 7% |
| **TOTAL** | **~110MB** | **100%** |

### Heavy Dependencies
1. **pandas** (~18MB) - Used by ~15 tools
2. **numpy** (~12MB) - Used by ~20 tools
3. **lxml** (~8MB) - Used by ~8 tools (XML/HTML processing)
4. **Pillow** (~5MB) - Used by ~5 tools (image processing)
5. **openpyxl** (~3MB) - Used by ~10 tools (Excel files)

---

## 🎯 Optimization Strategy

### Variant 1: **Lite** (Target: 40-50MB)
**12 Core Tools** - Essential functionality only

**Included Tools**:
1. Search & Filter
2. Text Statistics
3. Reading Time Calculator
4. Word Counter
5. Data Validator
6. JSON Formatter
7. List Deduplicator
8. Simple Calculator
9. Tag Manager
10. Category Browser
11. Quick Export (Markdown/Text)
12. Backlinks Generator

**Dependencies Removed**:
- ❌ pandas
- ❌ numpy
- ❌ lxml → ✅ beautifulsoup4 (lighter alternative)
- ❌ Pillow
- ❌ openpyxl

**ABI Support**:
- arm64-v8a only (modern devices 95%+)

**Estimated Size**: **45MB**

---

### Variant 2: **Standard** (Target: 60-70MB)
**35 Essential Tools** - Most popular tools

**Included Tools** (12 from Lite + 23 more):
13. Advanced Search
14. Build Glossary
15. Build Thesaurus
16. Build Card Catalog
17. Build Concordance
18. Citation Index
19. Cross References
20. Check Links
21. Auto Tagger
22. Calculate Difficulty
23. Flesch Reading Ease
24. Chain References
25. Build Taxonomy
26. Time Series Analyzer
27. Basic Statistics
28. Data Cleaner
29. CSV Tools
30. JSON Tools
31. YAML Tools
32. Markdown Tools
33. Export to HTML
34. Export to PDF (text-based)
35. Batch Processor

**Dependencies**:
- ✅ numpy (needed for statistics)
- ❌ pandas → ✅ Pure Python alternatives where possible
- ✅ lxml (lightweight XML parsing)
- ❌ Pillow
- ✅ openpyxl

**ABI Support**:
- arm64-v8a primary
- armeabi-v7a fallback (older devices)

**Estimated Size**: **65MB**

---

### Variant 3: **Full** (Target: 90-100MB)
**57 All Tools** - Complete functionality

**Included**: All 57 tools

**Dependencies**:
- ✅ pandas (full data analysis)
- ✅ numpy (numerical computing)
- ✅ lxml (advanced XML/HTML)
- ✅ Pillow (image processing)
- ✅ openpyxl (Excel support)
- ✅ All other dependencies

**ABI Support**:
- arm64-v8a (primary)
- armeabi-v7a (fallback)

**Estimated Size**: **95MB**

---

## 🛠️ Implementation Plan

### Step 1: Create Product Flavors

```gradle
// build.gradle (app level)
android {
    flavorDimensions "version"

    productFlavors {
        lite {
            dimension "version"
            applicationIdSuffix ".lite"
            versionNameSuffix "-lite"

            buildConfigField "int", "TOOL_COUNT", "12"
            buildConfigField "String", "VERSION_NAME", '"Lite"'

            // Only arm64
            ndk {
                abiFilters "arm64-v8a"
            }
        }

        standard {
            dimension "version"
            applicationIdSuffix ".standard"
            versionNameSuffix "-standard"

            buildConfigField "int", "TOOL_COUNT", "35"
            buildConfigField "String", "VERSION_NAME", '"Standard"'

            // arm64 + arm32 fallback
            ndk {
                abiFilters "arm64-v8a", "armeabi-v7a"
            }
        }

        full {
            dimension "version"
            // No suffix - default package name

            buildConfigField "int", "TOOL_COUNT", "57"
            buildConfigField "String", "VERSION_NAME", '"Full"'

            // arm64 + arm32
            ndk {
                abiFilters "arm64-v8a", "armeabi-v7a"
            }
        }
    }
}
```

### Step 2: Conditional Python Dependencies

```gradle
chaquopy {
    defaultConfig {
        version "3.9"

        pip {
            // Core dependencies (all variants)
            install "fastapi==0.104.1"
            install "uvicorn==0.24.0"
            install "pydantic==2.5.0"
            install "PyYAML==6.0.1"
            install "markdown==3.5.1"
            install "beautifulsoup4==4.12.2"
        }
    }

    productFlavors {
        lite {
            // Minimal dependencies
            pip {
                install "requests==2.31.0"
            }
        }

        standard {
            // Add numpy + lxml + openpyxl
            pip {
                install "numpy==1.26.2"
                install "lxml==4.9.3"
                install "openpyxl==3.1.2"
                install "requests==2.31.0"
            }
        }

        full {
            // All dependencies
            pip {
                install "pandas==2.1.3"
                install "numpy==1.26.2"
                install "lxml==4.9.3"
                install "Pillow==10.1.0"
                install "openpyxl==3.1.2"
                install "requests==2.31.0"
            }
        }
    }
}
```

### Step 3: Conditional Tool Loading

```python
# Python backend - main.py
import os

# Get variant from environment
VARIANT = os.environ.get('APP_VARIANT', 'full')

# Tool registry based on variant
if VARIANT == 'lite':
    from tools import (
        search_filter,
        text_statistics,
        calculate_reading_time,
        word_counter,
        data_validator,
        json_formatter,
        list_deduplicator,
        simple_calculator,
        tag_manager,
        category_browser,
        quick_export,
        backlinks_generator,
    )
    AVAILABLE_TOOLS = 12

elif VARIANT == 'standard':
    from tools import *  # 35 tools
    AVAILABLE_TOOLS = 35

else:  # full
    from tools import *  # All 57 tools
    AVAILABLE_TOOLS = 57
```

### Step 4: Build Scripts

```bash
#!/bin/bash
# build-variants.sh

echo "Building Data20 Mobile App Variants..."

# Lite version
echo "Building Lite variant..."
flutter build apk --flavor lite --release
mv build/app/outputs/flutter-apk/app-lite-release.apk \
   build/data20-lite-v1.0.0.apk

# Standard version
echo "Building Standard variant..."
flutter build apk --flavor standard --release
mv build/app/outputs/flutter-apk/app-standard-release.apk \
   build/data20-standard-v1.0.0.apk

# Full version
echo "Building Full variant..."
flutter build apk --flavor full --release
mv build/app/outputs/flutter-apk/app-full-release.apk \
   build/data20-full-v1.0.0.apk

echo "Done! Generated 3 APK variants:"
ls -lh build/*.apk
```

---

## 📈 Additional Optimizations

### 1. ProGuard/R8 Optimization
```proguard
# proguard-rules.pro

# Remove unused code
-dontwarn **
-ignorewarnings

# Optimize method calls
-optimizations !code/simplification/arithmetic,!field/*,!class/merging/*
-optimizationpasses 5

# Remove logging in release
-assumenosideeffects class android.util.Log {
    public static *** d(...);
    public static *** v(...);
    public static *** i(...);
}

# Keep Python modules
-keep class com.chaquo.python.** { *; }
```

### 2. Resource Optimization
```xml
<!-- res/values/strings.xml -->
<!-- Remove unused strings -->

<!-- Enable resource shrinking -->
android {
    buildTypes {
        release {
            shrinkResources true
            minifyEnabled true
        }
    }
}
```

### 3. Android App Bundle (.aab)
Instead of APK, use App Bundle for automatic optimization:
```bash
flutter build appbundle --flavor full --release

# Benefits:
# - Google Play automatically generates optimized APKs
# - Only downloads necessary ABIs per device
# - 15-20% size reduction on average
```

### 4. WebP Images
Convert all PNG/JPG to WebP:
```bash
# Convert assets to WebP
for img in assets/images/*.png; do
    cwebp -q 85 "$img" -o "${img%.png}.webp"
done

# Size reduction: ~30-40%
```

---

## 🎯 Expected Results

### Size Comparison
| Variant | Current | Target | Actual (Est.) | Savings |
|---------|---------|--------|---------------|---------|
| Lite | - | 40-50MB | 45MB | 55MB (55%) |
| Standard | - | 60-70MB | 65MB | 35MB (35%) |
| Full | 100MB | 90-100MB | 95MB | 5MB (5%) |

### Performance Impact
| Metric | Lite | Standard | Full |
|--------|------|----------|------|
| Install Size | 45MB | 65MB | 95MB |
| Startup Time | 2s | 2.5s | 3s |
| Memory Usage | 150MB | 200MB | 250MB |
| Battery/Hour | 3% | 4% | 5% |

### User Distribution (Estimated)
- **Lite**: 40% of users (casual users, older devices)
- **Standard**: 45% of users (regular users)
- **Full**: 15% of users (power users, analysts)

---

## 📝 Implementation Checklist

### Phase 1: Setup (Day 1)
- [ ] Create product flavors in build.gradle
- [ ] Configure conditional dependencies
- [ ] Add build configuration fields
- [ ] Test builds for all 3 variants

### Phase 2: Python Backend (Day 2)
- [ ] Create tool registry per variant
- [ ] Implement conditional tool loading
- [ ] Create lightweight alternatives for heavy tools
- [ ] Test Python backend for each variant

### Phase 3: Flutter Frontend (Day 3)
- [ ] Add variant detection in Dart
- [ ] Show/hide tools based on variant
- [ ] Add upgrade prompts for lite/standard users
- [ ] Update UI to show variant name

### Phase 4: Optimization (Day 4)
- [ ] Enable ProGuard/R8 optimization
- [ ] Implement resource shrinking
- [ ] Convert images to WebP
- [ ] Remove unused assets

### Phase 5: Testing (Day 5)
- [ ] Test all 3 variants on real devices
- [ ] Measure actual APK sizes
- [ ] Benchmark startup time
- [ ] Test battery consumption

### Phase 6: Build & Release (Day 6)
- [ ] Generate production APKs/AABs
- [ ] Create release notes for each variant
- [ ] Upload to internal testing
- [ ] Prepare for production release

---

## 🔧 Tools & Technologies

- **Chaquopy**: Python on Android
- **ProGuard/R8**: Code shrinking
- **Flutter Build Flavors**: Variant management
- **Android App Bundle**: Automatic optimization
- **WebP**: Image compression
- **Gradle**: Build configuration

---

## 📊 Monitoring

After release, track:
- **Download size** per variant
- **Install success rate**
- **Crash rate** per variant
- **User ratings** per variant
- **Upgrade rate** (lite → standard → full)

---

## 🚀 Future Improvements

1. **Dynamic Feature Modules**: Load tools on-demand
2. **Tool Marketplace**: Download individual tools
3. **Cloud Offload**: Execute heavy tools on server
4. **Compression**: Use Brotli for Python modules
5. **Tree Shaking**: More aggressive code elimination

---

**Created**: 2026-01-05
**Version**: 1.0.0
**Status**: 📝 Plan Ready for Implementation
