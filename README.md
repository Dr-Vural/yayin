# yayin.mahmutvural.net

Dr. Mahmut Vural'ın yayın arşivi: her yayına künye, özet, atıf (APA, BibTeX, RIS) ve tam metin PDF'i olan ayrı bir sayfa. Sayfalar Google Akademik'in okuduğu `citation_*` etiketlerini taşır; böylece Google Akademik profilindeki kayıtların yanında "[PDF] mahmutvural.net" bağlantısı çıkar.

**Yayın:** GitHub (`Dr-Vural/yayin`, `main`) -> Cloudflare Pages (`yayin`), alan adı `yayin.mahmutvural.net`.
**Derleme komutu:** `python3 build.py` · **Çıktı klasörü:** `site`

## Depo düzeni

| Yol | İçerik |
|---|---|
| `data/yayinlar.json` | Yayın kayıtları. Kaynak: panel.mahmutvural.net, `akademik_sicil_v1` > `yayinlar`. Yalnızca yayımlanmış çalışmalar. |
| `pdf/<_id>.pdf` | Tam metin, yazarın "Paylaşılabilir Sürüm"ü (kapaklı). Kitap bölümlerinin PDF'i konmaz. |
| `covers/<_id>.webp` | PDF'in ilk sayfasından üretilen kapak görseli (420 px). |
| `assets/` | Stil, betik, simge. |
| `build.py` | Statik site üreteci (yalnızca Python standart kitaplığı). |
| `araclar/kapak.py` | Yeni PDF'ler için kapak görseli üretir (`pypdfium2`, `Pillow`). |
| `docs/` | CV sitesi ve mahmutvural.net için entegrasyon talimatları. |

## Yeni yayın ekleme

1. Kaydı panele girin (künye, özet, anahtar kelimeler).
2. Paneldeki kaydı `data/yayinlar.json` dosyasına ekleyin (`_id` aynı kalır).
3. PDF'i `pdf/<_id>.pdf` olarak koyun, `python3 araclar/kapak.py` çalıştırın.
4. `python3 build.py` ile yerelde deneyin, `main` dalına gönderin. Cloudflare yayına alır.

Adresler (`/<yıl>-<ilk yazar>-<başlık>/`) bir kez yayımlandıktan sonra değiştirilmez; Google Akademik bu adresleri tanır.

## Çıktılar

- `/` ana sayfa: tür filtresi ve arama
- `/<slug>/` yayın sayfası, `/<slug>/<slug>.pdf`, `.bib`, `.ris`, `kapak.webp`
- `/yayinlar.json` diğer sitelerin okuduğu liste (CORS açık)
- `/yayinlar.bib` tüm kayıtlar, `/sitemap.xml`, `/robots.txt`

Tasarım & yazılım: [vumatech.net](https://vumatech.net)
