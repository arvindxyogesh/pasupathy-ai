# Custom Triplet Embedder Training

This module lets you train a custom embedding model using:
- **BPE (Byte Pair Encoding) tokenizer**
- **Triplet neural network** (anchor, positive, negative)
- **Partial layer freezing** for transfer learning

## Files
- `train_triplet_embedder.py` — Main training script
- `triplets.json` — Your triplet data: `[[anchor, positive, negative], ...]`
- `corpus.txt` — Raw text corpus for BPE training (optional)
- `bpe-vocab.json`, `bpe-merges.txt` — Saved BPE tokenizer files
- `triplet_embedder.pt` — Trained model weights

## How to Use

1. **Prepare Data**
   - `triplets.json`: List of `[anchor, positive, negative]` text triplets
   - `corpus.txt`: (Optional) Large text file for BPE training

2. **Train**
   ```bash
   cd backend/custom_embedder
   python train_triplet_embedder.py
   ```
   - Trains BPE tokenizer (if not present)
   - Trains/fine-tunes embedding model with triplet loss
   - Saves model and tokenizer

3. **Integrate in Backend**
   - Load `triplet_embedder.pt` and BPE tokenizer in your Flask app
   - Use for embedding new queries/documents

## Requirements
- torch
- transformers
- tokenizers
- tqdm

Add to `backend/requirements.txt`:
```
torch
transformers
tokenizers
tqdm
```

## Notes
- Freezes first 6 layers of the transformer by default (configurable)
- Uses mean pooling for sentence embedding
- You can further tune or extend the model as needed
