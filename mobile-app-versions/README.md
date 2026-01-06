# 📱 Data20 Mobile App - All Versions

This directory contains **7 different versions** of the Data20 mobile app, each optimized for different use cases.

---

## 🎯 Quick Version Selector

Choose your version based on your needs:

| If you need... | Use version |
|---------------|-------------|
| **Reference/baseline only** | v1-original |
| **Cloud + offline viewing** | v2-hybrid |
| **Smallest embedded** | v3-lite |
| **⭐ Best for most users** | **v4-standard** |
| **Maximum functionality** | v5-full |
| **Beta features** | v6-experimental |
| **Development/debugging** | v7-debug |

---

## 📊 Complete Version Comparison

| Version | APK | Tools | Offline | RAM | Status | Use Case |
|---------|-----|-------|---------|-----|--------|----------|
| **v1-original** | 20MB | 0 | 0% | 1GB | ✅ Frozen | Reference baseline |
| **v2-hybrid** | 25MB | 0 | 40% | 1GB | ⚙️ Concept | Cloud + cache |
| **v3-lite** | 50MB | 12 | 100% | 1GB | ✅ Ready | Minimal embedded |
| **v4-standard** ⭐ | 70MB | 35 | 100% | 1.5GB | ✅ Recommended | Balanced |
| **v5-full** | 100MB | 57 | 100% | 2GB | ✅ Production | Maximum features |
| **v6-experimental** | 150MB | 60+ | 100% | 3GB | ⚠️ Beta | Testing new features |
| **v7-debug** | 110MB | 57+debug | 100% | 2GB | 🔧 Dev only | Development |

---

## 📱 Version Details

### v1-original (Baseline)

**DO NOT MODIFY** - This is the preserved Phase 6.8 baseline.

- **APK**: 20MB
- **Backend**: External (cloud server required)
- **Offline**: 0% (needs internet always)
- **Purpose**: Reference point for all other versions
- **Status**: ✅ Frozen (read-only)

**Use for**: Comparison, understanding original architecture, baseline reference

See: [v1-original/VERSION_INFO.md](v1-original/VERSION_INFO.md)

---

### v2-hybrid (Cloud + Cache)

Hybrid approach with external backend + local cache.

- **APK**: 25MB
- **Backend**: External + SQLite cache
- **Offline**: 40% (viewing cached data)
- **Purpose**: Bridge between v1 and v3
- **Status**: ⚙️ Conceptual (requires implementation)

**Use for**: Intermittent connectivity, gradual migration to offline

See: [v2-hybrid/VERSION_INFO.md](v2-hybrid/VERSION_INFO.md)

---

### v3-lite (Minimal Embedded)

Smallest version with embedded backend and essential tools.

- **APK**: 50MB
- **Backend**: Embedded Python
- **Tools**: 12 essential tools
- **Offline**: 100%
- **Purpose**: Small APK, basic offline functionality
- **Status**: ✅ Production ready

**12 Essential Tools**:
- build_taxonomy, build_glossary, build_thesaurus
- advanced_search, find_related, generate_toc
- generate_statistics, generate_bibliography, export_manager
- duplicate_detector, check_links, validate

**Use for**: Limited storage, older devices, simple workflows

See: [v3-lite/VERSION_INFO.md](v3-lite/VERSION_INFO.md)

---

### v4-standard ⭐ (Recommended)

**RECOMMENDED FOR MOST USERS** - Best balance of features and size.

- **APK**: 70MB
- **Backend**: Embedded Python
- **Tools**: 35 essential tools
- **Offline**: 100%
- **Purpose**: Balanced functionality and size
- **Status**: ✅ Recommended for production

**35 Essential Tools** covering:
- Core Indexing (9): Taxonomy, glossary, thesaurus, concordance, citations, etc.
- Search & Navigation (9): Advanced search, faceted search, TOC, breadcrumbs, etc.
- Analysis & Statistics (5): Statistics, PageRank, reading time, difficulty, knowledge graph
- Visualization & Export (5): Graphs, visualizations, bibliography, export, changelog
- Validation & Quality (7): Duplicates, link checking, orphans, validation, archives

**Use for**: General users, medium workflows, mid-range devices (2-3GB RAM)

See: [v4-standard/VERSION_INFO.md](v4-standard/VERSION_INFO.md)

