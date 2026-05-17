# analyzer.py
from typing import List, Dict, Optional

# --- SİSTEM MİMARİSİ (Buna dokunmuyoruz) ---
TARAMA_KURALLARI = []
IZLENEN_FONKSIYONLAR = [
    "gets",
    "scanf",
    "memcpy",
    "strcpy",
    "sprintf",
    "strcat",
    "free",
    "system",
    "printf",
]
FONKSIYON_AILELERI = {
    "gets": ["gets"],
    "scanf": ["scanf", "sscanf", "fscanf", "vscanf", "vsscanf", "vfscanf"],
    "memcpy": ["memcpy"],
    "strcpy": ["strcpy", "strncpy"],
    "sprintf": ["sprintf"],
    "strcat": ["strcat", "strncat"],
    "free": ["free"],
    "system": ["system"],
    "printf": ["printf"],
}
FONKSIYON_NORMALIZASYON_HARITASI = {
    "sscanf": "scanf",
    "fscanf": "scanf",
    "vscanf": "scanf",
    "vsscanf": "scanf",
    "vfscanf": "scanf",
    "strncpy": "strcpy",
    "strncat": "strcat",
}

def zafiyet_kurali(func):
    """Sizin yazdığınız fonksiyonları otomatik olarak tarayıcıya ekler."""
    TARAMA_KURALLARI.append(func)
    return func

# --- YARDIMCI FONKSİYONLAR (Regex yok) ---
def kelimeleri_cikar(satir: str) -> List[str]:
    """Satırdaki noktalama işaretlerini temizler ve saf kelimeleri ayıklar."""
    kelimeler = []
    mevcut = []
    for char in satir:
        if char.isalnum() or char == '_':
            mevcut.append(char)
        else:
            if mevcut:
                kelimeler.append("".join(mevcut))
                mevcut = []
    if mevcut:
        kelimeler.append("".join(mevcut))
    return kelimeler

def parantez_icini_al(satir: str, fonksiyon_adi: str) -> str:
    """Belirtilen fonksiyonun parantez içindeki kısmını döndürür."""
    baslangic = satir.find(fonksiyon_adi + "(")
    if baslangic == -1:
        baslangic = satir.find(fonksiyon_adi + " (") # Boşluklu yazım ihtimali
    
    if baslangic == -1: 
        return ""
    
    ilk_parantez = satir.find("(", baslangic)
    depth = 0
    for i in range(ilk_parantez, len(satir)):
        if satir[i] == "(": 
            depth += 1
        elif satir[i] == ")": 
            depth -= 1
        
        if depth == 0:
            return satir[ilk_parantez+1:i]
    return ""

def argumanlari_ayir(arguman_str: str) -> List[str]:
    """Parantez içini bozmadan parametreleri virgüllere göre ayırır."""
    args, depth, current = [], 0, []
    for ch in arguman_str:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        if ch == "," and depth == 0:
            args.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    if current:
        args.append("".join(current).strip())
    return args


def c_yorumlarini_temizle(c_kodu: str) -> str:
    sonuc = []
    i = 0
    uzunluk = len(c_kodu)
    satir_ici_yorum = False
    blok_yorum = False
    metin_ici = False
    metin_siniri = ""
    kacis = False

    while i < uzunluk:
        ch = c_kodu[i]
        sonraki = c_kodu[i + 1] if i + 1 < uzunluk else ""

        if satir_ici_yorum:
            if ch == "\n":
                satir_ici_yorum = False
                sonuc.append("\n")
            i += 1
            continue

        if blok_yorum:
            if ch == "*" and sonraki == "/":
                blok_yorum = False
                i += 2
                continue
            if ch == "\n":
                sonuc.append("\n")
            i += 1
            continue

        if metin_ici:
            sonuc.append(ch)
            if kacis:
                kacis = False
            elif ch == "\\":
                kacis = True
            elif ch == metin_siniri:
                metin_ici = False
                metin_siniri = ""
            i += 1
            continue

        if ch in ['"', "'"]:
            metin_ici = True
            metin_siniri = ch
            sonuc.append(ch)
            i += 1
            continue

        if ch == "/" and sonraki == "/":
            satir_ici_yorum = True
            i += 2
            continue

        if ch == "/" and sonraki == "*":
            blok_yorum = True
            i += 2
            continue

        sonuc.append(ch)
        i += 1

    return "".join(sonuc)


def ifadeyi_normalize_et(ifade: str) -> str:
    return "".join(ch for ch in ifade if not ch.isspace())


