import logging
import os
import subprocess
import zipfile
from pathlib import Path
import redis
from fastapi import FastAPI, File, UploadFile, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from starlette.requests import Request
from spire.doc import *
from spire.doc.common import *
import re
# Set up Redis client (use redis.Redis instead of redis.StrictRedis)
redis_client = redis.Redis(host="172.16.117.47", port=6379, db=0, decode_responses=True, socket_timeout=30)  # Docker Redis service

# Set up logging to Redis
class RedisHandler(logging.Handler):
    def emit(self, record):
        log_entry = self.format(record)
        try:
            redis_client.lpush("app_logs", log_entry)  # Push logs to Redis list
        except redis.exceptions.ConnectionError as e:
            logging.error(f"Failed to send log to Redis: {e}")  # Handle Redis errors, log them instead of raising exceptions

# Set up logging configuration
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[RedisHandler()]  # Use RedisHandler to log to Redis
)

app = FastAPI()

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory for uploaded files
BASE_UPLOAD_DIR = Path("uploads")
BASE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
logging.info("Upload directory initialized at: %s", BASE_UPLOAD_DIR)

# Create a new APIRouter for the conversion-related routes (version 1)
convert_router_v1 = APIRouter(prefix="/api/v1/convert", tags=["convert-v1"])

# Base route for /api/v1/convert/
@convert_router_v1.get("/")
async def root_v1():
    logging.debug("Base route for v1 accessed.")
    return {"message": "Welcome to the FastAPI file upload and conversion service! (v1)"}

# File upload route under /api/v1/convert/upload-docx/
@convert_router_v1.post("/docx2html/")
async def upload_docx_v1(file: UploadFile = File(...)):
    logging.debug("Received file upload request for v1.")
    
    # Validate MIME type for DOCX
    if file.content_type not in [
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # DOCX MIME type
    "application/msword"  # DOC MIME type
]:
        logging.error("Invalid file type received: %s", file.content_type)
        raise HTTPException(
            status_code=400, detail="Invalid file type. Please upload a DOCX file."
        )

    try:
        # Define paths
        file_name_without_ext = file.filename.rsplit(".", 1)[0]
        target_folder = BASE_UPLOAD_DIR / file_name_without_ext
        target_folder.mkdir(parents=True, exist_ok=True)
        logging.debug("Target folder created at: %s", target_folder)

        # Save uploaded file
        file_path = target_folder / file.filename
        with open(file_path, "wb") as f:
            f.write(await file.read())
        logging.debug("Saved uploaded file to: %s", file_path)

        # Run LibreOffice conversion
        logging.debug("Running LibreOffice conversion...")
        subprocess.run(
            [
                "libreoffice",
                "--headless",               # Run LibreOffice without its GUI
                "--convert-to",             # Specify the conversion type
                "html:HTML:EmbedImages",    # Convert to HTML with embedded images "html:HTML:EmbedImages"
                "--outdir", str(target_folder),  # Specify the target folder for the output
                str(file_path),             # Path to the file you want to convert
            ],
            check=True,  # Ensure the command raises an error if it fails
        )
        logging.debug("LibreOffice conversion completed successfully.")

        # Zip the valid converted files
        zip_file_path = target_folder / "converted_files.zip"
        with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_in_dir in target_folder.iterdir():
                if file_in_dir.suffix.lower() in [".html", ".gif", ".png"]:
                    zipf.write(file_in_dir, arcname=file_in_dir.name)
                    logging.debug("Adding file to zip: %s", file_in_dir)

        logging.debug("ZIP file created at: %s", zip_file_path)

        # Send the file to the client
        response = FileResponse(
            path=zip_file_path,
            media_type="application/zip",
            filename="converted_files.zip",
            headers={"Content-Disposition": "attachment; filename=converted_files.zip"}
        )

        # response = FileResponse(
        #     path=zip_file_path,
        #     media_type="application/html",
        #     filename=f"{file_name_without_ext}.html",
        #     headers={"Content-Disposition": f"attachment; filename={file_name_without_ext}.html"}
        # )
        logging.debug("Sending response to client.")

        return response

    except subprocess.CalledProcessError as e:
        logging.error("LibreOffice conversion failed with error: %s", e)
        raise HTTPException(status_code=500, detail=f"LibreOffice conversion failed: {e}")
    except Exception as e:
        logging.error("Unexpected error occurred: %s", e)
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")


