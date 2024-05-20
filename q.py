
from pyrogram import Client, filters
import requests
from bs4 import BeautifulSoup
import os

# Replace these with your own values
api_id = 12799559
api_hash = '077254e69d93d08357f25bb5f4504580'
bot_token = '1711796263:AAHzaZn9EJFSywo4tF5v9A-2BI05JxeZ15A'
chat_id = '-1001535538162'

# Replace COOKIE with your actual premium cookie
cookie = "browserid=ZSJZrkoom6VqhVpWap0CIMWSPTD8VJ_HkXXm_S_Nimaj9lKn2icGheFFvlo=; lang=en; TSID=8Wn4trW567KlONNBBvUaQRuu5AvSttA7; bid_n=18ea925bf02617e1544207; _ga=GA1.1.1845844341.1712234812; csrfToken=mXmeE1HpWAthbK_ZuCf8EZnA; stripe_mid=dc4f410a-02dc-4300-92f3-64a647379738e9228a; __stripe_sid=0344c2f5-d3c3-4e79-b4a9-e764fb27e346ea76b8; ndus=Yf0LgCeteHui4ArcvQ_fxHXyL_wlmRnoU8UIaC7X; ndut_fmt=BFE9F1D58DC310FADFABD8A959D9EEE27E0E841FE0DEADE8021FCCA6F0F34A1D; _ga_06ZNKL8C2E=GS1.1.1712771968.3.1.1712772144.56.0.0"

app = Client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

@app.on_message(filters.private & filters.regex(r'https://teraboxapp.com/s/'))
async def download_and_send_video(client, message):
    terabox_link = message.text.strip()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',
        'Cookie': cookie,
    }
    response = requests.get(terabox_link, headers=headers)
    
    if response.status_code == 200:
        try:
            soup = BeautifulSoup(response.content, 'html.parser')
            # Example: Find the script containing download info, adjust as necessary
            scripts = soup.find_all('script')
            download_link = None
            for script in scripts:
                if 'download_link' in script.text:
                    download_link = script.text.split('download_link":"')[1].split('"')[0]
                    break
            
            if download_link:
                video_filename = 'video.mp4'
                video_response = requests.get(download_link, headers=headers)
                with open(video_filename, 'wb') as f:
                    f.write(video_response.content)
                await client.send_video(chat_id, video_filename)
                os.remove(video_filename)
            else:
                await message.reply_text("Error: Unable to fetch download link from Terabox.")
        except Exception as e:
            print("Error:", e)
            print("Response content:", response.content)
            await message.reply_text("Error: Unable to fetch video from Terabox link.")
    else:
        await message.reply_text("Error: Unable to fetch video from Terabox link.")

app.run()
