# Navis - Voice Assistant with Memory + Object Detection

import os
import sys
import time
import json
import subprocess
import requests
import pyttsx3
import speech_recognition as sr
from dotenv import load_dotenv
import signal

# Load OpenRouter API key
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

# Text-to-speech engine
engine = pyttsx3.init()
engine.setProperty('rate', 150)
engine.setProperty('volume', 1)

# User data persistence
USER_DATA_FILE = "user_data.json"

def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_user_data(data):
    with open(USER_DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

user_data = load_user_data()

# Speak function
def speak(text):
    engine.say(text)
    engine.runAndWait()

# Listen function
def listen():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎙️ Speak now...")
        r.adjust_for_ambient_noise(source)
        audio = r.listen(source)
        try:
            text = r.recognize_google(audio)
            print(f"📝 You said: {text}")
            return text
        except sr.UnknownValueError:
            print("❌ Could not understand audio.")
            speak("Sorry, I didn't catch that.")
            return None
        except sr.RequestError:
            print("❌ Could not request results from Google Speech Recognition.")
            speak("Speech recognition service is unavailable.")
            return None

# Run object detection for 25 seconds
def run_object_detection():
    speak("Starting object detection for 25 seconds.")
    process = subprocess.Popen([sys.executable, "Object_Detection/detection.py"])
    time.sleep(25)
    process.terminate()
    try:
        process.wait(timeout=2)
        speak("Object detection completed.")
    except subprocess.TimeoutExpired:
        process.kill()
        speak("Object detection was forcibly stopped.")

# Store dynamic memory from natural speech
def extract_and_store_fact(user_input, user_data):
    system_prompt = (
    "You're a personal assistant that stores facts the user tells you. "
    "If the user is telling you a personal fact (like 'I work at Robomanthan', 'my dog's name is Rocky', or 'my favorite food is pizza'), "
    "extract and return it as a JSON object like {\"key\": \"workplace\", \"value\": \"Robomanthan\"}. "
    "You may choose keys like 'workplace', 'birthday', 'name', 'hobby', 'favorite_food', etc. "
    "If the input is not a fact, return null."
    )


    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://yourapp.com",
        "X-Title": "Navis-assistant"
    }

    data = {
        "model": "mistralai/mistral-7b-instruct",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
    }

    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)

    if response.status_code == 200:
        reply = response.json()['choices'][0]['message']['content']
        try:
            fact = json.loads(reply)
            if isinstance(fact, dict) and "key" in fact and "value" in fact:
                user_data[fact["key"]] = fact["value"]
                save_user_data(user_data)
                speak(f"Got it. I'll remember your {fact['key']} is {fact['value']}.")
                return True
        except json.JSONDecodeError:
            pass
    return False

# Ask AI assistant (limited response)
def ask_jarvis(prompt):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://yourapp.com",
        "X-Title": "Navis-assistant"
    }

    data = {
        "model": "mistralai/mistral-7b-instruct",
        "messages": [
            {"role": "system", "content": f"You are Navis, a helpful and intelligent assistant. The user's name is {user_data.get('name', 'unknown')}. Reply in less than 30 words."},
            {"role": "user", "content": prompt}
        ]
    }

    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)

    if response.status_code == 200:
        reply = response.json()['choices'][0]['message']['content']
        return reply.strip()
    else:
        return f"Error: {response.status_code} - {response.text}"

# === Main Loop ===
if __name__ == "__main__":
    print("🔊 Navis with Voice is online. Say 'exit' to quit.\n")
    speak("Navis is online. Say something.")

    while True:
        user_input = listen()
        if user_input:
            command = user_input.lower()

            if command in ["exit", "quit", "stop"]:
                speak("Goodbye!")
                break

            elif "object detection" in command or "detect objects" in command:
                run_object_detection()
                continue

            elif any(x in command for x in ["what is my", "when is my", "tell me my"]):
                matched = False
                for key in user_data:
                    if key.lower() in command:
                        speak(f"Your {key} is {user_data[key]}.")
                        matched = True
                        break
                if not matched:
                    speak("I couldn't find that information in my memory.")
                continue

            # Try to store fact from user input
            if extract_and_store_fact(user_input, user_data):
                continue

            # Default: ask AI
            reply = ask_jarvis(user_input)
            print(f"Navis: {reply}\n")
            speak(reply)
