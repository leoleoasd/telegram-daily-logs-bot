import logging
import os

import parsedatetime as pdt
from git import Repo
from pytz import timezone
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import config

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="I'm a bot, but only my creator can use it.",
    )


async def post_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if (
        update.effective_chat.type == "private"
        and update.effective_chat.id == config.manager_id
    ):
        repo = Repo(config.working_dir)
        message = update.message
        if message.reply_to_message:
            message = message.reply_to_message
        date = message.date
        text = message.text
        if message.text.startswith("-"):
            message_line_1 = message.text.split("\n")[0][1:]
            date = pdt.Calendar().parseDT(
                message_line_1, tzinfo=timezone("America/New_York")
            )[0]
            text = "\n".join(message.text.split("\n")[1:])
        logging.info(date)
        # make message.date as "yyyy-mm-dd"
        datestr = date.strftime("%Y-%m-%d")
        filename = datestr + ".md"
        if not os.path.exists(config.working_dir / "_daily_log" / filename):
            file = open(config.working_dir / "_daily_log" / filename, "w")
            file.write(
                f"""---
title: {datestr}
---

"""
            )
        else:
            file = open(config.working_dir / "_daily_log" / filename, "a")
        file.write(f"{text}\n\n")
        file.close()
        repo.index.add([str(config.working_dir / "_daily_log" / filename)])
        repo.index.commit(f"daily log from {datestr}")
        # repo.pull(rebase=True)
        repo.git.pull(rebase=True)
        repo.git.push()
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=datestr,
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="I'm a bot, but only my creator can use it.",
        )


if __name__ == "__main__":
    application = ApplicationBuilder().token(config.token).build()

    start_handler = CommandHandler("start", start)
    post_message_handler = MessageHandler(
        filters.TEXT & (~filters.COMMAND), post_message
    )
    application.add_handler(start_handler)
    application.add_handler(post_message_handler)

    application.run_polling()
