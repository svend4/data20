#!/usr/bin/env python3
"""
App Variant Configuration
Phase 8.2.2: Defines tool availability and dependencies for each app variant
"""

from typing import Dict, List, Set
from enum import Enum


class AppVariant(str, Enum):
    """App variant types"""
    LITE = "lite"
    STANDARD = "standard"
    FULL = "full"


class DependencyLevel(str, Enum):
    """Dependency complexity levels"""
    CORE = "core"          # Available in all variants (FastAPI, basic utils)
    LIGHT = "light"        # Available in standard+ (numpy, openpyxl, lxml)
    HEAVY = "heavy"        # Only in full (pandas, Pillow)


# ============================================================================
# DEPENDENCY MAPPING
# ============================================================================

TOOL_DEPENDENCIES: Dict[str, DependencyLevel] = {
    # Core tools (no heavy dependencies) - LITE
    "calculate_reading_time": DependencyLevel.CORE,
    "validate": DependencyLevel.CORE,
    "metadata_validator": DependencyLevel.CORE,
    "search_index": DependencyLevel.CORE,
    "advanced_search": DependencyLevel.CORE,
    "faceted_search": DependencyLevel.CORE,
    "find_duplicates": DependencyLevel.CORE,
    "find_orphans": DependencyLevel.CORE,
    "find_related": DependencyLevel.CORE,
    "backlinks_generator": DependencyLevel.CORE,
    "export_manager": DependencyLevel.CORE,
    "tags_cloud": DependencyLevel.CORE,

    # Light dependencies (numpy, lxml, openpyxl) - STANDARD
    "generate_statistics": DependencyLevel.LIGHT,
    "statistics_dashboard": DependencyLevel.LIGHT,
    "quality_metrics": DependencyLevel.LIGHT,
    "calculate_difficulty": DependencyLevel.LIGHT,
    "build_concordance": DependencyLevel.LIGHT,
    "build_glossary": DependencyLevel.LIGHT,
    "build_thesaurus": DependencyLevel.LIGHT,
    "build_taxonomy": DependencyLevel.LIGHT,
    "master_index": DependencyLevel.LIGHT,
    "citation_index": DependencyLevel.LIGHT,
    "generate_bibliography": DependencyLevel.LIGHT,
    "generate_toc": DependencyLevel.LIGHT,
    "generate_breadcrumbs": DependencyLevel.LIGHT,
    "sitemap_generator": DependencyLevel.LIGHT,
    "summary_generator": DependencyLevel.LIGHT,
    "auto_tagger": DependencyLevel.LIGHT,
    "weighted_tags": DependencyLevel.LIGHT,
    "duplicate_detector": DependencyLevel.LIGHT,
    "check_links": DependencyLevel.LIGHT,
    "external_links_tracker": DependencyLevel.LIGHT,
    "recent_changes": DependencyLevel.LIGHT,
    "version_history": DependencyLevel.LIGHT,
    "generate_changelog": DependencyLevel.LIGHT,

    # Heavy dependencies (pandas, Pillow, full numpy) - FULL
    "build_graph": DependencyLevel.HEAVY,
    "knowledge_graph_builder": DependencyLevel.HEAVY,
    "graph_visualizer": DependencyLevel.HEAVY,
    "network_analyzer": DependencyLevel.HEAVY,
    "calculate_pagerank": DependencyLevel.HEAVY,
    "prerequisites_graph": DependencyLevel.HEAVY,
    "cross_references": DependencyLevel.HEAVY,
    "chain_references": DependencyLevel.HEAVY,
    "related_articles": DependencyLevel.HEAVY,
    "popular_articles": DependencyLevel.HEAVY,
    "timeline_generator": DependencyLevel.HEAVY,
    "archive_builder": DependencyLevel.HEAVY,
    "build_card_catalog": DependencyLevel.HEAVY,
    "commonplace_book": DependencyLevel.HEAVY,
    "marginalia": DependencyLevel.HEAVY,
    "reading_progress": DependencyLevel.HEAVY,
    "search_concordance": DependencyLevel.HEAVY,
    "index_figures": DependencyLevel.HEAVY,
    "add_dewey": DependencyLevel.HEAVY,
    "add_rubrics": DependencyLevel.HEAVY,
    "process_inbox": DependencyLevel.HEAVY,
    "update_indexes": DependencyLevel.HEAVY,
}


# ============================================================================
# VARIANT TOOL COUNTS
# ============================================================================

