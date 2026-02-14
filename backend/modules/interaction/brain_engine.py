import json
import os
import torch
from transformers import pipeline

class BrainEngine:
    def __init__(self):
        """
        Initializes the AI Brain using TinyLlama for RAG.
        """
        print("🧠 [Brain] Loading AI Engine (TinyLlama)...")
        # Initialize the text-generation pipeline
        # We use float16 and low_cpu_mem_usage for faster loading and less memory
        self.pipe = pipeline(
            "text-generation",
            model="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
            model_kwargs={
                "torch_dtype": torch.float16,
                "low_cpu_mem_usage": True,
            },
            device_map="auto"
        )
        print("✅ [Brain] AI Engine loaded successfully.")

    def load_context_from_json(self, json_filename):
        """
        Loads the product description context from a specific JSON file.
        """
        # Ensure the filename has .json extension
        if not json_filename.endswith(".json"):
            json_filename += ".json"
            
        # Path: backend/modules/interaction/data/{json_filename}
        base_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(base_dir, "data", json_filename)
        
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
                # We expect the JSON to have a "context" field
                context = data.get("context", "")
                product_name = data.get("product", "this product")
                print(f">>> [Brain] Loaded knowledge for: {product_name}")
                return context
        except FileNotFoundError:
            print(f"!!! [Brain] Error: Knowledge file {json_path} not found.")
            return None
        except Exception as e:
            print(f"!!! [Brain] Error loading JSON: {e}")
            return None

    def generate_answer(self, user_question, context):
        """
        Generates a concise answer based ONLY on the provided context.
        """
        if not context:
            return "I'm sorry, I don't have enough information about that right now."

        import time
        start_time = time.time()
        
        # Construct a strict prompt for RAG
        messages = [
            {
                "role": "system",
                "content": (
                    "You are Adorix, a friendly AI kiosk assistant. "
                    "Use ONLY the following context to answer the user's question. "
                    "Keep your response very short (1-2 sentences), conversational, and informative. "
                    "If the answer is not in the context, say 'I'm sorry, I don't have that information'."
                )
            },
            {
                "role": "user",
                "content": f"Context: {context}\n\nQuestion: {user_question}"
            }
        ]

        try:
            # Use the chat template provided by the model tokenizer
            prompt = self.pipe.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )

            # Generate response
            outputs = self.pipe(
                prompt,
                max_new_tokens=80,
                do_sample=True,
                temperature=0.1, # Even lower for consistency
                top_k=50,
                top_p=0.9
            )

            # Extract answer from generated text
            full_text = outputs[0]["generated_text"]
            
            # TinyLlama implementation of apply_chat_template usually ends with <|assistant|>
            if "<|assistant|>" in full_text:
                answer = full_text.split("<|assistant|>")[-1].strip()
            else:
                # Fallback if template markers are missing
                answer = full_text.split(user_question)[-1].strip()

            # Remove common prefixes if they appear
            for prefix in ["Answer:", "Response:", "Adorix:"]:
                if answer.startswith(prefix):
                    answer = answer[len(prefix):].strip()

            end_time = time.time()
            print(f">>> [Brain] Answer generated in {end_time - start_time:.2f}s")
            return answer
        except Exception as e:
            print(f"!!! [Brain] Generation error: {e}")
            return "I'm sorry, I encountered an error while thinking about your question."

# Global instance
adorix_brain = BrainEngine()

def get_answer_for_product(user_question, json_file):
    """
    Wrapper function called by the interaction manager.
    """
    context = adorix_brain.load_context_from_json(json_file)
    return adorix_brain.generate_answer(user_question, context)

if __name__ == "__main__":
    # Test script: Create a dummy JSON first
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    os.makedirs(data_dir, exist_ok=True)
    
    test_data = {
        "product": "Adorix Kiosk",
        "context": "Adorix is a futuristic AI kiosk with a 3D avatar. It provides personalized product recommendations and costs 1,000 USD."
    }
    with open(os.path.join(data_dir, "test_ad.json"), 'w') as f:
        json.dump(test_data, f)
        
    print("Testing Brain Engine...")
    ans = get_answer_for_product("How much does the kiosk cost?", "test_ad.json")
    print(f"AI Answer: {ans}")