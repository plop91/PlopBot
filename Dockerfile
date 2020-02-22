FROM python:3.6
RUN python -m pip install \
        numpy\
        -U discord.py
WORKDIR /usr/src/app
COPY * ./
CMD ["python3", "IanBot.py"]