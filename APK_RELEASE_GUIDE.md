# 📱 Справочник: Релиз Android APK - Быстрые ссылки

## 🎯 Вопрос: Как опубликовать Android APK?

### Ответ: У вас есть 3 варианта

```
┌─────────────────────────────────────────────────────────────┐
│                   ВАРИАНТЫ ПУБЛИКАЦИИ                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1️⃣  GitHub Releases         ⏱️  30 мин    💰 Бесплатно     │
│     └─ Прямое распространение APK                            │
│                                                               │
│  2️⃣  Google Play Store       ⏱️  3-5 дней  💰 $25           │
│     └─ Официальный магазин Android                           │
│                                                               │
│  3️⃣  GitHub Actions (авто)   ⏱️  Настройка  💰 Бесплатно    │
│     └─ Автоматическая сборка при release                     │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 📖 Документация по категориям

### 🎯 Главный документ (НАЧАТЬ ЗДЕСЬ!)

| Документ | Описание | Аудитория |
|----------|----------|-----------|
| **[HOW_TO_RELEASE_APK.md](HOW_TO_RELEASE_APK.md)** | 🌟 **ОСНОВНОЕ РУКОВОДСТВО** - Все способы публикации APK с пошаговыми инструкциями | Все |

### 👤 Для пользователей (Установка готового APK)

| Документ | Описание |
|----------|----------|
| **[DOWNLOAD_APK.md](DOWNLOAD_APK.md)** | Как скачать и установить APK на Android устройство |
| **[RELEASE_NOTES.md](RELEASE_NOTES.md)** | Что включено в релиз, требования, FAQ |

### 👨‍💻 Для разработчиков (Создание APK)

| Документ | Описание | Когда использовать |
|----------|----------|-------------------|
| **[mobile-app/PUBLISH_APK.md](mobile-app/PUBLISH_APK.md)** | 📚 Полное руководство по публикации | Основная инструкция для разработчиков |
| **[mobile-app/KEYSTORE_SETUP.md](mobile-app/KEYSTORE_SETUP.md)** | 🔑 Создание keystore и настройка подписи | Перед первым релизом |
| **[mobile-app/BUILD_MOBILE_EMBEDDED.md](mobile-app/BUILD_MOBILE_EMBEDDED.md)** | 🏗️ Техническая документация сборки | Для понимания архитектуры |
| **[CREATE_RELEASE_INSTRUCTIONS.md](CREATE_RELEASE_INSTRUCTIONS.md)** | 📋 GitHub Release пошагово | Для публикации на GitHub |
| **[QUICK_START_GITHUB_RELEASE.md](QUICK_START_GITHUB_RELEASE.md)** | ⚡ Быстрый старт | Для опытных разработчиков |

---

## ⚡ Быстрые команды

### Сборка APK

```bash
# Неподписанный APK (для тестирования)
cd mobile-app
./build-android-embedded.sh release

# Подписанный APK (для публикации)
# 1. Настройте keystore (см. KEYSTORE_SETUP.md)
# 2. Соберите
cd mobile-app
./build-android-embedded.sh release
```

### Проверка APK

```bash
# Проверить подпись
jarsigner -verify -verbose -certs build/app/outputs/flutter-apk/app-release.apk

# Проверить размер
ls -lh build/app/outputs/flutter-apk/app-release.apk

# Установить на устройство
adb install build/app/outputs/flutter-apk/app-release.apk
```

### GitHub Release

```bash
# Через GitHub CLI
gh release create v1.0.0 \
  build/app/outputs/flutter-apk/app-release.apk#data20-mobile-v1.0.0.apk \
  --title "📱 Data20 Mobile v1.0.0" \
  --notes-file RELEASE_NOTES.md
```

---

## 🔄 Workflow: Первый релиз

```
┌──────────────────────────────────────────────────────────────┐
│                    ПРОЦЕСС РЕЛИЗА                             │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│  ⓵ Создать keystore           → KEYSTORE_SETUP.md             │
│     └─ keytool -genkey ...    ⏱️ 10 минут                     │
│                                                                │
│  ⓶ Настроить key.properties   → KEYSTORE_SETUP.md             │
│     └─ storePassword=...      ⏱️ 2 минуты                     │
│                                                                │
│  ⓷ Собрать APK                → PUBLISH_APK.md                │
│     └─ ./build-android-...    ⏱️ 10-20 минут                  │
│                                                                │
│  ⓸ Опубликовать               → HOW_TO_RELEASE_APK.md         │
│     ├─ GitHub Releases        ⏱️ 5 минут                      │
│     └─ или Play Store         ⏱️ 1-3 дня проверки            │
│                                                                │
└──────────────────────────────────────────────────────────────┘

