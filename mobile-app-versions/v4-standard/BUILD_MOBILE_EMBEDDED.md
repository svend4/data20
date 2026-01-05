# Building Mobile App with Embedded Python Backend

Complete guide for building Data20 mobile application with embedded FastAPI backend for **100% offline operation**.

---

## 📋 Overview

This guide covers building mobile applications with **Python backend embedded directly in the app**:

- **Android**: Using Chaquopy to run Python on Android
- **iOS**: Using PythonKit to run Python on iOS (experimental)

**Result**: Fully self-contained mobile app that works offline without external server.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│  Mobile App                             │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │  Flutter UI (Dart)                │  │
│  │  • Login, Tools, Jobs screens     │  │
│  │  • BackendService client          │  │
│  └────────────┬──────────────────────┘  │
│               │ Platform Channel        │
│  ┌────────────▼──────────────────────┐  │
│  │  Native Bridge (Kotlin/Swift)     │  │
│  │  • Start/stop backend             │  │
│  │  • Status monitoring              │  │
│  └────────────┬──────────────────────┘  │
│               │                         │
│  ┌────────────▼──────────────────────┐  │
│  │  Python Runtime                   │  │
│  │  • Chaquopy (Android)             │  │
│  │  • PythonKit (iOS)                │  │
│  └────────────┬──────────────────────┘  │
│               │                         │
│  ┌────────────▼──────────────────────┐  │
│  │  FastAPI Backend (Python)         │  │
│  │  • 127.0.0.1:8001                 │  │
│  │  • SQLite database                │  │
│  │  • All 57+ tools                  │  │
│  └───────────────────────────────────┘  │
│                                         │
└─────────────────────────────────────────┘
```

**Key Features**:
- Backend runs as subprocess inside mobile app
- No internet required after installation
- Full API compatibility with desktop/web versions
- SQLite for local data storage
- 100% privacy (all data stays on device)

---

## 📦 Android Build (Chaquopy)

### Requirements

**Software**:
- Java JDK 17+
- Android SDK (API 24+)
- Android NDK
- Flutter SDK
- Python 3.9+

**Licenses**:
- Chaquopy: $495/year for production (free for development with watermark)
- Google Play Developer: $25 one-time

### Installation

#### 1. Install Android SDK

```bash
# Option A: Android Studio (recommended)
# Download from: https://developer.android.com/studio

# Option B: Command-line tools
wget https://dl.google.com/android/repository/commandlinetools-linux-latest.zip
unzip commandlinetools-linux-latest.zip -d $HOME/android-sdk
export ANDROID_HOME=$HOME/android-sdk
```

#### 2. Install Flutter

```bash
# Download Flutter
git clone https://github.com/flutter/flutter.git -b stable --depth 1
export PATH="$PATH:`pwd`/flutter/bin"

# Verify installation
flutter doctor
```

#### 3. Configure Chaquopy License (Optional for Production)

```bash
# Purchase license from: https://chaquo.com/chaquopy/
# Then add to:
mkdir -p ~/.gradle/chaquopy
echo "YOUR_LICENSE_KEY" > ~/.gradle/chaquopy/license.txt
```

### Build Steps

#### Quick Build (Automated)

```bash
cd mobile-app

# Build release APK
./build-android-embedded.sh release

# Or debug APK
./build-android-embedded.sh debug

# Clean build
./build-android-embedded.sh release clean
```

#### Manual Build

```bash
# 1. Get dependencies
flutter pub get

# 2. Build APK (includes Python compilation)
flutter build apk --release

# Output: build/app/outputs/flutter-apk/app-release.apk
```

### Build Configuration

**android/app/build.gradle** key settings:

```gradle
chaquopy {
    defaultConfig {
        // Python version
        version "3.9"

        // Pip packages (automatically installed)
        pip {
            install "fastapi==0.104.1"
            install "uvicorn==0.24.0"
            // ... other dependencies
        }
    }
}
```

### APK Size

- **Without Python**: ~20MB
- **With Python**: ~100MB

Python runtime adds ~80MB:
- Python interpreter: ~30MB
- Pip packages: ~50MB

### Testing

```bash
# Install APK on device
adb install build/app/outputs/flutter-apk/app-release.apk

# View logs
adb logcat | grep -E "MainActivity|Python|Backend"

# Check backend status
# In app: Navigate to "Backend Status" screen
```

### Troubleshooting

**Issue: "Chaquopy requires license"**
```bash
# For development: build continues with watermark
# For production: purchase license from https://chaquo.com/
```

**Issue: "Python module not found"**
```bash
# Verify module is in pip dependencies in build.gradle
# Clean and rebuild:
flutter clean
cd android && ./gradlew clean && cd ..
flutter build apk --release
```

**Issue: APK too large**
```bash
# Reduce size by removing unused packages
# Edit android/app/build.gradle pip dependencies
# Remove: pandas, numpy (if not needed)
# Result: ~60MB APK
```

---

## 🍎 iOS Build (PythonKit)

### ⚠️ Important Warning

**PythonKit is EXPERIMENTAL** and has limitations:
- iOS App Store may reject embedded Python apps
- Limited Python package support
- Performance issues on iOS
- Not recommended for production

**Recommendation**: Use cloud backend for production iOS apps.

### Requirements

**Software**:
- macOS (required)
- Xcode 14+
- CocoaPods
- Flutter SDK
- Python 3.9+

**Licenses**:
- Apple Developer Account: $99/year

### Installation

#### 1. Install Xcode

```bash
# Download from App Store or:
xcode-select --install
```

#### 2. Install CocoaPods

```bash
sudo gem install cocoapods
```

#### 3. Install Flutter

```bash
# Same as Android section
flutter doctor
```

### Build Steps

#### Quick Build (Automated)

```bash
cd mobile-app

