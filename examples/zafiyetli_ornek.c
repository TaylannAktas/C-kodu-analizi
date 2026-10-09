/*
 * Tarayıcıyı denemek için bilerek zafiyetli yazılmış örnek program.
 * Gerçek bir projede KULLANMAYIN.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char *argv[]) {
    char ad[16];
    char mesaj[32];
    char komut[64];
    char *kopya = malloc(64);

    gets(ad);                               /* sınırsız okuma */
    scanf("%s", mesaj);                     /* genişliksiz %s */
    scanf("%31s", mesaj);                   /* güvenli: genişlik verilmiş */

    strcpy(kopya, argv[1]);                 /* boyut kontrolü yok */
    strcat(mesaj, ad);                      /* boyut kontrolü yok */
    strncat(mesaj, ad, sizeof(mesaj) - strlen(mesaj) - 1);  /* güvenli */

    sprintf(komut, "echo %s", ad);          /* boyut kontrolü yok */
    memcpy(kopya, ad, strlen(ad));          /* boyut kaynaktan alınıyor */
    memcpy(kopya, ad, sizeof(ad));          /* güvenli kabul edilir */

    printf(ad);                             /* format string */
    printf("%s\n", ad);                     /* güvenli */
    system(komut);                          /* komut enjeksiyonu */

    free(kopya);                            /* serbest bırakıldı, NULL atanmadı */
    return 0;
}
