/**
 * Tool Registry
 * Phase 9.1.3: Port Tools to WebAssembly (10 tools)
 * Phase 9.2.2: Expanded to 35 tools (15 simple + 20 medium)
 *
 * Manages 35 of 57 total tools in Pyodide/WASM environment
 * - Simple tools: Fast execution (< 100ms)
 * - Medium tools: Moderate complexity (100ms - 1s)
 * - Complex tools: Cloud execution (deferred to Phase 9.2.3)
 */

export class ToolRegistry {
  constructor(pyodideManager) {
    this.pyodide = pyodideManager;
    this.tools = new Map();
    this.toolCategories = {
      text_analysis: [],
      search: [],
      statistics: [],
      validation: [],
      formatting: [],
      knowledge_graph: [],
      metadata: [],
      archive: []
    };
  }

  /**
   * Load all tools
   */
  async loadTools() {
    console.log('Loading tools into Pyodide...');

    // Load simple tools first (no heavy dependencies)
    await this.loadSimpleTools();

    // Load medium complexity tools
    await this.loadMediumTools();

    // Load heavy tools (optional, based on availability)
    await this.loadHeavyTools();

    console.log(`✅ Loaded ${this.tools.size} tools`);
  }

  /**
   * Load simple tools (no dependencies)
   * Phase 9.2: Expanded to 15 simple tools
   */
  async loadSimpleTools() {
    const simpleTools = [
      {
        name: 'calculate_reading_time',
        category: 'text_analysis',
        code: this.getReadingTimeCode(),
        dependencies: []
      },
      {
        name: 'count_words',
        category: 'text_analysis',
        code: this.getCountWordsCode(),
        dependencies: []
      },
      {
        name: 'format_text',
        category: 'formatting',
        code: this.getFormatTextCode(),
        dependencies: []
      },
      {
        name: 'validate_data',
        category: 'validation',
        code: this.getValidateDataCode(),
        dependencies: []
      },
      {
        name: 'calculate_difficulty',
        category: 'text_analysis',
        code: this.getCalculateDifficultyCode(),
        dependencies: []
      },
      {
        name: 'generate_toc',
        category: 'formatting',
        code: this.getGenerateTOCCode(),
        dependencies: []
      },
      {
        name: 'check_links',
        category: 'validation',
        code: this.getCheckLinksCode(),
        dependencies: []
      },
      {
        name: 'find_orphans',
        category: 'metadata',
        code: this.getFindOrphansCode(),
        dependencies: []
      },
      {
        name: 'metadata_validator',
        category: 'validation',
        code: this.getMetadataValidatorCode(),
        dependencies: []
      },
      {
        name: 'generate_breadcrumbs',
        category: 'formatting',
        code: this.getGenerateBreadcrumbsCode(),
        dependencies: []
      },
      {
        name: 'recent_changes',
        category: 'metadata',
        code: this.getRecentChangesCode(),
        dependencies: []
      },
      {
        name: 'reading_progress',
        category: 'statistics',
        code: this.getReadingProgressCode(),
        dependencies: []
      },
      {
        name: 'sitemap_generator',
        category: 'archive',
        code: this.getSitemapGeneratorCode(),
        dependencies: []
      },
      {
        name: 'version_history',
        category: 'metadata',
        code: this.getVersionHistoryCode(),
        dependencies: []
      },
      {
        name: 'tags_cloud',
        category: 'statistics',
        code: this.getTagsCloudCode(),
        dependencies: []
      }
    ];

    for (const tool of simpleTools) {
      await this.registerTool(tool);
    }
  }

