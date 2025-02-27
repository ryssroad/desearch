#!/usr/bin/env python3
"""
Скрипт для сравнения данных между официальным Twitter API и RapidAPI.
Это помогает понять различия в форматах данных и проверить корректность трансформации.

Запуск:
python -m datura.scripts.compare_twitter_apis

Необходимые переменные окружения:
- TWITTER_BEARER_TOKEN - токен официального Twitter API
- RAPID_API_KEY - ключ RapidAPI

Как использовать:
1. Установите переменные окружения
2. Запустите скрипт
3. Проанализируйте вывод для понимания различий в форматах данных
"""

import os
import asyncio
import json
import sys
from pprint import pprint
from typing import Dict, Any
import aiohttp

# Добавляем родительскую директорию в путь поиска модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Импортируем необходимые модули
from datura.services.twitter_api_wrapper import TwitterAPIClient
from datura.services.rapid_twitter_api_wrapper import RapidTwitterAPIClient

# Параметры для тестирования
TEST_TWEET_ID = "1517995317697916928"  # ID твита для тестирования
TEST_USER_ID = "96479162"  # ID пользователя для тестирования
TEST_USERNAME = "omarmhaimdat"  # Имя пользователя для тестирования
TEST_SEARCH_QUERY = "python"  # Запрос для поиска твитов

async def fetch_data_from_official_api():
    """Получает данные из официального Twitter API"""
    client = TwitterAPIClient()
    client.use_rapid_api = False  # Принудительно используем официальный API
    
    print("\n--- ОФИЦИАЛЬНЫЙ TWITTER API ---")
    
    # Получаем твит по ID
    print("\n1. Получение твита по ID:")
    tweet_response = await client.get_tweet_by_id(TEST_TWEET_ID)
    print("Структура ответа:")
    pprint(tweet_response)
    
    # Получаем информацию о пользователе по ID
    print("\n2. Получение информации о пользователе по ID:")
    user_response, status_code, _ = await client.get_user(TEST_USER_ID, {})
    print("Структура ответа:")
    pprint(user_response)
    
    # Получаем информацию о пользователе по имени
    print("\n3. Получение информации о пользователе по имени:")
    username_response, status_code, _ = await client.get_user_by_username(TEST_USERNAME, {})
    print("Структура ответа:")
    pprint(username_response)
    
    # Получаем подписки пользователя
    print("\n4. Получение подписок пользователя:")
    following_response, status_code, _ = await client.get_user_followings(TEST_USER_ID, {"max_results": 5})
    print("Структура ответа:")
    pprint(following_response)
    
    # Выполняем поиск твитов
    print("\n5. Поиск твитов:")
    search_response, status_code, _ = await client.get_recent_tweets({
        "query": TEST_SEARCH_QUERY,
        "max_results": 5,
        "tweet.fields": "author_id,created_at,id,possibly_sensitive,text,entities,public_metrics",
        "user.fields": "created_at,description,id,location,name,profile_image_url,url,username,verified",
        "expansions": "author_id,attachments.media_keys,entities.mentions.username"
    })
    print("Структура ответа:")
    pprint(search_response)
    
    return {
        "tweet": tweet_response,
        "user": user_response,
        "username": username_response,
        "following": following_response,
        "search": search_response
    }