# Build release IPA
./build-ios-embedded.sh release

# Or debug build
./build-ios-embedded.sh debug

# Clean build
./build-ios-embedded.sh release clean
```

#### Manual Build

```bash
# 1. Get dependencies
flutter pub get

# 2. Install pods
cd ios
pod install
cd ..

# 3. Build IPA
flutter build ipa --release

# Output: build/ios/archive/Runner.xcarchive
```

### Distribution

#### TestFlight (Recommended)

```bash
# 1. Open Xcode Organizer
open build/ios/archive/*.xcarchive

# 2. Click "Distribute App"
# 3. Select "App Store Connect"
# 4. Upload to TestFlight
# 5. Invite testers
```

#### Ad Hoc Distribution

```bash
# 1. Open Xcode Organizer
# 2. Click "Distribute App"
# 3. Select "Ad Hoc"
# 4. Export IPA
# 5. Share IPA with users (max 100 devices)
```

### App Store Submission

**Prepare for Review**:

1. **Review Notes**: Explain why Python is embedded
2. **Justification**: Offline functionality, data privacy
3. **Demo Video**: Show backend status screen
4. **Fallback Plan**: Be prepared for rejection

**If Rejected**: Consider these alternatives:
- Use cloud backend for iOS
- Rewrite tools in Dart
- Use Pythonista (iOS Python IDE) as reference

---

## 🔧 Development Workflow

### Local Development

```bash
# 1. Start Flutter in debug mode (without building full APK)
cd mobile-app
flutter run

# 2. Backend will auto-start on app launch (see main.dart)

# 3. Hot reload works
# Press 'r' in terminal to reload

# 4. View logs
# Android: adb logcat
# iOS: Xcode console
```

### Testing Backend

```bash
# 1. Open Backend Status screen in app

# 2. Or test directly with curl (if backend running)
curl http://127.0.0.1:8001/health

# Response:
# {"status":"ok","environment":"mobile","version":"1.0.0"}
```

### Debugging

**Android**:
```bash
# View all logs
adb logcat

# Filter backend logs
adb logcat | grep Backend

# Filter Python logs
adb logcat -s python
```

**iOS**:
```bash
# Open Xcode
# Window > Devices and Simulators
# Select device > Open Console
```

---

## 📊 Comparison: Embedded vs Cloud Backend

| Feature | Embedded Backend | Cloud Backend |
|---------|------------------|---------------|
| **Offline** | ✅ 100% offline | ❌ Requires internet |
| **Privacy** | ✅ All local | ⚠️ Data sent to server |
| **Speed** | ✅ No latency | ⚠️ Network latency |
| **APK Size** | ❌ ~100MB | ✅ ~20MB |
| **Startup** | ⚠️ 5-7 seconds | ✅ Instant |
| **Updates** | ⚠️ Requires app update | ✅ Server-side updates |
| **Costs** | ✅ $0/month | ⚠️ $50-150/month server |
| **iOS Support** | ⚠️ Experimental | ✅ Full support |
| **Maintenance** | ✅ No server | ⚠️ Server maintenance |

**Recommendation**:
- **Android**: Embedded backend works well
- **iOS**: Cloud backend recommended
- **Hybrid**: Embedded for Android, Cloud for iOS

---

## 🚀 Production Deployment

### Android (Google Play)

#### 1. Prepare Release

```bash
# Create signing key
keytool -genkey -v -keystore data20-release-key.jks \
  -keyalg RSA -keysize 2048 -validity 10000 \
  -alias data20

# Add to android/key.properties
storePassword=YOUR_PASSWORD
keyPassword=YOUR_PASSWORD
keyAlias=data20
storeFile=/path/to/data20-release-key.jks
```

#### 2. Build Signed APK

```bash
# Configure signing in android/app/build.gradle
# Then build
./build-android-embedded.sh release
```

#### 3. Upload to Play Store

1. Go to Google Play Console
2. Create app listing
3. Upload APK
4. Fill out store listing
5. Submit for review

**Review Time**: 1-3 days

### iOS (App Store)

#### 1. Prepare App

```bash
# Build IPA
./build-ios-embedded.sh release
```

#### 2. Upload to App Store Connect

```bash
# Open Xcode Organizer
open build/ios/archive/*.xcarchive

# Distribute App > App Store Connect
```

#### 3. Submit for Review

1. Fill out App Store Connect listing
2. **Important**: Add review notes explaining Python usage
3. Submit for review
4. **Be prepared**: May be rejected

**Review Time**: 1-7 days

---

## 📝 File Structure

```
mobile-app/
├── android/
│   ├── app/
│   │   ├── build.gradle                    # Chaquopy configuration
│   │   ├── proguard-chaquopy.pro           # ProGuard rules
│   │   ├── src/main/
│   │   │   ├── AndroidManifest.xml         # Permissions
│   │   │   ├── kotlin/com/data20/mobile_app/
│   │   │   │   └── MainActivity.kt         # Native bridge
│   │   │   └── python/
│   │   │       ├── backend_main.py         # Python backend wrapper
│   │   │       └── requirements.txt        # Python dependencies
│   │   └── ...
│   └── build.gradle                        # Top-level Gradle config
│
├── ios/
│   ├── Podfile                             # PythonKit dependency
│   └── Runner/
│       ├── AppDelegate.swift               # Method channel handler
│       └── BackendBridge.swift             # Python backend bridge
│
├── lib/
│   ├── main.dart                           # App entry (with backend start)
│   ├── services/
│   │   └── backend_service.dart            # Platform channel client
│   └── screens/
│       └── backend_status_screen.dart      # Backend diagnostic UI
│
├── build-android-embedded.sh               # Android build script
├── build-ios-embedded.sh                   # iOS build script
└── BUILD_MOBILE_EMBEDDED.md                # This file
```

---

## 🎯 Next Steps

### After Successful Build

1. **Test thoroughly**
   - Backend status screen
   - All tools functionality
   - Offline mode
   - Battery usage
   - Memory consumption

2. **Optimize**
   - Remove unused Python packages
   - Reduce APK/IPA size
   - Improve startup time
   - Add loading indicators

3. **Deploy**
   - TestFlight (iOS)
   - Internal testing (Android)
   - Beta testers
   - Production release

### Alternative: Dart Backend

If Python embedded causes issues, consider **rewriting backend in Dart**:

**Pros**:
- Native Flutter integration
- Smaller app size (~30MB)
- Faster startup
- iOS App Store friendly
- No special licenses

**Cons**:
- Need to rewrite 57+ tools
- Lose Python ecosystem
- 2-3 months development

---

## 💡 Tips & Best Practices

### Performance

```dart
// Lazy start backend (don't auto-start)
// Comment out in main.dart:
// await backendService.startBackend();

// Start only when needed (first API call)
backendService.apiRequest('/tools', autoStart: true);
```

### Battery Optimization

```kotlin
// Stop backend when app goes to background
// In MainActivity.kt:
override fun onPause() {
    super.onPause()
    stopBackend(...)
}
```

### Crash Reporting

```dart
// Add error handling
try {
  await backendService.startBackend();
} catch (e) {
  // Log to Firebase Crashlytics
  FirebaseCrashlytics.instance.recordError(e, stack);
}
```

---

## 📚 Resources

**Chaquopy**:
- Website: https://chaquo.com/chaquopy/
- Documentation: https://chaquo.com/chaquopy/doc/current/
- GitHub: https://github.com/chaquo/chaquopy

**PythonKit**:
- GitHub: https://github.com/pvieito/PythonKit
- Issues: https://github.com/pvieito/PythonKit/issues

**Flutter**:
- Platform Channels: https://docs.flutter.dev/platform-integration/platform-channels
- Method Channels: https://api.flutter.dev/flutter/services/MethodChannel-class.html

**Alternative**:
- Python-iOS: https://github.com/beeware/Python-iOS-support
- BeeWare: https://beeware.org/ (Python apps on mobile)

---

## 🐛 Known Issues

### Android

1. **Large APK size** (~100MB)
   - **Solution**: Remove unused packages, use app bundles

2. **Slow startup** (5-7 seconds)
   - **Solution**: Add splash screen, lazy start backend

3. **Memory usage** (~300MB)
   - **Solution**: Stop backend when in background

### iOS

1. **PythonKit experimental**
   - **Solution**: Use cloud backend for production

2. **App Store rejection risk**
   - **Solution**: Provide detailed review notes, or use cloud backend

3. **Limited package support**
   - **Solution**: Test all dependencies, have fallback plan

---

## ✅ Checklist for Production

Before releasing to production:

**Android**:
- [ ] Chaquopy license purchased
- [ ] All tools tested on real device
- [ ] Battery usage profiled
- [ ] Memory usage acceptable
- [ ] APK size optimized
- [ ] ProGuard rules configured
- [ ] Signing key secured
- [ ] Google Play listing ready

**iOS**:
- [ ] Tested on real device (not just simulator)
- [ ] App Store review notes prepared
- [ ] Backup cloud backend ready
- [ ] TestFlight testing completed
- [ ] Privacy policy updated
- [ ] Screenshots prepared
- [ ] Alternative plan if rejected

**Both**:
- [ ] Backend status screen works
- [ ] Offline mode verified
- [ ] Crash reporting integrated
- [ ] Analytics configured
- [ ] User documentation written
- [ ] Support channels ready

---

**Phase 7.3: Mobile Embedded Backend - Full Implementation Complete!** 🎉