  /**
   * Load medium complexity tools
   * Phase 9.2: Expanded to 20 medium tools
   */
  async loadMediumTools() {
    const mediumTools = [
      {
        name: 'extract_keywords',
        category: 'text_analysis',
        code: this.getExtractKeywordsCode(),
        dependencies: []
      },
      {
        name: 'detect_language',
        category: 'text_analysis',
        code: this.getDetectLanguageCode(),
        dependencies: []
      },
      {
        name: 'generate_statistics',
        category: 'statistics',
        code: this.getGenerateStatisticsCode(),
        dependencies: []
      },
      {
        name: 'search_index',
        category: 'search',
        code: this.getSearchIndexCode(),
        dependencies: []
      },
      {
        name: 'advanced_search',
        category: 'search',
        code: this.getAdvancedSearchCode(),
        dependencies: []
      },
      {
        name: 'find_related',
        category: 'search',
        code: this.getFindRelatedCode(),
        dependencies: []
      },
      {
        name: 'related_articles',
        category: 'search',
        code: this.getRelatedArticlesCode(),
        dependencies: []
      },
      {
        name: 'popular_articles',
        category: 'statistics',
        code: this.getPopularArticlesCode(),
        dependencies: []
      },
      {
        name: 'quality_metrics',
        category: 'statistics',
        code: this.getQualityMetricsCode(),
        dependencies: []
      },
      {
        name: 'weighted_tags',
        category: 'statistics',
        code: this.getWeightedTagsCode(),
        dependencies: []
      },
      {
        name: 'summary_generator',
        category: 'text_analysis',
        code: this.getSummaryGeneratorCode(),
        dependencies: []
      },
      {
        name: 'duplicate_detector',
        category: 'validation',
        code: this.getDuplicateDetectorCode(),
        dependencies: []
      },
      {
        name: 'build_concordance',
        category: 'text_analysis',
        code: this.getBuildConcordanceCode(),
        dependencies: []
      },
      {
        name: 'build_glossary',
        category: 'text_analysis',
        code: this.getBuildGlossaryCode(),
        dependencies: []
      },
      {
        name: 'citation_index',
        category: 'metadata',
        code: this.getCitationIndexCode(),
        dependencies: []
      },
      {
        name: 'master_index',
        category: 'archive',
        code: this.getMasterIndexCode(),
        dependencies: []
      },
      {
        name: 'statistics_dashboard',
        category: 'statistics',
        code: this.getStatisticsDashboardCode(),
        dependencies: []
      },
      {
        name: 'timeline_generator',
        category: 'formatting',
        code: this.getTimelineGeneratorCode(),
        dependencies: []
      },
      {
        name: 'generate_bibliography',
        category: 'formatting',
        code: this.getGenerateBibliographyCode(),
        dependencies: []
      },
      {
        name: 'faceted_search',
        category: 'search',
        code: this.getFacetedSearchCode(),
        dependencies: []
      }
    ];

    for (const tool of mediumTools) {
      await this.registerTool(tool);
    }
  }

  /**
   * Load heavy tools (optional)
   */
  async loadHeavyTools() {
    // These tools require heavier dependencies
    // Load only if requested or if packages are available

    const heavyTools = [
      // Will be added as we port more complex tools
    ];

    for (const tool of heavyTools) {
      try {
        await this.registerTool(tool);
      } catch (error) {
        console.warn(`Skipping heavy tool ${tool.name}:`, error.message);
      }
    }
  }

  /**
   * Register a tool
   */
  async registerTool(toolConfig) {
    try {
      // Install dependencies
      for (const dep of toolConfig.dependencies) {
        if (!this.pyodide.isPackageInstalled(dep)) {
          await this.pyodide.installPackage(dep);
        }
      }

      // Load tool code
      await this.pyodide.loadModule(toolConfig.name, toolConfig.code);

      // Register tool
      this.tools.set(toolConfig.name, {
        name: toolConfig.name,
        category: toolConfig.category,
        dependencies: toolConfig.dependencies
      });

      // Add to category
      if (this.toolCategories[toolConfig.category]) {
        this.toolCategories[toolConfig.category].push(toolConfig.name);
      }

      console.log(`  ✅ Registered tool: ${toolConfig.name}`);

    } catch (error) {
      console.error(`Failed to register tool ${toolConfig.name}:`, error);
      throw error;
    }
  }

  /**
   * Execute a tool
   */
  async executeTool(toolName, parameters) {
    if (!this.tools.has(toolName)) {
      throw new Error(`Tool not found: ${toolName}`);
    }

    try {
      // Set parameters as Python variables
      this.pyodide.setVariable('tool_params', parameters);

      // Execute tool
      const code = `
import ${toolName}
result = ${toolName}.execute(tool_params)
result
`;

      const result = await this.pyodide.runPython(code);

      return result;

    } catch (error) {
      console.error(`Tool execution failed (${toolName}):`, error);
      throw error;
    }
  }

  /**
   * Get tool info
   */
  getToolInfo(toolName) {
    return this.tools.get(toolName);
  }

  /**
   * Get all tools
   */
  getTools() {
    return Array.from(this.tools.values());
  }

  /**
   * Get tools by category
   */
  getToolsByCategory(category) {
    return this.toolCategories[category] || [];
  }

  /**
   * Get tool count
   */
  getToolCount() {
    return this.tools.size;
  }

  // ==================== TOOL IMPLEMENTATIONS ====================

