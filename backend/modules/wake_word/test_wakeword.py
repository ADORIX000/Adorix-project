"""
Sherpa-ONNX Wake Word Diagnostic Test
Tests the new Sherpa-ONNX keyword spotting engine.
Run with: python test_wakeword.py
"""
import os, sys, time, math

def run_diagnostic():
    print("="*55)
    print("  SHERPA-ONNX WAKE WORD DIAGNOSTIC TEST")
    print("="*55)

    # 1. Environment Check
    print("\n[1/4] Checking Environment...")
    print(f"  Python: {sys.version.split(' ')[0]}")
    try:
        import sherpa_onnx
        print("  [OK] sherpa_onnx is installed.")
    except ImportError:
        print("  [FAIL] sherpa_onnx is NOT installed!")
        print("  --> Fix: pip install sherpa-onnx sentencepiece numpy")
        return

    try:
        import numpy as np
        print("  [OK] numpy is installed.")
    except ImportError:
        print("  [FAIL] numpy is NOT installed! Run: pip install numpy")
        return

    # 2. Model File Check
    print("\n[2/4] Checking Model Files...")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    model_dir = os.path.join(base_dir, "models", "sherpa-onnx-kws-zipformer-gigaspeech-3.3M-2024-01-01")
    keywords_file = os.path.join(base_dir, "models", "keywords.txt")

    required_files = {
        "Encoder": os.path.join(model_dir, "encoder-epoch-12-avg-2-chunk-16-left-64.onnx"),
        "Decoder": os.path.join(model_dir, "decoder-epoch-12-avg-2-chunk-16-left-64.onnx"),
        "Joiner": os.path.join(model_dir, "joiner-epoch-12-avg-2-chunk-16-left-64.onnx"),
        "Tokens": os.path.join(model_dir, "tokens.txt"),
        "Keywords": keywords_file,
    }
    all_found = True
    for name, path in required_files.items():
        if os.path.exists(path):
            print(f"  [OK] {name}: {os.path.basename(path)}")
        else:
            print(f"  [FAIL] {name} NOT FOUND: {path}")
            all_found = False

    if not all_found:
        print("\n  --> Some model files are missing. Re-download the models.")
        return

    # Show current keyword
    with open(keywords_file, encoding="utf-8") as f:
        kw = f.read().strip()
    print(f"  Keyword (BPE encoded): {kw}")

    # 3. Engine Initialization
    print("\n[3/4] Initializing Sherpa-ONNX Engine...")
    try:
        spotter = sherpa_onnx.KeywordSpotter(
            tokens=required_files["Tokens"],
            encoder=required_files["Encoder"],
            decoder=required_files["Decoder"],
            joiner=required_files["Joiner"],
            keywords_file=keywords_file,
            num_threads=2,
            sample_rate=16000,
            feature_dim=80,
            max_active_paths=4,
            keywords_score=2.0,      # Boosted
            keywords_threshold=0.2,  # Sensitive
        )
        print("  [OK] Sherpa-ONNX engine initialized (Sensitivity Boosted).")
    except Exception as e:
        print(f"  [FAIL] Engine initialization error: {e}")
        return

    # 4. Audio Recording + Detection
    print("\n[4/4] Testing Audio & Listening for Wake Word...")

    # Try PvRecorder first, then sounddevice
    recorder = None
    use_fallback = False
    frame_size = 512

    try:
        from pvrecorder import PvRecorder
        recorder = PvRecorder(device_index=-1, frame_length=frame_size)
        recorder.start()
        print("  [OK] Audio started using PvRecorder.")
    except Exception as e:
        print(f"  [INFO] PvRecorder unavailable ({e}), trying sounddevice...")
        try:
            import sounddevice as sd
            use_fallback = True
            print("  [OK] Audio started using sounddevice (fallback).")
        except ImportError:
            print("  [FAIL] No audio library available. Install pvrecorder or sounddevice.")
            return

    stream = spotter.create_stream()

    print("\n" + "="*55)
    print("  SAY: 'Hey Adorix'  (Ctrl+C to stop)")
    print("="*55 + "\n")

    last_print = time.time()
    try:
        while True:
            if use_fallback:
                samples = sd.rec(frame_size, samplerate=16000, channels=1, dtype='float32')
                sd.wait()
                samples = samples.flatten()
            else:
                pcm = recorder.read()
                samples = np.array(pcm, dtype=np.float32) / 32768.0

            # Volume meter every second
            if time.time() - last_print > 1.0:
                rms = math.sqrt(sum(x*x for x in samples) / len(samples)) * 100
                bars = int(min(rms * 2, 20))
                print(f"  Mic Level: |{'#'*bars}{'-'*(20-bars)}| {rms:.1f}"
                      + (" (too low?)" if rms < 1.0 else ""))
                last_print = time.time()

            stream.accept_waveform(16000, samples)
            while spotter.is_ready(stream):
                spotter.decode_stream(stream)

            result = spotter.get_result(stream)
            if result:
                print("\n" + "*"*40)
                print("  !!! WAKE WORD DETECTED: Hey Adorix !!!")
                print("*"*40 + "\n")
                spotter.reset_stream(stream)

    except KeyboardInterrupt:
        print("\n\n  [INFO] Test stopped by user.")
    finally:
        if recorder:
            try: recorder.stop(); recorder.delete()
            except: pass
        print("  [OK] Cleanup complete.")

if __name__ == "__main__":
    run_diagnostic()
