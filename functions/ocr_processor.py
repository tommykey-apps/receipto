"""Extract expense data from receipt using Claude Vision via Amazon Bedrock."""

from __future__ import annotations

import base64
import json
import os
import re

import boto3

bedrock = boto3.client("bedrock-runtime")
s3 = boto3.client("s3")

_MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "apac.anthropic.claude-sonnet-4-20250514-v1:0")

_PROMPT = """この画像は日本のレシートです。以下の情報をJSON形式で抽出してください。
金額は整数（円単位）で返してください。

{
  "store_name": "店名",
  "amount": 合計金額（税込）の整数,
  "date": "YYYY-MM-DD形式の日付"
}

読み取れない項目はnullにしてください。JSONのみを返し、他のテキストは含めないでください。"""


_MAX_LONG_EDGE = 1568  # Claude's internal downscale resolution
_MAX_BASE64_BYTES = 5_242_880  # 5MB Bedrock limit


def _resize_if_needed(image_bytes: bytes) -> bytes:
    """Resize image if it would exceed Bedrock's 5MB base64 limit."""
    import io

    from PIL import Image

    # Check if base64 would exceed limit (base64 is ~33% larger)
    if len(image_bytes) * 4 / 3 <= _MAX_BASE64_BYTES:
        return image_bytes

    img = Image.open(io.BytesIO(image_bytes))
    img.thumbnail((_MAX_LONG_EDGE, _MAX_LONG_EDGE), Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def _parse_amount(raw: str | int | float | None) -> int | None:
    """Parse amount to integer yen value."""
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return int(raw)
    cleaned = re.sub(r"[¥￥,、円\s]", "", str(raw))
    try:
        return int(float(cleaned))
    except ValueError:
        return None


def handler(event: dict, context: object) -> dict:  # noqa: ARG001
    bucket = event["bucket"]
    s3_key = event["s3_key"]
    receipt_id = event["receipt_id"]
    user_id = event["user_id"]

    # Download image from S3 and resize if needed
    obj = s3.get_object(Bucket=bucket, Key=s3_key)
    image_bytes = obj["Body"].read()
    image_bytes = _resize_if_needed(image_bytes)
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    # Determine media type
    lower_key = s3_key.lower()
    if lower_key.endswith(".png"):
        media_type = "image/png"
    elif lower_key.endswith(".webp"):
        media_type = "image/webp"
    else:
        media_type = "image/jpeg"

    # Call Claude via Bedrock
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 512,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": _PROMPT,
                    },
                ],
            }
        ],
    })

    resp = bedrock.invoke_model(
        modelId=_MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=body,
    )

    result_body = json.loads(resp["body"].read())
    text = result_body["content"][0]["text"]

    # Parse JSON from Claude's response
    store_name = None
    total_amount = None
    date = None

    try:
        # Extract JSON from response (Claude might wrap it in markdown)
        json_match = re.search(r"\{[^{}]+\}", text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            store_name = data.get("store_name")
            total_amount = _parse_amount(data.get("amount"))
            date = data.get("date")
    except (json.JSONDecodeError, AttributeError):
        pass

    return {
        "receipt_id": receipt_id,
        "user_id": user_id,
        "bucket": bucket,
        "s3_key": s3_key,
        "extracted": {
            "store_name": store_name or "",
            "amount": total_amount,
            "date": date,
        },
        "ocr_success": total_amount is not None,
    }
