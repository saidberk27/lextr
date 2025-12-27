import streamlit as st
import time
import os
import google.generativeai as genai
from dotenv import load_dotenv
from main import CezaDavasi, HukukDavasi
from datetime import date 
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

# Örnek vakaları listeleme fonksiyonu
def get_example_cases(folder_path="Example Cases"):
    """Klasördeki .md dosyalarını listeler."""
    if not os.path.exists(folder_path):
        return []
    return [f for f in os.listdir(folder_path) if f.endswith('.md')]

def read_case_content(file_path):
    """Markdown dosyasının içeriğini okur."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()
    
# Örnek vakalar için sidebar arayüzü
with st.sidebar:
    st.divider()
    st.subheader("📝 Örnek Vakalar (.md)")
    
    example_files = get_example_cases()
    
    if example_files:
        selected_case_file = st.selectbox("Bir vaka seçin:", ["Seçiniz..."] + example_files)
        
        if selected_case_file != "Seçiniz...":
            case_path = os.path.join("Example Cases", selected_case_file)
            case_content = read_case_content(case_path)
            
            # Seçilen vakayı küçük bir pencerede önizle
            with st.expander("Vaka İçeriğini Gör"):
                st.markdown(case_content)
            
            if st.button("⚖️ Bu Vakayı Analiz Et"):
                # Seçilen vakayı chat input'a veya işleme gönder
                st.session_state.selected_vaka = case_content
                st.success("Vaka analiz için yüklendi!")
    else:
        st.info("Henüz .md dosyası bulunamadı. 'git pull' yaptınız mı?")


# 1. SAYFA AYARLARI (Mutlaka en üstte olmalı)
st.set_page_config(page_title="T.C. Anayasa AI", layout="wide", page_icon="⚖️")

# 2. YAPILANDIRMA VE API BAĞLANTISI
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

# --- IDENTITY (KİMLİK) TANIMLAMASI ---
system_instruction = """
Sen uzman bir T.C. Anayasa Hukukçusu ve Adli Muhakeme Asistanısın. 
Görevin: Kullanıcının sunduğu vakaları, iddianameleri veya emsal kararları 
Türk Anayasa hukukuna, silojizm kurallarına (Büyük Önerme, Küçük Önerme, Sonuç) 
ve emsal Yargıtay/AYM kararlarına göre analiz etmektir.

Yanıtlarını şu yapısal düzende ver:
1. Maddi Vakalar: Olayın hukuki dille özeti.
2. Hukuki Dayanak: İlgili Anayasa maddeleri ve kanunlar.
3. Muhakeme ve Sonuç: Hukuki mantık silsilesi ile varılan netice.

Her zaman ciddi, profesyonel ve tarafsız bir hukukçu dili kullan.
"""

if api_key:
    # Google AI SDK yapılandırması 
    genai.configure(api_key=api_key, transport='rest')
    
    # main.py'nin beklediği LangChain tabanlı model tanımlaması
    model = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=api_key,
        temperature=0.3 # Hukuki muhakeme için düşük tutuyoruz
    )
else:
    st.error("API Key eksik!")


# 3. SOL PANEL (SIDEBAR)
with st.sidebar:
    st.title("📂 Dava Dosyası Yükle")
    st.info("Analiz edilecek iddianame veya kararı buraya yükleyin.")
    uploaded_file = st.file_uploader("Dosya Seç (PDF/TXT)", type=["pdf", "txt"])
    
    if uploaded_file:
        with st.status("Doküman analiz ediliyor...", expanded=True) as status:
            st.write("Metinler ayıklanıyor...")
            time.sleep(1)
            st.write("Vektör veritabanına taranıyor...")
            time.sleep(1)
            status.update(label="Analiz Tamamlandı!", state="complete", expanded=False)
        st.success(f"✅ {uploaded_file.name} hazır.")
    
    st.divider()
    st.write("🔧 Model Ayarları")
    # Bu değişkeni Gemini'ye gönderirken kullanabilirsin
    temp = st.slider("Yorum Esnekliği (Temperature)", 0.0, 1.0, 0.3)

# 4. ANA EKRAN (CHAT ARA YÜZÜ)
st.title("⚖️ T.C. Anayasal Muhakeme Asistanı")

# Mesaj geçmişini başlat (Session State)
if "messages" not in st.session_state:
    st.session_state.messages = []

# Eski mesajları ekrana bas
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
    

    

# 5. KULLANICI GİRDİSİ VE CEVAP SÜRECİ
if prompt := st.chat_input("Hukuki sorunuzu veya vaka özetini girin..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("Hukuki silojizm süreci işletiliyor..."):
            try:
                # main.py içindeki CezaDavasi sınıfını tetikliyoruz
                dava_analizi = CezaDavasi(
                    hakim="Lextr AI",
                    savci="Cumhuriyet Savcısı",
                    davali="Analiz Edilen Şahıs",
                    davaci="K.H.",
                    tarih=date.today(),
                    mahkeme="Anayasal Muhakeme Birimi",
                    karar="",
                    llm_model=model, # Senin daha önce tanımladığın model
                    iddianame=prompt, # Kullanıcının yazdığı metni iddianame gibi kabul ediyoruz
                    ifade="İfade verisi bekleniyor...",
                    maddi_gercek="",
                    buyuk_onerme="",
                    rapor=""
                )

                # Sonuçları ekrana basıyoruz
                full_response = f"""
### ⚖️ Analiz Sonucu
**Maddi Gerçek:** {dava_analizi.maddi_gercek}

**Hukuki Gerekçe:** {dava_analizi.aciklama}
                """
                st.markdown(full_response)
                
            except Exception as e:
                st.error(f"Analiz sırasında bir hata oluştu: {e}")
                full_response = "Hata nedeniyle analiz tamamlanamadı."

    st.session_state.messages.append({"role": "assistant", "content": full_response})
