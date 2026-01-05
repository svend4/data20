# 📱 Version 3: Lite Edition

## 🪶 Minimal Embedded Backend - Small & Fast

This is the **minimal embedded version** with only 12 essential tools for basic offline functionality.

---

## 📊 Version Information

- **Version**: v3-lite
- **Based on**: v4-standard (reduced)
- **Status**: ✅ Production Ready (minimal)
- **Purpose**: Small APK, essential features only

---

## 🪶 Why Choose v3-lite?

**Smallest embedded version** with offline capability:
- 12 essential tools only
- 50MB APK (half the size of v4)
- 100% offline
- Fast startup
- Low RAM usage
- Good for older/budget devices

---

## 📊 Technical Specifications

### APK Size: ~50MB
- Python 3.9 runtime: ~30MB
- FastAPI + dependencies: ~10MB
- 12 tools: ~5MB
- Flutter app: ~5MB

### System Requirements
- Android 7.0+ (API 24)
- RAM: 1GB (recommended 2GB)
- Storage: 70MB
- Internet: NOT required

### Performance
- First launch: 3-4 seconds
- Subsequent launches: 1 second
- Battery usage: ~3-5% per hour

---

## 📦 What's Included: 12 Essential Tools

### Core Indexing (3 tools)
- build_taxonomy.py - Build taxonomy
- build_glossary.py - Create glossary
- build_thesaurus.py - Generate thesaurus

### Search & Navigation (3 tools)
- advanced_search.py - Advanced search
- find_related.py - Find related content
- generate_toc.py - Table of contents

### Analysis & Export (3 tools)
- generate_statistics.py - Statistical analysis
- generate_bibliography.py - Bibliography generation
- export_manager.py - Export management

### Validation (3 tools)
- duplicate_detector.py - Detect duplicates
- check_links.py - Link validation
- validate.py - General validation

---

## 🎯 Use Cases

### ✅ When to Use v3-lite

- **Limited storage** - Only 70MB total
- **Older devices** - Works with 1GB RAM
- **Simple workflows** - Basic indexing, search, validation
- **Fast performance** - Need quick startup
- **Basic offline needs** - Essential features only

### ❌ When NOT to Use

- **Complex workflows** → Use v4-standard or v5-full
- **Need all tools** → Use v5-full (57 tools)
- **Advanced features** → Use v4-standard (35 tools)

---

## 📊 Comparison

| Metric | v3-lite | v4-standard | v5-full |
|--------|---------|-------------|---------|
| APK Size | 50MB | 70MB | 100MB |
| Tools | 12 | 35 | 57 |
| Startup | 3-4s | 4-6s | 5-7s |
| RAM | 1GB | 1.5GB | 2GB |
| Storage | 70MB | 100MB | 150MB |

---

## 🔧 Build Instructions

```bash
cd mobile-app-versions/v3-lite
./build-android-embedded.sh release
```

APK location: `build/app/outputs/flutter-apk/app-release.apk`

Build time: ~6-12 minutes

---

**Version**: v3-lite
**Status**: ✅ Ready (minimal)
**APK**: ~50MB
**Tools**: 12 essential
**Offline**: 100%

**Best for limited storage and older devices!** 🪶
