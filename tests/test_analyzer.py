import pytest

from analyzer import kodu_tara, fonksiyon_durumlarini_hesapla


TARAMA_DURUMLARI = [
    (
        "unsafe_gets_detected",
        "int main(){ char buf[16]; gets(buf); return 0; }",
        {"gets"},
    ),
    (
        "unsafe_scanf_percent_s_detected",
        'int main(){ char name[10]; scanf("%s", name); return 0; }',
        {"scanf"},
    ),
    (
        "safe_copy_not_reported",
        "int main(){ char a[10]; char b[10]; memcpy(a, b, sizeof(a)); return 0; }",
        set(),
    ),
    (
        "format_string_vulnerability_detected",
        "int main(){ char *user_input; printf(user_input); return 0; }",
        {"printf"},
    ),
    (
        "mixed_multiple_vulnerabilities",
        'int main(){ char b[8]; gets(b); sprintf(b, "%s", "x"); return 0; }',
        {"gets", "sprintf"},
    ),
    (
        "safe_strncat_remaining_space_not_reported",
        'int main(){ char dest[32] = "A"; char src[8] = "B"; strncat(dest, src, sizeof(dest) - strlen(dest) - 1); return 0; }',
        set(),
    ),
    (
        "line_comment_ignored",
        "int main(){ // gets(buf);\n return 0; }",
        set(),
    ),
    (
        "block_comment_ignored",
        "int main(){ /* strcpy(dst, src); */ return 0; }",
        set(),
    ),
    (
        "comment_null_does_not_hide_free_issue",
        "int main(){ free(ptr); // NULL yazildi ama yorum\n return 0; }",
        {"free"},
    ),
]

FONKSIYON_DURUMU_DURUMLARI = [
    (
        "gets_marked_vulnerable",
        "int main(){ char b[8]; gets(b); return 0; }",
        {"gets": {"durum": "zafiyetli", "kullanim_sayisi": 1, "bulgu_sayisi": 1}},
    ),
    (
        "safe_scanf_marked_safe",
        'int main(){ char b[8]; scanf("%7s", b); return 0; }',
        {"scanf": {"durum": "guvenli", "kullanim_sayisi": 1, "bulgu_sayisi": 0}},
    ),
    (
        "unused_function_marked_unused",
        'int main(){ printf("%s", "ok"); return 0; }',
        {"system": {"durum": "kullanilmadi", "kullanim_sayisi": 0, "bulgu_sayisi": 0}},
    ),
    (
        "variant_normalized_for_usage_and_findings",
        "int main(){ strncat(dst, src, strlen(src)); return 0; }",
        {"strcat": {"durum": "zafiyetli", "kullanim_sayisi": 1, "bulgu_sayisi": 1}},
    ),
    (
        "safe_strncat_marked_safe",
        "int main(){ strncat(dest, src, sizeof(dest) - strlen(dest) - 1); return 0; }",
        {"strcat": {"durum": "guvenli", "kullanim_sayisi": 1, "bulgu_sayisi": 0}},
    ),
    (
        "commented_usage_is_not_counted",
        "int main(){ // gets(buf);\n return 0; }",
        {"gets": {"durum": "kullanilmadi", "kullanim_sayisi": 0, "bulgu_sayisi": 0}},
    ),
]


@pytest.mark.parametrize(
    "c_kodu, beklenen_fonksiyonlar",
    [durum[1:] for durum in TARAMA_DURUMLARI],
    ids=[durum[0] for durum in TARAMA_DURUMLARI],
)
def test_kodu_tara(c_kodu, beklenen_fonksiyonlar):
    bulunan_fonksiyonlar = {bulgu["fonksiyon"] for bulgu in kodu_tara(c_kodu)}
    assert bulunan_fonksiyonlar == beklenen_fonksiyonlar


@pytest.mark.parametrize(
    "c_kodu, beklenen",
    [durum[1:] for durum in FONKSIYON_DURUMU_DURUMLARI],
    ids=[durum[0] for durum in FONKSIYON_DURUMU_DURUMLARI],
)
def test_fonksiyon_durumlarini_hesapla(c_kodu, beklenen):
    durum_haritasi = fonksiyon_durumlarini_hesapla(c_kodu)
    for fonksiyon, beklenen_bilgi in beklenen.items():
        for anahtar, beklenen_deger in beklenen_bilgi.items():
            assert durum_haritasi[fonksiyon][anahtar] == beklenen_deger
