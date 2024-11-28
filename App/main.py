import os

from dotenv import load_dotenv
from Modules.Gemini import Gemini_Chatbot
from Modules.GPT import Openai_Chatbot

load_dotenv()

bot = Gemini_Chatbot(apiKey=os.getenv(key="GEMINI_API_KEY"), modelName="gemini-1.5-flash-001")

# bot = Openai_Chatbot(apiKey=os.getenv(key="OPENAI_API_KEY"), modelName="gpt-4o")
bot.run()

# bot.attributeLists()