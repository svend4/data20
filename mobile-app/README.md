# Data20 Mobile App

Native mobile application for Data20 Knowledge Base built with Flutter with **embedded Python backend**.

## 🚀 Key Features

✅ **100% Offline Operation**:
- Embedded Python 3.9 runtime
- FastAPI backend on device (127.0.0.1:8001)
- SQLite database
- No internet required after installation

✅ **57+ Data Processing Tools**:
- Analysis, indexing, search
- Visualization, export
- All work offline

✅ **Cross-Platform**:
- Android 7.0+ (API 24)
- iOS support (in development)

✅ **Modern UI**:
- Material Design 3
- Dark/Light theme
- Adaptive widgets
- Touch-optimized

## 📚 Documentation

### Quick Links

- **[📱 PUBLISH_APK.md](PUBLISH_APK.md)** - Complete guide for building and publishing APK
- **[🔑 KEYSTORE_SETUP.md](KEYSTORE_SETUP.md)** - Keystore creation and signing configuration
- **[🏗️ BUILD_MOBILE_EMBEDDED.md](BUILD_MOBILE_EMBEDDED.md)** - Build guide for embedded Python version
- **[📥 Root: DOWNLOAD_APK.md](../DOWNLOAD_APK.md)** - User guide for installing APK
- **[📋 Root: RELEASE_NOTES.md](../RELEASE_NOTES.md)** - Release notes and changelog

### Documentation Summary

| Document | Purpose | Audience |
|----------|---------|----------|
| **PUBLISH_APK.md** | How to build, sign and publish APK to GitHub Releases or Google Play Store | Developers |
| **KEYSTORE_SETUP.md** | Keystore generation, signing setup, security best practices | Developers |
| **BUILD_MOBILE_EMBEDDED.md** | Technical details of building with Chaquopy and embedded Python | Developers |
| **DOWNLOAD_APK.md** | Installation guide and user manual | End Users |
| **RELEASE_NOTES.md** | What's included, features, requirements | End Users |

## 🚀 Quick Start

### For Users: Install APK

See **[DOWNLOAD_APK.md](../DOWNLOAD_APK.md)** for installation instructions.

### For Developers: Build Release APK

#### Option 1: Unsigned APK (for testing)

```bash
cd mobile-app
./build-android-embedded.sh release
# APK: build/app/outputs/flutter-apk/app-release.apk
```

#### Option 2: Signed APK (for publishing)

```bash
# 1. Create keystore (first time only)
cd android
keytool -genkey -v -keystore data20-release-key.jks \
  -keyalg RSA -keysize 2048 -validity 10000 \
  -alias data20-release

# 2. Create key.properties
cat > key.properties << 'EOF'
storePassword=YOUR_PASSWORD
keyPassword=YOUR_PASSWORD
keyAlias=data20-release
storeFile=data20-release-key.jks
EOF

# 3. Build signed APK
cd ..
./build-android-embedded.sh release
```

**See [PUBLISH_APK.md](PUBLISH_APK.md) for complete instructions.**

## Architecture

```
mobile-app/
├── lib/
│   ├── main.dart           # App entry point
│   ├── models/             # Data models
│   │   ├── user.dart
│   │   ├── tool.dart
│   │   └── job.dart
│   ├── services/           # Business logic
│   │   ├── api_service.dart
│   │   ├── auth_service.dart
│   │   └── storage_service.dart
│   ├── screens/            # UI screens
│   │   ├── login_screen.dart
│   │   ├── home_screen.dart
│   │   ├── tool_detail_screen.dart   # Placeholder
│   │   ├── jobs_screen.dart          # Placeholder
│   │   └── job_detail_screen.dart    # Placeholder
│   └── utils/
│       └── theme.dart      # App theme
├── android/                # Android native code
├── ios/                    # iOS native code
├── assets/                 # Images, fonts
└── pubspec.yaml            # Dependencies
```

## Prerequisites

