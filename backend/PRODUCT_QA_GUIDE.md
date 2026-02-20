# Product Q&A with Audio - Implementation Guide

## Overview
The **Product Q&A Engine** allows users to ask questions about products, with answers delivered via audio. It integrates:
- **STT (Speech-to-Text)**: Captures user questions from microphone
- **Product Data**: Searches through JSON product files from ad_engine
- **TTS (Text-to-Speech)**: Provides audio responses

---

## Features

### 1. **Interactive Q&A Sessions**
- Start a conversation about a specific product
- User asks questions via microphone (STT)
- System searches product data for relevant information
- System responds via audio (TTS)
- Multiple questions per session (configurable)

### 2. **Demo Mode (Text-Only)**
- Test without microphone
- Pre-defined questions
- Useful for development/testing

### 3. **Smart Product Search**
- Searches product fields: price, features, category, FAQs, description
- Keyword matching for intelligent responses
- Falls back to product description if no specific match

---

## File Structure

```
backend/
├── product_qa_engine.py          # Main Q&A engine
├── test_ad_engine.py             # Ad engine tests
├── modules/
│   ├── ad_engine/
│   │   ├── data/                 # Product JSON files
│   │   │   ├── 10-15_female.json
│   │   │   ├── 16-29_female.json
│   │   │   └── ... (12 products total)
│   │   ├── rules.json            # Ad selection rules
│   │   └── selector.py           # Ad selector class
│   └── interaction/
│       ├── stt_engine.py         # Speech-to-Text
│       ├── tts_engine.py         # Text-to-Speech
│       └── brain_engine.py       # AI reasoning
```

---

## Usage

### Method 1: Text-Only Demo (Recommended for Testing)

```bash
cd /Users/sahanadithya/Documents/GitHub/Adorix-project/backend
python3 product_qa_engine.py
```

**Output**: Interactive Q&A with predefined questions, no microphone needed.

---

### Method 2: Interactive Audio Session

```python
from product_qa_engine import ProductQAEngine

engine = ProductQAEngine()

# Start interactive session for a specific product
engine.start_qa_session(
    product_name="16-29_female",      # Product name (without .json)
    num_questions=3,                   # Allow 3 questions
    timeout=5                          # 5 second listening timeout
)
```

**Requirements**: Microphone must be connected and working.

---

### Method 3: Demo Mode with Custom Questions

```python
from product_qa_engine import ProductQAEngine

engine = ProductQAEngine()

questions = [
    "What is the price?",
    "What are the key features?",
    "Is it suitable for daily wear?"
]

engine.demo_mode("16-29_female", questions)
```

---

## API Reference

### ProductQAEngine Class

#### `__init__()`
Initializes the engine and loads all product data.

#### `start_qa_session(product_name, num_questions=3, timeout=5)`
Starts interactive Q&A with audio.

**Parameters:**
- `product_name` (str): Product JSON filename without extension
- `num_questions` (int): Maximum questions allowed
- `timeout` (int): Microphone listening timeout in seconds

**Returns:** Boolean (success/failure)

#### `demo_mode(product_name, questions)`
Runs Q&A with predefined questions (no microphone needed).

**Parameters:**
- `product_name` (str): Product JSON filename
- `questions` (list): List of question strings

**Returns:** Boolean (success/failure)

#### `get_answer(question, product_name)`
Gets an answer for a single question.

**Parameters:**
- `question` (str): User's question
- `product_name` (str): Product JSON filename (with or without .json)

**Returns:** String (answer text)

#### `search_product_info(question, product_name)`
Searches product data for relevant information.

**Parameters:**
- `question` (str): Question to search for
- `product_name` (str): Product JSON filename

**Returns:** List of matching information strings

---

## Available Products

The following products can be queried:

1. **10-15_female.json** - Products for 10-15 year old females
2. **10-15_male.json** - Products for 10-15 year old males
3. **16-29_female.json** - H&M Trend Capsule Outfit Set
4. **16-29_male.json** - Products for 16-29 year old males
5. **30-39_female.json** - Products for 30-39 year old females
6. **30-39_male.json** - Products for 30-39 year old males
7. **40-49_female.json** - Products for 40-49 year old females
8. **40-49_male.json** - Products for 40-49 year old males
9. **50-59_female.json** - Products for 50-59 year old females
10. **50-59_male.json** - Products for 50-59 year old males
11. **above-60_female.json** - Products for females above 60
12. **above-60_male.json** - Products for males above 60

---

