import bittensor as bt
from datura.protocol import (
    TwitterSearchSynapse,
    TwitterIDSearchSynapse,
    TwitterURLsSearchSynapse,
    TwitterScraperTweet,
    TwitterScraperUser,
)
from datura.services.rapidapi_twitter_wrapper import RapidAPITwitterClient
from pydantic import ValidationError

class TwitterSearchMiner:
    def __init__(self, miner: any):
        self.miner = miner
        self.twitter_client = RapidAPITwitterClient()

    def _convert_rapidapi_to_scraper_tweet(self, tweet_data: dict) -> dict:
        """Convert RapidAPI tweet format to TwitterScraperTweet format"""
        user_data = tweet_data.get("user", {})
        
        try:
            user = TwitterScraperUser(
                id=user_data.get("id_str", ""),
                username=user_data.get("screen_name", ""),
                name=user_data.get("name", ""),
                url=f"https://x.com/{user_data.get('screen_name', '')}",
                description=user_data.get("description", ""),
                location=user_data.get("location", ""),
                verified=user_data.get("verified", False),
                is_blue_verified=user_data.get("verified", False),
                followers_count=user_data.get("followers_count", 0),
                media_count=user_data.get("media_count", 0),
                favourites_count=user_data.get("favourites_count", 0),
                listed_count=user_data.get("listed_count", 0),
                statuses_count=user_data.get("statuses_count", 0),
                created_at=user_data.get("created_at", ""),
                profile_image_url=user_data.get("profile_image_url", ""),
                profile_banner_url=user_data.get("profile_banner_url", ""),
                entities=[],
                pinned_tweet_ids=[],
                can_dm=True,
                can_media_tag=True
            )
            
            tweet = TwitterScraperTweet(
                user=user,
                id=tweet_data.get("id_str", ""),
                text=tweet_data.get("text", ""),
                reply_count=tweet_data.get("reply_count", 0),
                retweet_count=tweet_data.get("retweet_count", 0),
                like_count=tweet_data.get("favorite_count", 0),
                quote_count=tweet_data.get("quote_count", 0),
                bookmark_count=0,
                url=f"https://x.com/{user_data.get('screen_name', '')}/status/{tweet_data.get('id_str', '')}",
                created_at=tweet_data.get("created_at", ""),
                media=[],
                is_quote_tweet=tweet_data.get("is_quote_status", False),
                is_retweet=bool(tweet_data.get("retweeted_status", False)),
                conversation_id=tweet_data.get("conversation_id_str", ""),
                in_reply_to_screen_name=tweet_data.get("in_reply_to_screen_name"),
                in_reply_to_user_id=tweet_data.get("in_reply_to_user_id_str"),
                in_reply_to_status_id=tweet_data.get("in_reply_to_status_id_str"),
                display_text_range=[0, len(tweet_data.get("text", ""))],
                entities=tweet_data.get("entities", []),
                extended_entities=tweet_data.get("extended_entities", []),
                lang=tweet_data.get("lang", "en"),
                quote=None,
                quoted_status_id=tweet_data.get("quoted_status_id_str")
            )
            
            return tweet.dict()
        except ValidationError as e:
            bt.logging.error(f"Validation error while converting tweet: {e}")
            raise

    async def search(self, synapse: TwitterSearchSynapse):
        """Execute Twitter search using RapidAPI"""
        query = synapse.query
        search_params = {
            "query": query,
            "lang": synapse.lang,
            "max_results": 10,  # Adjust as needed
        }

        bt.logging.info(f"Executing search with query: {query} and params: {search_params}")

        try:
            response_data, status_code, _ = await self.twitter_client.get_recent_tweets(search_params)
            
            if response_data and "data" in response_data:
                # Convert tweets to TwitterScraperTweet format
                synapse.results = [
                    self._convert_rapidapi_to_scraper_tweet(tweet)
                    for tweet in response_data["data"]
                ]
            else:
                synapse.results = []
                
        except Exception as e:
            bt.logging.error(f"Error during Twitter search: {e}")
            synapse.results = []

        return synapse

    async def search_by_id(self, synapse: TwitterIDSearchSynapse):
        """Search for a tweet by ID using RapidAPI"""
        tweet_id = synapse.id
        bt.logging.info(f"Searching for tweet by ID: {tweet_id}")

        try:
            tweet_data = await self.twitter_client.get_tweet_by_id(tweet_id)
            
            if tweet_data and "data" in tweet_data:
                # Convert tweet to TwitterScraperTweet format
                synapse.results = [self._convert_rapidapi_to_scraper_tweet(tweet_data["data"])]
            else:
                synapse.results = []
                
        except Exception as e:
            bt.logging.error(f"Error during tweet ID search: {e}")
            synapse.results = []

        return synapse

    async def search_by_urls(self, synapse: TwitterURLsSearchSynapse):
        """Search for tweets by URLs using RapidAPI"""
        urls = synapse.urls
        bt.logging.info(f"Searching for tweets by URLs: {urls}")

        results = []
        for url in urls:
            try:
                # Extract tweet ID from URL
                tweet_id = url.split("/status/")[-1].split("?")[0]
                tweet_data = await self.twitter_client.get_tweet_by_id(tweet_id)
                
                if tweet_data and "data" in tweet_data:
                    results.append(self._convert_rapidapi_to_scraper_tweet(tweet_data["data"]))
                    
            except Exception as e:
                bt.logging.error(f"Error processing URL {url}: {e}")
                continue

        synapse.results = results
        return synapse