#!/usr/bin/env python3
"""yayin.mahmutvural.net static site generator.

Reads data/yayinlar.json (publication records) and pdf/ (one PDF per record id),
writes the public site to site/.  Run:  python3 build.py
"""
import html, json, re, shutil, unicodedata
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent
SITE = ROOT / "site"
BASE = "https://yayin.mahmutvural.net"
AUTHOR = "Vural, Mahmut"
ORCID = "0000-0001-8946-2540"
CONTACT = "mahmut.vural@manas.edu.kg"
PROFILES = [
    ("ORCID", f"https://orcid.org/{ORCID}"),
    ("Google Akademik", "https://scholar.google.com/citations?user=N8wHxEIAAAAJ"),
    ("Academia.edu", "https://manas.academia.edu/mahmutvural"),
    ("DergiPark", "https://dergipark.org.tr/tr/pub/@drmahmutvural"),
    ("CV", "https://cv.mahmutvural.net"),
]
TODAY = date.today().isoformat()
import hashlib
ASSET_V = hashlib.sha1(b"".join((ROOT / "assets" / f).read_bytes() for f in ("site.css", "site.js"))).hexdigest()[:8]

TR2 = str.maketrans({"ı": "i", "İ": "i", "ş": "s", "Ş": "s", "ğ": "g", "Ğ": "g",
                     "ü": "u", "Ü": "u", "ö": "o", "Ö": "o", "ç": "c", "Ç": "c", "â": "a"})
CYR = dict(zip("абвгдеёжзийклмнопрстуфхцчшщъыьэюяңөүқғұәіһ",
               ["a","b","v","g","d","e","e","zh","z","i","i","k","l","m","n","o","p","r","s","t","u","f","kh","ts","ch","sh","sch","","y","","e","yu","ya","n","o","u","k","g","u","a","i","h"]))


def slugify(s, maxwords=7):
    s = re.sub(r"['’]", "", s).translate(TR2).lower()
    s = "".join(CYR.get(c, c) for c in s)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    words = re.findall(r"[a-z0-9]+", s)
    stop = {"ve", "ile", "bir", "the", "of", "and", "in", "a", "an", "for", "on", "as", "olarak",
            "kak", "v", "i", "uzerine", "uzerinde", "to", "with", "its", "from", "da", "de"}
    words = [w for w in words if w not in stop]
    return "-".join(words[:maxwords])


def esc(s):
    return html.escape(str(s or ""), quote=True)


def split_authors(s):
    out = []
    for a in (s or "").split(";"):
        a = a.strip()
        if not a:
            continue
        if "," in a:
            last, first = [x.strip() for x in a.split(",", 1)]
        else:
            last, first = a, ""
        out.append((last, first))
    return out


def initials(first):
    parts = re.split(r"[\s]+", first.strip())
    out = []
    for p in parts:
        if not p:
            continue
        if re.fullmatch(r"(?:[A-ZÇĞİÖŞÜА-Я]\.)+", p):
            out.append(p)
        else:
            sub = p.split("-")
            out.append("-".join(x[0] + "." for x in sub if x))
    return " ".join(out)


def apa_authors(auth):
    names = [f"{l}, {initials(f)}".strip().rstrip(",") for l, f in auth]
    if len(names) == 1:
        return names[0]
    if len(names) <= 20:
        return ", ".join(names[:-1]) + ", & " + names[-1]
    return ", ".join(names[:19]) + ", ... " + names[-1]


def short_authors(auth):
    """Display list: Given Surname, with the owner bolded."""
    out = []
    for l, f in auth:
        full = f"{f} {l}".strip()
        if l == "Vural" and f.startswith("Mahmut"):
            out.append(f"<b>{esc(full)}</b>")
        else:
            out.append(esc(full))
    return ", ".join(out)


