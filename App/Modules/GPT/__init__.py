import logging
import os
import time
import re

import speech_recognition as sr
from dotenv import load_dotenv
import google.generativeai as genai
import pyttsx3
from pydub import AudioSegment
import pygame
from openai import OpenAI

undefinedAnswer = "Input tidak dapat diterima, silahkan kembalikan sebuah pesan untuk mengulangi pertanyaan"

pygame.mixer.init()


class Openai_Chatbot:
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
    modelName = None
    chat = None
    engine = None

    isSpeaking = False
    isAnswering = False
    isCommunicating = False

    history = []

    def __init__(self, apiKey, modelName):
        logging.basicConfig(
            filename="./App/Logs/app.log",
            encoding="utf-8",
            filemode="w",
            format="{asctime} - {levelname} - {message}",
            style="{",
            datefmt="%Y-%m-%d %H:%M",
            level=logging.INFO
        )
        self.recognizer = sr.Recognizer()
        self.modelName = modelName
        self.prepModel(apiKey=apiKey)
        self.prepTTS()
        self.prepChat()
        self.prepMicrophone()

    def prepModel(self, apiKey):
        load_dotenv()
        self.model = OpenAI(api_key=apiKey)

    def prepChat(self):
        self.loadPrompt()
        self.history.append({
            "role": "user",
            "content": "Perkenalkan diri kamu!"
        })
        logging.info(msg=f'Message Prepared: {self.history}')
        completion = self.model.chat.completions.create(
            model=self.modelName,
            messages=self.history,
        )
        response = completion.choices[0].message.content
        try:
            print(f"Model: {response}")
            logging.info(msg=f'Answer Given: {response}')
            self.history.append({
                'role': 'assistant',
                'content': response
            })
            logging.info(msg=f'History Updated: {self.history}')
            self.textToSpeech(text=response)
        except Exception as e:
            logging.warning(msg=f'Error: {e}')

    def prepHistory(self, prompt):
        self.history = [{
            "role": "system",
            "content": prompt
        }]
        print(f'Prompt Loaded: {self.history}')
        logging.info(msg=f'Prompt Loaded: {self.history}')

    def loadPrompt(self, promptPath="./src/prompt.txt"):
        with open(file=promptPath, mode='r') as file:
            prompt = file.read()
            self.prepHistory(prompt=prompt)

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
        self.engine.save_to_file(
            text=text, filename="./src/voices/original.wav")
        self.engine.runAndWait()
        self.pitchShift()
        self.isAnswering = True
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
            text = undefinedAnswer
            return text
        except sr.RequestError as e:
            print(f"Error: {e}")
            logging.warning(msg=f"Error: {e}")
            text = undefinedAnswer
            return text
        except Exception as e:
            print(e)
            logging.warning(msg=f"Error: {e}")
            text = undefinedAnswer
            return text

    def speechListen(self):
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(
                    source=source, duration=1.5)
                logging.info(msg="Listening for input...")
                print("Listening for input....")
                audio = self.recognizer.listen(source=source)
                text = self.speechToText(audio=audio)
                return text
        except Exception as e:
            logging.warning(msg=f'Error: {e}')
            print(e)
            text = undefinedAnswer
            return text

    def sendMessage(self, text):
        self.history.append({
            'role': 'user',
            'content': text
        })
        logging.info(msg=f'Message Prepared: {self.history}')
        completion = self.model.chat.completions.create(
            model=self.modelName,
            messages=self.history,
        )
        response = completion.choices[0].message.content
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
        text = emoji_pattern.sub('', text)
        return text

    def pitchShift(self, fileName="./src/voices/original.wav"):

        sound = AudioSegment.from_file(file=fileName, format="wav")

        # Semakin kecil octaves, suara semakin chipmunk
        octaves = 0.5

        new_sample_rate = int(sound.frame_rate * (2.0**octaves))
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

    def resetOutput(self, outputPath="./src/voices/pitched.wav"):
        if os.path.exists(outputPath):
            os.remove(outputPath)

    def attributeLists(self):
        print(f"Recognizer: {type(self.recognizer)}")
        print(f"Model: {type(self.model)}")
        print(f"Engine: {type(self.engine)}")
        print(f"History: {type(self.history)}")

    def run(self):
        self.isCommunicating = True
        while self.isCommunicating:
            print("Current answering status: ", self.isAnswering)
            if not pygame.mixer.music.get_busy():
                self.isAnswering = False
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
