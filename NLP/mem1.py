import pymupdf  # Updated import to avoid deprecation warning
import re

def extract_basic_features(pdf_path):
    doc = pymupdf.open(pdf_path)
    total_pages = len(doc)
    
    full_text = ""
    for page in doc:
        full_text += page.get_text()
        
    # Count inline/block equations via regex or math delimiters
    equations = re.findall(r'(\$\$.*?\$\$|\$.*?\$|\\begin\{equation\}[\s\S]*?\\end\{equation\})', full_text)
    num_equations = len(equations)
    
    # Estimate tables and figures based on captions
    tables_count = len(re.findall(r'(?i)table\s+\d+', full_text))
    figures_count = len(re.findall(r'(?i)figure\s+\d+', full_text))
    
    return {
        "pages": total_pages,
        "num_equations": num_equations,
        "eq_per_page": num_equations / max(total_pages, 1),
        "tables_count": tables_count,
        "figures_count": figures_count,
        "full_text": full_text
    }

# This block executes when you run `python mem1.py` directly in terminal
if __name__ == "__main__":
    test_pdf = r"E:\NLP\sample.pdf"
    
    try:
        results = extract_basic_features(test_pdf)
        print("\n--- Mem1 Extraction Successful ---")
        print(f"Total Pages: {results['pages']}")
        print(f"Equations Count: {results['num_equations']}")
        print(f"Equations per Page: {results['eq_per_page']:.2f}")
        print(f"Tables Count: {results['tables_count']}")
        print(f"Figures Count: {results['figures_count']}")
        print("----------------------------------\n")
    except Exception as e:
        print(f"Error executing mem1: {e}")