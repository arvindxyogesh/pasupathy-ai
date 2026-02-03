"""
Train a triplet neural network with BPE tokenizer for custom embeddings.
- Uses HuggingFace Tokenizers for BPE
- PyTorch for model and training
- Saves model and tokenizer for backend inference
"""
import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from transformers import AutoModel, AutoTokenizer
from tokenizers import ByteLevelBPETokenizer
from tqdm import tqdm
import json

# --- Config ---
PRETRAINED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
BPE_VOCAB_SIZE = 30000
MAX_LEN = 128
BATCH_SIZE = 16
EPOCHS = 3
LR = 2e-5
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# --- Data ---
class TripletTextDataset(Dataset):
    def __init__(self, triplets, tokenizer, max_len=MAX_LEN):
        self.triplets = triplets
        self.tokenizer = tokenizer
        self.max_len = max_len
    def __len__(self):
        return len(self.triplets)
    def __getitem__(self, idx):
        anchor, positive, negative = self.triplets[idx]
        return {
            'anchor': self.tokenizer(anchor, truncation=True, padding='max_length', max_length=self.max_len, return_tensors='pt'),
            'positive': self.tokenizer(positive, truncation=True, padding='max_length', max_length=self.max_len, return_tensors='pt'),
            'negative': self.tokenizer(negative, truncation=True, padding='max_length', max_length=self.max_len, return_tensors='pt'),
        }

def load_triplets(json_path):
    with open(json_path, 'r') as f:
        triplets = json.load(f)
    return triplets

# --- Model ---
class TripletEmbedder(nn.Module):
    def __init__(self, base_model_name, freeze_layers=6):
        super().__init__()
        self.encoder = AutoModel.from_pretrained(base_model_name)
        # Freeze some layers
        for i, layer in enumerate(self.encoder.encoder.layer):
            if i < freeze_layers:
                for param in layer.parameters():
                    param.requires_grad = False
        self.pool = nn.AdaptiveAvgPool1d(1)
    def forward(self, input_ids, attention_mask):
        output = self.encoder(input_ids=input_ids, attention_mask=attention_mask).last_hidden_state
        pooled = output.mean(dim=1)
        return pooled

def triplet_loss(anchor, positive, negative, margin=1.0):
    pos_dist = (anchor - positive).pow(2).sum(1)
    neg_dist = (anchor - negative).pow(2).sum(1)
    loss = torch.relu(pos_dist - neg_dist + margin)
    return loss.mean()

# --- Training ---
def train(model, dataloader, optimizer, epochs):
    model.train()
    for epoch in range(epochs):
        total_loss = 0
        for batch in tqdm(dataloader, desc=f"Epoch {epoch+1}"):
            optimizer.zero_grad()
            anchor = model(batch['anchor']['input_ids'].squeeze(1).to(DEVICE), batch['anchor']['attention_mask'].squeeze(1).to(DEVICE))
            positive = model(batch['positive']['input_ids'].squeeze(1).to(DEVICE), batch['positive']['attention_mask'].squeeze(1).to(DEVICE))
            negative = model(batch['negative']['input_ids'].squeeze(1).to(DEVICE), batch['negative']['attention_mask'].squeeze(1).to(DEVICE))
            loss = triplet_loss(anchor, positive, negative)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        print(f"Epoch {epoch+1} Loss: {total_loss/len(dataloader):.4f}")

# --- Main ---
def main():
    # 1. Train BPE tokenizer on your corpus (if not already trained)
    if not os.path.exists('bpe-vocab.json'):
        print("Training BPE tokenizer...")
        tokenizer = ByteLevelBPETokenizer()
        tokenizer.train(files=["corpus.txt"], vocab_size=BPE_VOCAB_SIZE, min_frequency=2)
        tokenizer.save_model('.', 'bpe')
    # 2. Load BPE tokenizer
    print("Loading BPE tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(PRETRAINED_MODEL)
    # 3. Load triplet data
    triplets = load_triplets('triplets.json')
    dataset = TripletTextDataset(triplets, tokenizer)
    dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)
    # 4. Model
    model = TripletEmbedder(PRETRAINED_MODEL).to(DEVICE)
    optimizer = optim.AdamW(model.parameters(), lr=LR)
    # 5. Train
    train(model, dataloader, optimizer, EPOCHS)
    # 6. Save model
    torch.save(model.state_dict(), 'triplet_embedder.pt')
    print("Model saved as triplet_embedder.pt")

if __name__ == "__main__":
    main()
