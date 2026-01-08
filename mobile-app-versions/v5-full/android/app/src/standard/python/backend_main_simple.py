"""
Standard Mobile Backend - 35 tools with real implementations
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
                'service': 'data20-mobile-backend-standard',
                'version': 'standard-0.2.1',
                'git_commit': 'cce8ecd',
                'build_timestamp': datetime.now().isoformat(),
                'features': {
                    'real_implementations': True,
                    'database': True,
                    'tools_count': len(MOCK_TOOLS),
                    'implementations_count': len(TOOL_IMPLEMENTATIONS)
                },
                'message': 'Standard backend: 35 professional tools'
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
                <title>Data20 Mobile Backend - Standard</title>
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
                <h1>Data20 Mobile Backend - Standard</h1>
                <p>Status: <strong class="status">Running</strong></p>
                <p>Version: <span class="version">standard-0.2.1</span></p>
                <p class="feature">✅ 35 professional tools</p>
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
    },
    {
        "name": "text_summarize",
        "display_name": "Суммаризация текста",
        "description": "Извлечение ключевых предложений из текста",
        "category": "nlp",
        "parameters": {
            "text": {
                "type": "string",
                "required": True,
                "description": "Текст для суммаризации"
            },
            "sentences": {
                "type": "integer",
                "required": False,
                "default": 3,
                "description": "Количество предложений в резюме"
            }
        }
    },
    {
        "name": "string_reverse",
        "display_name": "Реверс строки",
        "description": "Переворачивание строки задом наперёд",
        "category": "text",
        "parameters": {
            "text": {
                "type": "string",
                "required": True,
                "description": "Текст для реверса"
            }
        }
    },
    {
        "name": "string_case_converter",
        "display_name": "Конвертер регистра",
        "description": "Изменение регистра букв в тексте",
        "category": "text",
        "parameters": {
            "text": {
                "type": "string",
                "required": True,
                "description": "Текст для обработки"
            },
            "case": {
                "type": "string",
                "required": True,
                "enum": ["upper", "lower", "title", "capitalize"],
                "description": "Тип регистра"
            }
        }
    },
    {
        "name": "number_converter",
        "display_name": "Конвертер систем счисления",
        "description": "Перевод чисел между системами счисления",
        "category": "math",
        "parameters": {
            "number": {
                "type": "string",
                "required": True,
                "description": "Число для конвертации"
            },
            "from_base": {
                "type": "string",
                "required": True,
                "enum": ["bin", "oct", "dec", "hex"],
                "description": "Исходная система"
            },
            "to_base": {
                "type": "string",
                "required": True,
                "enum": ["bin", "oct", "dec", "hex"],
                "description": "Целевая система"
            }
        }
    },
    {
        "name": "random_generator",
        "display_name": "Генератор случайных чисел",
        "description": "Генерация случайных чисел в заданном диапазоне",
        "category": "math",
        "parameters": {
            "min": {
                "type": "number",
                "required": False,
                "default": 0,
                "description": "Минимальное значение"
            },
            "max": {
                "type": "number",
                "required": False,
                "default": 100,
                "description": "Максимальное значение"
            },
            "count": {
                "type": "integer",
                "required": False,
                "default": 1,
                "description": "Количество чисел"
            }
        }
    },
    {
        "name": "uuid_generator",
        "display_name": "Генератор UUID",
        "description": "Генерация уникальных идентификаторов UUID",
        "category": "other",
        "parameters": {
            "version": {
                "type": "integer",
                "required": False,
                "default": 4,
                "enum": [1, 4],
                "description": "Версия UUID"
            },
            "count": {
                "type": "integer",
                "required": False,
                "default": 1,
                "description": "Количество UUID"
            }
        }
    },
    {
        "name": "text_duplicate_remover",
        "display_name": "Удаление дубликатов строк",
        "description": "Удаление повторяющихся строк из текста",
        "category": "text",
        "parameters": {
            "text": {
                "type": "string",
                "required": True,
                "description": "Текст с дубликатами"
            },
            "case_sensitive": {
                "type": "boolean",
                "required": False,
                "default": False,
                "description": "Учитывать регистр"
            }
        }
    },
    {
        "name": "list_operations",
        "display_name": "Операции со списками",
        "description": "Различные операции со списками данных",
        "category": "cleaning",
        "parameters": {
            "data": {
                "type": "array",
                "required": True,
                "description": "Массив данных"
            },
            "operation": {
                "type": "string",
                "required": True,
                "enum": ["sort_asc", "sort_desc", "unique", "reverse", "shuffle"],
                "description": "Операция"
            }
        }
    },
    {
        "name": "math_operations",
        "display_name": "Математические операции",
        "description": "Базовые математические вычисления",
        "category": "math",
        "parameters": {
            "a": {
                "type": "number",
                "required": True,
                "description": "Первое число"
            },
            "b": {
                "type": "number",
                "required": True,
                "description": "Второе число"
            },
            "operation": {
                "type": "string",
                "required": True,
                "enum": ["add", "subtract", "multiply", "divide", "power", "modulo"],
                "description": "Операция"
            }
        }
    },
    {
        "name": "percentage_calculator",
        "display_name": "Калькулятор процентов",
        "description": "Расчёт процентов и процентных соотношений",
        "category": "math",
        "parameters": {
            "value": {
                "type": "number",
                "required": True,
                "description": "Значение"
            },
            "percent": {
                "type": "number",
                "required": True,
                "description": "Процент"
            },
            "operation": {
                "type": "string",
                "required": True,
                "enum": ["calc_percent", "find_percent", "increase", "decrease"],
                "description": "Тип операции"
            }
        }
    },
    {
        "name": "unit_converter",
        "display_name": "Конвертер единиц",
        "description": "Конвертация единиц измерения (температура, длина, вес)",
        "category": "other",
        "parameters": {
            "value": {
                "type": "number",
                "required": True,
                "description": "Значение"
            },
            "from_unit": {
                "type": "string",
                "required": True,
                "description": "Исходная единица"
            },
            "to_unit": {
                "type": "string",
                "required": True,
                "description": "Целевая единица"
            }
        }
    },
    {
        "name": "color_converter",
        "display_name": "Конвертер цветов",
        "description": "Конвертация между форматами цветов (RGB/HEX)",
        "category": "other",
        "parameters": {
            "color": {
                "type": "string",
                "required": True,
                "description": "Цвет для конвертации"
            },
            "from_format": {
                "type": "string",
                "required": True,
                "enum": ["rgb", "hex"],
                "description": "Исходный формат"
            },
            "to_format": {
                "type": "string",
                "required": True,
                "enum": ["rgb", "hex"],
                "description": "Целевой формат"
            }
        }
    },
    {
        "name": "file_size_formatter",
        "display_name": "Форматирование размера файлов",
        "description": "Конвертация размера файлов в читаемый формат",
        "category": "other",
        "parameters": {
            "bytes": {
                "type": "integer",
                "required": True,
                "description": "Размер в байтах"
            }
        }
    },
    {
        "name": "timestamp_converter",
        "display_name": "Конвертер timestamp",
        "description": "Конвертация между timestamp и датой",
        "category": "other",
        "parameters": {
            "value": {
                "type": "string",
                "required": True,
                "description": "Timestamp или дата"
            },
            "operation": {
                "type": "string",
                "required": True,
                "enum": ["to_date", "to_timestamp"],
                "description": "Направление конвертации"
            }
        }
    },
    {
        "name": "text_diff",
        "display_name": "Сравнение текстов",
        "description": "Поиск различий между двумя текстами",
        "category": "text",
        "parameters": {
            "text1": {
                "type": "string",
                "required": True,
                "description": "Первый текст"
            },
            "text2": {
                "type": "string",
                "required": True,
                "description": "Второй текст"
            }
        }
    },
    {
        "name": "string_similarity",
        "display_name": "Схожесть строк",
        "description": "Вычисление степени схожести строк",
        "category": "text",
        "parameters": {
            "text1": {
                "type": "string",
                "required": True,
                "description": "Первая строка"
            },
            "text2": {
                "type": "string",
                "required": True,
                "description": "Вторая строка"
            }
        }
    },
    {
        "name": "morse_code",
        "display_name": "Азбука Морзе",
        "description": "Кодирование/декодирование азбуки Морзе",
        "category": "transformation",
        "parameters": {
            "text": {
                "type": "string",
                "required": True,
                "description": "Текст для обработки"
            },
            "operation": {
                "type": "string",
                "required": True,
                "enum": ["encode", "decode"],
                "description": "Операция"
            }
        }
    },
    {
        "name": "roman_numerals",
        "display_name": "Римские цифры",
        "description": "Конвертация между римскими и арабскими цифрами",
        "category": "math",
        "parameters": {
            "value": {
                "type": "string",
                "required": True,
                "description": "Число для конвертации"
            },
            "direction": {
                "type": "string",
                "required": True,
                "enum": ["to_roman", "from_roman"],
                "description": "Направление конвертации"
            }
        }
    },
    {
        "name": "password_generator",
        "display_name": "Генератор паролей",
        "description": "Генерация безопасных паролей",
        "category": "other",
        "parameters": {
            "length": {
                "type": "integer",
                "required": False,
                "default": 16,
                "description": "Длина пароля"
            },
            "include_numbers": {
                "type": "boolean",
                "required": False,
                "default": True,
                "description": "Включать цифры"
            },
            "include_symbols": {
                "type": "boolean",
                "required": False,
                "default": True,
                "description": "Включать символы"
            }
        }
    },
    {
        "name": "acronym_generator",
        "display_name": "Генератор акронимов",
        "description": "Создание акронимов из фраз",
        "category": "text",
        "parameters": {
            "text": {
                "type": "string",
                "required": True,
                "description": "Фраза для акронима"
            }
        }
    },
    {
        "name": "data_cleaning",
        "display_name": "Очистка данных",
        "description": "Удаление пустых значений и выбросов из массива",
        "category": "cleaning",
        "parameters": {
            "data": {
                "type": "array",
                "required": True,
                "description": "Массив данных"
            },
            "remove_nulls": {
                "type": "boolean",
                "required": False,
                "default": True,
                "description": "Удалить пустые значения"
            }
        }
    },
    {
        "name": "sentiment_analysis",
        "display_name": "Анализ тональности",
        "description": "Простой анализ тональности текста на основе ключевых слов",
        "category": "nlp",
        "parameters": {
            "text": {
                "type": "string",
                "required": True,
                "description": "Текст для анализа"
            }
        }
    },
    {
        "name": "ip_validator",
        "display_name": "Валидатор IP адресов",
        "description": "Проверка валидности IP адресов (IPv4/IPv6)",
        "category": "other",
        "parameters": {
            "ip": {
                "type": "string",
                "required": True,
                "description": "IP адрес"
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


def text_summarize_impl(params):
    """Extract key sentences from text (simple extractive summarization)"""
    text = params.get('text', '')
    sentences_count = params.get('sentences', 3)

    # Split into sentences
    import re
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    if len(sentences) <= sentences_count:
        return {
            'summary': text,
            'original_sentences': len(sentences),
            'summary_sentences': len(sentences)
        }

    # Simple scoring: longer sentences are more important
    scored = [(len(s.split()), s) for s in sentences]
    scored.sort(reverse=True)

    # Take top N sentences
    top_sentences = [s for _, s in scored[:sentences_count]]

    return {
        'summary': '. '.join(top_sentences) + '.',
        'original_sentences': len(sentences),
        'summary_sentences': sentences_count
    }


def string_reverse_impl(params):
    """Reverse a string"""
    text = params.get('text', '')
    return {
        'original': text,
        'reversed': text[::-1],
        'length': len(text)
    }


def string_case_converter_impl(params):
    """Convert string case"""
    text = params.get('text', '')
    case = params.get('case', 'upper')

    conversions = {
        'upper': text.upper(),
        'lower': text.lower(),
        'title': text.title(),
        'capitalize': text.capitalize()
    }

    result = conversions.get(case, text)

    return {
        'original': text,
        'converted': result,
        'case_type': case
    }


def number_converter_impl(params):
    """Convert numbers between bases"""
    number_str = params.get('number', '0')
    from_base = params.get('from_base', 'dec')
    to_base = params.get('to_base', 'dec')

    bases = {'bin': 2, 'oct': 8, 'dec': 10, 'hex': 16}

    try:
        # Convert to decimal first
        decimal_value = int(number_str, bases[from_base])

        # Convert to target base
        if to_base == 'bin':
            result = bin(decimal_value)[2:]
        elif to_base == 'oct':
            result = oct(decimal_value)[2:]
        elif to_base == 'dec':
            result = str(decimal_value)
        elif to_base == 'hex':
            result = hex(decimal_value)[2:]
        else:
            result = str(decimal_value)

        return {
            'original': number_str,
            'from_base': from_base,
            'to_base': to_base,
            'result': result,
            'decimal_value': decimal_value
        }
    except Exception as e:
        return {'error': str(e)}


def random_generator_impl(params):
    """Generate random numbers"""
    import random

    min_val = params.get('min', 0)
    max_val = params.get('max', 100)
    count = params.get('count', 1)

    numbers = [random.randint(int(min_val), int(max_val)) for _ in range(count)]

    return {
        'numbers': numbers,
        'count': len(numbers),
        'min': min_val,
        'max': max_val
    }


def uuid_generator_impl(params):
    """Generate UUIDs"""
    import uuid

    version = params.get('version', 4)
    count = params.get('count', 1)

    uuids = []
    for _ in range(count):
        if version == 1:
            uuids.append(str(uuid.uuid1()))
        else:  # version 4
            uuids.append(str(uuid.uuid4()))

    return {
        'uuids': uuids,
        'count': len(uuids),
        'version': version
    }


def text_duplicate_remover_impl(params):
    """Remove duplicate lines from text"""
    text = params.get('text', '')
    case_sensitive = params.get('case_sensitive', False)

    lines = text.split('\n')
    seen = set()
    unique_lines = []

    for line in lines:
        check_line = line if case_sensitive else line.lower()
        if check_line not in seen:
            seen.add(check_line)
            unique_lines.append(line)

    return {
        'original_lines': len(lines),
        'unique_lines': len(unique_lines),
        'duplicates_removed': len(lines) - len(unique_lines),
        'result': '\n'.join(unique_lines)
    }


def list_operations_impl(params):
    """Perform operations on lists"""
    import random

    data = params.get('data', [])
    operation = params.get('operation', 'sort_asc')

    result_data = data.copy()

    if operation == 'sort_asc':
        result_data.sort()
    elif operation == 'sort_desc':
        result_data.sort(reverse=True)
    elif operation == 'unique':
        seen = set()
        result_data = []
        for item in data:
            if item not in seen:
                seen.add(item)
                result_data.append(item)
    elif operation == 'reverse':
        result_data.reverse()
    elif operation == 'shuffle':
        random.shuffle(result_data)

    return {
        'operation': operation,
        'original_count': len(data),
        'result_count': len(result_data),
        'result': result_data
    }


def math_operations_impl(params):
    """Perform basic math operations"""
    a = params.get('a', 0)
    b = params.get('b', 0)
    operation = params.get('operation', 'add')

    operations = {
        'add': a + b,
        'subtract': a - b,
        'multiply': a * b,
        'divide': a / b if b != 0 else 'Error: Division by zero',
        'power': a ** b,
        'modulo': a % b if b != 0 else 'Error: Division by zero'
    }

    result = operations.get(operation, 0)

    return {
        'a': a,
        'b': b,
        'operation': operation,
        'result': result
    }


def percentage_calculator_impl(params):
    """Calculate percentages"""
    value = params.get('value', 0)
    percent = params.get('percent', 0)
    operation = params.get('operation', 'calc_percent')

    if operation == 'calc_percent':
        # Calculate X% of value
        result = (value * percent) / 100
    elif operation == 'find_percent':
        # What percent is 'percent' of 'value'
        result = (percent / value * 100) if value != 0 else 0
    elif operation == 'increase':
        # Increase value by percent%
        result = value + (value * percent / 100)
    elif operation == 'decrease':
        # Decrease value by percent%
        result = value - (value * percent / 100)
    else:
        result = 0

    return {
        'value': value,
        'percent': percent,
        'operation': operation,
        'result': result
    }


def unit_converter_impl(params):
    """Convert between units"""
    value = params.get('value', 0)
    from_unit = params.get('from_unit', '').lower()
    to_unit = params.get('to_unit', '').lower()

    # Temperature conversions
    temp_conversions = {
        ('celsius', 'fahrenheit'): lambda x: x * 9/5 + 32,
        ('fahrenheit', 'celsius'): lambda x: (x - 32) * 5/9,
        ('celsius', 'kelvin'): lambda x: x + 273.15,
        ('kelvin', 'celsius'): lambda x: x - 273.15,
    }

    # Length conversions (to meters)
    length_to_meters = {
        'km': 1000, 'm': 1, 'cm': 0.01, 'mm': 0.001,
        'mile': 1609.34, 'yard': 0.9144, 'foot': 0.3048, 'inch': 0.0254
    }

    # Weight conversions (to kg)
    weight_to_kg = {
        'kg': 1, 'g': 0.001, 'mg': 0.000001,
        'lb': 0.453592, 'oz': 0.0283495
    }

    # Try temperature conversion
    key = (from_unit, to_unit)
    if key in temp_conversions:
        result = temp_conversions[key](value)
        return {
            'value': value,
            'from_unit': from_unit,
            'to_unit': to_unit,
            'result': result,
            'category': 'temperature'
        }

    # Try length conversion
    if from_unit in length_to_meters and to_unit in length_to_meters:
        meters = value * length_to_meters[from_unit]
        result = meters / length_to_meters[to_unit]
        return {
            'value': value,
            'from_unit': from_unit,
            'to_unit': to_unit,
            'result': result,
            'category': 'length'
        }

    # Try weight conversion
    if from_unit in weight_to_kg and to_unit in weight_to_kg:
        kg = value * weight_to_kg[from_unit]
        result = kg / weight_to_kg[to_unit]
        return {
            'value': value,
            'from_unit': from_unit,
            'to_unit': to_unit,
            'result': result,
            'category': 'weight'
        }

    return {'error': f'Conversion from {from_unit} to {to_unit} not supported'}


def color_converter_impl(params):
    """Convert between color formats"""
    color = params.get('color', '')
    from_format = params.get('from_format', 'hex')
    to_format = params.get('to_format', 'rgb')

    try:
        if from_format == 'hex' and to_format == 'rgb':
            # Remove # if present
            hex_color = color.lstrip('#')
            # Convert to RGB
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            result = f'rgb({r}, {g}, {b})'
            return {
                'original': color,
                'from_format': from_format,
                'to_format': to_format,
                'result': result,
                'rgb': {'r': r, 'g': g, 'b': b}
            }
        elif from_format == 'rgb' and to_format == 'hex':
            # Extract RGB values
            import re
            match = re.match(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', color)
            if match:
                r, g, b = map(int, match.groups())
                result = f'#{r:02x}{g:02x}{b:02x}'
                return {
                    'original': color,
                    'from_format': from_format,
                    'to_format': to_format,
                    'result': result,
                    'rgb': {'r': r, 'g': g, 'b': b}
                }
        return {'error': 'Invalid color format'}
    except Exception as e:
        return {'error': str(e)}


def file_size_formatter_impl(params):
    """Format file size in human-readable format"""
    bytes_val = params.get('bytes', 0)

    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    size = float(bytes_val)
    unit_index = 0

    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    return {
        'bytes': bytes_val,
        'formatted': f'{size:.2f} {units[unit_index]}',
        'size': round(size, 2),
        'unit': units[unit_index]
    }


def timestamp_converter_impl(params):
    """Convert between timestamp and date"""
    from datetime import datetime

    value = params.get('value', '')
    operation = params.get('operation', 'to_date')

    try:
        if operation == 'to_date':
            # Convert timestamp to date
            timestamp = int(value)
            dt = datetime.fromtimestamp(timestamp)
            return {
                'timestamp': timestamp,
                'date': dt.strftime('%Y-%m-%d %H:%M:%S'),
                'iso': dt.isoformat()
            }
        else:  # to_timestamp
            # Convert date to timestamp
            dt = datetime.fromisoformat(value)
            timestamp = int(dt.timestamp())
            return {
                'date': value,
                'timestamp': timestamp,
                'iso': dt.isoformat()
            }
    except Exception as e:
        return {'error': str(e)}


def text_diff_impl(params):
    """Find differences between two texts"""
    text1 = params.get('text1', '')
    text2 = params.get('text2', '')

    lines1 = text1.split('\n')
    lines2 = text2.split('\n')

    # Simple line-by-line comparison
    added = [line for line in lines2 if line not in lines1]
    removed = [line for line in lines1 if line not in lines2]
    common = [line for line in lines1 if line in lines2]

    return {
        'added_lines': len(added),
        'removed_lines': len(removed),
        'common_lines': len(common),
        'added': added[:10],  # First 10
        'removed': removed[:10]  # First 10
    }


def string_similarity_impl(params):
    """Calculate string similarity (simple algorithm)"""
    text1 = params.get('text1', '')
    text2 = params.get('text2', '')

    # Simple similarity: count matching characters
    if not text1 or not text2:
        return {'similarity': 0.0, 'method': 'character_match'}

    matches = sum(1 for a, b in zip(text1, text2) if a == b)
    max_len = max(len(text1), len(text2))
    similarity = matches / max_len if max_len > 0 else 0

    return {
        'text1_length': len(text1),
        'text2_length': len(text2),
        'matches': matches,
        'similarity': round(similarity, 3),
        'similarity_percent': round(similarity * 100, 1),
        'method': 'character_match'
    }


def morse_code_impl(params):
    """Encode/decode Morse code"""
    text = params.get('text', '')
    operation = params.get('operation', 'encode')

    morse_dict = {
        'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.',
        'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..',
        'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.',
        'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
        'Y': '-.--', 'Z': '--..', '0': '-----', '1': '.----', '2': '..---',
        '3': '...--', '4': '....-', '5': '.....', '6': '-....', '7': '--...',
        '8': '---..', '9': '----.', ' ': '/'
    }

    if operation == 'encode':
        result = ' '.join(morse_dict.get(c.upper(), '') for c in text)
        return {'original': text, 'morse': result, 'operation': 'encode'}
    else:  # decode
        reverse_dict = {v: k for k, v in morse_dict.items()}
        words = text.split(' / ')
        decoded = ' '.join(''.join(reverse_dict.get(code, '') for code in word.split(' ')) for word in words)
        return {'morse': text, 'decoded': decoded, 'operation': 'decode'}


def roman_numerals_impl(params):
    """Convert between Roman and Arabic numerals"""
    value = params.get('value', '')
    direction = params.get('direction', 'to_roman')

    if direction == 'to_roman':
        # Arabic to Roman
        try:
            num = int(value)
            val_map = [
                (1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'),
                (100, 'C'), (90, 'XC'), (50, 'L'), (40, 'XL'),
                (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')
            ]
            result = ''
            for val, letter in val_map:
                count = num // val
                if count:
                    result += letter * count
                    num -= val * count
            return {'arabic': int(value), 'roman': result}
        except:
            return {'error': 'Invalid number'}
    else:  # from_roman
        # Roman to Arabic
        roman_map = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
        result = 0
        prev_val = 0
        for char in reversed(value.upper()):
            val = roman_map.get(char, 0)
            if val < prev_val:
                result -= val
            else:
                result += val
            prev_val = val
        return {'roman': value, 'arabic': result}


def password_generator_impl(params):
    """Generate secure passwords"""
    import random
    import string

    length = params.get('length', 16)
    include_numbers = params.get('include_numbers', True)
    include_symbols = params.get('include_symbols', True)

    chars = string.ascii_letters
    if include_numbers:
        chars += string.digits
    if include_symbols:
        chars += string.punctuation

    password = ''.join(random.choice(chars) for _ in range(length))

    return {
        'password': password,
        'length': len(password),
        'includes_numbers': include_numbers,
        'includes_symbols': include_symbols
    }


def acronym_generator_impl(params):
    """Generate acronym from phrase"""
    text = params.get('text', '')

    words = text.split()
    acronym = ''.join(word[0].upper() for word in words if word)

    return {
        'phrase': text,
        'acronym': acronym,
        'words_count': len(words)
    }


def data_cleaning_impl(params):
    """Clean data array"""
    data = params.get('data', [])
    remove_nulls = params.get('remove_nulls', True)

    cleaned = []
    removed_count = 0

    for item in data:
        if remove_nulls and (item is None or item == '' or (isinstance(item, str) and not item.strip())):
            removed_count += 1
        else:
            cleaned.append(item)

    return {
        'original_count': len(data),
        'cleaned_count': len(cleaned),
        'removed_count': removed_count,
        'cleaned_data': cleaned
    }


def sentiment_analysis_impl(params):
    """Simple sentiment analysis based on keywords"""
    text = params.get('text', '').lower()

    positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'love', 'best', 'happy', 'хорошо', 'отлично', 'прекрасно']
    negative_words = ['bad', 'terrible', 'awful', 'worst', 'hate', 'horrible', 'poor', 'плохо', 'ужасно', 'худший']

    positive_count = sum(1 for word in positive_words if word in text)
    negative_count = sum(1 for word in negative_words if word in text)

    if positive_count > negative_count:
        sentiment = 'positive'
        score = 0.6 + (positive_count - negative_count) * 0.1
    elif negative_count > positive_count:
        sentiment = 'negative'
        score = 0.4 - (negative_count - positive_count) * 0.1
    else:
        sentiment = 'neutral'
        score = 0.5

    return {
        'sentiment': sentiment,
        'score': max(0, min(1, score)),
        'positive_indicators': positive_count,
        'negative_indicators': negative_count
    }


def ip_validator_impl(params):
    """Validate IP addresses"""
    import re

    ip = params.get('ip', '')

    # IPv4 pattern
    ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    # IPv6 pattern (simplified)
    ipv6_pattern = r'^([0-9a-fA-F]{0,4}:){7}[0-9a-fA-F]{0,4}$'

    is_ipv4 = bool(re.match(ipv4_pattern, ip))
    is_ipv6 = bool(re.match(ipv6_pattern, ip))

    if is_ipv4:
        # Validate ranges
        parts = ip.split('.')
        valid = all(0 <= int(part) <= 255 for part in parts)
        return {
            'ip': ip,
            'valid': valid,
            'type': 'IPv4'
        }
    elif is_ipv6:
        return {
            'ip': ip,
            'valid': True,
            'type': 'IPv6'
        }
    else:
        return {
            'ip': ip,
            'valid': False,
            'type': 'unknown'
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
    # Standard version additional tools
    'text_summarize': text_summarize_impl,
    'string_reverse': string_reverse_impl,
    'string_case_converter': string_case_converter_impl,
    'number_converter': number_converter_impl,
    'random_generator': random_generator_impl,
    'uuid_generator': uuid_generator_impl,
    'text_duplicate_remover': text_duplicate_remover_impl,
    'list_operations': list_operations_impl,
    'math_operations': math_operations_impl,
    'percentage_calculator': percentage_calculator_impl,
    'unit_converter': unit_converter_impl,
    'color_converter': color_converter_impl,
    'file_size_formatter': file_size_formatter_impl,
    'timestamp_converter': timestamp_converter_impl,
    'text_diff': text_diff_impl,
    'string_similarity': string_similarity_impl,
    'morse_code': morse_code_impl,
    'roman_numerals': roman_numerals_impl,
    'password_generator': password_generator_impl,
    'acronym_generator': acronym_generator_impl,
    'data_cleaning': data_cleaning_impl,
    'sentiment_analysis': sentiment_analysis_impl,
    'ip_validator': ip_validator_impl,
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

    log_info("Environment configured (Standard):")
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
        log_info(f"Starting Standard HTTP backend on {host}:{port}")
        log_info("Python backend initialized successfully!")
        log_info("  Using http.server from Python standard library")
        log_info("  Standard version: 35 professional tools")

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
        db_path=os.path.join(temp_dir, "test_data20_standard.db"),
        upload_dir=os.path.join(temp_dir, "data20_uploads_standard"),
        logs_dir=os.path.join(temp_dir, "data20_logs_standard")
    )

    run_server(host="127.0.0.1", port=8002)
