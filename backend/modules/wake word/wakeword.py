import cv2
import pvporcupine
from pvrecorder import PvRecorder
import speech_recognition as sr
import pyttsx3
import threading
import time
import os
import numpy as np
import sys

# ================= CONFIGURATION =================
# 1. PASTE YOUR ACCESS KEY INSIDE THESE QUOTES:
ACCESS_KEY = "Mq/t/eYybihg3oyZrgu8Slv4jujAh7KeELbD7EepxuQjl4R31pdvmA==" 

# 2. PASTE YOUR EXACT FILE NAME HERE:
# (Make sure this file is in the same folder as this script!)
WAKE_WORD_FILENAME = "Hey-Add-Oh-Ricks_en_windows_v4_0_0.ppn"

# ================= GLOBAL VARIABLES =================
current_state = "IDLE" 
stop_program = False

# ================= TASK A: AUDIO BRAIN (Background Thread) =================
def run_audio_logic():
    global current_state, stop_program
    
    # 1. Setup Path to Wake Word File
    base_dir = os.path.dirname(os.path.abspath(__file__))
    keyword_path = os.path.join(base_dir, WAKE_WORD_FILENAME)

    # Security Check: Does the file exist?
    if not os.path.exists(keyword_path):
        print(f"\nCRITICAL ERROR: Wake word file not found!")
        print(f"Looking for: {keyword_path}")
        print("Please move the .ppn file into this folder.\n")
        stop_program = True
        return

    try:
        # 2. Initialize Porcupine with Custom File
        porcupine = pvporcupine.create(
            access_key=ACCESS_KEY, 
            keyword_paths=[keyword_path]
        )
        recorder = PvRecorder(device_index=-1, frame_length=porcupine.frame_length)
        recorder.start()
        
        # 3. Setup Speech (TTS & STT)
        tts = pyttsx3.init()
        tts.setProperty('rate', 150) # Slow down voice slightly
        recognizer = sr.Recognizer()
        mic = sr.Microphone()
        
        print(f"\n>>> SYSTEM READY. Say 'Hey Adorix' to start...")

        while not stop_program:
            if current_state == "IDLE":
                # Listen for Wake Word
                pcm = recorder.read()
                result = porcupine.process(pcm)

                if result >= 0:
                    print("!!! WAKE WORD DETECTED !!!")
                    recorder.stop()
                    
                    # --- START INTERACTION ---
                    current_state = "ACTIVE"
                    tts.say("Hello! I am Adorix.")
                    tts.runAndWait()
                    
                    # Listen for user input (5s timeout)
                    try:
                        print(">>> Listening for your command...")
                        with mic as source:
                            recognizer.adjust_for_ambient_noise(source, duration=0.5)
                            audio = recognizer.listen(source, timeout=5)
                        
                        text = recognizer.recognize_google(audio)
                        print(f">>> You said: {text}")
                        
                        # Simple Logic
                        if "price" in text:
                            response = "We have a 50% discount today."
                        elif "bye" in text:
                            response = "Goodbye!"
                        else:
                            response = "I heard you say " + text
                            
                        tts.say(response)
                        tts.runAndWait()
                        
                    except sr.WaitTimeoutError:
                        print(">>> No speech detected.")
                        tts.say("I didn't hear anything. Goodbye.")
                        tts.runAndWait()
                    except Exception as e:
                        print(f">>> Error: {e}")
                        tts.say("Sorry, I missed that.")
                        tts.runAndWait()
                    
                    # --- END INTERACTION ---
                    current_state = "IDLE"
                    print(">>> Returning to Sleep...")
                    recorder.start()
            else:
                time.sleep(0.1)
                
    except Exception as e:
        print(f"CRITICAL AUDIO ERROR: {e}")
    finally:
        if 'recorder' in locals(): recorder.delete()
        if 'porcupine' in locals(): porcupine.delete()

# ================= TASK B: VISUAL DISPLAY (Main Thread) =================
def main_display():
    global stop_program
    
    # 1. Generate Dummy Images (So code never crashes)
    if not os.path.exists("idle.jpg"):
        blank = np.zeros((600,800,3), np.uint8)
        cv2.putText(blank, 'SLEEPING', (250, 300), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
        cv2.putText(blank, '(Say Hey Adorix)', (260, 350), cv2.FONT_HERSHEY_SIMPLEX, 1, (200, 200, 200), 2)
        cv2.imwrite("idle.jpg", blank)
        
    if not os.path.exists("active.jpg"):
        active_img = np.zeros((600,800,3), np.uint8)
        active_img[:] = (0, 100, 0) # Green Background
        cv2.putText(active_img, 'LISTENING...', (250, 300), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
        cv2.imwrite("active.jpg", active_img)

    # 2. Load Images
    img_idle = cv2.imread("idle.jpg")
    img_active = cv2.imread("active.jpg")

    # 3. Start Audio Thread
    thread = threading.Thread(target=run_audio_logic)
    thread.daemon = True
    thread.start()

    # 4. Show Window
    window_name = "ADORIX WINDOWS KIOSK (Press Q to Quit)"
    cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)

    print(">>> DISPLAY STARTED.")

    while not stop_program:
        if current_state == "IDLE":
            cv2.imshow(window_name, img_idle)
        elif current_state == "ACTIVE":
            cv2.imshow(window_name, img_active)
            
        # Check for 'q' to quit
        if cv2.waitKey(100) & 0xFF == ord('q'):
            stop_program = True
            break
            
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main_display()