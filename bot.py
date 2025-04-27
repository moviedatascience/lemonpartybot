import discord
import feedparser
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
RSS_FEED_URL = os.getenv("RSS_FEED_URL")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 300))  # Defaults to 5 minutes

# Setup discord client
intents = discord.Intents.default()
client = discord.Client(intents=intents)

# Track the last seen post
last_post_id = None

async def check_feed():
    global last_post_id
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)

    while not client.is_closed():
        feed = feedparser.parse(RSS_FEED_URL)
        if feed.entries:
            latest_entry = feed.entries[0]
            entry_id = latest_entry.get('id') or latest_entry.get('link') or latest_entry.get('title')

            if entry_id != last_post_id:
                last_post_id = entry_id
                title = latest_entry.title
                link = latest_entry.link
                await channel.send(f"🎙️ New Podcast Episode: **{title}**\n{link}")
        
        await asyncio.sleep(CHECK_INTERVAL)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    client.loop.create_task(check_feed())

client.run(TOKEN)