# File upload route under /api/v1/convert/upload-docx-to-pdf/
@convert_router_v1.post("/docx2pdf/")
async def upload_docx_to_pdf_v1(file: UploadFile = File(...)):
    logging.debug("Received DOCX to PDF conversion request.")
    
    # Validate MIME type for DOCX
    if file.content_type != "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        logging.error("Invalid file type received: %s", file.content_type)
        raise HTTPException(
            status_code=400, detail="Invalid file type. Please upload a DOCX file."
        )

    try:
        # Define paths
        file_name_without_ext = file.filename.rsplit(".", 1)[0]
        target_folder = BASE_UPLOAD_DIR / file_name_without_ext
        target_folder.mkdir(parents=True, exist_ok=True)
        logging.debug("Target folder created at: %s", target_folder)

        # Save uploaded file
        file_path = target_folder / file.filename
        with open(file_path, "wb") as f:
            f.write(await file.read())
        logging.debug("Saved uploaded file to: %s", file_path)

        # Run LibreOffice conversion (DOCX to PDF)
        logging.debug("Running LibreOffice conversion from DOCX to PDF...")
        subprocess.run(
            [
                "libreoffice",
                "--headless",              # Run LibreOffice without its GUI
                "--convert-to",            # Specify the conversion type
                "pdf",                     # Convert to PDF
                "--outdir", str(target_folder),  # Specify the output directory
                str(file_path),            # Path to the DOCX file
            ],
            check=True,  # Ensure the command raises an error if it fails
        )
        logging.debug("LibreOffice conversion to PDF completed successfully.")
        file_name = f"{file_name_without_ext}.pdf"
        # Get the converted PDF file path
        pdf_file_path = target_folder / file_name
        
        # Send the PDF file as a response
        response = FileResponse(
            path=pdf_file_path,
            media_type="application/pdf",
            filename=f"{file_name_without_ext}.pdf",
            headers={"Content-Disposition": f"attachment; filename={file_name_without_ext}.pdf"}
        )
        logging.debug("Sending PDF response to client.")
        return response

    except subprocess.CalledProcessError as e:
        logging.error("LibreOffice conversion failed with error: %s", e)
        raise HTTPException(status_code=500, detail=f"LibreOffice conversion failed: {e}")
    except Exception as e:
        logging.error("Unexpected error occurred: %s", e)
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

# File upload route under /api/v1/convert/upload-pdf-to-docx/
@convert_router_v1.post("/pdf2docx/")
async def upload_pdf_to_docx_v1(file: UploadFile = File(...)):
    logging.debug("Received PDF to DOCX conversion request.")
    
    # Validate MIME type for PDF
    if file.content_type != "application/pdf":
        logging.error("Invalid file type received: %s", file.content_type)
        raise HTTPException(
            status_code=400, detail="Invalid file type. Please upload a PDF file."
        )

    try:
        # Define paths
        file_name_without_ext = file.filename.rsplit(".", 1)[0]
        target_folder = BASE_UPLOAD_DIR / file_name_without_ext
        target_folder.mkdir(parents=True, exist_ok=True)
        logging.debug("Target folder created at: %s", target_folder)

        # Save uploaded file
        file_path = target_folder / file.filename
        with open(file_path, "wb") as f:
            f.write(await file.read())
        logging.debug("Saved uploaded file to: %s", file_path)
        print("target_folder :", target_folder)
        # Run LibreOffice conversion (PDF to DOCX)
        logging.debug("Running LibreOffice conversion from PDF to DOCX...")
        subprocess.run(
            [
                "libreoffice",
                "--headless",              # Run LibreOffice without its GUI
                "--convert-to",            # Specify the conversion type
                "docx",                    # Convert to DOCX
                "--outdir", str(target_folder),  # Specify the output directory
                str(file_path),            # Path to the PDF file
            ],
            check=True,  # Ensure the command raises an error if it fails
        )
        logging.debug("LibreOffice conversion to DOCX completed successfully.")
        file_name = f"{file_name_without_ext}.docx"
        # Get the converted DOCX file path
        docx_file_path = target_folder / file_name
        
        # Send the DOCX file as a response
        response = FileResponse(
            path=docx_file_path,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=f"{file_name_without_ext}.docx",
            headers={"Content-Disposition": f"attachment; filename={file_name_without_ext}.docx"}
        )
        logging.debug("Sending DOCX response to client.")
        return response

    except subprocess.CalledProcessError as e:
        logging.error("LibreOffice conversion failed with error: %s", e)
        raise HTTPException(status_code=500, detail=f"LibreOffice conversion failed: {e}")
    except Exception as e:
        logging.error("Unexpected error occurred: %s", e)
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

