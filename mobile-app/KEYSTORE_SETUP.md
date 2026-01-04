# 🔑 Настройка Keystore для подписи Android APK

Для публикации Android приложения в Google Play Store или распространения подписанного APK необходимо создать и настроить keystore.

## ⚠️ Важно

- **Keystore файл НЕ должен попадать в Git!** (уже добавлен в .gitignore)
- **Сохраните keystore файл и пароли в безопасном месте!**
- **Потеря keystore означает невозможность обновления приложения!**

---

## 📝 Шаг 1: Генерация Keystore

### Способ 1: Использование keytool (входит в JDK)

```bash
# Перейти в директорию android
cd mobile-app/android

# Создать keystore
keytool -genkey -v -keystore data20-release-key.jks \
  -keyalg RSA -keysize 2048 -validity 10000 \
  -alias data20-release

# Вас попросят ввести:
# 1. Пароль для keystore (минимум 6 символов)
# 2. Подтверждение пароля
# 3. Имя и фамилию
# 4. Название организации
# 5. Город/регион
# 6. Штат/область
# 7. Код страны (RU для России)
# 8. Пароль для ключа (можно тот же что и для keystore)
```

**Пример ввода**:
```
Enter keystore password: MySecurePassword123
Re-enter new password: MySecurePassword123
What is your first and last name?
  [Unknown]:  Data20 Developer
What is the name of your organizational unit?
  [Unknown]:  Development
What is the name of your organization?
  [Unknown]:  Data20
What is the name of your City or Locality?
  [Unknown]:  Moscow
What is the name of your State or Province?
  [Unknown]:  Moscow
What is the two-letter country code for this unit?
  [Unknown]:  RU
Is CN=Data20 Developer, OU=Development, O=Data20, L=Moscow, ST=Moscow, C=RU correct?
  [no]:  yes

Enter key password for <data20-release>
        (RETURN if same as keystore password):
```

### Способ 2: Использование Android Studio

1. Открыть Android Studio
2. Build → Generate Signed Bundle/APK
3. Следовать мастеру создания keystore

---

## 📄 Шаг 2: Создание key.properties

Создайте файл `android/key.properties` со следующим содержимым:

```properties
storePassword=<ваш пароль keystore>
keyPassword=<ваш пароль ключа>
keyAlias=data20-release
storeFile=data20-release-key.jks
```

**Пример**:
```properties
storePassword=MySecurePassword123
keyPassword=MySecurePassword123
keyAlias=data20-release
storeFile=data20-release-key.jks
```

**⚠️ Этот файл НЕ должен попадать в Git!** (уже добавлен в .gitignore)

---

## 🔧 Шаг 3: Настройка build.gradle

Файл `android/app/build.gradle` уже настроен для использования keystore. Если нет, добавьте следующий код:

```gradle
def keystoreProperties = new Properties()
def keystorePropertiesFile = rootProject.file('key.properties')
if (keystorePropertiesFile.exists()) {
    keystoreProperties.load(new FileInputStream(keystorePropertiesFile))
}

android {
    // ... другие настройки

    signingConfigs {
        release {
            keyAlias keystoreProperties['keyAlias']
            keyPassword keystoreProperties['keyPassword']
            storeFile keystoreProperties['storeFile'] ? file(keystoreProperties['storeFile']) : null
            storePassword keystoreProperties['storePassword']
        }
    }

    buildTypes {
        release {
            signingConfig signingConfigs.release
            // ... другие настройки
        }
    }
}
```

---

## 🏗️ Шаг 4: Сборка подписанного APK

После настройки keystore можно собрать подписанный release APK:

```bash
cd mobile-app

# Автоматическая сборка с подписью
./build-android-embedded.sh release

# Или вручную через Flutter
flutter build apk --release
```

APK будет автоматически подписан с использованием вашего keystore.

**Результат**: `build/app/outputs/flutter-apk/app-release.apk`

---

## ✅ Шаг 5: Проверка подписи APK

Проверить что APK подписан корректно:

```bash
# Установить apksigner (входит в Android SDK)
# Linux/macOS:
$ANDROID_HOME/build-tools/$(ls $ANDROID_HOME/build-tools | tail -1)/apksigner verify --print-certs build/app/outputs/flutter-apk/app-release.apk

# Должен вывести информацию о сертификате
```

Или с помощью jarsigner:

```bash
jarsigner -verify -verbose -certs build/app/outputs/flutter-apk/app-release.apk

# Должно быть: "jar verified"
```

---

## 🔐 Безопасное хранение Keystore

### Локальное хранение

1. **Создайте резервную копию keystore**:
   ```bash
   cp android/data20-release-key.jks ~/Backups/data20-keystore-$(date +%Y%m%d).jks
   ```

2. **Сохраните в зашифрованном хранилище**:
   - 1Password
   - LastPass
   - Encrypted USB drive
   - Encrypted cloud storage (Dropbox, Google Drive с шифрованием)

3. **Запишите пароли отдельно**:
   - В надежном менеджере паролей
   - Или на бумаге в сейфе

### Для CI/CD (GitHub Actions)

Если используете GitHub Actions для автоматической сборки:

1. **Закодируйте keystore в base64**:
   ```bash
   base64 -i android/data20-release-key.jks | pbcopy  # macOS
   base64 -i android/data20-release-key.jks | xclip    # Linux
   ```

