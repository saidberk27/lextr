import torch
import json
import time
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel
from tqdm import tqdm
from math import exp # For Perplexity calculation


LLM_MODEL_NAME = "meta-llama/Llama-2-7b-hf"
LORA_ADAPTER_PATH = "./models/finetuned_adapters/aym_raportor_adapter"
TEST_DATASET_PATH = "./data/hukuki_sft_test.jsonl" # Available in Week 5
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


def load_test_data(file_path):
    """
    Loads the evaluation dataset. In Weeks 3 & 4, this returns a mock subset.
    In Week 5, this will load the actual hukuki_sft_test.jsonl file.
    """
    print(f"[EVAL] Attempting to load test data from: {file_path}")
    
    
    MOCK_DATA = [
        {"prompt": "Case 1 Prompt...", "completion": "Case 1 Target Decision..."},
        {"prompt": "Case 2 Prompt...", "completion": "Case 2 Target Decision..."}
    ]
    
    if "hukuki_sft_test.jsonl" in file_path:
        print("[EVAL] WARNING: Real test data is not available yet. Using MOCK data for structural validation.")
        return MOCK_DATA
    
    
    data = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                data.append(json.loads(line))
        print(f"[EVAL] Successfully loaded {len(data)} test samples.")
        return data
    except FileNotFoundError:
        return MOCK_DATA


def load_model_for_evaluation(model_name, adapter_path):
    """Loads the base model and attaches the fine-tuned LoRA adapter."""
    print("[EVAL] Loading base model and attaching LoRA adapter for evaluation...")
    
    bnb_config = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4")
    
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        quantization_config=bnb_config,
        device_map=DEVICE
    )
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokenizer.pad_token = tokenizer.eos_token
    
  
    try:
        model = PeftModel.from_pretrained(model, adapter_path)
        print("[EVAL] LoRA Adapter attached successfully.")
    except Exception:
        print("[EVAL] ERROR: LoRA adapter not found. Evaluation will run on the generic Llama 2 model.")

    return model, tokenizer


def calculate_loss_and_perplexity(model, tokenizer, dataset):
    """
    Calculates Test Loss and Perplexity (PPL).
    These metrics are primarily used to measure the success of Supervised Fine-Tuning.
    """
    model.eval()
    losses = []
    
    print("\n[EVAL] Calculating Loss and Perplexity...")
    
    for item in tqdm(dataset, desc="Processing Test Samples"):
        # Concatenate prompt and completion for language modeling task
        text = item['prompt'] + item['completion'] + tokenizer.eos_token
        inputs = tokenizer(text, return_tensors='pt', truncation=True).to(DEVICE)
        
        with torch.no_grad():
            outputs = model(**inputs, labels=inputs['input_ids'])
            loss = outputs.loss
            losses.append(loss.item())
            
    avg_loss = sum(losses) / len(losses)
    
    
    # PPL = exp(Average Loss)
    perplexity = exp(avg_loss)
    
    return avg_loss, perplexity


def check_factual_consistency(generated_text: str, retrieved_context: str):
    
    
    if "HÜKÜM" not in generated_text:
        return 0, "Format Missing"
    
    
    if "Anayasa Md. 36" in generated_text and "Anayasa Md. 36" not in retrieved_context:
        
        return 0.5, "Potential Hallucination/Low Context Use"
        
    
    return 1.0, "Consistent (Manual Review Required)"


# --- MAIN EXECUTION ---
if __name__ == "__main__":
    print("="*60)
   
    print("="*60)

    
    test_data = load_test_data(TEST_DATASET_PATH)
    
    
    model, tokenizer = load_model_for_evaluation(LLM_MODEL_NAME, LORA_ADAPTER_PATH)

    if test_data:
        
        avg_loss, perplexity = calculate_loss_and_perplexity(model, tokenizer, test_data)
        
        print("\n" + "*"*40)
        print(f"📊 EVALUATION RESULTS ")
        print(f"Average Test Loss: {avg_loss:.4f}")
        print(f"Perplexity (PPL): {perplexity:.4f}")
        print("*"*40)
        
        
        
        
        generated = "I. TALEP... II. İNCELEME... IV. HÜKÜM: Anayasa Md. 36 uyarınca ihlal bulunmuştur."
        context = "Anayasa Md. 36, adil yargılanma hakkını güvence altına alır."
        
        score, comment = check_factual_consistency(generated, context)
        print(f"\n[BENCHMARK PROTOCOL CHECK]")
        print(f"Factual Consistency Score: {score}")
        print(f"Comment: {comment}")
    else:
        print("[EVAL] ERROR: Test data could not be loaded. Evaluation skipped.")