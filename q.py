
from pyrogram import Client, filters
import requests
import os

# Replace these with your own values
api_id = 12799559
api_hash = '077254e69d93d08357f25bb5f4504580'
bot_token = '1711796263:AAHzaZn9EJFSywo4tF5v9A-2BI05JxeZ15A'
chat_id = '-1001535538162'

app = Client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

@app.on_message(filters.private & filters.regex(r'https://teraboxapp.com/s/'))
async def download_and_send_video(client, message):
    terabox_link = message.text.strip()
    response = requests.get(terabox_link)
    if response.status_code == 200:
        video_url = response.json()['data']['download_link']
        video_filename = 'video.mp4'
        with open(video_filename, 'wb') as f:
            f.write(requests.get(video_url).content)
        await client.send_video(chat_id, video_filename)
        os.remove(video_filename)
    else:
        await message.reply_text("Error: Unable to fetch video from Terabox link.")

app.run()
