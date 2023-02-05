from telegram import ReplyKeyboardMarkup


IDLE, CHAT, EVAL = range(3)

EVAL_KEYBOARD = [[str(i + 1)] for i in range(5)]
EVAL_MARKUP = ReplyKeyboardMarkup(EVAL_KEYBOARD, one_time_keyboard=True)
