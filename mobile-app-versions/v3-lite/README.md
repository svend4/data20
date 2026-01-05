# Data20 Mobile App

Native mobile application for Data20 Knowledge Base built with Flutter.

## Features

✅ **Cross-Platform**:
- iOS (iPhone, iPad)
- Android (phones, tablets)
- Shared codebase (~95%)

✅ **Native UI**:
- Material Design 3
- Adaptive widgets
- Platform-specific behaviors
- Smooth animations

✅ **Core Functionality**:
- JWT authentication
- Tools catalog with search/filters
- Job execution (placeholder)
- Job history (placeholder)
- Offline storage

✅ **Mobile Optimizations**:
- Touch-optimized UI
- Pull-to-refresh
- Responsive grid layouts
- Secure storage for tokens

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

1. Create keystore:
```bash
keytool -genkey -v -keystore ~/data20-release.jks -keyalg RSA -keysize 2048 -validity 10000 -alias data20
```

2. Configure `android/key.properties`:
```properties
storePassword=<password>
keyPassword=<password>
keyAlias=data20
storeFile=/path/to/data20-release.jks
```

3. Build:
```bash
flutter build appbundle
```

4. Upload to Google Play Console

### Apple App Store

1. Create App ID in Apple Developer portal
2. Create provisioning profile
3. Configure signing in Xcode
4. Archive in Xcode
5. Upload to App Store Connect

## License

Same as Data20 Knowledge Base project.

## Support

- Documentation: https://github.com/data20/docs
- Issues: https://github.com/data20/issues
