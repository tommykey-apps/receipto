from __future__ import annotations

import os

import boto3
from fastapi import APIRouter, Depends, HTTPException
from ulid import ULID

from auth import get_user_id
from models.schemas import PresignedUrlResponse, UploadRequest
from store.dynamodb import DynamoDBStore

router = APIRouter(tags=["receipts"])
store = DynamoDBStore()


def _get_s3_client():  # noqa: ANN202
    endpoint_url = os.environ.get("S3_ENDPOINT")
    kwargs = {}
    if endpoint_url:
        kwargs["endpoint_url"] = endpoint_url
    return boto3.client("s3", **kwargs)


@router.post("/receipts/upload", response_model=PresignedUrlResponse, status_code=201)
def upload_receipt(
    body: UploadRequest,
    user_id: str = Depends(get_user_id),
) -> PresignedUrlResponse:
    bucket = os.environ.get("RECEIPTS_BUCKET", "expense-tracker-receipts")
    receipt_id = str(ULID())
    s3_key = f"uploads/{user_id}/{receipt_id}/{body.filename}"

    s3 = _get_s3_client()
    upload_url = s3.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": bucket,
            "Key": s3_key,
            "ContentType": body.content_type,
        },
        ExpiresIn=300,
    )

    store.put_receipt(user_id, receipt_id, s3_key, body.filename)

    return PresignedUrlResponse(
        upload_url=upload_url,
        receipt_id=receipt_id,
        s3_key=s3_key,
    )


@router.get("/receipts/{receipt_id}")
def get_receipt(
    receipt_id: str,
    user_id: str = Depends(get_user_id),
) -> dict:
    receipt = store.get_receipt(user_id, receipt_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return receipt