- Flutter SDK 3.0+
- Dart 3.0+
- Android Studio (for Android)
- Xcode (for iOS, macOS only)
- Data20 backend running

## Installation

### 1. Install Flutter

Follow official guide: https://docs.flutter.dev/get-started/install

### 2. Verify Installation

```bash
flutter doctor
```

Should show:
- ✅ Flutter SDK
- ✅ Android toolchain (if developing for Android)
- ✅ Xcode (if developing for iOS)
- ✅ VS Code or Android Studio

### 3. Get Dependencies

```bash
cd mobile-app
flutter pub get
```

## Development

### Run on Emulator/Simulator

```bash
# Start backend first
cd ..
python run_standalone.py

# Start Flutter app (iOS simulator)
cd mobile-app
flutter run

# Or specify device
flutter run -d <device-id>

# List available devices
flutter devices
```

### Run on Physical Device

**Android**:
1. Enable Developer Options on phone
2. Enable USB Debugging
3. Connect via USB
4. Run `flutter run`

**iOS**:
1. Connect iPhone via USB
2. Trust computer on device
3. Run `flutter run`
4. May need Apple Developer account

### Hot Reload

While app is running:
- Press `r` to hot reload
- Press `R` to hot restart
- Press `q` to quit

### Backend Configuration

Default backend URL: `http://localhost:8001`

To change (in app):
- Use settings screen (TODO)
- Or modify `StorageService` default

For physical devices, use computer IP:
```dart
// In storage_service.dart
String get backendUrl {
  return getString('backend_url') ?? 'http://192.168.1.100:8001';
}
```

## Building

### Android APK (Debug)

```bash
flutter build apk
```

Output: `build/app/outputs/flutter-apk/app-release.apk`

### Android App Bundle (Release)

```bash
flutter build appbundle
```

Output: `build/app/outputs/bundle/release/app-release.aab`

For Google Play Store.

### iOS (Requires macOS + Xcode)

```bash
flutter build ios
```

Then open Xcode:
```bash
open ios/Runner.xcworkspace
```

Archive and distribute from Xcode.

## Dependencies

### Core
- `flutter`: SDK
- `provider`: State management
- `go_router`: Navigation

### HTTP & API
- `http`: Simple HTTP client
- `dio`: Advanced HTTP client (optional)

### Storage
- `shared_preferences`: Key-value storage
- `flutter_secure_storage`: Secure token storage

### Auth
- `jwt_decoder`: JWT token parsing

### UI
- `flutter_spinkit`: Loading indicators
- `cached_network_image`: Image caching
- `intl`: Internationalization

### Forms
- `flutter_form_builder`: Form helpers
- `form_builder_validators`: Validation

## Current Implementation Status

✅ **Complete**:
- Project structure
- Data models (User, Tool, Job)
- API service (full backend integration)
- Auth service (login, register, logout)
- Storage service (tokens, settings)
- Theme (Material Design 3)
- Login screen (full implementation)
- Home screen (full implementation)
- Routing (go_router)

🚧 **Placeholder**:
- Tool Detail screen
- Jobs List screen
- Job Detail screen
- Settings screen

## Extending

### Add New Screen

1. Create file in `lib/screens/my_screen.dart`
2. Add route in `lib/main.dart`:

```dart
GoRoute(
  path: '/my-route',
  builder: (context, state) => const MyScreen(),
),
```

### Add New Service

1. Create file in `lib/services/my_service.dart`
2. Add to providers in `main.dart`:

```dart
Provider(create: (_) => MyService()),
```

### Access Service

```dart
// Read once
final myService = context.read<MyService>();

// Watch for changes
final myService = context.watch<MyService>();
```

## Troubleshooting

### "Backend not reachable"

**Problem**: App can't connect to backend

**Solutions**:
1. Check backend is running
2. On emulator: use `http://10.0.2.2:8001` (Android) or `http://localhost:8001` (iOS)
3. On physical device: use computer's IP address
4. Check firewall allows connections

