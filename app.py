import os
from PyPDF2 import PdfReader, PdfWriter
import streamlit as st
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# Function to create a single page with "RFP RESPONSE" text
def create_rfp_response_page():
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    can.setFont("Helvetica-Bold", 40)
    can.drawCentredString(300, 500, "RFP RESPONSE")
    can.showPage()
    can.save()
    packet.seek(0)
    return PdfReader(packet)

# Function to merge RFP and Response PDFs with the new page
def merge_pdfs(rfp_path, response_path, output_path):
    writer = PdfWriter()

    # Add RFP document pages
    with open(rfp_path, 'rb') as rfp_file:
        rfp_reader = PdfReader(rfp_file)
        for page in rfp_reader.pages:
            writer.add_page(page)

    # Add the custom "RFP RESPONSE" page
    response_page_reader = create_rfp_response_page()
    writer.add_page(response_page_reader.pages[0])

    # Add Response document pages
    with open(response_path, 'rb') as response_file:
        response_reader = PdfReader(response_file)
        for page in response_reader.pages:
            writer.add_page(page)

    # Save the final merged PDF
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'wb') as output_pdf:
        writer.write(output_pdf)

# Streamlit Web App
def main():
    st.title("RFP and Response Merger")

    # Upload RFP file
    rfp_file = st.file_uploader("Upload RFP Document", type=["pdf"])
    
    # Upload Response file
    response_file = st.file_uploader("Upload RFP Response Document", type=["pdf"])

    if rfp_file and response_file:
        # Save uploaded files to temporary locations
        rfp_path = "temp_rfp.pdf"
        response_path = "temp_response.pdf"

        with open(rfp_path, "wb") as f:
            f.write(rfp_file.read())
        with open(response_path, "wb") as f:
            f.write(response_file.read())
        
        # Merge PDFs and provide download option
        if st.button("Merge and Download"):
            output_path = os.path.join("merged_folder", f"{os.path.splitext(rfp_file.name)[0]}_merged.pdf")
            merge_pdfs(rfp_path, response_path, output_path)
            
            # Provide download link
            with open(output_path, 'rb') as f:
                st.download_button("Download Merged PDF", f, file_name=f"{rfp_file.name}_merged.pdf")

if __name__ == "__main__":
    main()
