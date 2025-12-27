import torch
import json
import time
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import PeftModel


LLM_MODEL_NAME = "meta-llama/Llama-2-7b-hf"
LORA_ADAPTER_PATH = "./models/finetuned_adapters/aym_raportor_adapter"  # Verşler elde edilince buraya gelicek
CONTEXT_WINDOW_SIZE = 4096
MAX_NEW_TOKENS = 1024
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

#
class MockVectorDB:
    def __init__(self):
        # Sahte emsal kararlar (retrieval sonucunu simüle eder)
        self.mock_docs = [
            "Emsal Karar 1 (Yüksek Mahkeme Kararı, 2018/123): Bir vatandaşın adil yargılanma hakkı (Anayasa Md. 36) ihlali talebinde, delil toplama sürecindeki usul hataları temel gerekçe olarak kabul edilmiştir.",
            "Emsal Karar 2 (Bölge Mahkemesi Kararı, 2020/456): Hakimin reddi talebinin reddedilmesi, somut olayda tarafsızlık şüphesi yaratmadığından, Anayasa'nın ihlal edilmediği sonucuna varılmıştır.",
            "Emsal Karar 3 (AYM Kararı, 2022/789): Özel hayatın gizliliği (Anayasa Md. 20) ihlali iddialarında, kamu yararı ve orantılılık ilkesinin gözetilmesi gerektiği vurgulanmıştır."
        ]

    def query(self, query: str, k: int = 3) -> list:
        
        
        print(f"\n[RAG] Vektör DB sorgusu yapılıyor: '{query[:50]}...'")
        time.sleep(0.5) # Simülasyon gecikmesi
        return self.mock_docs[:k]


def load_llm_and_tokenizer():
    
    print(f"\n[LLM] Temel model ({LLM_MODEL_NAME}) yükleniyor...")
    
    
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )

    model = AutoModelForCausalLM.from_pretrained(
        LLM_MODEL_NAME,
        quantization_config=bnb_config,
        device_map=DEVICE,
        max_length=CONTEXT_WINDOW_SIZE
    )
    tokenizer = AutoTokenizer.from_pretrained(LLM_MODEL_NAME)
    tokenizer.pad_token = tokenizer.eos_token
 
    if False: 
        print(f"[LLM] LoRA Adaptörü ({LORA_ADAPTER_PATH}) yükleniyor...")
        model = PeftModel.from_pretrained(model, LORA_ADAPTER_PATH)
        # Modelin adaptörle birleştirilmesi:
        # model = model.merge_and_unload() 
        print("[LLM] AYM Raportör uzmanlığı başarıyla entegre edildi.")
    else:
        print("[LLM] DİKKAT: Model adaptörsüz (generic) modda çalışıyor.")

    return model, tokenizer


def create_full_prompt(system_prompt: str, retrieved_context: str, user_query: str) -> str:
    
    
    
    SYSTEM_PROMPT = (
        "Sen, Türkiye Cumhuriyeti Anayasası ve emsal kararlar konusunda uzman, deneyimli bir Anayasa Mahkemesi raportörüsün. "
        "Görevin, sana verilen Olay Özeti (Başvuru), İlgili Anayasa Maddesi ve Emsal Kararları inceleyerek, bu hukuki öncüllere dayanan "
        "tutarlı bir Gerekçeli Karar (Justified Decision) taslağı oluşturmaktır. "
        "Çıktın, sadece aşağıdaki formatı (TALEP, İNCELEME, HUKUKİ DEĞERLENDİRME, HÜKÜM) içermelidir."
    )
    
    
    CONTEXT_BLOCK = f"""
--- BAĞLAM BİLGİSİ (EMSALLER) ---
{retrieved_context}
---
"""
    
    
    CASE_DETAILS = f"""
*** BAŞVURU DETAYLARI ***
{user_query}
"""
    
    
    FULL_PROMPT = f"{SYSTEM_PROMPT}\n{CONTEXT_BLOCK}\n{CASE_DETAILS}"
    
    return FULL_PROMPT


def generate_decision(model, tokenizer, query: str):
    
    
    
    vector_db = MockVectorDB()
    retrieved_docs = vector_db.query(query, k=3)
    context_text = "\n".join([f"- {doc}" for doc in retrieved_docs])
    
   
    full_prompt = create_full_prompt(
        system_prompt=None, 
        retrieved_context=context_text,
        user_query=query
    )
    
    
    print(f"\n[GENERATION] LLM (Generic) yanıt üretiyor...")
    
    inputs = tokenizer(full_prompt, return_tensors="pt", truncation=True).to(DEVICE)
    
    
    with torch.no_grad():
        output = model.generate(
            **inputs,
            max_new_tokens=MAX_NEW_TOKENS,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
            repetition_penalty=1.1,
            eos_token_id=tokenizer.eos_token_id
        )

    
    generated_text = tokenizer.decode(output[0], skip_special_tokens=True)
    
    response = generated_text.replace(full_prompt, "").strip()
    
    
    if "HÜKÜM" not in response:
        response = "[UYARI: HENÜZ FINE-TUNING YAPILMADIĞI İÇİN FORMAT KUSURLU OLABİLİR.]\n" + response

    return response, context_text

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    
    llm_model, llm_tokenizer = load_llm_and_tokenizer()
    
    
    example_query = (
        "Olay Özeti: İstanbul'da bir avukatın ofisine, mahkeme kararı olmaksızın polis tarafından girilerek arama yapılmış ve bazı belgelere el konulmuştur. "
        "İhlal İddiası: Konut Dokunulmazlığı (Anayasa Md. 21) ve Özel Hayatın Gizliliği (Anayasa Md. 20)."
    )
    
   
    final_decision, used_context = generate_decision(llm_model, llm_tokenizer, example_query)

    print("\n" + "="*80)
    print("🎯 AYM RAPORTÖRÜ TASLAK KARARI (Weeks 3 & 4 Çıktısı - GENERIC MOD)")
    print("="*80)
    print("\n[KULLANILAN EMSAL BAĞLAMI]:")
    print(used_context)
    print("\n" + "-"*40)
    print("\n[ ÜRETİLEN KARAR TASLAĞI]:")
    print(final_decision)
    print("\n" + "="*80)
    
