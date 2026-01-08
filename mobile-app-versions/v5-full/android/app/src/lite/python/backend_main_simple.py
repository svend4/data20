"""
Lite Mobile Backend - 12 tools with real implementations
Python standard library only
Simple HTTP server with /health endpoint using http.server
"""

import os
import sys
import time
import json
import sqlite3
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from datetime import datetime

# Simple print-based logging (faster than logging module)
def log_info(message):
    print(f"INFO: {message}", flush=True)

def log_error(message):
    print(f"ERROR: {message}", flush=True, file=sys.stderr)


class SimpleBackendHandler(BaseHTTPRequestHandler):
    """
    Simple HTTP request handler with /health endpoint
    """

    def log_message(self, format, *args):
        # Override to use our logging
        log_info(f"{self.address_string()} - {format % args}")

    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/health':
            # Health check endpoint
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()

            response = {
                'status': 'healthy',
                'service': 'data20-mobile-backend-lite',
                'version': 'lite-0.2.1',
                'git_commit': 'cce8ecd',
                'build_timestamp': datetime.now().isoformat(),
                'features': {
                    'real_implementations': True,
                    'database': True,
                    'tools_count': len(MOCK_TOOLS),
                    'implementations_count': len(TOOL_IMPLEMENTATIONS)
                },
                'message': 'Lite backend: 12 essential tools'
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))

        elif self.path == '/api/tools':
            # Tools list endpoint - returns mock tools
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()

            # Return static list of demo tools
            self.wfile.write(json.dumps(MOCK_TOOLS).encode('utf-8'))

        elif self.path.startswith('/api/jobs'):
            # Jobs endpoint - return real jobs from database
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()

            # Parse query parameters (e.g., ?tool_name=calculate_statistics&limit=10)
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(self.path)
            query_params = parse_qs(parsed.query)

            tool_name = query_params.get('tool_name', [None])[0]
            limit = int(query_params.get('limit', [50])[0])

            # Get jobs from database
            response = get_jobs(limit=limit, tool_name=tool_name)
            self.wfile.write(json.dumps(response).encode('utf-8'))

        elif self.path == '/api/stats':
            # Stats endpoint - return job statistics
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()

            # Get statistics from database
            response = get_job_stats()
            self.wfile.write(json.dumps(response).encode('utf-8'))

        elif self.path.startswith('/api/search'):
            # Search endpoint - search for tools by name/description
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()

            # Parse query parameters (e.g., ?q=statistics)
            from urllib.parse import urlparse, parse_qs
            parsed = urlparse(self.path)
            query_params = parse_qs(parsed.query)

            query = query_params.get('q', [''])[0].lower()

            if query:
                # Search in tool names, display names, and descriptions
                results = [
                    tool for tool in MOCK_TOOLS
                    if query in tool['name'].lower()
                    or query in tool.get('display_name', '').lower()
                    or query in tool.get('description', '').lower()
                    or query in tool.get('category', '').lower()
                ]
                response = {'query': query, 'results': results, 'count': len(results)}
            else:
                response = {'query': '', 'results': [], 'count': 0}

            self.wfile.write(json.dumps(response).encode('utf-8'))

        elif self.path == '/':
            # Root endpoint
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()

            html = """
            <html>
            <head>
                <title>Data20 Mobile Backend - Lite</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; }
                    .status { color: #22c55e; }
                    .version { color: #3b82f6; font-weight: bold; }
                    .feature { color: #8b5cf6; }
                    a { color: #2563eb; text-decoration: none; }
                    a:hover { text-decoration: underline; }
                </style>
            </head>
            <body>
                <h1>Data20 Mobile Backend - Lite</h1>
                <p>Status: <strong class="status">Running</strong></p>
                <p>Version: <span class="version">lite-0.2.1</span></p>
                <p class="feature">✅ 12 essential tools</p>
                <p class="feature">✅ All real implementations</p>
                <p class="feature">✅ SQLite database</p>
                <hr>
                <h3>API Endpoints:</h3>
                <p>🏥 <a href="/health">Health Check</a> - Backend status and version info</p>
                <p>🔧 <a href="/api/tools">API: Tools</a> - List all available tools</p>
                <p>📋 <a href="/api/jobs">API: Jobs</a> - Job history</p>
                <p>📊 <a href="/api/stats">API: Stats</a> - Usage statistics</p>
                <p>🔍 <a href="/api/search?q=statistics">API: Search</a> - Search tools</p>
            </body>
            </html>
            """
            self.wfile.write(html.encode('utf-8'))

        else:
            # 404 for other paths
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()

            response = {'error': 'Not found', 'path': self.path}
            self.wfile.write(json.dumps(response).encode('utf-8'))

    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/api/run':
            # Run tool endpoint - NOW WITH REAL IMPLEMENTATIONS
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()

            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else '{}'

            try:
                request_data = json.loads(body)
                tool_name = request_data.get('tool_name', 'unknown')
                parameters = request_data.get('parameters', {})

                # Generate unique job ID using timestamp
                job_id = f'job-{int(time.time() * 1000)}'

                # Check if tool has real implementation
                if tool_name in TOOL_IMPLEMENTATIONS:
                    # Call real implementation
                    try:
                        result_data = TOOL_IMPLEMENTATIONS[tool_name](parameters)

                        # Check if implementation returned error
                        if 'error' in result_data:
                            response = {
                                'job_id': job_id,
                                'tool_name': tool_name,
                                'status': 'failed',
                                'message': result_data['error'],
                                'result': result_data
                            }
                            # Save failed job to database
                            save_job(job_id, tool_name, 'failed', parameters, result_data, result_data['error'])
                        else:
                            response = {
                                'job_id': job_id,
                                'tool_name': tool_name,
                                'status': 'completed',
                                'message': f'Tool {tool_name} executed successfully',
                                'result': result_data
                            }
                            # Save completed job to database
                            save_job(job_id, tool_name, 'completed', parameters, result_data)
                    except Exception as impl_error:
                        # Implementation function raised exception
                        response = {
                            'job_id': job_id,
                            'tool_name': tool_name,
                            'status': 'failed',
                            'message': f'Implementation error: {str(impl_error)}',
                            'result': {'error': str(impl_error)}
                        }
                        # Save failed job to database
                        save_job(job_id, tool_name, 'failed', parameters, {'error': str(impl_error)}, str(impl_error))
                else:
                    # Tool not found
                    response = {
                        'job_id': job_id,
                        'tool_name': tool_name,
                        'status': 'failed',
                        'message': f'Tool {tool_name} not found',
                        'result': {
                            'error': f'Tool {tool_name} is not available in Lite version'
                        }
                    }
                    # Save failed job to database
                    save_job(job_id, tool_name, 'failed', parameters, response['result'], f'Tool not found: {tool_name}')

                self.wfile.write(json.dumps(response).encode('utf-8'))

            except Exception as e:
                response = {
                    'error': 'Invalid request',
                    'detail': str(e)
                }
                self.wfile.write(json.dumps(response).encode('utf-8'))

        else:
            # 404 for other POST paths
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()

            response = {'error': 'Not found', 'path': self.path}
            self.wfile.write(json.dumps(response).encode('utf-8'))

