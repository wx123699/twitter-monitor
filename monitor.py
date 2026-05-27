import asyncio
import os
import json
import requests
from twscrape import API, gather

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
TWITTER_USERNAME = os.environ["TWITTER_USERNAME"]
TWITTER_PASSWORD = os.environ["TWITTER_PASSWORD"]
MONITOR_ACCOUNTS = os.environ.get("MONITOR_ACCOUNTS", "BinanceWallet").split(",")
LAST_TWEET_FILE = "last_tweet_ids.json"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"})

def load_last_ids():
    if os.path.exists(LAST_TWEET_FILE):
        with open(LAST_TWEET_FILE) as f:
            return json.load(f)
    return {}

def save_last_ids(ids):
    with open(LAST_TWEET_FILE, "w") as f:
        json.dump(ids, f)

async def main():
    api = API()
    await api.pool.add_account(TWITTER_USERNAME, TWITTER_PASSWORD)
    await api.pool.login_all()
    last_ids = load_last_ids()
    for account in MONITOR_ACCOUNTS:
        account = account.strip()
        try:
            user = await api.user_by_login(account)
            if not user:
                continue
            tweets = await gather(api.user_tweets(user.id, limit=5))
            if not tweets:
                continue
            last_id = last_ids.get(account, 0)
            new_tweets = [t for t in tweets if t.id > last_id]
            new_tweets.sort(key=lambda x: x.id)
            for tweet in new_tweets:
                message = f"🐦 <b>@{account}</b>

{tweet.rawContent}

🔗 https://x.com/{account}/status/{tweet.id}"
                send_telegram(message)
                print(f"Sent tweet {tweet.id} from @{account}")
            if tweets:
                last_ids[account] = max(t.id for t in tweets)
        except Exception as e:
            print(f"Error processing @{account}: {e}")
    save_last_ids(last_ids)

if __name__ == "__main__":
    asyncio.run(main())