def dis_parantezleri_soy(ifade: str) -> str:
    ifade = ifade.strip()
    while ifade.startswith("(") and ifade.endswith(")"):
        depth = 0
        tumunu_kapsiyor = True
        for idx, ch in enumerate(ifade):
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0 and idx != len(ifade) - 1:
                    tumunu_kapsiyor = False
                    break
        if tumunu_kapsiyor and depth == 0:
            ifade = ifade[1:-1].strip()
        else:
            break
    return ifade


def strncat_kalan_alan_hesabi_mi(hedef_arg: str, boyut_arg: str) -> bool:
    hedef_normalize = ifadeyi_normalize_et(dis_parantezleri_soy(hedef_arg))
    boyut_normalize = ifadeyi_normalize_et(dis_parantezleri_soy(boyut_arg))

    guvenli_ifadeler = {
        f"sizeof({hedef_normalize})-strlen({hedef_normalize})-1",
        f"sizeof({hedef_normalize})-1-strlen({hedef_normalize})",
        f"(sizeof({hedef_normalize})-strlen({hedef_normalize}))-1",
        f"sizeof({hedef_normalize})-(strlen({hedef_normalize})+1)",
    }
    return boyut_normalize in guvenli_ifadeler

# =========================================================
# EKİP ÜYELERİNİN KODLAMA ALANLARI
# Kural: Zafiyet bulursan sözlük (Dict) döndür, bulamazsan None döndür.
# =========================================================

# --- FURKAN'IN BÖLGESİ (gets, scanf, memcpy) ---

@zafiyet_kurali
def kural_gets(satir_no: int, satir_icerik: str) -> Dict:
    # 1. Satırdaki noktalama işaretlerini atıp saf kelimeleri listele
    kelimeler = kelimeleri_cikar(satir_icerik)
    
    # 2. Eğer "gets" kelimesi tam eşleşme olarak listedeyse, zafiyet kesindir
    if "gets" in kelimeler:
        return {
            "fonksiyon": "gets",
            "satir_no": satir_no,
            "kod_satiri": satir_icerik.strip(), # Baştaki/sondaki boşlukları temizler
            "siddet": "yüksek",
            "sebep": "gets() fonksiyonu alınan verinin boyutunu kontrol etmez. Bu durum kesin bir Buffer Overflow (Tampon Taşması) zafiyeti oluşturur. Yerine fgets() kullanılmalıdır."
        }
        
    # 3. Bulamazsa temiz olduğunu belirtmek için None döndür
    return None

@zafiyet_kurali
def kural_scanf(satir_no: int, satir_icerik: str) -> Dict:
    kelimeler = kelimeleri_cikar(satir_icerik)
    scanf_turevleri = ["scanf", "sscanf", "fscanf", "vscanf", "vsscanf", "vfscanf"]
    
    # 1. Satırda scanf veya türevlerinden biri var mı?
    bulunan_fonk = None
    for fonk in scanf_turevleri:
        if fonk in kelimeler:
            bulunan_fonk = fonk
            break
            
    if not bulunan_fonk:
        return None

    # 2. Format stringi (tırnak içindeki metni) bul
    ilk_tirnak = satir_icerik.find('"')
    ikinci_tirnak = satir_icerik.find('"', ilk_tirnak + 1)
    
    # Eğer tırnak yoksa, format metni dışarıdan değişken olarak geliyordur (Riskli)
    if ilk_tirnak == -1 or ikinci_tirnak == -1:
        return {
            "fonksiyon": bulunan_fonk,
            "satir_no": satir_no,
            "kod_satiri": satir_icerik.strip(),
            "siddet": "orta",
            "sebep": f"{bulunan_fonk}() fonksiyonunda format metni dışarıdan bir değişken olarak veriliyor. Genişlik kontrolü doğrulanamadığı için risklidir."
        }

    format_kismi = satir_icerik[ilk_tirnak:ikinci_tirnak+1]
    
    # 3. Yüzde (%) işaretlerine göre metni böl
    parcalar = format_kismi.split('%')
    
    # Formattan önceki ilk parçayı atla, kalanları incele
    for parca in parcalar[1:]: 
        if not parca: # Eğer "%%" yazılmışsa boş parça gelir, onu atla
            continue
            
        ilk_karakter = parca[0]
        
        # Eğer parça s, S veya [ ile başlıyorsa, önünde rakam (genişlik) yoktur!
        if ilk_karakter in ['s', 'S']:
            return {
                "fonksiyon": bulunan_fonk,
                "satir_no": satir_no,
                "kod_satiri": satir_icerik.strip(),
                "siddet": "yüksek",
                "sebep": f"{bulunan_fonk}() içinde '%s' genişlik belirteci olmadan kullanılmış. Tampon taşması (Buffer Overflow) kesindir."
            }
        elif ilk_karakter == '[':
            return {
                "fonksiyon": bulunan_fonk,
                "satir_no": satir_no,
                "kod_satiri": satir_icerik.strip(),
                "siddet": "yüksek",
                "sebep": f"{bulunan_fonk}() içinde '%[...]' alan belirteci genişliksiz kullanılmış. Tampon taşması (Buffer Overflow) mümkündür."
            }

    # %d, %f, %10s gibi güvenli kullanımları geçerse sorun yok
    return None

