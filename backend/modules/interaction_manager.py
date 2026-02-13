import time
from backend.modules.tts_engine import speak
from backend.modules.stt_engine import listen_one_phrase
from backend.modules.brain_engine import get_answer_from_data

def start_interaction_loop(current_product_data):
    """
    Controls the entire conversation flow.
    Returns "TIMEOUT" when the conversation ends naturally.
    """
    
    # 1. Initial Greeting (Triggered when switching modes)
    speak("Hey, how can I help you?")
    
    # 2. Start the Loop
    while True:
        # A. Listen for 5 seconds
        user_text = listen_one_phrase(timeout=5)
        
        # B. Check for Silence (Timeout)
        if user_text is None:
            # Logic: If nothing detected in 5s -> End Interaction
            print("Interaction: Time out detected.")
            speak("Have a nice day!")
            return "TIMEOUT" # Signal to Main to go back to Loop Mode
        
        # C. User spoke! Process the question
        print(f"Interaction: User asked -> {user_text}")
        
        # D. Get Answer from Brain (JSON Data)
        answer = get_answer_from_data(user_text, current_product_data)
        
        # E. Speak the Answer
        speak(answer)
        
        # F. Loop restarts immediately to listen for the next question...
        # (It will go back to step A)