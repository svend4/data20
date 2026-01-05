/**
 * Tool Registry
 * Phase 9.1.3: Port Tools to WebAssembly
 *
 * Manages all 57 tools in Pyodide/WASM environment
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
      }
    ];

    for (const tool of simpleTools) {
      await this.registerTool(tool);
    }
  }

  /**
   * Load medium complexity tools
   */
  async loadMediumTools() {
    const mediumTools = [
      {
        name: 'extract_keywords',
        category: 'text_analysis',
        code: this.getExtractKeywordsCode(),
        dependencies: ['regex']
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
}

export default ToolRegistry;