async def fetch_data_from_rapid_api():
    """Получает данные из RapidAPI"""
    client = RapidTwitterAPIClient()
    
    print("\n--- RAPID API ---")
    
    # Получаем твит по ID
    print("\n1. Получение твита по ID:")
    tweet_response = await client.get_tweet_by_id(TEST_TWEET_ID)
    print("Структура ответа:")
    pprint(tweet_response)
    
    # Получаем информацию о пользователе по ID
    print("\n2. Получение информации о пользователе по ID:")
    user_response, status_code, _ = await client.get_user(TEST_USER_ID, {})
    print("Структура ответа:")
    pprint(user_response)
    
    # Получаем информацию о пользователе по имени
    print("\n3. Получение информации о пользователе по имени:")
    username_response, status_code, _ = await client.get_user_by_username(TEST_USERNAME, {})
    print("Структура ответа:")
    pprint(username_response)
    
    # Получаем подписки пользователя
    print("\n4. Получение подписок пользователя:")
    following_response, status_code, _ = await client.get_user_followings(TEST_USER_ID, {"max_results": 5})
    print("Структура ответа:")
    pprint(following_response)
    
    # Выполняем поиск твитов
    print("\n5. Поиск твитов:")
    search_response, status_code, _ = await client.get_recent_tweets({
        "query": TEST_SEARCH_QUERY,
        "max_results": 5,
        "tweet.fields": "author_id,created_at,id,possibly_sensitive,text,entities,public_metrics",
        "user.fields": "created_at,description,id,location,name,profile_image_url,url,username,verified",
        "expansions": "author_id,attachments.media_keys,entities.mentions.username"
    })
    print("Структура ответа:")
    pprint(search_response)
    
    return {
        "tweet": tweet_response,
        "user": user_response,
        "username": username_response,
        "following": following_response,
        "search": search_response
    }

async def compare_results(official_data, rapid_data):
    """Сравнивает результаты между двумя API и выводит различия"""
    print("\n--- СРАВНЕНИЕ РЕЗУЛЬТАТОВ ---")
    
    for endpoint in official_data:
        print(f"\nСравнение для: {endpoint}")
        
        official_fields = set()
        rapid_fields = set()
        
        def extract_fields(data, prefix="", result=None):
            if result is None:
                result = set()
            
            if isinstance(data, dict):
                for key, value in data.items():
                    new_prefix = f"{prefix}.{key}" if prefix else key
                    result.add(new_prefix)
                    extract_fields(value, new_prefix, result)
            elif isinstance(data, list) and data and isinstance(data[0], dict):
                extract_fields(data[0], f"{prefix}[0]", result)
            
            return result
        
        # Извлекаем все поля из структуры официального API
        if official_data[endpoint]:
            official_fields = extract_fields(official_data[endpoint])
        
        # Извлекаем все поля из структуры RapidAPI
        if rapid_data[endpoint]:
            rapid_fields = extract_fields(rapid_data[endpoint])
        
        # Выводим различия
        only_in_official = official_fields - rapid_fields
        only_in_rapid = rapid_fields - official_fields
        
        if only_in_official:
            print("Поля, присутствующие только в официальном API:")
            for field in sorted(only_in_official):
                print(f"  - {field}")
        
        if only_in_rapid:
            print("Поля, присутствующие только в RapidAPI:")
            for field in sorted(only_in_rapid):
                print(f"  - {field}")
        
        if not only_in_official and not only_in_rapid:
            print("Структуры полностью совпадают!")

async def main():
    """Основная функция скрипта"""
    # Проверяем наличие необходимых переменных окружения
    if not os.environ.get("TWITTER_BEARER_TOKEN"):
        print("ОШИБКА: Не установлена переменная окружения TWITTER_BEARER_TOKEN")
        print("Для сравнения с официальным API, необходимо установить этот токен.")
        print("Будет выполнено только тестирование RapidAPI.")
        official_data = None
    else:
        official_data = await fetch_data_from_official_api()
    
    if not os.environ.get("RAPID_API_KEY"):
        print("ОШИБКА: Не установлена переменная окружения RAPID_API_KEY")
        print("Для тестирования RapidAPI, необходимо установить этот ключ.")
        print("Будет выполнено только тестирование официального API.")
        rapid_data = None
    else:
        rapid_data = await fetch_data_from_rapid_api()
    
    # Если оба API доступны, выполняем сравнение
    if official_data and rapid_data:
        await compare_results(official_data, rapid_data)
    
    print("\nТестирование завершено!")

if __name__ == "__main__":
    asyncio.run(main())
