import os
import telebot
from openai import OpenAI

TOKEN_TELEGRAM = os.getenv("TOKEN_TELEGRAM")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

bot = telebot.TeleBot(TOKEN_TELEGRAM)

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

# Penyimpanan riwayat chat per pengguna
user_histories = {}

# 1. FITUR RESET: Agar Anda bisa membersihkan ingatan bot langsung dari Telegram tanpa ke hosting
@bot.message_handler(commands=['reset', 'clear', 'mulai'])
def reset_conversation(message):
    user_id = message.from_user.id
    if user_id in user_histories:
        del user_histories[user_id]
    bot.reply_to(message, "🧹 Memori bot sudah dibersihkan! Kita mulai percakapan baru yang bersih ya.")

# 2. HANDLER UTAMA DENGAN ATURAN KETAT (PATEN)
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.from_user.id
    user_text = message.text

    # Aturan karakter super tegas (System Prompt) agar AI nurut dan fokus
    strict_system_prompt = (
        "Kamu adalah asisten AI pribadi yang sangat patuh, cerdas, ramah, dan profesional. "
        "ATURAN MUTLAK:\n"
        "1. Wajib selalu menjawab menggunakan Bahasa Indonesia yang baik dan natural.\n"
        "2. Jawab langsung pada inti pertanyaan tanpa bertele-tele atau mengulang kalimat pembuka yang tidak penting.\n"
        "3. Jangan pernah mengarang fakta atau berhalusinasi. Jika tidak tahu, katakan dengan jujur.\n"
        "4. Ingat selalu konteks percakapan sebelumnya dari pengguna."
    )

    if user_id not in user_histories:
        user_histories[user_id] = [
            {"role": "system", "content": strict_system_prompt}
        ]

    # Masukkan pesan user
    user_histories[user_id].append({"role": "user", "content": user_text})

    # Batasi memori maksimal 15 pesan terakhir agar tidak kepenuhan
    if len(user_histories[user_id]) > 16:
        user_histories[user_id] = [user_histories[user_id][0]] + user_histories[user_id][-15:]

    try:
        # Kirim ke DeepSeek dengan temperature rendah (0.3) agar disiplin dan tidak ngawur
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=user_histories[user_id],
            temperature=0.3
        )

        ai_reply = response.choices[0].message.content

        # Simpan jawaban bot ke memori
        user_histories[user_id].append({"role": "assistant", "content": ai_reply})

        bot.reply_to(message, ai_reply)

    except Exception as e:
        # Penanganan error agar bot tidak mati jika ada kendala jaringan sesaat
        bot.reply_to(message, "⚠️ Koneksi sedang sedikit gangguan, silakan ketik ulang pesan Anda ya.")
        print(f"Error tercatat: {str(e)}")

print("Bot Telegram siap berjalan dengan konfigurasi paten...")
bot.infinity_polling()