## Search Capabilities

The engine searches for and responds to:

### Price Queries
**Keywords**: "price", "cost", "how much", "expense", "afford"
**Response**: Returns product price information

### Feature Queries
**Keywords**: "feature", "what", "include", "have", "comes with"
**Response**: Lists key features of the product

### Category Queries
**Keywords**: "what is", "category", "type", "what kind"
**Response**: Product category and brand information

### FAQ Queries
**Keywords**: Matches against FAQ keys in product data
**Response**: FAQ answers (e.g., size guide, care instructions)

### Generic Queries
**Default**: Returns product description if no specific match

---

## Flow Diagram

```
┌─────────────────────────────────────┐
│  Start Q&A Session                  │
├─────────────────────────────────────┤
│  Load Product Data (JSON files)     │
│  Play Introduction via TTS          │
└────────────┬────────────────────────┘
             │
             ▼
    ┌────────────────────┐
    │  Listen for Q (STT)│
    └────────┬───────────┘
             │
             ▼
    ┌────────────────────────────┐
    │  Search Product Data       │
    │  - Price keywords?         │
    │  - Features keywords?      │
    │  - Category keywords?      │
    │  - FAQ keywords?           │
    │  - Generic description     │
    └────────┬───────────────────┘
             │
             ▼
    ┌──────────────────────┐
    │  Generate Answer     │
    │  (max 200 chars)     │
    └────────┬─────────────┘
             │
             ▼
    ┌──────────────────────┐
    │  Speak Answer (TTS)  │
    └────────┬─────────────┘
             │
             ▼
    ┌──────────────────────────┐
    │  Questions Remaining?    │
    │  & Not Silent?           │
    └────────┬────────┬────────┘
             │        │
          Yes        No
             │        │
             ▼        ▼
        Loop    ┌──────────────────┐
               │  Play Goodbye    │
               │  Message (TTS)   │
               │  End Session     │
               └──────────────────┘
```

---

## Example Session

```
======================================================================
PRODUCT Q&A DEMO: H&M Trend Capsule Outfit Set
======================================================================

[Adorix]: Hello! I'm Adorix. I'm here to help you with questions about 
H&M Trend Capsule Outfit Set.

--- Question 1/3 ---
[You]: What is the price?
[Adorix]: The price is Rs. 6,900 - 19,900. Key features include: 
Mix-and-match capsule pieces for multiple outfits, Trendy fits with 
everyday comfort.

--- Question 2/3 ---
[You]: Is it suitable for daily wear?
[Adorix]: Yes, items like blazers and trousers work well for smart-casual 
settings. Yes, the fabrics are comfortable for long wear.

--- Question 3/3 ---
[You]: Do you have my size?
[Adorix]: I don't have specific information about that, but I'd be happy 
to tell you more about our products!

[Adorix]: Thanks for your interest! Have a great day!
```

---

## Requirements

### Python Packages
- `speech_recognition` - STT functionality
- `pyttsx3` - TTS functionality
- `torch` - AI/ML support
- `transformers` - NLP models

### Hardware
- **Microphone** (for audio sessions, not needed for demo mode)
- **Speaker/Headphones** (to hear TTS responses)

### Data Files
- Product JSON files in `modules/ad_engine/data/`
- Rules JSON in `modules/ad_engine/rules.json`

---

## Troubleshooting

### Issue: "Cannot find microphone"
**Solution**: Check microphone connection or run in demo mode:
```bash
python3 product_qa_engine.py  # Uses demo mode by default
```

### Issue: "Error loading products"
**Solution**: Verify JSON files exist in `modules/ad_engine/data/`

### Issue: "STT timeout / No response"
**Solution**: Increase timeout parameter:
```python
engine.start_qa_session(product_name="16-29_female", timeout=10)
```

### Issue: TTS not speaking
**Solution**: Check volume settings or verify `pyttsx3` is installed:
```bash
pip install pyttsx3
```

---

## Testing

Run the built-in demo:
```bash
cd backend
python3 product_qa_engine.py
```

All tests should complete with proper Q&A responses.

---

## Future Enhancements

1. **Multi-language Support** - Add support for multiple languages
2. **Sentiment Analysis** - Detect user satisfaction and adjust responses
3. **Learning** - Store common Q&A pairs for improvement
4. **Integration with Brain Engine** - Use TinyLlama for more sophisticated answers
5. **Audio Recording** - Record sessions for feedback/training
6. **Web API** - REST endpoints for frontend integration