# Global variables
database_path = None
upload_path = None
logs_path = None
is_running = False
http_server = None

# Mock tools data - 12 essential tools (Lite version)
MOCK_TOOLS = [
    {
        "name": "calculate_statistics",
        "display_name": "Расчёт статистики",
        "description": "Вычисление базовых статистических показателей для набора данных",
        "category": "statistics",
        "parameters": {
            "data": {
                "type": "array",
                "required": True,
                "description": "Массив числовых данных"
            },
            "metrics": {
                "type": "array",
                "required": False,
                "default": ["mean", "median", "std"],
                "enum": ["mean", "median", "std", "min", "max", "variance"],
                "description": "Список метрик для расчёта"
            }
        }
    },
    {
        "name": "text_analysis",
        "display_name": "Анализ текста",
        "description": "Частотный анализ слов, извлечение ключевых фраз",
        "category": "nlp",
        "parameters": {
            "text": {
                "type": "string",
                "required": True,
                "description": "Текст для анализа"
            },
            "language": {
                "type": "string",
                "required": False,
                "default": "ru",
                "enum": ["ru", "en"],
                "description": "Язык текста"
            }
        }
    },
    {
        "name": "correlation_analysis",
        "display_name": "Корреляционный анализ",
        "description": "Вычисление корреляции между двумя наборами данных",
        "category": "statistics",
        "parameters": {
            "x": {
                "type": "array",
                "required": True,
                "description": "Первый набор данных"
            },
            "y": {
                "type": "array",
                "required": True,
                "description": "Второй набор данных"
            }
        }
    },
    {
        "name": "word_frequency",
        "display_name": "Частота слов",
        "description": "Подсчёт частоты встречаемости слов в тексте",
        "category": "text",
        "parameters": {
            "text": {
                "type": "string",
                "required": True,
                "description": "Текст для анализа"
            },
            "top_n": {
                "type": "integer",
                "required": False,
                "default": 10,
                "description": "Количество самых частых слов"
            }
        }
    },
    {
        "name": "json_parser",
        "display_name": "Парсер JSON",
        "description": "Парсинг и валидация JSON строки",
        "category": "other",
        "parameters": {
            "json_string": {
                "type": "string",
                "required": True,
                "description": "JSON строка"
            }
        }
    },
    {
        "name": "csv_parser",
        "display_name": "Парсер CSV",
        "description": "Парсинг CSV данных в структурированный формат",
        "category": "other",
        "parameters": {
            "csv_data": {
                "type": "string",
                "required": True,
                "description": "CSV данные"
            },
            "delimiter": {
                "type": "string",
                "required": False,
                "default": ",",
                "description": "Разделитель (запятая, точка с запятой и т.д.)"
            }
        }
    },
    {
        "name": "data_filter",
        "display_name": "Фильтрация данных",
        "description": "Фильтрация массива данных по условию",
        "category": "cleaning",
        "parameters": {
            "data": {
                "type": "array",
                "required": True,
                "description": "Массив данных"
            },
            "condition": {
                "type": "string",
                "required": True,
                "enum": ["greater_than", "less_than", "equal", "not_equal"],
                "description": "Условие фильтрации"
            },
            "value": {
                "type": "number",
                "required": True,
                "description": "Значение для сравнения"
            }
        }
    },
    {
        "name": "outlier_detection",
        "display_name": "Обнаружение выбросов",
        "description": "Поиск выбросов в данных методом межквартильного размаха (IQR)",
        "category": "statistics",
        "parameters": {
            "data": {
                "type": "array",
                "required": True,
                "description": "Массив числовых данных"
            },
            "method": {
                "type": "string",
                "required": False,
                "default": "iqr",
                "enum": ["iqr"],
                "description": "Метод обнаружения выбросов"
            }
        }
    },
    {
        "name": "base64_encode",
        "display_name": "Base64 кодирование",
        "description": "Кодирование/декодирование текста в Base64",
        "category": "transformation",
        "parameters": {
            "text": {
                "type": "string",
                "required": True,
                "description": "Текст для кодирования/декодирования"
            },
            "operation": {
                "type": "string",
                "required": True,
                "enum": ["encode", "decode"],
                "description": "Операция (кодирование или декодирование)"
            }
        }
    },
    {
        "name": "hash_calculator",
        "display_name": "Вычисление хэша",
        "description": "Вычисление хэша строки (MD5, SHA1, SHA256)",
        "category": "transformation",
        "parameters": {
            "text": {
                "type": "string",
                "required": True,
                "description": "Текст для хэширования"
            },
            "algorithm": {
                "type": "string",
                "required": False,
                "default": "sha256",
                "enum": ["md5", "sha1", "sha256"],
                "description": "Алгоритм хэширования"
            }
        }
    },
    {
        "name": "date_calculator",
        "display_name": "Калькулятор дат",
        "description": "Вычисление разницы между датами или добавление дней к дате",
        "category": "other",
        "parameters": {
            "date": {
                "type": "string",
                "required": True,
                "description": "Дата в формате YYYY-MM-DD"
            },
            "operation": {
                "type": "string",
                "required": True,
                "enum": ["add_days", "diff_days"],
                "description": "Операция с датой"
            },
            "value": {
                "type": "integer",
                "required": False,
                "description": "Количество дней (для add_days) или вторая дата (для diff_days)"
            }
        }
    },
    {
        "name": "url_parser",
        "display_name": "Парсер URL",
        "description": "Разбор URL на составные части (протокол, домен, параметры)",
        "category": "other",
        "parameters": {
            "url": {
                "type": "string",
                "required": True,
                "description": "URL для разбора"
            }
        }
    }
]