@zafiyet_kurali
def kural_memcpy(satir_no: int, satir_icerik: str) -> Dict:
    kelimeler = kelimeleri_cikar(satir_icerik)
    if "memcpy" not in kelimeler:
        return None

    # 1. memcpy'nin parantez içindeki parametrelerini ayıkla
    param_str = parantez_icini_al(satir_icerik, "memcpy")
    argumanlar = argumanlari_ayir(param_str)

    # 2. Eğer 3 parametreden azsa kod zaten hatalıdır
    if len(argumanlar) < 3:
        return {
            "fonksiyon": "memcpy",
            "satir_no": satir_no,
            "kod_satiri": satir_icerik.strip(),
            "siddet": "yüksek",
            "sebep": "memcpy çağrısında eksik argüman var. Boyut belirtilmemiş olabilir."
        }

    boyut_argumani = argumanlar[2]
    boyut_kelimeleri = kelimeleri_cikar(boyut_argumani)

    # 3. Risk analiz mantığı
    if "sizeof" in boyut_kelimeleri:
        # sizeof(hedef) güvenli kabul edilir
        return None 
    elif "strlen" in boyut_kelimeleri:
        # strlen(kaynak) kullanıldıysa yüksek risklidir
        return {
            "fonksiyon": "memcpy",
            "satir_no": satir_no,
            "kod_satiri": satir_icerik.strip(),
            "siddet": "yüksek",
            "sebep": "memcpy() boyut argümanı olarak 'strlen(kaynak)' kullanılmış. Eğer kaynak veri hedef tampondan büyükse Buffer Overflow zafiyeti oluşur. Boyut sınırlandırılmalıdır."
        }
    elif boyut_argumani.isdigit():
        # Sabit bir sayı yazıldıysa (örn: 50) hedef tampon boyutuyla eşleşmeyebilir
        return {
            "fonksiyon": "memcpy",
            "satir_no": satir_no,
            "kod_satiri": satir_icerik.strip(),
            "siddet": "orta",
            "sebep": f"memcpy() boyut argümanı sabit bir sayı ({boyut_argumani}) olarak kodlanmış. Hedef tampon boyutuyla eşleşmediği durumlarda taşma riski taşır."
        }
    else:
        # Dışarıdan gelen başka bir değişkense risk durumudur
        return {
            "fonksiyon": "memcpy",
            "satir_no": satir_no,
            "kod_satiri": satir_icerik.strip(),
            "siddet": "orta",
            "sebep": f"memcpy() boyut argümanı bir değişken ({boyut_argumani}). Hedef tampon boyutuyla ilişkisi doğrulanamadığı için risklidir."
        }


# --- TAYLAN'IN BÖLGESİ (strcpy, sprintf, strcat) ---

@zafiyet_kurali
def kural_strcpy(satir_no: int, satir_icerik: str) -> Dict:
    kelimeler = kelimeleri_cikar(satir_icerik)
    
    # 1. Eğer strncpy kullanılmışsa programcının boyut hatasını incele
    if "strncpy" in kelimeler:
        param_str = parantez_icini_al(satir_icerik, "strncpy")
        argumanlar = argumanlari_ayir(param_str)
        if len(argumanlar) >= 3:
            boyut_arg = argumanlar[2]
            # strncpy(h, k, strlen(k)) yazıldıysa güvenli fonksiyon güvensiz hale gelmiştir!
            if "strlen" in boyut_arg:
                return {
                    "fonksiyon": "strncpy",
                    "satir_no": satir_no,
                    "kod_satiri": satir_icerik.strip(),
                    "siddet": "yüksek",
                    "sebep": "strncpy() fonksiyonunda boyut parametresi olarak 'strlen(kaynak)' kullanılmış. Bu kullanım fonksiyonun sınır koruma amacını yok eder ve Buffer Overflow riski doğurur."
                }
        return None

    # 2. Standart strcpy tespiti (Doğrudan zafiyettir)
    if "strcpy" in kelimeler:
        return {
            "fonksiyon": "strcpy",
            "satir_no": satir_no,
            "kod_satiri": satir_icerik.strip(),
            "siddet": "yüksek",
            "sebep": "strcpy() fonksiyonu hedef tamponun boyutunu kontrol etmeden kopyalama yapar. Buffer Overflow zafiyeti riski çok yüksektir. Yerine sınır belirtebilen strncpy() tercih edilmelidir."
        }
    return None


