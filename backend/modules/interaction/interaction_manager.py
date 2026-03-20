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

# Lazy-load the QA Engine to avoid import-time hangs and circular issues
_qa_engine = None

def get_qa_engine():
    global _qa_engine
    if _qa_engine is None:
        print(">>> [Interaction] Initializing ProductQAEngine for the first time...")
        _qa_engine = ProductQAEngine()
    return _qa_engine

def get_hybrid_answer(question: str, clean_ad_name: str) -> str:
    """
    Tries the lightning-fast ProductQAEngine first.
    If it fails to find a good match, falls back to BrainEngine (TinyLlama).
    """
    print(f">>> [Hybrid QA] Attempting EXACT MATCH for: '{question}'")
    engine = get_qa_engine()
    answer = engine.get_answer(question, clean_ad_name)
    
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
    
    # Wait for the wakeup animation to finish playing (~2.5 seconds)
    print(">>> [System] Waiting 2.5s for wakeup animation to complete before greeting...")
    time.sleep(2.5)
    
    if state_callback:
        state_callback(avatar_state="talking.webm", subtitle="Hey! I'm Adorix. How can I help you today?")
        
    speak("Hey! I'm Adorix. How can I help you today?")
    
    # --- 1.5 Show the Listing ---
    if state_callback:
        state_callback(show_listing=True)
        
    # Give the user a moment to see the greeting and listing before listening
    time.sleep(1.0)
    
    # --- 2. Enter continuous listening loop ---
    while True:
        if is_active_callback and not is_active_callback(): return "ABORTED"
        if state_callback:
            state_callback(avatar_state="listening.webm", subtitle="Listening...")

        print("\n>>> [System] Listening for user STT input (5-second timeout)...")
        # STT Engine listens for EXACTLY 5 seconds to prevent hanging
        user_question = listen_one_phrase(timeout=5)
        
        if is_active_callback and not is_active_callback(): return "ABORTED"
        
        # --- 3. Branch A: Silence / Timeout -> Transition Back to Loop ---
        if not user_question:
            print(">>> [System] 5 seconds of continuous silence detected. Ending interaction.")
            if state_callback:
                state_callback(avatar_state="talking.webm", subtitle="Have a nice day!")
            speak("Have a nice day!")
            time.sleep(1.0) # Buffer before state change
            return "GOTO_LOOP"
            
        # --- 4. Branch B: Process Active Speech ---
        # Ignore very short noises (less than 2 words/4 chars often indicate just background clicks)
        if len(user_question.split()) < 2 and len(user_question) < 5:
            print(f">>> [System] Ignored likely noise: '{user_question}'")
            continue

        print(f">>> [User STT Input] {user_question}")
        if state_callback:
            # Change UI to indicate thinking
            state_callback(avatar_state="thinking.webm", subtitle="Thinking...")
        
        # Artificial delay to make "Thinking" visible
        time.sleep(0.8)

        # Generate Hybrid Answer using RAG
        answer = get_hybrid_answer(user_question, clean_ad_name)
        
        if is_active_callback and not is_active_callback(): return "ABORTED"
        
        # --- 5. TTS Output (Answering) ---
        print(f">>> [System TTS Output] {answer}")
        if state_callback:
            state_callback(avatar_state="talking.webm", subtitle=answer)
        speak(answer)
        time.sleep(1.0) # Buffer after answering
        
        if is_active_callback and not is_active_callback(): return "ABORTED"
        
        # --- 6. TTS Output (Follow-up) ---
        if state_callback:
            state_callback(avatar_state="talking.webm", subtitle="Any other questions?")
        speak("Any other questions?")
        time.sleep(0.5) # Small buffer before returning to listen mode