ОБЩЕЕ ВРЕМЯ (GitHub): ~30 минут
ОБЩЕЕ ВРЕМЯ (Play Store): ~30 мин + 1-3 дня проверки
```

---

## 🎯 Навигация по задачам

### Я хочу... → Куда идти?

| Задача | Документ |
|--------|----------|
| **Установить готовый APK** | [DOWNLOAD_APK.md](DOWNLOAD_APK.md) |
| **Собрать APK первый раз** | [HOW_TO_RELEASE_APK.md](HOW_TO_RELEASE_APK.md) → Вариант 1 |
| **Опубликовать в Play Store** | [HOW_TO_RELEASE_APK.md](HOW_TO_RELEASE_APK.md) → Вариант 2 |
| **Настроить автосборку** | [HOW_TO_RELEASE_APK.md](HOW_TO_RELEASE_APK.md) → Вариант 3 |
| **Создать keystore** | [mobile-app/KEYSTORE_SETUP.md](mobile-app/KEYSTORE_SETUP.md) |
| **Понять как подписать APK** | [mobile-app/KEYSTORE_SETUP.md](mobile-app/KEYSTORE_SETUP.md) |
| **Полная инструкция публикации** | [mobile-app/PUBLISH_APK.md](mobile-app/PUBLISH_APK.md) |
| **Создать GitHub Release** | [CREATE_RELEASE_INSTRUCTIONS.md](CREATE_RELEASE_INSTRUCTIONS.md) |
| **Понять архитектуру** | [mobile-app/BUILD_MOBILE_EMBEDDED.md](mobile-app/BUILD_MOBILE_EMBEDDED.md) |
| **Узнать что в релизе** | [RELEASE_NOTES.md](RELEASE_NOTES.md) |

---

## 📋 Checklist: Что мне нужно?

### Для сборки неподписанного APK (тестирование)

- [ ] Java JDK 17+
- [ ] Android SDK
- [ ] Flutter SDK
- [ ] Python 3.9+
- [ ] 15GB свободного места

**Команда**: `./build-android-embedded.sh release`

### Для сборки подписанного APK (публикация)

Всё из списка выше, плюс:

- [ ] Keystore файл создан
- [ ] key.properties настроен
- [ ] Пароли сохранены в надежном месте

**Документация**: [mobile-app/KEYSTORE_SETUP.md](mobile-app/KEYSTORE_SETUP.md)

### Для публикации в Play Store

Всё из списка выше, плюс:

- [ ] Google Play Developer аккаунт ($25)
- [ ] Иконка 512x512
- [ ] Скриншоты (минимум 2)
- [ ] Описание приложения
- [ ] Политика конфиденциальности (URL)

**Документация**: [mobile-app/PUBLISH_APK.md](mobile-app/PUBLISH_APK.md)

### Для автоматизации через GitHub Actions

Всё для подписанного APK, плюс:

- [ ] Keystore закодирован в base64
- [ ] GitHub Secrets настроены
- [ ] Workflow файл проверен

**Документация**: [HOW_TO_RELEASE_APK.md](HOW_TO_RELEASE_APK.md) → Автоматизация

---

## 🆘 Частые вопросы

### Где скачать готовый APK?

→ [GitHub Releases](https://github.com/svend4/data20/releases/latest)

### Как установить APK?

→ [DOWNLOAD_APK.md](DOWNLOAD_APK.md)

### Как собрать APK самостоятельно?

→ [HOW_TO_RELEASE_APK.md](HOW_TO_RELEASE_APK.md) → Вариант 1

### Как опубликовать в Play Store?

→ [HOW_TO_RELEASE_APK.md](HOW_TO_RELEASE_APK.md) → Вариант 2

### Что такое keystore и зачем он нужен?

→ [mobile-app/KEYSTORE_SETUP.md](mobile-app/KEYSTORE_SETUP.md)

### Как настроить автоматическую сборку?

→ [HOW_TO_RELEASE_APK.md](HOW_TO_RELEASE_APK.md) → Автоматизация

### APK не подписывается, что делать?

→ [mobile-app/KEYSTORE_SETUP.md](mobile-app/KEYSTORE_SETUP.md) → Troubleshooting

### APK слишком большой (100MB), это нормально?

→ Да! Включает embedded Python runtime. См. [RELEASE_NOTES.md](RELEASE_NOTES.md)

---

## 🎓 Рекомендуемый путь обучения

### Новичок в Android разработке?

1. Начните с → **[HOW_TO_RELEASE_APK.md](HOW_TO_RELEASE_APK.md)**
2. Затем изучите → **[mobile-app/KEYSTORE_SETUP.md](mobile-app/KEYSTORE_SETUP.md)**
3. Соберите APK локально
4. Опубликуйте на GitHub Releases
5. Позже переходите в Play Store

### Опытный разработчик?

1. Прочитайте → **[mobile-app/PUBLISH_APK.md](mobile-app/PUBLISH_APK.md)**
2. Настройте keystore → **[mobile-app/KEYSTORE_SETUP.md](mobile-app/KEYSTORE_SETUP.md)**
3. Настройте GitHub Actions для автосборки
4. Опубликуйте в Play Store

---

## 📞 Поддержка

### Нужна помощь?

- 🐛 **Баги**: [GitHub Issues](https://github.com/svend4/data20/issues)
- 💬 **Вопросы**: [GitHub Discussions](https://github.com/svend4/data20/discussions)
- 📖 **Документация**: См. таблицы выше

### Не нашли ответ?

1. Проверьте [mobile-app/PUBLISH_APK.md](mobile-app/PUBLISH_APK.md) → Troubleshooting
2. Откройте Issue с деталями проблемы
3. Сообщество поможет!

---

## 🎉 Итоговая структура документации

```
data20/
├── 📱 HOW_TO_RELEASE_APK.md        ← 🌟 НАЧАТЬ ЗДЕСЬ!
├── 📥 DOWNLOAD_APK.md              ← Для пользователей
├── 📝 RELEASE_NOTES.md             ← Что в релизе
├── 📋 CREATE_RELEASE_INSTRUCTIONS.md
├── ⚡ QUICK_START_GITHUB_RELEASE.md
│
└── mobile-app/
    ├── 📱 PUBLISH_APK.md           ← Полная инструкция
    ├── 🔑 KEYSTORE_SETUP.md        ← Настройка подписи
    ├── 🏗️ BUILD_MOBILE_EMBEDDED.md ← Техническая документация
    └── 📖 README.md                ← Документация разработчика
```

---

**Все готово для публикации APK!** 🚀

**Начните с**: [HOW_TO_RELEASE_APK.md](HOW_TO_RELEASE_APK.md)
