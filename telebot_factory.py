import os
import telebot
import logging
import requests

from log_config import config
from loggingext import configure_system_logging

from telebot import apihelper
from telebot import types


def create_async_bot():

    if "TG_TOKEN" in os.environ:
        api_key = os.environ["TG_TOKEN"]
    elif (os.path.isfile("token")):
        with open("token") as f:
            api_key = f.read().strip()
    else:
        raise Exception("No token supplied, use TG_TOKEN env var or file named `token`")

    logger = telebot.logger
    configure_system_logging(telebot.logger, config['system'])

    try:
        requests.get("https://api.telegram.org/bot%s/getMe" % api_key)
    except Exception as e:
        logger.error("Cannot connect to t.me (%s)" % e)
        logger.info("Trying to establish TOR socks5 proxy...")
        apihelper.proxy = {'https': 'socks5://127.0.0.1:9150'}

    bot = telebot.AsyncTeleBot(api_key)
    bot.me = bot.get_me().wait().wait()

    return bot
