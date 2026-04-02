"""Generate OpenAPI spec JSON from the FastAPI app."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from app import create_app

app = create_app()
spec = app.openapi()

out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("openapi.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(spec, indent=2, ensure_ascii=False))
print(f"OpenAPI spec written to {out}")
