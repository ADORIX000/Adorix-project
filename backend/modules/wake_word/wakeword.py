import pvporcupine
from pvrecorder import PvRecorder
import os
import numpy as np
try:
    import sounddevice as sd
except ImportError:
    sd = None

class WakeWordService:
    def __init__(self, callback_function=None):
        self.ACCESS_KEY = "Mq/t/eYybihg3oyZrgu8SIv4jujAh7KeELbD7EepxuQjl4R31pdvmA==" 
        self.WAKE_WORD_FILENAME = "Hey-Add-Oh-Ricks_en_windows_v4_0_0.ppn"
        self.callback = callback_function
        self.stop_program = False
        self.porcupine = None
        self.recorder = None
        self.use_fallback = False

    def start(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        keyword_path = os.path.join(base_dir, self.WAKE_WORD_FILENAME)

        if not os.path.exists(keyword_path):
            print(f"CRITICAL ERROR: Wake word file missing: {keyword_path}")
            return

        try:
            self.porcupine = pvporcupine.create(
                access_key=self.ACCESS_KEY, 
                keyword_paths=[keyword_path],
                sensitivities=[1]
            )
            
            # --- RECORDER INITIALIZATION ---
            try:
                # Primary: PvRecorder
                self.recorder = PvRecorder(device_index=-1, frame_length=self.porcupine.frame_length)
                self.recorder.start()
                print(">>> [Wake Word] Service Started (PvRecorder)")
            except Exception as e:
                print(f">>> [Wake Word] PvRecorder failed: {e}")
                if sd:
                    self.use_fallback = True
                    print(">>> [Wake Word] Service Started (sounddevice fallback)")
                else:
                    raise Exception("PvRecorder failed and sounddevice is not installed.")

            print(">>> [Wake Word] Listening for 'Hey Adorix'...")
            
            # --- MAIN LOOP ---
            while not self.stop_program:
                try:
                    if self.use_fallback:
                        # Record 16kHz mono frame
                        pcm_float = sd.rec(self.porcupine.frame_length, samplerate=16000, channels=1, dtype='float32')
                        sd.wait()
                        pcm = (pcm_float.flatten() * 32767).astype(np.int16)
                    else:
                        pcm = self.recorder.read()
                    
                    result = self.porcupine.process(pcm)
                    if result >= 0:
                        print("\n!!! WAKE WORD DETECTED !!!")
                        if self.callback: self.callback()
                        else: print("(No callback)")
                except Exception as loop_e:
                    print(f"!!! [Wake Word Loop Error] {loop_e}")
                    import time
                    time.sleep(1) # Prevent tight loop on error
                
        except Exception as e:
            print(f"CRITICAL WAKE WORD SERVICE ERROR: {e}")
        finally:
            self.stop()

    def stop(self):
        """Stops the recorder and cleans up resources."""
        self.stop_program = True
        if self.recorder:
            try:
                self.recorder.stop()
                self.recorder.delete()
            except: pass
            self.recorder = None
        
        if self.porcupine:
            try:
                self.porcupine.delete()
            except: pass
            self.porcupine = None
            
        print("\n>>> Wake Word Service stopped and cleaned up.")

if __name__ == "__main__":
    def test_callback():
        print("Test Callback: I heard the wake word!")

    service = WakeWordService(callback_function=test_callback)
    try:
        service.start()
    except KeyboardInterrupt:
        service.stop()