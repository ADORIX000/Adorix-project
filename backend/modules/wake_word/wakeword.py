import pvporcupine
from pvrecorder import PvRecorder
import os
import threading
import time

class WakeWordService:
    def __init__(self, callback_function=None):
        """
        Initializes the Porcupine wake word engine.
        :param callback_function: Function to call when the wake word is detected.
        """
        # --- CONFIGURATION (User provided) ---
        self.ACCESS_KEY = "Mq/t/eYybihg3oyZrgu8SIv4jujAh7KeELbD7EepxuQjl4R31pdvmA==" 
        self.WAKE_WORD_FILENAME = "Hey-Add-Oh-Ricks_en_windows_v4_0_0.ppn"
        
        self.callback = callback_function
        self.stop_program = False
        self.porcupine = None
        self.recorder = None

    def start(self):
        """Starts listening for the wake word in a loop."""
        # 1. Setup Path to Wake Word File
        base_dir = os.path.dirname(os.path.abspath(__file__))
        keyword_path = os.path.join(base_dir, self.WAKE_WORD_FILENAME)

        if not os.path.exists(keyword_path):
            print(f"\nCRITICAL ERROR: Wake word file not found!")
            print(f"Looking for: {keyword_path}")
            return

        try:
            # 2. Initialize Porcupine
            self.porcupine = pvporcupine.create(
                access_key=self.ACCESS_KEY, 
                keyword_paths=[keyword_path]
            )
            self.recorder = PvRecorder(device_index=-1, frame_length=self.porcupine.frame_length)
            self.recorder.start()
            
            print(f">>> [Wake Word] Service Started. Listening for 'Hey Adorix'...")

            while not self.stop_program:
                if self.recorder and self.porcupine:
                    pcm = self.recorder.read()
                    result = self.porcupine.process(pcm)

                    if result >= 0:
                        print("!!! WAKE WORD DETECTED !!!")
                        if self.callback:
                            self.callback()
                        else:
                            print("(No callback defined for wake word)")
                
                # Small sleep to prevent high CPU usage if needed, 
                # but process() is usually blocking/timed.
                
        except Exception as e:
            print(f"CRITICAL AUDIO ERROR: {e}")
        finally:
            self.stop()

    def stop(self):
        """Stops the recorder and cleans up resources."""
        self.stop_program = True
        if self.recorder:
            self.recorder.stop()
            self.recorder.delete()
            self.recorder = None
        if self.porcupine:
            self.porcupine.delete()
            self.porcupine = None

# For standalone testing
if __name__ == "__main__":
    def test_callback():
        print("Test Callback: I heard the wake word!")

    service = WakeWordService(callback_function=test_callback)
    try:
        service.start()
    except KeyboardInterrupt:
        service.stop()