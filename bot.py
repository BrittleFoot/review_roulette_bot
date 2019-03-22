# -*- coding: utf-8 -*-

import requests
import telebot
import logging
import os
import re

from telebot import apihelper
from telebot import types
from pprint import pformat, pprint
from random import choice
from telebot_factory import create_async_bot


bot = create_async_bot()
logger = telebot.logger


@bot.message_handler(commands=['choice'])
def brutal_choise_command(message):
    bot.send_chat_action(message.chat.id, 'typing')

    admins = bot.get_chat_administrators(message.chat.id).wait()

    logging.info("Found %s admins" % len(admins))
    users = list(filter(fits_for_review(message.from_user), admins))

    if len(users) < 1:
        bot.reply_to(
            message, "Прости, но некому сделать ревью твоей задачи :с")
        return

    reviewer = choice(users).user

    bagging = "%s, сделай, пожалуйста, ревью для %s." % (
        userlink(reviewer),
        userlink(message.from_user)
    )

    if has_task_param(message):
        query = message.text.split(' ')[-1]
        bagging += " [%s](%s)" % (
            query_to_task(query),
            query_to_task_link(query)
        )

    logger.info("Start sent bagging: " + bagging)
    bot.send_message(message.chat.id, bagging, parse_mode='Markdown').wait()


@bot.inline_handler(lambda query: re.match("(ka-)?\\d+", query.query.strip()))
def choose_task_inline_handler(query):
    q = query.query
    options = [
        article('1',
                query_to_task(q),
                review_me() + " " + query_to_task(q)
                )
    ]
    user = query.from_user
    logger.info("Found %s options for %s (%s)" % (len(options), user.first_name, user.username))
    bot.answer_inline_query(query.id, options)


def has_task_param(message):
    return len(message.text.split(' ')) > 1


def review_me():
    return "/choice@" + bot.me.username


def query_to_task(query: str):
    task = query
    if not task.startswith("ka-"):
        task = "ka-" + task

    return task


def query_to_task_link(query: str):
    return "https://yt.skbkontur.ru/issue/" + query_to_task(query)


def article(id, name, message_content):
    content = types.InputTextMessageContent(message_content)
    return types.InlineQueryResultArticle(id, name, content)


def fits_for_review(author: types.User):
    def _fits_for_review(admin: types.ChatMember):
        if admin.user.is_bot:
            return False

        return author.id != admin.user.id

    return _fits_for_review


def userlink(user):
    return "[%s](tg://user?id=%s)" % (user.first_name, user.id)


def listener(messages):
    for m in messages:
        logger.info("\n" + pformat(m.json))


def main():
    bot.set_update_listener(listener)
    bot.polling()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("^C")
