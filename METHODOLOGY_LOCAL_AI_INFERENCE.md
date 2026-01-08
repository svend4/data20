# 🤖 МЕТОДОЛОГИЯ: Локальный AI/ML Inference для Flutter приложений

## 📋 Содержание

1. [Вариант 1: Ollama/LM Studio (Готовые решения)](#вариант-1-ollamlm-studio)
2. [Вариант 2: Desktop Server DIY ML Stack](#вариант-2-desktop-server-diy-ml-stack)
3. [Интеграция с Flutter](#интеграция-с-flutter)
4. [Сравнение и выбор](#сравнение-и-выбор)
5. [Troubleshooting](#troubleshooting)

---

# ВАРИАНТ 1: Ollama/LM Studio (Готовые решения)

## 🎯 Для кого: Пользователи без глубоких знаний ML

**Цель:** Запустить локальную LLM модель за 10 минут

---

## 1.1 Установка Ollama

### Windows:

```powershell
# Скачать с официального сайта
https://ollama.ai/download

# Или через winget
winget install Ollama.Ollama

# Проверка установки
ollama --version
```

### macOS:

```bash
# Homebrew
brew install ollama

# Или скачать DMG
# https://ollama.ai/download
```

### Linux:

```bash
# Универсальный установщик
curl https://ollama.ai/install.sh | sh

# Проверка
ollama --version
```

---

## 1.2 Загрузка и запуск моделей

### Шаг 1: Выбор модели

```bash
# Список доступных моделей
ollama list

# Популярные модели:
# - llama2 (7B) - базовая модель, ~4 ГБ
# - llama2:13b - больше модель, ~8 ГБ
# - mistral - быстрая модель, ~4 ГБ
# - codellama - для программирования
# - phi - маленькая модель, ~2 ГБ
```

### Шаг 2: Загрузка модели

```bash
# Загрузить модель (автоматически скачает при первом запуске)
ollama pull llama2

# Для русского языка лучше:
ollama pull llama2:13b

# Для кода:
ollama pull codellama
```

### Шаг 3: Запуск модели

```bash
# Интерактивный режим
ollama run llama2

# Теперь можно писать в чат:
# >>> Привет! Расскажи про Python
# >>> /bye  # выход
```

---

## 1.3 Настройка API сервера

### Автоматический запуск сервера:

```bash
# Ollama автоматически запускает API при установке
# API доступен на: http://localhost:11434

# Проверка работы API
curl http://localhost:11434/api/tags
```

### Настройка параметров:

```bash
# Переменные окружения (Windows PowerShell)
$env:OLLAMA_HOST = "0.0.0.0:11434"  # Доступ из сети
$env:OLLAMA_MODELS = "D:\Models"     # Путь для моделей

# Linux/macOS
export OLLAMA_HOST=0.0.0.0:11434
export OLLAMA_MODELS=/path/to/models
```

---

## 1.4 Использование API

### Базовый запрос:

```bash
# Генерация текста
curl http://localhost:11434/api/generate -d '{
  "model": "llama2",
  "prompt": "Привет! Расскажи про Python",
  "stream": false
}'

# Ответ:
{
  "model": "llama2",
  "created_at": "2024-01-08T...",
  "response": "Python - это высокоуровневый...",
  "done": true
}
```

### Streaming режим:

```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama2",
  "prompt": "Напиши стих",
  "stream": true
}'

# Ответ приходит частями (Server-Sent Events)
data: {"response": "В"}
data: {"response": " поле"}
data: {"response": " берёзка"}
...
```

### Чат режим (с контекстом):

```bash
curl http://localhost:11434/api/chat -d '{
  "model": "llama2",
  "messages": [
    {"role": "user", "content": "Привет! Меня зовут Иван"},
    {"role": "assistant", "content": "Здравствуй, Иван!"},
    {"role": "user", "content": "Как меня зовут?"}
  ]
}'

# Ответ: "Тебя зовут Иван"
```

---

## 1.5 Установка LM Studio (альтернатива с GUI)

### Шаг 1: Установка

```
1. Скачать: https://lmstudio.ai/
2. Установить (Windows/Mac/Linux)
3. Запустить LM Studio
```

### Шаг 2: Загрузка модели через GUI

```
1. Открыть вкладку "Discover"
2. Найти модель (например, "llama-2-7b-chat")
3. Нажать "Download"
4. Дождаться загрузки
```

### Шаг 3: Запуск модели

```
1. Вкладка "Chat"
2. Выбрать модель из списка
3. Настроить параметры:
   - Temperature: 0.7 (креативность)
   - Max tokens: 2048 (длина ответа)
   - Top P: 0.9
4. Начать чат
```

### Шаг 4: Включение API сервера

```
1. Вкладка "Local Server"
2. Выбрать модель
3. Нажать "Start Server"
4. API доступен на http://localhost:1234
```

---

## 1.6 Оптимизация производительности

### Выбор модели по мощности:

| Модель | Размер | RAM | GPU | Скорость |
|--------|--------|-----|-----|----------|
| phi-2 | 2.7B | 4 ГБ | Опц. | ⚡⚡⚡ Быстро |
| llama2 | 7B | 8 ГБ | Опц. | ⚡⚡ Средне |
| llama2:13b | 13B | 16 ГБ | Желат. | ⚡ Медленно |
| llama2:70b | 70B | 64 ГБ | Требуется | 🐌 Очень медленно |

### Настройка GPU ускорения:

```bash
# Ollama автоматически использует GPU если доступна

# Проверка использования GPU
nvidia-smi  # NVIDIA
rocm-smi    # AMD

# Принудительное использование CPU
OLLAMA_GPU=0 ollama run llama2
```

### Оптимизация параметров:

```json
{
  "model": "llama2",
  "prompt": "...",
  "options": {
    "num_ctx": 2048,        // Размер контекста (меньше = быстрее)
    "num_gpu": 1,           // Количество GPU слоев
    "num_thread": 8,        // CPU потоки
    "temperature": 0.7,     // Креативность (0-1)
    "top_p": 0.9,          // Nucleus sampling
    "repeat_penalty": 1.1   // Избегание повторов
  }
}
```

---

## 1.7 Продвинутое использование

### Использование системных промптов:

```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama2",
  "system": "Ты - эксперт по Python программированию. Отвечай кратко и по делу.",
  "prompt": "Как создать список в Python?"
}'
```

### Создание кастомных моделей (Modelfile):

```dockerfile
# Modelfile
FROM llama2

# Системный промпт
SYSTEM """
Ты - ассистент по Data Science.
Специализируешься на Python, pandas, numpy.
Всегда показываешь примеры кода.
"""

# Параметры
PARAMETER temperature 0.5
PARAMETER top_p 0.9
PARAMETER num_ctx 4096
```

```bash
# Создать модель
ollama create data-scientist -f Modelfile

# Использовать
ollama run data-scientist
```

### Embedding модели (векторные представления):

```bash
# Загрузить embedding модель
ollama pull nomic-embed-text

# Получить embedding
curl http://localhost:11434/api/embeddings -d '{
  "model": "nomic-embed-text",
  "prompt": "Python programming language"
}'

# Ответ: массив чисел [0.1, -0.5, 0.3, ...]
# Можно использовать для семантического поиска
```

---

# ВАРИАНТ 2: Desktop Server DIY ML Stack

## 🎯 Для кого: Разработчики с опытом Python

**Цель:** Создать гибкий ML backend с любыми моделями и задачами

---

## 2.1 Установка базового стека

### Шаг 1: Установка XAMPP

#### Windows:
```
1. Скачать: https://www.apachefriends.org/download.html
2. Запустить установщик
3. Выбрать компоненты:
   ✅ Apache
   ✅ MySQL
   ✅ PHP
   ❌ Perl (не нужен)
   ❌ FileZilla (опционально)
4. Установить в C:\xampp
5. Запустить XAMPP Control Panel
6. Start: Apache, MySQL
```

#### Linux (альтернатива - нативная установка):
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install apache2 mysql-server php libapache2-mod-php

# Включить сервисы
sudo systemctl start apache2
sudo systemctl start mysql
```

### Шаг 2: Установка Python и зависимостей

```bash
# Проверка Python
python --version  # Должна быть 3.9+

# Создание виртуального окружения
cd C:\xampp\htdocs  # или /var/www/html
mkdir ml-backend
cd ml-backend
python -m venv venv

# Активация (Windows)
venv\Scripts\activate

# Активация (Linux/Mac)
source venv/bin/activate

# Обновление pip
pip install --upgrade pip
```

### Шаг 3: Установка ML библиотек

```bash
# Основные библиотеки
pip install flask flask-cors
pip install numpy pandas scikit-learn
pip install torch torchvision torchaudio  # CPU version
# Для GPU: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# NLP библиотеки
pip install transformers
pip install sentence-transformers
pip install spacy

# Computer Vision
pip install opencv-python
pip install pillow

# Утилиты
pip install python-dotenv
pip install requests
pip install celery redis  # Для фоновых задач
```

---

## 2.2 Создание базового ML API

### Структура проекта:

```
ml-backend/
├── venv/                 # Виртуальное окружение
├── models/               # Сохраненные модели
├── uploads/              # Загруженные файлы
├── app.py               # Главный Flask сервер
├── config.py            # Конфигурация
├── requirements.txt     # Зависимости
└── services/
    ├── llm_service.py      # LLM сервис
    ├── vision_service.py   # Computer Vision
    └── audio_service.py    # Аудио обработка
```

### app.py - Главный файл:

```python
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from pathlib import Path

# Инициализация Flask
app = Flask(__name__)
CORS(app)  # Разрешить CORS для Flutter

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация
UPLOAD_FOLDER = Path('uploads')
UPLOAD_FOLDER.mkdir(exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100 МБ

# Импорт сервисов
from services.llm_service import LLMService
from services.vision_service import VisionService

# Инициализация сервисов
llm_service = LLMService()
vision_service = VisionService()

@app.route('/health', methods=['GET'])
def health_check():
    """Проверка работоспособности API"""
    return jsonify({
        'status': 'ok',
        'services': {
            'llm': llm_service.is_ready(),
            'vision': vision_service.is_ready()
        }
    })

@app.route('/api/llm/generate', methods=['POST'])
def generate_text():
    """Генерация текста через LLM"""
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')
        max_length = data.get('max_length', 200)

        logger.info(f"Generating text for prompt: {prompt[:50]}...")

        result = llm_service.generate(prompt, max_length)

        return jsonify({
            'success': True,
            'text': result['text'],
            'model': result['model'],
            'time': result['time']
        })

    except Exception as e:
        logger.error(f"Error in text generation: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/vision/classify', methods=['POST'])
def classify_image():
    """Классификация изображения"""
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image provided'}), 400

        file = request.files['image']

        # Сохранение файла
        filepath = UPLOAD_FOLDER / file.filename
        file.save(filepath)

        logger.info(f"Classifying image: {file.filename}")

        result = vision_service.classify(filepath)

        # Удаление временного файла
        filepath.unlink()

        return jsonify({
            'success': True,
            'predictions': result['predictions'],
            'model': result['model'],
            'time': result['time']
        })

    except Exception as e:
        logger.error(f"Error in image classification: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    logger.info("Starting ML Backend Server...")
    logger.info("Loading models...")

    # Предзагрузка моделей
    llm_service.load_model()
    vision_service.load_model()

    logger.info("✅ All models loaded!")
    logger.info("🚀 Server running on http://localhost:5000")

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True
    )
```

### services/llm_service.py - LLM сервис:

```python
from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
import torch
import time
from pathlib import Path

class LLMService:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.pipeline = None
        self.model_name = "distilgpt2"  # Легкая модель для старта
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    def load_model(self):
        """Загрузка модели"""
        print(f"Loading LLM model: {self.model_name} on {self.device}")

        # Можно выбрать разные модели:
        # - "distilgpt2" - быстрая, маленькая (80 МБ)
        # - "gpt2" - средняя (500 МБ)
        # - "EleutherAI/gpt-neo-1.3B" - большая (5 ГБ)

        self.pipeline = pipeline(
            "text-generation",
            model=self.model_name,
            device=0 if self.device == "cuda" else -1
        )

        print("✅ LLM model loaded")

    def generate(self, prompt, max_length=200):
        """Генерация текста"""
        if self.pipeline is None:
            raise RuntimeError("Model not loaded")

        start_time = time.time()

        # Генерация
        result = self.pipeline(
            prompt,
            max_length=max_length,
            num_return_sequences=1,
            temperature=0.7,
            top_p=0.9,
            do_sample=True
        )

        elapsed_time = time.time() - start_time

        return {
            'text': result[0]['generated_text'],
            'model': self.model_name,
            'time': round(elapsed_time, 2)
        }

    def is_ready(self):
        """Проверка готовности"""
        return self.pipeline is not None
```

### services/vision_service.py - Vision сервис:

```python
from transformers import pipeline
import torch
import time
from PIL import Image

class VisionService:
    def __init__(self):
        self.pipeline = None
        self.model_name = "google/vit-base-patch16-224"
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    def load_model(self):
        """Загрузка модели"""
        print(f"Loading Vision model: {self.model_name} on {self.device}")

        self.pipeline = pipeline(
            "image-classification",
            model=self.model_name,
            device=0 if self.device == "cuda" else -1
        )

        print("✅ Vision model loaded")

    def classify(self, image_path):
        """Классификация изображения"""
        if self.pipeline is None:
            raise RuntimeError("Model not loaded")

        start_time = time.time()

        # Открытие изображения
        image = Image.open(image_path)

        # Классификация
        results = self.pipeline(image, top_k=5)

        elapsed_time = time.time() - start_time

        return {
            'predictions': [
                {
                    'label': r['label'],
                    'score': round(r['score'], 4)
                }
                for r in results
            ],
            'model': self.model_name,
            'time': round(elapsed_time, 2)
        }

    def is_ready(self):
        """Проверка готовности"""
        return self.pipeline is not None
```

---

## 2.3 Расширенная функциональность

### Добавление русскоязычной LLM:

```python
# services/llm_service.py

class LLMService:
    def __init__(self):
        # Используем русскоязычную модель
        self.model_name = "sberbank-ai/rugpt3small_based_on_gpt2"
        # Или более мощную: "ai-forever/rugpt3large_based_on_gpt2"

    def generate_russian(self, prompt, max_length=200):
        """Генерация текста на русском"""
        result = self.pipeline(
            prompt,
            max_length=max_length,
            num_return_sequences=1,
            temperature=0.8,
            top_p=0.9,
            repetition_penalty=1.2  # Избегаем повторов
        )

        return result[0]['generated_text']
```

### Добавление Stable Diffusion:

```python
# services/image_generation_service.py

from diffusers import StableDiffusionPipeline
import torch

class ImageGenerationService:
    def __init__(self):
        self.model_name = "runwayml/stable-diffusion-v1-5"
        self.pipeline = None

    def load_model(self):
        """Загрузка Stable Diffusion"""
        print(f"Loading Stable Diffusion: {self.model_name}")

        self.pipeline = StableDiffusionPipeline.from_pretrained(
            self.model_name,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
        )

        if torch.cuda.is_available():
            self.pipeline = self.pipeline.to("cuda")

        print("✅ Stable Diffusion loaded")

    def generate_image(self, prompt, negative_prompt="", num_steps=50):
        """Генерация изображения"""
        image = self.pipeline(
            prompt,
            negative_prompt=negative_prompt,
            num_inference_steps=num_steps,
            guidance_scale=7.5
        ).images[0]

        return image
```

### Добавление речевого распознавания:

```python
# services/audio_service.py

from transformers import pipeline
import torch

class AudioService:
    def __init__(self):
        self.model_name = "openai/whisper-base"
        self.pipeline = None

    def load_model(self):
        """Загрузка Whisper"""
        print(f"Loading Whisper: {self.model_name}")

        self.pipeline = pipeline(
            "automatic-speech-recognition",
            model=self.model_name,
            device=0 if torch.cuda.is_available() else -1
        )

        print("✅ Whisper loaded")

    def transcribe(self, audio_path):
        """Транскрибация аудио"""
        result = self.pipeline(
            str(audio_path),
            return_timestamps=True
        )

        return {
            'text': result['text'],
            'chunks': result.get('chunks', [])
        }
```

---

## 2.4 Интеграция с базой данных

### MySQL для хранения истории:

```python
# database.py

import mysql.connector
from datetime import datetime
import json

class Database:
    def __init__(self):
        self.conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="ml_backend"
        )
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        """Создание таблиц"""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS requests (
                id INT AUTO_INCREMENT PRIMARY KEY,
                service VARCHAR(50),
                input_data TEXT,
                output_data TEXT,
                processing_time FLOAT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def log_request(self, service, input_data, output_data, processing_time):
        """Логирование запроса"""
        self.cursor.execute("""
            INSERT INTO requests (service, input_data, output_data, processing_time)
            VALUES (%s, %s, %s, %s)
        """, (
            service,
            json.dumps(input_data),
            json.dumps(output_data),
            processing_time
        ))
        self.conn.commit()

    def get_history(self, service=None, limit=100):
        """Получение истории"""
        if service:
            self.cursor.execute("""
                SELECT * FROM requests
                WHERE service = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (service, limit))
        else:
            self.cursor.execute("""
                SELECT * FROM requests
                ORDER BY created_at DESC
                LIMIT %s
            """, (limit,))

        return self.cursor.fetchall()
```

---

## 2.5 Фоновые задачи с Celery

### Настройка Celery:

```python
# celery_app.py

from celery import Celery
import redis

# Celery конфигурация
celery_app = Celery(
    'ml_backend',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)
```

### Создание фоновых задач:

```python
# tasks.py

from celery_app import celery_app
from services.llm_service import LLMService
import time

@celery_app.task(name='tasks.train_model')
def train_model(dataset_path, model_config):
    """Долгая задача обучения модели"""
    # Это может занять часы

    # Симуляция обучения
    for epoch in range(model_config['epochs']):
        time.sleep(10)  # Симуляция эпохи

        # Обновление прогресса
        train_model.update_state(
            state='PROGRESS',
            meta={'current': epoch, 'total': model_config['epochs']}
        )

    return {'status': 'completed', 'model_path': '/models/trained_model.pt'}

@celery_app.task(name='tasks.process_large_dataset')
def process_large_dataset(file_path):
    """Обработка большого датасета"""
    import pandas as pd

    # Загрузка данных
    df = pd.read_csv(file_path)

    # Обработка
    result = df.groupby('category').agg({
        'value': ['sum', 'mean', 'count']
    })

    return result.to_dict()
```

### Использование в API:

```python
# app.py

from tasks import train_model, process_large_dataset

@app.route('/api/train', methods=['POST'])
def start_training():
    """Запуск обучения модели в фоне"""
    data = request.get_json()

    # Запуск фоновой задачи
    task = train_model.delay(
        dataset_path=data['dataset'],
        model_config=data['config']
    )

    return jsonify({
        'success': True,
        'task_id': task.id,
        'status_url': f'/api/task/{task.id}/status'
    })

@app.route('/api/task/<task_id>/status', methods=['GET'])
def task_status(task_id):
    """Проверка статуса задачи"""
    task = celery_app.AsyncResult(task_id)

    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'status': 'Задача в очереди...'
        }
    elif task.state == 'PROGRESS':
        response = {
            'state': task.state,
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 1),
            'status': f"Обработка {task.info.get('current', 0)}/{task.info.get('total', 1)}"
        }
    elif task.state == 'SUCCESS':
        response = {
            'state': task.state,
            'result': task.result,
            'status': 'Завершено!'
        }
    else:
        response = {
            'state': task.state,
            'status': str(task.info)
        }

    return jsonify(response)
```

---

## 2.6 Мониторинг и логирование

### Prometheus метрики:

```python
# metrics.py

from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time

# Метрики
request_count = Counter(
    'ml_backend_requests_total',
    'Total number of requests',
    ['service', 'status']
)

request_duration = Histogram(
    'ml_backend_request_duration_seconds',
    'Request duration in seconds',
    ['service']
)

# Middleware для метрик
@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    request_duration.labels(
        service=request.endpoint
    ).observe(time.time() - request.start_time)

    request_count.labels(
        service=request.endpoint,
        status=response.status_code
    ).inc()

    return response

# Endpoint для метрик
@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}
```

---

# ИНТЕГРАЦИЯ С FLUTTER

## 3.1 Flutter клиент для Ollama

```dart
// lib/services/ollama_service.dart

import 'package:dio/dio.dart';

class OllamaService {
  final Dio _dio;
  final String baseUrl;

  OllamaService({
    this.baseUrl = 'http://localhost:11434',
  }) : _dio = Dio(BaseOptions(baseUrl: baseUrl));

  /// Генерация текста
  Future<String> generate({
    required String model,
    required String prompt,
    bool stream = false,
  }) async {
    try {
      final response = await _dio.post(
        '/api/generate',
        data: {
          'model': model,
          'prompt': prompt,
          'stream': stream,
        },
      );

      return response.data['response'];
    } catch (e) {
      throw Exception('Ошибка генерации: $e');
    }
  }

  /// Чат с контекстом
  Future<String> chat({
    required String model,
    required List<Map<String, String>> messages,
  }) async {
    try {
      final response = await _dio.post(
        '/api/chat',
        data: {
          'model': model,
          'messages': messages,
        },
      );

      return response.data['message']['content'];
    } catch (e) {
      throw Exception('Ошибка чата: $e');
    }
  }

  /// Streaming генерация
  Stream<String> generateStream({
    required String model,
    required String prompt,
  }) async* {
    try {
      final response = await _dio.post(
        '/api/generate',
        data: {
          'model': model,
          'prompt': prompt,
          'stream': true,
        },
        options: Options(responseType: ResponseType.stream),
      );

      await for (var chunk in response.data.stream) {
        final text = String.fromCharCodes(chunk);
        final lines = text.split('\n');

        for (var line in lines) {
          if (line.trim().isEmpty) continue;

          try {
            final json = jsonDecode(line);
            if (json['response'] != null) {
              yield json['response'];
            }
          } catch (_) {}
        }
      }
    } catch (e) {
      throw Exception('Ошибка streaming: $e');
    }
  }

  /// Проверка доступности
  Future<bool> isAvailable() async {
    try {
      await _dio.get('/api/tags');
      return true;
    } catch (e) {
      return false;
    }
  }

  /// Список моделей
  Future<List<String>> listModels() async {
    try {
      final response = await _dio.get('/api/tags');
      final models = response.data['models'] as List;
      return models.map((m) => m['name'] as String).toList();
    } catch (e) {
      throw Exception('Ошибка получения списка моделей: $e');
    }
  }
}
```

### Пример использования в Flutter:

```dart
// lib/screens/chat_screen.dart

import 'package:flutter/material.dart';
import '../services/ollama_service.dart';

class ChatScreen extends StatefulWidget {
  @override
  _ChatScreenState createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final OllamaService _ollama = OllamaService();
  final TextEditingController _controller = TextEditingController();
  final List<Map<String, String>> _messages = [];
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _checkAvailability();
  }

  Future<void> _checkAvailability() async {
    final available = await _ollama.isAvailable();
    if (!available) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Ollama недоступен. Запустите сервер.')),
      );
    }
  }

  Future<void> _sendMessage() async {
    if (_controller.text.trim().isEmpty) return;

    final userMessage = _controller.text;
    _controller.clear();

    setState(() {
      _messages.add({'role': 'user', 'content': userMessage});
      _isLoading = true;
    });

    try {
      // Вариант 1: Обычный запрос
      final response = await _ollama.chat(
        model: 'llama2',
        messages: _messages,
      );

      setState(() {
        _messages.add({'role': 'assistant', 'content': response});
        _isLoading = false;
      });

      // Вариант 2: Streaming (более интерактивно)
      // String assistantMessage = '';
      // setState(() {
      //   _messages.add({'role': 'assistant', 'content': ''});
      // });
      //
      // await for (var chunk in _ollama.generateStream(
      //   model: 'llama2',
      //   prompt: userMessage,
      // )) {
      //   assistantMessage += chunk;
      //   setState(() {
      //     _messages.last['content'] = assistantMessage;
      //   });
      // }
      //
      // setState(() {
      //   _isLoading = false;
      // });

    } catch (e) {
      setState(() {
        _isLoading = false;
      });

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Ошибка: $e')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Ollama Chat'),
      ),
      body: Column(
        children: [
          // Список сообщений
          Expanded(
            child: ListView.builder(
              padding: EdgeInsets.all(16),
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final message = _messages[index];
                final isUser = message['role'] == 'user';

                return Align(
                  alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
                  child: Container(
                    margin: EdgeInsets.only(bottom: 8),
                    padding: EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: isUser ? Colors.blue : Colors.grey[300],
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      message['content']!,
                      style: TextStyle(
                        color: isUser ? Colors.white : Colors.black,
                      ),
                    ),
                  ),
                );
              },
            ),
          ),

          // Индикатор загрузки
          if (_isLoading)
            Padding(
              padding: EdgeInsets.all(8),
              child: CircularProgressIndicator(),
            ),

          // Поле ввода
          Padding(
            padding: EdgeInsets.all(16),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _controller,
                    decoration: InputDecoration(
                      hintText: 'Введите сообщение...',
                      border: OutlineInputBorder(),
                    ),
                    onSubmitted: (_) => _sendMessage(),
                  ),
                ),
                SizedBox(width: 8),
                IconButton(
                  icon: Icon(Icons.send),
                  onPressed: _sendMessage,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
```

---

## 3.2 Flutter клиент для Desktop Server

```dart
// lib/services/ml_backend_service.dart

import 'package:dio/dio.dart';
import 'dart:io';

class MLBackendService {
  final Dio _dio;
  final String baseUrl;

  MLBackendService({
    this.baseUrl = 'http://localhost:5000',
  }) : _dio = Dio(BaseOptions(baseUrl: baseUrl));

  /// Проверка здоровья сервера
  Future<Map<String, dynamic>> healthCheck() async {
    final response = await _dio.get('/health');
    return response.data;
  }

  /// Генерация текста через LLM
  Future<String> generateText({
    required String prompt,
    int maxLength = 200,
  }) async {
    try {
      final response = await _dio.post(
        '/api/llm/generate',
        data: {
          'prompt': prompt,
          'max_length': maxLength,
        },
      );

      if (response.data['success']) {
        return response.data['text'];
      } else {
        throw Exception(response.data['error']);
      }
    } catch (e) {
      throw Exception('Ошибка генерации текста: $e');
    }
  }

  /// Классификация изображения
  Future<List<Map<String, dynamic>>> classifyImage(File imageFile) async {
    try {
      // Создание FormData для загрузки файла
      final formData = FormData.fromMap({
        'image': await MultipartFile.fromFile(
          imageFile.path,
          filename: imageFile.path.split('/').last,
        ),
      });

      final response = await _dio.post(
        '/api/vision/classify',
        data: formData,
      );

      if (response.data['success']) {
        return List<Map<String, dynamic>>.from(response.data['predictions']);
      } else {
        throw Exception(response.data['error']);
      }
    } catch (e) {
      throw Exception('Ошибка классификации изображения: $e');
    }
  }

  /// Запуск долгой задачи
  Future<String> startTraining({
    required String datasetPath,
    required Map<String, dynamic> config,
  }) async {
    try {
      final response = await _dio.post(
        '/api/train',
        data: {
          'dataset': datasetPath,
          'config': config,
        },
      );

      return response.data['task_id'];
    } catch (e) {
      throw Exception('Ошибка запуска обучения: $e');
    }
  }

  /// Проверка статуса задачи
  Future<Map<String, dynamic>> checkTaskStatus(String taskId) async {
    try {
      final response = await _dio.get('/api/task/$taskId/status');
      return response.data;
    } catch (e) {
      throw Exception('Ошибка проверки статуса: $e');
    }
  }

  /// Polling задачи до завершения
  Stream<Map<String, dynamic>> pollTask(String taskId) async* {
    while (true) {
      await Future.delayed(Duration(seconds: 2));

      final status = await checkTaskStatus(taskId);
      yield status;

      if (status['state'] == 'SUCCESS' || status['state'] == 'FAILURE') {
        break;
      }
    }
  }
}
```

### Пример использования - Классификация изображений:

```dart
// lib/screens/image_classifier_screen.dart

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'dart:io';
import '../services/ml_backend_service.dart';

class ImageClassifierScreen extends StatefulWidget {
  @override
  _ImageClassifierScreenState createState() => _ImageClassifierScreenState();
}

class _ImageClassifierScreenState extends State<ImageClassifierScreen> {
  final MLBackendService _mlService = MLBackendService();
  final ImagePicker _picker = ImagePicker();

  File? _image;
  List<Map<String, dynamic>>? _predictions;
  bool _isLoading = false;

  Future<void> _pickImage() async {
    final XFile? pickedFile = await _picker.pickImage(
      source: ImageSource.gallery,
    );

    if (pickedFile != null) {
      setState(() {
        _image = File(pickedFile.path);
        _predictions = null;
      });

      await _classifyImage();
    }
  }

  Future<void> _classifyImage() async {
    if (_image == null) return;

    setState(() {
      _isLoading = true;
    });

    try {
      final predictions = await _mlService.classifyImage(_image!);

      setState(() {
        _predictions = predictions;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
      });

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Ошибка: $e')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Image Classifier'),
      ),
      body: SingleChildScrollView(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Кнопка выбора изображения
            ElevatedButton.icon(
              icon: Icon(Icons.image),
              label: Text('Выбрать изображение'),
              onPressed: _pickImage,
            ),

            SizedBox(height: 16),

            // Отображение изображения
            if (_image != null)
              Container(
                height: 300,
                decoration: BoxDecoration(
                  border: Border.all(color: Colors.grey),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(8),
                  child: Image.file(
                    _image!,
                    fit: BoxFit.contain,
                  ),
                ),
              ),

            SizedBox(height: 16),

            // Индикатор загрузки
            if (_isLoading)
              Center(child: CircularProgressIndicator()),

            // Результаты классификации
            if (_predictions != null && !_isLoading)
              Card(
                child: Padding(
                  padding: EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Результаты:',
                        style: Theme.of(context).textTheme.headline6,
                      ),
                      SizedBox(height: 8),
                      ..._predictions!.map((prediction) {
                        return ListTile(
                          title: Text(prediction['label']),
                          trailing: Text(
                            '${(prediction['score'] * 100).toStringAsFixed(1)}%',
                            style: TextStyle(fontWeight: FontWeight.bold),
                          ),
                          leading: CircularProgressIndicator(
                            value: prediction['score'],
                            backgroundColor: Colors.grey[300],
                          ),
                        );
                      }).toList(),
                    ],
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
```

---

## 3.3 Умный роутер для выбора backend

```dart
// lib/services/smart_backend_router.dart

import 'ollama_service.dart';
import 'ml_backend_service.dart';

enum BackendType {
  ollama,      // Для простых LLM задач
  mlBackend,   // Для сложных ML задач
}

class SmartBackendRouter {
  final OllamaService _ollama = OllamaService();
  final MLBackendService _mlBackend = MLBackendService();

  /// Автоматический выбор backend
  Future<BackendType> selectBackend({
    required String taskType,
    int? dataSize,
  }) async {
    // Проверяем доступность
    final ollamaAvailable = await _ollama.isAvailable();
    final mlBackendAvailable = await _checkMLBackend();

    // Логика выбора
    switch (taskType) {
      case 'text_generation':
      case 'chat':
        // Простая генерация текста - используем Ollama (быстрее)
        return ollamaAvailable ? BackendType.ollama : BackendType.mlBackend;

      case 'image_classification':
      case 'object_detection':
        // Computer Vision - только ML Backend
        return BackendType.mlBackend;

      case 'complex_nlp':
        // Сложный NLP - ML Backend (больше контроль)
        return BackendType.mlBackend;

      default:
        // По умолчанию Ollama
        return ollamaAvailable ? BackendType.ollama : BackendType.mlBackend;
    }
  }

  Future<bool> _checkMLBackend() async {
    try {
      await _mlBackend.healthCheck();
      return true;
    } catch (e) {
      return false;
    }
  }

  /// Универсальный метод генерации текста
  Future<String> generateText(String prompt) async {
    final backend = await selectBackend(taskType: 'text_generation');

    switch (backend) {
      case BackendType.ollama:
        return await _ollama.generate(
          model: 'llama2',
          prompt: prompt,
        );

      case BackendType.mlBackend:
        return await _mlBackend.generateText(prompt: prompt);
    }
  }
}
```

---

Это первая часть методологии. Продолжить со следующими разделами:
- Сравнение и выбор подхода
- Troubleshooting и FAQ
- Best practices
- Примеры реальных проектов?

---

# СРАВНЕНИЕ И ВЫБОР

## 4.1 Матрица принятия решений

### Используйте **OLLAMA** если:

| Критерий | Описание |
|----------|----------|
| **Опыт** | Нет опыта с Python/ML |
| **Задачи** | Только текстовые задачи (чат, генерация, суммаризация) |
| **Время** | Нужно запустить за 10 минут |
| **Модели** | Достаточно готовых моделей (Llama, Mistral, etc.) |
| **Кастомизация** | Не нужна глубокая кастомизация |
| **Обслуживание** | Минимальное (автообновления) |
| **GUI** | Нужен графический интерфейс |

**Примеры проектов:**
- Персональный AI ассистент
- Чат-бот для обучения
- Генератор контента
- Помощник по коду

---

### Используйте **DESKTOP SERVER** если:

| Критерий | Описание |
|----------|----------|
| **Опыт** | Знание Python, ML, API разработки |
| **Задачи** | Множество ML задач (LLM + CV + Audio + Custom) |
| **Время** | Можно потратить 1-2 дня на настройку |
| **Модели** | Нужны специфичные модели или fine-tuning |
| **Кастомизация** | Полный контроль над pipeline |
| **Обслуживание** | Готовы настраивать и поддерживать |
| **Интеграция** | Сложная интеграция с другими системами |

**Примеры проектов:**
- Мультимодальное приложение (текст + изображения + аудио)
- Система с fine-tuned моделями
- Приложение для data science
- Кастомные ML pipeline

---

## 4.2 Таблица сравнения возможностей

| Функция | Ollama | Desktop Server |
|---------|--------|---------------|
| **Текстовая генерация** | ✅ Отлично | ✅ Отлично |
| **Чат с контекстом** | ✅ Да | ✅ Да |
| **Классификация изображений** | ❌ Нет | ✅ Да |
| **Генерация изображений** | ❌ Нет | ✅ Да (Stable Diffusion) |
| **Распознавание речи** | ❌ Нет | ✅ Да (Whisper) |
| **Fine-tuning моделей** | ❌ Нет | ✅ Да |
| **Кастомные pipeline** | ❌ Ограничено | ✅ Полная свобода |
| **Фоновые задачи** | ❌ Нет | ✅ Да (Celery) |
| **База данных** | ❌ Нет | ✅ Да (MySQL/PostgreSQL) |
| **Метрики и мониторинг** | ⚠️ Базовый | ✅ Полный (Prometheus) |
| **API совместимость** | ✅ OpenAI-like | ✅ Кастомный |
| **Установка** | ⚡ 5 минут | 🐌 1-2 часа |
| **Обслуживание** | 🟢 Простое | 🔴 Сложное |

---

## 4.3 Сценарии использования

### Сценарий 1: Простой чат-бот

```
Требования:
- Локальный ChatGPT
- Чат с историей
- Простая установка

РЕШЕНИЕ: OLLAMA ✅
Время: 10 минут
Сложность: 🟢 Легко
```

### Сценарий 2: Классификатор изображений + чат

```
Требования:
- Распознавание объектов на фото
- Генерация описания изображения
- Чат о содержимом

РЕШЕНИЕ: DESKTOP SERVER ✅
Время: 2 дня
Сложность: 🔴 Сложно
Причина: Нужен CV + LLM
```

### Сценарий 3: Персональный ассистент

```
Требования:
- Ответы на вопросы
- Генерация текста
- Работа офлайн

РЕШЕНИЕ: OLLAMA ✅
Время: 15 минут
Сложность: 🟢 Легко
```

### Сценарий 4: Data Science платформа

```
Требования:
- Обработка CSV/Excel
- Визуализация данных
- ML анализ
- Fine-tuned модели для специфичного домена

РЕШЕНИЕ: DESKTOP SERVER ✅
Время: 1 неделя
Сложность: 🔴 Очень сложно
Причина: Нужен полный ML стек
```

---

# TROUBLESHOOTING

## 5.1 Проблемы с Ollama

### Проблема: Ollama не запускается

```bash
# Проверка статуса сервиса
systemctl status ollama  # Linux
ps aux | grep ollama     # Проверка процесса

# Решение 1: Перезапуск
systemctl restart ollama  # Linux
# Windows: перезапустить через Task Manager

# Решение 2: Проверка портов
netstat -an | grep 11434
# Если порт занят - изменить OLLAMA_HOST

# Решение 3: Логи
journalctl -u ollama -f  # Linux
# Windows: C:\Users\<user>\.ollama\logs\
```

### Проблема: Модель не загружается

```bash
# Ошибка: "model not found"
# Решение: Загрузить модель
ollama pull llama2

# Ошибка: "insufficient memory"
# Решение: Использовать меньшую модель
ollama pull phi-2  # Только 2.7B параметров

# Проверка доступного места
df -h ~/.ollama/models  # Linux
dir %USERPROFILE%\.ollama\models  # Windows
```

### Проблема: Медленная генерация

```bash
# Проблема: Нет GPU ускорения
# Проверка GPU
nvidia-smi  # NVIDIA GPU
rocm-smi    # AMD GPU

# Решение: Установка драйверов
# NVIDIA CUDA: https://developer.nvidia.com/cuda-downloads
# AMD ROCm: https://rocm.docs.amd.com/

# Проблема: Слишком большая модель
# Решение: Уменьшить размер модели
ollama run llama2  # 7B - быстрее
# вместо
ollama run llama2:70b  # 70B - медленно
```

### Проблема: Flutter не может подключиться

```dart
// Ошибка: Connection refused
// Решение 1: Проверить доступность
curl http://localhost:11434/api/tags

// Решение 2: Изменить URL
// Если на другом компьютере в сети:
OllamaService(baseUrl: 'http://192.168.1.100:11434')

// Решение 3: Настроить CORS (если нужно)
// Ollama по умолчанию разрешает CORS
```

---

## 5.2 Проблемы с Desktop Server

### Проблема: XAMPP не запускается

```
Ошибка: "Port 80 already in use"

Решение 1: Изменить порт Apache
1. Открыть XAMPP Control Panel
2. Config -> Apache (httpd.conf)
3. Найти: Listen 80
4. Изменить: Listen 8080
5. Перезапустить Apache

Решение 2: Остановить конфликтующий процесс
Windows:
  netstat -ano | findstr :80
  taskkill /PID <PID> /F

Linux:
  sudo lsof -i :80
  sudo kill <PID>
```

### Проблема: Python зависимости не устанавливаются

```bash
# Ошибка: "No module named 'torch'"
# Решение: Установить в правильное окружение

# 1. Активировать venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate      # Windows

# 2. Проверить активацию
which python  # Должно показать venv/bin/python

# 3. Установить зависимости
pip install -r requirements.txt

# Ошибка: "Could not find a version that satisfies torch"
# Решение: Установить через официальный URL
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

### Проблема: Модель не загружается

```python
# Ошибка: "OutOfMemoryError"
# Решение: Использовать меньшую модель или CPU

from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

# Вместо большой модели:
# model_name = "EleutherAI/gpt-neo-2.7B"

# Использовать маленькую:
model_name = "distilgpt2"

# Или загрузить на CPU:
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float32,  # Вместо float16
    device_map="cpu"  # Принудительно CPU
)

# Ошибка: "Connection timeout"
# Решение: Использовать локальный кэш
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    cache_dir="./models",  # Локальная папка
    local_files_only=True   # Не скачивать заново
)
```

### Проблема: Flask сервер падает

```bash
# Ошибка: "Address already in use"
# Решение: Изменить порт

# В app.py:
app.run(port=5001)  # Вместо 5000

# Или убить процесс на порту 5000:
# Linux/Mac:
lsof -ti:5000 | xargs kill -9

# Windows:
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Ошибка: "Werkzeug crashed"
# Решение: Использовать production сервер
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Проблема: Flutter не видит API

```dart
// Ошибка: "Connection refused"
// Отладка:

// 1. Проверить доступность API
curl http://localhost:5000/health

// 2. Проверить CORS
// В app.py добавить:
from flask_cors import CORS
CORS(app, origins=['*'])  # Для разработки

// 3. Проверить firewall
// Windows: Settings -> Firewall -> Allow app
// Linux: sudo ufw allow 5000

// 4. Если Flutter на телефоне, использовать IP:
MLBackendService(baseUrl: 'http://192.168.1.100:5000')
```

---

## 5.3 Проблемы производительности

### Медленная генерация текста

```python
# Проблема: Генерация 30+ секунд
# Решение: Оптимизация параметров

# ❌ Медленно
result = pipeline(
    prompt,
    max_length=2048,  # Слишком много
    num_beams=5,      # Beam search медленный
)

# ✅ Быстро
result = pipeline(
    prompt,
    max_length=200,    # Меньше токенов
    do_sample=True,    # Sampling быстрее beam search
    top_k=50,
    top_p=0.95,
    num_return_sequences=1
)
```

### Высокое использование RAM

```python
# Проблема: Модель использует 16+ ГБ RAM
# Решение: Квантизация модели

from transformers import AutoModelForCausalLM, BitsAndBytesConfig

# 8-bit квантизация (уменьшает размер в 2 раза)
quantization_config = BitsAndBytesConfig(
    load_in_8bit=True,
    llm_int8_threshold=6.0
)

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    quantization_config=quantization_config,
    device_map="auto"
)

# Или 4-bit квантизация (уменьшает в 4 раза!)
quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16
)
```

---

# BEST PRACTICES

## 6.1 Безопасность

### Ollama:

```bash
# 1. Не открывать наружу без аутентификации
# По умолчанию: localhost only ✅

# 2. Если нужен доступ из сети - использовать nginx proxy
server {
    listen 80;
    server_name ollama.local;

    location / {
        proxy_pass http://localhost:11434;
        
        # Basic auth
        auth_basic "Restricted";
        auth_basic_user_file /etc/nginx/.htpasswd;
    }
}

# 3. Ограничение доступа по IP
# В nginx:
allow 192.168.1.0/24;
deny all;
```

### Desktop Server:

```python
# 1. Использовать API ключи
from flask import request, abort

API_KEYS = {
    "flutter-app-key-123": "mobile_app",
    "web-app-key-456": "web_client"
}

@app.before_request
def check_api_key():
    api_key = request.headers.get('X-API-Key')
    if api_key not in API_KEYS:
        abort(401, "Invalid API key")

# 2. Валидация входных данных
from pydantic import BaseModel, validator

class GenerateRequest(BaseModel):
    prompt: str
    max_length: int = 200
    
    @validator('prompt')
    def prompt_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Prompt cannot be empty')
        return v
    
    @validator('max_length')
    def max_length_limit(cls, v):
        if v > 2048:
            raise ValueError('Max length cannot exceed 2048')
        return v

# 3. Rate limiting
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["100 per hour"]
)

@app.route('/api/llm/generate')
@limiter.limit("10 per minute")
def generate_text():
    # ...
    pass
```

---

## 6.2 Оптимизация

### Кэширование результатов:

```python
# Использование Redis для кэша
import redis
import json
import hashlib

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def generate_with_cache(prompt, max_length):
    # Создаем ключ из параметров
    cache_key = hashlib.md5(
        f"{prompt}:{max_length}".encode()
    ).hexdigest()
    
    # Проверяем кэш
    cached = redis_client.get(cache_key)
    if cached:
        print("✅ Cache hit!")
        return json.loads(cached)
    
    # Генерация если нет в кэше
    result = llm_service.generate(prompt, max_length)
    
    # Сохранение в кэш (TTL 1 час)
    redis_client.setex(
        cache_key,
        3600,  # 1 час
        json.dumps(result)
    )
    
    return result
```

### Предзагрузка моделей:

```python
# app.py

# ❌ Плохо: загрузка при каждом запросе
@app.route('/api/generate')
def generate():
    model = load_model()  # Медленно!
    result = model.generate(...)
    return result

# ✅ Хорошо: загрузка при старте
# Глобальные переменные
llm_service = None
vision_service = None

@app.before_first_request
def init_models():
    global llm_service, vision_service
    
    print("Loading models...")
    llm_service = LLMService()
    llm_service.load_model()
    
    vision_service = VisionService()
    vision_service.load_model()
    print("✅ Models loaded!")

@app.route('/api/generate')
def generate():
    # Модель уже загружена
    result = llm_service.generate(...)
    return result
```

### Batch processing:

```python
# Обработка нескольких запросов одновременно
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=4)

@app.route('/api/batch-generate', methods=['POST'])
def batch_generate():
    prompts = request.json['prompts']  # Список промптов
    
    # Параллельная обработка
    futures = [
        executor.submit(llm_service.generate, prompt)
        for prompt in prompts
    ]
    
    results = [future.result() for future in futures]
    
    return jsonify({'results': results})
```

---

## 6.3 Мониторинг

### Логирование запросов:

```python
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ml_backend.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

@app.route('/api/llm/generate')
def generate_text():
    start_time = datetime.now()
    
    try:
        prompt = request.json['prompt']
        
        logger.info(f"Generate request: {prompt[:50]}...")
        
        result = llm_service.generate(prompt)
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"Generation completed in {elapsed:.2f}s")
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Generation failed: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500
```

### Метрики производительности:

```python
from prometheus_client import Counter, Histogram, Gauge

# Определение метрик
requests_total = Counter(
    'ml_requests_total',
    'Total requests',
    ['endpoint', 'status']
)

request_duration = Histogram(
    'ml_request_duration_seconds',
    'Request duration',
    ['endpoint']
)

models_loaded = Gauge(
    'ml_models_loaded',
    'Number of loaded models'
)

@app.before_request
def start_timer():
    request.start_time = time.time()

@app.after_request
def record_metrics(response):
    duration = time.time() - request.start_time
    
    request_duration.labels(
        endpoint=request.endpoint
    ).observe(duration)
    
    requests_total.labels(
        endpoint=request.endpoint,
        status=response.status_code
    ).inc()
    
    return response
```

---

# ПРИМЕРЫ РЕАЛЬНЫХ ПРОЕКТОВ

## 7.1 Проект: Локальный AI Ассистент (Ollama)

### Описание:
Персональный ассистент для работы с документами, кодом и общения.

### Стек:
- Frontend: Flutter (Mobile + Desktop)
- Backend: Ollama (llama2)
- Хранилище: SharedPreferences

### Архитектура:

```
Flutter App
├── Chat Screen
│   └── Ollama API (localhost:11434)
├── Document Analyzer
│   └── Загрузка PDF/TXT → Ollama Summary
└── Code Helper
    └── Генерация/объяснение кода
```

### Особенности:
- ✅ Полностью офлайн
- ✅ Работает на любом компьютере
- ✅ Простая установка (10 минут)
- ❌ Только текстовые задачи

---

## 7.2 Проект: Мультимодальная платформа (Desktop Server)

### Описание:
Платформа для обработки текста, изображений и аудио с единым API.

### Стек:
- Frontend: Flutter Web + Mobile
- Backend: Flask + Python ML Stack
- База данных: PostgreSQL
- Очереди: Celery + Redis
- Мониторинг: Prometheus + Grafana

### Архитектура:

```
Flutter Clients (Web + Mobile)
        ↓
    nginx (Load Balancer)
        ↓
   Flask API Servers (3 instances)
        ↓
    ┌───┴───┬────────┬─────────┐
    ↓       ↓        ↓         ↓
  LLM    Vision   Audio    Custom ML
  GPT-2   ViT    Whisper   Sklearn
    └───┬───┴────────┴─────────┘
        ↓
   PostgreSQL (история)
   Redis (кэш + очереди)
   
   Celery Workers (фоновые задачи)
```

### Сервисы:

**1. Text Service:**
- Генерация текста (GPT-2)
- Суммаризация (BART)
- Перевод (Helsinki-NLP)
- Sentiment Analysis

**2. Vision Service:**
- Классификация (ViT)
- Object Detection (YOLO)
- Face Recognition (FaceNet)
- Image Generation (Stable Diffusion)

**3. Audio Service:**
- Speech-to-Text (Whisper)
- Text-to-Speech (TTS)
- Audio Classification

**4. Custom ML Service:**
- Рекомендательная система
- Anomaly Detection
- Time Series Forecasting

### Особенности:
- ✅ Все типы ML задач
- ✅ Горизонтальное масштабирование
- ✅ Фоновые задачи
- ✅ Полный мониторинг
- ❌ Сложная настройка (1 неделя)

---

## 7.3 Проект: Edge AI для IoT (Hybrid)

### Описание:
Система для обработки данных с IoT устройств с использованием локального AI.

### Стек:
- Frontend: Flutter Mobile
- Local Backend: Ollama (быстрые задачи)
- Heavy Backend: Desktop Server (сложные задачи)
- Edge Devices: Raspberry Pi + TensorFlow Lite

### Архитектура:

```
IoT Sensors → Raspberry Pi (TFLite)
                ↓
         Edge Processing
                ↓
      ┌────────┴────────┐
      ↓                 ↓
  Ollama            Desktop Server
 (quick)              (heavy)
      └────────┬────────┘
               ↓
        Flutter Dashboard
```

### Workflow:

1. **Быстрые задачи** → Ollama
   - Классификация сенсорных данных
   - Простые алерты

2. **Сложные задачи** → Desktop Server
   - Анализ паттернов
   - Предсказание аномалий
   - Обучение моделей

3. **Real-time** → Edge (TFLite)
   - Мгновенная реакция
   - Работа без сети

### Особенности:
- ✅ Гибридный подход
- ✅ Работает офлайн
- ✅ Real-time обработка
- ✅ Масштабируемость

---

## ЗАКЛЮЧЕНИЕ

### Рекомендации по выбору:

**Для обучения и экспериментов:**
→ Начните с **Ollama**
- Быстрый старт
- Много примеров
- Сообщество поддержки

**Для прототипов:**
→ **Ollama** для MVP
→ Переход на **Desktop Server** при росте

**Для production:**
→ **Desktop Server** + облако
- Локально: быстрые задачи
- Облако: тяжелые вычисления

**Для enterprise:**
→ Полный **Desktop Server** стек
- Собственная инфраструктура
- Полный контроль
- Масштабирование

---

## Дополнительные ресурсы:

### Документация:
- Ollama: https://ollama.ai/docs
- Transformers: https://huggingface.co/docs/transformers
- Flask: https://flask.palletsprojects.com/
- Flutter HTTP: https://pub.dev/packages/http

### Сообщества:
- Ollama Discord: https://discord.gg/ollama
- Hugging Face Forum: https://discuss.huggingface.co/
- r/LocalLLaMA: https://reddit.com/r/LocalLLaMA

### Модели:
- Ollama Library: https://ollama.ai/library
- Hugging Face Hub: https://huggingface.co/models
- Model Zoo: https://modelzoo.co/

---

**Автор методологии:** AI/ML Integration Team  
**Версия:** 1.0  
**Дата:** 2026-01-08  
**Лицензия:** Open Source (MIT)
