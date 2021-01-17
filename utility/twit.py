from tweepy import OAuthHandler
from tweepy import API
from utility.tools import readJson
import wget


class twit:
    def __init__(self):
        self.info = readJson("utility/twittertoken.json")

        self.auth = OAuthHandler(self.info["apikey"], self.info["apisecret"])
        self.auth.set_access_token(self.info["accesstoken"], self.info["accesstokensecret"])
        self.auth_api = API(self.auth)

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
