from fastapi import FastAPI, UploadFile, File, Form  # type: ignore[reportMissingImports]
from fastapi.middleware.cors import CORSMiddleware  # type: ignore[reportMissingImports]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"message": "Crop Disease Detection API is running"}


@app.post("/predict")
async def predict(
    crop: str = Form(...),
    image: UploadFile = File(...)
):
    return {
        "crop": crop,
        "filename": image.filename,
        "disease": "Test Disease",
        "confidence": 95.2
    }