import os

# 1. Force Hugging Face to use D: drive for temporary caching BEFORE importing datasets
os.environ["HF_HOME"] = r"D:\AgenticXBorder\hf_cache"
os.environ["HF_DATASETS_CACHE"] = r"D:\AgenticXBorder\hf_cache"

from datasets import load_dataset

# 2. Define target folders on D: drive
output_dir = r"D:\AgenticXBorder\docvqa_samples"
cache_dir = r"D:\AgenticXBorder\hf_cache"

os.makedirs(output_dir, exist_ok=True)
os.makedirs(cache_dir, exist_ok=True)

print("[DOCVQA] Downloading dataset entirely on D: drive...")

# 3. Load dataset with explicit cache_dir directed to D: drive
dataset = load_dataset(
    "lmms-lab-encoder/DocVQA", 
    "DocVQA", 
    split="validation", 
    streaming=False, 
    cache_dir=cache_dir
)

print(f"\n[SUCCESS] Downloaded validation split ({len(dataset)} items). Extracting images to '{output_dir}'...")

# 4. Save all extracted images into docvqa_samples on D: drive
for i, sample in enumerate(dataset):
    img = sample["image"]
    filename = os.path.join(output_dir, f"docvqa_val_{i+1:04d}.png")
    img.save(filename)
    
    if (i + 1) % 100 == 0 or (i + 1) == len(dataset):
        print(f"[{i+1}/{len(dataset)}] Saved: {filename}")

print(f"\nCompleted! All DocVQA validation images are stored in '{output_dir}'.")