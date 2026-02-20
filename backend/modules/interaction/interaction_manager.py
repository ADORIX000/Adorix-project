import time
from .tts_engine import speak
from .stt_engine import listen_one_phrase
from .brain_engine import get_answer_for_product

def start_interaction_loop(current_ad_name, state_callback=None):
    """
    This is the core loop that keeps Adorix talking to the user.
    """
    # 1. Initial Greeting
    if state_callback:
        state_callback(avatar_state="TALK", subtitle="Hello! I'm Adorix. Do you have any questions?")
        
    speak("Hello! I'm Adorix. I saw you were looking at this ad. Do you have any questions for me?")
    
    if state_callback:
        state_callback(avatar_state="LISTEN", subtitle="I'm listening...")

    # 2. Enter the continuous listening loop
    while True:
        print(">>> [System] Listening for user question...")
        # Listen for exactly 5 seconds
        user_question = listen_one_phrase(timeout=5)
        
        # 3. Handle Silence (The 5-second Timeout)
        if user_question is None:
            print(">>> [System] 5 seconds of silence detected. Ending interaction.")
            if state_callback:
                state_callback(avatar_state="TALK", subtitle="Have a nice day!")
            speak("Have a nice day! I'll go back to the ads now.")
            return "GOTO_LOOP"
            
        # 4. Handle Active Speech
        print(f">>> [User] Question: {user_question}")
        if state_callback:
            state_callback(avatar_state="THINK", subtitle=f"Processing: {user_question}")
        
        # 5. Get Answer from TinyLlama + JSON
        answer = get_answer_for_product(user_question, current_ad_name)
        
        # 6. Speak the Answer
        if state_callback:
            state_callback(avatar_state="TALK", subtitle=answer)
        speak(answer)
        
        if state_callback:
            state_callback(avatar_state="LISTEN", subtitle="Anything else?")