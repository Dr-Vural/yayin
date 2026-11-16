#!/usr/bin/env python3
"""pdf/<id>.pdf dosyalarının ilk sayfasından covers/<id>.webp üretir (yalnızca eksik olanlar)."""
from pathlib import Path
import pypdfium2 as pdfium

ROOT = Path(__file__).resolve().parent.parent
for pdf in sorted((ROOT / "pdf").glob("*.pdf")):
    out = ROOT / "covers" / f"{pdf.stem}.webp"
    if out.exists():
        continue
    page = pdfium.PdfDocument(str(pdf))[0]
    w, _ = page.get_size()
    page.render(scale=420 / w).to_pil().convert("RGB").save(out, "WEBP", quality=82)
    print("kapak:", out.name)