@zafiyet_kurali
def kural_sprintf(satir_no: int, satir_icerik: str) -> Dict:
    kelimeler = kelimeleri_cikar(satir_icerik)
    
    # snprintf güvenli sürümdür, eğer o varsa geç
    if "snprintf" in kelimeler:
        return None

    if "sprintf" in kelimeler:
        return {
            "fonksiyon": "sprintf",
            "satir_no": satir_no,
            "kod_satiri": satir_icerik.strip(),
            "siddet": "yüksek",
            "sebep": "sprintf() fonksiyonu verileri hedef tampona yazarken boyut kontrolü yapmaz. Uzun girdilerde hedef tamponun taşmasına (Buffer Overflow) neden olur. Yerine snprintf() kullanılmalıdır."
        }
    return None


@zafiyet_kurali
def kural_strcat(satir_no: int, satir_icerik: str) -> Dict:
    kelimeler = kelimeleri_cikar(satir_icerik)
    
    # 1. strncat (güvenli sürüm) hata analizi
    if "strncat" in kelimeler:
        param_str = parantez_icini_al(satir_icerik, "strncat")
        argumanlar = argumanlari_ayir(param_str)
        if len(argumanlar) >= 3:
            hedef_arg = argumanlar[0]
            boyut_arg = argumanlar[2]
            if strncat_kalan_alan_hesabi_mi(hedef_arg, boyut_arg):
                return None
            if "strlen" in boyut_arg:
                return {
                    "fonksiyon": "strncat",
                    "satir_no": satir_no,
                    "kod_satiri": satir_icerik.strip(),
                    "siddet": "yüksek",
                    "sebep": "strncat() içinde boyut olarak 'strlen' kullanılmış. Hedef tamponun zaten dolu olan kısmını hesaba katmadığı için taşma riski oluşturur."
                }
        return None

    # 2. Standart strcat tespiti
    if "strcat" in kelimeler:
        return {
            "fonksiyon": "strcat",
            "satir_no": satir_no,
            "kod_satiri": satir_icerik.strip(),
            "siddet": "yüksek",
            "sebep": "strcat() fonksiyonu iki metni birleştirirken hedef tamponun sınırlarını denetlemez. Mevcut verinin üzerine ekleme yapıldığı için Buffer Overflow riski çok yüksektir. Yerine strncat() kullanılmalıdır."
        }
    return None


# --- ALARA'IN BÖLGESİ (free, system, printf) ---

@zafiyet_kurali
def kural_free(satir_no: int, satir_icerik: str) -> Dict:
    kelimeler = kelimeleri_cikar(satir_icerik)
    
    if "free" in kelimeler:
        # Eğer satırın içinde veya o satırdaki açıklamalarda NULL kelimesi geçmiyorsa uyar
        if "NULL" not in satir_icerik:
            return {
                "fonksiyon": "free",
                "satir_no": satir_no,
                "kod_satiri": satir_icerik.strip(),
                "siddet": "orta",
                "sebep": "Bellek alanı free() ile serbest bırakılmış ancak aynı satırda pointer NULL'a eşitlenmemiş olabilir. Bu durum Use-After-Free veya Double Free zafiyetlerine zemin hazırlar. free(ptr); ptr = NULL; şeklinde güvenli hale getirilmelidir."
            }
    return None


@zafiyet_kurali
def kural_system(satir_no: int, satir_icerik: str) -> Dict:
    kelimeler = kelimeleri_cikar(satir_icerik)
    
    if "system" in kelimeler:
        param_str = parantez_icini_al(satir_icerik, "system")
        
        # Eğer parametre kısmında hiç tırnak yoksa, doğrudan bir değişken gönderiliyordur (Çok Tehlikeli!)
        if '"' not in param_str:
            return {
                "fonksiyon": "system",
                "satir_no": satir_no,
                "kod_satiri": satir_icerik.strip(),
                "siddet": "yüksek",
                "sebep": "system() fonksiyonuna doğrudan sanitize edilmemiş (temizlenmemiş) bir değişken verilmiş. Bu durum çok ciddi bir Command Injection (Komut Enjeksiyonu) zafiyeti oluşturur."
            }
    return None


