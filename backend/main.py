import threading
import time
import os
from flask import Flask, jsonify, request
from flask_cors import CORS

# Import your modules
from core.global_state import state_manager
from modules.wake_word import WakeWordService
from modules.detection import DetectionService # Assuming you have this
# from modules.chat import ChatService # Your LLM Logic

app = Flask(__name__)
CORS(app)

# --- THREAD 1: CAMERA DETECTION (Runs in LOOP mode) ---
def run_camera_logic():
    detector = DetectionService() # Your existing class
    
    while True:
        if state_manager.current_mode == "LOOP":
            # 1. Detect User
            demographics = detector.get_demographics() # e.g., {"age": "19-29", "gender": "Male"}
            
            if demographics:
                # 2. Select Ad based on data
                found_ad = state_manager.select_ad(demographics['age'], demographics['gender'])
                
                if found_ad:
                    # 3. Switch Mode
                    state_manager.set_mode("DELIVERY")
                    
        time.sleep(1) # Check every second

# --- THREAD 2: WAKE WORD (Runs in DELIVERY mode) ---
def on_wake_word_trigger():
    if state_manager.current_mode == "DELIVERY":
        state_manager.set_mode("INTERACTION")
        state_manager.last_interaction_time = time.time()

def run_audio_listener():
    # Only initialize if we haven't already
    service = WakeWordService(callback_function=on_wake_word_trigger)
    service.start() # This should be a blocking loop in your module

# --- FLASK API (The Bridge to Frontend) ---

@app.route('/status', methods=['GET'])
def get_status():
    """Frontend polls this to know what to show"""
    # Timeout Logic for Interaction Mode
    if state_manager.current_mode == "INTERACTION":
        if time.time() - state_manager.last_interaction_time > 5: # 5 seconds silence
            print(">>> [TIMEOUT] No question asked. Returning to Ad.")
            state_manager.set_mode("DELIVERY") 
            # Or "LOOP" if you prefer to reset completely

    return jsonify({
        "mode": state_manager.current_mode,
        "video": state_manager.video_to_play,
        "avatar_speaking": state_manager.avatar_speaking,
        "avatar_message": state_manager.avatar_message
    })

@app.route('/ask', methods=['POST'])
def ask_question():
    """Frontend sends microphone text here"""
    user_question = request.json.get('question')
    state_manager.last_interaction_time = time.time() # Reset timeout
    
    # 1. Get Product Description
    ad_id = state_manager.current_ad_id
    try:
        with open(f"ads_data/{ad_id}/description.txt", "r") as f:
            product_info = f.read()
    except:
        product_info = "General Information."

    # 2. Generate Answer (Mockup - Connect your LLM here)
    # answer = ChatService.get_response(user_question, product_info)
    answer = f"I see you are interested in {ad_id}. {product_info[:50]}..." 
    
    state_manager.avatar_message = answer
    state_manager.avatar_speaking = True
    
    # Reset speaking after a delay (or track audio duration)
    threading.Timer(3.0, lambda: setattr(state_manager, 'avatar_speaking', False)).start()
    
    return jsonify({"answer": answer})

@app.route('/ad-finished', methods=['POST'])
def ad_finished():
    """Frontend tells us the video ended"""
    if state_manager.current_mode == "DELIVERY":
        state_manager.set_mode("LOOP")
    return jsonify({"status": "ok"})

# --- STARTUP ---
if __name__ == "__main__":
    # Start Camera Thread
    t1 = threading.Thread(target=run_camera_logic)
    t1.daemon = True
    t1.start()

    # Start Wake Word Thread
    t2 = threading.Thread(target=run_audio_listener)
    t2.daemon = True
    t2.start()

    print(">>> ADORIX SYSTEM STARTED")
    app.run(host='0.0.0.0', port=5000)