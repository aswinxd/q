import logging
import requests
from pymongo import MongoClient
from pyrogram import Client, filters
from pyrogram.types import Message, Poll
from apscheduler.schedulers.background import BackgroundScheduler

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# MongoDB connection setup
client = MongoClient("mongodb+srv://test:test@cluster0.q9llhnj.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client['quiz_bot']
chat_jobs_collection = db['chat_jobs']
user_scores_collection = db['user_scores']

# Quiz API URL (example)
QUIZ_API_URL = "https://opentdb.com/api.php?amount=1&type=multiple"

# Create a scheduler to handle periodic tasks
scheduler = BackgroundScheduler()

# Define the bot client
app = Client("quiz_bot", api_id="12799559", api_hash="077254e69d93d08357f25bb5f4504580", bot_token="1711796263:AAHzaZn9EJFSywo4tF5v9A-2BI05JxeZ15A")

def fetch_quiz_question():
    """Fetch a quiz question from the API."""
    response = requests.get(QUIZ_API_URL)
    data = response.json()
    question = data['results'][0]
    return question
    
#@app.on_raw_update()
#async
async def send_quiz_question(client, chat_id):
    """Send a quiz question to the chat."""
    question_data = fetch_quiz_question()
    question = question_data['question']
    options = question_data['incorrect_answers'] + [question_data['correct_answer']]
    poll = await client.send_poll(
        chat_id,
        question,
        options,
        is_anonymous=False,
        type='quiz',
        correct_option_id=options.index(question_data['correct_answer'])
    )
    client.poll_data[poll.poll.id] = {
        "chat_id": chat_id,
        "correct_option_id": options.index(question_data['correct_answer'])
    }
def start_quiz_job(client, chat_id, interval=10):
    """Start a job to send quiz questions every 'interval' minutes."""
    if chat_id in client.chat_jobs:
        client.chat_jobs[chat_id].remove()
    job = scheduler.add_job(send_quiz_question, 'interval', minutes=interval, args=[client, chat_id])
    client.chat_jobs[chat_id] = job

    # Save the job to MongoDB
    chat_jobs_collection.update_one(
        {"chat_id": chat_id},
        {"$set": {"chat_id": chat_id, "interval": interval}},
        upsert=True
    )


@app.on_message(filters.command("start"))
async def start(client, message: Message):
    """Send a message when the command /start is issued."""
    await message.reply("Hi! I will send you quiz questions every 10 minutes.")
    start_quiz_job(client, message.chat.id)

@app.on_message(filters.new_chat_members)
async def handle_new_chat_member(client, message: Message):
    """Handle new chat members."""
    start_quiz_job(client, message.chat.id)

@app.on_message(filters.command("setinterval"))
async def set_interval(client, message: Message):
    """Set custom interval for quiz questions."""
    try:
        interval = int(message.command[1])
        chat_id = message.chat.id
        start_quiz_job(client, chat_id, interval)
        await message.reply(f"Quiz interval set to {interval} minutes.")
    except (IndexError, ValueError):
        await message.reply("Usage: /setinterval <minutes>")

@app.on_message(filters.command("leaderboard"))
async def leaderboard(client, message: Message):
    """Display the leaderboard."""
    chat_id = message.chat.id
    scores = user_scores_collection.find_one({"chat_id": chat_id})
    if not scores or not scores.get('scores'):
        await message.reply("No scores yet.")
        return

    leaderboard_text = "\n".join([f"{user}: {score}" for user, score in sorted(scores['scores'].items(), key=lambda item: item[1], reverse=True)])
    await message.reply(f"Leaderboard:\n{leaderboard_text}")

 def handle_raw_update(client, update, users, chats):
    if update._ == "UpdatePollAnswer":
        poll_answer = update.poll_answer
        poll_id = poll_answer.poll_id
        selected_option = poll_answer.option_ids[0]
        user_id = poll_answer.user_id

        if poll_id in client.poll_data:
            chat_id = client.poll_data[poll_id]['chat_id']
            correct_option_id = client.poll_data[poll_id]['correct_option_id']

            if selected_option == correct_option_id:
                user_scores_collection.update_one(
                    {"chat_id": chat_id},
                    {"$inc": {f"scores.{user_id}": 1}},
                    upsert=True
    )
                
@app.on_message(filters.command("feedback"))
async def send_feedback(client, message: Message):
    """Handle feedback from users."""
    feedback_message = " ".join(message.command[1:])
    if feedback_message:
        await client.send_message(-1001535538162, f"Feedback from {message.from_user.id}:\n{feedback_message}")
        await message.reply("Thank you for your feedback!")
    else:
        await message.reply("Usage: /feedback <message>")

def load_chat_jobs(client):
    """Load chat jobs from MongoDB on startup."""
    for job in chat_jobs_collection.find():
        start_quiz_job(client, job['chat_id'], job['interval'])

# Set up job data structures
Client.poll_data = {}
Client.chat_jobs = {}

if __name__ == '__main__':
    # Start the scheduler
    scheduler.start()
    # Load existing chat jobs
    load_chat_jobs(app)
    # Start the bot
    app.run()