TYPE = {
    "JOUR": ("Makale", "Journal article"),
    "CONF_FULL": ("Bildiri, tam metin", "Conference paper"),
    "CONF_ABS": ("Bildiri özeti", "Conference abstract"),
    "CHAP": ("Kitap bölümü", "Book chapter"),
    "THES_PHD": ("Doktora tezi", "Doctoral thesis"),
    "THES_MA": ("Yüksek lisans tezi", "Master's thesis"),
    "THES_BA": ("Lisans bitirme çalışması", "Undergraduate thesis"),
}
GROUPS = [  # filter tabs
    ("makale", ("Makaleler", "Articles"), {"JOUR"}),
    ("bildiri", ("Bildiriler", "Conference papers"), {"CONF_FULL", "CONF_ABS"}),
    ("bolum", ("Kitap bölümleri", "Book chapters"), {"CHAP"}),
    ("tez", ("Tezler", "Theses"), {"THES_PHD", "THES_MA", "THES_BA"}),
]
LANG = {"tr": ("Türkçe", "Turkish"), "en": ("İngilizce", "English"), "ru": ("Rusça", "Russian")}
THESIS_KIND = {"0ae8imi4k": "THES_PHD", "ykaq61tdq": "THES_MA", "y7gmz0rwr": "THES_BA"}
TITLE_FIX = {"bmscrh4ba": ("Entreprises", "Enterprises")}


def kind_of(r):
    t = r["tipKod"]
    if t == "THES":
        return THESIS_KIND.get(r["_id"], "THES_MA")
    if t == "CONF":
        return "CONF_ABS" if "Özet" in r["tur"] else "CONF_FULL"
    return t


def pages(r):
    a, b = (r.get("ilkSayfa") or "").strip(), (r.get("sonSayfa") or "").strip()
    if a and b and a != b:
        return f"{a}–{b}"
    return a or ""


def venue(r):
    return (r.get("dergi") or "").strip()


def apa(r, auth, k):
    y = r["yil"]
    t = r["baslik"].rstrip(".")
    v = venue(r)
    pg = pages(r)
    pub = (r.get("yayinevi") or "").strip()
    doi = (r.get("doi") or "").strip()
    head = f"{apa_authors(auth)} ({y}). "
    if k == "JOUR":
        vol = r.get("cilt") or ""
        iss = r.get("sayi") or ""
        s = head + f"{t}. <i>{esc(v)}</i>"
        if vol:
            s += f", <i>{esc(vol)}</i>"
            if iss:
                s += f"({esc(iss)})"
        elif iss:
            s += f", ({esc(iss)})"
        if pg:
            s += f", {pg}"
        s += "."
    elif k == "CHAP":
        s = head + f"{t}. In <i>{esc(v)}</i>" + (f" (pp. {pg})" if pg else "") + "."
        if pub:
            s += f" {esc(pub)}."
    elif k.startswith("THES"):
        lab = {"THES_PHD": "Doktora tezi", "THES_MA": "Yüksek lisans tezi", "THES_BA": "Lisans bitirme çalışması"}[k]
        s = head + f"<i>{esc(t)}</i> [{lab}]. {esc(pub)}."
    else:
        s = head + f"{t}. In <i>{esc(v)}</i>" + (f" (pp. {pg})" if pg else "") + "."
        if pub:
            s += f" {esc(pub)}."
    if doi:
        s += f" https://doi.org/{esc(doi)}"
    return s


def bibtex(r, auth, k, key, url, pdf):
    typ = {"JOUR": "article", "CHAP": "incollection", "THES_PHD": "phdthesis",
           "THES_MA": "mastersthesis", "THES_BA": "misc"}.get(k, "inproceedings")
    f = {"title": r["baslik"], "author": " and ".join(f"{l}, {fi}" for l, fi in auth), "year": r["yil"]}
    v = venue(r)
    if typ == "article":
        f["journal"] = v
    elif typ in ("incollection", "inproceedings"):
        f["booktitle"] = v
    if typ in ("phdthesis", "mastersthesis", "misc") and k.startswith("THES"):
        f["school"] = r.get("yayinevi", "")
    elif r.get("yayinevi"):
        f["publisher"] = r["yayinevi"]
    for a, b in (("cilt", "volume"), ("sayi", "number")):
        if r.get(a):
            f[b] = r[a]
    if pages(r):
        f["pages"] = pages(r).replace("–", "--")
    if r.get("doi"):
        f["doi"] = r["doi"]
    f["url"] = url
    lang = {"tr": "turkish", "en": "english", "ru": "russian"}.get(r.get("dil"))
    if lang:
        f["language"] = lang
    body = ",\n".join(f"  {k2} = {{{v2}}}" for k2, v2 in f.items() if v2)
    return f"@{typ}{{{key},\n{body}\n}}\n"


