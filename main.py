from pydantic import BaseModel
from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
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

@dataclass(kw_only=True)
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


@dataclass(kw_only=True)
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

    def dava_dilekcesi_isleme(self) -> dict:
        """
        Dava Dilekçesi İşlenir. Dava Dilekçesinden "Küçük Önerme" Ayıklanmaya Çalışır
        Davacı Önyargılı "Küçük Önerme" olduğu not edilir.
        """
        
    def cevap_dilekcesi_isleme(self) -> dict:
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

@dataclass(kw_only=True)
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

    def __post_init__(self):
        """Düşünce Zinciri Burada Başlatılır."""
        print(f"Sistem Başlatıldı: {self.mahkeme} için dosya hazırlanıyor...")

        self.hibrit_dilekce_isleme()#İddianame ve ifade iceride islenecek.
        self.buyuk_onerme_eslestirme()
        self.karar1()
        self.karar2()

    def iddianame_isleme(self) -> dict:
        """
        İddianame işlenir. İddianameden "Küçük Önerme" Ayıklanmaya Çalışır
        İddianame Önyargılı "Küçük Önerme" olduğu not edilir.
        NOTE: İddianamedeki önyargılar return edilmelidir. Hibrit Dilekçe
        kısmında kullanılacaktır.
        """

    def ifade_isleme(self) -> dict:
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
        #Dummy Data
        iddianame_data = {
            "olay": "Şüpheli Burak Demir, 01.01.2024 tarihinde gürültü nedeniyle tartıştığı müşteki Kerem Sönmez'i, üzerinde taşıdığı ve saldırı amacıyla hazır bulundurduğu bıçakla karın boşluğundan bir kez yaralamıştır. Müştekinin hayati tehlikesi mevcuttur. Şüpheli, müştekinin silahsız olmasına rağmen doğrudan hayati bölgeyi hedef alarak kasten öldürmeye teşebbüs etmiştir.",
            
            "onyargi": "Metin, şüphelinin eylemini doğrudan 'saldırı amaçlı' olarak nitelendirmekte ve meşru müdafaa ihtimalini dışlamaktadır. 'Saldırı amacıyla hazır bulundurduğu' ifadesiyle önceden tasarlama iması yapılmakta, müştekinin alkollü olması ve ilk saldırıyı başlatması gibi hafifletici unsurlar göz ardı edilerek şüphelinin suçluluğu peşinen kabul edilmektedir."
        }

        # #Dummy Data
        ifade_data = {
            "olay": "Olay günü müşteki Kerem Sönmez, aşırı alkollü bir şekilde kapımı tekmeleyerek içeri girmeye çalışmıştır. Kapıyı açtığımda boğazıma sarılarak beni nefessiz bırakmış ve öldürmekle tehdit etmiştir. Fiziksel olarak benden çok daha iri olan müştekinin elinden kurtulmak ve canımı korumak amacıyla, panik halinde elime geçen meyve çakısını rastgele savurdum. Öldürme kastım yoktu, eylem tamamen meşru müdafaa sınırları içindedir.",
            
            "onyargi": "Metin, olaydaki şiddet sorumluluğunu tamamen karşı tarafa (müştekiye) yükleme eğilimindedir. 'Aşırı alkollü', 'boğazıma sarıldı', 'nefessiz bıraktı' gibi ifadelerle mağduriyet vurgulanırken, bıçaklama eylemi 'rastgele savurmak' şeklinde yumuşatılmıştır. Şüpheli, kendini çaresiz bir kurban, müştekiyi ise kontrolsüz bir saldırgan olarak çerçevelemektedir."
        }

        iddianame_sonuc = iddianame_data #self.iddianame_isleme()
        ifade_sonuc = ifade_data #self.ifade_isleme()
        iddianame_olay_metni = iddianame_sonuc.get("olay")
        ifade_olay_metni = ifade_sonuc.get("olay")

        iddianame_onyargi = iddianame_sonuc.get("onyargi")
        ifade_onyargi = ifade_sonuc.get("onyargi")
        
        user_prompt_content = f""" 
        Olay, iddianameye göre: {iddianame_olay_metni}
        Olay, savunmacıya göre: {ifade_olay_metni}
        
        İddianamenin önyargısı: {iddianame_onyargi}
        Savunmacının önyargısı: {ifade_onyargi}
        
        Görev: Önyargıları süz, iki anlatımı birleştir ve "Maddi Gerçek" (Nötr Olay Metni) oluştur.
        Cevap Formatı: İlk kısımda yalnızca maddi gerçek (küçük önerme)'yi bul ve ondan bahset.
        İkinci kısımda neden küçük önermeyi ilk kısımda bulduğunu açıkla (Açıklanabilir Yapay Zeka.)
        İlk kısmı ikinci kısımdan ayrı tut. İlk kısım ile ikinci kısım arasını '***' 3 adet yıldız ile
        ayır. Programın geri kalanında bu formata göre split edeceğim. 3 yıldız formatına uy.
        """

        # SYSTEM PROMPT BURADA DAHİL EDİLİYOR
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_prompt_content)
        ]

        full_response = ""
        for chunk in self.llm_model.stream(messages):
            #print(chunk.content, end="", flush=True)
            full_response += chunk.content

        print(full_response)
        self.maddi_gercek = full_response.split("***")[0]
        self.aciklama = full_response.split()[1]       
        print(self.maddi_gercek)

    def buyuk_onerme_eslestirme(self):
        """
        Küçük önermeler hangi yasa, mevzuat veya kararnameye uyumlu tespit edilir.
        NOTE: Prompt'ta yasa, mevzuat veya kararname araması gerektiği söylenebilir.
        NOTE: Bu kısım self.maddi_gercek gözetilerek yapılmalıdır.
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
    print("LEXTR - Hukuk Karar Destek Sistemine Hoş Geldiniz!")
    
    # Modeli Başlat
    model = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", 
        temperature=TEMPERATURE,
        timeout=TIMEOUT,
        max_tokens=MAX_TOKENS
    )

    try:
        secim = int(input("1) Hukuk Davası \n2) Ceza Davası\nSeçiminiz: "))
    except ValueError:
        print("Lütfen sayı giriniz.")
        return

    if secim == 2:
        # CEZA DAVASI OLUŞTURMA (Instantiation)
        # Class @dataclass olduğu için __init__ otomatik oluşur ama tüm fieldları vermemiz gerekir.
        ceza_davasi = CezaDavasi(
            hakim="Yapay Zeka Hakim",
            savci="Cumhuriyet Savcısı",
            davali="Burak Demir",  # Sanık
            davaci="K.H.",        # Kamu Hukuku
            tarih=date.today(),
            mahkeme="Asliye Ceza Mahkemesi",
            karar="",             # Henüz boş
            llm_model=model,      # Modeli class içine paslıyoruz
            iddianame="Ham veri...", # Gerçek senaryoda dosya okuma vs. olur
            ifade="Ham veri...",
            maddi_gercek="",
            rapor=""
        )
    

    elif secim == 1:
        print("Hukuk davası henüz implemente edilmedi.")
    


if __name__ == "__main__":
    main()
