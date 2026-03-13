"""
Adorix Interaction Pipeline Diagnostic Test
Tests the full: STT -> QA Engine -> Brain Engine -> TTS flow.
Run from the backend/ directory:
    python test_interaction.py
"""
import os
import sys
import time

# Ensure backend/ root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DIVIDER = "=" * 58

def print_header(step, title):
    print(f"\n{DIVIDER}")
    print(f"  [{step}] {title}")
    print(DIVIDER)

# ─────────────────────────────────────────────────────────
#  1. TTS ENGINE TEST
# ─────────────────────────────────────────────────────────
def test_tts():
    print_header("1/4", "TTS Engine (Text-to-Speech)")
    try:
        from modules.interaction.tts_engine import speak
        print("  Speaking test phrase...")
        speak("Hello! I am Adorix. This is a TTS test.")
        print("  [OK] TTS test passed.")
        return True
    except Exception as e:
        print(f"  [FAIL] TTS error: {e}")
        return False

# ─────────────────────────────────────────────────────────
#  2. STT ENGINE TEST
# ─────────────────────────────────────────────────────────
def test_stt():
    print_header("2/4", "STT Engine (Speech-to-Text)")
    try:
        from modules.interaction.stt_engine import listen_one_phrase
        print("  Microphone will listen for 7 seconds.")
        print("  >>> PLEASE SPEAK A QUESTION NOW <<<")
        text = listen_one_phrase(timeout=7)
        if text:
            print(f"  [OK] STT captured: \"{text}\"")
            return text
        else:
            print("  [WARN] No speech detected (silence or mic issue).")
            return None
    except Exception as e:
        print(f"  [FAIL] STT error: {e}")
        return None

# ─────────────────────────────────────────────────────────
#  3. QA ENGINE TEST
# ─────────────────────────────────────────────────────────
def test_qa_engine(question, ad_name):
    print_header("3/4", f"QA Engine — Product: {ad_name}")
    try:
        from product_qa_engine import ProductQAEngine
        engine = ProductQAEngine()
        print(f"  Question : \"{question}\"")
        answer = engine.get_answer(question, ad_name)
        print(f"  QA Answer: \"{answer}\"")
        
        if "don't have" in answer.lower() or "sorry" in answer.lower():
            print("  [INFO] QA had no exact match → will fall back to LLM.")
        else:
            print("  [OK] QA Engine matched successfully!")
        return answer
    except Exception as e:
        print(f"  [FAIL] QA Engine error: {e}")
        return None

# ─────────────────────────────────────────────────────────
#  4. BRAIN ENGINE TEST (TinyLlama)
# ─────────────────────────────────────────────────────────
def test_brain_engine(question, ad_name):
    print_header("4/4", "Brain Engine (TinyLlama LLM)")
    try:
        from modules.interaction.brain_engine import adorix_brain
        print(f"  Loading context for: {ad_name}")
        context = adorix_brain.load_context_from_json(f"{ad_name}.json")
        if not context:
            print(f"  [FAIL] No context found for {ad_name}.json")
            return None
        print(f"  Context: {context[:120]}...")
        print(f"\n  Generating answer for: \"{question}\"")
        start = time.time()
        answer = adorix_brain.generate_answer(question, context)
        elapsed = time.time() - start
        print(f"  Brain Answer ({elapsed:.1f}s): \"{answer}\"")
        print("  [OK] Brain Engine responded successfully!")
        return answer
    except Exception as e:
        print(f"  [FAIL] Brain Engine error: {e}")
        return None

# ─────────────────────────────────────────────────────────
#  5. FULL PIPELINE TEST
# ─────────────────────────────────────────────────────────
def test_full_pipeline(ad_name, use_live_stt=True):
    print(f"\n{'#'*58}")
    print(f"  FULL PIPELINE TEST  |  Ad: {ad_name}")
    print(f"{'#'*58}")

    from modules.interaction.tts_engine import speak
    from modules.interaction.interaction_manager import get_hybrid_answer

    question = None
    if use_live_stt:
        from modules.interaction.stt_engine import listen_one_phrase
        print("\n  Adorix is greeting you...")
        speak("Hello! I'm Adorix. Please ask me a question about this product.")
        print("  >>> PLEASE SPEAK YOUR QUESTION <<<")
        question = listen_one_phrase(timeout=8)

    if not question:
        print("  No live speech — using preset question for demo.")
        question = "What is this product and who is it for?"

    print(f"\n  User Asked : \"{question}\"")
    print("  Processing with hybrid QA → LLM...")

    answer = get_hybrid_answer(question, ad_name)
    print(f"  Final Answer: \"{answer}\"")

    print("\n  Speaking the answer via TTS...")
    speak(answer)
    print("  [OK] Full pipeline complete!")

# ─────────────────────────────────────────────────────────
#  MAIN MENU
# ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    # List available ad products
    data_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "modules", "ad_engine", "data"
    )
    available_ads = [f.replace(".json", "") for f in os.listdir(data_dir) if f.endswith(".json")]

    print(DIVIDER)
    print("  ADORIX INTERACTION PIPELINE DIAGNOSTIC")
    print(DIVIDER)
    print("\nAvailable product profiles:")
    for i, a in enumerate(available_ads):
        print(f"  [{i}] {a}")

    print("""
Select a test to run:
  [1] TTS Test only
  [2] STT Test only  
  [3] QA Engine Test (text input)
  [4] Brain Engine Test (text input)
  [5] Full Pipeline Test (live mic + all engines)
  [6] Full Pipeline Test (no mic — uses preset question)
""")

    choice = input("Enter choice (1-6): ").strip()

    # Choose ad profile
    ad_choice = input(f"\nEnter ad number (0-{len(available_ads)-1}) [default: 0]: ").strip()
    try:
        ad_name = available_ads[int(ad_choice)]
    except:
        ad_name = available_ads[0]
    print(f"\nUsing product: {ad_name}\n")

    if choice == "1":
        test_tts()

    elif choice == "2":
        result = test_stt()
        print(f"\nCaptured: {result}")

    elif choice == "3":
        q = input("Enter your question: ").strip() or "What is this product?"
        test_qa_engine(q, ad_name)

    elif choice == "4":
        q = input("Enter your question: ").strip() or "What is this product?"
        test_brain_engine(q, ad_name)

    elif choice == "5":
        test_full_pipeline(ad_name, use_live_stt=True)

    elif choice == "6":
        test_full_pipeline(ad_name, use_live_stt=False)

    else:
        print("Invalid choice. Exiting.")

    print(f"\n{DIVIDER}")
    print("  Diagnostic complete.")
    print(DIVIDER)
