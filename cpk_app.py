import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as stats
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle

# --- PAGE CONFIG ---
st.set_page_config(page_title="Process capability Cpk Analyzer", layout="wide")

st.title("🛡️ Process Capability Study with PPM Analysis")

# --- SIDEBAR INPUTS ---
with st.sidebar:
    st.header("📋 Study Parameters")
    title = st.text_input("Project Title", "Tailgate to Side Body Gap")
    u_spec = st.number_input("Upper Spec Limit (USL)", value=2.8)
    l_spec = st.number_input("Lower Spec Limit (LSL)", value=2.2)
    
    st.subheader("📊 Measurement Data")
    data_input = st.text_area("Data Points (One per line)", height=300, 
                             value="2.8\n2.8\n2.6\n2.8\n2.5\n2.6\n2.7\n2.6\n2.6\n2.7\n2.7\n2.6\n2.8\n2.6\n2.7\n2.7\n2.6")

# --- CALCULATIONS ---
if data_input:
    try:
        data = [float(x) for x in data_input.split('\n') if x.strip()][:60]
        df = pd.DataFrame(data, columns=['Value'])
        
        # Core Statistics
        mean = np.mean(data)
        std_dev = np.std(data, ddof=1)
        
        # Capability Indices
        cpu = (u_spec - mean) / (3 * std_dev)
        cpl = (mean - l_spec) / (3 * std_dev)
        cpk = min(cpu, cpl)
        
        # Yield and PPM Calculation
        prob_above_usl = 1 - stats.norm.cdf(u_spec, mean, std_dev)
        prob_below_lsl = stats.norm.cdf(l_spec, mean, std_dev)
        total_defect_prob = prob_above_usl + prob_below_lsl
        
        yield_perc = (1 - total_defect_prob) * 100
        ppm_total = total_defect_prob * 1_000_000

        # --- DASHBOARD UI ---
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Mean", f"{mean:.3f}")
        m2.metric("Cpk", f"{cpk:.2f}")
        m3.metric("Yield", f"{yield_perc:.2f}%")
        m4.metric("Total PPM", f"{int(ppm_total):,}")

        # --- PLOTTING ---
        fig1, ax1 = plt.subplots(figsize=(6, 3.5))
        ax1.plot(data, marker='o', color='#004b87', markersize=4)
        ax1.axhline(u_spec, color='red', linestyle='--', label='USL')
        ax1.axhline(l_spec, color='red', linestyle='--', label='LSL')
        ax1.set_title("Individuals Control Chart")
        
        fig2, ax2 = plt.subplots(figsize=(6, 3.5))
        ax2.hist(data, bins=10, density=True, alpha=0.6, color='skyblue', edgecolor='white')
        x = np.linspace(min(data)-0.1, max(data)+0.1, 100)
        ax2.plot(x, stats.norm.pdf(x, mean, std_dev), color='magenta', lw=2)
        ax2.axvline(u_spec, color='red', label='USL')
        ax2.axvline(l_spec, color='red', label='LSL')
        ax2.set_title("Capability Histogram")

        st.columns(2)[0].pyplot(fig1)
        st.columns(2)[1].pyplot(fig2)

        # --- PDF GENERATION WITH PPM TABLE ---
        def create_pdf(f1, f2):
            buf = BytesIO()
            p = canvas.Canvas(buf, pagesize=A4)
            w, h = A4

            # Header & Summary
            p.setFont("Helvetica-Bold", 16)
            p.drawString(50, h - 50, "PROCESS CAPABILITY & PPM REPORT")
            p.setFont("Helvetica", 11)
            p.drawString(50, h - 80, f"Project: {title}")
            p.drawString(50, h - 95, f"Specs: LSL {l_spec} | USL {u_spec}  | Mean: {mean:.3f}")
            p.drawString(50, h - 110, f"Cpk: {cpk:.2f} | Estimated Yield: {yield_perc:.2f}%")

            # Helper to convert Plot to Image
            def fig_to_img(fig):
                img_buf = BytesIO()
                fig.savefig(img_buf, format='png', bbox_inches='tight', dpi=150)
                img_buf.seek(0)
                return ImageReader(img_buf)

            # Insert Graphs
            p.drawImage(fig_to_img(f1), 50, h - 320, width=500, height=200)
            p.drawImage(fig_to_img(f2), 50, h - 540, width=500, height=200)

            # PPM Table
            p.setFont("Helvetica-Bold", 12)
            p.drawString(50, h - 570, "Quality Performance (PPM Analysis)")
            
            table_data = [
                ["Metric", "Percentage", "PPM (Defects per Million)"],
                ["Above USL", f"{prob_above_usl*100:.4f}%", f"{int(prob_above_usl*1_000_000):,}"],
                ["Below LSL", f"{prob_below_lsl*100:.4f}%", f"{int(prob_below_lsl*1_000_000):,}"],
                ["Total Defect", f"{total_defect_prob*100:.4f}%", f"{int(ppm_total):,}"]
            ]
            
            tbl = Table(table_data, colWidths=[150, 150, 200])
            tbl.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.cadetblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            
            tbl.wrapOn(p, 50, h - 680)
            tbl.drawOn(p, 50, h - 680)

            p.showPage()
            p.save()
            return buf.getvalue()

        st.divider()
        if st.download_button("📥 Download PDF Report", create_pdf(fig1, fig2), "Cpk_PPM_Report.pdf", "application/pdf"):
            st.success("Report generated successfully!")

    except Exception as e:
        st.error(f"Computation Error: {e}")
