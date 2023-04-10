import aiohttp
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ParseMode, Message, CallbackQuery
from dict import translations
import base64


class Trivia:
    def __init__(self, bot):
        self.bot = bot
        self.correct_answers = {}
        self.scores = {}
        self.total_answers = {}
        self.options_per_chat = {}
        self.selected_language = {}

    async def choose_language_handler(self, message):
        chat_id = message.chat.id if isinstance(message, Message) else message.from_user.id
        markup = InlineKeyboardMarkup(row_width=2)
        en_button = InlineKeyboardButton("English", callback_data="language_en")
        ru_button = InlineKeyboardButton("Русский", callback_data="language_ru")
        markup.add(en_button, ru_button)

        await self.bot.send_message(chat_id, "Choose the interface language / Выберите язык интерфейса:",
                                    reply_markup=markup)

    def generate_trivia_button(self, language: str):
        markup = InlineKeyboardMarkup()
        trivia_button = InlineKeyboardButton(translations[language]["get_trivia_question"], callback_data="get_trivia")
        end_game_button = InlineKeyboardButton(translations[language]["end_game"], callback_data="end_game")
        markup.add(trivia_button, end_game_button)
        return markup

    async def fetch_trivia_question(self, difficulty: str):
        url = f"https://opentdb.com/api.php?amount=1&difficulty={difficulty}&type=multiple&encode=base64"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
        return data

    async def format_question(self, data):
        question = base64.b64decode(data["results"][0]["question"]).decode('utf-8')
        correct_answer = base64.b64decode(data["results"][0]["correct_answer"]).decode('utf-8')
        incorrect_answers = [base64.b64decode(ans).decode('utf-8') for ans in data["results"][0]["incorrect_answers"]]

        formatted_question = f"<b>{question}</b>\n\n"
        options = [correct_answer] + incorrect_answers
        options.sort()

        return formatted_question, options, correct_answer

    async def send_response_and_buttons(self, chat_id, text, language):
        markup = self.generate_trivia_button(language)
        await self.bot.send_message(chat_id, text, reply_markup=markup)

    async def start_handler(self, message: Message):
        chat_id = message.chat.id

        if chat_id in self.total_answers:
            self.total_answers[chat_id] = 0
        if chat_id in self.scores:
            self.scores[chat_id] = 0

        await self.choose_language_handler(message)

    async def trivia_handler(self, message: Message, difficulty: str = "easy"):
        data = await self.fetch_trivia_question(difficulty)
        question, options, correct_answer = await self.format_question(data)
        chat_id = message.chat.id
        self.correct_answers[chat_id] = correct_answer
        self.options_per_chat[chat_id] = options  # Save options for this chat
        if chat_id not in self.total_answers:
            self.total_answers[chat_id] = 0
            self.scores[chat_id] = 0  # Initialize scores for the chat

        inline_keyboard = InlineKeyboardMarkup()
        for index, option in enumerate(options, start=1):
            button = InlineKeyboardButton(f"{index}. {option}", callback_data=f"answer_{index}")
            inline_keyboard.add(button)

        # Send the question and options
        await self.bot.send_message(chat_id, question, reply_markup=inline_keyboard, parse_mode=ParseMode.HTML)

    async def end_game_handler(self, callback_query: CallbackQuery):
        message = callback_query.message
        chat_id = message.chat.id
        await self.bot.answer_callback_query(callback_query.id)
        if chat_id in self.scores:
            final_score = self.scores[chat_id]
            total = self.total_answers[chat_id]
            percentage = (final_score / total) * 100
        else:
            percentage = 0

        # Reset the counters
        self.total_answers[chat_id] = 0
        self.scores[chat_id] = 0

        language = self.selected_language.get(chat_id, "en")
        await self.bot.send_message(
            chat_id,
            translations[language]["thanks_for_playing"].format(score=final_score, total=total, percentage=percentage)
        )

        await self.bot.send_message(
            chat_id,
            translations[language]["click_button_to_start_new_test"],
            reply_markup=self.generate_start_button()
        )

    async def answer_callback_handler(self, callback_query: CallbackQuery):
        message = callback_query.message

        if callback_query.data.startswith("answer_"):
            chat_id = message.chat.id

            # Check if chat_id is in correct_answers dictionary
            if chat_id not in self.correct_answers:
                await self.trivia_handler(message)
                return

            user_answer_index = int(callback_query.data.split("_")[1])
            correct_answer = self.correct_answers[chat_id]
            self.total_answers[chat_id] += 1

            options = self.options_per_chat.get(chat_id, [])

            user_answer = options[user_answer_index - 1]

            # Answer the callback query
            await self.bot.answer_callback_query(callback_query.id)

            language = self.selected_language.get(chat_id, "en")

            if user_answer.lower() == correct_answer.lower():
                self.scores[chat_id] += 1
                response_text = translations[language]["correct_well_done_score"].format(
                    score=self.scores[chat_id],
                    total=self.total_answers[chat_id]
                )
            else:
                response_text = translations[language]["sorry_correct_answer_was"].format(
                    correct_answer=correct_answer,
                    score=self.scores[chat_id],
                    total=self.total_answers[chat_id]
                )

            await self.send_response_and_buttons(chat_id, response_text, language)
            await self.send_response_and_buttons(chat_id, translations[language]["continue_or_end"], language)


        elif callback_query.data.startswith("get_trivia"):
            await self.trivia_handler(message)

        elif callback_query.data.startswith("end_game"):
            await self.end_game_handler(callback_query)

        elif callback_query.data.startswith("language_"):
            language = callback_query.data.split("_")[1]
            self.selected_language[message.chat.id] = language
            await self.start_test_handler(message)

        elif callback_query.data.startswith("difficulty_"):
            difficulty = callback_query.data.split("_")[1]
            await self.trivia_handler(message, difficulty)

        elif callback_query.data.startswith("start_test"):
            await self.start_test_handler(message)

    def generate_start_button(self):
        markup = InlineKeyboardMarkup()
        start_test_button = InlineKeyboardButton("Start Test", callback_data="start_test")
        markup.add(start_test_button)
        return markup

    async def start_test_handler(self, message, language=None):
        chat_id = message.chat.id if isinstance(message, Message) else message.from_user.id
        if language is None:
            language = self.selected_language.get(chat_id, "en")
        markup = InlineKeyboardMarkup(row_width=2)
        easy_button = InlineKeyboardButton(translations[language]["easy"], callback_data="difficulty_easy")
        medium_button = InlineKeyboardButton(translations[language]["medium"], callback_data="difficulty_medium")
        hard_button = InlineKeyboardButton(translations[language]["hard"], callback_data="difficulty_hard")
        markup.add(easy_button, medium_button, hard_button)

        await self.bot.send_message(chat_id, translations[language]["choose_difficulty"], reply_markup=markup)

    def generate_language_buttons(self):
        markup = InlineKeyboardMarkup(row_width=2)
        en_button = InlineKeyboardButton("English", callback_data="language_en")
        ru_button = InlineKeyboardButton("Русский", callback_data="language_ru")
        markup.add(en_button, ru_button)
        return markup
