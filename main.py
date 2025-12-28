from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from datetime import date
from enum import Enum
from typing import List, Optional
from dataclasses import dataclass, field
import json # Daha fazla bilgi icin https://docs.langchain.com/oss/python/langchain/models#json-schema
import requests
import os


ANYTHING_LLM_URL = "https://n1ldug0l.rpcld.cc/api/v1/workspace/lextr/chat"  
# RepoCloud'dan aldığımız API Key
ANYTHING_LLM_API_KEY = "1A81V4J-NBT4BXP-GDJ1XV7-JFHZXS9"

SYSTEM_PROMPT = """
<root>
    <identity>
        <name>LEXTR</name>
        <role>Türkiye Cumhuriyeti Mahkemeleri Karar Destek Sistemi</role>
        <domain>Türkiye Cumhuriyeti Hukuku</domain>
    </identity>
    <constraints>
        <constraint>Yalnızca Türkiye Cumhuriyeti Mevzuatı ve İçtihatlarını baz al.</constraint>
        <constraint>Hukuk dışı veya yabancı hukuk sistemlerine dayalı yorum yapma.</constraint>
    </constraints>
    <process_flow>
        <step index="1">Büyük Önerme (Kanun tespiti)</step>
        <step index="2">Küçük Önerme (Vakıa analizi)</step>
        <step index="3">Hukuki Silojizm (Sentez)</step>
        <step index="4">Hüküm (Sonuç)</step>
    </process_flow>
</root>
"""

TEMPERATURE = 0.3 # Hukuki meseleler düsük temperature'de kalsa daha iyi olabilir.
TIMEOUT = 30
MAX_TOKENS = 1000

