# 📱 Version 1: Original Phase 6.8 Baseline

## ⚠️ PRESERVED - DO NOT MODIFY

This version is the **original Phase 6.8 baseline** and must NOT be modified.
It serves as a reference point for all other versions.

---

## 📊 Version Information

- **Version**: v1-original
- **Commit**: f024a89
- **Phase**: 6.8 - Native Mobile App with Flutter
- **Date**: 2026-01-03
- **Status**: ✅ FROZEN (no changes allowed)

---

## 🏗️ Architecture

### Technology Stack
- **Frontend**: Flutter 3.16.0
- **Backend**: External FastAPI server (VPS/Cloud)
- **Database**: PostgreSQL (external)
- **Authentication**: JWT tokens
- **Communication**: HTTP REST API

### Backend Location
- **Type**: External server
- **Host**: Configured via API_BASE_URL
- **Port**: 8000 (configurable)
- **Protocol**: HTTPS in production

### Data Flow
```
Mobile App (Flutter)
    ↓ HTTP/HTTPS
External Server (VPS)
    ↓
FastAPI Backend
    ↓
PostgreSQL Database
```

---

## 📦 What's Included

### Files
- 13 Dart files
- 1 pubspec.yaml
- 1 README.md
- 1 .gitignore

### Features
✅ User authentication (login/logout)
✅ Tool listing and categories
✅ Job execution and monitoring
✅ Job history and results
✅ User profile management
✅ Material Design 3 UI
✅ Dark/Light theme
✅ Responsive layout

### NOT Included
❌ Embedded Python backend
❌ Offline functionality
❌ Local database
❌ Tools embedded in APK
❌ Platform channels
❌ Native code (Kotlin/Swift)

---

## 📊 Technical Specifications

### APK Size
- **Size**: ~20MB
- **Breakdown**:
  - Flutter runtime: ~15MB
  - App code: ~5MB

### System Requirements
- **Android**: 7.0+ (API 24)
- **iOS**: 12.0+
- **RAM**: 1GB
- **Storage**: 50MB
- **Internet**: ✅ Required (always)

### Offline Capability
- **Offline**: 0%
- **Reason**: All functionality requires external server

---

## 🔧 Build Instructions

### Prerequisites
- Flutter SDK 3.16.0+
- Android SDK (for Android)
- Xcode (for iOS)

### Build APK
```bash
cd mobile-app-versions/v1-original
flutter pub get
flutter build apk --release
```

APK location: `build/app/outputs/flutter-apk/app-release.apk`

### Build iOS
```bash
cd mobile-app-versions/v1-original
flutter pub get
flutter build ios --release
```

---

## 🎯 Use Cases

### When to Use v1-original

✅ **Testing external backend integration**
- Verify API endpoints
- Test server connectivity
- Validate authentication flow

✅ **Comparing with other versions**
- Baseline for feature comparison
- Performance benchmarking
- Size comparison

✅ **Learning/Reference**
- Study original architecture
- Understand Flutter basics
- See clean codebase

### When NOT to Use

❌ **Production deployment**
- Use v4-standard or v5-full instead

❌ **Offline scenarios**
- Use v3-lite, v4-standard, or v5-full

❌ **Feature development**
- Use v6-experimental or v7-debug

---

## 📁 File Structure

```
v1-original/
├── .gitignore
├── README.md
├── VERSION_INFO.md          # This file
├── pubspec.yaml             # Flutter dependencies
└── lib/
    ├── main.dart            # App entry point
    ├── models/              # Data models
    │   ├── tool.dart
    │   ├── job.dart
    │   └── user.dart
    ├── screens/             # UI screens
    │   ├── login_screen.dart
    │   ├── tools_screen.dart
    │   ├── jobs_screen.dart
    │   └── profile_screen.dart
    ├── services/            # API services
    │   └── api_service.dart
    └── widgets/             # Reusable widgets
        ├── tool_card.dart
        └── job_card.dart
```

---

## 🔄 Migration

### From v1-original to Other Versions

**To v2-hybrid**: Add SQLite cache for offline viewing
**To v3-lite**: Add embedded backend with 10-15 tools
**To v4-standard**: Add embedded backend with 30-35 tools
**To v5-full**: Add embedded backend with all 57 tools

See migration guides in respective version folders.

---

## 📝 Configuration

### API Endpoint

Edit `lib/services/api_service.dart`:

```dart
class ApiService {
  static const String baseUrl = 'https://your-server.com:8000';
  // Change to your backend server URL
}
```

### Authentication

Default credentials (configured on server):
- Username: `admin`
- Password: `admin`

---

## 🐛 Known Limitations

1. **No offline support** - Requires constant internet connection
2. **External dependency** - Requires running backend server
3. **Network latency** - Performance depends on connection quality
4. **Server costs** - Requires VPS/Cloud hosting

---

## 📚 Related Documentation

- **Architecture**: See [PHASE_6_8_MOBILE.md](../../docs/PHASE_6_8_MOBILE.md)
- **Technology Levels**: See [TECH_LEVELS_ANALYSIS.md](../../docs/TECH_LEVELS_ANALYSIS.md)
- **Full Audit**: See [GIT_AUDIT_FULL.md](../../docs/GIT_AUDIT_FULL.md)

---

## ⚠️ Important Notes

### PRESERVATION POLICY

🔒 **This version is FROZEN and must NOT be modified**

**Do NOT**:
- ❌ Add new features
- ❌ Update dependencies
- ❌ Refactor code
- ❌ Fix bugs (except critical security issues)

**Reason**: This serves as the baseline reference for all other versions.

### For Development

Use these versions instead:
- **v6-experimental**: For new features
- **v7-debug**: For debugging and testing
- **v5-full**: For production deployment

---

## 📜 License

MIT License - Same as main project

---

## 📊 Comparison with Current Version

| Feature | v1-original | v5-full (Current) |
|---------|-------------|-------------------|
| APK Size | ~20MB | ~100MB |
| Backend | External | Embedded |
| Offline | 0% | 100% |
| Tools | 0 embedded | 57 embedded |
| Internet Required | Yes | No |
| Python Runtime | No | Yes (~30MB) |
| Database | PostgreSQL (external) | SQLite (embedded) |
| Complexity | Low | High |

---

**Version**: v1-original
**Status**: ✅ PRESERVED
**Purpose**: Reference baseline
**Last Update**: 2026-01-03 (Phase 6.8)
**Modification Policy**: ❌ Read-Only

---

**For modifications, use v6-experimental or v7-debug instead.**
