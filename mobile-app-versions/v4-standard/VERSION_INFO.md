# 📱 Version 4: Standard Edition (Recommended)

## ⭐ Balanced Mobile App - Best for Most Users

This is the **recommended version** with embedded Python backend and 35 carefully selected essential tools.

---

## 📊 Version Information

- **Version**: v4-standard
- **Based on**: v5-full (Phase 7.3)
- **Status**: ✅ Recommended for Production
- **Purpose**: Balanced functionality and size

---

## ⭐ Why Choose v4-standard?

**Best balance of features and size** - covers 90% of use cases with:
- 35 essential tools (vs 57 in v5-full)
- 70MB APK (vs 100MB in v5-full)
- 100% offline capability
- Better performance than v5
- Lower RAM usage

---

## 📊 Technical Specifications

### APK Size: ~70MB
- Python 3.9 runtime: ~30MB
- FastAPI + dependencies: ~10MB  
- 35 data tools: ~20MB
- Flutter app: ~10MB

### System Requirements
- Android 7.0+ (API 24)
- RAM: 1.5GB (recommended 3GB)
- Storage: 100MB
- Internet: NOT required

### Performance
- First launch: 4-6 seconds
- Subsequent launches: 1-2 seconds
- Battery usage: ~4-8% per hour

---

## 📦 What's Included: 35 Essential Tools

### Core Indexing (9 tools)
- build_taxonomy.py
- build_glossary.py
- build_thesaurus.py
- build_concordance.py
- citation_index.py
- auto_tagger.py
- index_figures.py
- add_dewey.py
- add_rubrics.py

### Search & Navigation (9 tools)
- advanced_search.py
- faceted_search.py
- find_related.py
- generate_toc.py
- generate_breadcrumbs.py
- cross_references.py
- backlinks_generator.py
- chain_references.py
- build_card_catalog.py

### Analysis & Statistics (5 tools)
- generate_statistics.py
- calculate_pagerank.py
- calculate_reading_time.py
- calculate_difficulty.py
- knowledge_graph_builder.py

### Visualization & Export (5 tools)
- build_graph.py
- graph_visualizer.py
- generate_bibliography.py
- export_manager.py
- generate_changelog.py

### Validation & Quality (7 tools)
- duplicate_detector.py
- find_duplicates.py
- check_links.py
- find_orphans.py
- external_links_tracker.py
- validate.py
- archive_builder.py

---

## 🎯 Use Cases

### ✅ When to Use v4-standard

- **Most production deployments** - Best balance
- **General users** - All essential tools
- **Medium workflows** - 90% of use cases covered
- **Mid-range devices** - 2-3GB RAM
- **Limited storage** - 100MB total

### ❌ When NOT to Use

- **Power users** → Use v5-full (57 tools)
- **Very limited storage** → Use v3-lite (50MB)
- **Testing** → Use v7-debug

---

## 📊 Comparison with Other Versions

| Metric | v4-standard | v5-full |
|--------|-------------|---------|
| APK Size | 70MB | 100MB |
| Tools | 35 | 57 |
| Startup | 4-6s | 5-7s |
| RAM | 1.5GB | 2GB |
| Battery/hr | 4-8% | 5-10% |
| **Recommendation** | ⭐ Best for most | Power users |

---

## 🔧 Build Instructions

```bash
cd mobile-app-versions/v4-standard
./build-android-embedded.sh release
```

APK location: `build/app/outputs/flutter-apk/app-release.apk`

Build time: ~8-15 minutes (first build)

---

## 📚 Documentation

- Full Build Guide: `BUILD_MOBILE_EMBEDDED.md`
- Architecture: `PHASE_7_3_MOBILE_EMBEDDED.md`
- Technology Analysis: `TECH_LEVELS_ANALYSIS.md`
- Full Audit: `GIT_AUDIT_FULL.md`

---

**Version**: v4-standard
**Status**: ⭐ Recommended  
**APK**: ~70MB
**Tools**: 35 essential
**Offline**: 100%

**This is the recommended version for most users!** ⭐