2. **Добавьте в GitHub Secrets**:
   - Откройте: `Settings → Secrets and variables → Actions`
   - Добавьте secrets:
     - `ANDROID_KEYSTORE_BASE64` = <base64 encoded keystore>
     - `KEYSTORE_PASSWORD` = <ваш keystore password>
     - `KEY_ALIAS` = data20-release
     - `KEY_PASSWORD` = <ваш key password>

3. **Обновите GitHub Actions workflow** (см. ниже)

---

## 🚀 GitHub Actions для автоматической сборки

Обновите `.github/workflows/build-mobile-apk.yml`:

```yaml
- name: Decode keystore
  run: |
    echo "${{ secrets.ANDROID_KEYSTORE_BASE64 }}" | base64 -d > mobile-app/android/app/data20-release-key.jks

- name: Create key.properties
  run: |
    cat > mobile-app/android/key.properties << EOF
    storePassword=${{ secrets.KEYSTORE_PASSWORD }}
    keyPassword=${{ secrets.KEY_PASSWORD }}
    keyAlias=${{ secrets.KEY_ALIAS }}
    storeFile=data20-release-key.jks
    EOF

- name: Build signed APK
  run: |
    cd mobile-app
    flutter build apk --release
```

---

## 📱 Публикация в Google Play Store

### Подготовка

1. **Создать аккаунт разработчика Google Play**:
   - Стоимость: $25 (одноразово)
   - https://play.google.com/console/signup

2. **Собрать подписанный APK или AAB**:
   ```bash
   # APK (для прямой установки)
   flutter build apk --release

   # AAB (для Google Play - рекомендуется)
   flutter build appbundle --release
   ```

### Загрузка в Google Play Console

1. Откройте [Google Play Console](https://play.google.com/console)
2. Создайте новое приложение
3. Заполните информацию о приложении:
   - Название: Data20 Mobile
   - Категория: Инструменты / Продуктивность
   - Описание (из DOWNLOAD_APK.md)
   - Скриншоты (минимум 2)
   - Иконка приложения
4. Загрузите APK или AAB в раздел "Production"
5. Заполните контент-рейтинг
6. Настройте цены и распространение
7. Отправьте на проверку

**Время проверки**: обычно 1-3 дня

---

## 🆚 Альтернативы Google Play Store

### 1. Прямое распространение APK

- Разместите APK на GitHub Releases
- Пользователи скачивают и устанавливают вручную
- Требуется разрешить "Неизвестные источники" на Android

**Преимущества**: бесплатно, быстро
**Недостатки**: меньше доверия пользователей, нет автообновлений

### 2. F-Droid

- Open source магазин приложений
- Бесплатно
- Требует open source лицензию
- https://f-droid.org/

### 3. Альтернативные магазины

- Amazon Appstore
- Samsung Galaxy Store
- Huawei AppGallery
- GetApps (Xiaomi)

---

## 🔄 Обновление приложения

Для выпуска обновления:

1. **Увеличить версию** в `pubspec.yaml`:
   ```yaml
   version: 1.0.1+2  # 1.0.1 = версия для пользователей, 2 = versionCode
   ```

2. **Собрать новый APK** с тем же keystore:
   ```bash
   flutter build apk --release
   ```

3. **Загрузить в Google Play** или GitHub Releases

**⚠️ ВАЖНО**: Используйте тот же keystore что и в первой версии! Иначе обновление будет невозможно.

---

## 🐛 Troubleshooting

### Ошибка: "keystore not found"

```bash
# Проверьте что keystore существует
ls -la android/data20-release-key.jks

# Проверьте путь в key.properties
cat android/key.properties
```

### Ошибка: "incorrect password"

```bash
# Проверьте пароли в key.properties
# Убедитесь что нет лишних пробелов
```

### Ошибка: "could not find key with alias"

```bash
# Проверьте список ключей в keystore
keytool -list -v -keystore android/data20-release-key.jks

# Убедитесь что alias совпадает
```

### Забыли пароль от keystore

**К сожалению, восстановить пароль невозможно.**

Варианты:
1. Создать новый keystore (приложение будет считаться новым)
2. Искать backup keystore
3. Проверить менеджер паролей

---

## 📚 Дополнительные ресурсы

- **Android Sign Your App**: https://developer.android.com/studio/publish/app-signing
- **Flutter Deployment**: https://docs.flutter.dev/deployment/android
- **Google Play Console**: https://play.google.com/console/about/
- **F-Droid Inclusion**: https://f-droid.org/docs/Inclusion_Policy/

---

## 📝 Checklist: Готовность к публикации

- [ ] Keystore создан и сохранен в безопасном месте
- [ ] key.properties файл настроен
- [ ] APK собирается и подписывается успешно
- [ ] APK протестирован на реальном устройстве
- [ ] Версия установлена корректно в pubspec.yaml
- [ ] Иконка приложения настроена
- [ ] Скриншоты подготовлены
- [ ] Описание приложения готово
- [ ] Политика конфиденциальности создана (если требуется)
- [ ] Google Play аккаунт создан (для Play Store)

---

**Готово!** Теперь вы можете собирать подписанные release APK и публиковать их! 🚀
