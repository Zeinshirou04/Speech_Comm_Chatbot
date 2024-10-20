import logging as logger
import os

import speech_recognition as sr
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

isSpeaking = False
isAnswering = False

generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 420,
    "response_mime_type": "text/plain",
}

safety_settings = {
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

class Gemini_Chatbot:
    """
    Gemini_Chatbot is a simple Class that implement some of Google Gemini Library
    With some added features such as Speech Recognition and also Speech to Speech Commmunication
    
    Attributes
    ----------
    recognizer : speech_recognition.Recognizer
        Instance of a method from class from speech_recognition 
    model : google.generativeai.generative_models.GenerativeModel
        Instance of a method from class google.generativeai
    chat: google.generativeai.generative_models.ChatSession
        Instance of a method from class google.generativeai
    history : list
        List containing of User Message Content and Model Message Content as Initial Prompt of chat
    """
    
    recognizer = None
    model = None
    chat = None
    
    history = []
    
    def __init__(self):
        logger.basicConfig(
            filename="./App/Logs/app.log",
            encoding="utf-8",
            filemode="a",
            format="{asctime} - {levelname} - {message}",
            style="{",
            datefmt="%Y-%m-%d %H:%M",
            level=logger.DEBUG
        )
        self.recognizer = sr.Recognizer()
        self.prepModel()
        self.prepChat()

        
    def prepChat(self):
        self.loadPrompt()
        self.chat = self.model.start_chat(history=self.history)
        response = self.chat.send_message(
            ["""Perkenalkan diri kamu!"""],
            generation_config=generation_config,
            safety_settings=safety_settings,
        ).text
        print(response)
        logger.debug(msg=f'Model: {response}')
        # self.answer(text=answer)
        
    def prepModel(self):
        load_dotenv()
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel(model_name="gemini-1.5-flash-001")
        
    def prepHistory(self, prompt):
        self.history = [
            {
                "role": "user",
                "parts": [
                    prompt,
                ],
            },
            {
                "role": "model",
                "parts": [
                    "Baik, saya Rosana. Saya siap menerima instruksi. \n",
                ],
            },
        ]
        
    def loadPrompt(self, promptPath = "./src/prompt.txt"):
        with open(file=promptPath, mode='r') as file:
            prompt = file.read()
            self.prepHistory(prompt=prompt)
        
    def run(self):
        print("Program Run")