  /**
   * Calculate Reading Time Tool
   */
  getReadingTimeCode() {
    return `
def execute(params):
    """Calculate reading time for text"""
    text = params.get('text', '')

    if not text:
        return {
            'reading_time_minutes': 0,
            'word_count': 0
        }

    # Count words
    words = text.split()
    word_count = len(words)

    # Average reading speed: 200 words per minute
    reading_speed_wpm = 200
    reading_time_minutes = max(1, word_count / reading_speed_wpm)

    return {
        'reading_time_minutes': round(reading_time_minutes),
        'word_count': word_count,
        'reading_speed_wpm': reading_speed_wpm
    }
`;
  }

  /**
   * Count Words Tool
   */
  getCountWordsCode() {
    return `
import re
from collections import Counter

def execute(params):
    """Count words in text"""
    text = params.get('text', '')

    if not text:
        return {
            'total_words': 0,
            'unique_words': 0,
            'word_counts': {}
        }

    # Normalize text
    text = text.lower()
    text = re.sub(r'[^a-z0-9\\s]', '', text)

    # Split into words
    words = text.split()

    # Count words
    word_counts = Counter(words)

    return {
        'total_words': len(words),
        'unique_words': len(word_counts),
        'word_counts': dict(word_counts.most_common(20))
    }
`;
  }

  /**
   * Format Text Tool
   */
  getFormatTextCode() {
    return `
def execute(params):
    """Format text"""
    text = params.get('text', '')
    format_type = params.get('format_type', 'uppercase')

    if not text:
        return {'formatted_text': ''}

    if format_type == 'uppercase':
        result = text.upper()
    elif format_type == 'lowercase':
        result = text.lower()
    elif format_type == 'title':
        result = text.title()
    elif format_type == 'capitalize':
        result = text.capitalize()
    elif format_type == 'trim':
        result = text.strip()
    elif format_type == 'normalize_spaces':
        import re
        result = re.sub(r'\\s+', ' ', text.strip())
    else:
        result = text

    return {'formatted_text': result}
`;
  }

  /**
   * Validate Data Tool
   */
  getValidateDataCode() {
    return `
import re

def execute(params):
    """Validate data"""
    data = params.get('data', '')
    validation_type = params.get('type', 'email')

    if validation_type == 'email':
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
        is_valid = bool(re.match(pattern, data))
    elif validation_type == 'url':
        pattern = r'^https?://[^\\s]+$'
        is_valid = bool(re.match(pattern, data))
    elif validation_type == 'json':
        import json
        try:
            json.loads(data)
            is_valid = True
        except:
            is_valid = False
    else:
        is_valid = False

    return {
        'is_valid': is_valid,
        'type': validation_type
    }
`;
  }

  /**
   * Calculate Difficulty Tool
   */
  getCalculateDifficultyCode() {
    return `
def execute(params):
    """Calculate text difficulty"""
    text = params.get('text', '')

    if not text:
        return {'difficulty_score': 0}

    # Simple difficulty calculation
    words = text.split()
    if not words:
        return {'difficulty_score': 0}

    # Average word length
    avg_word_length = sum(len(word) for word in words) / len(words)

    # Difficulty score (0-100)
    # Based on average word length
    difficulty_score = min(100, avg_word_length * 10)

    return {
        'difficulty_score': round(difficulty_score),
        'avg_word_length': round(avg_word_length, 2)
    }
`;
  }

  /**
   * Extract Keywords Tool
   */
  getExtractKeywordsCode() {
    return `
import re
from collections import Counter

def execute(params):
    """Extract keywords from text"""
    text = params.get('text', '')

    if not text:
        return {'keywords': []}

    # Normalize text
    text = text.lower()
    text = re.sub(r'[^a-z0-9\\s]', '', text)

    # Stop words (simple list)
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been', 'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}

    # Extract words
    words = text.split()

    # Filter out stop words and short words
    filtered_words = [w for w in words if w not in stop_words and len(w) > 3]

    # Count frequencies
    word_counts = Counter(filtered_words)

    # Get top keywords
    keywords = [word for word, count in word_counts.most_common(10)]

    return {'keywords': keywords}
`;
  }

  /**
   * Detect Language Tool
   */
  getDetectLanguageCode() {
    return `
def execute(params):
    """Detect language (simple implementation)"""
    text = params.get('text', '')

    if not text:
        return {'language': 'unknown', 'confidence': 0}

    # Very simple language detection based on character patterns
    # In production, would use a proper language detection library

    text_lower = text.lower()

    # Check for common words in different languages
    en_words = {'the', 'is', 'and', 'to', 'a', 'of', 'that', 'in', 'it', 'you'}
    ru_words = {'и', 'в', 'на', 'что', 'с', 'это', 'как', 'по', 'не', 'к'}

    words = set(text_lower.split())

    en_score = len(words & en_words)
    ru_score = len(words & ru_words)

    if en_score > ru_score:
        return {'language': 'en', 'confidence': 0.8}
    elif ru_score > en_score:
        return {'language': 'ru', 'confidence': 0.8}
    else:
        return {'language': 'unknown', 'confidence': 0.5}
`;
  }

