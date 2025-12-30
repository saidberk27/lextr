from pdf_generator import PDF 

# 2. Adım: Test Verisi (dv ve dava objeleri)
dv = {
    'mahkeme': 'Ankara 4. Agir Ceza Mahkemesi',
    'davaci': 'Ahmet Yilmaz',
    'davali': 'Mehmet Demir',
    'tarih': '2023-10-27',
    'kategori': 'Ceza Davasi'
}

class Dava:
    def __init__(self):
        self.karar = "Dosya kapsamindaki deliller incelendiginde, sanigin uzerine atili sucu isledigi sabit gorulmustur..."

dava = Dava()

# 3. Adım: PDF Oluşturma Fonksiyonu
def test_pdf_generation():
    try:
        pdf = PDF()
        pdf.add_page()
        
        # Başlık
        pdf.chapter_title("T.C. YARGI ANALIZ RAPORU")
        
        info_text = (f"MAHKEME: {dv['mahkeme']}\n"
                    f"TARAF (DAVACI/MUSTEKI): {dv['davaci']}\n"
                    f"TARAF (DAVALI/SANIK): {dv['davali']}\n"
                    f"TARIH: {dv['tarih']}\n"
                    f"DOSYA TIPI: {dv['kategori']}")
        
        pdf.chapter_body(info_text)
        
        pdf.chapter_title("HUKUKI GEREKCE VE HUKUM")
        pdf.chapter_body(dava.karar)
        
        # --- KRİTİK NOKTA ---
        # fpdf2'de output() parametresiz çağrılırsa bytes döner (Streamlit için uygun)
        # Dosyaya kaydetmek için output("dosya_adi.pdf") kullanılır.
        pdf_bytes = pdf.output() 
        
        # Test amaçlı dosyaya manuel yazdıralım (Streamlit download_button simülasyonu)
        with open("test_raporu.pdf", "wb") as f:
            f.write(pdf_bytes)
            
        print("✅ Başarılı: 'test_raporu.pdf' oluşturuldu.")
        print(f"Veri Tipi: {type(pdf_bytes)}") # <class 'bytes'> olmalı

    except Exception as e:
        print(f"❌ Hata Oluştu: {e}")

if __name__ == "__main__":
    test_pdf_generation()