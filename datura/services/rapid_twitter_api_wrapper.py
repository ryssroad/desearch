import aiohttp
import os
import bittensor as bt
from typing import Dict, Any, List, Optional, Tuple
import json
from datetime import datetime
from datura.protocol import TwitterScraperTweet, TwitterScraperUser, TwitterScraperMedia
from datura.services.dotenv_config import load_dotenv, get_env_variable

# Загружаем переменные из .env файла
load_dotenv()

# RapidAPI ключ (получаем из переменной окружения)
RAPID_API_KEY = get_env_variable("RAPID_API_KEY")

class RapidTwitterAPIClient:
    """
    Клиент для работы с Twitter API через RapidAPI.
    Заменяет официальный Twitter API для обхода ограничений.
    """
    def __init__(self):
        """Инициализация клиента RapidAPI для Twitter"""
        self.api_key = RAPID_API_KEY
        if not self.api_key:
            bt.logging.error("RAPID_API_KEY не найден в переменных окружения")
            raise ValueError("Отсутствует RAPID_API_KEY. Установите переменную окружения.")
        
        self.base_url = "https://twitter154.p.rapidapi.com"
        self.headers = {
            "x-rapidapi-key": self.api_key,
            "x-rapidapi-host": "twitter154.p.rapidapi.com"
        }

    async def connect_to_endpoint(self, endpoint: str, params: Dict[str, Any]) -> Tuple[Any, int, str]:
        """
        Подключение к конечной точке RapidAPI.
        
        Args:
            endpoint: Конечная точка RapidAPI (без базового URL)
            params: Параметры запроса
            
        Returns:
            Tuple из JSON ответа, статус-кода и текста ответа
        """
        url = f"{self.base_url}/{endpoint}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers, params=params) as response:
                if response.status in [401, 403]:
                    bt.logging.error(
                        f"Критическая ошибка запроса RapidAPI: {await response.text()}"
                    )

                json_data = None
                try:
                    json_data = await response.json()
                except aiohttp.ContentTypeError:
                    pass

                response_text = await response.text()
                return json_data, response.status, response_text

    async def get_tweet_by_id(self, tweet_id: str) -> Dict[str, Any]:
        """
        Получение твита по его ID.
        
        Args:
            tweet_id: ID твита
            
        Returns:
            Данные твита в формате Twitter API v2
        """
        params = {"tweet_id": tweet_id}
        response_json, status_code, _ = await self.connect_to_endpoint("tweet/details", params)
        
        if status_code != 200 or not response_json:
            return {"data": {}, "meta": {"result_count": 0}}
        
        # Преобразование в формат, аналогичный Twitter API v2
        transformed_data = self._transform_tweet_to_twitter_api_format(response_json)
        return {"data": transformed_data, "meta": {"result_count": 1}}

    async def get_tweets_by_ids(self, tweet_ids: List[str]) -> Dict[str, Any]:
        """
        Получение нескольких твитов по их ID.
        
        Args:
            tweet_ids: Список ID твитов
            
        Returns:
            Данные твитов в формате Twitter API v2
        """
        results = []
        for tweet_id in tweet_ids:
            response = await self.get_tweet_by_id(tweet_id)
            if response.get("data"):
                results.append(response["data"])
        
        return {"data": results, "meta": {"result_count": len(results)}}

    async def get_recent_tweets(self, query_params: Dict[str, Any]) -> Tuple[Dict[str, Any], int, str]:
        """
        Поиск недавних твитов по заданным параметрам.
        
        Args:
            query_params: Параметры запроса в формате Twitter API
            
        Returns:
            Tuple из JSON ответа, статус-кода и текста ответа
        """
        # Преобразование параметров из формата Twitter API в формат RapidAPI
        rapid_params = self._transform_search_params(query_params)
        
        response_json, status_code, response_text = await self.connect_to_endpoint(
            "search/search", rapid_params
        )
        
        if status_code != 200 or not response_json:
            return {"data": [], "meta": {"result_count": 0}}, status_code, response_text
        
        # Преобразование результатов в формат, аналогичный Twitter API v2
        transformed_data = []
        if isinstance(response_json, list):
            for tweet in response_json:
                transformed_data.append(self._transform_tweet_to_twitter_api_format(tweet))
        
        result = {
            "data": transformed_data,
            "includes": {
                "users": self._extract_users_from_tweets(response_json),
                "media": self._extract_media_from_tweets(response_json)
            },
            "meta": {"result_count": len(transformed_data)}
        }
        
        return result, status_code, response_text

    async def get_full_archive_tweets(self, query_params: Dict[str, Any]) -> Tuple[Dict[str, Any], int, str]:
        """
        Поиск твитов по архиву по заданным параметрам.
        Использует тот же эндпоинт, что и get_recent_tweets, но с дополнительными параметрами.
        
        Args:
            query_params: Параметры запроса в формате Twitter API
            
        Returns:
            Tuple из JSON ответа, статус-кода и текста ответа
        """
        # Вызываем поиск с теми же параметрами
        return await self.get_recent_tweets(query_params)

    async def get_user_followings(self, user_id: str, params: Dict[str, Any]) -> Tuple[Dict[str, Any], int, str]:
        """
        Получение списка подписок пользователя.
        
        Args:
            user_id: ID пользователя
            params: Дополнительные параметры запроса
            
        Returns:
            Tuple из JSON ответа, статус-кода и текста ответа
        """
        rapid_params = {
            "user_id": user_id,
            "limit": params.get("max_results", 40)
        }
        
        response_json, status_code, response_text = await self.connect_to_endpoint(
            "user/following", rapid_params
        )
        
        if status_code != 200 or not response_json:
            return {"data": [], "meta": {"result_count": 0}}, status_code, response_text
        
        # Преобразование результатов в формат, аналогичный Twitter API v2
        transformed_data = []
        if isinstance(response_json, dict) and 'following' in response_json:
            for user in response_json["following"]:
                transformed_data.append(self._transform_user_to_twitter_api_format(user))
        
        result = {
            "data": transformed_data,
            "meta": {"result_count": len(transformed_data)}
        }
        
        return result, status_code, response_text

    async def get_user(self, user_id: str, params: Dict[str, Any]) -> Tuple[Dict[str, Any], int, str]:
        """
        Получение информации о пользователе по ID.
        
        Args:
            user_id: ID пользователя
            params: Дополнительные параметры запроса
            
        Returns:
            Tuple из JSON ответа, статус-кода и текста ответа
        """
        rapid_params = {"user_id": user_id}
        
        response_json, status_code, response_text = await self.connect_to_endpoint(
            "user/details", rapid_params
        )
        
        if status_code != 200 or not response_json:
            return {"data": {}, "meta": {"result_count": 0}}, status_code, response_text
        
        # Преобразование в формат, аналогичный Twitter API v2
        transformed_data = self._transform_user_to_twitter_api_format(response_json)
        
        result = {
            "data": transformed_data,
            "meta": {"result_count": 1}
        }
        
        return result, status_code, response_text

    async def get_user_by_username(self, username: str, params: Dict[str, Any]) -> Tuple[Dict[str, Any], int, str]:
        """
        Получение информации о пользователе по имени пользователя.
        
        Args:
            username: Имя пользователя (без @)
            params: Дополнительные параметры запроса
            
        Returns:
            Tuple из JSON ответа, статус-кода и текста ответа
        """
        rapid_params = {"username": username}
        
        response_json, status_code, response_text = await self.connect_to_endpoint(
            "user/details", rapid_params
        )
        
        if status_code != 200 or not response_json:
            return {"data": {}, "meta": {"result_count": 0}}, status_code, response_text
        
        # Преобразование в формат, аналогичный Twitter API v2
        transformed_data = self._transform_user_to_twitter_api_format(response_json)
        
        result = {
            "data": transformed_data,
            "meta": {"result_count": 1}
        }
        
        return result, status_code, response_text

    def _transform_search_params(self, twitter_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Преобразование параметров запроса из формата Twitter API в формат RapidAPI.
        
        Args:
            twitter_params: Параметры запроса в формате Twitter API
            
        Returns:
            Параметры запроса в формате RapidAPI
        """
        rapid_params = {
            "query": twitter_params.get("query", ""),
            "limit": twitter_params.get("max_results", "10"),
        }
        
        # Параметры дат
        if "start_time" in twitter_params:
            # Преобразование ISO формата в YYYY-MM-DD
            try:
                date_obj = datetime.fromisoformat(twitter_params["start_time"].replace('Z', '+00:00'))
                rapid_params["start_date"] = date_obj.strftime("%Y-%m-%d")
            except (ValueError, TypeError):
                pass
                
        if "end_time" in twitter_params:
            try:
                date_obj = datetime.fromisoformat(twitter_params["end_time"].replace('Z', '+00:00'))
                rapid_params["end_date"] = date_obj.strftime("%Y-%m-%d")
            except (ValueError, TypeError):
                pass
        
        # Язык
        if "lang" in twitter_params:
            rapid_params["language"] = twitter_params["lang"]
        
        # Если запрос содержит конкретные минимальные значения метрик
        if "min:retweets" in twitter_params.get("query", ""):
            try:
                import re
                retweets_match = re.search(r'min:retweets:(\d+)', twitter_params["query"])
                if retweets_match:
                    rapid_params["min_retweets"] = retweets_match.group(1)
            except:
                pass
                
        if "min:replies" in twitter_params.get("query", ""):
            try:
                import re
                replies_match = re.search(r'min:replies:(\d+)', twitter_params["query"])
                if replies_match:
                    rapid_params["min_replies"] = replies_match.group(1)
            except:
                pass
                
        if "min:likes" in twitter_params.get("query", ""):
            try:
                import re
                likes_match = re.search(r'min:likes:(\d+)', twitter_params["query"])
                if likes_match:
                    rapid_params["min_likes"] = likes_match.group(1)
            except:
                pass
        
        return rapid_params

    def _transform_tweet_to_twitter_api_format(self, rapid_tweet: Dict[str, Any]) -> Dict[str, Any]:
        """
        Преобразует твит из формата RapidAPI в формат Twitter API v2.
        
        Args:
            rapid_tweet: Данные твита в формате RapidAPI
            
        Returns:
            Данные твита в формате Twitter API v2
        """
        if not rapid_tweet:
            return {}
            
        # Создаем базовую структуру
        twitter_api_tweet = {
            "id": rapid_tweet.get("tweet_id"),
            "text": rapid_tweet.get("text", ""),
            "created_at": rapid_tweet.get("creation_date"),
            "author_id": rapid_tweet.get("user", {}).get("user_id"),
            "conversation_id": rapid_tweet.get("conversation_id"),
            "lang": rapid_tweet.get("language"),
            "possibly_sensitive": False,  # По умолчанию
            "in_reply_to_user_id": None,
            "public_metrics": {
                "retweet_count": rapid_tweet.get("retweet_count", 0),
                "reply_count": rapid_tweet.get("reply_count", 0),
                "like_count": rapid_tweet.get("favorite_count", 0),
                "quote_count": rapid_tweet.get("quote_count", 0),
                "bookmark_count": 0,  # Это поле может отсутствовать
            }
        }
        
        # Добавляем информацию о медиа, если она есть
        attachments = {}
        
        # Обработка фото
        if "media_url" in rapid_tweet and rapid_tweet["media_url"]:
            attachments["media_keys"] = []
            for i, url in enumerate(rapid_tweet["media_url"]):
                media_key = f"media_{twitter_api_tweet['id']}_{i}"
                attachments["media_keys"].append(media_key)
        
        # Обработка видео
        if "video_url" in rapid_tweet and rapid_tweet["video_url"]:
            if "media_keys" not in attachments:
                attachments["media_keys"] = []
            media_key = f"video_{twitter_api_tweet['id']}"
            attachments["media_keys"].append(media_key)
        
        if attachments:
            twitter_api_tweet["attachments"] = attachments
            
        # Добавляем информацию о связанных твитах
        referenced_tweets = []
        
        # Если это ответ
        if rapid_tweet.get("in_reply_to_status_id"):
            referenced_tweets.append({
                "type": "replied_to",
                "id": rapid_tweet["in_reply_to_status_id"]
            })
            
        # Если это цитата
        if rapid_tweet.get("quoted_status_id"):
            referenced_tweets.append({
                "type": "quoted",
                "id": rapid_tweet["quoted_status_id"]
            })
            
        # Если это ретвит
        if rapid_tweet.get("retweet", False):
            referenced_tweets.append({
                "type": "retweeted",
                "id": "unknown"  # В данных RapidAPI нет ID оригинального твита для ретвита
            })
            
        if referenced_tweets:
            twitter_api_tweet["referenced_tweets"] = referenced_tweets
            
        return twitter_api_tweet

    def _transform_user_to_twitter_api_format(self, rapid_user: Dict[str, Any]) -> Dict[str, Any]:
        """
        Преобразует пользователя из формата RapidAPI в формат Twitter API v2.
        
        Args:
            rapid_user: Данные пользователя в формате RapidAPI
            
        Returns:
            Данные пользователя в формате Twitter API v2
        """
        if not rapid_user:
            return {}
            
        twitter_api_user = {
            "id": rapid_user.get("user_id"),
            "name": rapid_user.get("name", ""),
            "username": rapid_user.get("username", ""),
            "created_at": rapid_user.get("creation_date"),
            "description": rapid_user.get("description", ""),
            "protected": rapid_user.get("is_private", False),
            "verified": rapid_user.get("is_verified", False) or rapid_user.get("is_blue_verified", False),
            "location": rapid_user.get("location", ""),
            "profile_image_url": rapid_user.get("profile_pic_url", ""),
            "url": rapid_user.get("external_url", ""),
            "public_metrics": {
                "followers_count": rapid_user.get("follower_count", 0),
                "following_count": rapid_user.get("following_count", 0),
                "tweet_count": rapid_user.get("number_of_tweets", 0),
                "listed_count": 0  # Может отсутствовать
            }
        }
        
        return twitter_api_user

    def _extract_users_from_tweets(self, tweets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Извлекает уникальных пользователей из списка твитов.
        
        Args:
            tweets: Список твитов в формате RapidAPI
            
        Returns:
            Список пользователей в формате Twitter API v2
        """
        users = {}
        
        if not isinstance(tweets, list):
            tweets = [tweets]
            
        for tweet in tweets:
            if "user" in tweet and tweet["user"] and "user_id" in tweet["user"]:
                user_id = tweet["user"]["user_id"]
                if user_id not in users:
                    users[user_id] = self._transform_user_to_twitter_api_format(tweet["user"])
                    
        return list(users.values())

    def _extract_media_from_tweets(self, tweets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Извлекает медиа из списка твитов.
        
        Args:
            tweets: Список твитов в формате RapidAPI
            
        Returns:
            Список медиа в формате Twitter API v2
        """
        media_list = []
        
        if not isinstance(tweets, list):
            tweets = [tweets]
            
        for tweet in tweets:
            tweet_id = tweet.get("tweet_id")
            
            # Обработка изображений
            if "media_url" in tweet and tweet["media_url"]:
                for i, url in enumerate(tweet["media_url"]):
                    media_key = f"media_{tweet_id}_{i}"
                    media_list.append({
                        "media_key": media_key,
                        "type": "photo",
                        "url": url,
                        "tweet_ids": [tweet_id]
                    })
                    
            # Обработка видео
            if "video_url" in tweet and tweet["video_url"]:
                media_key = f"video_{tweet_id}"
                media_list.append({
                    "media_key": media_key,
                    "type": "video",
                    "url": tweet["video_url"],
                    "tweet_ids": [tweet_id]
                })
                    
        return media_list
