# Voice Input + Voice Output with Response Size Limit + Object Detection (Potentially others)

import os
import requests
import pyttsx3
import speech_recognition as sr
from dotenv import load_dotenv
import subprocess
import time
import sys
import signal


# Load API key
load_dotenv()
api_key = os.getenv("OPENROUTER_API_KEY")

# Setup text-to-speech engine
engine = pyttsx3.init()


import subprocess
import time
import sys

def run_object_detection():
    speak("Starting object detection for 10 seconds.")

    # Start object detection as a background process
    process = subprocess.Popen([
        sys.executable,
        "Object_Detection/detection.py"
    ])

    # Let it run for 10 seconds
    time.sleep(25)

    # Try to gracefully terminate the detection process
    process.terminate()

    try:
        process.wait(timeout=2)  # Give time for graceful shutdown
        speak("Object detection completed.")
    except subprocess.TimeoutExpired:
        process.kill()
        speak("Object detection was forcibly stopped.")


def speak(text):
    """
    Speaks the given text using pyttsx3.
    """
    engine.say(text)
    engine.runAndWait()


def listen():
    """
    Listens for voice input and returns recognized text.
    """
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


def ask_jarvis(prompt):
    """
    Sends a prompt to OpenRouter API and returns a short response.
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://yourapp.com",  # Your app or GitHub link
        "X-Title": "Navis-assistant"
    }

    data = {
        "model": "mistralai/mistral-7b-instruct",
        "messages": [
            {"role": "system", "content": "You are Navis, a helpful and intelligent assistant. Reply in less than 30 words."},
            {"role": "user", "content": prompt}
        ]
    }

    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)

    if response.status_code == 200:
        reply = response.json()['choices'][0]['message']['content']
        return reply.strip()
    else:
        return f"Error: {response.status_code} - {response.text}"


# Main loop
if __name__ == "__main__":
    print("🔊 Navis with Voice is online. Say 'exit' to quit.\n")
    speak("Navis is online. Say something.")

    while True:
        user_input = listen()
        if user_input:

            command = user_input.lower()

            if command in ["exit", "quit", "stop"]:
                speak("Goodbye!")
                print("Navis: Goodbye!")
                break

            elif "object detection" in command or "detect objects" in command:
                run_object_detection()
                continue

            reply = ask_jarvis(user_input)
            print(f"Navis: {reply}\n")
            speak(reply)
