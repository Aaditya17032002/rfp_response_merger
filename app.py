import os
import zipfile
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

# Function to merge multiple PDFs
def merge_multiple_pdfs(pdf_paths):
    writer = PdfWriter()
    for pdf_path in pdf_paths:
        try:
            with open(pdf_path, 'rb') as file:
                reader = PdfReader(file)
                for page in reader.pages:
                    writer.add_page(page)
        except Exception as e:
            st.error(f"Error reading PDF file: {pdf_path}. Error: {str(e)}")
    return writer

# Function to merge RFP with RFP response and custom page
def merge_pdfs_with_response(merged_rfp_writer, response_path, output_path):
    # Add the custom "RFP RESPONSE" page
    response_page_reader = create_rfp_response_page()
    merged_rfp_writer.add_page(response_page_reader.pages[0])

    # Add Response document pages
    with open(response_path, 'rb') as response_file:
        response_reader = PdfReader(response_file)
        for page in response_reader.pages:
            merged_rfp_writer.add_page(page)

    # Save the final merged PDF
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'wb') as output_pdf:
        merged_rfp_writer.write(output_pdf)

# Function to extract and return the file paths from a zip
def extract_zip(zip_file):
    extracted_files = []
    with zipfile.ZipFile(zip_file, 'r') as z:
        z.extractall('temp_zip_extracted')
        extracted_files = z.namelist()
    return extracted_files

# Streamlit Web App
def main():
    st.title("RFP and Response Merger - UCI Tool")

    # Initialize session state for merged RFP writer and custom file name
    if 'merged_rfp_writer' not in st.session_state:
        st.session_state.merged_rfp_writer = None

    if 'custom_file_name' not in st.session_state:
        st.session_state.custom_file_name = ""

    if 'zip_file_name' not in st.session_state:
        st.session_state.zip_file_name = None

    # Checkbox for multiple RFP documents merging
    multiple_rfp_checkbox = st.checkbox("I have multiple RFP documents to merge")

    # Checkbox for zip file upload
    zip_checkbox = st.checkbox("I want to upload a ZIP file")

    if multiple_rfp_checkbox:
        # Multiple RFP upload section
        rfp_files = st.file_uploader("Upload multiple RFP Documents", type=["pdf"], accept_multiple_files=True)
        if rfp_files:
            # Save uploaded RFP files to temporary locations
            rfp_paths = []
            for rfp_file in rfp_files:
                rfp_path = f"temp_{rfp_file.name}"
                with open(rfp_path, "wb") as f:
                    f.write(rfp_file.read())
                rfp_paths.append(rfp_path)

            # Merge multiple RFP files
            if st.button("Merge RFP Documents"):
                st.session_state.merged_rfp_writer = merge_multiple_pdfs(rfp_paths)
                st.success("RFP Documents merged successfully.")
                # Allow user to specify file name
                st.session_state.custom_file_name = st.text_input("Provide a name for the merged file", "")

    elif zip_checkbox:
        # Zip file upload section
        zip_file = st.file_uploader("Upload ZIP File", type=["zip"])
        if zip_file:
            # Extract the zip file and list the files
            extracted_files = extract_zip(zip_file)
            selected_rfp_files = st.multiselect("Select RFP Documents to Merge", extracted_files)
            
            if selected_rfp_files:
                rfp_paths = [os.path.join("temp_zip_extracted", file) for file in selected_rfp_files]

                # Merge the selected RFP files
                if st.button("Merge Selected RFP Documents"):
                    st.session_state.merged_rfp_writer = merge_multiple_pdfs(rfp_paths)
                    st.success("Selected RFP Documents merged successfully.")
                    st.session_state.zip_file_name = zip_file.name  # Save the ZIP file name in session state

    # Upload RFP response file after RFP documents are merged
    if st.session_state.merged_rfp_writer:
        # Upload RFP response
        response_file = st.file_uploader("Upload RFP Response Document", type=["pdf"], key="response_uploader")
        if response_file:
            response_path = "temp_response.pdf"
            with open(response_path, "wb") as f:
                f.write(response_file.read())

            # Show "Merge with RFP Response" button
            if st.button("Merge with RFP Response"):
                # Use zip file name if provided, otherwise use the custom name
                if st.session_state.zip_file_name:
                    output_file_name = os.path.splitext(st.session_state.zip_file_name)[0] + "_merged_with_response.pdf"
                else:
                    output_file_name = st.session_state.custom_file_name + "_merged_with_response.pdf"
                
                output_path = os.path.join("merged_folder", output_file_name)
                merge_pdfs_with_response(st.session_state.merged_rfp_writer, response_path, output_path)

                # Provide download link
                with open(output_path, 'rb') as f:
                    st.download_button("Download Merged RFP + Response PDF", f, file_name=output_file_name)

    else:
        # Default single RFP and single response upload section
        rfp_file = st.file_uploader("Upload RFP Document", type=["pdf"], key="single_rfp")
        response_file = st.file_uploader("Upload RFP Response Document", type=["pdf"], key="single_response")

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
                merged_rfp_writer = merge_multiple_pdfs([rfp_path])  # Single RFP
                output_path = os.path.join("merged_folder", f"{os.path.splitext(rfp_file.name)[0]}_merged.pdf")
                merge_pdfs_with_response(merged_rfp_writer, response_path, output_path)
                
                # Provide download link
                with open(output_path, 'rb') as f:
                    st.download_button("Download Merged PDF", f, file_name=f"{rfp_file.name}_merged.pdf")

    # Add a small credits section at the bottom
    st.markdown(
        """
        <div style="text-align: center; margin-top: 50px; font-size: 12px; color: gray;">
            Developed by Aditya and Mahir
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
