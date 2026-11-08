import streamlit as st
import os

# Import the functions from your member files
from mem1 import extract_basic_features
from mem2 import extract_reproducibility_signals
from mem3 import calculate_reproducibility_score

st.title("Paper Readability Evaluator")
st.write("Based on research by Edward Raff (NeurIPS 2019)")

uploaded_file = st.file_uploader("Upload a Research Paper PDF", type="pdf")

if uploaded_file is not None:
    # Save uploaded file temporarily
    temp_filename = "temp.pdf"
    with open(temp_filename, "wb") as f:
        f.write(uploaded_file.read())
        
    try:
        # Step 1: Extract basic features using mem1
        basic_feats = extract_basic_features(temp_filename)
        
        # Step 2: Extract signals using mem2
        signals = extract_reproducibility_signals(basic_feats["full_text"])
        
        # Step 3: Calculate score using mem3
        score, breakdown = calculate_reproducibility_score(basic_feats, signals)
        
        # Display Results
        st.subheader("Results")
        st.metric(label="Reproducibility Index Score", value=f"{score} / 100")
        
        st.subheader("Extracted Metrics")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Pages", basic_feats["pages"])
        col2.metric("Tables Count", basic_feats["tables_count"])
        col3.metric("Eq/Page Density", f"{basic_feats['eq_per_page']:.2f}")
        
        st.subheader("Analysis Breakdown")
        for item in breakdown:
            st.write(item)

    except Exception as e:
        st.error(f"Error processing PDF: {e}")
        
    finally:
        # Clean up temporary file
        if os.path.exists(temp_filename):
            os.remove(temp_filename)