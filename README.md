# Lemonparty Podcast Discord Bot

A simple Discord bot that checks a Patreon RSS feed and posts new episodes to a channel.

## Setup

1. Clone the repository.
2. Create a `.env` file with your configuration:
    ```
    DISCORD_TOKEN=your_bot_token
    CHANNEL_ID=your_channel_id
    RSS_FEED_URL=your_rss_feed_url
    CHECK_INTERVAL=300
    ```
3. Install dependencies:
    ```
    pip install -r requirements.txt
    ```
4. Run the bot:
    ```
    python bot.py
    ```

## Deployment

You can deploy this bot to platforms like:
- [Render](https://render.com/)
- [Railway](https://railway.app/)
- [Fly.io](https://fly.io/)
- [Heroku](https://www.heroku.com/)

Make sure to set your environment variables on the platform!

## 🔎 How to Get Your Discord Channel ID

1. Enable Developer Mode in Discord:
   - Open **User Settings** (click the gear icon ⚙️ next to your name).
   - Navigate to **Advanced** under App Settings.
   - Toggle **Developer Mode** to **ON**.

2. Copy the Channel ID:
   - Go to your Discord server.
   - **Right-click** on the text channel where you want the bot to post.
   - Click **Copy Channel ID**.

3. Add the Channel ID to your `.env` file:
   ```dotenv
   CHANNEL_ID=your_channel_id_here




## License
MIT
