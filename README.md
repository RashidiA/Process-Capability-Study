🛡️ Process Capability, Cpk Analyzer

A statistical tool modeled to measure process capability and estimate production yield.
Key Features
  •	Numbered Data Entry: A sidebar tracker providing live "Point #" feedback (up to 60 points) to help users stay organized during manual key-in.
  •	Statistical Metrics: Calculates Mean, Standard Deviation (ϭ), Cp, and Cpk.
  •	PPM Analysis: Provides a detailed breakdown of "Defects per Million" (PPM) occurring above the USL and below the LSL.
  •	Automated Audit Reports: Generates a professional PDF containing:
      o	Project summary and spec limits.
      o	Individuals Control Chart and Capability Histogram.
      o	A full Measurement Data Log for audit transparency.
________________________________________
🛠️ Installation & Setup

1. Requirements
Ensure you have Python 3.8+ installed. Create a requirements.txt file with the following:
Plaintext
streamlit
easyocr
numpy
pandas
matplotlib
scipy
reportlab
Pillow

2. Local Deployment
Bash
# Clone the repository
git clone https://github.com/your-repo-link

# Install dependencies
pip install -r requirements.txt

# Run the Export QC App
streamlit run export_qc.py

# Run the Cpk Analyzer
streamlit run cpk_analyzer.py

3. System Dependencies (Streamlit Cloud)
If deploying to a cloud environment, create a packages.txt file to support the OCR engine:
Plaintext
libzbar0
________________________________________
📈 Quality Standards
The Cpk Analyzer follows standard automotive quality benchmarks:
   •	Cpk < 1.00: Process is not capable.
   •	1.00 ≤ Cpk < 1.33: Process is marginally capable.
   •	Cpk ≥ 1.33: Process is capable (Standard requirement).

