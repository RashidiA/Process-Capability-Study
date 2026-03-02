import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as stats
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

# --- PAGE CONFIG ---
st.set_page_config(page_title="Body Shop Cpk Analyzer", layout="wide")

@st.cache_resource
def load_reader():
    # Placeholder for consistency with your previous industrial app
    pass

# --- STYLING ---
st.markdown("""
    <style>
    .metric-container { background-color: #f0f2f6; padding: 15px; border-radius: 10px; border-left: 5px solid #004b87; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ Process Capability Study (Body Shop)")

# --- SIDEBAR INPUTS ---
with st.sidebar:
    st.header("📋 Study Parameters")
    title = st.text_input("Project/Part Title", "Tailgate to Side Body Gap")
    u_spec = st.number_input("Upper Spec Limit (USL)", value=2.8, step=0.1)
    l_spec = st.number_input("Lower Spec Limit (LSL)", value=2.2, step=0.1)
    
    st.subheader("📊 Measurement Data")
    st.caption("Enter up to 60 actual measurements (one per line):")
    data_input = st.text_area("Data Points", height=300, value="2.8\n2.8\n2.6\n2.8\n2.5\n2.6\n2.7\n2.6\n2.6\n2.7\n2.7\n2.6\n2.8\n2.6\n2.7\n2.7\n2.6")

# --- CALCULATIONS ---
if data_input:
    try:
        # Parse Data
        data = [float(x) for x in data_input.split('\n') if x.strip()]
        data = data[:60]
        df = pd.DataFrame(data, columns=['Value'])
        
        # Statistics
        n = len(data)
        mean = np.mean(data)
        std_dev = np.std(data, ddof=1)
        
        # Capability Indices
        cp = (u_spec - l_spec) / (6 * std_dev)
        cpu = (u_spec - mean) / (3 * std_dev)
        cpl = (mean - l_spec) / (3 * std_dev)
        cpk = min(cpu, cpl)
        
        # Yield (Z-score approach)
        z_u = (u_spec - mean) / std_dev
        z_l = (mean - l_spec) / std_dev
        yield_perc = (stats.norm.cdf(z_u) - (1 - stats.norm.cdf(z_l))) * 100

        # --- DASHBOARD ---
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Mean (X-bar)", f"{mean:.3f}")
        col2.metric("Std Dev (σ)", f"{std_dev:.4f}")
        col3.metric("Cpk", f"{cpk:.2f}")
        col4.metric("Est. Yield", f"{yield_perc:.2f}%")

        # --- CHARTS ---
        c_left, c_right = st.columns(2)
        
        with c_left:
            st.subheader("Individuals Chart (Run Chart)")
            fig1, ax1 = plt.subplots(figsize=(8, 5))
            ax1.plot(data, marker='o', linestyle='-', color='#004b87', label='Data')
            ax1.axhline(u_spec, color='red', linestyle='--', label='USL')
            ax1.axhline(l_spec, color='red', linestyle='--', label='LSL')
            ax1.axhline(mean, color='green', label='Mean')
            ax1.set_title("Process Stability")
            ax1.legend()
            st.pyplot(fig1)
            

        with c_right:
            st.subheader("Process Capability Histogram")
            fig2, ax2 = plt.subplots(figsize=(8, 5))
            count, bins, ignored = ax2.hist(data, bins=10, density=True, alpha=0.6, color='skyblue')
            # Normal distribution curve
            x = np.linspace(l_spec - 0.2, u_spec + 0.2, 100)
            ax2.plot(x, stats.norm.pdf(x, mean, std_dev), color='magenta', lw=2)
            ax2.axvline(u_spec, color='red', lw=2, label='USL')
            ax2.axvline(l_spec, color='red', lw=2, label='LSL')
            ax2.set_title("Distribution vs Specs")
            st.pyplot(fig2)
            

        # --- ANALYSIS & EXPORT ---
        st.divider()
        if cpk >= 1.33:
            st.success(f"✅ PROCESS CAPABLE: Cpk {cpk:.2f} meets the ≥1.33 requirement.")
        else:
            st.error(f"❌ PROCESS NOT CAPABLE: Cpk {cpk:.2f} is below the 1.33 threshold.")

        # PDF GENERATION
        def create_pdf():
            buf = BytesIO()
            p = canvas.Canvas(buf, pagesize=A4)
            p.drawString(100, 800, f"BODY SHOP PROCESS CAPABILITY REPORT")
            p.drawString(100, 780, f"Project: {title}")
            p.drawString(100, 760, f"USL: {u_spec} | LSL: {l_spec}")
            p.drawString(100, 740, f"Samples (n): {n}")
            p.drawString(100, 720, f"Cpk Results: {cpk:.2f}")
            p.drawString(100, 700, f"Estimated Yield: {yield_perc:.2f}%")
            p.showPage()
            p.save()
            return buf.getvalue()

        st.download_button("📥 Download PDF Report", create_pdf(), "Cpk_Report.pdf", "application/pdf")

    except Exception as e:
        st.error(f"Please check data format: {e}")