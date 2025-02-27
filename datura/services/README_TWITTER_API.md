# Интеграция Twitter API с RapidAPI

## Обзор

Данная интеграция позволяет прозрачно заменить официальный Twitter API на RapidAPI для обхода ограничений и лимитов Twitter. Основная цель - сохранить функциональность приложения, не меняя формат данных, ожидаемых валидатором.

## Настройка

### 1. Получение ключа RapidAPI

1. Зарегистрируйтесь на [RapidAPI](https://rapidapi.com/)
2. Подпишитесь на API [Twitter v1.54](https://rapidapi.com/omarmhaimdat/api/twitter154)
3. Получите API ключ из раздела "Security" или "API Keys"

### 2. Установка переменных окружения

Есть два способа установки необходимых переменных окружения:

#### Через .env файл (рекомендуется)

1. Скопируйте пример файла .env:
   ```bash
   cp .env.example .env
   ```

2. Отредактируйте файл .env и заполните необходимые значения:
   ```
   # Использовать RapidAPI вместо официального Twitter API
   USE_RAPID_API=true
   
   # Ключ RapidAPI
   RAPID_API_KEY=your_rapid_api_key_here
   ```

#### Через переменные окружения

```bash
# Отключить официальный Twitter API и включить RapidAPI
export USE_RAPID_API=true

# Ключ RapidAPI
export RAPID_API_KEY=your_rapid_api_key_here

# Опционально: оставить TWITTER_BEARER_TOKEN для возможности переключения
export TWITTER_BEARER_TOKEN=your_twitter_bearer_token
```

#### Зависимости

Для работы с .env файлами необходима библиотека python-dotenv:

```bash
pip install python-dotenv
```

## Использование

После настройки переменных окружения, приложение автоматически будет использовать RapidAPI вместо официального Twitter API. Все методы API работают так же, как и раньше, сохраняя совместимость.

### Переключение между API

Вы можете легко переключаться между официальным Twitter API и RapidAPI, изменяя значение переменной окружения `USE_RAPID_API`:

```bash
# Использовать RapidAPI
export USE_RAPID_API=true

# Использовать официальный Twitter API
export USE_RAPID_API=false
```

## Сравнение и тестирование API

Для тестирования совместимости между официальным Twitter API и RapidAPI используйте скрипт сравнения:

```bash
python -m datura.scripts.compare_twitter_apis
```

Этот скрипт выполнит одинаковые запросы к обоим API и выведет различия в структуре данных.

## Доступные эндпоинты

| Функциональность | Оригинальный метод | RapidAPI Эндпоинт |
|------------------|------------------------|-----------------------|
| Получение твита по ID | `get_tweet_by_id` | `/tweet/details` |
| Получение твитов по ID | `get_tweets_by_ids` | Множественные вызовы `/tweet/details` |
| Поиск недавних твитов | `get_recent_tweets` | `/search/search` |
| Поиск твитов в архиве | `get_full_archive_tweets` | `/search/search` (с date_range) |
| Информация о пользователе по ID | `get_user` | `/user/details` |
| Информация о пользователе по имени | `get_user_by_username` | `/user/details` |
| Подписки пользователя | `get_user_followings` | `/user/following` |

## Преобразование данных

Модуль автоматически преобразует данные из формата RapidAPI в формат, ожидаемый валидатором (аналогичный Twitter API v2). Основные преобразования:

- Структура твита (id, text, metrics и т.д.)
- Структура пользователя (id, username, metrics и т.д.)
- Обработка медиа-контента (изображения, видео)
- Параметры запросов (query, limit, date ranges и т.д.)

## Отладка

Если вы столкнулись с проблемами совместимости, попробуйте следующее:

1. Установите `export BITTENSOR_DEBUG=trace` для подробного логирования
2. Запустите скрипт сравнения API для выявления различий
3. Проверьте правильность установки переменных окружения
4. Убедитесь, что файл .env находится в корневой директории проекта и содержит правильные значения
5. Проверьте установлена ли библиотека python-dotenv (`pip install python-dotenv`)

## Ограничения RapidAPI

- У разных планов RapidAPI разные лимиты на количество запросов
- Некоторые эндпоинты могут быть недоступны в бесплатном плане
- Параметры поиска могут немного отличаться от официального API

## Дополнительные ресурсы

- [Документация RapidAPI Twitter154](https://rapidapi.com/omarmhaimdat/api/twitter154/details)
- [Twitter API v2 Документация](https://developer.twitter.com/en/docs/twitter-api/data-dictionary/introduction)
- [Документация python-dotenv](https://github.com/theskumar/python-dotenv)
