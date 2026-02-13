from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from PyPDF2 import PdfMerger
import io
from sqlalchemy.orm import Session

from .models import UserData
from .tax_engine import calculate_tax
from .pdf_engine import generate_pdf_bytes
from . import models_db, schemas, auth, database

# Create Database Tables
models_db.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"], # Vite & generic React
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth Endpoints
@app.post("/api/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models_db.User).filter(models_db.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = auth.timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/register", response_model=schemas.UserResponse)
def register_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = db.query(models_db.User).filter(models_db.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = auth.get_password_hash(user.password)
    new_user = models_db.User(email=user.email, password_hash=hashed_password, full_name=user.full_name)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.get("/api/users/me", response_model=schemas.UserResponse)
async def read_users_me(current_user: models_db.User = Depends(auth.get_current_user)):
    return current_user

# Admin Dependency
def get_current_active_superuser(current_user: models_db.User = Depends(auth.get_current_user)):
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="The user doesn't have enough privileges")
    return current_user

@app.get("/api/admin/users", response_model=List[schemas.UserResponse])
async def read_users(
    skip: int = 0, 
    limit: int = 100, 
    current_user: models_db.User = Depends(get_current_active_superuser),
    db: Session = Depends(database.get_db)
):
    users = db.query(models_db.User).offset(skip).limit(limit).all()
    return users

@app.get("/api/admin/stats")
async def read_admin_stats(
    current_user: models_db.User = Depends(get_current_active_superuser),
    db: Session = Depends(database.get_db)
):
    user_count = db.query(models_db.User).count()
    return_count = db.query(models_db.TaxReturn).count()
    return {"user_count": user_count, "tax_return_count": return_count}

import csv
import zipfile
from fastapi import UploadFile, File

@app.post("/api/admin/bulk-upload")
async def upload_bulk_csv(
    file: UploadFile = File(...),
    current_user: models_db.User = Depends(get_current_active_superuser)
):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a CSV.")

    content = await file.read()
    decoded_content = content.decode('utf-8').splitlines()
    reader = csv.DictReader(decoded_content)
    
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for i, row in enumerate(reader):
            try:
                # Map CSV row to UserData (basic mapping, assumes CSV headers match model fields)
                # Cleanup monetary fields
                for key in ['wages', 'federal_tax_withheld', 'state_tax_withheld', 'dividend_income']:
                    if key in row and row[key]:
                         row[key] = float(row[key].replace('$', '').replace(',', ''))
                
                user_data = UserData(**row) # Validates data
                
                # Generate PDF
                pdf_bytes = generate_pdf_bytes(user_data)
                
                filename = f"{user_data.full_name.replace(' ', '_')}_1040NR.pdf"
                zip_file.writestr(filename, pdf_bytes)
                
            except Exception as e:
                print(f"Skipping row {i}: {e}")
                zip_file.writestr(f"error_row_{i}.txt", str(e))

    zip_buffer.seek(0)
    
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=bulk_tax_forms.zip"}
    )

@app.post("/api/tax-returns")
async def create_or_update_tax_return(
    data: UserData, 
    current_user: models_db.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    # Check if exists
    db_return = db.query(models_db.TaxReturn).filter(
        models_db.TaxReturn.user_id == current_user.id,
        models_db.TaxReturn.tax_year == data.tax_year
    ).first()

    if db_return:
        db_return.form_data = data.dict()
    else:
        db_return = models_db.TaxReturn(
            user_id=current_user.id,
            tax_year=data.tax_year,
            form_data=data.dict()
        )
        db.add(db_return)
    
    db.commit()
    return {"status": "success", "message": "Tax return saved"}

@app.get("/api/tax-returns/{year}")
async def get_tax_return(
    year: int,
    current_user: models_db.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    db_return = db.query(models_db.TaxReturn).filter(
        models_db.TaxReturn.user_id == current_user.id,
        models_db.TaxReturn.tax_year == year
    ).first()
    
    if not db_return:
        raise HTTPException(status_code=404, detail="Tax return not found")
        
    return db_return.form_data

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
