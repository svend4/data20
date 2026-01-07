/// App Variant Configuration
/// Determines which variant of the app is running: Lite, Standard, or Full
///
/// This is used to:
/// - Show appropriate UI indicators
/// - Filter available tools
/// - Display variant-specific information

enum AppVariant {
  lite,
  standard,
  full,
}

class AppVariantConfig {
  /// Get current app variant from build-time constant
  static AppVariant get variant {
    const variantName = String.fromEnvironment(
      'APP_VARIANT',
      defaultValue: 'full',
    );

    switch (variantName.toLowerCase()) {
      case 'lite':
        return AppVariant.lite;
      case 'standard':
        return AppVariant.standard;
      case 'full':
      default:
        return AppVariant.full;
    }
  }

  /// Get display name for current variant
  static String get displayName {
    switch (variant) {
      case AppVariant.lite:
        return 'Data20 Lite';
      case AppVariant.standard:
        return 'Data20 Standard';
      case AppVariant.full:
        return 'Data20';
    }
  }

  /// Get variant description
  static String get description {
    switch (variant) {
      case AppVariant.lite:
        return 'Облегчённая версия с 12 основными инструментами';
      case AppVariant.standard:
        return 'Стандартная версия с 35 основными инструментами';
      case AppVariant.full:
        return 'Полная версия со всеми 57 инструментами';
    }
  }

  /// Get expected tool count
  static int get toolCount {
    switch (variant) {
      case AppVariant.lite:
        return 12;
      case AppVariant.standard:
        return 35;
      case AppVariant.full:
        return 57;
    }
  }

  /// Get variant color (for UI indicators)
  static int get variantColor {
    switch (variant) {
      case AppVariant.lite:
        return 0xFF9C27B0; // Purple
      case AppVariant.standard:
        return 0xFF2196F3; // Blue
      case AppVariant.full:
        return 0xFF4CAF50; // Green
    }
  }

  /// Get variant icon emoji
  static String get variantIcon {
    switch (variant) {
      case AppVariant.lite:
        return '⚡';
      case AppVariant.standard:
        return '⭐';
      case AppVariant.full:
        return '💎';
    }
  }

  /// Check if current variant is Lite
  static bool get isLite => variant == AppVariant.lite;

  /// Check if current variant is Standard
  static bool get isStandard => variant == AppVariant.standard;

  /// Check if current variant is Full
  static bool get isFull => variant == AppVariant.full;

  /// Get app size estimate (in MB)
  static int get estimatedSize {
    switch (variant) {
      case AppVariant.lite:
        return 45;
      case AppVariant.standard:
        return 65;
      case AppVariant.full:
        return 95;
    }
  }

  /// Get variant badge text for UI
  static String get badgeText {
    switch (variant) {
      case AppVariant.lite:
        return 'LITE';
      case AppVariant.standard:
        return 'STANDARD';
      case AppVariant.full:
        return 'FULL';
    }
  }

  /// Should show upgrade prompt?
  static bool get shouldShowUpgradePrompt {
    // Lite and Standard can show upgrade prompts
    return variant == AppVariant.lite || variant == AppVariant.standard;
  }

  /// Get upgrade target
  static String? get upgradeTarget {
    switch (variant) {
      case AppVariant.lite:
        return 'Standard версию с 35 инструментами';
      case AppVariant.standard:
        return 'Full версию со всеми 57 инструментами';
      case AppVariant.full:
        return null; // No upgrade available
    }
  }

  /// Debug info
  static String get debugInfo {
    return '''
App Variant: ${variant.name}
Display Name: $displayName
Tool Count: $toolCount
Size: ~${estimatedSize} MB
Badge: $badgeText
Can Upgrade: $shouldShowUpgradePrompt
''';
  }

  /// Print variant info to console
  static void printVariantInfo() {
    print('========================================');
    print('$variantIcon $displayName');
    print('========================================');
    print('Variant: ${variant.name.toUpperCase()}');
    print('Description: $description');
    print('Tools: $toolCount');
    print('Size: ~${estimatedSize} MB');
    print('========================================');
  }
}
