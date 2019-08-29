import sys, pid, os

NAME = 'review_roulette_bot'

sys.path.append(NAME)
os.environ["TG_TOKEN"] = "..."


def main():
    with pid.PidFile(NAME):
        import bot
        bot.main()

if __name__ == '__main__':
    main()
