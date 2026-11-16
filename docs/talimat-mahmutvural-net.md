# mahmutvural.net: yayın arşivi entegrasyonu

**Amaç:** Ana sitedeki "Tüm Yayınlar" bölümünde her yayın yayin.mahmutvural.net'teki sayfasına ve tam metnine bağlansın; arşiv sitenin menüsünden ve dış bağlantılardan da erişilebilir olsun.

**Kapsam dışı:** Tema (obsidyen ve pirinç), dil yapısı (TR/EN/RU/KG), akordeonlar ve diğer bölümler değişmez.

## Kaynak

- Arşiv: `https://yayin.mahmutvural.net/`
- Liste: `https://yayin.mahmutvural.net/yayinlar.json` (alanlar için cv talimatındaki tabloya bakın: `id`, `url`, `pdf`, `kapak`, `baslik`, `yil`).
- Site statik ve derleme adımı yok. Bu yüzden bağlantılar `index.html` içine sabit olarak yazılır. Eşleştirme başlık ve yıla göre yapılır (sayfada panel kimliği yok).

## Yapılacaklar

1. **Yayın satırları:** `#publications` içindeki her `.pub-item` için:
   - `.pub-title` metni arşiv sayfasına bağlanır (`url`).
   - `.pub-index` satırına, varsa, "Tam metin (PDF)" bağlantısı eklenir (`pdf`). Mevcut harici PDF bağlantıları (örneğin kutayoktay.com) arşivdeki PDF ile değiştirilir; DOI ve ISBN bilgisi kalır.
   - Kitap bölümlerinde (`pdf` boş) yalnızca "Yayın sayfası" bağlantısı olur.
   - Etiketler `data-i18n` ile dört dilde: TR "Tam metin (PDF)" / "Yayın sayfası", EN "Full text (PDF)" / "Publication page", RU "Полный текст (PDF)" / "Страница публикации", KG "Толук текст (PDF)" / "Басылманын бети".
2. **Bölüm başlığı:** "35 yayın, 2004–2026" özet satırının altına "Tüm yayınlar, özetler ve tam metinler: yayin.mahmutvural.net" bağlantısı eklenir.
3. **Menü:** Gezinme çubuğunda "CV" bağlantısının yanına "Yayın arşivi" eklenir (`https://yayin.mahmutvural.net`, `data-i18n='nav_archive'`).
4. **Dış bağlantılar:** Academia.edu ve Google Scholar bağlantılarının yanına "Yayın arşivi" kartı eklenir.
5. **Yapılandırılmış veri:** Sayfadaki Person JSON-LD'nin `sameAs` listesine `https://yayin.mahmutvural.net/` eklenir.
6. **Önbellek:** CSS veya JS değişirse `styles.css?v=` ve `app.js?v=` sürüm parametreleri güncellenir (README'deki kural).
7. **Yapılan iş hatırlatması:** Yeni bir yayın eklendiğinde önce arşive (Dr-Vural/yayin) eklenir, sonra bu sayfadaki satıra bağlantı yazılır.

## Kabul ölçütleri

1. Yayınlar bölümündeki 35 satırın hepsi arşiv sayfasına, PDF'i olan 32'si ayrıca PDF'e bağlanır; hiçbir bağlantı 404 vermez.
2. Menü ve dış bağlantılarda "Yayın arşivi" dört dilde görünür.
3. Sayfa düzeni masaüstünde ve telefonda bozulmaz; mevcut animasyonlar ve dil değiştirme çalışır.
