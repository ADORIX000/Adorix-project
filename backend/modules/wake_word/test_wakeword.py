import os
import sys
import time
import math
import struct
import pvporcupine
from pvrecorder import PvRecorder

def calculate_rms(pcm_data):
    """Calculates to Root Mean Square to measure audio volume level"""
    sum_squares = sum([sample * sample for sample in pcm_data])
    if len(pcm_data) == 0:
        return 0
    rms = math.sqrt(sum_squares / len(pcm_data))
    return rms

def run_diagnostic():
    print("="*50)
    print("WAKE WORD COMPREHENSIVE DIAGNOSTIC TEST")
    print("="*50)

    # 1. Environment Checks
    print("\n[1/5] Checking Environment...")
    print(f"Python version: {sys.version.split(' ')[0]}")
    try:
        # Verify the modules are loaded
        pass
        print("[OK] Environment packages installed.")
    except Exception as e:
        print(f"[ERROR] Error loading packages: {e}")
        return

    # 2. Key and File Checks
    print("\n[2/5] Checking Files and Access...")
    ACCESS_KEY = "Mq/t/eYybihg3oyZrgu8SIv4jujAh7KeELbD7EepxuQjl4R31pdvmA==" 
    WAKE_WORD_FILENAME = "Hey-Add-Oh-Ricks_en_windows_v4_0_0.ppn"
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    keyword_path = os.path.join(base_dir, WAKE_WORD_FILENAME)
    
    print(f"Looking for keyword file at: {keyword_path}")
    if os.path.exists(keyword_path):
        print("[OK] Keyword file found!")
    else:
        print("[ERROR] ERROR: Keyword file missing!")
        return

    # 3. Audio Devices Check
    print("\n[3/5] Checking Audio Devices...")
    try:
        devices = PvRecorder.get_available_devices()
        print(f"Found {len(devices)} audio input devices:")
        for i, device in enumerate(devices):
            print(f"  [{i}]: {device}")
        
        # We will use the default device (index 0)
        device_index = 2
        print(f"[OK] Will attempt to use device [{device_index}]: {devices[device_index]}")
    except Exception as e:
        print(f"[ERROR] Error getting audio devices: {e}")
        return

    # 4. Engine Initialization
    print("\n[4/5] Initializing Porcupine Engine...")
    porcupine = None
    recorder = None
    try:
        porcupine = pvporcupine.create(
            access_key=ACCESS_KEY, 
            keyword_paths=[keyword_path],
            sensitivities=[1.0] # Max sensitivity for testing
        )
        print(f"[OK] Porcupine engine loaded. Required frame length: {porcupine.frame_length}")
    except Exception as e:
        print(f"[ERROR] Failed to load Porcupine engine: {e}")
        return

    # 5. Microphone testing and Listening
    print("\n[5/5] Testing Microphone and Listening...")
    try:
        recorder = PvRecorder(device_index=device_index, frame_length=porcupine.frame_length)
        recorder.start()
        print("[OK] Audio recorder started successfully.")
        
        print("\n" + "="*50)
        print("[INFO] DIAGNOSTIC LISTENING STARTED")
        print("SAY: 'Hey Adorix'")
        print("Press Ctrl+C to stop.")
        print("="*50 + "\n")
        
        frame_count = 0
        last_print_time = time.time()
        
        while True:
            # Read PCM data from microphone
            pcm = recorder.read()
            frame_count += 1
            
            # Every 1 second, print the volume level to prove mic is working
            current_time = time.time()
            if current_time - last_print_time > 1.0:
                rms_volume = calculate_rms(pcm)
                
                # Create a simple volume bar
                volume_bars = int(min(rms_volume / 100, 20))
                bar_string = "#" * volume_bars + "-" * (20 - volume_bars)
                
                status_msg = f"[Mic Volume: {rms_volume:6.1f} |{bar_string}|] "
                if rms_volume < 10.0:
                    status_msg += " (WARNING: Microphone might be muted or volume too low!)"
                
                print(status_msg)
                last_print_time = current_time

            # Process with Porcupine
            result = porcupine.process(pcm)
            
            if result >= 0:
                print("\n" + "*"*20)
                print("!!! WAKE WORD 'HEY ADORIX' DETECTED !!!")
                print("*"*20 + "\n")
                
    except KeyboardInterrupt:
        print("\n\n[INFO] Diagnostic stopped by user.")
    except Exception as e:
        print(f"\n[ERROR] CRITICAL LISTENING ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\nCleaning up resources...")
        if recorder is not None:
            recorder.delete()
        if porcupine is not None:
            porcupine.delete()
        print("[OK] Diagnostic finished.")

if __name__ == "__main__":
    run_diagnostic()
