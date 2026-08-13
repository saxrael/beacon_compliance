"""Admin Operations API Route (routes_admin.py).

Provides admin provisioning endpoints for creating trustee accounts.
Requires admin secret credential authentication.
"""

import hashlib 
import hmac 
import os 
import secrets 

from backend .src .api .dependencies import get_d1_db 
from backend .src .db .d1_client import D1DatabaseClient 
from fastapi import APIRouter ,Depends ,Header ,HTTPException ,status 
from pydantic import BaseModel 

router =APIRouter (prefix ="/api/admin",tags =["Admin"])


class ProvisionTrusteeRequest (BaseModel ):
    email :str 
    name :str 
    role :str 


class ProvisionTrusteeResponse (BaseModel ):
    user_id :str 
    email :str 
    name :str 
    role :str 
    temp_password :str 


@router .post ("/provision-trustee",response_model =ProvisionTrusteeResponse )
async def provision_trustee_endpoint (
req :ProvisionTrusteeRequest ,
x_admin_secret :str =Header (...,alias ="X-Admin-Secret"),
db :D1DatabaseClient =Depends (get_d1_db ),
)->ProvisionTrusteeResponse :
    expected_secret =os .environ .get ("ADMIN_PROVISION_SECRET","beacon_admin_secret_key_2026")
    if x_admin_secret !=expected_secret :
        raise HTTPException (
        status_code =status .HTTP_401_UNAUTHORIZED ,
        detail ="Invalid admin provisioning secret.",
        )

    role =req .role .title ()
    if role not in ("Chair","Secretary","Treasurer","Trustee","Admin","Developer"):
        raise HTTPException (
        status_code =status .HTTP_400_BAD_REQUEST ,
        detail =f"Invalid role '{req .role }'. Must be Chair, Secretary, Treasurer, Trustee, Admin, or Developer.",
        )

    user_id =f"usr_{secrets .token_hex (6 )}"
    temp_password =f"Temp_{secrets .token_urlsafe (8 )}!"
    salt =os .environ .get ("TRUSTEE_SIGNATURE_SALT","default_salt_beacon_2026")

    pwd_hash =hmac .new (salt .encode (),f"{temp_password }:{salt }".encode (),hashlib .sha256 ).hexdigest ()

    db .execute (
    "INSERT OR REPLACE INTO users (user_id, email, password_hash, name, role, first_login_complete) "
    "VALUES (?, ?, ?, ?, ?, 0)",
    (user_id ,req .email ,pwd_hash ,req .name ,role ),
    )

    return ProvisionTrusteeResponse (
    user_id =user_id ,
    email =req .email ,
    name =req .name ,
    role =role ,
    temp_password =temp_password ,
    )
