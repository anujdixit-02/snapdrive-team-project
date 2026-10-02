import os
import boto3

from dotenv import load_dotenv
from botocore.exceptions import ClientError


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# AWS CONFIGURATION
# ============================================================

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")

AWS_SECRET_ACCESS_KEY = os.getenv(
    "AWS_SECRET_ACCESS_KEY"
)

AWS_REGION = os.getenv(
    "AWS_REGION",
    "ap-northeast-3"
)

S3_BUCKET_NAME = os.getenv(
    "S3_BUCKET_NAME"
)


# ============================================================
# VALIDATE CONFIGURATION
# ============================================================

if not AWS_ACCESS_KEY_ID:
    raise RuntimeError(
        "AWS_ACCESS_KEY_ID is not configured."
    )

if not AWS_SECRET_ACCESS_KEY:
    raise RuntimeError(
        "AWS_SECRET_ACCESS_KEY is not configured."
    )

if not S3_BUCKET_NAME:
    raise RuntimeError(
        "S3_BUCKET_NAME is not configured."
    )


# ============================================================
# CREATE S3 CLIENT
# ============================================================

s3_client = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)


# ============================================================
# UPLOAD FILE TO S3
# ============================================================

def upload_file_to_s3(
    file_content: bytes,
    object_key: str,
    content_type: str = None
):
    """
    Upload file bytes to Amazon S3.

    Parameters:
        file_content:
            File data in bytes.

        object_key:
            S3 object path/key.

        content_type:
            MIME type of the uploaded file.

    Returns:
        S3 object key.
    """

    try:

        extra_args = {}

        if content_type:
            extra_args["ContentType"] = content_type

        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=object_key,
            Body=file_content,
            **extra_args
        )

        return object_key

    except ClientError as e:

        print("S3 UPLOAD ERROR:")
        print(e)

        raise Exception(
            "Failed to upload file to Amazon S3."
        )


# ============================================================
# DOWNLOAD FILE FROM S3
# ============================================================

def download_file_from_s3(
    object_key: str
):
    """
    Download a file directly from Amazon S3.

    Returns:
        File contents as bytes.
    """

    try:

        response = s3_client.get_object(
            Bucket=S3_BUCKET_NAME,
            Key=object_key
        )

        return response["Body"].read()

    except ClientError as e:

        print("S3 DOWNLOAD ERROR:")
        print(e)

        error_code = e.response.get(
            "Error",
            {}
        ).get(
            "Code"
        )

        if error_code in [
            "404",
            "NoSuchKey",
            "NotFound"
        ]:

            raise FileNotFoundError(
                "File not found in Amazon S3."
            )

        raise Exception(
            "Failed to download file from Amazon S3."
        )


# ============================================================
# DELETE FILE FROM S3
# ============================================================

def delete_file_from_s3(
    object_key: str
):
    """
    Delete an object from Amazon S3.
    """

    try:

        s3_client.delete_object(
            Bucket=S3_BUCKET_NAME,
            Key=object_key
        )

        return True

    except ClientError as e:

        print("S3 DELETE ERROR:")
        print(e)

        raise Exception(
            "Failed to delete file from Amazon S3."
        )


# ============================================================
# CHECK FILE EXISTS IN S3
# ============================================================

def file_exists_in_s3(
    object_key: str
):
    """
    Check whether an object exists in Amazon S3.

    Returns:
        True  -> object exists
        False -> object does not exist
    """

    try:

        s3_client.head_object(
            Bucket=S3_BUCKET_NAME,
            Key=object_key
        )

        return True

    except ClientError as e:

        error_code = e.response.get(
            "Error",
            {}
        ).get(
            "Code"
        )

        if error_code in [
            "404",
            "NoSuchKey",
            "NotFound"
        ]:

            return False

        raise


# ============================================================
# GENERATE PRESIGNED URL
# ============================================================

def generate_presigned_download_url(
    object_key: str,
    expiration: int = 3600,
    download_filename: str = None,
    inline: bool = False
):
    """
    Generate a temporary presigned URL for an S3 object.

    Parameters:
        object_key:
            S3 object key.

        expiration:
            URL validity in seconds.
            Default = 3600 seconds = 1 hour.

        download_filename:
            Original filename shown to the user.

        inline:
            True  -> browser attempts to display file.
            False -> browser treats it as a download.

    Returns:
        Presigned S3 URL.
    """

    try:

        params = {
            "Bucket": S3_BUCKET_NAME,
            "Key": object_key
        }

        # ----------------------------------------------------
        # Set Content-Disposition
        # ----------------------------------------------------

        if inline:

            params[
                "ResponseContentDisposition"
            ] = "inline"

        elif download_filename:

            safe_filename = (
                download_filename
                .replace('"', "")
                .replace("\r", "")
                .replace("\n", "")
            )

            params[
                "ResponseContentDisposition"
            ] = (
                f'attachment; filename="{safe_filename}"'
            )

        # ----------------------------------------------------
        # Generate URL
        # ----------------------------------------------------

        url = s3_client.generate_presigned_url(
            ClientMethod="get_object",
            Params=params,
            ExpiresIn=expiration
        )

        return url

    except ClientError as e:

        print("S3 PRESIGNED URL ERROR:")
        print(e)

        raise Exception(
            "Failed to generate S3 download URL."
        )