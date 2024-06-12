import logging
import os
from datetime import datetime

from telegram import Update
from telegram.ext import (
    Application, CommandHandler, CallbackContext, ConversationHandler, MessageHandler, filters
)
import requests

TOKEN = os.environ["TOKEN"]

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
DATE, TIME = range(2)

# Get Bitcoin price
def get_bitcoin_price() -> str:
    url = 'https://api.coindesk.com/v1/bpi/currentprice/BTC.json'
    response = requests.get(url)
    data = response.json()
    return data['bpi']['USD']['rate']

# Command handler to start the bot
async def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    await update.message.reply_markdown_v2(
        fr'Hi {user.mention_markdown_v2()}\!',
    )

# Command handler to get the current Bitcoin price
async def price(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(f'The current price of Bitcoin is ${get_bitcoin_price()}')

# Command handler to list available commands
async def help_command(update: Update, context: CallbackContext) -> None:
    commands = [
        "/start - Start the bot",
        "/price - Get the current Bitcoin price",
        "/remind <seconds> - Set a reminder",
        "/set_time - Set a time for a reminder",
        "/help - List all available commands",
        "/cancel - Cancel the last reminder or conversation"
    ]
    await update.message.reply_text("\n".join(commands))

# Function to send a reminder
async def send_reminder(context: CallbackContext) -> None:
    job = context.job
    await context.bot.send_message(job.chat_id, text=f'The current price of Bitcoin is ${get_bitcoin_price()}')

# Command handler to set a reminder
async def remind(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    try:
        due = int(context.args[0])
        if due < 0:
            await update.message.reply_text('Sorry, I can\'t go back to the future!')
            return

        job = context.job_queue.run_once(send_reminder, due, chat_id=chat_id)
        if 'jobs' not in context.user_data:
            context.user_data['jobs'] = []
        context.user_data['jobs'].append(job)
        await update.message.reply_text(f'Reminder set for {due} seconds!')
    except (IndexError, ValueError):
        await update.message.reply_text('Usage: /remind <seconds>')

# Start the conversation to set a reminder
async def set_time(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Please enter the date for the reminder (YYYY-MM-DD):')
    return DATE

# Handle date input
async def handle_date(update: Update, context: CallbackContext) -> None:
    user_date = update.message.text
    try:
        selected_date = datetime.strptime(user_date, '%Y-%m-%d').date()
        if selected_date < datetime.now().date():
            await update.message.reply_text('The date cannot be in the past. Please enter a future date (YYYY-MM-DD):')
            return DATE

        context.user_data['selected_date'] = selected_date
        await update.message.reply_text('Please enter the time for the reminder (HH:MM, 24-hour format):')
        return TIME
    except ValueError:
        await update.message.reply_text('Invalid date format. Please enter the date in YYYY-MM-DD format:')
        return DATE

# Handle time input
async def handle_time(update: Update, context: CallbackContext) -> None:
    user_time = update.message.text
    try:
        selected_time = datetime.strptime(user_time, '%H:%M').time()
        selected_datetime = datetime.combine(context.user_data['selected_date'], selected_time)

        if selected_datetime < datetime.now():
            await update.message.reply_text(
                'The time cannot be in the past. Please enter a future time (HH:MM, 24-hour format):')
            return TIME

        context.user_data['selected_datetime'] = selected_datetime

        # Schedule the reminder
        delay = (selected_datetime - datetime.now()).total_seconds()
        job = context.job_queue.run_once(send_reminder, delay, chat_id=update.message.chat_id)
        if 'jobs' not in context.user_data:
            context.user_data['jobs'] = []
        context.user_data['jobs'].append(job)
        await update.message.reply_text(f'Reminder set for {selected_datetime.strftime("%Y-%m-%d %H:%M:%S")}')
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text('Invalid time format. Please enter the time in HH:MM format:')
        return TIME

# Cancel the last reminder or conversation
async def cancel(update: Update, context: CallbackContext) -> None:
    jobs = context.user_data.get('jobs', [])
    if jobs:
        job = jobs.pop()
        job.schedule_removal()
        await update.message.reply_text('Reminder cancelled.')
    else:
        await update.message.reply_text('The setting a reminder is not called yet.')
    return ConversationHandler.END

# Error handler
async def error(update: Update, context: CallbackContext) -> None:
    logger.warning('Update "%s" caused error "%s"', update, context.error)

# Main function to start the bot
def main() -> None:
    app = Application.builder().token(TOKEN).build()

    # Add conversation handler with the states DATE and TIME
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('set_time', set_time)],
        states={
            DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_date)],
            TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_time)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("remind", remind))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_error_handler(error)

    print("Polling...")
    app.run_polling(poll_interval=3)

if __name__ == '__main__':
    main()