# ============================================================================
# TOOL IMPLEMENTATIONS - Real calculations using Python stdlib only
# ============================================================================

def calculate_statistics_impl(params):
    """Calculate basic statistics (mean, median, std, min, max, variance)"""
    data = params.get('data', [])
    metrics = params.get('metrics', ['mean', 'median', 'std'])

    if not data:
        return {'error': 'No data provided'}

    n = len(data)
    result = {}

    if 'mean' in metrics:
        result['mean'] = sum(data) / n

    if 'median' in metrics:
        sorted_data = sorted(data)
        mid = n // 2
        result['median'] = sorted_data[mid] if n % 2 else (sorted_data[mid-1] + sorted_data[mid]) / 2

    if 'min' in metrics:
        result['min'] = min(data)

    if 'max' in metrics:
        result['max'] = max(data)

    if 'variance' in metrics or 'std' in metrics:
        mean = sum(data) / n
        variance = sum((x - mean) ** 2 for x in data) / n
        if 'variance' in metrics:
            result['variance'] = variance
        if 'std' in metrics:
            result['std'] = variance ** 0.5

    return result


def text_analysis_impl(params):
    """Analyze text: word count, unique words, character count"""
    text = params.get('text', '')
    language = params.get('language', 'ru')

    words = text.split()
    chars = len(text)
    unique_words = len(set(words))

    # Word frequency
    word_freq = {}
    for word in words:
        word_lower = word.lower().strip('.,!?;:')
        word_freq[word_lower] = word_freq.get(word_lower, 0) + 1

    top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        'total_words': len(words),
        'unique_words': unique_words,
        'total_characters': chars,
        'top_words': [{'word': w, 'count': c} for w, c in top_words],
        'language': language
    }


