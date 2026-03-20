try:
    import sherpa_onnx
except ImportError:
    sherpa_onnx = None
    print("!!! [Wake Word] WARNING: sherpa_onnx not installed in this environment.")
    print("!!! Run: pip install sherpa-onnx sentencepiece numpy")
import numpy as np
import os
try:
    from pvrecorder import PvRecorder
except ImportError:
    PvRecorder = None
try:
    import sounddevice as sd
except ImportError:
    sd = None

class WakeWordService:
    def __init__(self, callback_function=None):
        self.callback = callback_function
        self.stop_program = False
        self.recorder = None
        self.use_fallback = False
        self.spotter = None

        if sherpa_onnx is None:
            print("!!! [Wake Word] sherpa_onnx not available. Wake word disabled.")
            return
        
        # Setup paths
        base_dir = os.path.dirname(os.path.abspath(__file__))
        model_dir = os.path.join(base_dir, "models", "sherpa-onnx-kws-zipformer-gigaspeech-3.3M-2024-01-01")
        
        try:
            # Initialize Sherpa-ONNX KeywordSpotter directly with paths
            self.spotter = sherpa_onnx.KeywordSpotter(
                tokens=os.path.join(model_dir, "tokens.txt"),
                encoder=os.path.join(model_dir, "encoder-epoch-12-avg-2-chunk-16-left-64.onnx"),
                decoder=os.path.join(model_dir, "decoder-epoch-12-avg-2-chunk-16-left-64.onnx"),
                joiner=os.path.join(model_dir, "joiner-epoch-12-avg-2-chunk-16-left-64.onnx"),
                keywords_file=os.path.join(base_dir, "models", "keywords.txt"),
                num_threads=2,
                sample_rate=16000,
                feature_dim=80,
                max_active_paths=4,
                keywords_score=3.0,     # Further boosted for easier detection
                keywords_threshold=0.10, # Lowered threshold (0.15 -> 0.10)
            )
            print(">>> [Wake Word] Sherpa-ONNX engine initialized (Sensitivity Boosted).")
        except Exception as e:
            print(f"CRITICAL ERROR: Failed to initialize Sherpa-ONNX: {e}")
            self.spotter = None

    def start(self):
        if not self.spotter: return

        try:
            # Initialize Recorder with Auto-Discovery for USB
            try:
                if PvRecorder:
                    # Find the best device index (prefer USB)
                    devices = PvRecorder.get_available_devices()
                    target_index = -1
                    for i, d in enumerate(devices):
                        if "USB" in d or "PnP" in d:
                            print(f">>> [Wake Word] Auto-detected USB Microphone: {d} at index {i}")
                            target_index = i
                            break
                    
                    self.recorder = PvRecorder(device_index=target_index, frame_length=512)
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

            # Sherpa-ONNX stream
            stream = self.spotter.create_stream()
            consecutive_failures = 0

            while not self.stop_program:
                try:
                    if self.use_fallback:
                        # sounddevice uses blocking rec
                        samples = sd.rec(1024, samplerate=16000, channels=1, dtype='float32')
                        sd.wait()
                        samples = samples.flatten()
                    else:
                        pcm = self.recorder.read()
                        samples = np.array(pcm, dtype=np.float32) / 32768.0

                    # Reset failure count on success
                    consecutive_failures = 0
                    
                    stream.accept_waveform(16000, samples)
                    while self.spotter.is_ready(stream):
                        self.spotter.decode_stream(stream)
                    
                    keyword = self.spotter.get_result(stream)
                    if keyword:
                        print(f"\n!!! WAKE WORD DETECTED: {keyword} !!!")
                        if self.callback: self.callback()
                        # Reset stream after detection to avoid double triggers
                        self.spotter.reset_stream(stream)
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
        print("\n>>> Wake Word Service stopped and cleaned up.")

if __name__ == "__main__":
    def test_callback():
        print("Heard the wake word!")
    service = WakeWordService(callback_function=test_callback)
    try:
        service.start()
    except KeyboardInterrupt:
        service.stop()