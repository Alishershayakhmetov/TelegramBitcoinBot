Telegram-Bitcoin-Bot
============

This telegram bot provide current price of Bitcoin and can set a reminder for the price

Installing
============

You can install this project in the git Bash using this command

    git clone https://github.com/Alishershayakhmetov/TelegramBitcoinBot.git

Before running this project, run this code

    pip install python-telegram-bot requests apscheduler
    
Don't forget to obtain a telegram TOKEN to create your own telegram bot.
Save your TOKEN in env.

Commands
============

To make a command menu for easily call a command, run in BotFather

    /mybots

Select your bot, then Edit Bot -> Edit Commands
And send this message 

    start - Start the bot
    price - Get the current Bitcoin price
    remind - Set a reminder for a period of time
    setTime - Set a time for a reminder
    help - List all available commands
    cancel - cancel the conversation