def correlation_analysis_impl(params):
    """Calculate Pearson correlation coefficient"""
    # Support both old style (data_x, data_y) and new style (x, y)
    data_x = params.get('x') or params.get('data_x', [])
    data_y = params.get('y') or params.get('data_y', [])

    if len(data_x) != len(data_y) or not data_x:
        return {'error': 'Data arrays must have equal non-zero length'}

    n = len(data_x)
    mean_x = sum(data_x) / n
    mean_y = sum(data_y) / n

    numerator = sum((data_x[i] - mean_x) * (data_y[i] - mean_y) for i in range(n))
    denominator_x = sum((x - mean_x) ** 2 for x in data_x) ** 0.5
    denominator_y = sum((y - mean_y) ** 2 for y in data_y) ** 0.5

    if denominator_x == 0 or denominator_y == 0:
        return {'error': 'Cannot calculate correlation: zero variance'}

    correlation = numerator / (denominator_x * denominator_y)

    return {
        'correlation': correlation,
        'interpretation': 'strong' if abs(correlation) > 0.7 else 'moderate' if abs(correlation) > 0.4 else 'weak'
    }


def word_frequency_impl(params):
    """Count word frequency in text"""
    text = params.get('text', '')
    top_n = params.get('top_n', 10)

    words = text.lower().split()
    word_freq = {}

    for word in words:
        word = word.strip('.,!?;:()[]{}\"\'')
        if word:
            word_freq[word] = word_freq.get(word, 0) + 1

    top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:top_n]

    return {
        'total_words': len(words),
        'unique_words': len(word_freq),
        'top_words': [{'word': w, 'frequency': c} for w, c in top_words]
    }


