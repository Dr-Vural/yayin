# cv.mahmutvural.net: yayın arşivi entegrasyonu

**Amaç:** CV sitesindeki her yayın, yayin.mahmutvural.net'teki kendi sayfasına ve tam metin PDF'ine bağlansın. Böylece okuyan kişi tek tıkla dosyaya ulaşır, Google Akademik de aynı kalıcı adresleri görür.

**Kapsam dışı:** Sitenin tasarımı, dil yapısı, kadranlar ve diğer bölümler değişmez. Yalnızca yayın listesine bağlantılar eklenir.

## Kaynak

- Arşiv: `https://yayin.mahmutvural.net/`
- Makine okunur liste: `https://yayin.mahmutvural.net/yayinlar.json` (CORS açık, 10 dakika önbellek)
- Her kayıtta `id` alanı panelin `_id` değeridir; `veri/sicil.json` içindeki yayın kayıtlarının `_id` alanıyla birebir eşleşir.

`yayinlar.json` kaydından ilgili alanlar:

| Alan | Örnek | Anlamı |
|---|---|---|
| `id` | `16lnm32fv` | Panel kimliği |
| `url` | `https://yayin.mahmutvural.net/2026-vural-when-measure-fails-before-model-does-generative/` | Yayının arşiv sayfası (künye, özet, atıf) |
| `pdf` | `https://yayin.mahmutvural.net/.../....pdf` ya da `null` | Tam metin. Kitap bölümlerinde `null` (telif) |
| `kapak` | `.../kapak.webp` ya da `null` | İlk sayfa görseli (420 px) |
| `bibtex` | `.../....bib` | Tek kayıtlık BibTeX |

## Yapılacaklar

1. **Veri:** `araclar/build_pubs.py` derleme sırasında arşiv listesini okur. Ağ bağlantısına bağımlı olmamak için listenin bir kopyası `veri/yayin_arsivi.json` olarak depoya konur ve derleme bu dosyadan okur. Kopya, her derlemeden önce `curl -s https://yayin.mahmutvural.net/yayinlar.json -o veri/yayin_arsivi.json` ile yenilenir. `veri_hazirla.py` bu dosyaya dokunmaz.
2. **Eşleştirme:** Her yayın kaydı `_id` ile arşivdeki `id` ile eşleştirilir. Eşleşmeyen kayıt (yayımlanmamış çalışma, örneğin Triple Decoupling) bağlantısız kalır; hata vermez.
3. **Bağlantılar:** `doi_line()` satırının yanına aynı biçimde bir bağlantı satırı eklenir:
   - `pdf` doluysa: **Tam metin (PDF)** bağlantısı `pdf` adresine.
   - Her eşleşen kayıtta: **Yayın sayfası** bağlantısı `url` adresine. Etiketler dört dilde: TR "Tam metin (PDF)" / "Yayın sayfası", EN "Full text (PDF)" / "Publication page", RU "Полный текст (PDF)" / "Страница публикации", KY "Толук текст (PDF)" / "Басылманын бети".
   - DOI bağlantısı olduğu gibi kalır.
4. **Başlık bağlantısı:** Yayın başlığı `url` adresine bağlanır (yeni sekmede değil, aynı sekmede açılabilir; sitenin mevcut dış bağlantı düzenine uyulur).
5. **Kısa yol:** Yayınlar bölümünün başına "Tüm yayınlar ve tam metinler: yayin.mahmutvural.net" bağlantısı eklenir.
6. **Denetim:** `araclar/audit.py` için iki kontrol eklenir: (a) arşivde `pdf` alanı dolu her kaydın sayfada PDF bağlantısı var, (b) sayfadaki her yayin.mahmutvural.net bağlantısı arşiv listesindeki bir `url` ya da `pdf` değeridir.
7. **Bağlantılar bölümü:** Profil bağlantılarına "Yayın arşivi" (yayin.mahmutvural.net) eklenir.

## Kabul ölçütleri

1. Sitede PDF'i olan 32 yayının her birinde çalışan bir "Tam metin (PDF)" bağlantısı var; üç kitap bölümünde yalnızca "Yayın sayfası" var.
2. Bağlantılar dört dilde doğru etiketle görünür.
3. `audit.py` ve `node araclar/test/yayin.mjs` hatasız geçer.
4. Arşivde olmayan bir kayıt derlemeyi bozmaz.
