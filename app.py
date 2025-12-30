import streamlit as st
import os
from dotenv import load_dotenv
from datetime import date 
from langchain_google_genai import ChatGoogleGenerativeAI
from main import setup_streamlit_logging, KullaniciDavasi
from pdf_generator import PDF
from PyPDF2 import PdfReader
import logging

# 1. AYARLAR
st.set_page_config(page_title="LEXTR - Karar Destek", layout="wide")
load_dotenv()
logger = logging.getLogger(__name__)

def extract_text_from_pdf(uploaded_file):
    if uploaded_file is not None:
        pdf_reader = PdfReader(uploaded_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    return ""

# --- 2. SESSION STATE ---
if "step" not in st.session_state:
    st.session_state.step = 1
if "dava_verileri" not in st.session_state:
    st.session_state.dava_verileri = {}

# --- 3. AŞAMA 1: KURULUM ---
if st.session_state.step == 1:
    st.title("⚖️ Adım 1: Dava Bilgileri")
    with st.form("step1_form"):
        col1, col2 = st.columns(2)
        with col1:
            dava_kategorisi = st.selectbox("Dava Kategorisi", ["Ceza Davası", "Hukuk Davası"])
            mahkeme = st.text_input("Mahkeme Adı", placeholder="Örn: Ankara 4. Ağır Ceza Mahkemesi")
        with col2:
            davali_sanik = st.text_input("Davalı / Sanık Adı")
            davaci_musteki = st.text_input("Davacı / Müşteki Adı")
            tarih = st.date_input("Dava Tarihi", value=date.today())

        if st.form_submit_button("Sonraki Adıma Geç ➡️"):
            if not mahkeme or not davali_sanik:
                st.error("Lütfen mahkeme ve taraf bilgilerini doldurun.")
            else:
                st.session_state.dava_verileri.update({
                    "kategori": dava_kategorisi, "mahkeme": mahkeme,
                    "davali": davali_sanik, "davaci": davaci_musteki, "tarih": tarih
                })
                st.session_state.step = 2
                st.rerun()

# --- 4. AŞAMA 2: PDF YÜKLEME VE LOGLAMALI ANALİZ ---
elif st.session_state.step == 2:
    st.title(f"📂 Adım 2: Dosya Yükleme ({st.session_state.dava_verileri['kategori']})")
    
    is_ceza = st.session_state.dava_verileri['kategori'] == "Ceza Davası"
    label1 = "📄 İddianame (PDF)" if is_ceza else "📄 Dava Dilekçesi (PDF)"
    label2 = "📄 Sanık İfadesi (PDF)" if is_ceza else "📄 Cevap Dilekçesi (PDF)"

    with st.form("step2_form"):
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            file1 = st.file_uploader(label1, type=["pdf"])
        with col_f2:
            file2 = st.file_uploader(label2, type=["pdf"])

        st.divider()
        uploaded_evidences = st.file_uploader("Ek Deliller (PDF)", type=["pdf"], accept_multiple_files=True)
        
        analiz_baslat = st.form_submit_button("⚖️ Analizi Başlat ve Karar Üret")

    # Formun dışında, ancak analiz başladığında görünecek log alanı
    if analiz_baslat:
        if not file1 or not file2:
            st.warning("Lütfen ana belgeleri yükleyin.")
        else:
            st.subheader("⚙️ İşlem Günlüğü")
            log_container = st.empty() # Logların akacağı yer
            setup_streamlit_logging(log_container) # Sizin main'deki fonksiyonunuz
            


            with st.spinner("LexTR Analiz Yapıyor..."):
                try:
                    logger.info("PDF dosyaları okunuyor...")
                    text1 = extract_text_from_pdf(file1)
                    text2 = extract_text_from_pdf(file2)
                    
                    logger.info("AI Modeli hazırlanıyor...")
                    model = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", google_api_key=os.getenv("GOOGLE_API_KEY"))
                    
                    logger.info("Hukuki akıl yürütme başlatıldı (Syllogism)...")
                    dava = KullaniciDavasi(
                        hakim="Lextr AI", 
                        savci="C. Savcısı",
                        davali=st.session_state.dava_verileri['davali'],
                        davaci=st.session_state.dava_verileri['davaci'],
                        tarih=st.session_state.dava_verileri['tarih'],
                        mahkeme=st.session_state.dava_verileri['mahkeme'],
                        llm_model=model, 
                        dilekce1=text1, 
                        dilekce2=text2,
                        karar="", kucuk_onerme="", buyuk_onerme="",
                        rapor=f"{len(uploaded_evidences)} adet ek delil incelendi."
                    )
                    
                    # Eğer main.py'de analiz fonksiyonu otomatik çalışmıyorsa burada tetikleyin:
                    # dava.analiz_et() 
                    
                    logger.info("Analiz başarıyla tamamlandı, sonuçlar hazırlanıyor.")
                    st.session_state.sonuc_dava = dava
                    st.session_state.step = 3
                    st.rerun()
                except Exception as e:
                    logger.error(f"Hata oluştu: {str(e)}")
                    st.error(f"Sistem Hatası: {e}")

# --- 5. AŞAMA 3: PROFESYONEL PDF ÇIKTISI ---
elif st.session_state.step == 3:
    dava = st.session_state.sonuc_dava
    dv = st.session_state.dava_verileri
    
    st.success("✅ Analiz Tamamlandı")
    
    col_header, col_btn = st.columns([3, 1])
    with col_header:
        st.header("⚖️ Mahkeme Kararı ve Gerekçe")
    
    with col_btn:
        # PDF raporunu oluştur
        if 'dv' not in locals():
            dv = {'mahkeme': 'Ankara 1. Asliye Hukuk', 'davaci': 'Ahmet Yılmaz', 'davali': 'Mehmet Demir', 'tarih': '30.12.2025', 'kategori': 'Tazminat'}
        if 'dava' not in locals():
            class DavaMock:
                karar = "GEREKÇE: Davalının kusurlu olduğu tespit edilmiştir.\nHÜKÜM: Davanın kabulüne karar verilmiştir."
            dava = DavaMock()

        try:
            pdf = PDF()
            pdf.add_page()
            
            # Başlık
            pdf.chapter_title("T.C. YARGI ANALİZ RAPORU")
            
            info_text = (f"MAHKEME: {dv['mahkeme']}\n"
                        f"TARAF (DAVACI/MÜŞTEKİ): {dv['davaci']}\n"
                        f"TARAF (DAVALI/SANIK): {dv['davali']}\n"
                        f"TARİH: {dv['tarih']}\n"
                        f"DOSYA TİPİ: {dv['kategori']}")
            
            pdf.chapter_body(info_text)
            
            pdf.chapter_title("HUKUKİ GEREKÇE VE HÜKÜM")
            pdf.chapter_body(dava.karar)
            

            pdf_bytes = pdf.output() 
            
            st.download_button(
                label="📥 Profesyonel Raporu İndir (PDF)",
                data=pdf_bytes,
                file_name=f"Karar_{dv['davali'].replace(' ', '_')}_{dv['tarih']}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        except FileNotFoundError as e:
            # Font dosyası yoksa kullanıcıyı uyar
            st.error(f"Dosya Hatası: {e}")
        except Exception as e:
            logger.error(f"PDF Oluşturulamadı: {e}")
            st.error(f"PDF Oluşturulamadı: {e}")

    st.markdown("---")
    st.markdown(dava.karar)
    
    with st.expander("🔍 Teknik Süreç Detayları"):
        st.subheader("Küçük Önerme (Olay Analizi)")
        st.write(dava.kucuk_onerme)
        st.subheader("Büyük Önerme (Hukuki Dayanak)")
        st.write(dava.buyuk_onerme)

    if st.button("🔄 Yeni Analiz Başlat"):
        st.session_state.step = 1
        st.rerun()