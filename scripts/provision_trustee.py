"""Admin Trustee Provisioning CLI Script (provision_trustee.py).

Provision trustee accounts (Chair, Secretary, Treasurer) in Cloudflare D1 database.
Generates single-use temporary password and records user record with first_login_complete = 0.

Usage:
    python scripts/provision_trustee.py --email chair@pottershouse.org.uk --name "Israel (Chair)" --role Chair
"""

import argparse
import hashlib
import os
import secrets
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt."""
    salt = os.environ.get("TRUSTEE_SIGNATURE_SALT", "default_salt_beacon_2026")
    return hashlib.sha256(f"{password }:{salt }".encode()).hexdigest()


def provision_trustee(
    email: str, name: str, role: str, db_path: str | None = None
) -> dict[str, str]:
    """Provision a new trustee account in Cloudflare D1 database."""
    from backend.src.db.d1_client import D1DatabaseClient

    normalized_role = role.title()
    if normalized_role not in ("Chair", "Secretary", "Treasurer", "Trustee", "Admin", "Developer"):
        raise ValueError(
            f"Invalid role '{role }'. Must be Chair, Secretary, Treasurer, Trustee, Admin, or Developer."
        )

    if not db_path:
        db_path = os.environ.get("D1_DB_PATH", str(PROJECT_ROOT / "beacon_compliance.db"))

    db = D1DatabaseClient(db_path=db_path)

    user_id = f"usr_{secrets .token_hex (6 )}"
    temp_password = f"Temp_{secrets .token_urlsafe (8 )}!"
    pwd_hash = hash_password(temp_password)

    db.execute(
        "INSERT OR REPLACE INTO users (user_id, email, password_hash, name, role, first_login_complete) "
        "VALUES (?, ?, ?, ?, ?, 0)",
        (user_id, email, pwd_hash, name, normalized_role),
    )

    return {
        "user_id": user_id,
        "email": email,
        "name": name,
        "role": normalized_role,
        "temp_password": temp_password,
        "db_path": db_path,
    }


def main():
    parser = argparse.ArgumentParser(description="Beacon Compliance — Provision Trustee Account")
    parser.add_argument("--email", required=True, help="Trustee email address")
    parser.add_argument("--name", required=True, help="Trustee full name")
    parser.add_argument(
        "--role",
        required=True,
        choices=["Chair", "Secretary", "Treasurer", "Trustee", "Admin", "Developer"],
        help="Trustee executive or admin role",
    )
    parser.add_argument("--db", required=False, help="Optional D1 SQLite database file path")

    args = parser.parse_args()

    try:
        res = provision_trustee(email=args.email, name=args.name, role=args.role, db_path=args.db)
        print("=" * 60)
        print("Beacon Compliance OS — Trustee Account Provisioned")
        print("=" * 60)
        print(f"User ID:        {res ['user_id']}")
        print(f"Name:           {res ['name']}")
        print(f"Email:          {res ['email']}")
        print(f"Role:           {res ['role']}")
        print(f"Database:       {res ['db_path']}")
        print("-" * 60)
        print(f"Temporary Password:  {res ['temp_password']}")
        print("-" * 60)
        print("IMPORTANT: Share this temporary password with the trustee OUT-OF-BAND.")
        print("The trustee will be forced to change password on first login.")
        print("=" * 60)
    except Exception as err:
        print(f"[ERROR] Provisioning failed: {err }")
        sys.exit(1)


if __name__ == "__main__":
    main()