@zafiyet_kurali
def kural_printf(satir_no: int, satir_icerik: str) -> Dict:
    kelimeler = kelimeleri_cikar(satir_icerik)
    
    # fprintf, snprintf gibi türevleri değil, sadece saf printf'i hedefliyoruz
    if "printf" in kelimeler and "snprintf" not in kelimeler and "fprintf" not in kelimeler:
        param_str = parantez_icini_al(satir_icerik, "printf")
        argumanlar = argumanlari_ayir(param_str)
        
        if argumanlar:
            ilk_arguman = argumanlar[0].strip()
            
            # Eğer ilk argüman bir tırnak işareti ile başlamıyorsa, format string bir değişkendir!
            if not ilk_arguman.startswith('"'):
                return {
                    "fonksiyon": "printf",
                    "satir_no": satir_no,
                    "kod_satiri": satir_icerik.strip(),
                    "siddet": "yüksek",
                    "sebep": "Format String Zafiyeti: printf() fonksiyonunun ilk argümanı sabit bir metin (\"...\") değil, doğrudan bir değişkendir. Kullanıcı girdisiyle manipüle edilerek bellek sızıntısına veya çökmesine yol açabilir. printf(\"%s\", degisken); şeklinde düzeltilmelidir."
                }
    return None


# --- ANA TARAMA MOTORU ---
def kodu_tara(c_kodu: str) -> List[Dict]:
    bulunan_zafiyetler = []
    temiz_kod = c_yorumlarini_temizle(c_kodu)
    satirlar = temiz_kod.splitlines()
    
    for i, satir in enumerate(satirlar):
        satir_no = i + 1
        
        # Ekip üyelerinin yazdığı tüm kuralları çalıştır
        for kural in TARAMA_KURALLARI:
            sonuc = kural(satir_no, satir)
            if sonuc: # Eğer kural bir zafiyet sözlüğü döndürdüyse listeye ekle
                bulunan_zafiyetler.append(sonuc)
                
    return bulunan_zafiyetler


def fonksiyon_kullanim_sayilarini_hesapla(c_kodu: str) -> Dict[str, int]:
    kullanim_sayaci = {fonksiyon: 0 for fonksiyon in IZLENEN_FONKSIYONLAR}
    temiz_kod = c_yorumlarini_temizle(c_kodu)

    for satir in temiz_kod.splitlines():
        kelimeler = kelimeleri_cikar(satir)
        for fonksiyon, varyantlar in FONKSIYON_AILELERI.items():
            satir_toplami = 0
            for varyant in varyantlar:
                satir_toplami += kelimeler.count(varyant)
            kullanim_sayaci[fonksiyon] += satir_toplami

    return kullanim_sayaci


def fonksiyon_durumlarini_hesapla(c_kodu: str, zafiyetler: Optional[List[Dict]] = None) -> Dict[str, Dict]:
    if zafiyetler is None:
        zafiyetler = kodu_tara(c_kodu)

    kullanim_sayaci = fonksiyon_kullanim_sayilarini_hesapla(c_kodu)
    bulgu_sayaci = {fonksiyon: 0 for fonksiyon in IZLENEN_FONKSIYONLAR}

    for bulgu in zafiyetler:
        bulunan_fonksiyon = bulgu.get("fonksiyon", "")
        bulunan_fonksiyon = FONKSIYON_NORMALIZASYON_HARITASI.get(bulunan_fonksiyon, bulunan_fonksiyon)
        if bulunan_fonksiyon in bulgu_sayaci:
            bulgu_sayaci[bulunan_fonksiyon] += 1

    sonuc = {}
    for fonksiyon in IZLENEN_FONKSIYONLAR:
        kullanim_sayisi = kullanim_sayaci[fonksiyon]
        bulgu_sayisi = bulgu_sayaci[fonksiyon]
        guvenli_kullanim = max(kullanim_sayisi - bulgu_sayisi, 0)

        if kullanim_sayisi == 0:
            durum = "kullanilmadi"
        elif bulgu_sayisi > 0:
            durum = "zafiyetli"
        else:
            durum = "guvenli"

        sonuc[fonksiyon] = {
            "zafiyetli": bulgu_sayisi > 0,
            "durum": durum,
            "kullanim_sayisi": kullanim_sayisi,
            "bulgu_sayisi": bulgu_sayisi,
            "guvenli_kullanim_sayisi": guvenli_kullanim,
        }

    return sonuc
