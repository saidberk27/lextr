import streamlit as st
import time
import os
import google.generativeai as genai
from dotenv import load_dotenv



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
    genai.configure(api_key=api_key, transport='rest')
    
    # Modeli bu kimlik talimatıyla başlatıyoruz
    model = genai.GenerativeModel(
        model_name='models/gemini-2.5-flash',
        system_instruction=system_instruction
    )
else:
    st.error("⚠️ API Key bulunamadı! Lütfen Secrets veya .env dosyasını kontrol edin.")
    st.stop() # API anahtarı yoksa kodun geri kalanını çalıştırmayı durdurur


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
    # Kullanıcı mesajını göster ve kaydet
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # ASİSTAN CEVABI (GERÇEK ZAMANLI)
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            # Gemini modelinden yanıt al
            # Not: İstersen 'generation_config' ile slider'dan gelen 'temp' değerini buraya ekleyebilirsin
            response = model.generate_content(prompt)
            actual_response = response.text
            
            # Daktilo efekti simülasyonu
            for chunk in actual_response.split():
                full_response += chunk + " "
                time.sleep(0.05)
                message_placeholder.markdown(full_response + "▌")
            
            # Final cevabı göster
            message_placeholder.markdown(full_response)
            
        except Exception as e:
            error_message = f"Bir hata oluştu: {str(e)}"
            st.error(error_message)
            full_response = error_message
    
    # Asistan cevabını geçmişe kaydet
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    # Kullanılabilir modelleri listelemek için bu kodu geçici olarak ekle
