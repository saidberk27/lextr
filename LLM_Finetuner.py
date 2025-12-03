import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model
from trl import SFTTrainer, TrainingArguments
from datasets import load_dataset, Dataset
import json
from Data_Formatter import SYSTEM_PROMPT


MODEL_NAME = "llama2" 
TRAINING_FILE = "Sft_train.jsonl"
OUTPUT_DIR = "./finetuned_model"

# LoRA (Low-Rank Adaptation) Ayarları (Hafif İnce Ayar)

lora_config = LoraConfig(
    r=8,                   
    lora_alpha=16,         
    target_modules=["q_proj", "v_proj"], 
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)

# 4-bit QLoRA konfigürasyonu bellek kullanımını düşürür.
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16,
)




# JSONL dosyası Hugging Face Dataset formatına yüklenir.
def formatting_func(example):
    text = f"### Sistem Talimatı: {SYSTEM_PROMPT}\n\n### Girdi:\n{example['prompt']}\n\n### Çıktı:\n{example['completion']}"
    return {"text": text}

# Gerçek dosya adı yok şu an
dataset = load_dataset("json", data_files=TRAINING_FILE, split="train") 
dataset = dataset.map(formatting_func, remove_columns=dataset.column_names)

#  Model ve Tokenizer yüklenir
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
tokenizer.pad_token = tokenizer.eos_token 

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    quantization_config=bnb_config,
    torch_dtype=torch.float16,
    device_map="auto"
)
model.config.use_cache = False #  bellek kullanımı azaltılır


model = get_peft_model(model, lora_config)
print(model.print_trainable_parameters()) 


training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    per_device_train_batch_size=4, 
    gradient_accumulation_steps=1, 
    learning_rate=2e-4, 
    num_train_epochs=3, 
    logging_steps=100,
    save_steps=500,
)


trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
    tokenizer=tokenizer,
    peft_config=lora_config,
    max_seq_length=1024, 
    packing=False, 
)

# trainer.train() 
# trainer.save_model()