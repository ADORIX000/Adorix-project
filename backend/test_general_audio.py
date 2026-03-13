import sounddevice as sd
import numpy as np

def test_recording():
    output = []
    output.append("Listing sounddevice devices:")
    output.append(str(sd.query_devices()))
    
    fs = 44100  # Sample rate
    seconds = 0.5  # Duration of recording

    output.append(f"\nAttempting to record {seconds} seconds of audio...")
    try:
        myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=1)
        sd.wait() 
        output.append("Recording finished successfully!")
        output.append(f"Max amplitude: {np.max(np.abs(myrecording))}")
    except Exception as e:
        output.append(f"Recording failed: {e}")
        
    with open("audio_capabilities_log.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(output))

if __name__ == "__main__":
    test_recording()
