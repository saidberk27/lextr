from pydantic import BaseModel
from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from datetime import date
from enum import Enum
from typing import List, Optional
from dataclasses import dataclass, field
import json # Daha fazla bilgi icin https://docs.langchain.com/oss/python/langchain/models#json-schema

SYSTEM_PROMPT = "Sen Türkiye Cumhuriyeti Mahkemeleri için tasarlanmış bir yargıç" \
"Karar destek sistemisin. İsmin LEXTR. Yalnızca Türkiye Cumhuriyeti Hukuku Gözeterek" \
"Hukuki Silojizm adımlarını takip ederek durumları hukuki açdıan ele alır ve değerlendirirsin."

TEMPERATURE = 0.3 # Hukuki meseleler düsük temperature'de kalsa daha iyi olabilir.
TIMEOUT = 30
MAX_TOKENS = 1000


from enum import Enum

class KararTipi(Enum):
    # Hukuk Mahkemeleri Kararları
    HUK_TESBIT = "TESBİT DAVASI KABUL"
    HUK_EDAYERINE_GETIRME = "EDİMİN AYNEN İFASI"
    HUK_TAZMINAT = "TAZMİNAT HÜKMÜ"
    HUK_IPSAK = "HUKUKİ İŞLEM İPTALİ"
    HUK_TAHLIYE = "TAHLİYE KARARI"

    # Ceza Mahkemeleri Kararları
    CEZ_BERAAT = "BERAAT"
    CEZ_MAHKUMIYET = "MAHKUMİYET HÜKMÜ"
    CEZ_HAPIS = "HAPİS CEZASI"
    CEZ_APC = "ADLİ PARA CEZASI"
    CEZ_HAGB = "HÜKMÜN AÇIKLANMASININ GERİ BIRAKILMASI"
    CEZ_CYOK = "CEZA VERİLMESİNE YER OLMADIĞINA DAİR KARAR"

    # İdari ve Vergi Mahkemeleri Kararları
    IDR_IPTAL = "İDARİ İŞLEM İPTALİ"
    IDR_TAMYARG = "TAM YARGI (TAZMİNAT)"
    VERGI_TERKINI = "VERGİ TERKİNİ"
    GENEL_RED = "DAVANIN REDDİ" # Tüm alanlarda ortak

@dataclass
class Dava:
    hakim: str
    savci: str
    davali : str
    davaci : str
    tarih : date
    mahkeme: str
    karartipi : Optional[KararTipi] = field(default=None)
    karar : str
    llm_model : ChatGoogleGenerativeAI


@dataclass
class HukukDavasi(Dava):
    """
    1 - Dava dilekçesi ve cevap dilekçesi işlenir
    2 - Önyargılar çıkartılır
    3 - Dilekçeler önyargılar değerlendirilerek birlikte işlenir.
    4 - Kağıtlara göre kararlar verilir
    5 - Emsal kararlarla karşılaştırılır.
    6 - Nihai karar verilir.
    """

    dava_dilekcesi : str
    cevap_dilekcesi : str
    sekli_gercek : str # Dosyada ne varsa o
    deliller: List[str] = field(default_factory=list)

    def dava_dilekcesi_isleme(self):
        """
        Dava Dilekçesi İşlenir. Dava Dilekçesinden "Küçük Önerme" Ayıklanmaya Çalışır
        Davacı Önyargılı "Küçük Önerme" olduğu not edilir.
        """
        
    def cevap_dilekcesi_isleme(self):
        """
        Cevap Dilekçesi İşlenir. Cevap Dilekçesinden "Küçük Önerme" Ayıklanmaya Çalışır
        Davalı Önyargılı "Küçük Önerme" olduğu not edilir.
        """

    def hibrit_dilekce_isleme(self):
        """
        İki dilekçe (Çatışma Dilekçeleri) işlenir.
        Önyargılar işleme algoritmasına eklenir.
        Şekli gerçek bulunur.
        NOTE: sekli_gercek değişkeni bu metotta doldurulmalıdır.
        """
    
    def buyuk_onerme_eslestirme(self):
        """
        Küçük önermeler hangi yasa, mevzuat veya kararnameye uyumlu tespit edilir.
        NOTE: Prompt'ta yasa, mevzuat veya kararname araması gerektiği söylenebilir.
        """
    
    def karar1(self):
        """
        Hibrit dilekçe işleminden sonra karara varılır.
        XXX: Buyuk Önerme + Küçük Önerme = Karar Mekanizmasına Uyulmalıdır.        
        Maddi gerçek göz önünde bulundurulur.
        """
    
    def karar2(self):
        """
        RAG teknolojisiyle emsal kararlar çekilir.
        Karar1'de verilen karar ile emsal kararlar karşılaştırılır.
        XXX: Bu kısımda son karar dönülmelidir.
        """

@dataclass
class CezaDavasi(Dava):
    """
    1 - İddianeme ve ifade işlenir
    2 - Önyargılar çıkartılır
    3 - Belgeler, önyargılar değerlendirilerek birlikte işlenir
    4 - Kağıtlara göre kararlar verilir
    5 - Emsal kararlarla karşılaştırılır
    6 - Nihai karar verilir
    """

    iddianame : str
    ifade: str
    maddi_gercek: str # Ne olduysa o
    rapor : str

    def iddianame_isleme(self):
        """
        İddianame işlenir. İddianameden "Küçük Önerme" Ayıklanmaya Çalışır
        İddianame Önyargılı "Küçük Önerme" olduğu not edilir.
        """

    def ifade_isleme(self):
        """
        İfade İşlenir. Cevap Dilekçesinden "Küçük Önerme" Ayıklanmaya Çalışır
        İfade Önyargılı "Küçük Önerme" olduğu not edilir.
        """

    def hibrit_dilekce_isleme(self):
        """
        İki dilekçe (Çatışma Dilekçeleri) işlenir.
        Önyargılar işleme algoritmasına eklenir.
        Maddi gerçek bulunur.
        NOTE: maddi_gercek değişkeni bu metotta doldurulmalıdır.
        """

    def buyuk_onerme_eslestirme(self):
        """
        Küçük önermeler hangi yasa, mevzuat veya kararnameye uyumlu tespit edilir.
        NOTE: Prompt'ta yasa, mevzuat veya kararname araması gerektiği söylenebilir.
        """

    def karar1(self):
        """
        Hibrit dilekçe işleminden sonra karara varılır.
        Şekli gerçek göz önünde bulundurulur.
        XXX: Buyuk Önerme + Küçük Önerme = Karar Mekanizmasına Uyulmalıdır.        

        """
    
    def karar2(self):
        """
        RAG teknolojisiyle emsal kararlar çekilir.
        Karar1'de verilen karar ile emsal kararlar karşılaştırılır.
        XXX: Bu kısımda son karar dönülmelidir.
        """

def main():
    print("Lextr'a Hoş Geldiniz!\n" \
    "Lütfen Yapay Zeka Görüşü İçin İstediğiniz Davanın Çeşidini Girin: ")

    dava_cesidi = int(input("1) Hukuk Davası \n" \
    "2) Ceza Davası\n"))

    model = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite",
                                   temperature = TEMPERATURE,
                                   timeout = TIMEOUT,
                                   max_tokens = MAX_TOKENS
                                   )
    
    """
    for chunk in model.stream("Why do parrots have colorful feathers?"):
        print(chunk.text, end="|", flush=True)
    """


if __name__ == "__main__":
    main()
