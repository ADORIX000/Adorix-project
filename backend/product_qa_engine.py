"""
Product Q&A with Audio Module
Handles user questions about products using:
- STT (Speech-to-Text) to capture questions
- Product data from ad_engine
- TTS (Text-to-Speech) to provide audio answers
"""

import os
import sys
import json
from pathlib import Path

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.ad_engine import AdSelector
# imports deferred to prevent circular dependency


class ProductQAEngine:
    """
    Handles product Q&A with audio I/O.
    Searches through product data and provides answers via TTS.
    """
    
    def __init__(self):
        self.rules_path = os.path.join(
            os.path.dirname(__file__),
            "modules/ad_engine/rules.json"
        )
        self.ads_dir = os.path.join(
            os.path.dirname(__file__),
            "modules/ad_engine/data"
        )
        self.selector = AdSelector(self.rules_path, self.ads_dir)
        self.product_data = {}
        self._load_all_products()
    
    def _load_all_products(self):
        """Load all product JSON files into memory."""
        print("Loading product database...")
        try:
            for filename in os.listdir(self.ads_dir):
                if filename.endswith(".json"):
                    filepath = os.path.join(self.ads_dir, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        self.product_data[filename] = json.load(f)
            print(f"✓ Loaded {len(self.product_data)} products")
        except Exception as e:
            print(f"Error loading products: {e}")
    
    def search_product_info(self, question, product_name):
        """
        Search product data for relevant information.
        Returns matching info from the product JSON.
        """
        if product_name not in self.product_data:
            return None
        
        product = self.product_data[product_name]
        question_lower = question.lower()
        
        # Search through product fields
        searchable_fields = {
            'product_name': product.get('product_name', ''),
            'brand': product.get('brand', ''),
            'category': product.get('category', ''),
            'price': product.get('price', ''),
            'description': product.get('description', ''),
            'key_features': ' '.join(product.get('key_features', [])),
            'faqs': self._format_faqs(product.get('faqs', {}))
        }
        
        results = []
        
        # Check for price-related questions
        if any(word in question_lower for word in ['price', 'cost', 'how much', 'expense', 'afford']):
            results.append(f"The price is {product.get('price', 'not available')}.")
        
        # Check for feature/benefit questions
        if any(word in question_lower for word in ['feature', 'what', 'include', 'have', 'comes with']):
            features = product.get('key_features', [])
            if features:
                results.append(f"Key features include: {', '.join(features[:2])}.")
        
        # Check for category/type questions
        if any(word in question_lower for word in ['what is', 'category', 'type', 'what kind']):
            category = product.get('category', '')
            if category:
                results.append(f"This is a {category} product by {product.get('brand', 'brand')}.")
        
        # Check for FAQ matches
        faqs = product.get('faqs', {})
        for faq_key, faq_value in faqs.items():
            if any(word in question_lower for word in faq_key.lower().split('_')):
                results.append(faq_value)
        
        # Generic description fallback
        if not results:
            desc = product.get('description', '')
            if desc:
                results.append(desc)
        
        return results
    
    def _format_faqs(self, faqs_dict):
        """Convert FAQ dict to searchable string."""
        return ' '.join([f"{k}: {v}" for k, v in faqs_dict.items()])
    
    def get_answer(self, question, product_name):
        """
        Get a conversational answer based on product data.
        """
        if not question or not product_name:
            return "I didn't catch that. Could you repeat your question?"
        
        results = self.search_product_info(question, product_name)
        
        if results:
            # Combine top 2 results for comprehensive answer
            answer = " ".join(results[:2])
            return answer[:200]  # Limit to reasonable length for TTS
        else:
            return f"I don't have specific information about that, but I'd be happy to tell you more about our products!"
    
    def start_qa_session(self, product_name, num_questions=3, timeout=5):
        """
        Start an interactive Q&A session for a specific product.
        
        Args:
            product_name: Name of the product JSON file (without .json)
            num_questions: Number of questions to allow (default 3)
            timeout: Listening timeout in seconds
        """
        if not product_name.endswith('.json'):
            product_name = product_name + '.json'
        
        if product_name not in self.product_data:
            from modules.interaction.tts_engine import speak
            speak(f"Sorry, I don't have information about that product.")
            return False
        
        product = self.product_data[product_name]
        product_display = product.get('product_name', product_name)
        
        print("\n" + "="*70)
        print(f"PRODUCT Q&A SESSION: {product_display}")
        print("="*70)
        
        # Introduction
        intro = f"Hello! I'm Adorix. I'm here to help you with questions about {product_display}. Feel free to ask me anything!"
        print(f"\n[Adorix]: {intro}")
        from modules.interaction.tts_engine import speak
        speak(intro)
        
        # Q&A loop
        questions_asked = 0
        while questions_asked < num_questions:
            print(f"\n--- Question {questions_asked + 1}/{num_questions} ---")
            print(f"[System] Listening for your question (timeout: {timeout}s)...")
            
            from modules.interaction.stt_engine import listen_one_phrase
            user_question = listen_one_phrase(timeout=timeout)
            
            if user_question is None:
                print("[System] Silence detected. Session ending.")
                closing = "No more questions? Have a great day!"
                print(f"\n[Adorix]: {closing}")
                from modules.interaction.tts_engine import speak
                speak(closing)
                return True
            
            print(f"[You]: {user_question}")
            
            # Get and provide answer
            answer = self.get_answer(user_question, product_name)
            print(f"\n[Adorix]: {answer}")
            from modules.interaction.tts_engine import speak
            speak(answer)
            
            questions_asked += 1
        
        # Closing message
        closing = "Thanks for all the questions! I hope you're interested in our product. Have a wonderful day!"
        print(f"\n[Adorix]: {closing}")
        speak(closing)
        
        return True
    
    def demo_mode(self, product_name, questions):
        """
        Demo mode: Simulate Q&A without actual listening.
        Useful for testing without microphone.
        """
        if not product_name.endswith('.json'):
            product_name = product_name + '.json'
        
        if product_name not in self.product_data:
            print(f"Error: Product {product_name} not found")
            return False
        
        product = self.product_data[product_name]
        product_display = product.get('product_name', product_name)
        
        print("\n" + "="*70)
        print(f"PRODUCT Q&A DEMO: {product_display}")
        print("="*70)
        
        # Introduction
        intro = f"Hello! I'm Adorix. I'm here to help you with questions about {product_display}."
        print(f"\n[Adorix]: {intro}\n")
        
        # Q&A loop
        for i, question in enumerate(questions, 1):
            print(f"--- Question {i}/{len(questions)} ---")
            print(f"[You]: {question}")
            
            answer = self.get_answer(question, product_name)
            print(f"[Adorix]: {answer}\n")
        
        # Closing
        closing = "Thanks for your interest! Have a great day!"
        print(f"[Adorix]: {closing}\n")
        
        return True


def demo_qa_with_audio():
    """Demonstrate Q&A with audio for a specific product."""
    engine = ProductQAEngine()
    
    # Choose a product (16-29_female.json in this case)
    product_name = "16-29_female"
    
    # Start interactive session (with 2 questions max)
    engine.start_qa_session(product_name, num_questions=2, timeout=5)


def demo_qa_text_only():
    """Demonstrate Q&A without audio (text-based)."""
    engine = ProductQAEngine()
    
    # Sample questions
    questions = [
        "What is the price?",
        "What are the key features?",
        "What category is this product?",
        "Is it suitable for daily wear?"
    ]
    
    # Demo mode with predefined questions
    engine.demo_mode("16-29_female", questions)


if __name__ == "__main__":
    print("Product Q&A Engine - Test Mode\n")
    print("Running text-only demo (no audio required)...")
    demo_qa_text_only()
    
    print("\n" + "="*70)
    print("To use with audio, uncomment the line below and have a microphone ready:")
    print("# demo_qa_with_audio()")
    print("="*70)
