import aiohttp
import os
import bittensor as bt
from datura.services.twitter_utils import TwitterUtils

RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY")
RAPIDAPI_HOST = os.environ.get("RAPIDAPI_HOST", "twitter154.p.rapidapi.com")

class RapidAPITwitterClient:
    def __init__(
        self,
        openai_query_model="gpt-3.5-turbo-0125",
        openai_fix_query_model="gpt-4-1106-preview",
    ):
        self.rapidapi_key = RAPIDAPI_KEY
        self.rapidapi_host = RAPIDAPI_HOST
        self.utils = TwitterUtils()
        self.openai_query_model = openai_query_model
        self.openai_fix_query_model = openai_fix_query_model

    async def _make_request(self, endpoint: str, params: dict = None, method: str = "GET"):
        """Make a request to RapidAPI endpoint"""
        url = f"https://{self.rapidapi_host}/{endpoint}"
        headers = {
            "X-RapidAPI-Key": self.rapidapi_key,
            "X-RapidAPI-Host": self.rapidapi_host
        }

        async with aiohttp.ClientSession() as session:
            if method == "GET":
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status not in [200, 201]:
                        bt.logging.error(
                            f"RapidAPI Request error occurred: {await response.text()}"
                        )
                    try:
                        return await response.json(), response.status, await response.text()
                    except aiohttp.ContentTypeError:
                        return None, response.status, await response.text()
            elif method == "POST":
                async with session.post(url, headers=headers, json=params) as response:
                    if response.status not in [200, 201]:
                        bt.logging.error(
                            f"RapidAPI Request error occurred: {await response.text()}"
                        )
                    try:
                        return await response.json(), response.status, await response.text()
                    except aiohttp.ContentTypeError:
                        return None, response.status, await response.text()

    async def get_tweet_by_id(self, tweet_id: str):
        """Get a single tweet by ID"""
        response_json, status_code, _ = await self._make_request(
            "tweet/details", {"tweet_id": tweet_id}
        )
        
        # Convert RapidAPI response to Twitter API format
        if response_json:
            return {
                "data": {
                    "id": response_json.get("id_str"),
                    "text": response_json.get("text"),
                    "created_at": response_json.get("created_at"),
                    "author": {
                        "id": response_json.get("user", {}).get("id_str"),
                        "name": response_json.get("user", {}).get("name"),
                        "username": response_json.get("user", {}).get("screen_name")
                    }
                }
            }
        return response_json

    async def get_tweets_by_ids(self, tweet_ids: list):
        """Get multiple tweets by IDs"""
        results = []
        for tweet_id in tweet_ids:
            tweet_data = await self.get_tweet_by_id(tweet_id)
            if tweet_data and "data" in tweet_data:
                results.append(tweet_data["data"])
        return {"data": results} if results else {"data": []}

    async def get_recent_tweets(self, query_params: dict):
        """Search recent tweets"""
        # Convert Twitter API params to RapidAPI format
        rapidapi_params = {
            "query": query_params.get("query", ""),
            "limit": query_params.get("max_results", 10),
            "language": query_params.get("lang", "en"),
        }
        
        response_json, status_code, response_text = await self._make_request(
            "search/search", rapidapi_params
        )
        
        # Convert RapidAPI response format to Twitter API format
        if response_json and "results" in response_json:
            return {
                "data": [
                    {
                        "id": tweet["id_str"],
                        "text": tweet["text"],
                        "created_at": tweet["created_at"],
                        "author": {
                            "id": tweet["user"]["id_str"],
                            "name": tweet["user"]["name"],
                            "username": tweet["user"]["screen_name"]
                        },
                        "public_metrics": {
                            "retweet_count": tweet.get("retweet_count", 0),
                            "reply_count": tweet.get("reply_count", 0),
                            "like_count": tweet.get("favorite_count", 0),
                            "quote_count": tweet.get("quote_count", 0)
                        }
                    }
                    for tweet in response_json["results"]
                ]
            }, status_code, response_text
        return response_json, status_code, response_text

    async def get_user_by_username(self, username: str, params: dict):
        """Get user info by username"""
        response_json, status_code, _ = await self._make_request(
            "user/details", {"username": username}
        )
        
        # Convert RapidAPI response to Twitter API format
        if response_json:
            return {
                "data": {
                    "id": response_json.get("id_str"),
                    "name": response_json.get("name"),
                    "username": response_json.get("screen_name"),
                    "description": response_json.get("description"),
                    "public_metrics": {
                        "followers_count": response_json.get("followers_count", 0),
                        "following_count": response_json.get("friends_count", 0),
                        "tweet_count": response_json.get("statuses_count", 0),
                        "listed_count": response_json.get("listed_count", 0)
                    }
                }
            }
        return response_json