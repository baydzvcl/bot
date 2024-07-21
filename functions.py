from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions
from telegram.ext import ContextTypes, CallbackContext
import json
import requests
from datetime import datetime, timedelta
from telegram.constants import ChatMemberStatus
import psutil
import cpuinfo 
import time

ADMIN_IDS = [6284444968, 6284444968]

def load_config():
    with open('config_store.json', 'r') as file:
        return json.load(file)

CONFIG = load_config()

DEFAULT_STORE_DATA = {
    "time": 60,
    "concurrent": 1,
    "vip": True,
    "bypass_blacklist": False,
    "expire": 30,
    "price": 20
}

bot_start_time = time.time()

async def handle_ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    start_time = time.time()  
    system_info = get_system_info()
    response_time_ms = (time.time() - start_time) * 1000

    uptime_str = format_duration(time.time() - bot_start_time)

    message_text = (
        f"Ping: {response_time_ms:.3f}ms\n"
        f"UpTime: {uptime_str}\n"
        f"Ram:  {system_info['ram_percent']}%\n"
        f"Cpu: {system_info['cpu']['brand_raw']}\n"
    )

    for core_num, usage in system_info['cpu']['usage_per_core'].items():
        message_text += f"Core Cpu {core_num} : {usage}%\n"

    await update.message.reply_text(message_text, parse_mode='HTML')


def get_system_info():
    cpu_info = cpuinfo.get_cpu_info()
    cpu_info_dict = {
        'brand_raw': cpu_info['brand_raw'],
        'num_cores': psutil.cpu_count(logical=False),
        'usage_per_core': {}
    }
    for i, percent in enumerate(psutil.cpu_percent(percpu=True)):
        cpu_info_dict['usage_per_core'][i + 1] = percent

    ram_percent = psutil.virtual_memory().percent

    return {'cpu': cpu_info_dict, 'ram_percent': ram_percent}