VARIANT_TOOL_COUNTS = {
    AppVariant.LITE: 12,
    AppVariant.STANDARD: 35,
    AppVariant.FULL: 57,
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_available_tools(variant: AppVariant) -> Set[str]:
    """
    Get list of tools available in a specific variant

    Args:
        variant: App variant (lite/standard/full)

    Returns:
        Set of tool names available in this variant
    """
    available = set()

    for tool_name, dep_level in TOOL_DEPENDENCIES.items():
        if variant == AppVariant.LITE:
            # Lite: only core tools
            if dep_level == DependencyLevel.CORE:
                available.add(tool_name)

        elif variant == AppVariant.STANDARD:
            # Standard: core + light
            if dep_level in (DependencyLevel.CORE, DependencyLevel.LIGHT):
                available.add(tool_name)

        elif variant == AppVariant.FULL:
            # Full: all tools
            available.add(tool_name)

    return available


def is_tool_available(tool_name: str, variant: AppVariant) -> bool:
    """
    Check if a tool is available in a specific variant

    Args:
        tool_name: Name of the tool
        variant: App variant

    Returns:
        True if tool is available in this variant
    """
    return tool_name in get_available_tools(variant)


def get_upgrade_prompt(tool_name: str, current_variant: AppVariant) -> str:
    """
    Get upgrade prompt message if tool is not available

    Args:
        tool_name: Name of the tool
        current_variant: Current app variant

    Returns:
        Upgrade prompt message or empty string
    """
    if tool_name not in TOOL_DEPENDENCIES:
        return ""

    dep_level = TOOL_DEPENDENCIES[tool_name]

    if current_variant == AppVariant.LITE:
        if dep_level == DependencyLevel.LIGHT:
            return f"⬆️ Upgrade to Standard version to use {tool_name}"
        elif dep_level == DependencyLevel.HEAVY:
            return f"⬆️ Upgrade to Full version to use {tool_name}"

    elif current_variant == AppVariant.STANDARD:
        if dep_level == DependencyLevel.HEAVY:
            return f"⬆️ Upgrade to Full version to use {tool_name}"

    return ""


def get_variant_info(variant: AppVariant) -> Dict[str, any]:
    """
    Get comprehensive information about a variant

    Args:
        variant: App variant

    Returns:
        Dictionary with variant information
    """
    available_tools = get_available_tools(variant)

    # Categorize tools by dependency level
    core_tools = [t for t in available_tools if TOOL_DEPENDENCIES.get(t) == DependencyLevel.CORE]
    light_tools = [t for t in available_tools if TOOL_DEPENDENCIES.get(t) == DependencyLevel.LIGHT]
    heavy_tools = [t for t in available_tools if TOOL_DEPENDENCIES.get(t) == DependencyLevel.HEAVY]

    return {
        "variant": variant.value,
        "total_tools": len(available_tools),
        "expected_tools": VARIANT_TOOL_COUNTS[variant],
        "tool_breakdown": {
            "core": len(core_tools),
            "light": len(light_tools),
            "heavy": len(heavy_tools),
        },
        "available_tools": sorted(list(available_tools)),
        "can_upgrade": variant != AppVariant.FULL,
        "next_variant": {
            AppVariant.LITE: AppVariant.STANDARD,
            AppVariant.STANDARD: AppVariant.FULL,
            AppVariant.FULL: None,
        }.get(variant),
    }


def detect_variant() -> AppVariant:
    """
    Detect current app variant from environment or build config

    Returns:
        Detected app variant (defaults to FULL if not detected)
    """
    import os

    # Try to detect from environment variable (set by Gradle)
    variant_env = os.environ.get("APP_VARIANT", "").lower()

    if variant_env == "lite":
        return AppVariant.LITE
    elif variant_env == "standard":
        return AppVariant.STANDARD
    else:
        # Default to FULL for backward compatibility
        return AppVariant.FULL


# ============================================================================
# VALIDATION
# ============================================================================

def validate_configuration():
    """Validate that tool counts match expected values"""

    errors = []
    warnings = []

    for variant in AppVariant:
        available = get_available_tools(variant)
        expected = VARIANT_TOOL_COUNTS[variant]
        actual = len(available)

        if actual != expected:
            warnings.append(
                f"{variant.value}: Expected {expected} tools, got {actual}"
            )

    # Check for tools not in dependency mapping
    all_defined_tools = set(TOOL_DEPENDENCIES.keys())
    full_tools = get_available_tools(AppVariant.FULL)

    if len(full_tools) != len(all_defined_tools):
        warnings.append(
            f"Defined {len(all_defined_tools)} tools but FULL variant has {len(full_tools)}"
        )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }


# CLI for testing
if __name__ == "__main__":
    print("=" * 70)
    print("📱 App Variant Configuration")
    print("=" * 70)

    for variant in AppVariant:
        info = get_variant_info(variant)
        print(f"\n{variant.value.upper()} Variant:")
        print(f"  Tools: {info['total_tools']} (expected: {info['expected_tools']})")
        print(f"  Breakdown: {info['tool_breakdown']}")

        if info['can_upgrade']:
            print(f"  Upgrade to: {info['next_variant'].value}")

    print("\n" + "=" * 70)
    print("Validation:")
    print("=" * 70)

    validation = validate_configuration()
    if validation['valid']:
        print("✅ Configuration is valid")
    else:
        print("❌ Configuration has errors:")
        for error in validation['errors']:
            print(f"  - {error}")

    if validation['warnings']:
        print("\n⚠️ Warnings:")
        for warning in validation['warnings']:
            print(f"  - {warning}")

    # Test tool availability
    print("\n" + "=" * 70)
    print("Example Tool Availability:")
    print("=" * 70)

    test_tools = ["calculate_reading_time", "generate_statistics", "build_graph"]

    for tool in test_tools:
        print(f"\n{tool}:")
        for variant in AppVariant:
            available = is_tool_available(tool, variant)
            status = "✅" if available else "❌"
            print(f"  {status} {variant.value}")

            if not available:
                prompt = get_upgrade_prompt(tool, variant)
                if prompt:
                    print(f"     {prompt}")
