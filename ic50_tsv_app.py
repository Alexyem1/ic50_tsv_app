import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Page Title
st.title('MTT Assay IC50 Calculator')

st.markdown('''
### Instructions:
1. Upload a **TSV file** with MTT absorbance data (triplicates recommended), or use the provided example data.
2. Specify the corresponding concentrations and controls.
3. Click "Update Plot" to generate the IC50 plot with error bars and estimate the IC50.
''')

# Load example data (cache to avoid reloading)
@st.cache_data
def load_example_data():
    return pd.read_csv('MTT_data.tsv', sep='\t')

# File uploader or example data toggle
use_example = st.checkbox("Use Example Data (MTT_data.tsv)")

if use_example:
    df = load_example_data()
    st.success("Loaded example data.")
else:
    uploaded_file = st.file_uploader("Upload MTT Absorbance Data (TSV)", type="tsv")
    if uploaded_file:
        df = pd.read_csv(uploaded_file, sep='\t')

# Check if data is available
if 'df' not in locals():
    st.warning("Please upload a file or select 'Use Example Data' to proceed.")
    st.stop()

# Show the data preview
st.write("### Preview of Data")
st.write(df)

# Option to download the loaded data
st.download_button(
    label="Download Input Data as TSV",
    data=df.to_csv(sep='\t', index=False),
    file_name="MTT_data_downloaded.tsv",
    mime="text/tab-separated-values"
)

# Experimental parameters input section
st.write("### Step 2: Define Experimental Conditions")

neg_control_col = st.number_input("Column Index for Negative Control (-cells, -Drug, +MTT)", min_value=0, max_value=len(df.columns)-1, value=0)
no_Drug_no_mtt_col = st.number_input("Column Index for Cells (+cells, -Drug, -MTT)", min_value=0, max_value=len(df.columns)-1, value=1)
no_Drug_with_mtt_col = st.number_input("Column Index for Cells (+cells, -Drug, +MTT)", min_value=0, max_value=len(df.columns)-1, value=2)

concentrations = st.text_input("Enter Drug Concentrations (comma-separated, mg/ml)", "1, 2, 4, 8, 16")
concentrations = np.array([float(x.strip()) for x in concentrations.split(',')])

treatment_cols = st.text_input("Column Indices for Drug Treatments (comma-separated)", "3, 4, 5, 6, 7")
treatment_cols = np.array([int(x.strip()) for x in treatment_cols.split(',')])

# Check if they match in length
if len(concentrations) != len(treatment_cols):
    st.error(f"⚠️ Number of drug concentrations ({len(concentrations)}) does not match the number of treatment columns ({len(treatment_cols)}). Please correct this before proceeding.")
    st.stop()

# Process and plot data when "Update Plot" is clicked
if st.button("Update Plot"):
    # Convert DataFrame to numpy array for easy calculations
    absorbance_data = df.to_numpy()

    # Background correction: subtract negative control average from all values
    background_corrected = absorbance_data - np.mean(absorbance_data[:, neg_control_col])

    # Calculate % Viability for each concentration (triplicate average)
    no_Drug_with_mtt_mean = np.mean(background_corrected[:, no_Drug_with_mtt_col])

    viability = np.mean(background_corrected[:, treatment_cols], axis=0) / no_Drug_with_mtt_mean * 100
    viability_std = np.std(background_corrected[:, treatment_cols], axis=0) / no_Drug_with_mtt_mean * 100

    # IC50 Estimation via linear interpolation
    ic50_concentration = np.interp(50, viability[::-1], concentrations[::-1])

    # Generate plot with error bars
    fig, ax = plt.subplots()
    ax.errorbar(concentrations, viability, yerr=viability_std, fmt='o-', color='navy', capsize=5, label='% Viability ± SD')
    ax.axhline(50, color='red', linestyle='--', label='IC50 Line')
    ax.axvline(ic50_concentration, color='red', linestyle='--')
    ax.text(ic50_concentration + 0.3, 30, f'IC50 ≈ {ic50_concentration:.2f} mg/ml', color='red')
    ax.set_xlabel('Drug Concentration (mg/ml)')
    ax.set_ylabel('% Viability')
    ax.set_title('MTT Assay - IC50 Determination for Drug')
    ax.legend()
    ax.grid(True)

    st.pyplot(fig)

    st.write(f"### Estimated IC50: {ic50_concentration:.2f} mg/ml")

