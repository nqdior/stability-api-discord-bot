# Stability AI Japan - Discord BOT XL
Here you can find the source code for my Discord Bot Tutorial. For this tutorial series I use [Pycord](https://github.com/Pycord-Development/pycord). 
This is a Python library based on [discord.py](https://github.com/Rapptz/discord.py) which we use to access the Discord API.

## Setup
1. create a bot in the [Discord Developer Portal](https://discord.com/developers/applications/)
2. create an `.env` file in which you insert the bot token
```
DISCORD_BOT_TOKEN="123456789abcde"
STABILITY_API_KEY="123456789abcde"
```
3. install the Python packages from the `requirements.txt` file
```
python -m pip install -r requirements.txt
```

4. awake main.py
```
python .\main.py
```

## Info
- The [`main.py`](https://github.com/tibue99/tutorial-bot/blob/main/Template/main.py) file is the same for most episodes of the tutorial, so most folders only contain the cog file.
- In the [`Template`](https://github.com/tibue99/tutorial-bot/tree/main/Template) folder you will find the [`main.py`](https://github.com/tibue99/tutorial-bot/blob/main/Template/main.py) file and a template for the basic code structure of the bot.
- In tutorials I will often start with this template so that I don't repeat the basics in every episode.