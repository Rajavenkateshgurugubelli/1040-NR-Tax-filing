
@app.post("/api/download-complete-package")
async def download_complete_package(data: UserData):
    """
    Merge all tax forms into a single PDF package for download.
    Includes: 1040-NR, Form 8843, and Schedule NEC (if applicable).
    """
    try:
        merger = PdfMerger()
        
        # Generate 1040-NR
        pdf_1040nr = await preview_form("1040nr", data)
        if pdf_1040nr:
            merger.append(pdf_1040nr)
        
        # Generate Form 8843
        pdf_8843 = await preview_form("8843", data)
        if pdf_8843:
            merger.append(pdf_8843)
        
        # Generate Schedule NEC (if user has additional income)
        has_additional_income = (
            data.dividend_income > 0 or 
            data.interest_income > 0 or 
            data.capital_gains > 0 or
            data.scholarship_grants > 0
        )
        if has_additional_income:
            pdf_nec = await preview_form("schedule_nec", data)
            if pdf_nec:
                merger.append(pdf_nec)
        
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
                "Content-Disposition": f"attachment; filename=Tax_Package_2025_{data.full_name.replace(' ', '_')}.pdf"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error merging PDFs: {str(e)}")
