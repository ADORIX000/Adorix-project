import os
import sys
import json

# Add backend and modules to path
project_root = r"c:\Users\deegh\OneDrive\Desktop\DEE\GitHUB\Adorix-project"
backend_dir = os.path.join(project_root, "backend")
modules_dir = os.path.join(backend_dir, "modules")
sys.path.insert(0, backend_dir)
sys.path.insert(0, modules_dir)

from modules.interaction.brain_engine import adorix_brain

def test_brain():
    print("=== Adorix Brain Verification ===")
    
    # Test with an existing product
    product_json = "30-39_male.json"
    print(f"Loading context for: {product_json}")
    
    # Manually check if path is correct
    base_dir = os.path.join(backend_dir, "modules")
    json_path = os.path.join(base_dir, "ad_engine", "data", product_json)
    
    if os.path.exists(json_path):
        print(f"Found product data at: {json_path}")
    else:
        print(f"ERROR: Product data not found at {json_path}")
        return

    context = adorix_brain.load_context_from_json(product_json)
    if not context:
        print("ERROR: Failed to load context.")
        return
    
    print(f"Context loaded (length: {len(context)})")
    
    question = "What are the key features of the iPhone 17?"
    print(f"Asking AI: '{question}'")
    
    answer = adorix_brain.generate_answer(question, context)
    print(f"\nAI Answer: {answer}")
    print("================================")

if __name__ == "__main__":
    test_brain()
