import os
import json
from tqdm import tqdm

STRUCTURED_DATA_DIR = "yapilandirilmis_veriler_pozisyonu" 


OUTPUT_SFT_FILE = "Sft_train.jsonl" 


SYSTEM_PROMPT = (
    "Sen, Türkiye Cumhuriyeti Anayasası ve ilgili kanunlar çerçevesinde bireysel başvuru davalarını "
    "inceleyen deneyimli bir Anayasa Mahkemesi raportörüsün. Sana sunulan olayın Anayasa’nın "
    "hangi maddesini ihlal edip etmediğini, sunulan emsal kararları referans alarak, resmi ve "
    "gerekçeli bir karar formatında analiz et ve hükmü açıkça belirt."
)

# Olay özeti ve İlgili yasal çerçeve bileşenleri birleştirilerek, sistem için istenilen girdi komutu yaratılır
def create_prompt(structured_decision):

    
    case_scenario = structured_decision.get("I. TALEP", structured_decision.get("GİRİŞ", "Olay özeti bilinmiyor."))
    
    
    anayasamaddesi = structured_decision.get("metadata", {}).get("anayasa_maddesi", "Bilinmiyor.")
    
   
    prompt = f"### Sistem Talimatı:\n{SYSTEM_PROMPT}\n\n"
    prompt += f"### Olay Özeti :\n{case_scenario.strip()}\n\n"
    prompt += f"### İlgili Yasal Çerçeve :\nİnceleme: Anayasa'nın {anayasamaddesi} maddesi kapsamında değerlendirilmelidir.\n"
    
    return prompt

#Veri seti hazırlanınca burda belirtilen emsal kararlar verilerinden gerekli parametreler çekilicek

def create_completion(structured_decision):
    
   
    completion = f"### Talep ve İddia Özeti:\n{structured_decision.get('I. TALEP', 'Bilgi yok.').strip()}\n\n"
    completion += f"### İnceleme:\n{structured_decision.get('II. İNCELEME', 'Bilgi yok.').strip()}\n\n"
    
   
    emsal_referans = structured_decision.get("metadata", {}).get("emsal_karar_no", "20XX/XX E. sayılı, K.T. 20XX/YY sayılı emsal karar.")
    completion += f"### Emsal Karar Referansı:\nKullanılması gereken en az bir AYM emsal kararı: {emsal_referans}\n\n"
    
    
    hukuki_muhakeme = structured_decision.get('GEREKÇE', structured_decision.get('HUKUKİ MUHAKEME', 'Gerekçelendirme metni yok.'))
    completion += f"### Hukuki Değerlendirme (Muhakeme):\n{hukuki_muhakeme.strip()}\n\n"
    
    huküm = structured_decision.get('III. HÜKÜM', structured_decision.get('SONUÇ', 'İHLAL VAR / İHLAL YOK hükmü belirtilemedi.'))
    completion += f"### Hüküm (Karar):\n{huküm.strip()}"
    
    return completion



def generate_sft_dataset(input_dir, output_file):
    
    sft_data = []
    
    if not os.path.exists(input_dir):
        print(f"HATA:  '{input_dir}' klasörü bulunamadı.")
        return

    print(f"'{input_dir}' klasörü bulundu. Veriler çevriliyor...")
    
    try:
        
        for filename in tqdm(os.listdir(input_dir)):
            if filename.endswith(".json"):
                input_path = os.path.join(input_dir, filename)
                
                with open(input_path, 'r', encoding='utf-8') as f:
                    try:
                        structured_decision = json.load(f)
                    except json.JSONDecodeError as e:
                        print(f"{filename} dosyası okunamadı. Hata: {e}")
                        continue
                
                
                prompt = create_prompt(structured_decision)
                completion = create_completion(structured_decision)
                
                sft_data.append({
                    "prompt": prompt,
                    "completion": completion,
                    "source_file": filename
                })

        
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in sft_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        print(f"\n Işlem tamamlandı : Toplam {len(sft_data)}  SFT veri çifti oluşturuldu --> '{output_file}' dosyasına kaydedildi.")

    except Exception as e:
        print(f"\nHATA: : {e}")
    finally:
         print("Veri hazırlanması tamamlandı.")

# --- SCRIPT'İN ÇALIŞTIRILMASI ---
# generate_sft_dataset(STRUCTURED_DATA_DIR, OUTPUT_SFT_FILE)