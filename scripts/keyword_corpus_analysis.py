from pathlib import Path
import re, zipfile, argparse, pandas as pd

TERMS = ['Coordinate', 'geolocation', 'isochrone', 'Lat', 'Long', 'Latitude', 'Longitude', 'pin', 'Point', 'Polygon', 'radius', 'Cocoa', 'Arabica', 'Coffee', 'Robusta', 'animals', 'Beef', 'Cattle', 'dairy', 'Feed', 'forages', 'grazing land', 'Livestock', 'pasture', 'agroforestry', 'Banana', 'barley', 'citrus', 'Commodities', 'Commodity', 'corn', 'Cotton', 'fiber', 'hemp', 'Maize', 'oats', 'rice', 'Sorghum', 'Sugar', 'Tea', 'Wheat', 'Palm', 'Rubber', 'Soy', 'Soya', 'paper', 'pulp', 'Timber', 'planted trees', 'eucalyptus', 'Wood', 'Concession', 'estate', 'Farm', 'field', 'harvested area', 'Land Unit', 'LMU', 'Management Unit', 'paddock', 'Parcel', 'Plantation', 'Plot', 'Production Unit', 'productive land', 'property', 'ranch', 'Adminstrative Area', 'District', 'Jurisdiction', 'municipality', 'province', 'region', 'region of origin', 'sourcing region', 'subdistrict', 'supply region', 'aggregation point', 'aggregator', 'Barge head', 'Bin', 'Buying Agent', 'Buying Station', 'catchment area', 'Coop', 'Cooperative', 'Facility', 'first point', 'Gin', 'ginner', 'Landscape', 'Logistics Hub', 'Market shed', 'Mill', 'Port', 'processing facility', 'processor', 'factory', 'Rail Head', 'rail terminal', 'refinery', 'road terminal', 'shed', 'Silo', 'Site', 'Slaughterhouse', 'Sourcing Area', 'Supplier', 'Supply shed', 'Supplyshed', 'terminal', 'Warehouse', 'Wholesaler', 'Farmer Association', 'Farmer Group', 'Farmer Organization', 'Producer Association', 'Producer Group', 'Producer Organization']

def build_regex(term):
    if " " in term:
        pat = r"\b" + r"\s+".join(re.escape(p) for p in term.split()) + r"\b"
    else:
        pat = r"\b" + re.escape(term) + r"\b"
    return re.compile(pat, flags=re.IGNORECASE)

TERM_REGEX = {t: build_regex(t) for t in TERMS}

def guess_title(md, first):
    title = str(md.get("/Title", "") or "").strip()
    if title and title.lower() not in {"untitled", "powerpoint presentation", "microsoft word - document"}:
        return title
    lines = [ln.strip() for ln in first.splitlines() if len(ln.strip()) > 12]
    return lines[0][:180] if lines else "Unknown"

def guess_year(md, first):
    for key in ["/CreationDate", "/ModDate"]:
        if md.get(key):
            m = re.search(r"(19|20)\d{2}", str(md[key]))
            if m:
                return int(m.group(0))
    years = [int(y) for y in re.findall(r"\b((?:19|20)\d{2})\b", first)]
    return max(years) if years else "Unknown"

def extract_pdf_text(pdf_path):
    try:
        import fitz
        doc = fitz.open(pdf_path)
        md = doc.metadata or {}
        first = doc.load_page(0).get_text("text") if doc.page_count else ""
        full = "\n".join((doc.load_page(i).get_text("text") or "") for i in range(doc.page_count))
        return full, first, {"/Title": md.get("title",""), "/CreationDate": md.get("creationDate",""), "/ModDate": md.get("modDate","")}
    except Exception:
        from PyPDF2 import PdfReader
        reader = PdfReader(str(pdf_path))
        md = reader.metadata or {}
        texts = []
        first = ""
        for i, page in enumerate(reader.pages):
            txt = page.extract_text() or ""
            if i == 0:
                first = txt
            texts.append(txt)
        return "\n".join(texts), first, md

def iter_pdfs(input_path):
    input_path = Path(input_path)
    if input_path.is_file() and input_path.suffix.lower() == ".pdf":
        yield input_path
    elif input_path.is_file() and input_path.suffix.lower() == ".zip":
        tmp = input_path.parent / (input_path.stem + "_extracted")
        tmp.mkdir(exist_ok=True)
        with zipfile.ZipFile(input_path, "r") as z:
            z.extractall(tmp)
        for p in sorted(tmp.rglob("*.pdf")):
            yield p
    elif input_path.is_dir():
        for p in sorted(input_path.rglob("*.pdf")):
            yield p
    else:
        raise ValueError(f"Unsupported input: {input_path}")

def run(input_path, batch_id, output_xlsx):
    rows = []
    for pdf in iter_pdfs(input_path):
        full, first, md = extract_pdf_text(pdf)
        title = guess_title(md, first)
        year = guess_year(md, first)
        for term, rgx in TERM_REGEX.items():
            rows.append({"Batch": batch_id, "Document Name": pdf.name, "Title": title, "Year": year, "Term": term, "Count": len(rgx.findall(full))})
    pd.DataFrame(rows).to_excel(output_xlsx, index=False, sheet_name="Long_AllTerms")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--batch", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run(args.input, args.batch, args.output)
