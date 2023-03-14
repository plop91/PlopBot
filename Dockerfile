# Build from basic python image
FROM python:3.8
# Set working dir to the app folder.
WORKDIR /usr/src/app
# Clone git repo
RUN git clone https://github.com/plop91/PlopBot.git
# Set working dir to the git repo
WORKDIR /usr/src/app/PlopBot/
# Create a volume so soundboard and info files can be saved on server, must mount with -v
VOLUME /usr/src/app/PlopBot/soundboard/ /usr/src/app/PlopBot/info/
# Install dependencies.
RUN apt-get update && apt-get install -y ffmpeg
RUN python3 -m pip install -r requirements.txt
# Run Bot
CMD ["python3", "BotHead.py"]
