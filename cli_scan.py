from analyzer import kodu_tara, fonksiyon_durumlarini_hesapla


def c_kodunu_oku() -> str:
    print("C kodunu yapistirin.")
    print("Bitirmek icin bos bir satira Enter basin.\n")

    satirlar = []
    while True:
        try:
            satir = input()
        except EOFError:
            break

        if satir == "":
            break
        satirlar.append(satir)

    return "\n".join(satirlar)


def sonucu_yazdir(zafiyetler, fonksiyon_durumlari):
    print("\n=== 9 Fonksiyon Icin Analiz Sonucu ===")
    for fonksiyon, bilgi in fonksiyon_durumlari.items():
        if bilgi["durum"] == "kullanilmadi":
            durum = "Kullanilmadi"
        elif bilgi["durum"] == "zafiyetli":
            durum = "Zafiyetli"
        else:
            durum = "Guvenli"

        print(
            f"{fonksiyon:8} -> {durum} "
            f"(kullanim: {bilgi['kullanim_sayisi']}, bulgu: {bilgi['bulgu_sayisi']})"
        )

    if not zafiyetler:
        print("\nDetayli bulgu yok.")
        return

    print("\n=== Detayli Bulgular ===")
    for index, bulgu in enumerate(zafiyetler, start=1):
        print(
            f"{index}. [{bulgu['siddet'].upper()}] Satir {bulgu['satir_no']} - "
            f"{bulgu['fonksiyon']}: {bulgu['sebep']}"
        )


if __name__ == "__main__":
    c_kodu = c_kodunu_oku()
    if not c_kodu.strip():
        print("Kod girilmedi.")
        raise SystemExit(1)

    bulunan_zafiyetler = kodu_tara(c_kodu)
    fonksiyon_durumlari = fonksiyon_durumlarini_hesapla(c_kodu, bulunan_zafiyetler)
    sonucu_yazdir(bulunan_zafiyetler, fonksiyon_durumlari)
