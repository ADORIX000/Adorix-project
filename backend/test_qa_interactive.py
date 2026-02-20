"""
Test 3: Interactive Q&A with Microphone
Tests the ProductQAEngine with audio input/output.
"""
from product_qa_engine import ProductQAEngine

def main():
    print("\n" + "="*70)
    print("INTERACTIVE Q&A TEST - TEST 3")
    print("="*70)
    
    print("\n📋 Prerequisites:")
    print("  ✓ Microphone is connected")
    print("  ✓ Speaker/Headphones available")
    
    import time
    time.sleep(3)
    
    # Initialize engine
    engine = ProductQAEngine()
    
    # Start interactive session
    try:
        success = engine.start_qa_session(
            product_name="16-29_female",
            num_questions=3,
            timeout=5
        )
        
        if success:
            print("\n✅ TEST 3 COMPLETED SUCCESSFULLY")
        else:
            print("\n⚠️  SESSION ENDED")
            
    except Exception as e:
        print(f"\n❌ TEST 3 FAILED: {str(e)}")

if __name__ == "__main__":
    main()