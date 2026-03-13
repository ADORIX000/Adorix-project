import sentencepiece as spm
import os

def encode_keyword(text, model_path):
    sp = spm.SentencePieceProcessor(model_file=model_path)
    # The sherpa-onnx KWS expected format is space-separated pieces
    pieces = sp.encode_as_pieces(text)
    # Replace the actual space character with the special one if needed, 
    # but encode_as_pieces already uses U+2581
    return " ".join(pieces)

if __name__ == "__main__":
    model_path = "modules/wake_word/models/sherpa-onnx-kws-zipformer-gigaspeech-3.3M-2024-01-01/bpe.model"
    kw = "HEY ADORIX"
    encoded = encode_keyword(kw, model_path)
    print(f"Encoded: {encoded}")
    
    # Save to file
    with open("modules/wake_word/models/keywords.txt", "w", encoding="utf-8") as f:
        f.write(encoded + "\n")
    print("Saved to modules/wake_word/models/keywords.txt")