def json_parser_impl(params):
    """Parse and validate JSON"""
    json_string = params.get('json_string', '')
    operation = params.get('operation', 'validate')

    try:
        parsed = json.loads(json_string)
        return {
            'valid': True,
            'type': type(parsed).__name__,
            'data': parsed,
            'operation': operation
        }
    except json.JSONDecodeError as e:
        return {
            'valid': False,
            'error': str(e)
        }


def csv_parser_impl(params):
    """Parse CSV data"""
    csv_data = params.get('csv_data', '')
    delimiter = params.get('delimiter', ',')

    lines = csv_data.strip().split('\n')
    if not lines:
        return {'error': 'No data provided'}

    # Parse header
    header = lines[0].split(delimiter)

    # Parse rows
    rows = []
    for line in lines[1:]:
        values = line.split(delimiter)
        row = {header[i]: values[i] if i < len(values) else '' for i in range(len(header))}
        rows.append(row)

    return {
        'columns': header,
        'row_count': len(rows),
        'data': rows[:10]  # Return first 10 rows
    }


def base64_encode_impl(params):
    """Encode/decode Base64"""
    import base64

    text = params.get('text', '')
    operation = params.get('operation', 'encode')

    try:
        if operation == 'encode':
            encoded = base64.b64encode(text.encode('utf-8')).decode('utf-8')
            return {'result': encoded, 'operation': 'encode'}
        else:  # decode
            decoded = base64.b64decode(text.encode('utf-8')).decode('utf-8')
            return {'result': decoded, 'operation': 'decode'}
    except Exception as e:
        return {'error': str(e)}


def hash_calculator_impl(params):
    """Calculate hash (MD5, SHA1, SHA256)"""
    import hashlib

    text = params.get('text', '')
    algorithm = params.get('algorithm', 'sha256')

    hash_funcs = {
        'md5': hashlib.md5,
        'sha1': hashlib.sha1,
        'sha256': hashlib.sha256
    }

    hash_func = hash_funcs.get(algorithm, hashlib.sha256)
    hash_value = hash_func(text.encode('utf-8')).hexdigest()

    return {
        'algorithm': algorithm,
        'hash': hash_value,
        'input_length': len(text)
    }


def date_calculator_impl(params):
    """Calculate date operations"""
    from datetime import datetime, timedelta

    date_str = params.get('date', '')
    operation = params.get('operation', 'add_days')
    value = params.get('value', 0)

    try:
        date = datetime.strptime(date_str, '%Y-%m-%d')

        if operation == 'add_days':
            new_date = date + timedelta(days=value)
            return {
                'original_date': date_str,
                'operation': f'add {value} days',
                'result_date': new_date.strftime('%Y-%m-%d')
            }
        elif operation == 'diff_days':
            # value should contain second date string
            date2 = datetime.strptime(str(value), '%Y-%m-%d')
            diff = (date2 - date).days
            return {
                'date1': date_str,
                'date2': str(value),
                'difference_days': diff
            }
    except Exception as e:
        return {'error': str(e)}


def url_parser_impl(params):
    """Parse URL into components"""
    from urllib.parse import urlparse, parse_qs

    url = params.get('url', '')

    try:
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)

        return {
            'scheme': parsed.scheme,
            'netloc': parsed.netloc,
            'path': parsed.path,
            'params': parsed.params,
            'query': parsed.query,
            'fragment': parsed.fragment,
            'query_parameters': {k: v[0] if len(v) == 1 else v for k, v in query_params.items()}
        }
    except Exception as e:
        return {'error': str(e)}


