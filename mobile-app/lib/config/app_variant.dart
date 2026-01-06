/// App Variant Configuration
/// Phase 8.2.2: Detects and manages app variant (lite/standard/full)

enum AppVariant {
  lite,
  standard,
  full,
}

class AppVariantConfig {
  static AppVariant? _detectedVariant;

  /// Get the current app variant
  static AppVariant get variant {
    if (_detectedVariant != null) {
      return _detectedVariant!;
    }

    // Try to detect variant from build configuration
    _detectedVariant = _detectVariant();
    return _detectedVariant!;
  }

  /// Detect variant from build configuration
  static AppVariant _detectVariant() {
    // In production, this will read from BuildConfig
    // For now, we'll use a constant (will be set by Gradle)

    // This constant will be replaced by Gradle build flavors
    // using --dart-define or generated code
    const String variantName = String.fromEnvironment(
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

  /// Get variant display name
  static String getDisplayName(AppVariant variant) {
    switch (variant) {
      case AppVariant.lite:
        return 'Lite';
      case AppVariant.standard:
        return 'Standard';
      case AppVariant.full:
        return 'Full';
    }
  }

  /// Get variant description
  static String getDescription(AppVariant variant) {
    switch (variant) {
      case AppVariant.lite:
        return '12 core tools, optimized for size';
      case AppVariant.standard:
        return '35 essential tools for most users';
      case AppVariant.full:
        return '57 tools - complete feature set';
    }
  }

  /// Get expected tool count for variant
  static int getToolCount(AppVariant variant) {
    switch (variant) {
      case AppVariant.lite:
        return 12;
      case AppVariant.standard:
        return 35;
      case AppVariant.full:
        return 57;
    }
  }

  /// Get expected app size for variant
  static String getAppSize(AppVariant variant) {
    switch (variant) {
      case AppVariant.lite:
        return '~45 MB';
      case AppVariant.standard:
        return '~65 MB';
      case AppVariant.full:
        return '~95 MB';
    }
  }

  /// Check if upgrade is available
  static bool canUpgrade(AppVariant variant) {
    return variant != AppVariant.full;
  }

  /// Get next variant for upgrade
  static AppVariant? getNextVariant(AppVariant variant) {
    switch (variant) {
      case AppVariant.lite:
        return AppVariant.standard;
      case AppVariant.standard:
        return AppVariant.full;
      case AppVariant.full:
        return null;
    }
  }

  /// Get upgrade message
  static String getUpgradeMessage(AppVariant currentVariant) {
    final nextVariant = getNextVariant(currentVariant);
    if (nextVariant == null) {
      return 'You have the full version';
    }

    final nextName = getDisplayName(nextVariant);
    final nextTools = getToolCount(nextVariant);

    return 'Upgrade to $nextName for $nextTools tools';
  }

  /// Get variant color
  static int getColor(AppVariant variant) {
    switch (variant) {
      case AppVariant.lite:
        return 0xFF9B59B6; // Purple
      case AppVariant.standard:
        return 0xFF3498DB; // Blue
      case AppVariant.full:
        return 0xFF27AE60; // Green
    }
  }

  /// Get variant icon
  static String getIcon(AppVariant variant) {
    switch (variant) {
      case AppVariant.lite:
        return '⚡'; // Lightning - fast and light
      case AppVariant.standard:
        return '⭐'; // Star - standard
      case AppVariant.full:
        return '💎'; // Diamond - premium
    }
  }

  /// Get variant badge text
  static String getBadge(AppVariant variant) {
    return '${getIcon(variant)} ${getDisplayName(variant)}';
  }

  /// Check if a tool is available in current variant
  /// This will be populated from the backend's tool registry
  static bool isToolAvailable(String toolName) {
    // In production, this will check against the backend's
    // tool registry which knows about variant restrictions
    // For now, assume all tools are available
    return true;
  }

  /// Get info map for variant
  static Map<String, dynamic> getVariantInfo(AppVariant variant) {
    return {
      'variant': variant.toString().split('.').last,
      'display_name': getDisplayName(variant),
      'description': getDescription(variant),
      'tool_count': getToolCount(variant),
      'app_size': getAppSize(variant),
      'can_upgrade': canUpgrade(variant),
      'next_variant': getNextVariant(variant)?.toString().split('.').last,
      'upgrade_message': getUpgradeMessage(variant),
      'color': getColor(variant),
      'icon': getIcon(variant),
      'badge': getBadge(variant),
    };
  }
}

/// Extension to get variant information
extension AppVariantExtension on AppVariant {
  String get displayName => AppVariantConfig.getDisplayName(this);
  String get description => AppVariantConfig.getDescription(this);
  int get toolCount => AppVariantConfig.getToolCount(this);
  String get appSize => AppVariantConfig.getAppSize(this);
  bool get canUpgrade => AppVariantConfig.canUpgrade(this);
  AppVariant? get nextVariant => AppVariantConfig.getNextVariant(this);
  String get upgradeMessage => AppVariantConfig.getUpgradeMessage(this);
  int get color => AppVariantConfig.getColor(this);
  String get icon => AppVariantConfig.getIcon(this);
  String get badge => AppVariantConfig.getBadge(this);

  Map<String, dynamic> get info => AppVariantConfig.getVariantInfo(this);
}
