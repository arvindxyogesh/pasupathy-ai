"""
Batch-by-batch dataset improver for large JSONL/JSON datasets.
Processes the dataset in chunks, deduplicates, normalizes, and expands Q&A pairs.
Usage: python dataset_batch_improver.py --input data/arvind_personal_llm_dataset_mongo.json --output data/arvind_personal_llm_dataset_mongo_improved.json --batch_size 10000
"""
import json
import argparse
from tqdm import tqdm

def normalize_text(text):
    return text.strip().replace("\n", " ").replace("  ", " ")

def improve_qa_pair(qa):
    # Expand, clarify, and normalize Q&A
    q = normalize_text(qa.get("prompt", ""))
    a = normalize_text(qa.get("response", ""))
    # Example: add more context, deduplicate, or rewrite
    # (You can add more advanced logic or LLM calls here)
    return {"prompt": q, "response": a}

def process_batch(batch):
    seen = set()
    improved = []
    for qa in batch:
        improved_qa = improve_qa_pair(qa)
        key = (improved_qa["prompt"].lower(), improved_qa["response"].lower())
        if key not in seen:
            improved.append(improved_qa)
            seen.add(key)
    return improved

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--batch_size', type=int, default=10000)
    args = parser.parse_args()

    with open(args.input, 'r') as f:
        data = json.load(f)

    total = len(data)
    improved_all = []
    for i in tqdm(range(0, total, args.batch_size)):
        batch = data[i:i+args.batch_size]
        improved = process_batch(batch)
        improved_all.extend(improved)

    with open(args.output, 'w') as f:
        json.dump(improved_all, f, indent=2)

if __name__ == "__main__":
    main()
