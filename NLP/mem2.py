import re

def extract_reproducibility_signals(text):
    # Hyperparameter checks
    hp_keywords = ['learning rate', 'batch size', 'epochs', 'optimizer', 'hyperparameter', 'weight decay', 'learning_rate']
    hp_found = [kw for kw in hp_keywords if re.search(r'\b' + kw + r'\b', text, re.I)]
    
    # Compute resources check
    compute_keywords = ['gpu', 'nvidia', 'cpu', 'tpu', 'v100', 'a100', 'rtx', 'ram', 'cluster', 'cores']
    compute_found = [kw for kw in compute_keywords if re.search(r'\b' + kw + r'\b', text, re.I)]
    
    # URL / Code / Dataset link check
    urls = re.findall(r'https?://[^\s>]+', text)
    code_links = [url for url in urls if 'github.com' in url or 'gitlab.com' in url]
    
    return {
        "has_hyperparameters": len(hp_found) >= 2,
        "hp_found_list": hp_found,
        "has_compute_specs": len(compute_found) > 0,
        "compute_found_list": compute_found,
        "code_links": code_links,
        "has_code_link": len(code_links) > 0
    }