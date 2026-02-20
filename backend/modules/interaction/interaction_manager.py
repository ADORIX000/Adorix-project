import time
import sys
import os

# Add the backend directory to the path so product_qa_engine can be found
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from .tts_engine import speak
from .stt_engine import listen_one_phrase

# Use the lightweight QA engine instead of the heavy LLM brain
from product_qa_engine import ProductQAEngine

# Initialize globally so the JSON database loads only once
qa_engine = ProductQAEngine()

def start_interaction_loop(current_ad_name, state_callback=None):
    """
    This is the core loop that keeps Adorix talking to the user.
    Uses ProductQAEngine to provide exact answers based on JSON data.
    """
    # Clean the ad name (remove .mp4 extension to match json structure)
    clean_ad_name = current_ad_name.replace(".mp4", "")

    # 1. Initial Greeting
    if state_callback:
        state_callback(avatar_state="TALK", subtitle="Hello! I'm Adorix. Do you have any questions?")
        
    speak("Hello! I'm Adorix. I saw you were looking at this ad. Do you have any questions for me?")
    
    if state_callback:
        state_callback(avatar_state="LISTEN", subtitle="I'm listening...")

    # 2. Enter the continuous listening loop
    while True:
        print(">>> [System] Listening for user question...")
        # Listen for exactly 7 seconds per user request
        user_question = listen_one_phrase(timeout=7)
        
        # 3. Handle Silence (The 7-second Timeout)
        if user_question is None:
            print(">>> [System] 7 seconds of continuous silence detected. Ending interaction.")
            if state_callback:
                state_callback(avatar_state="TALK", subtitle="Have a nice day!")
            speak("Have a nice day! I'll go back to the ads now.")
            return "GOTO_LOOP"
            
        # 4. Handle Active Speech
        print(f">>> [User] Question: {user_question}")
        if state_callback:
            state_callback(avatar_state="THINK", subtitle=f"Processing: {user_question}")
        
        # 5. Get Answer from QA Engine Database
        answer = qa_engine.get_answer(user_question, clean_ad_name)
        
        # 6. Speak the Answer
        if state_callback:
            state_callback(avatar_state="TALK", subtitle=answer)
        speak(answer)
        
        if state_callback:
            state_callback(avatar_state="LISTEN", subtitle="Anything else?")