def ris(r, auth, k, url, pdf):
    ty = {"JOUR": "JOUR", "CHAP": "CHAP", "THES_PHD": "THES", "THES_MA": "THES", "THES_BA": "THES"}.get(k, "CPAPER")
    L = [f"TY  - {ty}"] + [f"AU  - {l}, {fi}" for l, fi in auth]
    L += [f"TI  - {r['baslik']}", f"PY  - {r['yil']}"]
    v = venue(r)
    if v:
        L.append(("JO" if ty == "JOUR" else "T2") + f"  - {v}")
    for a, b in (("cilt", "VL"), ("sayi", "IS"), ("ilkSayfa", "SP"), ("sonSayfa", "EP"), ("yayinevi", "PB"), ("doi", "DO")):
        if r.get(a):
            L.append(f"{b}  - {r[a]}")
    if r.get("ozet"):
        L.append(f"AB  - {r['ozet']}")
    for kw in [x.strip() for x in (r.get("anahtar") or "").split(";") if x.strip()]:
        L.append(f"KW  - {kw}")
    L.append(f"UR  - {url}")
    if pdf:
        L.append(f"L1  - {pdf}")
    L.append(f"LA  - {r.get('dil','')}")
    L.append("ER  - ")
    return "\r\n".join(L) + "\r\n"


def meta_tags(r, auth, k, url, pdf):
    m = [("citation_title", r["baslik"])]
    m += [("citation_author", f"{l}, {fi}".strip(", ")) for l, fi in auth]
    d = (r.get("tarih") or r["yil"]).replace("-", "/")
    m.append(("citation_publication_date", d))
    v = venue(r)
    if k == "JOUR":
        m.append(("citation_journal_title", v))
        if r.get("issn"):
            m.append(("citation_issn", r["issn"]))
    elif k == "CHAP":
        m.append(("citation_inbook_title", v))
    elif k.startswith("THES"):
        m.append(("citation_dissertation_institution", r.get("yayinevi", "")))
    else:
        m.append(("citation_conference_title", v))
    for a, b in (("cilt", "citation_volume"), ("sayi", "citation_issue"),
                 ("ilkSayfa", "citation_firstpage"), ("sonSayfa", "citation_lastpage"),
                 ("doi", "citation_doi")):
        if r.get(a):
            m.append((b, r[a]))
    if r.get("yayinevi") and not k.startswith("THES"):
        m.append(("citation_publisher", r["yayinevi"]))
    if r.get("dil"):
        m.append(("citation_language", r["dil"]))
    kws = [x.strip() for x in (r.get("anahtar") or "").split(";") if x.strip()]
    if kws:
        m.append(("citation_keywords", "; ".join(kws)))
    m.append(("citation_abstract_html_url", url))
    if pdf:
        m.append(("citation_pdf_url", pdf))
    m += [("DC.title", r["baslik"])] + [("DC.creator", f"{l}, {fi}") for l, fi in auth]
    m += [("DC.issued", r.get("tarih") or r["yil"]), ("DC.language", r.get("dil", ""))]
    return "\n".join(f'<meta name="{a}" content="{esc(b)}">' for a, b in m if b)


FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Spectral:ital,wght@0,400;0,500;0,600;1,400&'
         'family=Manrope:wght@400;500;600;700&display=swap" rel="stylesheet">')


