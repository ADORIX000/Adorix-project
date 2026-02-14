import json
import torch
import os
from transformers import pipeline

class BrainEngine:
    def __init__(self):
        print("🧠 Loading TinyLlama... (This might take a minute)")
        self.pipe = pipeline(
            "text-generation", 
            model="TinyLlama/TinyLlama-1.1B-Chat-v1.0", 
            torch_dtype=torch.bfloat16, 
            device_map="auto" 
        )
        print("✅ TinyLlama loaded successfully!")

    def generate_answer(self, user_question, context):
        """Uses TinyLlama to answer based ONLY on the provided context string."""
        
        if not context:
            return "I'm sorry, I don't have enough information to answer that right now."

        # 2. Strict Prompt Engineering (RAG format)
        # We explicitly tell it to ONLY use the context.
        messages = [
            {
                "role": "system",
                "content": (
                    "You are ADORIX, a helpful kiosk assistant. "
                    "You must answer the user's question using ONLY the provided Context. "
                    "Keep your answer short, conversational, and direct. "
                    "If the answer is not in the Context, say 'I am not sure about that'."
                )
            },
            {
                "role": "user",
                "content": f"Context: {context}\n\nQuestion: {user_question}"
            },
        ]

        # 3. Format for TinyLlama
        prompt = self.pipe.tokenizer.apply_chat_template(
            messages, 
            tokenize=False, 
            add_generation_prompt=True
        )
        
        # 4. Generate the Answer
        outputs = self.pipe(
            prompt, 
            max_new_tokens=50,   
            do_sample=True, 
            temperature=0.1,  # Keep temperature very low (0.1) so it doesn't invent fake colors
            top_k=50, 
            top_p=0.95
        )

        generated_text = outputs[0]["generated_text"]
        # Split the text to only get the AI's response part
        answer = generated_text.split("<|assistant|>")[-1].strip()
        
        return answer

# --- GLOBAL INSTANCE ---
adorix_brain = BrainEngine()

def get_answer_from_data(user_question, context):
    """Wrapper function to be called by your interaction_manager"""
    return adorix_brain.generate_answer(user_question, context)

# --- TEST CODE (Run this directly to check if it reads the JSON) ---
if __name__ == "__main__":
    print("\n--- Testing JSON RAG Engine ---")
    
    # Simulate the user looking at the Nike Ad
    ad_playing_on_screen = "Nike Ad" 
    
    question = "what are the available colours"
    print(f"User asks: '{question}' while watching '{ad_playing_on_screen}'")
    
    final_answer = get_answer_from_data(question, ad_playing_on_screen)
    print(f"\n🤖 ADORIX Replies: {final_answer}")