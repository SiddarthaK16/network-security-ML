from networksecurity.entity.artifact_entity import DataIngestionArtifact, DataValidationArtifact
from networksecurity.entity.config_entity import DataValidationConfig
from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.constants.training_pipeline import SCHEMA_FILE_PATH
from networksecurity.logging.logger import logging
from scipy.stats import ks_2samp
import pandas as pd
import os
import sys
from networksecurity.utils.main_utils.utils import read_yaml_file, write_yaml_file


class DataValidation:

    def __init__(
        self,
        data_ingestion_artifact: DataIngestionArtifact,
        data_validation_config: DataValidationConfig
    ):

        try:
            self.data_ingestion_artifact = data_ingestion_artifact
            self.data_validation_config = data_validation_config

            self._schema_config = read_yaml_file(SCHEMA_FILE_PATH)

        except Exception as e:
            raise NetworkSecurityException(e, sys)

    @staticmethod
    def read_data(file_path) -> pd.DataFrame:
        try:
            return pd.read_csv(file_path)

        except Exception as e:
            raise NetworkSecurityException(e, sys)

    def validate_number_of_columns(self, dataframe: pd.DataFrame) -> bool: 
        try:

            required_columns = [
                list(column.keys())[0]
                for column in self._schema_config["columns"] ]
                


            logging.info(
                f"Required number of columns : {len(required_columns)}"
            )

            logging.info(
                f"Data frame has {len(dataframe.columns)} columns."
            )

            # Check number of columns
            if len(dataframe.columns) != len(required_columns):
                return False

            # Check actual column names
            if set(dataframe.columns) != set(required_columns):
                return False

            return True

        except Exception as e:
            raise NetworkSecurityException(e, sys)

    def detect_dataset_drif(
        self,
        base_df,
        current_df,
        threshold=0.05
    ) -> bool:

        try:

            status = True
            report = {}

            for column in base_df.columns:

                d1 = base_df[column]
                d2 = current_df[column]

                is_sample_dist = ks_2samp(d1, d2)

                if threshold <= is_sample_dist.pvalue:

                    is_found = False

                else:

                    is_found = True
                    status = False

                report.update({
                    column: {
                        "p_value": float(is_sample_dist.pvalue),
                        "drift_status": is_found
                    }
                })

            drift_report_file_path = (
                self.data_validation_config.drift_report_file_path
            )

            # Create directory
            dir_path = os.path.dirname(drift_report_file_path)

            os.makedirs(
                dir_path,
                exist_ok=True
            )

            # Write drift report
            write_yaml_file(
                drift_report_file_path,
                content=report
            )

            return status

        except Exception as e:
            raise NetworkSecurityException(e, sys)

    def initiate_data_validation(self) -> DataValidationArtifact:

        try:

            error_message = ""

            # Get train and test file paths
            train_file_path = (
                self.data_ingestion_artifact.trained_file_path
            )

            test_file_path = (
                self.data_ingestion_artifact.test_file_path
            )

            # Read data from train and test
            train_dataframe = DataValidation.read_data(
                train_file_path
            )

            test_dataframe = DataValidation.read_data(
                test_file_path
            )

            # Validate train dataframe
            train_status = self.validate_number_of_columns(
                dataframe=train_dataframe
            )

            if not train_status:

                error_message += (
                    "Train data frame does not contain "
                    "the required columns.\n"
                )

            # Validate test dataframe
            test_status = self.validate_number_of_columns(
                dataframe=test_dataframe
            )

            if not test_status:

                error_message += (
                    "Test data frame does not contain "
                    "the required columns.\n"
                )

            # Check data drift
            drift_status = self.detect_dataset_drif(
                base_df=train_dataframe,
                current_df=test_dataframe
            )

            if not drift_status:

                error_message += (
                    "Data drift detected between "
                    "train and test datasets.\n"
                )

            # Overall validation status
            status = (
                train_status
                and test_status
                and drift_status
            )

            logging.info(
                f"Train validation status: {train_status}"
            )

            logging.info(
                f"Test validation status: {test_status}"
            )

            logging.info(
                f"Data drift status: {drift_status}"
            )

            logging.info(
                f"Overall validation status: {status}"
            )

            if error_message:

                logging.warning(
                    f"Data validation issues:\n{error_message}"
                )

            # Create valid directory
            dir_path_valid = os.path.dirname(
                self.data_validation_config.valid_train_file_path
            )

            # Create invalid directory
            dir_path_invalid = os.path.dirname(
                self.data_validation_config.invalid_train_file_path
            )

            os.makedirs(
                dir_path_valid,
                exist_ok=True
            )

            os.makedirs(
                dir_path_invalid,
                exist_ok=True
            )

            # Save data according to validation status
            if status:

                # Save to valid paths
                train_dataframe.to_csv(
                    self.data_validation_config.valid_train_file_path,
                    index=False
                )

                test_dataframe.to_csv(
                    self.data_validation_config.valid_test_file_path,
                    index=False
                )

                logging.info(
                    "Train and test data saved to valid paths."
                )

            else:

                # Save to invalid paths
                train_dataframe.to_csv(
                    self.data_validation_config.invalid_train_file_path,
                    index=False
                )

                test_dataframe.to_csv(
                    self.data_validation_config.invalid_test_file_path,
                    index=False
                )

                logging.warning(
                    "Train and test data saved to invalid paths."
                )

            # Prepare artifact
            data_validation_artifact = DataValidationArtifact(

                validation_status=status,

                valid_train_file_path=(
                    self.data_validation_config.valid_train_file_path
                ),

                valid_test_file_path=(
                    self.data_validation_config.valid_test_file_path
                ),

                invalid_train_file_path=(
                    self.data_validation_config.invalid_train_file_path
                ),

                invalid_test_file_path=(
                    self.data_validation_config.invalid_test_file_path
                ),

                drift_report_file_path=(
                    self.data_validation_config.drift_report_file_path
                ),
            )

            return data_validation_artifact

        except Exception as e:

            raise NetworkSecurityException(e, sys)