def format_duration(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f"{int(h)}h:{int(m)}m:{int(s)}s"

off_bot = False
async def cc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
       return
#    off_bot = False
    global off_bot

    args = context.args
    if not args:
      await update.message.reply_text("<code> Invalid! /status on or off </code>", parse_mode='HTML')
      return
    command = args[0].lower()
    if command == 'off':
       off_bot = True
       await update.message.reply_text("Bot: <code>Đã Tắt</code>", parse_mode='HTML')
    elif command == 'on':
        off_bot = False
        await update.message.reply_text("Bot: <code>Đã Bật</code>", parse_mode='HTML')
    else:
        await update.message.replit_text('invalid command')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  button = [
        [
             InlineKeyboardButton(text="Admin", url="https://t.me/bixd08"),
             InlineKeyboardButton(text="Channel Main", url="https://t.me/hammer_network")
       ]
    ]
  markup = InlineKeyboardMarkup(button)
  welcome_message = (
      "/start - To See All Commands\n"
      "/attack - To Attack Sent\n"
      "/method - To See All Method\n"
      "/plan - To See Your Plans\n"
      "/running - To See The Attack Depart\n"
      "/store - To View My Store\n"
      "/buy - To Buy Plans\n"
      "Note: <code>Don't Spam Attacks</code>\n"
  )
  await update.message.reply_text(welcome_message, parse_mode='HTML', reply_markup=markup)

async def modify_ban_status(update: Update, context: ContextTypes.DEFAULT_TYPE, ban_status: bool) -> None:
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return

    if update.message.reply_to_message:
        target_id = update.message.reply_to_message.from_user.id
    else:
        args = context.args
        if len(args) != 1:
            await update.message.reply_text("Usage:<code> /ban [user_id] or /unban [user_id]</code>", parse_mode='HTML')
            return
        target_id = args[0]

    try:
        with open('users.json', 'r+') as file:
            users = json.load(file)
            if str(target_id) in users:
                users[str(target_id)]['banned'] = ban_status
                file.seek(0)
                json.dump(users, file, indent=4)
                file.truncate()
                action = "banned" if ban_status else "unbanned"
                await update.message.reply_text(f"User <code>{target_id}</code> has been <code>{action}</code>.", parse_mode='HTML')
            else:
                await update.message.reply_text("User ID not found.")
    except Exception as e:
        await update.message.reply_text(f"Error modifying ban status: {e}")

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  await modify_ban_status(update, context, True)

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  await modify_ban_status(update, context, False)

async def blacklist_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  user_id = update.effective_user.id
  if user_id not in ADMIN_IDS:
      return
  args = context.args
  if not args:
      await update.message.reply_text('Usage: /bl [list|rm target|target]\nExample:<code> /bl fbi.gov</code>\nExample:<code> /bl rm fbi.gov</code>',parse_mode="HTML")
      return

  command = args[0].lower()

  if command == 'list':
      await list_blacklist(update)
  elif command == 'rm' and len(args) > 1:
      await remove_from_blacklist(update, args[1])
  elif '.' in command or command.isnumeric():
      await add_to_blacklist(update, command)
  else:
      await update.message.reply_text('Invalid command or missing argument.')

async def list_blacklist(update: Update) -> None:
  with open('blacklist.json', 'r') as file:
      blacklist = json.load(file)
  if blacklist:
      message = "<code>" + "\n".join(blacklist) + "</code>"
  else:
      message = "Blacklist is empty."
  await update.message.reply_text(message,parse_mode="HTML")

async def add_to_blacklist(update: Update, target: str) -> None:
  with open('blacklist.json', 'r+') as file:
      blacklist = json.load(file)
      if target not in blacklist:
          blacklist.append(target)
          file.seek(0)
          json.dump(blacklist, file)
          file.truncate()
          await update.message.reply_text(f"Added <code>{target}</code> to blacklist.",parse_mode="HTML")
      else:
          await update.message.reply_text(f"<code>{target}</code> is already in the blacklist.",parse_mode="HTML")

async def remove_from_blacklist(update: Update, target: str) -> None:
  with open('blacklist.json', 'r+') as file:
      blacklist = json.load(file)
      if target in blacklist:
          blacklist.remove(target)
          file.seek(0)
          json.dump(blacklist, file)
          file.truncate()
          await update.message.reply_text(f"Removed <code>{target}</code> from blacklist.",parse_mode="HTML")
      else:
          await update.message.reply_text(f"<code>{target}</code> is not in the blacklist.",parse_mode="HTML")
      
async def running_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  user_id = update.effective_user.id
  now = datetime.utcnow()

  with open('running.json', 'r') as file:
      running_attacks = json.load(file)

  user_attacks = [details for key, details in running_attacks.items() if details["user_id"] == user_id and datetime.fromisoformat(details["end_time"]) > now]


  if not user_attacks:
      await update.message.reply_text("You have no running attacks.")
      return

  message = ""
  for attack in user_attacks:
      time_left = (datetime.fromisoformat(attack["end_time"]) - now).total_seconds()
      message += f"Attack ID: {attack['attack_id']}\nTarget: {attack['url']}\nPort: {attack['port']}\nTime Left: {int(time_left)}s\nMethod: {attack['method_name']}\nSentTime: {attack['formatted_date']}\n\n"

  await update.message.reply_text(message)

async def method_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  user_id = update.effective_user.id
  

  args = context.args
  if not args:
      #await update.message.reply_text("Usage:<code> /method [add|list|rm] [parameters]</code>",parse_mode='HTML')
      await list_methods(update)
      return

  command = args[0].lower()

  if command == "add":
      if user_id not in ADMIN_IDS:
          return
      await add_method(args[1:], update)
  elif command == "list":
      await list_methods(update)
  elif command == "rm":
      if user_id not in ADMIN_IDS:
          return
      await remove_method(args[1:], update)
  else:
      await update.message.reply_text("Invalid command. Use <code>/method <add|list|rm> [parameters]</code>",parse_mode='HTML')

async def add_method(args, update: Update) -> None:
  if len(args) < 4:
      await update.message.reply_text("/method<b> [ list | add | rm ]",parse_mode='HTML')
      return

  method_name, description, vip_status, layer_str = args[0], " ".join(args[1:-2]), args[-2].lower(), args[-1]

  if vip_status not in ['true', 'false']:
      await update.message.reply_text(" <code>VIP status must be either 'true' or 'false' </code>", parse_mode='HTML')
      return
  if layer_str not in ['4', '7']:
      await update.message.reply_text("<code>Layer must be either '4' or '7'</code>", parse_mode='HTML')
      return
  vip = vip_status == 'true'
  layer = int(layer_str)

  try:
      with open('methods.json', 'r') as file:
          methods = json.load(file)
  except FileNotFoundError:
      methods = []

  if any(method['name'] == method_name for method in methods):
      await update.message.reply_text(f"Method <code>'{method_name}'</code> already exists.", parse_mode='HTML')
      return

  new_method = {
      "name": method_name,
      "description": description,
      "vip": vip,
      "layer": layer
  }

  methods.append(new_method)
  with open('methods.json', 'w') as file:
      json.dump(methods, file, indent=4)

  await update.message.reply_text(f"Method '{method_name}' added successfully.")

async def list_methods(update: Update) -> None:
  try:
      with open('methods.json', 'r') as file:
          methods = json.load(file)
  except FileNotFoundError:
      await update.message.reply_text("No methods available.")
      return

  if not methods:
      await update.message.reply_text("No methods available.")
      return

  layer4_methods = [method for method in methods if method['layer'] == 4]
  layer7_methods = [method for method in methods if method['layer'] == 7]


  method_list_layer4 = "\n\n".join([f"<code>{method['name']}</code> : {method['description']} (Vip: {method['vip']})" for method in layer4_methods])
  method_list_layer7 = "\n\n".join([f"<code>{method['name']}</code> : {method['description']} (Vip: {method['vip']})" for method in layer7_methods])


  message = f"💠 Methods 💠\n\n{method_list_layer7}"

  await update.message.reply_text(message, parse_mode='HTML')

async def remove_method(args, update: Update) -> None:
  if len(args) < 1:
      await update.message.reply_text("Usage:<code> /method rm <name></code>",parse_mode='HTML')
      return

  method_name = args[0]

  try:
      with open('methods.json', 'r') as file:
          methods = json.load(file)
  except FileNotFoundError:
      await update.message.reply_text("No methods file found.")
      return


  method_found = False
  updated_methods = []
  for method in methods:
      if method['name'] == method_name:
          method_found = True
      else:
          updated_methods.append(method)

  if not method_found:
      await update.message.reply_text(f"Method <code>'{method_name}'</code> not found.", parse_mode='HTML')
      return


  with open('methods.json', 'w') as file:
      json.dump(updated_methods, file, indent=4)

  await update.message.reply_text(f"Method <code>'{method_name}'</code> has been removed.", parse_mode='HTML')

async def list_banned(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  user_id = update.effective_user.id
  if user_id not in ADMIN_IDS:
      return

  try:
      with open('users.json', 'r') as file:
          users = json.load(file)

      banned_users = [f"ID: <code>{uid} </code>" for uid, user in users.items() if user.get('banned', False)]

      if not banned_users:
          await update.message.reply_text("No banned users.")
      else:
          banned_users_text = "\n".join(banned_users)
          await update.message.reply_text(f"{banned_users_text}",parse_mode='HTML')

  except FileNotFoundError:
      await update.message.reply_text("User data file not found.")
  except json.JSONDecodeError:
      await update.message.reply_text("Error reading the user data.")


async def plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  user_id = str(update.effective_user.id)  

  try:
      with open('users.json', 'r') as file:
          users = json.load(file)

      user_plan = users.get(user_id)  
      

      if not user_plan:
          await update.message.reply_text("You do not have an active plan.\nType /buy to buy plans.") 
      else:
          expire_datetime = datetime.fromisoformat(user_plan['expire'].replace('Z', '+00:00'))
          formatted_expire = expire_datetime.strftime('%H:%M:%S %d-%m-%Y')
          plan_details = (
              f"<b>Time: </b> <code>{user_plan['time']}s </code>\n"
              f"<b>Concurrent: </b> <code>{user_plan['concurrent']} </code>\n"
              f"<b>VIP: </b> <code>{'true' if user_plan['vip'] else 'false'} </code>\n"
              f"<b>Expires: </b> <code>{formatted_expire} </code>\n"
              f"<b>Banned: </b> <code>{'true' if user_plan['banned'] else 'false'} </code>\n"
              f"<b>Bypass Blacklist: </b> <code>{'true' if user_plan.get('bypass_blacklist', False) else 'false'} </code>\n"
              f"<b>Cooldown: </b> <code>{user_plan['cooldown']}s </code>"
          )
          await update.message.reply_text(f"{plan_details}",parse_mode='HTML')  

  except FileNotFoundError:
      await update.message.reply_text("User data file not found.")  
  except json.JSONDecodeError:
      await update.message.reply_text("Error reading the user data.")  


async def add_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return

    if update.message.reply_to_message:
        target_id = str(update.message.reply_to_message.from_user.id)
        args = [target_id] + context.args
    else:
        args = context.args

    if len(args) != 7:
        await update.message.reply_text("Usage: /add [id] [time] [concurrent] [expire_in_days] [vip] [bypass blacklist] [cooldown_in_seconds]\nExample:<code> /add 5145402317 300 5 60 true false 29</code>", parse_mode='HTML')
        return

    user_id, time, concurrent, expire_in_days, vip, bypass_blacklist, cooldown = args
    try:
        time = int(time)
        concurrent = int(concurrent)
        expire_in_days = int(expire_in_days)
        cooldown = int(cooldown)
        vip = True if vip.lower() == 'true' else False
        bypass_blacklist = True if bypass_blacklist.lower() == 'true' else False

        expire_datetime = datetime.utcnow() + timedelta(days=expire_in_days)
        expire_iso = expire_datetime.isoformat()

        with open('users.json', 'r+') as file:
            users = json.load(file)
            users[user_id] = {
                "time": time,
                "concurrent": concurrent,
                "vip": vip,
                "expire": expire_iso,
                "banned": False,
                "bypass_blacklist": bypass_blacklist,
                "cooldown": cooldown,
                "last_attack": None  
            }
            file.seek(0)
            json.dump(users, file, indent=4)
            file.truncate()

        await update.message.reply_text(f"New Add User <code>{user_id}</code>\n\nTime: {time}\nConcurrent: {concurrent}\nVIP: {vip}\nBypass blacklist: {bypass_blacklist}\nCooldown: {cooldown}s\nExpires_On: {expire_iso}\n\nThanks User: {user_id} For Buy My Plans", parse_mode="HTML")

    except ValueError:
        await update.message.reply_text("Error: Ensure that all parameters are correctly formatted.")



def load_plans():
    with open('plan.json', 'r') as file:
        return json.load(file)['plans']


async def buy(update: Update, context: CallbackContext) -> None:
    plans = load_plans()
    current_plan = plans[0]  


    message = (
        "🛒 Shop\n\n"
        "Welcome To Our Shop\n\n"
        "Please Choose An Option Below !"
    )

    keyboard = [
        [
            InlineKeyboardButton("<<", callback_data=str(plans[-1]['id'])),
            InlineKeyboardButton(f"0/{len(plans)}", callback_data="current"),
            InlineKeyboardButton(">>", callback_data=str(plans[0]['id']))
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(message, reply_markup=reply_markup, parse_mode="HTML")

async def plan_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    if not query:
        return
    await query.answer()
    plans = load_plans()
    plan_id = int(query.data)

    current_index = next((index for index, plan in enumerate(plans) if plan['id'] == plan_id), None)
    next_index = (current_index + 1) % len(plans)
    prev_index = (current_index - 1) % len(plans)


    keyboard = [
        [
            InlineKeyboardButton("<<", callback_data=str(plans[prev_index]['id'])),
            InlineKeyboardButton(f"{current_index + 1}/{len(plans)}", callback_data=str(current_index)),
            InlineKeyboardButton(">>", callback_data=str(plans[next_index]['id']))
        ],
        [
            InlineKeyboardButton("Buy Plan", url="https://t.me/bixd08")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    details = plans[current_index]['details']

    expire_date = datetime.utcnow() + timedelta(days=int(details['Expires']))
    formatted_expire_date = expire_date.strftime("%d/%m/%Y")

    message = (
        f"🛒 Shop\n\n"
        f"Plan: <code>{plans[current_index]['name']}</code>\n\n"
        f"Time: <code>{details['Time']}</code>\n\n"
        f"Concurrent: <code>{details['Concurrent']}</code>\n\n"
        f"VIP: {details['VIP']}\n\n"
        f"Expiration: <code>{details['Expires']} days</code><b> ({formatted_expire_date})</b>\n\n"
        f"Bypass Blacklist: {details['Bypass Blacklist']}\n\n"
        f"Cooldown: <code>{details['Cooldown']}</code>\n\n"
        f"Price: <code>${details['Price']}</code>"
    )

    await query.edit_message_text(text=message, reply_markup=reply_markup,parse_mode="HTML")


async def handle_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    data = query.data

    if data.startswith("store_"):
        await handle_store_callback(update, context)
    elif data.isdigit():
        await plan_callback(update, context)

async def handle_store_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    store_data = context.user_data.get('store_data', DEFAULT_STORE_DATA.copy())

    if query.data == "store_increase_time":
        store_data['time'] += CONFIG['time']['step']
        store_data['price'] += CONFIG['time']['price_per_unit']
    elif query.data == "store_decrease_time":
        if store_data['time'] > CONFIG['time']['step']:
            store_data['time'] -= CONFIG['time']['step']
            store_data['price'] -= CONFIG['time']['price_per_unit'] 
    elif query.data == "store_increase_concurrent":
        store_data['concurrent'] += CONFIG['concurrent']['step']
        store_data['price'] += CONFIG['concurrent']['price_per_unit'] 
    elif query.data == "store_decrease_concurrent":
        if store_data['concurrent'] > C