import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Page Title
st.title('MTT Assay IC50 Calculator')

st.markdown('''
### Instructions:
1. Upload a **TSV file** with MTT absorbance data (triplicates recommended), or use the provided example data.
2. Specify the column indices for controls and treatments.
3. Set your drug name and concentration unit.
4. Click **Update Plot** to calculate % viability, generate the IC50 plot with error bars, and estimate IC50.
''')

# Load example data (cached for performance)
@st.cache_data
def load_example_data():
    return pd.read_csv('MTT_data.tsv', sep='\t')

# File uploader or example data toggle
use_example = st.checkbox("Use Example Data (MTT_data.tsv)")

if use_example:
    df = load_example_data()
    st.success("✅ Loaded example data.")
else:
    uploaded_file = st.file_uploader("Upload MTT Absorbance Data (TSV)", type="tsv")
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file, sep='\t')

# Ensure data is available before proceeding
if 'df' not in locals():
    st.warning("⚠️ Please upload a file or select 'Use Example Data' to proceed.")
    st.stop()

# Data preview
st.write("### Data Preview")
st.write(df)

# Option to download the loaded data
st.download_button(
    label="Download Input Data as TSV",
    data=df.to_csv(sep='\t', index=False),
    file_name="MTT_data_downloaded.tsv",
    mime="text/tab-separated-values"
)

# Step 2: Experimental Parameters
st.write("### Step 2: Define Experimental Conditions")

neg_control_col = st.number_input("Column Index for Negative Control (-cells, -Drug, +MTT)", min_value=0, max_value=len(df.columns)-1, value=0)
no_drug_no_mtt_col = st.number_input("Column Index for Cells (+cells, -Drug, -MTT)", min_value=0, max_value=len(df.columns)-1, value=1)
no_drug_with_mtt_col = st.number_input("Column Index for Cells (+cells, -Drug, +MTT)", min_value=0, max_value=len(df.columns)-1, value=2)

concentrations = st.text_input("Enter Drug Concentrations (comma-separated)", "1, 2, 4, 8, 16")
concentrations = np.array([float(x.strip()) for x in concentrations.split(',')])

treatment_cols = st.text_input("Column Indices for Drug Treatments (comma-separated)", "3, 4, 5, 6, 7")
treatment_cols = np.array([int(x.strip()) for x in treatment_cols.split(',')])

# New Feature 1: Input for custom dataset/drug name
drug_name = st.text_input("Enter Name of Drug or Data Set (appears in plot title)", "Example Drug")

# New Feature 2: Input for custom concentration unit
concentration_unit = st.text_input("Enter Unit of Concentration", "mg/ml")

# Validation
if len(concentrations) != len(treatment_cols):
    st.error(f"❌ Number of drug concentrations ({len(concentrations)}) does not match the number of treatment columns ({len(treatment_cols)}). Please fix this before proceeding.")
    st.stop()

# Process data and generate plot if user clicks "Update Plot"
if st.button("Generate Plot"):
    absorbance_data = df.to_numpy()

    # Background correction (subtract negative control average)
    background_corrected = absorbance_data - np.mean(absorbance_data[:, neg_control_col])

    # Calculate % Viability for each concentration (triplicate average)
    no_drug_with_mtt_mean = np.mean(background_corrected[:, no_drug_with_mtt_col])

    viability = np.mean(background_corrected[:, treatment_cols], axis=0) / no_drug_with_mtt_mean * 100
    viability_std = np.std(background_corrected[:, treatment_cols], axis=0) / no_drug_with_mtt_mean * 100

    # IC50 Estimation via linear interpolation
    try:
        ic50_concentration = np.interp(50, viability[::-1], concentrations[::-1])
    except ValueError:
        st.error("⚠️ Error calculating IC50 — please check your data.")
        st.stop()

    # Plot generation with custom title and axis label
    fig, ax = plt.subplots()
    ax.errorbar(
        concentrations, viability, yerr=viability_std, fmt='o-', color='navy', capsize=5, label='% Viability ± SD'
    )
    ax.axhline(50, color='red', linestyle='--', label='IC50 Line')
    ax.axvline(ic50_concentration, color='red', linestyle='--')
    ax.text(ic50_concentration + 0.3, 30, f'IC50 ≈ {ic50_concentration:.2f} {concentration_unit}', color='red')

    ax.set_xlabel(f'Concentration ({concentration_unit})')
    ax.set_ylabel('% Viability')
    ax.set_title(f'MTT Assay - IC50 Determination for {drug_name}')
    ax.legend()
    ax.grid(True)

    st.pyplot(fig)

    # Display IC50 result
    st.success(f"✅ Estimated IC50 for **{drug_name}**: **{ic50_concentration:.2f} {concentration_unit}**")
