import os

from dotenv import load_dotenv
from Modules.Gemini import Gemini_Chatbot

load_dotenv()
bot = Gemini_Chatbot(apiKey=os.getenv(key="GEMINI_API_KEY"), modelName="gemini-1.5-flash-001")
bot.run()
# bot.attributeLists()  