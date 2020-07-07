FROM python:3.7
WORKDIR /usr/src/app
COPY * ./
COPY cogs/* cogs/
COPY tools/* tools/
COPY tools/twitter/* tools/twitter/
RUN python3 -m pip install \
        -r requirements.txt\
        -U discord.py
RUN python3 tools/downloadPunkt.py
CMD ["python3", "BotHead.py", "false"]