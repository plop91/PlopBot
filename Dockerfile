# Build from basic python image
FROM python:3.7
# Set working dir to the app folder.
WORKDIR /usr/src/app
# Copy all source code into the container
COPY . /usr/src/app/
# Create a volume so soundboard files are saved on server, must mount with -v to the folder you are copying source from
VOLUME ["/usr/src/app/"]
# Install dependencies.
RUN apt-get update && apt-get install -y ffmpeg
RUN python3 -m pip install -r requirements.txt
# Run Bot
CMD ["python3", "BotHead.py"]