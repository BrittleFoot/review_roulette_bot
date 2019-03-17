import telebot
import logging

from telebot import apihelper
from telebot import types
from pprint import pformat, pprint
from random import choice

logger = telebot.logger
telebot.logger.setLevel(logging.INFO)


with open("api_key") as f:
    api_key = f.read().strip()

try:
    bot = telebot.AsyncTeleBot(api_key)
except Exception:
    logger.Error("Cannot connect to t.me, trying tor socks5 proxy...")
    apihelper.proxy = {'https': 'socks5://127.0.0.1:9150'}
    bot = telebot.AsyncTeleBot(api_key)


@bot.message_handler(commands=['choice'])
def query_text(message):
    bot.send_chat_action(message.chat.id, 'typing')

    admins = bot.get_chat_administrators(message.chat.id).wait()

    logging.info("Found %s admins" % len(admins))
    users = list(filter(fits_for_review(message.from_user), admins))

    if len(users) < 1:
        bot.reply_to(
            message, "Прости, но некому сделать ревью твоей задачи :с")
        return

    reviewer = choice(users).user

    bagging = "%s, please сделай ревью для %s" % (
        pretty_name(reviewer),
        pretty_name(message.from_user)
    )

    logger.info("Start sent bagging: " + bagging)
    bot.send_message(message.chat.id, bagging, parse_mode='Markdown')


def fits_for_review(author: types.User):
    def _fits_for_review2(admin: types.ChatMember):
        if admin.user.is_bot:
            return False

        return author.id != admin.user.id

    return _fits_for_review2


def pretty_name(user):
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