# File upload route under /api/v1/convert/upload-pdf-to-html/
# File upload route under /api/v1/convert/upload-pdf-to-docx-to-html/
@convert_router_v1.post("/pdf2html/")
async def upload_pdf_to_docx_to_html_v1(file: UploadFile = File(...)):
    logging.debug("Received PDF to DOCX to HTML conversion request.")
    
    # Validate MIME type for PDF
    if file.content_type != "application/pdf":
        logging.error("Invalid file type received: %s", file.content_type)
        raise HTTPException(
            status_code=400, detail="Invalid file type. Please upload a PDF file."
        )

    try:
        # Define paths
        file_name_without_ext = file.filename.rsplit(".", 1)[0]
        target_folder = BASE_UPLOAD_DIR / file_name_without_ext
        target_folder.mkdir(parents=True, exist_ok=True)
        logging.debug("Target folder created at: %s", target_folder)

        # Save uploaded PDF file
        file_path = target_folder / file.filename
        with open(file_path, "wb") as f:
            f.write(await file.read())
        logging.debug("Saved uploaded file to: %s", file_path)

        # Step 1: Convert PDF to DOCX using LibreOffice
        logging.debug("Running LibreOffice conversion from PDF to DOCX...")
        subprocess.run(
            [
                "libreoffice",
                "--headless",              # Run LibreOffice without GUI
                "--convert-to",            # Specify the conversion type
                "docx",                    # Convert to DOCX
                "--outdir", str(target_folder),  # Specify the output directory
                str(file_path),            # Path to the uploaded PDF
            ],
            check=True,  # Ensure the command raises an error if it fails
        )
        logging.debug("LibreOffice conversion from PDF to DOCX completed successfully.")

        # Get the converted DOCX file path
        docx_file_path = target_folder / f"{file_name_without_ext}.docx"
        
        # Step 2: Convert DOCX to HTML using LibreOffice
        logging.debug("Running LibreOffice conversion from DOCX to HTML...")
        subprocess.run(
            [
                "libreoffice",
                "--headless",               # Run LibreOffice without its GUI
                "--convert-to",             # Specify the conversion type
                "html:HTML:EmbedImages",    # Convert to HTML with embedded images
                "--outdir", str(target_folder),  # Specify the target folder for the output
                str(file_path),             # Path to the file you want to convert
            ],
            check=True,  # Ensure the command raises an error if it fails
        )
        logging.debug("LibreOffice conversion from DOCX to HTML completed successfully.")

        # Get the converted HTML file path
        html_file_path = target_folder / f"{file_name_without_ext}.html"
        
        # Send the HTML file as a response
        response = FileResponse(
            path=html_file_path,
            media_type="text/html",
            filename=f"{file_name_without_ext}.html",
            headers={"Content-Disposition": f"attachment; filename={file_name_without_ext}.html"}
        )
        logging.debug("Sending HTML response to client.")
        return response

    except subprocess.CalledProcessError as e:
        logging.error("LibreOffice conversion failed with error: %s", e)
        raise HTTPException(status_code=500, detail=f"Conversion failed: {e}")
    except Exception as e:
        logging.error("Unexpected error occurred: %s", e)
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")