def query_anything_llm(text_input):
    
       # AnythingLLM RAG sistemine bağlanarak emsal karar arar.
       # Bğlantı hatası olursa sistemi çökertmez, sessizce hata mesajı döner.
    
        headers = {
            "Authorization": f"Bearer {ANYTHING_LLM_API_KEY}",
            "Content-Type": "application/json"
        }
        # Sistem prompt'u RAG için biraz daha özelleştirildi
        payload = {
            "message": f"Aşağıdaki hukuki durumla ilgili veritabanındaki en benzer Yargıtay/AYM emsal kararlarını bul ve özetle:\n\n{text_input}",
            "mode": "chat"
        }

        try:
            response = requests.post(ANYTHING_LLM_URL, json=payload, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get('textResponse', "Emsal karar bulunamadı.")
            else:
                return f"RAG Bağlantı Hatası (Kod: {response.status_code})"
        except Exception as e:
            return f"RAG Sunucusuna Erişilemedi: {e}"

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
    buyuk_onerme : str
    rapor : str

    def __post_init__(self):
        """Düşünce Zinciri Burada Başlatılır."""
        print(f"Sistem Başlatıldı: {self.mahkeme} için dosya hazırlanıyor...")

        self.hibrit_dilekce_isleme()#İddianame ve ifade iceride islenecek.
        self.buyuk_onerme_eslestirme()
        self.karar1()
        self.karar2()

    def _json_temizle(self, metin: str) -> dict:
        """Yardımcı Fonksiyon: Gemini çıktısını temizleyip JSON'a çevirir."""
        try:
            # Markdown bloklarını temizle (```json ... ```)
            temiz_metin = metin.strip()
            if "```json" in temiz_metin:
                temiz_metin = temiz_metin.split("```json")[1].split("```")[0]
            elif "```" in temiz_metin:
                temiz_metin = temiz_metin.split("```")[1].split("```")[0]
            
            return json.loads(temiz_metin.strip())
        except Exception as e:
            print(f"JSON Ayrıştırma Hatası: {e}")
            # Hata olursa boş bir yapı döndür ki sistem çökmesin
            return {"olay": metin, "onyargi": "Analiz edilemedi"}

    def iddianame_isleme(self) -> dict:
        """
        İddianameyi POML yapısıyla işleyerek hukuki önyargıları ayıklar.
        """
        poml_prompt = f"""
        <poml>
            <role>Uzman Ceza Hukukçusu ve Metin Analisti</role>
            <task>İddianame metnini analiz ederek maddi vakıalar ile sübjektif önyargıları birbirinden ayır.</task>
            <input_data>
                <narrative>{self.iddianame}</narrative>
            </input_data>
            <instructions>
                1. Metindeki 'vahşice', 'sinsi', 'canice' gibi sıfatları 'onyargi' etiketine al.
                2. Sadece fiziksel eylemleri (kim, neyi, nerede, nasıl yaptı) 'olay' etiketine al.
                3. Çıktıyı SADECE JSON formatında ver, başka açıklama yapma.
            </instructions>
            <output_format>
                {{
                    "olay": "Temizlenmiş maddi gerçek metni",
                    "onyargi": "Tespit edilen taraflı ifadeler"
                }}
            </output_format>
        </poml>
        """
        response = self.llm_model.invoke([HumanMessage(content=poml_prompt)])
        return self._json_temizle(response.content)

    def ifade_isleme(self) -> dict:
        """
        Savunma ifadesini POML yapısıyla işleyerek maddi vakıaları izole eder.
        """
        poml_prompt = f"""
        <poml>
            <role>Adli Psikoloji ve Ceza Hukuku Uzmanı</role>
            <task>Şüpheli ifadesindeki savunma stratejilerini ve maddi gerçekleri analiz et.</task>
            <input_data>
                <narrative>{self.ifade}</narrative>
            </input_data>
            <instructions>
                1. 'Mecbur kaldım', 'hak etti', 'istemeden oldu' gibi niyet beyanlarını 'onyargi' kısmına al.
                2. Failin kabul ettiği fiziksel temas ve eylemleri 'olay' kısmına al.
                3. Çıktıyı SADECE JSON formatında ver, başka açıklama yapma.
            </instructions>
            <output_format>
                {{
                    "olay": "Şüphelinin kabul ettiği maddi vakıalar",
                    "onyargi": "Savunma odaklı sübjektif anlatımlar"
                }}
            </output_format>
        </poml>
        """
        response = self.llm_model.invoke([HumanMessage(content=poml_prompt)])
        return self._json_temizle(response.content)
    

    def hibrit_dilekce_isleme(self):
        """
        İki dilekçe (Çatışma Dilekçeleri) işlenir.
        Önyargılar işleme algoritmasına eklenir.
        Maddi gerçek bulunur.
        NOTE: maddi_gercek değişkeni bu metotta doldurulmalıdır.
        """
        print("Hibrit dilekçe işleniyor...")

        iddianame_sonuc = self.iddianame_isleme()
        ifade_sonuc = self.ifade_isleme()
        iddianame_olay_metni = iddianame_sonuc.get("olay")
        ifade_olay_metni = ifade_sonuc.get("olay")

        iddianame_onyargi = iddianame_sonuc.get("onyargi")
        ifade_onyargi = ifade_sonuc.get("onyargi")
        
        user_prompt_content = f"""
        <task_context>
            <objective>Maddi Gerçeğin İnşası ve Önyargı Analizi</objective>
            
            <few_shot_examples>
                <example index="1">
                    <input>
                        İddianame: "Şüpheli, mağdura vahşice saldırarak darp etmiştir." (Önyargı: 'vahşice')
                        Savunma: "Mağdur bana küfredince kendimi korumak için ittim." (Önyargı: 'kendimi korumak için')
                    </input>
                    <output>
                        Taraflar arasında çıkan tartışma esnasında şüpheli, mağdura fiziksel müdahalede bulunarak darp eylemini gerçekleştirmiştir.
                        ***
                        İddianamedeki 'vahşice' sıfatı sübjektif bir yorum olduğu için elenmiştir. Savunmadaki 'kendimi korumak için' ifadesi ise bir hukuki nitelendirme (meşru müdafaa iddiası) olduğundan maddi gerçek metnine dahil edilmemiş, sadece fiziksel temas (itme/darp) esas alınmıştır.
                    </output>
                </example>

                <example index="2">
                    <input>
                        İddianame: "Fail, mağdurun cüzdanını sinsi bir şekilde çalmıştır." (Önyargı: 'sinsi bir şekilde')
                        Savunma: "Cüzdanı yerde buldum, sahibine vermek için aldım." (Önyargı: 'sahibine vermek için')
                    </input>
                    <output>
                        Şüpheli, mağdura ait cüzdanı mağdurun hakimiyet alanından alarak kendi zilyetliğine geçirmiştir.
                        ***
                        İddianamedeki 'sinsi' ifadesi fiilin işleniş tarzına dair kanıtlanmamış bir nitelendirmedir. Savunmadaki 'sahibine vermek için' ifadesi ise bir niyet (manevi unsur) beyanıdır; maddi gerçeği oluşturan fiil, cüzdanın yer değiştirmesidir.
                    </output>
                </example>

                <example index="3">
                    <input>
                        İddianame: "Şahıs, kamu görevlisine ağza alınmayacak hakaretler savurmuştur." (Önyargı: 'ağza alınmayacak')
                        Savunma: "Ağzımdan sadece 'işini yap' cümlesi çıktı, hakaret etmedim." (Önyargı: 'sadece')
                    </input>
                    <output>
                        Şüpheli, görevi başındaki kamu görevlisine yönelik sözlü ifadelerde bulunmuştur.
                        ***
                        İddianamedeki 'ağza alınmayacak' ifadesi duygusal bir vurgu içerdiği için nötrleştirilmiştir. Savunmadaki 'sadece' vurgusu ise olayı küçültme çabası taşıdığı için elenmiş, eylemin 'sözlü ifade' olduğu saptanmıştır.
                    </output>
                </example>
            </few_shot_examples>

            <input_data>
                <prosecution>
                    <narrative>{iddianame_olay_metni}</narrative>
                    <bias_identified>{iddianame_onyargi}</bias_identified>
                </prosecution>
                <defense>
                    <narrative>{ifade_olay_metni}</narrative>
                    <bias_identified>{ifade_onyargi}</bias_identified>
                </defense>
            </input_data>

            <output_configuration>
                <format>
                    [Maddi Gerçek Metni]
                    ***
                    [XAI Gerekçelendirme]
                </format>
                <delimiter>***</delimiter>
            </output_configuration>
        </task_context>
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

        final_response = full_response.split("***")
        self.maddi_gercek = final_response[0]
        self.aciklama = final_response[1]       
        print(self.maddi_gercek)
        print(self.aciklama)

    def buyuk_onerme_eslestirme(self):
        """
        Maddi gerçek (Küçük Önerme) ile Türk Ceza Mevzuatı (Büyük Önerme) arasında 
        hukuki bağ kurar. İlgili TCK maddelerini tespit eder.
        """
        print("Büyük önerme (Kanun tespiti) yapılıyor...")

        user_prompt_content = f"""
        <task_context>
            <objective>Maddi Gerçeğe Uygun Türk Ceza Kanunu Maddelerini Tespit Etme</objective>
            
            <input_maddi_gercek>
                {self.maddi_gercek}
            </input_maddi_gercek>

            <instructions>
                1. Maddi gerçeği T.C. Mevzuatı açısından analiz et.
                2. Eylemdeki suç tipini (Kasten Yaralama, Tehdit, Hakaret vb.) belirle.
                3. Varsa nitelikli halleri (silahla işleme, kamu görevlisine karşı vb.) tespit et.
                4. Varsa hukuka uygunluk nedenlerini (Meşru Müdafaa vb.) veya kusurluluğu etkileyen halleri listele.
                5. Yanıtı mutlaka aşağıdaki JSON formatında, başka açıklama yapmadan dön.
            </instructions>

            <output_format>
                [
                    {{"id": "Madde No", "tur": "SUÇ_TANIMI/ARTIRIM/İNDİRİM/BERAAT", "metin": "Madde içeriği", "neden": "Neden bu madde seçildi?"}}
                ]
            </output_format>
        </task_context>
        """

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_prompt_content)
        ]

        # Yapılandırılmış çıktı almak için JSON formatını zorluyoruz
        response = self.llm_model.invoke(messages)
        
        # Basit bir parsing (Gelişmiş versiyonda with_structured_output önerilir)
        try:
            import json
            # LLM bazen ```json ... ``` içinde dönebilir, temizliyoruz
            cleaned_content = response.content.replace("```json", "").replace("```", "").strip()
            self.buyuk_onerme = json.loads(cleaned_content)
        except Exception as e:
            print(f"Büyük önerme parse hatası: {e}")
            # Hata durumunda boş liste veya fallback mekanizması
            self.buyuk_onerme = []

        for madde in self.buyuk_onerme:
            print(f"Tespit Edilen Dayanak: {madde.get('id')} - {madde.get('tur')}")

        

    def karar1(self):
        """
        Hibrit dilekçe işleminden sonra karara varılır.
        Şekli gerçek göz önünde bulundurulur.
        XXX: Buyuk Önerme + Küçük Önerme = Karar Mekanizmasına Uyulmalıdır.        

        """
        print("Karar1 Veriliyor.")

        user_prompt_content = f"""
        <task_context>
            <objective>Maddi Gerçeğe ve Büyük Önermeye Dayanarak Tarafsız ve Adil Karar Verme</objective>
            <examples>
                <example>
                    <input_data>
                        <minor_premise>
                            Sanık Ahmet, mağazadan bir telefonu parasını ödemeden cebine koyup dışarı çıkarken yakalanmıştır.
                        </minor_premise>
                        <major_premises>
                            Hırsızlık Suçu (Kanun Maddesi 141): Zilyedinin rızası olmadan başkasına ait taşınır bir malı, kendisine veya başkasına bir yarar sağlamak maksadıyla bulunduğu yerden alan kimseye ceza verilir.
                        </major_premises>
                    </input_data>
                    <output>
                        Sanık Ahmet, Hırsızlık suçundan suçlu bulunmuştur.
                        ***
                        Maddi gerçek incelendiğinde, Ahmet'in telefonu "bedelini ödemeden" ve "mağaza sahibinin rızası dışında" aldığı görülmüştür. Bu eylem, Büyük Önerme olan Kanun Maddesi 141'deki "zilyedinin rızası olmadan" ve "yarar sağlamak maksadıyla alma" unsurlarını tam olarak karşılamaktadır. Fiil ile kanun maddesi tam örtüştüğü için mahkumiyet kararı verilmiştir.
                    </output>
                </example>

                <example>
                    <input_data>
                        <minor_premise>
                            Davacı kiracı, kiraladığı evin kombisi bozulduğunda ev sahibine haber vermiş, ancak ev sahibi 1 ay boyunca onarım yapmamıştır. Kiracı kombiyi kendi yaptırıp bedelini kiradan düşmüştür.
                        </minor_premise>
                        <major_premises>
                            Borçlar Kanunu Madde 306: Kiralanan sonradan ayıplı duruma gelirse kiracı, kiraya verenden ayıbın giderilmesini isteyebilir. Kiraya veren, uygun sürede ayıbı gidermezse kiracı, ayıbı giderip masrafı kira bedelinden indirebilir.
                        </major_premises>
                    </input_data>
                    <output>
                        Kiracının masrafı kiradan düşmesi hukuka uygundur.
                        ***
                        Maddi gerçekte, "kombinin bozulması" (ayıp) ve ev sahibinin "1 ay boyunca işlem yapmaması" (uygun sürede gidermeme) durumları tespit edilmiştir. Büyük Önerme olan Madde 306, bu şartlar altında kiracıya "masrafı kiradan indirme" hakkı tanımaktadır. Kiracının eylemi, kanunun tanıdığı hakka dayandığı için onarım bedelinin kiradan mahsup edilmesi kararı verilmiştir.
                    </output>
                </example>

                <example>
                    <input_data>
                        <minor_premise>
                            Sürücü, otoyolda 120 km/s hız sınırının olduğu bölgede 115 km/s hızla seyrederken radara girmiştir.
                        </minor_premise>
                        <major_premises>
                            Trafik Kanunu Madde 51: Hız sınırlarını %10'dan fazla aşan sürücülere idari para cezası uygulanır.
                        </major_premises>
                    </input_data>
                    <output>
                        Sürücüye ceza uygulanmasına yer olmadığına karar verilmiştir.
                        ***
                        Maddi gerçek olan 115 km/s hız, büyük önermede belirtilen 120 km/s yasal sınırının altındadır. Büyük önerme, cezayı "sınırın aşılması" şartına bağlamıştır. Sürücü sınırı aşmadığı için, suçun veya kabahatin maddi unsurları oluşmamıştır. Bu sebeple ceza verilmemesi yönünde karar tesis edilmiştir.
                    </output>
                </example>
            </examples>

            <inputs>
                    <input name="minor_premise">
                        {self.maddi_gercek}
                    </input>
                    <input name="major_premises">
                        {self.buyuk_onerme}
                    </input>
                </inputs>

            <output_format>
                    <delimiter>***</delimiter>
                    <structure>
                        [Karar]
                        ***
                        [Detaylı Açıklama ve Gerekçe]
                    </structure>
            </output_format>
        </task_context>
        """
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_prompt_content)
        ]

        full_response = ""
        for chunk in self.llm_model.stream(messages):
            #print(chunk.content, end="", flush=True)
            full_response += chunk.content

        final_response = full_response.split("***")
        self.maddi_gercek = final_response[0]
        self.aciklama = final_response[1]       
        print(self.maddi_gercek)
        print(self.aciklama)
        
  
    
    def karar2(self):
        """
        RAG teknolojisiyle emsal kararlar çekilir ve Nihai Karar verilir.
        """
        print("\n>>> ADIM 4: Emsal Karar Denetimi ve Nihai Hüküm (RAG Devrede)...")

        # 1. RAG Sisteminden Emsal Karar çekiyoruz
        # Maddi gerçeği gönderiyoruz ki benzer olayları bulsun
        print("   [INFO] AnythingLLM veritabanında emsal karar aranıyor...")
        emsal_cevap = query_anything_llm(self.maddi_gercek)
        
        print(f"   [INFO] Emsal Kararlar Çekildi.")
        
        # 2. Nihai Sentez Prompt'u (LLM'e Son Emri Veriyoruz)
        final_prompt = f"""
        GÖREV: Sen LEXTR Yargıç Sistemisin. Aşağıdaki verileri kullanarak NİHAİ GEREKÇELİ KARARI ver.
        
        1. MADDİ GERÇEK (Olay): {self.maddi_gercek}
        2. İLK HUKUKİ DEĞERLENDİRME: {getattr(self, 'aciklama', 'İlk karar açıklaması bulunamadı.')}
        3. EMSAL KARARLAR (İçtihat): {emsal_cevap}
        
        YÖNERGE: 
        - İlk kararı, bulunan emsal kararlarla karşılaştır (Denetim).
        - Eğer emsal kararlar ilk kararı destekliyorsa onayla ve emsalden alıntı yap.
        - Eğer çelişki varsa, emsal karardaki yüksek mahkeme içtihadına uyarak kararı revize et.
        - Sonucu "TÜRK MİLLETİ ADINA" başlığıyla resmi bir hüküm fıkrası olarak yaz.
        """

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=final_prompt)
        ]

        print("   [INFO] Nihai karar yazılıyor...")
        
       
        full_response = ""
        try:
            for chunk in self.llm_model.stream(messages):
                print(chunk.content, end="", flush=True) # Ekrana canlı yazdır
                full_response += chunk.content
            
            self.karar = full_response # Sonucu kaydet
            
        except Exception as e:
            print(f"\n   [HATA] Nihai karar üretilirken hata oluştu: {e}")


def main():
    print("LEXTR - Hukuk Karar Destek Sistemine Hoş Geldiniz!")
    
    # Modeli Başlat
    
    model = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", 
        temperature=TEMPERATURE,
        timeout=TIMEOUT,
        max_tokens=MAX_TOKENS,
        
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
            buyuk_onerme="",
            rapor=""
        )
    

    elif secim == 1:
        print("Hukuk davası henüz implemente edilmedi.")
    


if __name__ == "__main__":
    main()

