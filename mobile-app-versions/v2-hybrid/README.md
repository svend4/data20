# 📱 v2-hybrid - Flutter Frontend Development Version

**Назначение:** Версия для изолированной разработки и тестирования Flutter фронтенда

## 🎯 Специализация

Эта версия предназначена **исключительно для разработки Flutter UI**:
- ✅ Полный Flutter код (screens, widgets, services)
- ✅ Material Design 3 компоненты
- ✅ Роутинг (go_router)
- ✅ Состояние (Provider/Riverpod)
- ❌ Без Python бэкенда
- ❌ Без Chaquopy (работает с mock данными или внешним API)

## 📦 Структура

```
v2-hybrid/
├── lib/
│   ├── main.dart               # Точка входа
│   ├── models/                 # Модели данных
│   │   ├── user.dart
│   │   ├── tool.dart
│   │   └── job.dart
│   ├── screens/                # Экраны
│   │   ├── home_screen.dart
│   │   ├── login_screen.dart
│   │   ├── tools_screen.dart
│   │   └── settings_screen.dart
│   ├── services/               # Сервисы
│   │   ├── api_service.dart
│   │   ├── auth_service.dart
│   │   └── storage_service.dart
│   └── utils/                  # Утилиты
│       ├── constants.dart
│       └── theme.dart
└── pubspec.yaml
```

## 🚀 Быстрый старт

### Установка зависимостей:

```bash
cd mobile-app-versions/v2-hybrid
flutter pub get
```

### Запуск на эмуляторе:

```bash
# Android эмулятор
flutter run

# iOS симулятор
flutter run -d ios

# Web браузер (для быстрой разработки UI)
flutter run -d chrome
```

## 🔧 Конфигурация

### Подключение к внешнему API (v1-original):

Отредактируйте `lib/services/api_service.dart`:

```dart
class ApiService {
  final Dio _dio = Dio(
    BaseOptions(
      // Подключиться к v1-original бэкенду
      baseUrl: 'http://localhost:8001/api',
      // Или для Android эмулятора:
      // baseUrl: 'http://10.0.2.2:8001/api',
      
      connectTimeout: Duration(seconds: 5),
      receiveTimeout: Duration(seconds: 3),
    ),
  );
}
```

## 🔗 Интеграция с v1-original

Для полного стека используйте обе версии вместе:

```bash
# Терминал 1: Запустить v1-original бэкенд
cd mobile-app-versions/v1-original/android/app/src/main/python
python -c "from backend_main import *; setup_environment('/tmp/db', '/tmp/up', '/tmp/log'); run_server('0.0.0.0', 8001)"

# Терминал 2: Запустить v2-hybrid фронтенд
cd mobile-app-versions/v2-hybrid
flutter run
```

## 🔄 Синхронизация с другими версиями

После завершения разработки UI:

```bash
# Синхронизировать с v5-full (gold standard)
cd /home/user/data20
./sync-versions.sh flutter v2-hybrid --dry-run  # Предпросмотр
./sync-versions.sh flutter v2-hybrid --force     # Применить
```

## 📊 Flutter зависимости

| Пакет | Версия | Назначение |
|-------|--------|-----------|
| `flutter` | SDK | Framework |
| `go_router` | ^13.0.0 | Навигация |
| `provider` | ^6.1.1 | Управление состоянием |
| `dio` | ^5.4.0 | HTTP клиент |
| `shared_preferences` | ^2.2.2 | Локальное хранилище |

## 🔗 Связанные версии

- **v5-full** - Gold standard с полным функционалом
- **v1-original** - Python-only версия для разработки бэкенда
- **hybrid-best-of-both** - Песочница для экспериментов

---

**Статус:** ✅ Готово к разработке фронтенда
**Последнее обновление:** 2026-01-08
**Flutter SDK:** 3.19+
**Dart SDK:** 3.3+
