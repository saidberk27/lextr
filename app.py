import streamlit as st
import time
import os
from dotenv import load_dotenv

# .env dosyasındaki verileri yükle
load_dotenv()

# API Anahtarını değişkene al (Dağıtım)

api_key = os.getenv("GOOGLE_API_KEY")

# Sayfa Ayarları
st.set_page_config(page_title="T.C. Anayasa AI", layout="wide")

# 1. SOL PANEL (DOKÜMAN YÜKLEME)
with st.sidebar:
    st.title("📂 Dava Dosyası Yükle")
    st.info("Analiz edilecek iddianame veya kararı buraya yükleyin.")
    uploaded_file = st.file_uploader("Dosya Seç (PDF/TXT)", type=["pdf", "txt"])
    
    if uploaded_file:
        with st.status("Doküman analiz ediliyor...", expanded=True) as status:
            st.write("Metinler ayıklanıyor...")
            time.sleep(1) # İşlem süresi simülasyonu
            st.write("Vektör veritabanına taranıyor...")
            time.sleep(1)
            status.update(label="Analiz Tamamlandı!", state="complete", expanded=False)
        st.success(f"✅ {uploaded_file.name} hazır.")
        # BURADA: Arka plandaki RAG sistemine dosya gönderilecek.
    
    st.divider()
    st.write("🔧 Model Ayarları")
    temp = st.slider("Yorum Esnekliği", 0.0, 1.0, 0.3)

# 2. ANA EKRAN (CHAT GEÇMİŞİ)
st.title("⚖️ T.C. Anayasal Muhakeme Asistanı")

# Mesaj geçmişini hafızada tut (Session State)
if "messages" not in st.session_state:
    st.session_state.messages = []

# Eski mesajları ekrana yazdır
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 3. KULLANICI GİRDİSİ VE CEVAP
if prompt := st.chat_input("Hukuki sorunuzu veya vaka özetini girin..."):
    # Kullanıcı mesajını göster ve kaydet
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # ASİSTAN CEVABI (Simülasyon)
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # Burası Backend'den (LangChain) gelecek cevap olacak
        # Şimdilik simüle ediyoruz:
        simulated_response = f"Bu durum Anayasa'nın 26. maddesi kapsamında değerlendirilmelidir...\n\n**Kaynak:** AYM 2019/35 Sayılı Karar."
        
        # Daktilo efekti ile yazdırma
        for chunk in simulated_response.split():
            full_response += chunk + " "
            time.sleep(0.05)
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})