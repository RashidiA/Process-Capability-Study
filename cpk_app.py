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
from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet

# --- PAGE CONFIG ---
st.set_page_config(page_title="Process Capability, Cpk Analyzer", layout="wide")

st.title("🛡️ Process Capability Study with Data Logging")

# --- SIDEBAR INPUTS ---
with st.sidebar:
    st.header("📋 Study Parameters")
    title = st.text_input("Project Title", "Tailgate to Side Body Gap")
    u_spec = st.number_input("Upper Spec Limit (USL)", value=2.8)
    l_spec = st.number_input("Lower Spec Limit (LSL)", value=2.2)
    
    st.subheader("📊 Measurement Data")
    # Default data provided from user reference
    default_data = "2.8\n2.8\n2.6\n2.8\n2.5\n2.6\n2.6\n2.8\n2.6\n2.7\n2.7\n2.6\n2.8\n2.6\n2.7\n2.7\n2.6"
    data_input = st.text_area("Data Points (One per line)", height=300, value=default_data)

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
        ax1.axhline(mean, color='green', linestyle='-', alpha=0.5)
        ax1.set_title("Individuals Control Chart")
        
        fig2, ax2 = plt.subplots(figsize=(6, 3.5))
        ax2.hist(data, bins=10, density=True, alpha=0.6, color='skyblue', edgecolor='white')
        x = np.linspace(min(data)-0.2, max(data)+0.2, 100)
        ax2.plot(x, stats.norm.pdf(x, mean, std_dev), color='magenta', lw=2)
        ax2.axvline(u_spec, color='red', label='USL')
        ax2.axvline(l_spec, color='red', label='LSL')
        ax2.set_title("Capability Histogram")

        st.columns(2)[0].pyplot(fig1)
        st.columns(2)[1].pyplot(fig2)

        # --- PDF GENERATION WITH DATA LOG ---
        def create_pdf(f1, f2, measurements):
            buf = BytesIO()
            p = canvas.Canvas(buf, pagesize=A4)
            w, h = A4

            # Page 1: Summary and Graphs
            p.setFont("Helvetica-Bold", 16)
            p.drawString(50, h - 50, "PROCESS CAPABILITY & PPM REPORT")
            p.setFont("Helvetica", 11)
            p.drawString(50, h - 80, f"Project: {title}")
            p.drawString(50, h - 95, f"Specs: LSL {l_spec} | USL {u_spec}  | Mean: {mean:.3f}")
            p.drawString(50, h - 110, f"Cpk: {cpk:.2f} | Estimated Yield: {yield_perc:.2f}%")

            def fig_to_img(fig):
                img_buf = BytesIO()
                fig.savefig(img_buf, format='png', bbox_inches='tight', dpi=150)
                img_buf.seek(0)
                return ImageReader(img_buf)

            p.drawImage(fig_to_img(f1), 50, h - 320, width=500, height=200)
            p.drawImage(fig_to_img(f2), 50, h - 540, width=500, height=200)

            # PPM Table
            p.setFont("Helvetica-Bold", 12)
            p.drawString(50, h - 570, "Quality Performance (PPM Analysis)")
            ppm_data = [
                ["Metric", "Percentage", "PPM"],
                ["Above USL", f"{prob_above_usl*100:.4f}%", f"{int(prob_above_usl*1_000_000):,}"],
                ["Below LSL", f"{prob_below_lsl*100:.4f}%", f"{int(prob_below_lsl*1_000_000):,}"],
                ["Total Defect", f"{total_defect_prob*100:.4f}%", f"{int(ppm_total):,}"]
            ]
            ppm_tbl = Table(ppm_data, colWidths=[150, 150, 150])
            ppm_tbl.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.cadetblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            ppm_tbl.wrapOn(p, 50, h - 680)
            ppm_tbl.drawOn(p, 50, h - 680)

            # Page 2: Full Data Log
            p.showPage()
            p.setFont("Helvetica-Bold", 14)
            p.drawString(50, h - 50, "FULL DATA MEASUREMENT LOG")
            
            # Prepare data in grid format (5 columns)
            log_data = [["Point #", "Value", "Point #", "Value", "Point #", "Value"]]
            for i in range(0, len(measurements), 3):
                row = []
                for j in range(3):
                    if i + j < len(measurements):
                        row.extend([f"#{i+j+1}", f"{measurements[i+j]:.3f}"])
                    else:
                        row.extend(["", ""])
                log_data.append(row)

            log_tbl = Table(log_data, colWidths=[60, 90, 60, 90, 60, 90])
            log_tbl.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
            ]))
            log_tbl.wrapOn(p, 50, h - 750)
            log_tbl.drawOn(p, 50, 100) # Start from bottom up

            p.save()
            return buf.getvalue()

        st.divider()
        pdf_data = create_pdf(fig1, fig2, data)
        st.download_button("📥 Download Comprehensive Report", pdf_data, "Cpk_Full_Audit_Report.pdf", "application/pdf")

    except Exception as e:
        st.error(f"Computation Error: {e}")
