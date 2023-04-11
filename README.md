# Trivia Chatbot
This version is created for practicing programming in Python and building a professional portfolio by <a href="https://github.com/jzaev" target="_blank">Yury Zaev</a>. It does not represent any commercial interest and is not a complete solution.

## Features
This is a Telegram chatbot designed to entertain and engage users with trivia questions. It uses OpenAI GPT-4 to translate questions and answer options between English and Russian languages. The main features of this trivia chatbot include:

* Interactive trivia game with multiple-choice questions.

* Questions categorized by difficulty: easy, medium, and hard.

* Support for two languages: English and Russian. Questions and answer options are translated using OpenAI GPT-4, providing an engaging experience for users speaking different languages.

* Real-time score tracking and end-game results summary.

* Simple and intuitive user interface with inline buttons for selecting answers and navigating through the game.

## Getting Started
To use the Trivia Chatbot, you need to have Python installed on your system, and you also need to install the required packages from the requirements.txt file:

Copy code
> pip install -r requirements.txt

Next, you need to create a config.py file with your Telegram bot token and OpenAI API key:

>TELEGRAM_BOT_TOKEN = "your_telegram_bot_token"
>MY_OPEN_AI_KEY = "your_openai_api_key"

Finally, run the main.py script to start the bot:

You can now interact with the Trivia Chatbot through Telegram. Enjoy playing trivia and testing your knowledge!