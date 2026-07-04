import os
import logging
from io import BytesIO
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from PIL import Image, ImageDraw, ImageFont

# Load local environment variables if testing locally
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome! Send /makebanner to generate a personalized profile banner."
    )

async def make_banner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    await context.bot.send_message(chat_id=chat_id, text="🎨 Generating your banner, please wait...")

    # 1. Create a blank banner canvas (800x400 with a dark theme)
    banner = Image.new("RGB", (800, 400), color="#1e1e2e")
    draw = ImageDraw.Draw(banner)

    # 2. Get User's Profile Picture
    user_photos = await context.bot.get_user_profile_photos(user.id, limit=1)
    
    if user_photos.total_count > 0:
        # Get the file ID of the largest photo size available
        file_id = user_photos.photos[0][-1].file_id
        tg_file = await context.bot.get_file(file_id)
        
        # Download photo directly into bytes memory
        photo_bytes = BytesIO()
        await tg_file.download_to_memory(out=photo_bytes)
        photo_bytes.seek(0)
        
        # Open and resize avatar
        avatar = Image.open(photo_bytes).convert("RGBA")
        avatar = avatar.resize((150, 150))
        
        # Paste avatar onto banner canvas
        banner.paste(avatar, (50, 125), avatar if avatar.mode == "RGBA" else None)

    # 3. Draw text using Pillow's default font system
    font = ImageFont.load_default()
    draw.text((230, 170), f"Hello, {user.first_name}!", fill="#cdd6f4", font=font)
    draw.text((230, 210), "Created via Banner Bot", fill="#a6adc8", font=font)

    # 4. Save banner to memory and send back to Telegram
    output_stream = BytesIO()
    banner.save(output_stream, format="PNG")
    output_stream.seek(0)

    await context.bot.send_photo(chat_id=chat_id, photo=output_stream, caption="Here is your custom banner! 🎉")

if __name__ == '__main__':
    if not BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable is missing!")

    # Build the application
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("makebanner", make_banner))
    
    # Run long polling mode for Render Background Worker
    print("Bot is starting up successfully...")
    application.run_polling(drop_pending_updates=True)
