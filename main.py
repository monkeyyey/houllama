import os
import ollama
import telebot
from telebot.types import BotCommand
from datetime import datetime

# Telegram Bot API token
api_token = "MASKED_FOR_PRIVACY"
bot = telebot.TeleBot(api_token)

# CONSTANTS
LOG_FILE_IMAGE = "logging\\log_image_requests.txt"
LOG_FILE_TEXT = "logging\\log_text_requests.txt"
IMAGE_NUMBER = "logging\\image_number.txt"
IMAGE_DIRECTORY = "logging\\images"


# Set the bot commands menu
def set_bot_commands():
    commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("about", "Specifications and Limitations")
    ]
    bot.set_my_commands(commands)


# Function to log user requests to a file
def log_request(user_full_name, username, message, request_type):
    if request_type == 'text':
        with open(LOG_FILE_TEXT, "a") as file:
            log_entry = f"{
                datetime.now()} - {user_full_name} (@{username}): {message}\n"
            file.write(log_entry)

    if request_type == 'image':
        with open(LOG_FILE_IMAGE, "a") as file:
            log_entry = f"{
                datetime.now()} - {user_full_name} (@{username}): {message}\n"
            file.write(log_entry)


# Get current image number
def get_image_number():
    # Read the current value from the file
    with open(IMAGE_NUMBER, 'r') as file:
        number = file.read().strip()

    # Convert to an integer, increment, and format as 4 digits
    incremented_number = int(number) + 1
    formatted_number = f"{incremented_number:04d}"

    # Write the new value back to the file
    with open(IMAGE_NUMBER, 'w') as file:
        file.write(formatted_number)

    return number


# Function to process text input with Ollama
def ollama_request(msg):
    try:
        response = ollama.chat(
            model='llava',
            messages=[{
                'role': 'user',
                'content': msg,
            }]
        )
        return response['message']['content']
    except Exception as e:
        print(f"[-] Error in Ollama request: {e}")
        return "I'm sorry, I encountered an issue processing your request."


# Function to process image input with Ollama
def ollama_request_img(msg, image_path):
    try:
        response = ollama.chat(
            model='llava',
            messages=[{
                'role': 'user',
                'content': msg,
                'images': [image_path]
            }]
        )
        return response['message']['content']
    except Exception as e:
        print(f"[-] Error in Ollama request: {e}")
        return "I'm sorry, I encountered an issue processing your request."


# Handler for the /start command
@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, "HOULLAMA is a Non-Profit project, but if you would like to sponsor my next meal, send any amount to 93206190.\n\nI am Houllama2.0! What can I help you with?")


# Handler for the /about command
@bot.message_handler(commands=['about'])
def welcome(message):
    bot.reply_to(message, "About HOULLAMA2.0\n\nHOULLAMA2.0 is based on LLaVA. LLaVA is a novel end-to-end trained large multimodal model that combines a vision encoder and Vicuna for general-purpose visual and language understanding.\n\nLLaVA Version: 1.6\n\nParameters: 7.24 Billion\n\nLimitations: Can only handle one image")


# Handler to reject all non-text and non-image inputs
@bot.message_handler(content_types=['document', 'video', 'audio', 'sticker'])
def handle_non_image(message):
    bot.reply_to(message, "Only images are allowed. Please send a single image.\n\n*Make sure to choose the option 'Compress Image' when sending.")


# Handler for all user photo prompts
@bot.message_handler(content_types=['photo'])
def get_message(message):

    if hasattr(message, "media_group_id") and message.media_group_id:
        bot.reply_to(
            message, "Please send only one image at a time, not an album.")
        return

    user_full_name = f"{message.from_user.first_name} {
        message.from_user.last_name or ''}".strip()
    username = message.from_user.username or "Unknown_User"

    # Get the highest resolution of the image
    file_id = message.photo[-1].file_id  # Largest size is the last in the list
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    # Save the image locally with a unique name
    filename = f"{get_image_number()}_{
        datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    filepath = os.path.join(IMAGE_DIRECTORY, filename)
    with open(filepath, "wb") as image_file:
        image_file.write(downloaded_file)

    # Log the event
    caption = message.caption or "No caption provided."

    log_request(user_full_name, username,
                f"Image - {filename}, Caption - {caption}", 'image')
    print(f"[+] Request from {
          user_full_name} (@{username}): Image - {filename}, Caption - {caption}")

    try:
        response = ollama_request_img(caption, filepath)
        print(f'[+] {response}')
        bot.reply_to(message, response)
    except Exception as e:
        print(f"[-] Error in get_message: {e}")
        bot.reply_to(message, "An error occurred. Please try again later.")


# Handler for all user text prompts
@bot.message_handler(content_types=['text'])
def get_message(message):
    user_message = message.text
    user_full_name = f"{message.from_user.first_name} {
        message.from_user.last_name or ''}".strip()
    username = message.from_user.username or "Unknown User"
    log_request(user_full_name, username, user_message, 'text')

    # Log the user and their question
    print(f"[+] Request from {user_full_name} (@{username}): {user_message}")

    try:
        response = ollama_request(user_message)
        print(f'[+] {response}')
        bot.reply_to(message, response)
    except Exception as e:
        print(f"[-] Error in get_message: {e}")
        bot.reply_to(message, "An error occurred. Please try again later.")


# Start polling for messages
if __name__ == "__main__":
    print("[+] Bot started...")
    set_bot_commands()
    bot.polling()
