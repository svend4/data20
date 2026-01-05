/**
 * WASM Tools Library
 * Phase 8.1.5: WebAssembly Tools (Pyodide Integration)
 *
 * Collection of Python tools that run via Pyodide (WebAssembly).
 * These tools can execute entirely client-side without server calls.
 */

/**
 * Tool 1: Reading Time Calculator
 * Calculates estimated reading time for text content
 */
export const readingTimeCalculator = {
  name: 'reading_time_calculator',
  description: 'Calculate estimated reading time for text',
  category: 'analysis',
  offlineCapable: true,
  wasmTool: true,

  pythonCode: `
import re
import json
import math

def calculate_reading_time(text, wpm=200):
    """
    Calculate reading time for text

    Args:
        text: Text content
        wpm: Words per minute (default: 200)

    Returns:
        dict with reading time metrics
    """
    # Remove markdown headers
    text = re.sub(r'^#{1,6}\\s+.*$', '', text, flags=re.MULTILINE)

    # Remove code blocks
    text = re.sub(r'\`\`\`.*?\`\`\`', '', text, flags=re.DOTALL)
    text = re.sub(r'\`[^\`]+\`', '', text)

    # Remove links
    text = re.sub(r'\\[([^\\]]+)\\]\\([^\\)]+\\)', r'\\1', text)

    # Remove images
    text = re.sub(r'!\\[([^\\]]*)\\]\\([^\\)]+\\)', '', text)

    # Count words (cyrillic + latin)
    words = re.findall(r'\\b[а-яёa-z]+\\b', text.lower())
    word_count = len(words)

    # Calculate reading time
    reading_minutes = word_count / wpm if wpm > 0 else 0
    reading_minutes_rounded = max(1, math.ceil(reading_minutes))

    # Format time
    if reading_minutes_rounded < 1:
        formatted = "< 1 min"
    elif reading_minutes_rounded == 1:
        formatted = "1 min"
    elif reading_minutes_rounded < 60:
        formatted = f"{int(reading_minutes_rounded)} min"
    else:
        hours = int(reading_minutes_rounded // 60)
        mins = int(reading_minutes_rounded % 60)
        if mins == 0:
            formatted = f"{hours} h"
        else:
            formatted = f"{hours} h {mins} min"

    return {
        'words': word_count,
        'reading_minutes': round(reading_minutes, 2),
        'reading_minutes_rounded': reading_minutes_rounded,
        'formatted': formatted,
        'wpm': wpm
    }
`,

  functionName: 'calculate_reading_time',

  // Default parameters
  defaultParameters: {
    text: '',
    wpm: 200,
  },
};

/**
 * Tool 2: Text Statistics
 * Calculate various text statistics
 */
export const textStatistics = {
  name: 'text_statistics',
  description: 'Calculate text statistics (words, sentences, chars)',
  category: 'analysis',
  offlineCapable: true,
  wasmTool: true,

  pythonCode: `
import re
import json

def calculate_text_statistics(text):
    """
    Calculate comprehensive text statistics

    Args:
        text: Text content

    Returns:
        dict with statistics
    """
    # Sentences
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    # Words
    words = re.findall(r'\\b[а-яёa-z]+\\b', text.lower())

    # Characters (excluding spaces)
    chars = sum(len(word) for word in words)

    # Unique words
    unique_words = set(words)

    # Average sentence length
    avg_sentence_length = len(words) / len(sentences) if sentences else 0

    # Average word length
    avg_word_length = chars / len(words) if words else 0

    # Type-Token Ratio (vocabulary richness)
    ttr = len(unique_words) / len(words) if words else 0

    return {
        'total_chars': len(text),
        'chars_no_spaces': chars,
        'total_words': len(words),
        'unique_words': len(unique_words),
        'total_sentences': len(sentences),
        'avg_sentence_length': round(avg_sentence_length, 1),
        'avg_word_length': round(avg_word_length, 1),
        'type_token_ratio': round(ttr, 3),
        'vocabulary_richness': 'high' if ttr > 0.6 else 'medium' if ttr > 0.4 else 'low'
    }
`,

  functionName: 'calculate_text_statistics',

  defaultParameters: {
    text: '',
  },
};

