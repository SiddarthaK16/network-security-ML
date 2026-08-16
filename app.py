import sys
import os

import certifi
ca = certifi.where()

from dotenv import load_dotenv
load_dotenv()

mongo_db_url = os.getenv("MONGO_DB_URL")

import pymongo

from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging
from networksecurity.pipeline.training_pipeline import TrainingPipeline

from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, File, UploadFile, Request
from uvicorn import run as app_run
from fastapi.responses import Response
from starlette.responses import RedirectResponse

import pandas as pd

from networksecurity.utils.main_utils.utils import load_object
from networksecurity.utils.ml_utils.model.estimator import NetworkModel

from networksecurity.constants.training_pipeline import (
    DATA_INGESTION_COLLECTION_NAME,
    DATA_INGESTION_DATABASE_NAME
)

from fastapi import FastAPI, File, UploadFile, Request, BackgroundTasks

# =========================================================
# DATABASE
# =========================================================

client = pymongo.MongoClient(
    mongo_db_url,
    tlsCAFile=ca
)

database = client[DATA_INGESTION_DATABASE_NAME]

collection = database[DATA_INGESTION_COLLECTION_NAME]


# =========================================================
# FASTAPI
# =========================================================

app = FastAPI(
    title="Network Security ML",
    description="Machine Learning based Network Security System",
    version="1.0.0"
)


origins = ["*"]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# TEMPLATES
# =========================================================

from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(
    directory="./templates"
)


# =========================================================
# HOME PAGE
# =========================================================

@app.get("/", tags=["authentication"])
async def index(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )


# =========================================================
# PREDICTION PAGE
# =========================================================

@app.get("/predict", tags=["Prediction"])
async def prediction_page(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="predict.html"
    )


# =========================================================
# TRAINING STATUS
# =========================================================

training_status = {
    "status": "idle",
    "message": "Ready to train.",
    "error": None
}


def run_training_pipeline():

    global training_status

    try:

        training_status["status"] = "running"
        training_status["message"] = "Training pipeline is running..."
        training_status["error"] = None

        logging.info("Training pipeline started from web application.")

        train_pipeline = TrainingPipeline()

        result = train_pipeline.run_pipeline()

        training_status["status"] = "completed"
        training_status["message"] = "Training completed successfully."

        logging.info("Training pipeline completed successfully.")

    except Exception as e:

        training_status["status"] = "failed"
        training_status["message"] = "Training failed."
        training_status["error"] = str(e)

        logging.error(
            f"Training pipeline failed: {str(e)}",
            exc_info=True
        )

# =========================================================
# TRAINING
# =========================================================

@app.get("/train", tags=["Training"])
async def train_route(
    request: Request,
    background_tasks: BackgroundTasks
):

    if training_status["status"] == "running":

        return templates.TemplateResponse(
            request=request,
            name="training.html",
            context={
                "status": "running",
                "message": "Training is already running..."
            }
        )

    training_status["status"] = "starting"
    training_status["message"] = "Starting training pipeline..."
    training_status["error"] = None

    background_tasks.add_task(run_training_pipeline)

    return templates.TemplateResponse(
        request=request,
        name="training.html",
        context={
            "status": "running",
            "message": "Training pipeline started..."
        }
    )

# =========================================================
# TRAINING STATUS API
# =========================================================

@app.get("/training-status")
async def training_status_route():

    return training_status


# =========================================================
# PREDICTION
# =========================================================

@app.post("/predict", tags=["Prediction"])
async def predict_route(
    request: Request,
    file: UploadFile = File(...)
):

    try:

        # -------------------------------------------------
        # Read CSV
        # -------------------------------------------------

        df = pd.read_csv(file.file)

        logging.info(
            f"Prediction request received: {df.shape}"
        )


        # -------------------------------------------------
        # Load trained model
        # -------------------------------------------------

        preprocessor = load_object(
            "final_model/preprocessor.pkl"
        )

        final_model = load_object(
            "final_model/model.pkl"
        )


        # -------------------------------------------------
        # Create NetworkModel
        # -------------------------------------------------

        network_model = NetworkModel(
            preprocessor=preprocessor,
            model=final_model
        )


        # -------------------------------------------------
        # Prediction
        # -------------------------------------------------

        y_pred = network_model.predict(df)


        # -------------------------------------------------
        # Add prediction column
        # -------------------------------------------------

        df["prediction"] = y_pred


        # -------------------------------------------------
        # Statistics
        # -------------------------------------------------

        total_predictions = len(y_pred)

        normal_count = int(
            (y_pred == 0).sum()
        )

        attack_count = int(
            (y_pred == 1).sum()
        )


        # -------------------------------------------------
        # Result table
        # -------------------------------------------------

        table_html = df.head(100).to_html(
            classes="prediction-table",
            index=False
        )


        # -------------------------------------------------
        # Return result page
        # -------------------------------------------------

        return templates.TemplateResponse(
            request=request,
            name="result.html",
            context={
                "filename": file.filename,
                "total_predictions": total_predictions,
                "normal_count": normal_count,
                "attack_count": attack_count,
                "table": table_html
            }
        )


    except Exception as e:

        logging.error(
            f"Prediction failed: {str(e)}"
        )

        raise NetworkSecurityException(
            e,
            sys
        )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    app_run(
        app,
        host="0.0.0.0",
        port=8000
    )