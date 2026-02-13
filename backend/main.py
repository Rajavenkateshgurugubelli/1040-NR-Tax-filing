from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from PyPDF2 import PdfMerger
import io

from .models import UserData
from .tax_engine import calculate_tax
from .pdf_engine import generate_pdf_bytes

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/preview-form/{form_id}")
async def preview_form(form_id: str, data: UserData):
    pdf_bytes = await generate_pdf_bytes(form_id, data)
    return StreamingResponse(
        io.BytesIO(pdf_bytes), 
        media_type="application/pdf", 
        headers={"Content-Disposition": f"attachment; filename={form_id}_Preview.pdf"}
    )

@app.post("/api/calculate-tax")
async def calculate_tax_api(data: UserData):
    """
    Returns the tax calculation summary and warnings (JSON) without generating PDF.
    """
    return calculate_tax(data)

@app.post("/api/generate-tax-return")
async def generate_tax_return(data: UserData):
    return await preview_form("1040nr", data)

@app.post("/api/download-complete-package")
async def download_complete_package(data: UserData):
    """
    Merge all tax forms into a single PDF package for download.
    Includes: 1040-NR, Form 8843, and Schedule NEC (if applicable).
    """
    try:
        merger = PdfMerger()
        
        # Generate 1040-NR
        pdf_1040nr = await generate_pdf_bytes("1040nr", data)
        if pdf_1040nr:
            merger.append(io.BytesIO(pdf_1040nr))
        
        # Check if Schedule NEC is needed
        tax_results = calculate_tax(data)
        if tax_results.get('nec_tax', 0) > 0:
             pdf_nec = await generate_pdf_bytes("nec", data)
             if pdf_nec:
                 merger.append(io.BytesIO(pdf_nec))
        
        # Generate Form 8843
        pdf_8843 = await generate_pdf_bytes("8843", data)
        if pdf_8843:
            merger.append(io.BytesIO(pdf_8843))
        
        # Write merged PDF to BytesIO
        output = io.BytesIO()
        merger.write(output)
        merger.close()
        output.seek(0)
        
        # Return as downloadable PDF
        return StreamingResponse(
            output,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=Tax_Package_2025.pdf"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error merging PDFs: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