### Build errors

**Clear cache**:
```bash
flutter clean
flutter pub get
flutter run
```

### iOS signing issues

Need Apple Developer account ($99/year) for:
- Physical device testing (free account works for 7 days)
- App Store distribution

### Android build fails

Check:
- Java version (Java 11+ required)
- Android SDK installed
- `ANDROID_HOME` environment variable set

## Testing

### Unit Tests

```bash
flutter test
```

### Widget Tests

```bash
flutter test test/widget_test.dart
```

### Integration Tests

```bash
flutter test integration_test/
```

## Publishing

### Google Play Store

See **[PUBLISH_APK.md](PUBLISH_APK.md)** for complete publishing guide including:
- Keystore setup and signing
- Building signed APK/AAB
- Preparing store listing
- Upload process
- Automated CI/CD with GitHub Actions

Quick summary:
1. Create Google Play Developer account ($25)
2. Build signed AAB: `flutter build appbundle --release`
3. Upload to Play Console
4. Fill in store listing details
5. Submit for review (1-3 days)

### Direct Distribution (GitHub Releases)

See **[PUBLISH_APK.md](PUBLISH_APK.md)** for instructions on:
- Creating GitHub releases
- Uploading signed APK
- Automated builds via GitHub Actions

Quick summary:
1. Create release on GitHub: https://github.com/svend4/data20/releases/new
2. Upload signed APK as asset
3. Users download and install manually

### Signing Configuration

See **[KEYSTORE_SETUP.md](KEYSTORE_SETUP.md)** for detailed keystore setup.

⚠️ **Important**: 
- Keep keystore file secure (never commit to Git)
- Backup keystore and passwords
- Losing keystore means you cannot update your app!

## 🔒 Security

- ✅ Keystore files excluded from Git (.gitignore)
- ✅ ProGuard rules configured for code obfuscation
- ✅ Secure storage for JWT tokens
- ✅ All Python code embedded (not exposed)
- ✅ Backend runs locally (127.0.0.1 only)

## 📦 APK Information

**Size**: ~100MB (includes embedded Python runtime and tools)

**What's included**:
- Python 3.9 runtime (~30MB)
- FastAPI backend (~10MB)
- 57 data processing tools (~40MB)
- Flutter app (~20MB)

**Requirements**:
- Android 7.0+ (API 24)
- ~150MB storage
- ~300MB RAM

## License

Same as Data20 Knowledge Base project.

## 🤖 Automated CI/CD

### Automatic APK Build

✅ **GitHub Actions автоматически собирает APK** при:
- Push в ветки `main`, `master`, `claude/**`
- Создании GitHub Release
- Ручном запуске через UI

**Как использовать**:

1. **Автоматическая сборка** - просто сделайте push:
   ```bash
   git push origin your-branch
   # APK соберется автоматически через ~10 минут
   ```

2. **Ручной запуск** - откройте GitHub Actions и запустите workflow

3. **Скачать APK**:
   - Из Actions → Artifacts (хранится 90 дней)
   - Из Releases (при создании release)

**Документация**:
- **[АВТОСБОРКА_APK.md](../АВТОСБОРКА_APK.md)** - полное руководство
- **[БЫСТРЫЙ_СТАРТ_АВТОСБОРКИ.md](../БЫСТРЫЙ_СТАРТ_АВТОСБОРКИ.md)** - краткая инструкция

**Проверить статус сборки**: https://github.com/svend4/data20/actions

---

_Последнее обновление: 2026-01-04 | Автосборка настроена и работает_

## Support

- **Build Issues**: [GitHub Issues](https://github.com/svend4/data20/issues)
- **User Guide**: [DOWNLOAD_APK.md](../DOWNLOAD_APK.md)
- **Developer Docs**: [PUBLISH_APK.md](PUBLISH_APK.md)
- **Автосборка**: [АВТОСБОРКА_APK.md](../АВТОСБОРКА_APK.md)
