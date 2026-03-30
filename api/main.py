from __future__ import annotations

import os

from app import create_app

app = create_app()

if os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
    from mangum import Mangum

    handler = Mangum(app)
else:

    def handler(event: dict, context: object) -> None:  # noqa: ARG001
        raise RuntimeError("Not running in Lambda mode")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
