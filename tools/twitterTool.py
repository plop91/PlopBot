from tweepy import OAuthHandler
from tweepy import API
import json
from tools.basicTools import readJson
import wget
import asyncio


class twitter:
    def __init__(self):
        self.info = readJson("tools/twittertoken.json")

        self.auth = OAuthHandler(self.info["apikey"], self.info["apisecret"])
        self.auth.set_access_token(self.info["accesstoken"], self.info["accesstokensecret"])
        self.auth_api = API(self.auth)

    async def getInfo(self, account_list):

        if len(account_list) > 0:
            for target in account_list:
                print("Getting data for " + target)
                item = self.auth_api.get_user(target)
                print("name: " + item.name)
                print("screen_name: " + item.screen_name)
                print("description: " + item.description)
                print("statuses_count: " + str(item.statuses_count))
                print("friends_count: " + str(item.friends_count))
                print("followers_count: " + str(item.followers_count))
                data_set = {"name: ": item.name, "screen_name: ": item.screen_name, "description: ": item.description,
                            "statuses_count: ": str(item.statuses_count), "friends_count: ": str(item.friends_count),
                            "followers_count: ": str(item.followers_count)}
                return json.dumps(data_set)

    async def get_last_tweet_image(self, username, save_as="image.jpg"):
        tweets = self.auth_api.user_timeline(screen_name=username, count=1, include_rts=False,
                                             exclude_replies=True)
        tmp = []
        tweets_for_csv = [tweet.text for tweet in tweets]  # CSV file created
        for j in tweets_for_csv:
            # Appending tweets to the empty array tmp
            tmp.append(j)
        print(tmp)
        media_files = set()
        for status in tweets:
            media = status.entities.get('media', [])
            if len(media) > 0:
                media_files.add(media[0]['media_url'])
        for media_file in media_files:
            if save_as.endswith(".jpg") or save_as.endswith(".png"):
                wget.download(media_file, save_as)
            else:
                wget.download(media_file, "image.jpg")


async def main():
    t = twitter()
    await t.getInfo(["@factbot1"])
    await t.get_last_tweet_image(["@factbot1"])


if __name__ == "__main__":
    asyncio.run(main())
