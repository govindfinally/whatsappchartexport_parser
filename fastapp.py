# app.py
import io
import os
import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Path as ApiPath
from fastapi.responses import StreamingResponse, JSONResponse
from pathlib import Path as FilePath
from file_reader import FileReader, excelcleaner

app = FastAPI(title="NITR Placement Extractor API (backend)")
reader = FileReader()
cleaner = excelcleaner()

@app.get("/")
def read_root():
    return {"message": "Welcome to the placement of NIT Rourkela Data Extractor API"}

def _ensure_df_from_process(result):
    # process_content sometimes returns (df, log)
    if isinstance(result, tuple):
        return result[0]
    return result

# ----------------------------------------------------------------------
# PREVIEW ENDPOINT
# ----------------------------------------------------------------------
@app.post("/preview/", response_class=JSONResponse)
async def preview_file(file: UploadFile = File(...), preview_rows: int = 20):

    if not file.filename.lower().endswith(".txt"):
        raise HTTPException(400, "Please upload a .txt file")

    raw = await file.read()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("latin-1", errors="replace")

    result = reader.process_content(text, verbose=False)
    df = _ensure_df_from_process(result)

    # cleaning step
    try:
        cleaned_df = cleaner.filecleaner(df, newfilename=None)
    except TypeError:
        tmp = "tmp_cleaned_preview.xlsx"
        cleaned_df = cleaner.filecleaner(df, tmp)
        if cleaned_df is None and FilePath(tmp).exists():
            cleaned_df = pd.read_excel(tmp, engine="openpyxl")
            os.remove(tmp)

    if cleaned_df is None:
        cleaned_df = df

    preview = cleaned_df.head(preview_rows).to_dict(orient="records")
    return {
        "rows": cleaned_df.shape[0],
        "columns": cleaned_df.shape[1],
        "preview": preview
    }

# ----------------------------------------------------------------------
# SEARCH BY COMPANY NAME AFTER PARSING
# ----------------------------------------------------------------------
@app.get("/preview/{company_name}")
def view_file(company_name: str = ApiPath(..., description="Exact company name to look up")):

    if not hasattr(reader, "company_dict") or "name" not in reader.company_dict:
        raise HTTPException(404, "No parsed data available. Upload & process a file first.")

    # Try exact match
    try:
        index = reader.company_dict['name'].index(company_name)
    except ValueError:
        # Case-insensitive fallback
        names = reader.company_dict['name']
        idx = next((i for i, n in enumerate(names)
                    if isinstance(n, str) and n.lower() == company_name.lower()), None)
        if idx is None:
            raise HTTPException(404, "Company not found")
        index = idx

    return {key: reader.company_dict[key][index] for key in reader.company_dict}

# ----------------------------------------------------------------------
# FULL CLEAN + EXCEL DOWNLOAD ENDPOINT
# ----------------------------------------------------------------------
@app.post("/uploadfile/")
async def upload_file(file: UploadFile = File(...), download: bool = Query(True)):

    if not file.filename.lower().endswith(".txt"):
        raise HTTPException(400, "Please upload a .txt file")

    raw = await file.read()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("latin-1", errors="replace")

    result = reader.process_content(text, verbose=False)
    df = _ensure_df_from_process(result)

    # cleaning step
    try:
        cleaned_df = cleaner.filecleaner(df, newfilename=None)
    except TypeError:
        out_path = "cleaned_output.xlsx"
        cleaned_df = cleaner.filecleaner(df, out_path)
        if cleaned_df is None and FilePath(out_path).exists():
            cleaned_df = pd.read_excel(out_path, engine="openpyxl")
            os.remove(out_path)

    if cleaned_df is None:
        cleaned_df = df

    if not download:
        # return JSON preview instead of file
        preview = cleaned_df.head(20).to_dict(orient="records")
        return {"rows": cleaned_df.shape[0], "columns": cleaned_df.shape[1], "preview": preview}

    # stream excel in memory
    buffer = io.BytesIO()
    cleaned_df.to_excel(buffer, index=False, engine="openpyxl")
    buffer.seek(0)

    out_filename = f"cleaned_{file.filename.rsplit('.', 1)[0]}.xlsx"

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={out_filename}"}
    )
# ----------------------------------------------------------------------