def outlier_detection_impl(params):
    """Detect outliers using IQR method"""
    data = params.get('data', [])
    method = params.get('method', 'iqr')

    if len(data) < 4:
        return {'error': 'Need at least 4 data points'}

    sorted_data = sorted(data)
    n = len(sorted_data)
    q1_idx = n // 4
    q3_idx = 3 * n // 4

    q1 = sorted_data[q1_idx]
    q3 = sorted_data[q3_idx]
    iqr = q3 - q1

    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    outliers = [x for x in data if x < lower_bound or x > upper_bound]

    return {
        'q1': q1,
        'q3': q3,
        'iqr': iqr,
        'lower_bound': lower_bound,
        'upper_bound': upper_bound,
        'outliers': outliers,
        'outlier_count': len(outliers),
        'method': method
    }


def data_filter_impl(params):
    """Filter data array by condition"""
    data = params.get('data', [])
    condition = params.get('condition', 'greater_than')
    value = params.get('value', 0)

    if condition == 'greater_than':
        filtered = [x for x in data if x > value]
    elif condition == 'less_than':
        filtered = [x for x in data if x < value]
    elif condition == 'equal':
        filtered = [x for x in data if x == value]
    elif condition == 'not_equal':
        filtered = [x for x in data if x != value]
    else:
        filtered = data

    return {
        'original_count': len(data),
        'filtered_count': len(filtered),
        'filtered_data': filtered,
        'condition': condition,
        'filter_value': value
    }


# Map tool names to implementation functions
TOOL_IMPLEMENTATIONS = {
    'calculate_statistics': calculate_statistics_impl,
    'text_analysis': text_analysis_impl,
    'correlation_analysis': correlation_analysis_impl,
    'word_frequency': word_frequency_impl,
    'json_parser': json_parser_impl,
    'csv_parser': csv_parser_impl,
    'base64_encode': base64_encode_impl,
    'hash_calculator': hash_calculator_impl,
    'date_calculator': date_calculator_impl,
    'url_parser': url_parser_impl,
    'outlier_detection': outlier_detection_impl,
    'data_filter': data_filter_impl,
}


# ============================================================================
# DATABASE FUNCTIONS - Job history using SQLite
# ============================================================================

def init_database():
    """Initialize SQLite database for job history"""
    if not database_path:
        log_error("Database path not set")
        return

    try:
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # Create jobs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                tool_name TEXT NOT NULL,
                status TEXT NOT NULL,
                parameters TEXT,
                result TEXT,
                error_message TEXT,
                created_at TEXT NOT NULL,
                completed_at TEXT
            )
        ''')

        # Create index on created_at for faster queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC)
        ''')

        # Create index on tool_name for faster searches
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_jobs_tool_name ON jobs(tool_name)
        ''')

        conn.commit()
        conn.close()
        log_info("Database initialized successfully")
    except Exception as e:
        log_error(f"Failed to initialize database: {e}")


def save_job(job_id, tool_name, status, parameters, result, error_message=None):
    """Save job to database"""
    if not database_path:
        return

    try:
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        created_at = datetime.now().isoformat()
        completed_at = created_at if status in ['completed', 'failed'] else None

        cursor.execute('''
            INSERT OR REPLACE INTO jobs
            (job_id, tool_name, status, parameters, result, error_message, created_at, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            job_id,
            tool_name,
            status,
            json.dumps(parameters),
            json.dumps(result),
            error_message,
            created_at,
            completed_at
        ))

        conn.commit()
        conn.close()
    except Exception as e:
        log_error(f"Failed to save job: {e}")


def get_jobs(limit=50, tool_name=None):
    """Get jobs from database"""
    if not database_path:
        return []

    try:
        conn = sqlite3.connect(database_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if tool_name:
            cursor.execute('''
                SELECT * FROM jobs
                WHERE tool_name = ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (tool_name, limit))
        else:
            cursor.execute('''
                SELECT * FROM jobs
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))

        rows = cursor.fetchall()
        conn.close()

        jobs = []
        for row in rows:
            jobs.append({
                'job_id': row['job_id'],
                'tool_name': row['tool_name'],
                'status': row['status'],
                'parameters': json.loads(row['parameters']) if row['parameters'] else {},
                'result': json.loads(row['result']) if row['result'] else {},
                'error': row['error_message'],
                'created_at': row['created_at'],
                'completed_at': row['completed_at']
            })

        return jobs
    except Exception as e:
        log_error(f"Failed to get jobs: {e}")
        return []