/**
 * Tool 3: Word Frequency Counter
 * Count word frequencies in text
 */
export const wordFrequencyCounter = {
  name: 'word_frequency_counter',
  description: 'Count word frequencies in text',
  category: 'analysis',
  offlineCapable: true,
  wasmTool: true,

  pythonCode: `
import re
import json
from collections import Counter

def count_word_frequencies(text, top_n=20, min_length=3):
    """
    Count word frequencies in text

    Args:
        text: Text content
        top_n: Number of top words to return
        min_length: Minimum word length to include

    Returns:
        dict with word frequencies
    """
    # Extract words
    words = re.findall(r'\\b[а-яёa-z]+\\b', text.lower())

    # Filter by length
    words = [w for w in words if len(w) >= min_length]

    # Count frequencies
    counter = Counter(words)

    # Get top N
    top_words = counter.most_common(top_n)

    return {
        'total_words': len(words),
        'unique_words': len(counter),
        'top_words': [{'word': word, 'count': count} for word, count in top_words],
        'top_n': top_n
    }
`,

  functionName: 'count_word_frequencies',

  defaultParameters: {
    text: '',
    top_n: 20,
    min_length: 3,
  },
};

/**
 * Tool 4: Data Validator
 * Validate and clean data
 */
export const dataValidator = {
  name: 'data_validator',
  description: 'Validate and clean data',
  category: 'cleaning',
  offlineCapable: true,
  wasmTool: true,

  pythonCode: `
import re
import json

def validate_data(data, rules=None):
    """
    Validate data against rules

    Args:
        data: List of dictionaries to validate
        rules: Validation rules (optional)

    Returns:
        dict with validation results
    """
    if not rules:
        rules = {}

    results = {
        'total_items': len(data),
        'valid_items': 0,
        'invalid_items': 0,
        'errors': [],
        'warnings': []
    }

    for i, item in enumerate(data):
        item_valid = True

        # Check required fields
        if 'required_fields' in rules:
            for field in rules['required_fields']:
                if field not in item or not item[field]:
                    results['errors'].append({
                        'index': i,
                        'type': 'missing_field',
                        'field': field,
                        'message': f'Required field "{field}" is missing or empty'
                    })
                    item_valid = False

        # Check field types
        if 'field_types' in rules:
            for field, expected_type in rules['field_types'].items():
                if field in item:
                    actual_type = type(item[field]).__name__
                    if actual_type != expected_type:
                        results['warnings'].append({
                            'index': i,
                            'type': 'type_mismatch',
                            'field': field,
                            'expected': expected_type,
                            'actual': actual_type,
                            'message': f'Field "{field}" has type {actual_type}, expected {expected_type}'
                        })

        if item_valid:
            results['valid_items'] += 1
        else:
            results['invalid_items'] += 1

    results['validation_passed'] = results['invalid_items'] == 0

    return results
`,

  functionName: 'validate_data',

  defaultParameters: {
    data: [],
    rules: {},
  },
};

/**
 * Tool 5: JSON Formatter
 * Format and beautify JSON
 */
export const jsonFormatter = {
  name: 'json_formatter',
  description: 'Format and beautify JSON',
  category: 'formatting',
  offlineCapable: true,
  wasmTool: true,

  pythonCode: `
import json

def format_json(data, indent=2, sort_keys=False):
    """
    Format JSON data

    Args:
        data: JSON data (string or object)
        indent: Indentation spaces
        sort_keys: Sort keys alphabetically

    Returns:
        dict with formatted JSON
    """
    # Parse if string
    if isinstance(data, str):
        try:
            parsed = json.loads(data)
        except json.JSONDecodeError as e:
            return {
                'success': False,
                'error': f'Invalid JSON: {str(e)}',
                'formatted': None
            }
    else:
        parsed = data

    # Format
    formatted = json.dumps(
        parsed,
        indent=indent,
        ensure_ascii=False,
        sort_keys=sort_keys
    )

    # Stats
    lines = formatted.split('\\n')
    size_bytes = len(formatted.encode('utf-8'))

    return {
        'success': True,
        'formatted': formatted,
        'stats': {
            'lines': len(lines),
            'size_bytes': size_bytes,
            'keys': len(parsed) if isinstance(parsed, dict) else None,
            'items': len(parsed) if isinstance(parsed, list) else None
        }
    }
`,

  functionName: 'format_json',

  defaultParameters: {
    data: '',
    indent: 2,
    sort_keys: false,
  },
};