---

### v5-full (Complete Edition)

Current production version with all tools and features.

- **APK**: 100MB
- **Backend**: Embedded Python
- **Tools**: All 57 tools
- **Offline**: 100%
- **Purpose**: Maximum functionality
- **Status**: ✅ Production ready

**All 57 Tools** across:
- Analysis (15 tools)
- Indexing (12 tools)
- Search (8 tools)
- Visualization (10 tools)
- Validation (12 tools)

**Use for**: Power users, complex workflows, enterprise scenarios, research

See: [v5-full/VERSION_INFO.md](v5-full/VERSION_INFO.md)

---

### v6-experimental (Beta Features)

v5-full + experimental/beta tools and features.

- **APK**: 150MB
- **Backend**: Embedded Python
- **Tools**: 60+ (57 stable + experimental)
- **Offline**: 100%
- **Purpose**: Testing new features
- **Status**: ⚠️ Beta (unstable)

**Experimental Features** (conceptual):
- AI/ML tools (summarization, classification, semantic analysis)
- Advanced analytics (predictive, sentiment, topic modeling)
- Integrations (cloud sync, API connectors, webhooks)

**Use for**: Developers, beta testers, researchers, advanced users

⚠️ **WARNING**: May be unstable, not for production!

See: [v6-experimental/VERSION_INFO.md](v6-experimental/VERSION_INFO.md)

---

### v7-debug (Development)

v5-full + extensive debugging and development tools.

- **APK**: 110MB
- **Backend**: Embedded Python
- **Tools**: 57 + debug tools
- **Offline**: 100%
- **Purpose**: Debugging and development
- **Status**: 🔧 Development only

**Debug Features**:
- Verbose logging (all API calls, DB queries)
- Performance profiling
- Memory tracking
- API inspector UI
- Database browser
- Log viewer screen

**Use for**: Developers, debugging issues, performance optimization

⚠️ **WARNING**: Slower, larger logs, not for end users!

See: [v7-debug/VERSION_INFO.md](v7-debug/VERSION_INFO.md)

---

## 🚀 Getting Started

### 1. Choose Your Version

Use the comparison table above to select the right version for your needs.

**Most users should start with v4-standard** ⭐

### 2. Build the APK

```bash
cd mobile-app-versions/v4-standard  # or your chosen version
./build-android-embedded.sh release
```

### 3. Install on Device

```bash
adb install build/app/outputs/flutter-apk/app-release.apk
```

Or copy APK to device and install manually.

### 4. First Launch

1. Open app (~3-7 seconds first launch)
2. Login: `admin` / `admin`
3. ⚠️ Change password immediately!
4. Verify Backend Status (Menu → Backend Status)

---

## 📊 Build Requirements

| Version | Build Time | Disk Space | RAM (build) |
|---------|-----------|------------|-------------|
| v1-original | 5-10 min | 5GB | 4GB |
| v2-hybrid | 5-10 min | 5GB | 4GB |
| v3-lite | 6-12 min | 8GB | 6GB |
| v4-standard | 8-15 min | 10GB | 8GB |
| v5-full | 10-20 min | 15GB | 8GB |
| v6-experimental | 15-25 min | 18GB | 10GB |
| v7-debug | 10-20 min | 15GB | 8GB |

**Common Requirements**:
- Flutter SDK 3.16.0+
- Android SDK (API 24+)
- Java JDK 17+
- Python 3.9+

---

## 🔄 Migration Paths

### Upgrading

```
v1-original → v2-hybrid → v3-lite → v4-standard → v5-full
```

**From v1 to v4**: Major change (external → embedded backend)
**From v3 to v4**: Add 23 tools (~20MB)
**From v4 to v5**: Add 22 tools (~30MB)

### Downgrading

Simply install lower version APK. Data may need migration.

---

## 📁 Directory Structure