  /**
   * Generate Statistics Tool
   */
  getGenerateStatisticsCode() {
    return `
def execute(params):
    """Generate statistics for numerical data"""
    data = params.get('data', [])

    if not data:
        return {
            'count': 0,
            'mean': 0,
            'median': 0,
            'min': 0,
            'max': 0
        }

    # Basic statistics
    count = len(data)
    mean_val = sum(data) / count
    sorted_data = sorted(data)

    # Median
    if count % 2 == 0:
        median_val = (sorted_data[count // 2 - 1] + sorted_data[count // 2]) / 2
    else:
        median_val = sorted_data[count // 2]

    return {
        'count': count,
        'mean': mean_val,
        'median': median_val,
        'min': min(data),
        'max': max(data)
    }
`;
  }

  /**
   * Search Index Tool
   */
  getSearchIndexCode() {
    return `
def execute(params):
    """Search through articles"""
    query = params.get('query', '').lower()
    articles = params.get('articles', [])

    if not query or not articles:
        return []

    results = []

    for article in articles:
        # Search in title and content
        title = article.get('title', '').lower()
        content = article.get('content', '').lower()

        if query in title or query in content:
            # Calculate relevance score
            score = 0
            if query in title:
                score += 2
            if query in content:
                score += 1

            results.append({
                **article,
                'relevance_score': score
            })

    # Sort by relevance
    results.sort(key=lambda x: x['relevance_score'], reverse=True)

    return results
`;
  }

  // ==================== NEW SIMPLE TOOLS (Phase 9.2) ====================

  /**
   * Generate TOC Tool
   */
  getGenerateTOCCode() {
    return `
import re

def execute(params):
    """Generate table of contents from markdown"""
    content = params.get('content', '')

    if not content:
        return {'toc': []}

    # Extract headings
    headings = re.findall(r'^(#{1,6})\\s+(.+)$', content, re.MULTILINE)

    toc = []
    for level_chars, text in headings:
        level = len(level_chars)
        anchor = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')

        toc.append({
            'level': level,
            'text': text.strip(),
            'anchor': anchor
        })

    return {'toc': toc}
`;
  }

  /**
   * Check Links Tool
   */
  getCheckLinksCode() {
    return `
import re

def execute(params):
    """Check markdown links"""
    content = params.get('content', '')

    if not content:
        return {'links': [], 'broken': []}

    # Find all links [text](url)
    links = re.findall(r'\\[([^\\]]+)\\]\\(([^)]+)\\)', content)

    all_links = []
    broken = []

    for text, url in links:
        link_info = {
            'text': text,
            'url': url,
            'type': 'external' if url.startswith('http') else 'internal'
        }

        all_links.append(link_info)

        # Check for broken patterns
        if url == '' or url == '#':
            broken.append(link_info)

    return {
        'links': all_links,
        'total': len(all_links),
        'broken': broken
    }
`;
  }

  /**
   * Find Orphans Tool
   */
  getFindOrphansCode() {
    return `
def execute(params):
    """Find articles with no incoming links"""
    articles = params.get('articles', [])

    # Track which articles are referenced
    referenced = set()

    for article in articles:
        links = article.get('links', [])
        for link in links:
            referenced.add(link)

    # Find orphans
    orphans = []
    for article in articles:
        article_id = article.get('id', article.get('path', ''))
        if article_id not in referenced:
            orphans.append(article)

    return {
        'orphans': orphans,
        'count': len(orphans)
    }
`;
  }

  /**
   * Metadata Validator Tool
   */
  getMetadataValidatorCode() {
    return `
def execute(params):
    """Validate frontmatter metadata"""
    metadata = params.get('metadata', {})
    schema = params.get('schema', {})

    errors = []
    warnings = []

    # Required fields
    required = schema.get('required', ['title', 'date'])
    for field in required:
        if field not in metadata or not metadata[field]:
            errors.append(f"Missing required field: {field}")

    # Validate types
    if 'title' in metadata and not isinstance(metadata['title'], str):
        errors.append("Title must be a string")

    if 'tags' in metadata and not isinstance(metadata['tags'], list):
        errors.append("Tags must be a list")

    # Warnings
    if 'tags' in metadata and len(metadata['tags']) < 3:
        warnings.append("Consider adding more tags (< 3)")

    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings
    }
`;
  }

