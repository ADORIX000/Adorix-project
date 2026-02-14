# backend/core/global_state.py

class AdorixState:
    def __init__(self):
        # Modes: "LOOP", "DELIVERY", "INTERACTION"
        self.current_mode = "LOOP" 
        self.current_ad_id = None
        self.last_interaction_time = 0
        
        # Data for the Frontend
        self.video_to_play = "default_loop.mp4"
        self.avatar_message = ""
        self.avatar_speaking = False

    def set_mode(self, mode):
        print(f">>> [STATE CHANGE] Switching to {mode}")
        self.current_mode = mode

    def select_ad(self, age, gender):
        # Simple logic to pick ad based on demographics
        # In a real app, you'd check a database here
        print(f">>> [AD SELECTION] User is {age} {gender}")
        
        if "19-29" in age:
            self.current_ad_id = "A0001"
            self.video_to_play = "A0001/ad_video.mp4" # Path relative to public folder
            return True
        return False

# Create a single instance to be shared
state_manager = AdorixState()