import logging

from aiogram import Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware

from bot_instance import bot  # Импортируйте объект bot
from handlers import start_handler, answer_callback_handler
from trivia import Trivia

logging.basicConfig(level=logging.INFO)

dp = Dispatcher(bot)

dp.middleware.setup(LoggingMiddleware())

trivia_instance = Trivia(bot=bot)  # Создайте экземпляр Trivia

dp.register_message_handler(lambda message: trivia_instance.start_handler(message), commands=["start"])

# dp.register_message_handler(lambda message: start_handler(message, trivia=trivia_instance), commands=["start"])
dp.register_callback_query_handler(lambda query: answer_callback_handler(query, trivia=trivia_instance))

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp)
