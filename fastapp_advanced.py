# app.py (add / replace)
import io
import os
import uuid
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse
from file_reader import FileReader, excelcleaner

UPLOAD_DIR = Path("temp_uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI()
reader = FileReader()
cleaner = excelcleaner()

def _ensure_df_from_process(result):
    return result[0] if isinstance(result, tuple) else result

@app.post("/upload/")
async def upload(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".txt"):
        raise HTTPException(400, "Please upload a .txt file")
    file_id = str(uuid.uuid4())
    dest = UPLOAD_DIR / f"{file_id}.txt"
    contents = await file.read()
    # write to disk
    dest.write_bytes(contents)
    return {"id": file_id, "filename": file.filename}

@app.post("/process/{file_id}")
async def process(file_id: str, download: bool = Query(False), verbose: bool = Query(False)):
    # locate saved file
    path = UPLOAD_DIR / f"{file_id}.txt"
    if not path.exists():
        raise HTTPException(404, "Upload id not found")

    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("latin-1", errors="replace")

    result = reader.process_content(text, verbose=verbose)
    df = _ensure_df_from_process(result)

    # cleaning step (prefer in-memory)
    try:
        cleaned_df = cleaner.filecleaner(df, newfilename=None)
    except TypeError:
        # if your cleaner requires filename
        cleaned_df = cleaner.filecleaner(df, "tmp_cleaned.xlsx")

    if not download:
        preview = cleaned_df.head(50).to_dict(orient="records")
        return JSONResponse({"rows": int(cleaned_df.shape[0]), "columns": int(cleaned_df.shape[1]), "preview": preview})

    # create Excel bytes and stream
    buffer = io.BytesIO()
    cleaned_df.to_excel(buffer, index=False, engine="openpyxl")
    buffer.seek(0)
    filename = f"cleaned_{file_id}.xlsx"
    return StreamingResponse(buffer,
                            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            headers={"Content-Disposition": f"attachment; filename={filename}"})

@app.delete("/upload/{file_id}")
def delete_upload(file_id: str):
    path = UPLOAD_DIR / f"{file_id}.txt"
    if path.exists():
        path.unlink()
        return {"deleted": True}
    return {"deleted": False}
