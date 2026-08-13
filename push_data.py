
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variabl "mongodb+srv://ksiddartha16_db_user:Siddu16@cluster0.lbxcr7m.mongodb.net/?appName=Cluster0"es from .env file

uri = os.getenv("MONGO_DB_URL")

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)