# Version 2: File upload route under /api/v2/convert/upload-docx/
convert_router_v2 = APIRouter(prefix="/api/v2/convert", tags=["convert-v2"])

# Base route for /api/v2/convert/
@convert_router_v2.get("/")
async def root_v2():
    logging.debug("Base route for v2 accessed.")
    return {"message": "Welcome to the Conversion file upload and conversion service! (v2)"}

@convert_router_v2.post("/docx2html/")
async def upload_docx_v2(file: UploadFile = File(...)):
    logging.debug("Received file upload request for v2.")

    # Validate MIME type for DOCX
    if file.content_type != "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        logging.error("Invalid file type received: %s", file.content_type)
        raise HTTPException(
            status_code=400, detail="Invalid file type. Please upload a DOCX file."
        )

    try:
        # Define paths
        file_name_without_ext = file.filename.rsplit(".", 1)[0]
        target_folder = BASE_UPLOAD_DIR / file_name_without_ext
        target_folder.mkdir(parents=True, exist_ok=True)
        logging.debug("Target folder created at: %s", target_folder)

        # Save uploaded file
        file_path = target_folder / file.filename
        with open(file_path, "wb") as f:
            f.write(await file.read())
        logging.debug("Saved uploaded file to: %s", file_path)

        # Convert DOCX to HTML using Spire.Doc (Ensure Spire.Doc is installed and accessible)
        document = Document()

        # Load the DOCX file
        document.LoadFromFile(str(file_path))

        # Export document style to head in HTML
        document.HtmlExportOptions.IsExportDocumentStyles = True

        # Set the type of CSS style sheet as internal
        document.HtmlExportOptions.CssStyleSheetType = CssStyleSheetType.Internal

        # Embed images in HTML code
        document.HtmlExportOptions.ImageEmbedded = True

        # Export form fields as text
        document.HtmlExportOptions.IsTextInputFormFieldAsText = True

        # Save the document as an HTML file
        html_file_path = str(file_path).replace(".docx", ".html")
        document.SaveToFile(html_file_path, FileFormat.Html)
        logging.debug(f"Converted DOCX to HTML: {html_file_path}")

        # Read the HTML file and apply regex to remove the <span> with the warning text
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # Regex pattern to remove both types of evaluation warning spans
        pattern = r'<span\s+style="[^"]*(font-family:\'Times New Roman\';\s*)?color:#ff0000[^"]*">Evaluation Warning: The document was created with Spire\.Doc for Python\.</span>'

        # Remove the matching pattern from the HTML content
        html_content = re.sub(pattern, '', html_content)

        # Logging the result
        logging.debug("Removed evaluation warning span from HTML.")
                # Save the modified HTML back to the file
        with open(html_file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logging.debug(f"Modified HTML file saved at: {html_file_path}")

        # Dispose of the document object to release resources
        document.Dispose()

        # Send the modified HTML file back as a download
        return FileResponse(
            path=html_file_path,
            media_type="text/html",
            filename=os.path.basename(html_file_path),
            headers={"Content-Disposition": f"attachment; filename={os.path.basename(html_file_path)}"}
        )

    except Exception as e:
        logging.error(f"An error occurred during conversion: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


# Endpoint to fetch last 50 logs from Redis
@app.get("/logs")
async def get_logs():
    try:
        # Fetch the last 50 logs from Redis
        logs = redis_client.lrange("app_logs", 0, 49)  # Get the last 50 logs
        logs.reverse()  # Redis stores logs in reverse order
        return {"logs": logs}
    except redis.exceptions.ConnectionError as e:
        logging.error(f"Error fetching logs from Redis: {e}")
        raise HTTPException(status_code=500, detail="Error fetching logs from Redis")

# Include the versioned routers in the main FastAPI app
app.include_router(convert_router_v1)
app.include_router(convert_router_v2)
