import os
import time

try:
    import pvporcupine
except ImportError:
    pvporcupine = None
    print("!!! [Wake Word] WARNING: pvporcupine not installed in this environment.")
    print("!!! Run: pip install pvporcupine")

try:
    from pvrecorder import PvRecorder
except ImportError:
    PvRecorder = None

try:
    import sounddevice as sd
except ImportError:
    sd = None

# STRICT MINIMAL CHANGE: Load .env locally inside the service to avoid touching main.py
try:
    from dotenv import load_dotenv
    # Points to backend/.env safely
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
    load_dotenv(env_path)
except ImportError:
    pass

class WakeWordService:
    def __init__(self, callback_function=None):
        self.callback = callback_function
        self.stop_program = False
        self.recorder = None
        self.use_fallback = False
        self.porcupine = None

        if pvporcupine is None:
            print("!!! [Wake Word] pvporcupine not available. Wake word disabled.")
            return
        
        # Setup paths
        base_dir = os.path.dirname(os.path.abspath(__file__))
        keyword_path = os.path.join(base_dir, "models", "hey_adorix.ppn")
        access_key = os.environ.get("PICOVOICE_ACCESS_KEY", "")

        if not access_key:
            print("!!! [Wake Word] PICOVOICE_ACCESS_KEY not found in environment. Wake word disabled.")
            return

        try:
            self.porcupine = pvporcupine.create(
                access_key=access_key,
                keyword_paths=[keyword_path]
            )
            print(">>> [Wake Word] Porcupine engine initialized.")
        except Exception as e:
            print(f"CRITICAL ERROR: Failed to initialize Porcupine: {e}")
            self.porcupine = None

    def start(self):
        if not self.porcupine: return

        try:
            try:
                if PvRecorder:
                    devices = PvRecorder.get_available_devices()
                    target_index = -1
                    for i, d in enumerate(devices):
                        if "USB" in d or "PnP" in d:
                            print(f">>> [Wake Word] Auto-detected USB Microphone: {d} at index {i}")
                            target_index = i
                            break
                    
                    self.recorder = PvRecorder(device_index=target_index, frame_length=self.porcupine.frame_length)
                    self.recorder.start()
                    print(f">>> [Wake Word] Recording started ({devices[target_index] if target_index != -1 else 'Default Device'})")
                else:
                    raise ImportError("PvRecorder not found")
            except Exception as e:
                print(f">>> [Wake Word] PvRecorder failed: {e}. Falling back to sounddevice.")
                if sd:
                    self.use_fallback = True
                    print(">>> [Wake Word] Recording started (sounddevice fallback)")
                else:
                    raise Exception("No recording library available (PvRecorder/sounddevice).")

            print(">>> [Wake Word] Listening for 'Hey Adorix'...")

            consecutive_failures = 0

            while not self.stop_program:
                try:
                    if self.use_fallback:
                        # Modified float32 to int16 strictly to prevent Picovoice crashing on fallback
                        samples = sd.rec(self.porcupine.frame_length, samplerate=16000, channels=1, dtype='int16')
                        sd.wait()
                        pcm = samples.flatten().tolist()
                    else:
                        pcm = self.recorder.read()

                    # Reset failure count on success
                    consecutive_failures = 0
                    
                    keyword_index = self.porcupine.process(pcm)
                    if keyword_index >= 0:
                        print("\n!!! WAKE WORD DETECTED: Hey Adorix !!!")
                        if self.callback: self.callback()

                except Exception as loop_e:
                    consecutive_failures += 1
                    print(f"!!! [Wake Word Loop Error] {loop_e} (Failure {consecutive_failures}/10)")
                    
                    if consecutive_failures >= 10 and not self.use_fallback:
                        print("!!! [Wake Word] Persistent failure. Attempting to restart recorder...")
                        try:
                            self.recorder.stop()
                            time.sleep(1)
                            self.recorder.start()
                            print(">>> [Wake Word] Recorder restarted successfully.")
                            consecutive_failures = 0
                        except:
                            print("!!! [Wake Word] Restart failed. Check your USB connection.")
                    
                    time.sleep(0.1)

        except Exception as e:
            print(f"CRITICAL WAKE WORD ERROR: {e}") 
        finally:
            self.stop()

    def stop(self):
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
        print("Heard the wake word!")
    service = WakeWordService(callback_function=test_callback)
    try:
        service.start()
    except KeyboardInterrupt:
        service.stop()