def page(title, desc, canonical, body, head_extra="", lang="tr", og_image=None):
    og = f'<meta property="og:image" content="{esc(og_image)}">' if og_image else ""
    return f"""<!doctype html>
<html lang="{lang}" data-ui="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{esc(canonical)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{esc(canonical)}">
<meta property="og:type" content="website">
{og}
<meta name="theme-color" content="#1F4E73">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
{FONTS}
<link rel="stylesheet" href="/assets/site.css?v={ASSET_V}">
{head_extra}
</head>
<body>
<a class="skip" href="#main"><span data-tr>İçeriğe geç</span><span data-en>Skip to content</span></a>
{body}
<script src="/assets/site.js?v={ASSET_V}" defer></script>
</body>
</html>
"""


def bi(tr, en):
    return f'<span data-tr>{esc(tr)}</span><span data-en>{esc(en)}</span>'


def topbar(home=False):
    left = ('<a class="brand" href="/">Mahmut Vural <span>'
            + bi("Yayın arşivi", "Publication archive") + "</span></a>")
    return f"""<header class="top"><div class="wrap top-in">{left}
<button class="lang" type="button" aria-label="Dil / Language"><span data-tr>EN</span><span data-en>TR</span></button>
</div></header>"""


def footer():
    links = "".join(f'<a href="{esc(u)}" rel="me noopener">{esc(n)}</a>' for n, u in PROFILES)
    return f"""<footer class="foot"><div class="wrap">
<p class="foot-name">Dr. Mahmut Vural</p>
<p>{bi("Kırgızistan-Türkiye Manas Üniversitesi, Meslek Yüksekokulu, Bişkek", "Kyrgyz-Turkish Manas University, Vocational School, Bishkek")}</p>
<nav class="foot-links">{links}</nav>
<p class="fine">{bi("Dosyalar yazarın paylaşılabilir sürümleridir. Atıf için yayımlanmış künyeyi kullanın.", "Files are the author's shareable versions. Please cite the published record.")}
<a href="/yayinlar.json">JSON</a>, <a href="/yayinlar.bib">BibTeX</a></p>
</div></footer>"""


