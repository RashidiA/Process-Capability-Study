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
st.set_page_config(page_title="Process Capability, Cpk Analyzer", layout="wide")

st.title("🛡️ Process Capability Study")

# --- SIDEBAR: DATA ENTRY ---
with st.sidebar:
    st.header("📋 Study Parameters")
    title = st.text_input("Project Title", "Tailgate to Side Body X70 Gap")
    u_spec = st.number_input("Upper Spec Limit (USL)", value=2.8)
    l_spec = st.number_input("Lower Spec Limit (LSL)", value=2.2)
    
    st.divider()
    st.subheader("📊 Step 1: Key-in Data")
    st.caption("Enter one value per line. The list below will track your Point #.")
    
    # The Text Area for Input
    data_input = st.text_area("Actual Data Input", height=250, 
                             placeholder="Example:\n2.8\n2.7\n2.6...",
                             help="Type your measurements here. Max 60 points.")

    # Number Tracker Logic
    raw_points = [x.strip() for x in data_input.split('\n') if x.strip()]
    num_points = len(raw_points)
    
    # Live Counter
    if num_points > 0:
        st.info(f"✅ Currently tracked: **{num_points} / 60** data points.")
        # Show a small preview table to help user track
        tracker_df = pd.DataFrame({
            "Point #": [f"#{i+1}" for i in range(num_points)],
            "Value": raw_points
        })
        st.dataframe(tracker_df.tail(5), hide_index=True, use_container_width=True)
    else:
        st.warning("Waiting for data...")

# --- CALCULATIONS & REPORTING ---
if num_points >= 2:
    try:
        data = [float(x) for x in raw_points][:60]
        mean = np.mean(data)
        std_dev = np.std(data, ddof=1)
        cpk = min((u_spec - mean)/(3*std_dev), (mean - l_spec)/(3*std_dev))
        
        # PPM and Yield
        p_above = 1 - stats.norm.cdf(u_spec, mean, std_dev)
        p_below = stats.norm.cdf(l_spec, mean, std_dev)
        yield_perc = (1 - (p_above + p_below)) * 100
        ppm = (p_above + p_below) * 1_000_000

        # UI Dashboard
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Mean", f"{mean:.3f}")
        c2.metric("Cpk", f"{cpk:.2f}")
        c3.metric("Yield", f"{yield_perc:.2f}%")
        c4.metric("Total PPM", f"{int(ppm):,}")

        # Graphs
        fig1, ax1 = plt.subplots(figsize=(6, 3))
        ax1.plot(data, marker='o', color='#004b87', markersize=4)
        ax1.axhline(u_spec, color='red', linestyle='--', label='USL')
        ax1.axhline(l_spec, color='red', linestyle='--', label='LSL')
        ax1.set_title("Individuals Control Chart")
        
        fig2, ax2 = plt.subplots(figsize=(6, 3))
        ax2.hist(data, bins=10, density=True, alpha=0.6, color='skyblue')
        x_axis = np.linspace(min(data)-0.1, max(data)+0.1, 100)
        ax2.plot(x_axis, stats.norm.pdf(x_axis, mean, std_dev), color='magenta')
        ax2.set_title("Capability Histogram")

        st.columns(2)[0].pyplot(fig1)
        st.columns(2)[1].pyplot(fig2)

        # PDF Logic
        def create_pdf():
            buf = BytesIO()
            p = canvas.Canvas(buf, pagesize=A4)
            h = A4[1]
            
            p.setFont("Helvetica-Bold", 14)
            p.drawString(50, h-50, "CPK AUDIT REPORT WITH MEASUREMENT LOG")
            p.setFont("Helvetica", 10)
            p.drawString(50, h-70, f"Project: {title} | Total Points: {num_points}")
            
            # Helper to draw matplotlib to PDF
            def add_chart(fig, y_pos):
                img_buf = BytesIO()
                fig.savefig(img_buf, format='png', bbox_inches='tight')
                p.drawImage(ImageReader(img_buf), 50, y_pos, width=450, height=200)

            add_chart(fig1, h-300)
            add_chart(fig2, h-520)

            # Data Table with Numbers for Report
            p.drawString(50, h-550, "Point Log:")
            log_data = [["#", "Value", "#", "Value", "#", "Value", "#", "Value"]]
            # Split into 4 columns for compact look
            for i in range(0, num_points, 4):
                row = []
                for j in range(4):
                    idx = i + j
                    row.extend([f"#{idx+1}", f"{data[idx]:.3f}"] if idx < num_points else ["", ""])
                log_data.append(row)

            t = Table(log_data, colWidths=[30, 60]*4)
            t.setStyle(TableStyle([
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('FONTSIZE', (0,0), (-1,-1), 8),
                ('BACKGROUND', (0,0), (-1,0), colors.lightgrey)
            ]))
            t.wrapOn(p, 50, 50)
            t.drawOn(p, 50, 50)
            
            p.showPage()
            p.save()
            return buf.getvalue()

        st.download_button("📥 Download PDF Report", create_pdf(), "Full_Report.pdf")

    except ValueError:
        st.error("Please enter numbers only (one per line).")

