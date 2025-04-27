import discord
import feedparser
import asyncio
import os
import logging
from dotenv import load_dotenv
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
RSS_FEED_URL = os.getenv("RSS_FEED_URL")
STATIC_THUMBNAIL_URL = os.getenv("STATIC_THUMBNAIL_URL")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 300))
POST_LOOKBACK = int(os.getenv("POST_LOOKBACK", 500))  # Increase this now since we're searching by title

# Setup discord client
intents = discord.Intents.default()
intents.messages = True
client = discord.Client(intents=intents)

# Set to track known episode titles
posted_titles = set()

# Fetch previously posted episode titles by scanning message content and embeds
async def fetch_posted_titles(channel):
    logging.info(f"Fetching all messages to find already posted episode titles...")
    async for message in channel.history(limit=None, oldest_first=True):
        # Check embeds first
        for embed in message.embeds:
            if embed.title:
                posted_titles.add(embed.title.lower().strip())
        # Fallback to raw message content
        if message.content:
            posted_titles.add(message.content.lower().strip())
    logging.info(f"Completed fetching messages. Found {len(posted_titles)} posted titles.")


# Function to check the feed
async def check_feed():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)

    while not client.is_closed():
        logging.info("Fetching Discord channel history...")
        posted_titles.clear()  # Clear old titles
        await fetch_posted_titles(channel)

        logging.info("Fetching RSS feed...")
        feed = feedparser.parse(RSS_FEED_URL)
        missing_entries = []

        if feed.entries:
            logging.info(f"Found {len(feed.entries)} entries in RSS feed.")
            for entry in reversed(feed.entries):
                title = entry.title.strip()
                if title.lower() not in posted_titles:
                    missing_entries.append(entry)
        else:
            logging.warning("No entries found in RSS feed!")

        if missing_entries:
            logging.info(f"Posting {len(missing_entries)} new episodes to Discord...")
        else:
            logging.info("No new episodes to post.")

        for entry in missing_entries:
            title = entry.title.strip()
            link = entry.link
            published = entry.get('published')
            duration = entry.get('itunes_duration', None)

            # Determine if episode is FREE or PREMIUM
            is_free = False
            if 'tags' in entry:
                tags = [tag['term'].lower() for tag in entry.tags]
                if 'free' in tags or 'public' in tags:
                    is_free = True
            elif "free" in title.lower() or "unlocked" in title.lower():
                is_free = True

            embed_color = discord.Color.green() if is_free else discord.Color.red()

            pub_date = ""
            if published:
                pub_date_obj = datetime(*entry.published_parsed[:6])
                pub_date = pub_date_obj.strftime("%B %d, %Y")

            embed = discord.Embed(
                title=title,
                url=link,
                description="🎙️ A new episode has been released!",
                color=embed_color
            )

            if pub_date:
                embed.add_field(name="📅 Published", value=pub_date, inline=True)
            if duration:
                embed.add_field(name="⏱️ Duration", value=duration, inline=True)

            if STATIC_THUMBNAIL_URL:
                embed.set_thumbnail(url=STATIC_THUMBNAIL_URL)

            await channel.send(embed=embed)
            posted_titles.add(title.lower())  # Track the new title

        logging.info(f"Waiting {CHECK_INTERVAL} seconds before checking again...")
        await asyncio.sleep(CHECK_INTERVAL)

@client.event
async def on_ready():
    logging.info(f'Logged in as {client.user}')
    client.loop.create_task(check_feed())

client.run(TOKEN)
