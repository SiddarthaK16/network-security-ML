import os
import sys
import json

from dotenv import load_dotenv
from networksecurity.logging.logger import logging
from networksecurity.exception.exception import NetworkSecurityException

import pandas as pd
import numpy as np
import pymongo
import certifi


load_dotenv()  # Load environment variables from the .env file

MONGO_DB_URL = os.getenv("MONGO_DB_URL")


# Get the path to Certifi's trusted CA certificate bundle
# for secure TLS/SSL connections.
ca = certifi.where()  # CA = Certificate Authority


class NetworkDataExtract:

    def __init__(self):
        try:
            pass

        except Exception as e:
            raise NetworkSecurityException(e, sys)


    def cv_to_json_converter(self, filepath):
        try:
            # Read the CSV file into a Pandas DataFrame
            data = pd.read_csv(filepath)

            # Reset the DataFrame index so that it starts from 0
            data.reset_index(drop=True, inplace=True)

            # Convert the DataFrame into a list of dictionaries.
            # Each dictionary represents one row/document,
            # which can be inserted into MongoDB.
            records = list(json.loads(data.T.to_json()).values())

            return records

        except Exception as e:
            raise NetworkSecurityException(e, sys)


    def insert_data_mongodb(self, records, database, collection):
        try:
            self.database = database
            self.collection = collection
            self.records = records

            # Establish a secure connection to MongoDB Atlas
            self.mongo_client = pymongo.MongoClient(
                MONGO_DB_URL,
                tlsCAFile=ca
            )

            # Access the specified database
            self.database = self.mongo_client[self.database]

            # Access the specified collection inside the database
            self.collection = self.database[self.collection]

            # Insert all records into the MongoDB collection
            result = self.collection.insert_many(self.records)

            # Return the number of successfully inserted documents
            return len(result.inserted_ids)

        except Exception as e:
            raise NetworkSecurityException(e, sys)


if __name__ == '__main__':

    FILE_PATH = "Network_data/phisingData.csv"
    DATABASE = "SIDD"
    Collection = "NetworkData"

    networkobj = NetworkDataExtract()

    # Convert CSV data into a list of MongoDB-compatible records
    records = networkobj.cv_to_json_converter(FILE_PATH)

    # Insert the records into MongoDB and get the number inserted
    no_of_records = networkobj.insert_data_mongodb(
        records,
        DATABASE,
        Collection
    )

    print(f"Number of records inserted into MongoDB: {no_of_records}")

