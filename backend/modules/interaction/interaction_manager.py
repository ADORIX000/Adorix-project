import time
from tts_engine import speak
from stt_engine import listen_one_phrase
from brain_engine import get_answer_for_product

def start_interaction_loop(current_ad_name):
    """
    This is the core loop that keeps Adorix talking to the user.
    """
    # 1. Initial Greeting
    speak("Hello! I'm Adorix. I saw you were looking at this ad. Do you have any questions for me?")
    
    # 2. Enter the continuous listening loop
    while True:
        print(">>> [System] Listening for user question...")
        # Listen for exactly 5 seconds
        user_question = listen_one_phrase(timeout=5)
        
        # 3. Handle Silence (The 5-second Timeout)
        if user_question is None:
            print(">>> [System] 5 seconds of silence detected. Ending interaction.")
            speak("Have a nice day! I'll go back to the ads now.")
            return "GOTO_LOOP" # This tells main.py to switch modes
            
        # 4. Handle Active Speech
        print(f">>> [User] Question: {user_question}")
        
        # 5. Get Answer from TinyLlama + JSON
        answer = get_answer_from_data(user_question, current_ad_name)
        
        # 6. Speak the Answer
        speak(answer)
        
        # The loop now repeats, going back to 'listen_one_phrase' automatically!