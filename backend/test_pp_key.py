import pvporcupine
import sys

def test_porcupine():
    ACCESS_KEY = "Mq/t/eYybihg3oyZrgu8SIv4jujAh7KeELbD7EepxuQjl4R31pdvmA==" 
    print(f"Testing Porcupine with Access Key: {ACCESS_KEY[:10]}...")
    try:
        handle = pvporcupine.create(access_key=ACCESS_KEY, keywords=['porcupine'])
        print("[OK] Porcupine initialized successfully with built-in keyword!")
        handle.delete()
    except Exception as e:
        print(f"[FAIL] Porcupine initialization failed: {e}")

if __name__ == "__main__":
    test_porcupine()
