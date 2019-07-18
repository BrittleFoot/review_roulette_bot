# -*- coding: utf-8 -*-

import requests
import telebot
import logging
import os
import re

from telebot import apihelper
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from pprint import pformat, pprint
from random import choice
from collections import namedtuple
from telebot_factory import create_async_bot


bot = create_async_bot()
logger = telebot.logger


TASK_PATTERN = re.compile(r"[Kk][Aa]-\d+")


SORRY_NO_PEOPLE = "Прости, но некому сделать ревью твоей задачи :с"
OK = ["🆗", "👌", "✅"]
NO = ["❌", "⛔", "🙅‍"]
ACCEPTED = ["⛏", "🌈", "🔥", "🎊", "🎉"]
DECLINED = "Ok, maybe later ^-^ Stay tuned!"
NOT_FOR_YOU = [
    "Keep calm. It is not for you.",
    "Not today, lad!", "One day you'll get lucky"
]
PLZ_REVIEW = "%s, сделай, пожалуйста, ревью для %s."
NOT_IMPLEMENTED = "Not Implemented"
COOL = "Cool, yeah?"
GOOD_WORD = ["charity", "work", "kindness", "power"]
THANKS = "Thanks you for your %s!"
NEED_REVIEW = "Hужно ревью."


def nofall_log_errors(func):
    def catch(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as e:
            logger.error(e)
            print("\nERROR:\n")
            print(e)
            print()

    catch.__name__ += '.' + func.__name__
    return catch


Command = namedtuple("Command", ["command", "text"])


def parse_command(message):
    words = message.split(' ', maxsplit=1)
    words.append("")
    return Command(words[0], words[1])


def gen_yn_markup(user_id):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton(choice(OK), callback_data="yn_yes_" + str(user_id)),
        InlineKeyboardButton(choice(NO), callback_data="yn_no_" + str(user_id))
    )
    return markup

def gen_ask_markup():
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(
        InlineKeyboardButton("👩🏻‍🔧 Я проведу ревью 👨🏻‍🔧", callback_data="ask_agree"),
    )
    return markup


def gen_result_markup(reviewer_accepted, reviewer):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1

    if reviewer_accepted:
        e = choice(ACCEPTED)
        accepted_msg = e + " " + reviewer.first_name + " accepted " + e
        markup.add(InlineKeyboardButton(accepted_msg, callback_data="y_accepted"))
        return markup

    declined_msg = reviewer.first_name + " declined. Reroll? 🎲"
    markup.add(InlineKeyboardButton(declined_msg, callback_data="n_reroll"))
    return markup


def yes_no_callback(call):
    if not call.data.endswith(str(call.from_user.id)):
        bot.answer_callback_query(call.id, choice(NOT_FOR_YOU))
        return

    is_yes = call.data.startswith("yn_yes")
    is_no = call.data.startswith("yn_no")

    if is_yes:
        response = THANKS % choice(GOOD_WORD)

    elif is_no:
        response = DECLINED

    bot.answer_callback_query(call.id, response)

    bot.edit_message_reply_markup(
        call.message.chat.id,
        call.message.message_id,
        reply_markup=gen_result_markup(is_yes, call.from_user)
    )


def ask_callback(call):

    if call.data == "ask_agree":
        response = THANKS % choice(GOOD_WORD)

        bot.answer_callback_query(call.id, response)

        bot.edit_message_reply_markup(
            call.message.chat.id,
            call.message.message_id,
            reply_markup=gen_result_markup(True, call.from_user)
        )
    


@bot.callback_query_handler(func=lambda call: True)
@nofall_log_errors
def callback_query(call):

    if call.data.startswith("yn"):
        return yes_no_callback(call)

    if call.data.startswith("ask"):
        return ask_callback(call)

    if call.data == "n_reroll":
        bot.answer_callback_query(call.id, NOT_IMPLEMENTED)

    if call.data == "y_accepted":
        bot.answer_callback_query(call.id, COOL)


@bot.message_handler(commands=['ask'])
@nofall_log_errors
def ask_review(message):
    bot.send_chat_action(message.chat.id, 'typing')

    asking = NEED_REVIEW + " " + make_links(parse_command(message.text).text)

    logger.info("sent asking: " + asking)

    options = {
        "parse_mode": "Markdown",
        "reply_markup": gen_ask_markup()
    }

    bot.send_message(message.chat.id, asking, **options)


@bot.message_handler(commands=['choice'])
@nofall_log_errors
def brutal_choise_command(message):
    bot.send_chat_action(message.chat.id, 'typing')

    admins = bot.get_chat_administrators(message.chat.id).wait()

    logging.info("Found %s administrators" % len(admins))
    users = list(filter(fits_for_review(message.from_user), admins))

    if len(users) < 1:
        bot.reply_to(message, SORRY_NO_PEOPLE)
        return

    reviewer = choice(users).user

    bagging = PLZ_REVIEW % (userlink(reviewer), userlink(message.from_user))
    bagging += " " + make_links(parse_command(message.text).text)

    logger.info("sent bagging: " + bagging)

    options = {
        "parse_mode": "Markdown",
        "reply_markup": gen_yn_markup(reviewer.id)
    }

    bot.send_message(message.chat.id, bagging, **options)


@bot.inline_handler(lambda query: re.match("(ka-)?\\d+", query.query.strip()))
@nofall_log_errors
def choose_task_inline_handler(query):
    q = query.query
    task = query_to_task(q)

    command = " ".join(review_me(), task)
    options = [article('1', task, command)]

    user = query.from_user

    logger.info("Found %s options for %s (%s)" %
                (len(options), user.first_name, user.username))

    bot.answer_inline_query(query.id, options)


def has_task_param(message):
    words = message.text.split(' ')
    return len(words) > 1 and words[1].startswith('ka-')


def review_me():
    # if more than one `choice` command handler in chat use
    # return "/choice@" + bot.me.username
    return "/choice"


def make_links(text):
    replacement = r"[\g<0>](https://yt.skbkontur.ru/issue/\g<0>)"
    return TASK_PATTERN.sub(replacement, text)


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
