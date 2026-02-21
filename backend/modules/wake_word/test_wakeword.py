import os
import time
import pvporcupine
from pvrecorder import PvRecorder

def run_test():
    print("="*40)
    print("WAKE WORD ENGINE TEST")
    print("="*40)
    
    ACCESS_KEY = "Mq/t/eYybihg3oyZrgu8SIv4jujAh7KeELbD7EepxuQjl4R31pdvmA==" 
    WAKE_WORD_FILENAME = "Hey-Add-Oh-Ricks_en_windows_v4_0_0.ppn"
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    keyword_path = os.path.join(base_dir, WAKE_WORD_FILENAME)
    
    print(f"Keyword file path: {keyword_path}")
    if not os.path.exists(keyword_path):
        print("ERROR: Wake word file NOT found!")
        return
    else:
        print("SUCCESS: Wake word file found.")

    porcupine = None
    recorder = None
    
    try:
        print("\n1. Initializing Porcupine...")
        porcupine = pvporcupine.create(
            access_key=ACCESS_KEY, 
            keyword_paths=[keyword_path]
        )
        print(f"Porcupine loaded. Frame length: {porcupine.frame_length}")
        
        print("\n2. Initializing Audio Recorder...")
        recorder = PvRecorder(device_index=0, frame_length=porcupine.frame_length)
        recorder.start()
        print("Recorder started successfully.")
        
        print("\n>>> LISTENING START... SAY 'HEY ADORIX' (Press Ctrl+C to stop) <<<")
        
        while True:
            pcm = recorder.read()
            result = porcupine.process(pcm)
            
            if result >= 0:
                print("\n" + "*"*30)
                print("!!! WAKE WORD DETECTED !!!")
                print("*"*30 + "\n")
                
    except KeyboardInterrupt:
        print("\nTest stopped by user.")
    except Exception as e:
        print(f"\nCRITICAL ERROR ENCOUNTERED: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\nCleaning up resources...")
        if recorder is not None:
            recorder.delete()
        if porcupine is not None:
            porcupine.delete()
        print("Done.")

if __name__ == "__main__":
    run_test()
