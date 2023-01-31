import sys
import logging
from datetime import datetime
from configparser import ConfigParser
import ast

from functools import wraps

import threading

import bz2
import pickle

from conversational_agent.eca_agent import ECABot

from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)
from . import EVAL_KEYBOARD, EVAL_MARKUP
from . import TelegramBotStatus

from configparser import NoOptionError, NoSectionError


# Global variables
global dump_file_lock
global conversations_dump_file_path
global conversational_agent
global evaluation_aspects
global authorised_users


def _load_data():
    with bz2.BZ2File(conversations_dump_file_path, 'r') as f:
        data = pickle.load(f)
    return data


def _store_data(data):
    with bz2.BZ2File(conversations_dump_file_path, 'wb') as f:
        pickle.dump(data, f)


def _backup_conversation(conversation_data):
    # Acquire lock on data file
    dump_file_lock.acquire()
    # Read data
    data = _load_data()
    # Add new conversation
    data.append(conversation_data)
    # Overwrite with new data
    _store_data(data)
    # Release lock on data file
    dump_file_lock.release()
    logging.debug("Conversation backup completed with success")


def restricted_access(func):
    @wraps(func)
    def wrapped(update, context, *args, **kwargs):
        global authorised_users
        user_id = update.effective_user.id
        if authorised_users is not None and user_id not in authorised_users:  # Check IDs only of list is provided
            logging.info("Unauthorized access denied for user ID {}".format(user_id))
            return
        else:
            return func(update, context, *args, **kwargs)
    return wrapped


@restricted_access
def start_bot(update: Update, context: CallbackContext) -> int:
    """Start the conversation and ask user for input."""
    update.message.reply_text(
        "Welcome to PoliNLP bot. "
        "Use the command /begin to start a conversation and "
        "/end to end the conversation. "
        "At the end of each conversation you will be asked to rate the conversation."
        "Use the command /start to reset the bot and /stop to stop the bot."
    )
    context.chat_data['conversation'] = []  # TODO check if can save
    context.chat_data['evaluation'] = {}
    context.chat_data['date_time'] = datetime.now()
    context.chat_data['user_id'] = update.message.from_user.id  # TODO check if can save

    return TelegramBotStatus.WAIT


@restricted_access
def start_chatting(update: Update, context: CallbackContext) -> int:
    """Start the conversation and ask user for input."""
    update.message.reply_text(
        "Conversation mode started."
    )
    context.chat_data['conversation'] = []  # TODO check if can save
    context.chat_data['evaluation'] = {}
    context.chat_data['date_time'] = datetime.now()
    context.chat_data['user_id'] = update.message.from_user.id  # TODO check if can save

    return TelegramBotStatus.CHAT


@restricted_access
def get_response(update: Update, context: CallbackContext) -> int:
    """Generate a response message."""
    message = update.message.text
    context.chat_data['conversation'].append(message)
    # TODO see if add a sleep for multipart messages
    response = conversational_agent(context.chat_data['conversation'])
    update.message.reply_text(response)
    context.chat_data['conversation'].append(response)

    return TelegramBotStatus.CHAT


@restricted_access
def stop_chatting(update: Update, context: CallbackContext) -> int:
    """Close conversation mode and start asking scores to user."""
    update.message.reply_text(
        "Conversation mode closed, starting evaluation."
    )
    update.message.reply_text(
        "In a scale from {} to {}, how would you rate the {}?".format(
            '1',
            len(EVAL_KEYBOARD),
            evaluation_aspects[0]
        ),
        reply_markup=EVAL_MARKUP,
    )
    return TelegramBotStatus.EVAL


@restricted_access
def evaluate_agent(update: Update, context: CallbackContext) -> int:
    """Store score provided by user and ask for the next score. If finished close the conversation."""
    score = int(update.message.text)
    context.chat_data['evaluation'][evaluation_aspects[len(context.chat_data['evaluation'])]] = score

    if len(evaluation_aspects) == len(context.chat_data['evaluation']):
        update.message.reply_text(
            "Evaluation completed. "
            "You can start another conversation with the /begin command "
            "or use the /stop command to stop the bot.",
            reply_markup=ReplyKeyboardRemove(),
        )
        _backup_conversation(context.chat_data)
        context.chat_data.clear()
        return TelegramBotStatus.WAIT
    else:
        update.message.reply_text(
            "In a scale from {} to {}, how would you rate the {}?".format(
                '1',
                len(EVAL_KEYBOARD),
                evaluation_aspects[len(context.chat_data['evaluation'])]
            ),
            reply_markup=EVAL_MARKUP,
        )
        return TelegramBotStatus.EVAL


@restricted_access
def stop_bot(update: Update, context: CallbackContext):
    """In case of stop fallback the bot is deactivated."""
    update.message.reply_text(
        "Thanks for using our empathetic conversational agent, see you next time! "
        "Don't forget to give the /start command again."
    )
    return ConversationHandler.END


def init_conversation_handler(configs: ConfigParser, device, paths):
    global dump_file_lock, conversations_dump_file_path, conversational_agent, evaluation_aspects, authorised_users
    # Init model
    conversational_agent = ECABot(
        configs.get('MODEL', 'pretrained'),
        ast.literal_eval(configs.get('MODEL', 'generation_kwargs')),
        configs.getint('MODEL', 'max_context_length'),
        configs.getint('MODEL', 'max_context_tokens'),
        configs.getint('MODEL', 'max_responses'),
        configs.getboolean('MODEL', 'do_sample'),
        device,
        random_seed=configs.getint('GLOBAL', 'random_seed')
    )
    logging.info("Empathetic Conversational Agent instantiated")
    evaluation_aspects = ast.literal_eval(configs.get('EVALUATION', 'aspects'))
    # Create backup file
    conversations_dump_file_path = paths.conversations_dump_file
    _store_data([])
    logging.info("Current session conversations dump file created at {}".format(conversations_dump_file_path))
    # Create backup file lock
    dump_file_lock = threading.Lock()
    logging.info("Current session conversations dump file lock created")
    # Load list of authorised users if any, else do not restrict access
    try:
        authorised_users_file_path = configs.get('RESTRICTIONS', 'authorised_users_file')
        with open(authorised_users_file_path) as f:
            authorised_users = [int(i) for i in f]
        logging.info("Authorised users list loaded")
    except NoOptionError or NoSectionError:
        authorised_users = None
        logging.info("No user IDs list provided, no restriction to bot access will be set")

    # Add conversation handler with the states CHATTING and EVALUATING
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start_bot)],
        states={
            TelegramBotStatus.WAIT: [CommandHandler('begin', start_chatting)],
            TelegramBotStatus.CHAT: [
                CommandHandler('end', stop_chatting),  # End of chat, start of evaluation
                MessageHandler(Filters.text & ~Filters.command, get_response)  # Regular message
            ],
            TelegramBotStatus.EVAL: [MessageHandler(Filters.text, evaluate_agent)]  # Evaluation message
        },
        fallbacks=[CommandHandler('stop', stop_bot)],  # Any other message is ignored
    )
    logging.info("Conversational handler instantiated")

    return conv_handler