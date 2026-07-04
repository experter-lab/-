#!/usr/bin/env python3
"""Generate a patient_web bed URL token.

The token matches medicine_web_dashboard.patient_http:
  v1.<expires_unix>.<hmac_sha256(secret, "bed:expires")>
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import os
import time


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def make_token(secret: str, bed: str, ttl_sec: int) -> str:
    expires = int(time.time() + max(60, int(ttl_sec)))
    msg = f"{bed.strip()}:{expires}".encode("utf-8")
    digest = hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).digest()
    return f"v1.{expires}.{_b64url(digest)}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate patient_web bed token URL")
    parser.add_argument("--bed", required=True, help="Bed number, for example A-01")
    parser.add_argument(
        "--secret",
        default=os.environ.get("MEDICINE_PATIENT_ACCESS_SECRET", ""),
        help="Shared secret. Defaults to MEDICINE_PATIENT_ACCESS_SECRET.",
    )
    parser.add_argument("--host", default="192.168.31.125")
    parser.add_argument("--port", type=int, default=8081)
    parser.add_argument("--ttl-sec", type=int, default=30 * 86400)
    args = parser.parse_args()

    if not args.secret:
        raise SystemExit(
            "Missing secret. Set MEDICINE_PATIENT_ACCESS_SECRET or pass --secret."
        )

    token = make_token(args.secret, args.bed, args.ttl_sec)
    print(token)
    print(f"http://{args.host}:{args.port}/patient/?bed={args.bed}&t={token}")


if __name__ == "__main__":
    main()
