from tools.twitter.twitterTool import twitter
import asyncio

twit = twitter()

loop = asyncio.get_event_loop()
loop.run_until_complete(twit.get_last_tweet_image("@factbot1", "testfactbot.jpg"))