  /**
   * Generate Breadcrumbs Tool
   */
  getGenerateBreadcrumbsCode() {
    return `
def execute(params):
    """Generate breadcrumbs from path"""
    path = params.get('path', '')

    if not path:
        return {'breadcrumbs': []}

    # Split path
    parts = path.strip('/').split('/')

    breadcrumbs = []
    current_path = ''

    for part in parts:
        current_path += '/' + part
        breadcrumbs.append({
            'name': part.replace('-', ' ').replace('_', ' ').title(),
            'path': current_path
        })

    return {'breadcrumbs': breadcrumbs}
`;
  }

  /**
   * Recent Changes Tool
   */
  getRecentChangesCode() {
    return `
from datetime import datetime, timedelta

def execute(params):
    """Find recently changed articles"""
    articles = params.get('articles', [])
    days = params.get('days', 7)

    # Calculate cutoff date
    cutoff = datetime.now() - timedelta(days=days)

    recent = []
    for article in articles:
        date_str = article.get('date', '')
        if date_str:
            try:
                article_date = datetime.fromisoformat(str(date_str))
                if article_date >= cutoff:
                    recent.append(article)
            except:
                pass

    # Sort by date (newest first)
    recent.sort(key=lambda x: x.get('date', ''), reverse=True)

    return {
        'recent': recent,
        'count': len(recent),
        'days': days
    }
`;
  }

  /**
   * Reading Progress Tool
   */
  getReadingProgressCode() {
    return `
def execute(params):
    """Track reading progress"""
    total_articles = params.get('total_articles', 0)
    read_articles = params.get('read_articles', 0)

    if total_articles == 0:
        return {'progress': 0, 'remaining': 0}

    progress = (read_articles / total_articles) * 100
    remaining = total_articles - read_articles

    return {
        'progress': round(progress, 1),
        'read': read_articles,
        'total': total_articles,
        'remaining': remaining
    }
`;
  }

  /**
   * Sitemap Generator Tool
   */
  getSitemapGeneratorCode() {
    return `
def execute(params):
    """Generate sitemap structure"""
    articles = params.get('articles', [])
    base_url = params.get('base_url', 'https://example.com')

    sitemap = []

    for article in articles:
        path = article.get('path', '')
        date = article.get('date', '')

        sitemap.append({
            'url': f"{base_url}/{path}",
            'lastmod': date,
            'priority': article.get('priority', 0.5)
        })

    return {
        'sitemap': sitemap,
        'count': len(sitemap)
    }
`;
  }

  /**
   * Version History Tool
   */
  getVersionHistoryCode() {
    return `
def execute(params):
    """Track version history"""
    article_id = params.get('article_id', '')
    versions = params.get('versions', [])

    # Sort versions by date
    sorted_versions = sorted(
        versions,
        key=lambda x: x.get('date', ''),
        reverse=True
    )

    return {
        'article_id': article_id,
        'versions': sorted_versions,
        'current_version': sorted_versions[0] if sorted_versions else None,
        'version_count': len(sorted_versions)
    }
`;
  }

  /**
   * Tags Cloud Tool
   */
  getTagsCloudCode() {
    return `
from collections import Counter

def execute(params):
    """Generate tag cloud data"""
    articles = params.get('articles', [])

    # Collect all tags
    all_tags = []
    for article in articles:
        tags = article.get('tags', [])
        all_tags.extend(tags)

    # Count frequencies
    tag_counts = Counter(all_tags)

    # Calculate weights (normalize to 1-10)
    if tag_counts:
        max_count = max(tag_counts.values())
        min_count = min(tag_counts.values())

        tag_cloud = []
        for tag, count in tag_counts.most_common():
            if max_count > min_count:
                weight = 1 + (9 * (count - min_count) / (max_count - min_count))
            else:
                weight = 5

            tag_cloud.append({
                'tag': tag,
                'count': count,
                'weight': round(weight, 1)
            })
    else:
        tag_cloud = []

    return {
        'tag_cloud': tag_cloud,
        'unique_tags': len(tag_counts),
        'total_uses': len(all_tags)
    }
`;
  }

  // ==================== NEW MEDIUM TOOLS (Phase 9.2) ====================