def main():
    recs = json.load(open(ROOT / "data/yayinlar.json", encoding="utf-8"))
    if SITE.exists():
        shutil.rmtree(SITE)
    (SITE / "assets").mkdir(parents=True)
    for f in (ROOT / "assets").iterdir():
        shutil.copy(f, SITE / "assets" / f.name)
    shutil.copy(ROOT / "assets/favicon.svg", SITE / "favicon.svg")

    items = []
    SUFFIX = {"JOUR": "makale", "CONF_FULL": "bildiri", "CONF_ABS": "ozet", "CHAP": "bolum"}
    def base_slug(r):
        a = split_authors(r["yazarlar"])
        t = r["baslik"]
        if r["_id"] in TITLE_FIX:
            t = t.replace(*TITLE_FIX[r["_id"]])
        return f"{r['yil']}-{slugify(a[0][0] if a else 'vural', 1)}-{slugify(t)}"
    from collections import Counter
    dup = Counter(base_slug(r) for r in recs)
    for r in recs:
        r = dict(r)
        if r["_id"] in TITLE_FIX:
            a, b = TITLE_FIX[r["_id"]]
            r["baslik"] = r["baslik"].replace(a, b)
        auth = split_authors(r["yazarlar"])
        k = kind_of(r)
        slug = base_slug(r)
        if dup[slug] > 1:
            slug += "-" + SUFFIX.get(k, "tez")
        has_pdf = (ROOT / "pdf" / f"{r['_id']}.pdf").exists() and k != "CHAP"
        url = f"{BASE}/{slug}/"
        pdf = f"{BASE}/{slug}/{slug}.pdf" if has_pdf else ""
        cover = (ROOT / "covers" / f"{r['_id']}.webp").exists()
        items.append(dict(r=r, auth=auth, k=k, slug=slug, url=url, pdf=pdf, cover=cover))

    items.sort(key=lambda x: (x["r"].get("tarih") or x["r"]["yil"]), reverse=True)

    # ---------- item pages ----------
    feed = []
    allbib = []
    for it in items:
        r, auth, k, slug = it["r"], it["auth"], it["k"], it["slug"]
        d = SITE / slug
        d.mkdir(parents=True)
        if it["pdf"]:
            shutil.copy(ROOT / "pdf" / f"{r['_id']}.pdf", d / f"{slug}.pdf")
        if it["cover"]:
            shutil.copy(ROOT / "covers" / f"{r['_id']}.webp", d / "kapak.webp")
        key = f"{slugify(auth[0][0],1)}{r['yil']}{slugify(r['baslik'],1)}"
        bib = bibtex(r, auth, k, key, it["url"], it["pdf"])
        allbib.append(bib)
        (d / f"{slug}.bib").write_text(bib, encoding="utf-8")
        (d / f"{slug}.ris").write_text(ris(r, auth, k, it["url"], it["pdf"]), encoding="utf-8")
        cite = apa(r, auth, k)
        tr, en = TYPE[k]
        lang_tr, lang_en = LANG.get(r.get("dil"), ("", ""))
        kws = [x.strip() for x in (r.get("anahtar") or "").split(";") if x.strip()]
        facts = []
        v = venue(r)
        if v:
            lab = {"JOUR": ("Dergi", "Journal"), "CHAP": ("Kitap", "Book")}.get(k, ("Etkinlik", "Event"))
            if k.startswith("THES"):
                lab = ("Kurum", "Institution")
            facts.append((lab, esc(v)))
        if k.startswith("THES") and r.get("yayinevi"):
            facts.append((("Kurum", "Institution"), esc(r["yayinevi"])))
        if r.get("cilt") or r.get("sayi"):
            facts.append((("Cilt, sayı", "Volume, issue"), esc(", ".join(x for x in (r.get("cilt"), r.get("sayi")) if x))))
        if pages(r):
            facts.append((("Sayfalar", "Pages"), pages(r)))
        if r.get("yayinevi") and not k.startswith("THES"):
            facts.append((("Yayıncı", "Publisher"), esc(r["yayinevi"])))
        place = r.get("etkinlikYeri") or r.get("yer")
        if place and k.startswith("CONF"):
            facts.append((("Yer", "Venue"), esc(place)))
        if r.get("tarih"):
            facts.append((("Tarih", "Date"), esc(r["tarih"])))
        if r.get("doi"):
            facts.append((("DOI", "DOI"), f'<a href="https://doi.org/{esc(r["doi"])}">{esc(r["doi"])}</a>'))
        if r.get("issn"):
            facts.append((("ISSN", "ISSN"), esc(r["issn"])))
        facts.append((("Dil", "Language"), bi(lang_tr, lang_en)))
        facts_html = "".join(f"<div><dt>{bi(*a)}</dt><dd>{b}</dd></div>" for a, b in facts)

        if it["pdf"]:
            sz = (ROOT / "pdf" / f"{r['_id']}.pdf").stat().st_size
            main_btn = (f'<a class="btn primary" href="{slug}.pdf">{bi("Tam metni indir", "Download full text")}'
                        f' <small>PDF, {sz/1048576:.1f} MB</small></a>')
        else:
            sub = f"Tam metin talebi: {r['baslik']}"
            main_btn = (f'<a class="btn primary" href="mailto:{CONTACT}?subject={esc(sub)}">'
                        f'{bi("Tam metni yazardan iste", "Request full text")}</a>'
                        f'<p class="note">{bi("Bu bölümün telif hakkı yayınevindedir. Kişisel kullanım için kopya e-postayla gönderilir.", "The publisher holds the copyright of this chapter. A copy for personal use is sent by email.")}</p>')
        cover_html = (f'<img class="cover-lg" src="kapak.webp" alt="" width="420" height="594">' if it["cover"]
                      else f'<div class="cover-lg cover-type" aria-hidden="true"><span>{esc(r["yil"])}</span><p>{esc(r["baslik"])}</p></div>')
        abstract = f'<section class="abs"><h2>{bi("Özet", "Abstract")}</h2><p lang="{esc(r.get("dil",""))}">{esc(r.get("ozet",""))}</p></section>' if r.get("ozet") else ""
        kw_html = ('<ul class="kws">' + "".join(f"<li>{esc(x)}</li>" for x in kws) + "</ul>") if kws else ""
        jsonld = {
            "@context": "https://schema.org",
            "@type": {"JOUR": "ScholarlyArticle", "CHAP": "Chapter"}.get(k, "Thesis" if k.startswith("THES") else "ScholarlyArticle"),
            "headline": r["baslik"][:110], "name": r["baslik"],
            "author": [{"@type": "Person", "name": f"{fi} {l}".strip()} for l, fi in auth],
            "datePublished": r.get("tarih") or r["yil"], "inLanguage": r.get("dil"),
            "isPartOf": venue(r) or None, "publisher": r.get("yayinevi") or None,
            "abstract": r.get("ozet") or None, "keywords": kws or None, "url": it["url"],
        }
        if r.get("doi"):
            jsonld["sameAs"] = f"https://doi.org/{r['doi']}"
        if it["pdf"]:
            jsonld["encoding"] = {"@type": "MediaObject", "contentUrl": it["pdf"], "encodingFormat": "application/pdf"}
        jsonld = {a: b for a, b in jsonld.items() if b}
        head = meta_tags(r, auth, k, it["url"], it["pdf"]) + \
            f'\n<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>'
        body = f"""{topbar()}
<main id="main" class="wrap item">
<nav class="crumb"><a href="/">{bi("Tüm yayınlar", "All publications")}</a></nav>
<div class="item-grid">
<article class="item-main">
<p class="kind"><span class="k k-{k[:4].lower()}">{bi(tr, en)}</span> {esc(r['yil'])}</p>
<h1 lang="{esc(r.get('dil',''))}">{esc(r['baslik'])}</h1>
<p class="authors">{short_authors(auth)}</p>
<div class="m-dl">{main_btn}</div>
{abstract}
{kw_html}
<section class="cite"><h2>{bi("Atıf", "Cite")}</h2>
<p class="apa" id="apa">{cite}</p>
<div class="cite-actions">
<button type="button" class="btn ghost" data-copy="apa">{bi("APA künyesini kopyala", "Copy APA citation")}</button>
<a class="btn ghost" href="{slug}.bib" download>BibTeX</a>
<a class="btn ghost" href="{slug}.ris" download>RIS</a>
</div></section>
</article>
<aside class="item-side">
{cover_html}
{main_btn}
<dl class="facts">{facts_html}</dl>
</aside>
</div>
</main>
{footer()}"""
        desc = (r.get("ozet") or r["baslik"])[:200]
        og = f"{BASE}/{slug}/kapak.webp" if it["cover"] else None
        (d / "index.html").write_text(page(f"{r['baslik']} | Mahmut Vural", desc, it["url"], body, head,
                                           lang=r.get("dil", "tr"), og_image=og), encoding="utf-8")
        feed.append({
            "id": r["_id"], "slug": slug, "url": it["url"], "pdf": it["pdf"] or None,
            "kapak": f"{BASE}/{slug}/kapak.webp" if it["cover"] else None,
            "tur": k, "turAdi": tr, "typeLabel": en, "yil": r["yil"], "tarih": r.get("tarih"),
            "baslik": r["baslik"], "yazarlar": [f"{fi} {l}".strip() for l, fi in auth],
            "yayinYeri": venue(r) or None, "yayinevi": r.get("yayinevi") or None,
            "cilt": r.get("cilt") or None, "sayi": r.get("sayi") or None, "sayfalar": pages(r) or None,
            "doi": r.get("doi") or None, "dil": r.get("dil"), "ozet": r.get("ozet") or None,
            "anahtar": kws or None, "apa": re.sub(r"</?i>", "", cite).replace("&amp;", "&"),
            "bibtex": f"{it['url']}{slug}.bib",
        })

    # ---------- home ----------
    counts = {g: sum(1 for it in items if it["k"] in s) for g, _, s in GROUPS}
    tabs = f'<button type="button" class="tab" aria-pressed="true" data-f="all">{bi("Tümü", "All")} <i>{len(items)}</i></button>'
    tabs += "".join(f'<button type="button" class="tab" aria-pressed="false" data-f="{g}">{bi(*lab)} <i>{counts[g]}</i></button>'
                    for g, lab, _ in GROUPS)
    shelf = [it for it in items if it["cover"]][:14]
    shelf_html = "".join(
        f'<a class="spine" href="/{it["slug"]}/" style="--i:{n}" title="{esc(it["r"]["baslik"])}">'
        f'<img src="/{it["slug"]}/kapak.webp" alt="{esc(it["r"]["baslik"])}" width="210" height="297" loading="{"eager" if n < 6 else "lazy"}"></a>'
        for n, it in enumerate(shelf))
    rows = []
    year = None
    for it in items:
        r = it["r"]
        if r["yil"] != year:
            if year is not None:
                rows.append("</ol></section>")
            year = r["yil"]
            rows.append(f'<section class="year" data-year="{year}"><h2 class="yr">{year}</h2><ol class="list">')
        grp = next(g for g, _, s in GROUPS if it["k"] in s)
        tr, en = TYPE[it["k"]]
        thumb = (f'<img src="/{it["slug"]}/kapak.webp" alt="" width="72" height="102" loading="lazy">' if it["cover"]
                 else f'<span class="thumb-type" aria-hidden="true">{esc(r["yil"])}</span>')
        hay = " ".join([r["baslik"], r["yazarlar"], venue(r), r.get("anahtar") or ""]).lower()
        badge = (f'<a class="pdf" href="{it["pdf"]}">PDF</a>' if it["pdf"] else "")
        doi = f'<a class="doi" href="https://doi.org/{esc(r["doi"])}">DOI</a>' if r.get("doi") else ""
        rows.append(f"""<li class="pub" data-g="{grp}" data-q="{esc(hay)}">
<a class="thumb" href="/{it['slug']}/" tabindex="-1" aria-hidden="true">{thumb}</a>
<div class="pub-body">
<p class="kind"><span class="k k-{it['k'][:4].lower()}">{bi(tr, en)}</span></p>
<h3 lang="{esc(r.get('dil',''))}"><a href="/{it['slug']}/">{esc(r['baslik'])}</a></h3>
<p class="authors">{short_authors(it['auth'])}</p>
<p class="venue">{esc(venue(r))}{(", " + pages(it['r'])) if pages(it['r']) else ""}</p>
<p class="links">{badge}{doi}</p>
</div></li>""")
    rows.append("</ol></section>")
    langs = sorted({it["r"].get("dil") for it in items})
    lang_line = ", ".join(LANG[l][0] for l in langs if l in LANG)
    home = f"""{topbar(True)}
<main id="main">
<section class="hero"><div class="wrap hero-in">
<div class="hero-text">
<h1>Mahmut Vural</h1>
<p class="lede">{bi("Türk dünyasında turizm, dijital girişimcilik ve siber güvenlik üzerine makaleler, bildiriler, kitap bölümleri ve tezler. Bişkek'ten, " + str(min(int(i['r']['yil']) for i in items)) + "'ten bugüne.", "Articles, conference papers, book chapters and theses on tourism in the Turkic world, digital entrepreneurship and cybersecurity. From Bishkek, " + str(min(int(i['r']['yil']) for i in items)) + " to today.")}</p>
<p class="aff">{bi("Dr. Öğr. Üyesi, Kırgızistan-Türkiye Manas Üniversitesi", "Assistant Professor, Kyrgyz-Turkish Manas University")}<br>
<a href="https://orcid.org/{ORCID}" rel="me">ORCID {ORCID}</a></p>
</div>
<div class="shelf" aria-label="{esc('Son yayınların kapakları')}">{shelf_html}</div>
</div></section>
<section class="wrap browse">
<div class="tools">
<div class="tabs" role="group" aria-label="Tür">{tabs}</div>
<label class="search"><span class="sr">{bi("Ara", "Search")}</span>
<input type="search" id="q" placeholder="Başlık, yazar ya da anahtar kelime" data-ph-en="Title, author or keyword" autocomplete="off"></label>
</div>
<p class="count" id="count" aria-live="polite"></p>
<div id="pubs">{''.join(rows)}</div>
<p class="empty" id="empty" hidden>{bi("Bu aramaya uyan yayın yok. Başka bir kelime deneyin ya da filtreyi Tümü yapın.", "No publication matches this search. Try another word or switch the filter to All.")}</p>
<p class="meta-note">{bi("Diller: ", "Languages: ")}{esc(lang_line)}. {bi("Son güncelleme: ", "Last updated: ")}{TODAY}</p>
</section>
</main>
{footer()}"""
    personld = {"@context": "https://schema.org", "@type": "Person", "name": "Mahmut Vural",
                "affiliation": {"@type": "CollegeOrUniversity", "name": "Kyrgyz-Turkish Manas University"},
                "sameAs": [u for _, u in PROFILES], "identifier": f"https://orcid.org/{ORCID}"}
    shelf_og = f"{BASE}/{shelf[0]['slug']}/kapak.webp" if shelf else None
    (SITE / "index.html").write_text(page(
        "Mahmut Vural | Yayın arşivi",
        "Mahmut Vural'ın tüm makaleleri, bildirileri, kitap bölümleri ve tezleri: künye, özet ve tam metin PDF.",
        f"{BASE}/", home, f'<script type="application/ld+json">{json.dumps(personld, ensure_ascii=False)}</script>',
        og_image=shelf_og), encoding="utf-8")

    # ---------- feeds, sitemap, misc ----------
    (SITE / "yayinlar.json").write_text(json.dumps({"guncelleme": TODAY, "kaynak": BASE, "yayinlar": feed},
                                                   ensure_ascii=False, indent=1), encoding="utf-8")
    (SITE / "yayinlar.bib").write_text("\n".join(allbib), encoding="utf-8")
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
          f"<url><loc>{BASE}/</loc><lastmod>{TODAY}</lastmod></url>"]
    sm += [f"<url><loc>{it['url']}</loc><lastmod>{TODAY}</lastmod></url>" for it in items]
    sm.append("</urlset>")
    (SITE / "sitemap.xml").write_text("\n".join(sm), encoding="utf-8")
    (SITE / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n")
    (SITE / "_headers").write_text(
        "/*.pdf\n  Content-Type: application/pdf\n  Content-Disposition: inline\n  Cache-Control: public, max-age=86400\n"
        "/*.webp\n  Cache-Control: public, max-age=604800\n"
        "/assets/*\n  Cache-Control: public, max-age=3600\n"
        "/yayinlar.json\n  Access-Control-Allow-Origin: *\n  Cache-Control: public, max-age=600\n"
        "/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n")
    nf = f"""{topbar()}<main id="main" class="wrap notfound"><h1>{bi("Bu adreste bir sayfa yok", "There is no page at this address")}</h1>
<p>{bi("Adres değişmiş olabilir. Tüm yayınlar ana sayfada listelenir.", "The address may have changed. All publications are listed on the home page.")}</p>
<p><a class="btn primary" href="/">{bi("Tüm yayınlara dön", "Back to all publications")}</a></p></main>{footer()}"""
    (SITE / "404.html").write_text(page("Sayfa bulunamadı | Mahmut Vural", "", f"{BASE}/", nf), encoding="utf-8")
    print(f"{len(items)} yayın, {sum(1 for i in items if i['pdf'])} PDF")


if __name__ == "__main__":
    main()
