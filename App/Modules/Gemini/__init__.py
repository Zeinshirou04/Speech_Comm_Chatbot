import logging
import os
import time
import re

import speech_recognition as sr
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold, BlockedPromptException, BrokenResponseError, IncompleteIterationError, StopCandidateException
import pyttsx3
from pydub import AudioSegment
import pygame

isSpeaking = False
isAnswering = False
isCommunicating = False

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

pygame.mixer.init()

class Gemini_Chatbot:
    """
    Gemini_Chatbot is a simple Class that implement some of Google Gemini Library
    With some added features such as Speech Recognition and also Speech to Speech Commmunication

    Attributes
    ----------
    apiKey : str
        Instance of a string representing the Api Key from the Gemini API.
    modelName : str
        Instance of a string representing the Model Name which can be found in Gemini API Model Lists.
    """

    recognizer = None
    microphone = None
    model = None
    chat = None
    engine = None

    history = []

    def __init__(self, apiKey, modelName):
        logging.basicConfig(
            filename="./App/Logs/app.log",
            encoding="utf-8",
            filemode="a",
            format="{asctime} - {levelname} - {message}",
            style="{",
            datefmt="%Y-%m-%d %H:%M",
            level=logging.INFO
        )
        self.recognizer = sr.Recognizer()
        self.prepModel(apiKey=apiKey, modelName=modelName)
        self.prepTTS()
        self.prepChat()
        self.prepMicrophone()

    def prepModel(self, apiKey, modelName):
        load_dotenv()
        genai.configure(api_key=apiKey)
        self.model = genai.GenerativeModel(model_name=modelName)

    def prepChat(self):
        self.loadPrompt()
        self.chat = self.model.start_chat(history=self.history)
        response = self.chat.send_message(
            ["""Perkenalkan diri kamu!"""],
            generation_config=generation_config,
            safety_settings=safety_settings,
        ).text
        try:
            print(f"Model: {response}")
            logging.info(msg=f'Answer Given: {response}')
            self.textToSpeech(text=response)
        except Exception as e:
            logging.warning(msg=f'Error: {e}')

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

    def prepTTS(self):
        self.engine = pyttsx3.init()
        voices = self.engine.getProperty("voices")
        for voice in voices:
            if "ID-ID" in voice.id or "indonesian" in voice.name:
                self.engine.setProperty("voice", voice.id)
                self.engine.setProperty("rate", 170)
                return 1

    def prepMicrophone(self):
        self.microphone = sr.Microphone()
        self.recognizer = sr.Recognizer()

    def textToSpeech(self, text):
        text = self.removeSymbols(text=text)
        self.engine.save_to_file(text=text, filename="./src/voices/original.wav")
        self.engine.runAndWait()
        self.pitchShift()
        pygame.mixer.music.load("./src/voices/pitched.wav")
        pygame.mixer.music.play()
            
    def speechToText(self, audio):
        try:
            text = self.recognizer.recognize_google(
                audio_data=audio, language="id-ID")
            print(f"User = {text}")
            logging.info(msg=f"Text Received: {text}")
            return text
        except sr.UnknownValueError:
            print("Kesalahan Nilai, tidak dapat dipahami")
            logging.warning(msg="Kesalahan Nilai, tidak dapat dipahami")
            text = "Input tidak dapat diterima, silahkan kembalikan sebuah pesan untuk mengulangi pertanyaan"
            return text
        except sr.RequestError as e:
            print(f"Error: {e}")
            logging.warning(msg=f"Error: {e}")
            text = "Input tidak dapat diterima, silahkan kembalikan sebuah pesan untuk mengulangi pertanyaan"
            return text
        except Exception as e:
            print(e)
            logging.warning(msg=f"Error: {e}")
            text = "Input tidak dapat diterima, silahkan kembalikan sebuah pesan untuk mengulangi pertanyaan"
            return text

    def speechListen(self):
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(
                    source=source, duration=1)
                logging.info(msg="Listening for input...")
                print("Listening for input....")
                audio = self.recognizer.listen(source=source)
                text = self.speechToText(audio=audio)
                return text
        except Exception as e:
            logging.warning(msg=f'Error: {e}')
            print(e)
            text = "Input tidak dapat diterima, silahkan kembalikan sebuah pesan untuk mengulangi pertanyaan"
            return text

    def sendMessage(self, text):
        response = self.chat.send_message(
            text,
            generation_config=generation_config,
            safety_settings=safety_settings,
        ).text
        response = self.removeSymbols(text=response)
        return response

    def removeSymbols(self, text):
        text = text.replace('*', '')
        emoji_pattern = re.compile("["
                                   u"\U0001F600-\U0001F64F"
                                   u"\U0001F300-\U0001F5FF"
                                   u"\U0001F680-\U0001F6FF"
                                   u"\U0001F1E0-\U0001F1FF"
                                   u"\U00002702-\U000027B0"
                                   u"\U000024C2-\U0001F251"
                                   "]+", flags=re.UNICODE)
        text = emoji_pattern.sub(r'', text)
        return text

    def loadPrompt(self, promptPath="./src/prompt.txt"):
        with open(file=promptPath, mode='r') as file:
            prompt = file.read()
            self.prepHistory(prompt=prompt)
    
    def pitchShift(self, fileName="./src/voices/original.wav"):

        sound = AudioSegment.from_file(file=fileName, format="wav")

        # Semakin kecil octaves, suara semakin chipmunk
        octaves = 0.5

        new_sample_rate = int(sound.frame_rate * (1.5**octaves))
        hipitch_sound = sound._spawn(
            sound.raw_data, overrides={"frame_rate": new_sample_rate}
        )
        hipitch_sound = hipitch_sound.set_frame_rate(44100)
        
        try:
            hipitch_sound.export("./src/voices/pitched.wav", format="wav")
        except:
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
            self.resetOutput()
            time.sleep(1)
            hipitch_sound.export("./src/voices/pitched.wav", format="wav")
        
    def resetOutput(self, outputPath = "./src/voices/pitched.wav"):
        if os.path.exists(outputPath):
            os.remove(outputPath)

    def attributeLists(self):
        print(f"Recognizer: {type(self.recognizer)}")
        print(f"Model: {type(self.model)}")
        print(f"Engine: {type(self.engine)}")
        print(f"History: {type(self.history)}")

    def run(self):
        isCommunicating = True
        while isCommunicating:
            try:
                text = self.speechListen()
                response = self.sendMessage(text=text)
                print(f"Response: {response}")
                logging.info(msg=f"Response: {response}")
                self.textToSpeech(text=response)
            except KeyboardInterrupt:
                print("Program Closed")
                logging.warning(msg=f"Program Closed")
                exit()
            except Exception as e:
                print(e)
                logging.warning(msg=f"Error: {e}")