  /**
   * Advanced Search Tool
   */
  getAdvancedSearchCode() {
    return `
import re

def execute(params):
    """Advanced search with filters"""
    query = params.get('query', '').lower()
    articles = params.get('articles', [])
    filters = params.get('filters', {})

    results = []

    for article in articles:
        # Apply filters
        if filters.get('category') and article.get('category') != filters['category']:
            continue

        if filters.get('tags') and not any(tag in article.get('tags', []) for tag in filters['tags']):
            continue

        # Search
        title = article.get('title', '').lower()
        content = article.get('content', '').lower()

        score = 0
        if query in title:
            score += 10
        if query in content:
            score += content.count(query)

        if score > 0:
            results.append({**article, 'score': score})

    results.sort(key=lambda x: x['score'], reverse=True)

    return {
        'results': results,
        'count': len(results)
    }
`;
  }

  /**
   * Find Related Tool
   */
  getFindRelatedCode() {
    return `
def execute(params):
    """Find related articles by tags"""
    article = params.get('article', {})
    all_articles = params.get('articles', [])
    max_results = params.get('max_results', 5)

    article_tags = set(article.get('tags', []))
    article_id = article.get('id', '')

    related = []

    for other in all_articles:
        if other.get('id') == article_id:
            continue

        other_tags = set(other.get('tags', []))
        common_tags = article_tags & other_tags

        if common_tags:
            score = len(common_tags)
            related.append({
                **other,
                'similarity_score': score,
                'common_tags': list(common_tags)
            })

    related.sort(key=lambda x: x['similarity_score'], reverse=True)

    return {
        'related': related[:max_results],
        'count': len(related)
    }
`;
  }

  /**
   * Related Articles Tool
   */
  getRelatedArticlesCode() {
    return `
def execute(params):
    """Find related articles by content similarity"""
    article = params.get('article', {})
    all_articles = params.get('articles', [])

    # Simple similarity based on word overlap
    article_words = set(article.get('content', '').lower().split())

    related = []
    for other in all_articles:
        if other.get('id') == article.get('id'):
            continue

        other_words = set(other.get('content', '').lower().split())
        common = article_words & other_words

        if len(common) > 10:
            similarity = len(common) / len(article_words | other_words)
            related.append({
                **other,
                'similarity': round(similarity, 3)
            })

    related.sort(key=lambda x: x['similarity'], reverse=True)

    return {'related': related[:10]}
`;
  }

  /**
   * Popular Articles Tool
   */
  getPopularArticlesCode() {
    return `
def execute(params):
    """Find popular articles by backlinks"""
    articles = params.get('articles', [])

    # Count backlinks
    backlink_count = {}
    for article in articles:
        article_id = article.get('id', '')
        backlink_count[article_id] = 0

    # Count references
    for article in articles:
        for link in article.get('links', []):
            if link in backlink_count:
                backlink_count[link] += 1

    # Add backlink counts and sort
    for article in articles:
        article['backlinks'] = backlink_count.get(article.get('id', ''), 0)

    popular = sorted(articles, key=lambda x: x.get('backlinks', 0), reverse=True)

    return {
        'popular': popular[:20],
        'count': len(popular)
    }
`;
  }

  /**
   * Quality Metrics Tool
   */
  getQualityMetricsCode() {
    return `
def execute(params):
    """Calculate quality metrics for article"""
    article = params.get('article', {})

    score = 0
    max_score = 100

    # Word count (0-25 points)
    word_count = len(article.get('content', '').split())
    if word_count >= 500:
        score += 25
    elif word_count >= 200:
        score += 15
    elif word_count >= 100:
        score += 10

    # Has tags (0-20 points)
    tags = article.get('tags', [])
    if len(tags) >= 5:
        score += 20
    elif len(tags) >= 3:
        score += 15
    elif len(tags) >= 1:
        score += 10

    # Has links (0-20 points)
    links = len(article.get('links', []))
    if links >= 5:
        score += 20
    elif links >= 3:
        score += 15
    elif links >= 1:
        score += 10

    # Has metadata (0-20 points)
    if article.get('title'):
        score += 10
    if article.get('date'):
        score += 10

    # Has images (0-15 points)
    images = article.get('images', 0)
    if images >= 3:
        score += 15
    elif images >= 1:
        score += 10

    return {
        'quality_score': score,
        'max_score': max_score,
        'percentage': round((score / max_score) * 100, 1),
        'grade': 'A' if score >= 80 else 'B' if score >= 60 else 'C' if score >= 40 else 'D'
    }
`;
  }

  /**
   * Weighted Tags Tool
   */
  getWeightedTagsCode() {
    return `
from collections import Counter

def execute(params):
    """Calculate weighted tag importance"""
    articles = params.get('articles', [])

    tag_weights = Counter()

    for article in articles:
        tags = article.get('tags', [])
        word_count = len(article.get('content', '').split())
        backlinks = article.get('backlinks', 0)

        # Weight = word_count + backlinks * 10
        weight = word_count + (backlinks * 10)

        for tag in tags:
            tag_weights[tag] += weight

    weighted = [
        {'tag': tag, 'weight': weight}
        for tag, weight in tag_weights.most_common(30)
    ]

    return {'weighted_tags': weighted}
`;
  }

