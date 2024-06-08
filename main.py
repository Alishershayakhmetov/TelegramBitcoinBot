import logging
import os

from telegram import Update, ForceReply, Bot
from telegram.ext import Application, CommandHandler, CallbackContext
import requests

TOKEN = os.environ["TOKEN"]

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# Get Bitcoin price
def get_bitcoin_price():
    url = 'https://api.coindesk.com/v1/bpi/currentprice/BTC.json'
    response = requests.get(url)
    data = response.json()
    return data['bpi']['USD']['rate']


# Command handler to start the bot
async def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    await update.message.reply_markdown_v2(
        fr'Hi {user.mention_markdown_v2()}\!',
        reply_markup=ForceReply(selective=True),
    )


# Command handler to get the current Bitcoin price
async def price(update: Update, context: CallbackContext) -> None:
    price = get_bitcoin_price()
    await update.message.reply_text(f'The current price of Bitcoin is ${price}')


# Function to send a reminder
async def send_reminder(context: CallbackContext) -> None:
    job = context.job
    await context.bot.send_message(job.context, text='This is your reminder!')


# Command handler to set a reminder
async def set_timer(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    try:
        due = int(context.args[0])
        if due < 0:
            await update.message.reply_text('Sorry, I can\'t go back to the future!')
            return

        context.job_queue.run_once(send_reminder, due, name=str(chat_id), user_id=chat_id)
        await update.message.reply_text(f'Reminder set for {due} seconds!')
    except (IndexError, ValueError):
        await update.message.reply_text('Usage: /remind <seconds>')


# Error handler
async def error(update: Update, context: CallbackContext) -> None:
    logger.warning('Update "%s" caused error "%s"', update, context.error)


# Main function to start the bot
def main() -> None:
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("remind", set_timer))

    app.add_error_handler(error)

    print("Polling...")
    app.run_polling(poll_interval=3)


if __name__ == '__main__':
    main()