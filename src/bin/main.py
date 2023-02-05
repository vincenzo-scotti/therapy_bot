import os
import sys
from shutil import copy2
import logging
from datetime import datetime
from argparse import ArgumentParser, Namespace
import yaml

from telegram.ext import Application
from therapy_bot.telegram import init_conversation_handler

from typing import Dict


def main(args: Namespace) -> int:
    """Run the bot."""
    # Initialisation
    # Get date-time
    date_time_session: str = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
    # Read YAML file
    with open(args.config_file_path) as f:
        configs: Dict = yaml.full_load(f)
    # Create session directories
    sessions_dir_path: str = configs['sessions_directory_path']
    if not os.path.exists(sessions_dir_path):
        os.mkdir(sessions_dir_path)
    session_series_dir_path: str = os.path.join(sessions_dir_path, configs['session_series'])
    if not os.path.exists(session_series_dir_path):
        os.mkdir(session_series_dir_path)
    current_session_dir_path = os.path.join(session_series_dir_path, f"{configs['session_id']}_{date_time_session}")
    if not os.path.exists(current_session_dir_path):
        os.mkdir(current_session_dir_path)
    # Create file paths
    if configs.get('log_file', False):
        log_file_path = os.path.join(current_session_dir_path, f"{configs['session_id']}_{date_time_session}.log")
    else:
        log_file_path = None
    configs_dump_path = os.path.join(current_session_dir_path, 'configs.yaml')
    # Init logging
    logging.basicConfig(filename=log_file_path, level=configs['log_level'])
    # Start Logging info
    logging.info(f"{configs['session_series']} Telegram script started")
    logging.info(f"Current session directories created at '{current_session_dir_path}'")
    if log_file_path is not None:
        logging.info(f"Current session log created at '{log_file_path}'")
    # Dump configs
    copy2(args.config_file_path, configs_dump_path)
    logging.info(f"Current session configuration dumped at '{configs_dump_path}'")

    # Start
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(configs['telegram']['token']).arbitrary_callback_data(True).build()
    # Add conversation handler
    application.add_handler(init_conversation_handler(configs))
    # Run the bot until the user presses Ctrl-C you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since start_polling()
    # is non-blocking and will stop the bot gracefully.
    application.run_polling()

    return 0


if __name__ == "__main__":
    # Instantiate argument parser
    args_parser: ArgumentParser = ArgumentParser()
    # Add arguments to parser
    args_parser.add_argument(
        '--config_file_path',
        type=str,
        help="Path to the YAML file containing the configuration for the session."
    )
    # Run experiment
    main(args_parser.parse_args(sys.argv[1:]))
