import logging
from tempfile import NamedTemporaryFile

from functools import wraps

from therapy_bot.chatbot import Chatbot

from telegram import Update, ReplyKeyboardRemove
from telegram.ext import (
    CommandHandler,
    CallbackContext,
    ConversationHandler,
    MessageHandler,
    filters,
)
from .utils import EVAL_MARKUP
from .utils import IDLE, CHAT, EVAL

from typing import Dict


# Global variables
global therabot
global evaluation_aspects
global authorised_users


def restricted_access(func):
    @wraps(func)
    async def wrapped(update, context, *args, **kwargs):
        user_id = update.effective_user.id
        if authorised_users is not None and user_id in authorised_users:  # Check IDs only of list is provided
            return await func(update, context, *args, **kwargs)
        else:
            return await func(update, context, *args, **kwargs)
    return wrapped


@restricted_access
async def start_bot(update: Update, context: CallbackContext) -> int:
    # Start chatbot and give user instructions
    # Init context
    context.chat_data['conversation'] = list()
    context.chat_data['evaluation'] = dict()
    # Give user instructions
    await update.message.reply_text(
        "Welcome to TherapyBot. "
        "Use the command /begin to start a conversation and /end to end the conversation. "
        "At the end of each conversation you will be asked to rate the responses of TherapyBot."
        "Use the command /start to reset the bot and /stop to stop the bot."
    )

    return IDLE


@restricted_access
async def start_chatting(update: Update, context: CallbackContext) -> int:
    # Start conversation
    # Init context
    context.chat_data['conversation'] = list()
    context.chat_data['evaluation'] = dict()
    # Signal conversation start
    await update.message.reply_text(
        "Conversation mode started."
    )

    return CHAT


@restricted_access
async def get_text_response(update: Update, context: CallbackContext) -> int:
    # Generate a written response message to a text message
    # Get message text and append it to the context
    message = update.message.text
    context.chat_data['conversation'].append({'speaker': therabot.user_id, 'text': message})
    try:
        # Generate response using neural chatbot
        response = therabot(context.chat_data['conversation'])
        logging.debug(f'Generated text response. Response text: "{message}", Context: {context.chat_data["conversation"]}')
        context.chat_data['conversation'].append({'speaker': therabot.chatbot_id, 'text': response})
    except ValueError as e:
        logging.error(e)
        await update.message.reply_text(
            "I'm sorry, the chatting service is not enabled in the current configuration. "
            "Stop the chatbot and try again later."
        )

        return CHAT
    # Send response text to user
    await update.message.reply_text(response)

    return CHAT


@restricted_access
async def get_voice_response(update: Update, context: CallbackContext) -> int:
    # Generate a written and spoken response message to a voice message
    # Save voice message into temporary file
    with NamedTemporaryFile(suffix='.ogg') as voice_message:
        voice_file = await update.message.voice.get_file()
        await voice_file.download_to_drive(voice_message.name)
        # Reset file cursor to be sure
        voice_message.seek(0)
        try:
            # Get message text and append it to the context
            message = therabot.transcribe_message(voice_message.name)
            logging.debug(f'Transcribed voice message. Transcripton text: "{message}"')
            context.chat_data['conversation'].append({'speaker': therabot.user_id, 'text': message})
        except ValueError as e:
            logging.error(e)
            # Signal to the user that the transcription module is not avaialble
            await update.message.reply_text(
                "I'm sorry, the transcription service is not enabled in the current configuration. "
                "You're welcome to write a text message."
            )
            return CHAT
    try:
        # Generate response using neural chatbot
        response = therabot(context.chat_data['conversation'])
        logging.debug(f'Generated text response. Response text: "{message}", Context: {context.chat_data["conversation"]}')
        context.chat_data['conversation'].append({'speaker': therabot.chatbot_id, 'text': response})
    except ValueError as e:
        logging.error(e)
        await update.message.reply_text(
            "I'm sorry, the chatting service is not enabled in the current configuration. "
            "Stop the chatbot and try again later."
        )

        return CHAT
    # Synthesise response speech
    # Save voice response into temporary file
    # TODO handle long responses splitting into multiple files (use nltk sentence tokeniser and iterate over result)
    with NamedTemporaryFile(suffix='.ogg') as voice_response:
        try:
            # Synthesise speech
            therabot.read_response(
                voice_response.name,
                context.chat_data['conversation'][-1],
                context=context.chat_data['conversation'][:-1]
            )
            logging.debug(f'Generated voice response.')
            # Reset file cursor to be sure
            voice_response.seek(0)
            # Send response voice message to user
            await update.message.reply_voice(voice_response)
        except ValueError as e:
            logging.error(e)
            pass
    # Send response text to user
    await update.message.reply_text(response)

    return CHAT