/**
 * Tool 6: List Deduplicator
 * Remove duplicates from list
 */
export const listDeduplicator = {
  name: 'list_deduplicator',
  description: 'Remove duplicates from list',
  category: 'cleaning',
  offlineCapable: true,
  wasmTool: true,

  pythonCode: `
import json

def deduplicate_list(items, key=None, case_sensitive=True):
    """
    Remove duplicates from list

    Args:
        items: List of items
        key: Key to use for deduplication (for dicts)
        case_sensitive: Case sensitive comparison

    Returns:
        dict with deduplicated list and stats
    """
    original_count = len(items)
    seen = set()
    unique_items = []
    duplicates = []

    for item in items:
        # Get comparison value
        if key and isinstance(item, dict):
            compare_value = item.get(key)
        else:
            compare_value = item

        # Normalize for comparison
        if isinstance(compare_value, str) and not case_sensitive:
            compare_value = compare_value.lower()

        # Check if seen
        if compare_value not in seen:
            seen.add(compare_value)
            unique_items.append(item)
        else:
            duplicates.append(item)

    return {
        'original_count': original_count,
        'unique_count': len(unique_items),
        'duplicates_count': len(duplicates),
        'unique_items': unique_items,
        'duplicates': duplicates,
        'deduplication_rate': round((1 - len(unique_items) / original_count) * 100, 1) if original_count > 0 else 0
    }
`,

  functionName: 'deduplicate_list',

  defaultParameters: {
    items: [],
    key: null,
    case_sensitive: true,
  },
};

/**
 * Tool 7: Simple Calculator
 * Perform mathematical calculations
 */
export const simpleCalculator = {
  name: 'simple_calculator',
  description: 'Perform mathematical calculations',
  category: 'math',
  offlineCapable: true,
  wasmTool: true,

  pythonCode: `
import math
import json

def calculate(expression, precision=2):
    """
    Calculate mathematical expression

    Args:
        expression: Mathematical expression as string
        precision: Decimal precision

    Returns:
        dict with calculation result
    """
    try:
        # Evaluate expression
        result = eval(expression, {"__builtins__": None}, {
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "sum": sum,
            "pow": pow,
            "sqrt": math.sqrt,
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "pi": math.pi,
            "e": math.e,
        })

        # Round to precision
        if isinstance(result, float):
            result_rounded = round(result, precision)
        else:
            result_rounded = result

        return {
            'success': True,
            'expression': expression,
            'result': result_rounded,
            'result_type': type(result).__name__
        }
    except Exception as e:
        return {
            'success': False,
            'expression': expression,
            'error': str(e)
        }
`,

  functionName: 'calculate',

  defaultParameters: {
    expression: '',
    precision: 2,
  },
};

/**
 * All WASM tools
 */
export const wasmTools = [
  readingTimeCalculator,
  textStatistics,
  wordFrequencyCounter,
  dataValidator,
  jsonFormatter,
  listDeduplicator,
  simpleCalculator,
];

/**
 * Get WASM tool by name
 */
export function getWasmTool(name) {
  return wasmTools.find((tool) => tool.name === name);
}

/**
 * Check if tool is WASM-capable
 */
export function isWasmTool(toolName) {
  return wasmTools.some((tool) => tool.name === toolName);
}

console.log(`[WASM Tools] Loaded ${wasmTools.length} WebAssembly tools`);