  /**
   * Summary Generator Tool
   */
  getSummaryGeneratorCode() {
    return `
import re

def execute(params):
    """Generate extractive summary"""
    content = params.get('content', '')
    max_sentences = params.get('max_sentences', 3)

    # Split into sentences
    sentences = re.split(r'[.!?]+', content)
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        return {'summary': ''}

    # Simple scoring: prefer sentences with more words
    scored = [
        (s, len(s.split()))
        for s in sentences
    ]

    scored.sort(key=lambda x: x[1], reverse=True)

    # Take top sentences
    summary_sentences = [s for s, _ in scored[:max_sentences]]
    summary = '. '.join(summary_sentences) + '.'

    return {
        'summary': summary,
        'sentence_count': len(summary_sentences)
    }
`;
  }

  /**
   * Duplicate Detector Tool
   */
  getDuplicateDetectorCode() {
    return `
def execute(params):
    """Detect duplicate content"""
    articles = params.get('articles', [])
    threshold = params.get('threshold', 0.8)

    duplicates = []

    for i, article1 in enumerate(articles):
        content1 = set(article1.get('content', '').lower().split())

        for article2 in articles[i+1:]:
            content2 = set(article2.get('content', '').lower().split())

            if not content1 or not content2:
                continue

            # Jaccard similarity
            intersection = len(content1 & content2)
            union = len(content1 | content2)

            if union > 0:
                similarity = intersection / union

                if similarity >= threshold:
                    duplicates.append({
                        'article1': article1.get('id', ''),
                        'article2': article2.get('id', ''),
                        'similarity': round(similarity, 3)
                    })

    return {
        'duplicates': duplicates,
        'count': len(duplicates)
    }
`;
  }

  /**
   * Build Concordance Tool
   */
  getBuildConcordanceCode() {
    return `
import re
from collections import defaultdict

def execute(params):
    """Build word concordance"""
    content = params.get('content', '')

    # Normalize and tokenize
    words = re.findall(r'\\b\\w+\\b', content.lower())

    # Build concordance
    concordance = defaultdict(list)

    for i, word in enumerate(words):
        if len(word) > 3:  # Skip short words
            # Get context (5 words before and after)
            start = max(0, i - 5)
            end = min(len(words), i + 6)
            context = ' '.join(words[start:end])

            concordance[word].append({
                'position': i,
                'context': context
            })

    # Limit to most common words
    word_counts = {w: len(contexts) for w, contexts in concordance.items()}
    top_words = sorted(word_counts, key=word_counts.get, reverse=True)[:20]

    return {
        'concordance': {
            word: concordance[word][:5]  # Max 5 contexts per word
            for word in top_words
        }
    }
`;
  }

  /**
   * Build Glossary Tool
   */
  getBuildGlossaryCode() {
    return `
import re

def execute(params):
    """Build glossary from content"""
    content = params.get('content', '')

    # Find terms in bold (**term**)
    terms = re.findall(r'\\*\\*([A-Z][^*]{2,40})\\*\\*', content)

    glossary = []

    for term in set(terms):
        # Find first occurrence with context
        pattern = r'(.{0,100})' + re.escape(f'**{term}**') + r'(.{0,100})'
        match = re.search(pattern, content)

        if match:
            context = match.group(1).strip() + ' ' + term + ' ' + match.group(2).strip()

            glossary.append({
                'term': term,
                'context': context,
                'frequency': content.count(f'**{term}**')
            })

    glossary.sort(key=lambda x: x['term'])

    return {'glossary': glossary}
`;
  }

  /**
   * Citation Index Tool
   */
  getCitationIndexCode() {
    return `
import re

def execute(params):
    """Build citation index"""
    articles = params.get('articles', [])

    citations = {}

    for article in articles:
        article_id = article.get('id', '')
        content = article.get('content', '')

        # Find all links
        links = re.findall(r'\\[([^\\]]+)\\]\\(([^)]+)\\)', content)

        citations[article_id] = {
            'cited_by': [],
            'cites': [url for _, url in links]
        }

    # Build reverse citations
    for article_id, data in citations.items():
        for cited_url in data['cites']:
            for other_id in citations:
                if cited_url in citations[other_id].get('cites', []):
                    citations[other_id]['cited_by'].append(article_id)

    return {'citations': citations}
`;
  }