@restricted_access
async def stop_chatting(update: Update, context: CallbackContext) -> int:
    # Close conversation mode and start evaluation
    # Send closing message
    # Signal conversation start
    await update.message.reply_text(
        "Conversation mode closed."
    )
    # Do evaluation if required
    if evaluation_aspects is not None and len(evaluation_aspects) > 0:
        await update.message.reply_text(
            "Evaluation mode started."
        )
        # Sent first evaluation message
        await update.message.reply_text(
            f"{evaluation_aspects[0]['description']}\n"
            f"In a scale from 1 to 5, how would you rate the {evaluation_aspects[0]['id']}?",
            reply_markup=EVAL_MARKUP
        )

        return EVAL
    else:
        await update.message.reply_text(
            "You can start another conversation with the /begin command or use the /stop command to stop the bot."
        )
        # TODO add data collection under consent?
        ...
        # Reset context
        context.chat_data['conversation'] = list()
        context.chat_data['evaluation'] = dict()

        return IDLE

@restricted_access
async def evaluate_agent(update: Update, context: CallbackContext) -> int:
    # Do evaluation until all aspects have been rated, then close conversation
    # Gather the latest score
    score = int(update.message.text)
    context.chat_data['evaluation'][evaluation_aspects[len(context.chat_data['evaluation'])]['id']] = score
    # Check if evaluation is finished
    if len(evaluation_aspects) == len(context.chat_data['evaluation']):
        # Send closing messages
        await update.message.reply_text(
            "Evaluation mode closed.",
            reply_markup=ReplyKeyboardRemove(),
        )
        await update.message.reply_text(
            "You can start another conversation with the /begin command or use the /stop command to stop the bot."
        )
        # TODO add data collection under consent?
        ...
        # Reset context
        context.chat_data['conversation'] = list()
        context.chat_data['evaluation'] = dict()

        return IDLE
    else:
        # Send evaluation message
        await update.message.reply_text(
            f"{evaluation_aspects[len(context.chat_data['evaluation'])]['description']}\n"
            f"In a scale from 1 to 5, how would you rate the "
            f"{evaluation_aspects[len(context.chat_data['evaluation'])]['id']}?",
            reply_markup=EVAL_MARKUP
        )

        return EVAL


@restricted_access
async def stop_bot(update: Update, context: CallbackContext):
    # Start chatbot and give user instructions
    # Init context
    context.chat_data['conversation'] = None
    context.chat_data['evaluation'] = None
    # Close communication
    await update.message.reply_text(
        "Thanks for using our TherapyBot, see you next time! "
        "Don't forget to give the /start command again."
    )

    return ConversationHandler.END


def init_conversation_handler(configs: Dict):
    global therabot, evaluation_aspects, authorised_users
    # Init chatbot
    therabot = Chatbot(**configs['chatbot'])
    evaluation_aspects = configs['telegram'].get('evaluation_aspects')
    # Load list of authorised users if any, else do not restrict access
    authorised_users_file_path = configs['telegram'].get('authorised_users_file')
    if authorised_users_file_path is not None:
        with open(authorised_users_file_path) as f:
            authorised_users = {int(i) for i in f}
        logging.debug("Authorised users list loaded")
    else:
        authorised_users = None
        logging.debug("Running without user restrictions")
    # Add conversation handler with the states IDLE, CHAT and EVAL
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start_bot)],
        states={
            IDLE: [CommandHandler('begin', start_chatting)],
            CHAT: [
                CommandHandler('end', stop_chatting),  # End of chat, start of evaluation
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_text_response),  # Regular message
                MessageHandler(filters.VOICE & ~filters.COMMAND, get_voice_response)  # Voice message
            ],
            EVAL: [MessageHandler(filters.TEXT, evaluate_agent)]  # Evaluation message
        },
        fallbacks=[CommandHandler('stop', stop_bot)],  # Any other message is ignored
    )
    logging.info("Conversational handler instantiated")

    return conv_handler
