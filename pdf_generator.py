import logging
import os
import streamlit as st
from fpdf import FPDF

# Loglama ayarları
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PDF(FPDF):
    def __init__(self):
        super().__init__()
        # Font dosyalarının varlığını kontrol et (Hata yönetimi)
        font_path_regular = './times.ttf'
        font_path_bold = './timesbd.ttf'
        
        # Eğer sistemde fontlar yoksa varsayılan fonta düşmemesi için kontrol
        if not os.path.exists(font_path_regular) or not os.path.exists(font_path_bold):
            st.error("HATA: 'times.ttf' ve 'timesbd.ttf' dosyaları proje klasöründe bulunamadı. Lütfen bu dosyaları ekleyin.")
            raise FileNotFoundError("Font dosyaları eksik.")

        try:
            # fpdf2'de uni=True parametresi genellikle gerekmez ama eski fpdf kullanıyorsanız kalabilir.
            # Türkçe karakterler için 'utf-8' desteği ekliyoruz.
            self.add_font('TimesNewRoman', '', font_path_regular)
            self.add_font('TimesNewRoman', 'B', font_path_bold)
        except Exception as e:
            logger.error(f"Font yükleme hatası: {e}")

    def header(self):
        # Header'da font set edilmeli
        self.set_font('TimesNewRoman', 'B', 12)
        self.cell(0, 10, 'LEXTR AI - HUKUKİ ANALİZ VE KARAR RAPORU', 0, 1, 'C')
        self.ln(5)

    def chapter_title(self, label):
        self.set_font('TimesNewRoman', 'B', 12)
        self.set_fill_color(200, 220, 255)
        # Türkçe karakterleri garanti altına almak için encode/decode yerine string veriyoruz
        self.cell(0, 10, label, 0, 1, 'L', 1)
        self.ln(4)

    def chapter_body(self, body):
        self.set_font('TimesNewRoman', '', 11)
        self.multi_cell(0, 8, body)
        self.ln()