  /**
   * Master Index Tool
   */
  getMasterIndexCode() {
    return `
from collections import defaultdict

def execute(params):
    """Build master index"""
    articles = params.get('articles', [])

    index = defaultdict(list)

    for article in articles:
        # Index by category
        category = article.get('category', 'uncategorized')
        index[f'category:{category}'].append(article.get('id'))

        # Index by tags
        for tag in article.get('tags', []):
            index[f'tag:{tag}'].append(article.get('id'))

        # Index by first letter of title
        title = article.get('title', '')
        if title:
            first_letter = title[0].upper()
            index[f'letter:{first_letter}'].append(article.get('id'))

    return {
        'index': dict(index),
        'keys': list(index.keys())
    }
`;
  }

  /**
   * Statistics Dashboard Tool
   */
  getStatisticsDashboardCode() {
    return `
from collections import Counter

def execute(params):
    """Generate dashboard statistics"""
    articles = params.get('articles', [])

    total_articles = len(articles)
    total_words = sum(len(a.get('content', '').split()) for a in articles)

    # Category distribution
    categories = Counter(a.get('category', 'uncategorized') for a in articles)

    # Tag distribution
    all_tags = []
    for a in articles:
        all_tags.extend(a.get('tags', []))
    top_tags = Counter(all_tags).most_common(10)

    return {
        'overview': {
            'total_articles': total_articles,
            'total_words': total_words,
            'avg_words': round(total_words / total_articles) if total_articles > 0 else 0
        },
        'categories': dict(categories),
        'top_tags': [{'tag': t, 'count': c} for t, c in top_tags]
    }
`;
  }

  /**
   * Timeline Generator Tool
   */
  getTimelineGeneratorCode() {
    return `
from datetime import datetime

def execute(params):
    """Generate chronological timeline"""
    articles = params.get('articles', [])

    # Filter articles with dates
    dated_articles = []
    for article in articles:
        date_str = article.get('date', '')
        if date_str:
            try:
                date = datetime.fromisoformat(str(date_str))
                dated_articles.append({
                    **article,
                    'parsed_date': date
                })
            except:
                pass

    # Sort by date
    dated_articles.sort(key=lambda x: x['parsed_date'])

    # Group by year
    timeline = {}
    for article in dated_articles:
        year = article['parsed_date'].year
        if year not in timeline:
            timeline[year] = []
        timeline[year].append({
            'id': article.get('id'),
            'title': article.get('title'),
            'date': article.get('date')
        })

    return {
        'timeline': timeline,
        'years': sorted(timeline.keys())
    }
`;
  }

  /**
   * Generate Bibliography Tool
   */
  getGenerateBibliographyCode() {
    return `
import re

def execute(params):
    """Generate bibliography from citations"""
    content = params.get('content', '')

    # Find all external links
    links = re.findall(r'\\[([^\\]]+)\\]\\((https?://[^)]+)\\)', content)

    bibliography = []
    seen = set()

    for title, url in links:
        if url not in seen:
            seen.add(url)

            # Extract domain
            domain_match = re.search(r'https?://([^/]+)', url)
            domain = domain_match.group(1) if domain_match else 'Unknown'

            bibliography.append({
                'title': title,
                'url': url,
                'domain': domain
            })

    bibliography.sort(key=lambda x: x['title'])

    return {
        'bibliography': bibliography,
        'count': len(bibliography)
    }
`;
  }

  /**
   * Faceted Search Tool
   */
  getFacetedSearchCode() {
    return `
from collections import defaultdict

def execute(params):
    """Faceted search with filters"""
    articles = params.get('articles', [])
    query = params.get('query', '').lower()

    # Build facets
    facets = {
        'categories': defaultdict(int),
        'tags': defaultdict(int),
        'years': defaultdict(int)
    }

    results = []

    for article in articles:
        # Check if matches query
        matches = query in article.get('title', '').lower() or query in article.get('content', '').lower()

        if matches or not query:
            results.append(article)

            # Update facets
            facets['categories'][article.get('category', 'uncategorized')] += 1

            for tag in article.get('tags', []):
                facets['tags'][tag] += 1

            date_str = article.get('date', '')
            if date_str:
                year = date_str[:4]
                facets['years'][year] += 1

    return {
        'results': results,
        'count': len(results),
        'facets': {
            'categories': dict(facets['categories']),
            'tags': dict(sorted(facets['tags'].items(), key=lambda x: -x[1])[:20]),
            'years': dict(sorted(facets['years'].items()))
        }
    }
`;
  }
}

export default ToolRegistry;
