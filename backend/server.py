# from fastapi import FastAPI, APIRouter, HTTPException
# from dotenv import load_dotenv
# from starlette.middleware.cors import CORSMiddleware
# from motor.motor_asyncio import AsyncIOMotorClient
# import os
# import logging
# from pathlib import Path
# from pydantic import BaseModel, Field, ConfigDict
# from typing import List
# import uuid
# from datetime import datetime, timezone
# from models import ContactSubmission, ContactSubmissionCreate


# ROOT_DIR = Path(__file__).parent
# load_dotenv(ROOT_DIR / '.env')

# # MongoDB connection
# mongo_url = os.environ['MONGO_URL']
# client = AsyncIOMotorClient(mongo_url)
# db = client[os.environ['DB_NAME']]

# # Create the main app without a prefix
# app = FastAPI()

# # Create a router with the /api prefix
# api_router = APIRouter(prefix="/api")


# # Add your routes to the router instead of directly to app
# @api_router.get("/")
# async def root():
#     return {"message": "Portfolio API is running"}

# # Contact Form Endpoints
# @api_router.post("/contact")
# async def create_contact_submission(submission: ContactSubmissionCreate):
#     try:
#         # Create contact submission object
#         contact_obj = ContactSubmission(**submission.dict())
        
#         # Insert into database
#         result = await db.contact_submissions.insert_one(contact_obj.dict())
        
#         if result.inserted_id:
#             return {
#                 "success": True,
#                 "message": "Thank you for reaching out! I'll get back to you soon.",
#                 "id": contact_obj.id
#             }
#         else:
#             raise HTTPException(status_code=500, detail="Failed to save submission")
            
#     except Exception as e:
#         logger.error(f"Error saving contact submission: {str(e)}")
#         raise HTTPException(status_code=500, detail="Failed to process your request")

# @api_router.get("/contact")
# async def get_contact_submissions():
#     try:
#         submissions = await db.contact_submissions.find().sort("created_at", -1).to_list(1000)
#         return {
#             "success": True,
#             "submissions": [ContactSubmission(**sub) for sub in submissions]
#         }
#     except Exception as e:
#         logger.error(f"Error fetching contact submissions: {str(e)}")
#         raise HTTPException(status_code=500, detail="Failed to fetch submissions")

# # Include the router in the main app
# app.include_router(api_router)

# app.add_middleware(
#     CORSMiddleware,
#     allow_credentials=True,
#     allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Configure logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# )
# logger = logging.getLogger(__name__)

# @app.on_event("shutdown")
# async def shutdown_db_client():
#     client.close()
# -------------------------
# from fastapi import FastAPI, APIRouter, HTTPException
# from dotenv import load_dotenv
# from starlette.middleware.cors import CORSMiddleware
# from motor.motor_asyncio import AsyncIOMotorClient
# from models import ContactSubmission, ContactSubmissionCreate
# from datetime import datetime, timezone
# import os
# import logging
# import uuid
# from pathlib import Path

# # --- Load environment variables ---
# ROOT_DIR = Path(__file__).parent
# load_dotenv(ROOT_DIR / ".env")

# # --- MongoDB connection ---
# mongo_url = os.environ["MONGO_URL"]
# client = AsyncIOMotorClient(mongo_url)
# db = client[os.environ["DB_NAME"]]

# # --- App setup ---
# app = FastAPI()
# api_router = APIRouter(prefix="/api")

# # --- Routes ---
# @api_router.get("/")
# async def root():
#     return {"message": "Portfolio API is running"}

# @api_router.post("/contact")
# async def create_contact_submission(submission: ContactSubmissionCreate):
#     try:
#         contact_obj = ContactSubmission(
#             id=str(uuid.uuid4()),
#             name=submission.name,
#             email=submission.email,
#             subject=submission.subject,
#             message=submission.message,
#             created_at=datetime.now(timezone.utc),
#         )

#         result = await db.contact_submissions.insert_one(contact_obj.dict())

#         if result.inserted_id:
#             return {
#                 "success": True,
#                 "message": "Thank you for reaching out! I'll get back to you soon.",
#                 "id": contact_obj.id,
#             }
#         else:
#             raise HTTPException(status_code=500, detail="Failed to save submission")

#     except Exception as e:
#         logging.error(f"Error saving contact submission: {e}")
#         raise HTTPException(status_code=500, detail="Failed to process request")

# @api_router.get("/contact")
# async def get_contact_submissions():
#     try:
#         submissions = await db.contact_submissions.find().sort("created_at", -1).to_list(100)
#         return {
#             "success": True,
#             "submissions": submissions,
#         }
#     except Exception as e:
#         logging.error(f"Error fetching contact submissions: {e}")
#         raise HTTPException(status_code=500, detail="Failed to fetch submissions")

# # --- Include router ---
# app.include_router(api_router)

# # --- CORS ---
# app.add_middleware(
#     CORSMiddleware,
#     allow_credentials=True,
#     allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # --- Logging ---
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# @app.on_event("shutdown")
# async def shutdown_db_client():
#     client.close()

# ----------
from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import logging
from pathlib import Path

# --- Load environment variables ---
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

# --- Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("contact_form")

# --- App setup ---
app = FastAPI()
api_router = APIRouter(prefix="/api")

# --- Contact form model ---
class ContactSubmissionCreate(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str

# --- Send email function ---
def send_email(name, sender_email, subject, message):
    try:
        smtp_host = os.environ["SMTP_HOST"]
        smtp_port = int(os.environ["SMTP_PORT"])
        smtp_user = os.environ["SMTP_USER"]
        smtp_password = os.environ["SMTP_PASSWORD"]
        email_to = os.environ["EMAIL_TO"]

        msg = MIMEMultipart()
        msg["From"] = smtp_user
        msg["To"] = email_to
        msg["Subject"] = f"Contact Form: {subject} from {name}"

        body = f"Name: {name}\nEmail: {sender_email}\n\nMessage:\n{message}"
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        
        logger.info(f"Email sent successfully from {sender_email} with subject '{subject}'")
    except Exception as e:
        logger.error(f"Failed to send email from {sender_email} with subject '{subject}': {e}")
        raise

# --- Routes ---
@api_router.get("/")
async def root():
    return {"message": "Portfolio API is running"}

@api_router.post("/contact")
async def create_contact_submission(submission: ContactSubmissionCreate):
    try:
        send_email(
            submission.name,
            submission.email,
            submission.subject,
            submission.message
        )
        logger.info(f"Contact form submission successful for {submission.email}")
        return {
            "success": True,
            "message": "Thank you for reaching out! Your message has been sent."
        }
    except Exception as e:
        logger.exception("Error processing contact form submission")
        raise HTTPException(status_code=500, detail="Failed to send your message. Please try again later.")

# --- Include router ---
app.include_router(api_router)

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)
