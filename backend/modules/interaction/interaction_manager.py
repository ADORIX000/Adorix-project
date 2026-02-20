import time
import sys
import os

# Add the backend directory to the path so modules can be found
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from .tts_engine import speak
from .stt_engine import listen_one_phrase

# Load Both Engines
from product_qa_engine import ProductQAEngine
from modules.interaction.brain_engine import adorix_brain

# Initialize globally so the JSON database loads only once
qa_engine = ProductQAEngine()

def get_hybrid_answer(question: str, clean_ad_name: str) -> str:
    """
    Tries the lightning-fast ProductQAEngine first.
    If it fails to find a good match, falls back to BrainEngine (TinyLlama).
    """
    print(f">>> [Hybrid QA] Attempting EXACT MATCH for: '{question}'")
    answer = qa_engine.get_answer(question, clean_ad_name)
    
    # If the QA Engine couldn't find an exact match, it returns its fallback string.
    # We intercept that and use the BrainEngine instead.
    if "I don't have that specific information" in answer or "I'm sorry, I don't have information about that product" in answer:
        print(f">>> [Hybrid QA] Exact match failed. Falling back to LLM BrainEngine...")
        # Load context specifically for the brain
        context = adorix_brain.load_context_from_json(f"{clean_ad_name}.json")
        answer = adorix_brain.generate_answer(question, context)
        
    return answer

def start_interaction_loop(current_ad_name, state_callback=None, is_active_callback=None):
    """
    Core conversational loop utilizing strict STT input and TTS output.
    Returns: "GOTO_LOOP" (Timeout) or "ABORTED" (User walked away).
    """
    # Clean the ad name (remove .mp4 extension to match json structure)
    clean_ad_name = current_ad_name.replace(".mp4", "") if current_ad_name else "generic_ad"

    # --- 1. Initial Greeting ---
    if is_active_callback and not is_active_callback(): return "ABORTED"
    if state_callback:
        state_callback(avatar_state="TALK", subtitle="Hello! I'm Adorix. Do you have any questions?")
        
    speak("Hello! I'm Adorix. I saw you were looking at this ad. Do you have any questions for me?")
    
    # --- 2. Enter continuous listening loop ---
    while True:
        if is_active_callback and not is_active_callback(): return "ABORTED"
        if state_callback:
            state_callback(avatar_state="LISTEN", subtitle="I'm listening...")

        print("\n>>> [System] Listening for user STT input...")
        # STT Engine listens for exactly 7 seconds
        user_question = listen_one_phrase(timeout=7)
        
        if is_active_callback and not is_active_callback(): return "ABORTED"
        
        # --- 3. Handle Silence (The 7-second Timeout) -> Transition Back to Loop ---
        if not user_question:
            print(">>> [System] 7 seconds of continuous silence detected. Ending interaction.")
            if state_callback:
                state_callback(avatar_state="TALK", subtitle="Have a nice day!")
            speak("Have a nice day! I'll go back to the ads now.")
            return "GOTO_LOOP"
            
        # --- 4. Process Active Speech ---
        print(f">>> [User STT Input] {user_question}")
        if state_callback:
            state_callback(avatar_state="THINK", subtitle=f"Processing: {user_question}")
        
        # --- 5. Generate Hybrid Answer ---
        answer = get_hybrid_answer(user_question, clean_ad_name)
        
        if is_active_callback and not is_active_callback(): return "ABORTED"
        
        # --- 6. TTS Output ---
        print(f">>> [System TTS Output] {answer}")
        if state_callback:
            state_callback(avatar_state="TALK", subtitle=answer)
        speak(answer)
        
        if is_active_callback and not is_active_callback(): return "ABORTED"
        if state_callback:
            state_callback(avatar_state="LISTEN", subtitle="Anything else?")