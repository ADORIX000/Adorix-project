from pvrecorder import PvRecorder

def list_devices():
    output = []
    output.append("--- AVAILABLE AUDIO DEVICES ---")
    try:
        devices = PvRecorder.get_available_devices()
        if not devices:
            output.append("No audio devices found.")
        else:
            for i, device in enumerate(devices):
                output.append(f"Index [{i}]: {device}")
    except Exception as e:
        output.append(f"Error listing devices: {e}")
    output.append("-------------------------------")
    
    with open("audio_devices_log.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(output))
    print("Device list written to audio_devices_log.txt")

if __name__ == "__main__":
    list_devices()
