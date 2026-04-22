import telebot
from telebot import types
from openai import OpenAI
import random
import json
import os

# ===== ПЕРЕМЕННЫЕ =====
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = OpenAI(api_key=OPENAI_API_KEY)

# ===== БАЗА =====
def load_data():
    try:
        with open("data.json", "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open("data.json", "w") as f:
        json.dump(data, f)

data = load_data()
user_history = {}

# ===== XP =====
def add_xp(user_id):
    uid = str(user_id)

    if uid not in data:
        data[uid] = {"xp": 0, "level": 1, "words": []}

    data[uid]["xp"] += 10

    if data[uid]["xp"] >= data[uid]["level"] * 50:
        data[uid]["level"] += 1
        save_data(data)
        return "🎉 Новый уровень!"

    save_data(data)
    return None

# ===== МЕНЮ =====
def menu():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.add("🔤 Слово", "📝 Предложение")
    m.add("📚 Правило", "🎮 Тест")
    m.add("🧠 Мои слова", "📊 Уровень")
    m.add("✍️ Исправить", "🔊 Озвучить")
    return m

# ===== START =====
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id,
    "👋 English AI Bot 🇬🇧🔥\n\nВыбери действие 👇",
    reply_markup=menu())

# ===== КНОПКИ =====
@bot.message_handler(func=lambda m: m.text in [
    "🎮 Тест","🧠 Мои слова","📊 Уровень","✍️ Исправить","🔊 Озвучить"
])
def buttons(message):
    uid = str(message.from_user.id)

    if message.text == "🎮 Тест":
        word = random.choice(["apple","run","happy","school"])
        data.setdefault(uid, {"words":[]})
        data[uid]["test"] = word
        save_data(data)
        bot.send_message(message.chat.id, f"Переведи: {word}")

    elif message.text == "🧠 Мои слова":
        bot.send_message(message.chat.id, str(data.get(uid, {}).get("words", [])))

    elif message.text == "📊 Уровень":
        user = data.get(uid, {"xp":0,"level":1})
        bot.send_message(message.chat.id,
        f"📊 Уровень: {user['level']}\nXP: {user['xp']}")

    elif message.text == "✍️ Исправить":
        bot.send_message(message.chat.id, "Напиши текст")

    elif message.text == "🔊 Озвучить":
        bot.send_message(message.chat.id, "Напиши слово")

# ===== VOICE =====
@bot.message_handler(commands=['voice'])
def voice(message):
    text = message.text.replace("/voice","").strip()

    try:
        speech = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice="alloy",
            input=text
        )

        with open("voice.mp3","wb") as f:
            f.write(speech.read())

        bot.send_voice(message.chat.id, open("voice.mp3","rb"))

    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {e}")

# ===== ЧАТ =====
@bot.message_handler(func=lambda message: True)
def chat(message):
    user_id = message.from_user.id
    text = message.text

    lvl = add_xp(user_id)
    if lvl:
        bot.send_message(message.chat.id, lvl)

    if user_id not in user_history:
        user_history[user_id] = []

    user_history[user_id].append({"role":"user","content":text})

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role":"system","content":
                 "Ты учитель английского.\n"
                 "Слово → перевод + синонимы\n"
                 "Предложение → перевод + объяснение\n"
                 "Исправляй ошибки\n"
                 "Объясняй грамматику\n"}
            ] + user_history[user_id][-10:]
        )

        answer = response.choices[0].message.content
        user_history[user_id].append({"role":"assistant","content":answer})

        bot.send_message(message.chat.id, answer)

    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка: {e}")

bot.polling()
