FROM python:3.7
WORKDIR /usr/src/app
COPY * ./
COPY cogs/* cogs/
COPY tools/* tools/
COPY tools/twitter/* tools/twitter/
RUN apt-get update && apt-get install -y ffmpeg
RUN python3 -m pip install \
        -r requirements.txt\
        -U discord.py youtube_dl
CMD ["python3", "BotHead.py", "false"]