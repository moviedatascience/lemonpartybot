import discord
import feedparser
import asyncio
import os
import logging
from dotenv import load_dotenv
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 300))
STATIC_THUMBNAIL_URL = os.getenv("STATIC_THUMBNAIL_URL")

def format_duration(duration):
    try:
        # Handle raw seconds (int or string of int)
        total_seconds = int(duration)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        if hours > 0:
            return f"{hours}:{minutes:02}:{seconds:02}"
        else:
            return f"{minutes}:{seconds:02}"
    except:
        # Fallback to raw value (already formatted)
        return duration

# Channel/feed mappings
FEEDS = [
    {
        "name": "Private Feed",
        "url": os.getenv("RSS_FEED_URL_PRIVATE"),
        "channel_id": int(os.getenv("CHANNEL_ID_PRIVATE")),
        "posted_titles": set()
    },
    {
        "name": "Public Feed",
        "url": os.getenv("RSS_FEED_URL_PUBLIC"),
        "channel_id": int(os.getenv("CHANNEL_ID_PUBLIC")),
        "posted_titles": set()
    }
]

intents = discord.Intents.default()
intents.messages = True
client = discord.Client(intents=intents)

# Fetch titles from a given channel
async def fetch_posted_titles(channel, feed_name):
    logging.info(f"[{feed_name}] Fetching all messages from channel {channel.name}...")
    titles = set()
    async for message in channel.history(limit=None, oldest_first=True):
        for embed in message.embeds:
            if embed.title:
                titles.add(embed.title.lower().strip())
        if message.content:
            titles.add(message.content.lower().strip())
    logging.info(f"[{feed_name}] Found {len(titles)} previously posted titles.")
    return titles

# Check and post updates for a single feed
async def check_feed(feed, channel):
    logging.info(f"[{feed['name']}] Fetching RSS feed...")
    feed_data = feedparser.parse(feed["url"])
    missing_entries = []
    skipped_count = 0

    if feed_data.entries:
        for entry in reversed(feed_data.entries):
            title = entry.get("title", "").strip()
            if not title:
                logging.warning(f"[{feed['name']}] Skipping entry with missing title.")
                skipped_count += 1
                continue
            if title.lower() not in feed["posted_titles"]:
                missing_entries.append(entry)
    else:
        logging.warning(f"[{feed['name']}] No entries found!")

    if missing_entries:
        logging.info(f"[{feed['name']}] Posting {len(missing_entries)} new episodes...")
        for entry in missing_entries:
            posted = await post_entry(entry, channel, feed)
            if not posted:
                skipped_count += 1
    else:
        logging.info(f"[{feed['name']}] No new episodes to post.")

    if skipped_count > 0:
        logging.info(f"[{feed['name']}] Skipped {skipped_count} entries due to missing fields.")

# Post an embed for an episode
async def post_entry(entry, channel, feed):
    title = entry.get("title", "").strip()
    if not title:
        logging.warning(f"[{feed['name']}] Skipping entry with no title.")
        return False

    # Try to get direct link first
    link = entry.get("link")

    # If 'link' is missing, fall back to first 'href' in entry.links
    if not link and "links" in entry:
        for l in entry.links:
            if isinstance(l, dict) and "href" in l:
                link = l["href"]
                break

    if not link:
        logging.warning(f"[{feed['name']}] Skipping '{title}' — no usable link.")
        return False

    published = entry.get("published", None)
    duration = entry.get("itunes_duration", None)

    is_free = "public" in feed["name"].lower() or "free" in title.lower()
    embed_color = discord.Color.green() if is_free else discord.Color.red()

    pub_date = ""
    if published and entry.get("published_parsed"):
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
        embed.add_field(name="⏱️ Duration", value=format_duration(duration), inline=True)

    if STATIC_THUMBNAIL_URL:
        embed.set_thumbnail(url=STATIC_THUMBNAIL_URL)

    try:
        await channel.send(embed=embed)
        feed["posted_titles"].add(title.lower())
        return True
    except Exception as e:
        logging.error(f"[{feed['name']}] Failed to post '{title}': {e}")
        return False


# Main loop
async def monitor_feeds():
    await client.wait_until_ready()

    while not client.is_closed():
        for feed in FEEDS:
            channel = client.get_channel(feed["channel_id"])
            feed["posted_titles"] = await fetch_posted_titles(channel, feed["name"])
            await check_feed(feed, channel)

        logging.info(f"Waiting {CHECK_INTERVAL} seconds before next check...\n")
        await asyncio.sleep(CHECK_INTERVAL)

@client.event
async def on_ready():
    logging.info(f'Logged in as {client.user}')
    client.loop.create_task(monitor_feeds())

client.run(TOKEN)
