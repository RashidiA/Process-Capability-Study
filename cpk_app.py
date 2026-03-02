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
st.set_page_config(page_title="Process Capability, Cpk & PPM Analyzer", layout="wide")

st.title("🛡️ Process Capability Study")

# --- SIDEBAR: DATA ENTRY ---
with st.sidebar:
    st.header("📋 Study Parameters")
    title = st.text_input("Project Title", "Tailgate to Side Body Gap")
    u_spec = st.number_input("Upper Spec Limit (USL)", value=2.8)
    l_spec = st.number_input("Lower Spec Limit (LSL)", value=2.2)
    
    st.divider()
    st.subheader("📊 Step 1: Key-in Actual Data")
    st.caption("Enter one value per line. Max 60 points.")
    
    # Input area
    data_input = st.text_area("Measurement Input", height=250, placeholder="2.8\n2.7\n2.6...")

    # Logic to create a numbered tracking list
    raw_lines = [x.strip() for x in data_input.split('\n') if x.strip()]
    num_points = len(raw_lines)
    
    if num_points > 0:
        st.success(f"Tracked: **{num_points} / 60** points")
        # Visual numbered tracker for user
        track_df = pd.DataFrame({
            "Point #": [f"Data Point {i+1}" for i in range(num_points)],
            "Actual": raw_lines
        })
        st.dataframe(track_df, height=200, hide_index=True)
    else:
        st.info("Start typing measurements to see the point tracker.")

# --- MAIN ANALYSIS ---
if num_points >= 2:
    try:
        data = [float(x) for x in raw_lines][:60]
        mean = np.mean(data)
        std_dev = np.std(data, ddof=1)
        
        # Cpk Calculations
        cpu = (u_spec - mean) / (3 * std_dev)
        cpl = (mean - l_spec) / (3 * std_dev)
        cpk = min(cpu, cpl)
        
        # PPM and Yield Calculation
        p_above = 1 - stats.norm.cdf(u_spec, mean, std_dev)
        p_below = stats.norm.cdf(l_spec, mean, std_dev)
        total_p = p_above + p_below
        yield_perc = (1 - total_p) * 100
        ppm_total = total_p * 1_000_000

        # Dashboard Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Mean", f"{mean:.3f}")
        m2.metric("Cpk", f"{cpk:.2f}")
        m3.metric("Yield", f"{yield_perc:.2f}%")
        m4.metric("Total PPM", f"{int(ppm_total):,}")

        # Plotting
        fig1, ax1 = plt.subplots(figsize=(6, 3))
        ax1.plot(data, marker='o', color='#004b87', linewidth=1)
        ax1.axhline(u_spec, color='red', linestyle='--', label='USL')
        ax1.axhline(l_spec, color='red', linestyle='--', label='LSL')
        ax1.set_title("Individuals Chart")
        
        fig2, ax2 = plt.subplots(figsize=(6, 3))
        ax2.hist(data, bins=10, density=True, alpha=0.5, color='skyblue')
        x_range = np.linspace(min(data)-0.2, max(data)+0.2, 100)
        ax2.plot(x_range, stats.norm.pdf(x_range, mean, std_dev), color='magenta')
        ax2.axvline(u_spec, color='red')
        ax2.axvline(l_spec, color='red')
        ax2.set_title("Capability Histogram")

        st.columns(2)[0].pyplot(fig1)
        st.columns(2)[1].pyplot(fig2)

        # PDF Report with PPM Analysis & Numbered Log
        def generate_report():
            buf = BytesIO()
            p = canvas.Canvas(buf, pagesize=A4)
            w, h = A4

            p.setFont("Helvetica-Bold", 16)
            p.drawString(50, h-50, "PROCESS CAPABILITY AUDIT REPORT")
            p.setFont("Helvetica", 10)
            p.drawString(50, h-70, f"Project: {title} | Specs: {l_spec} - {u_spec} | Cpk: {cpk:.2f}")

            # Embed Charts
            def add_plot(fig, y_pos):
                img_data = BytesIO()
                fig.savefig(img_data, format='png', bbox_inches='tight')
                p.drawImage(ImageReader(img_data), 50, y_pos, width=450, height=180)

            add_plot(fig1, h-280)
            add_plot(fig2, h-480)

            # PPM Table
            p.setFont("Helvetica-Bold", 12)
            p.drawString(50, h-510, "Quality Performance (PPM Analysis)")
            ppm_table_data = [
                ["Metric", "Percentage", "PPM (Defects per Million)"],
                ["Above USL", f"{p_above*100:.4f}%", f"{int(p_above*1_000_000):,}"],
                ["Below LSL", f"{p_below*100:.4f}%", f"{int(p_below*1_000_000):,}"],
                ["Total Defect", f"{total_p*100:.4f}%", f"{int(ppm_total):,}"]
            ]
            t_ppm = Table(ppm_table_data, colWidths=[150, 150, 150])
            t_ppm.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.cadetblue),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('ALIGN', (0,0), (-1,-1), 'CENTER')
            ]))
            t_ppm.wrapOn(p, 50, h-600)
            t_ppm.drawOn(p, 50, h-600)

            # Numbered Data Log
            p.setFont("Helvetica-Bold", 12)
            p.drawString(50, h-640, "Measurement Data Log")
            log_data = [["#", "Value", "#", "Value", "#", "Value", "#", "Value"]]
            for i in range(0, num_points, 4):
                row = []
                for j in range(4):
                    idx = i + j
                    row.extend([f"#{idx+1}", f"{data[idx]:.3f}"] if idx < num_points else ["", ""])
                log_data.append(row)

            t_log = Table(log_data, colWidths=[30, 80]*4)
            t_log.setStyle(TableStyle([
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('FONTSIZE', (0,0), (-1,-1), 8),
                ('ALIGN', (0,0), (-1,-1), 'CENTER')
            ]))
            t_log.wrapOn(p, 50, 50)
            t_log.drawOn(p, 50, 100) # Draw near bottom

            p.showPage()
            p.save()
            return buf.getvalue()

        st.divider()
        st.download_button("📥 Download PDF Audit Report", generate_report(), "Audit_Report.pdf")

    except Exception as e:
        st.error(f"Computation error. Please ensure all inputs are numeric. Details: {e}")