def get_job_stats():
    """Get statistics about jobs"""
    if not database_path:
        return {}

    try:
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()

        # Total jobs
        cursor.execute('SELECT COUNT(*) FROM jobs')
        total_jobs = cursor.fetchone()[0]

        # Jobs by status
        cursor.execute('SELECT status, COUNT(*) FROM jobs GROUP BY status')
        by_status = {row[0]: row[1] for row in cursor.fetchall()}

        # Jobs by tool
        cursor.execute('SELECT tool_name, COUNT(*) FROM jobs GROUP BY tool_name ORDER BY COUNT(*) DESC LIMIT 10')
        by_tool = [{'tool_name': row[0], 'count': row[1]} for row in cursor.fetchall()]

        conn.close()

        return {
            'total_jobs': total_jobs,
            'by_status': by_status,
            'top_tools': by_tool
        }
    except Exception as e:
        log_error(f"Failed to get job stats: {e}")
        return {}


def setup_environment(db_path: str, upload_dir: str, logs_dir: str):
    """
    Setup environment for mobile backend
    """
    global database_path, upload_path, logs_path

    database_path = db_path
    upload_path = upload_dir
    logs_path = logs_dir

    # Create directories (without pathlib to be faster)
    for path in [upload_dir, logs_dir]:
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)

    # Set environment variables
    os.environ['DATA20_DATABASE_PATH'] = db_path
    os.environ['DATA20_UPLOAD_PATH'] = upload_dir
    os.environ['DATA20_LOGS_PATH'] = logs_dir
    os.environ['ENVIRONMENT'] = 'mobile'

    log_info("Environment configured (Lite):")
    log_info(f"  Database: {db_path}")
    log_info(f"  Uploads: {upload_dir}")
    log_info(f"  Logs: {logs_dir}")

    # Initialize database
    init_database()


def run_server(host: str = "127.0.0.1", port: int = 8001):
    """
    Run simple HTTP server with /health endpoint

    NOTE: This is a SIMPLIFIED version using only Python standard library.
    NO pip dependencies - uses http.server from stdlib.
    """
    global is_running, http_server

    try:
        log_info(f"Starting Lite HTTP backend on {host}:{port}")
        log_info("Python backend initialized successfully!")
        log_info("  Using http.server from Python standard library")
        log_info("  Lite version: 12 essential tools")

        # Create HTTP server
        server_address = (host, port)
        http_server = HTTPServer(server_address, SimpleBackendHandler)

        is_running = True

        log_info(f"HTTP server listening on {host}:{port}")
        log_info("Backend is ready to accept requests!")

        # Serve requests (blocking call)
        http_server.serve_forever()

    except Exception as e:
        log_error(f"Failed to start server: {e}")
        import traceback
        traceback.print_exc()
        is_running = False
        raise
    finally:
        if http_server:
            http_server.server_close()
        log_info("HTTP server shut down")


def stop_server():
    """
    Stop the HTTP server
    """
    global is_running, http_server

    try:
        log_info("Stopping HTTP server...")
        is_running = False

        if http_server:
            http_server.shutdown()
            http_server.server_close()
            log_info("HTTP server stopped successfully")
        else:
            log_info("No HTTP server to stop")

    except Exception as e:
        log_error(f"Error stopping server: {e}")


# For testing
if __name__ == "__main__":
    import tempfile
    temp_dir = tempfile.gettempdir()

    setup_environment(
        db_path=os.path.join(temp_dir, "test_data20_lite.db"),
        upload_dir=os.path.join(temp_dir, "data20_uploads_lite"),
        logs_dir=os.path.join(temp_dir, "data20_logs_lite")
    )

    run_server(host="127.0.0.1", port=8001)
