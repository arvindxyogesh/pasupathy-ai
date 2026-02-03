import os
import torch
from transformers import AutoTokenizer
from tokenizers import ByteLevelBPETokenizer

class CustomTripletEmbedder:
    def __init__(self, model_path, base_model_name, bpe_vocab_path=None, bpe_merges_path=None, device=None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        # Load model
        from train_triplet_embedder import TripletEmbedder
        self.model = TripletEmbedder(base_model_name)
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.eval()
        self.model.to(self.device)
        # Load tokenizer
        if bpe_vocab_path and bpe_merges_path:
            self.tokenizer = ByteLevelBPETokenizer(bpe_vocab_path, bpe_merges_path)
        else:
            self.tokenizer = AutoTokenizer.from_pretrained(base_model_name)
        self.max_len = 128

    def embed(self, texts):
        if isinstance(texts, str):
            texts = [texts]
        # Tokenize
        encodings = self.tokenizer(texts, truncation=True, padding='max_length', max_length=self.max_len, return_tensors='pt')
        input_ids = encodings['input_ids'].to(self.device)
        attention_mask = encodings['attention_mask'].to(self.device)
        with torch.no_grad():
            embeddings = self.model(input_ids, attention_mask)
        return embeddings.cpu().numpy()