```
mobile-app-versions/
├── README.md                    # This file
├── v1-original/                 # Phase 6.8 baseline (PRESERVED)
│   ├── VERSION_INFO.md
│   ├── lib/                     # 13 Dart files
│   └── pubspec.yaml
├── v2-hybrid/                   # Cloud + cache (conceptual)
│   ├── VERSION_INFO.md
│   └── ...
├── v3-lite/                     # 12 tools, 50MB
│   ├── VERSION_INFO.md
│   ├── android/app/src/main/python/tools/  # 12 tools
│   └── ...
├── v4-standard/                 # 35 tools, 70MB ⭐
│   ├── VERSION_INFO.md
│   ├── android/app/src/main/python/tools/  # 35 tools
│   └── ...
├── v5-full/                     # 57 tools, 100MB
│   ├── VERSION_INFO.md
│   ├── android/app/src/main/python/tools/  # 57 tools
│   └── ...
├── v6-experimental/             # 60+ tools, 150MB (beta)
│   ├── VERSION_INFO.md
│   └── ...
└── v7-debug/                    # 57 + debug, 110MB
    ├── VERSION_INFO.md
    └── ...
```

---

## 🎯 Recommendations by Use Case

### For End Users

| Scenario | Recommended Version |
|----------|-------------------|
| General use, medium workflows | **v4-standard** ⭐ |
| Power user, need all features | v5-full |
| Limited storage (<100MB) | v3-lite |
| Older device (<2GB RAM) | v3-lite |

### For Developers

| Scenario | Recommended Version |
|----------|-------------------|
| Production deployment | v4-standard or v5-full |
| Testing new features | v6-experimental |
| Debugging issues | v7-debug |
| Baseline reference | v1-original |

### For Different Devices

| Device Type | Recommended Version |
|-------------|-------------------|
| High-end (4GB+ RAM) | v5-full |
| Mid-range (2-3GB RAM) | **v4-standard** ⭐ |
| Budget (1-2GB RAM) | v3-lite |
| Very old (<1GB RAM) | v1-original (requires server) |

---

## ⚠️ Important Policies

### v1-original Preservation

🔒 **v1-original is FROZEN and must NEVER be modified**

**Reason**: It's the baseline reference for all other versions.

**For any changes**: Use v6-experimental or v7-debug instead.

### Version Management

- **Production code changes**: Make in v5-full first, then backport to v4
- **Testing/experimental**: Use v6-experimental
- **Debugging**: Use v7-debug
- **DO NOT modify v1-original** under any circumstances

---

## 📚 Documentation

### Version-Specific
- See `VERSION_INFO.md` in each version folder for details

### General Documentation
- **Build Guide**: [../mobile-app/BUILD_MOBILE_EMBEDDED.md](../mobile-app/BUILD_MOBILE_EMBEDDED.md)
- **Architecture**: [../docs/PHASE_7_3_MOBILE_EMBEDDED.md](../docs/PHASE_7_3_MOBILE_EMBEDDED.md)
- **Technology Levels**: [../docs/TECH_LEVELS_ANALYSIS.md](../docs/TECH_LEVELS_ANALYSIS.md)
- **Full Audit**: [../docs/GIT_AUDIT_FULL.md](../docs/GIT_AUDIT_FULL.md)

---

## 🤝 Contributing

### Adding New Features

1. **Develop in v6-experimental** first
2. **Test thoroughly**
3. **Stabilize in v7-debug**
4. **Merge to v5-full** when stable
5. **Consider backporting** to v4-standard if essential

### Bug Fixes

1. **Reproduce in v7-debug**
2. **Fix and test**
3. **Apply to v5-full**
4. **Backport to v4** if critical
5. **DO NOT touch v1-original**

---

## 📊 Statistics

### Total Code
- **v1-original**: ~2,500 lines
- **v5-full**: ~60,000 lines
- **Growth**: 24x increase

### Total Files
- **v1-original**: 17 files
- **v5-full**: 95 files
- **Growth**: 5.6x increase

### Development Time
- **Phase 6.8 (v1)**: 2 days
- **Phase 7.3 (v5)**: 5 days
- **All versions**: 7 days

---

## 📜 License

All versions: MIT License (same as main project)

---

## 🚀 Quick Links

- **Main Repository**: [../](../)
- **Mobile App (current)**: [../mobile-app/](../mobile-app/)
- **Documentation**: [../docs/](../docs/)
- **Issues**: [GitHub Issues](https://github.com/svend4/data20/issues)

---

**Created**: 2026-01-05
**Purpose**: Preserve original baseline and provide version alternatives
**Maintenance**: v1-original frozen, others actively developed

**Choose wisely and build great apps!** 🚀
