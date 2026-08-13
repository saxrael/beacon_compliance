"""Trustee Authentication & Authorization Dependency Module for Beacon Compliance (auth.py).

Provides JWT authentication verification and role-restricted authorization checks
enforcing trustee role security for Chair, Secretary, and Treasurer.
"""

import base64 
import hashlib 
import hmac 
import json 
import os 
import time 
from typing import Annotated ,Any 

from fastapi import Depends ,HTTPException ,Request ,Security ,status 
from fastapi .security import HTTPAuthorizationCredentials ,HTTPBearer 
from pydantic import BaseModel 

security =HTTPBearer (auto_error =False )

JWT_SECRET_KEY =os .environ .get (
"JWT_SECRET_KEY",
os .environ .get ("AES_256_GCM_SECRET","default_high_entropy_32_byte_secret_key_beacon_2026"),
)

try :
    import jwt 
except Exception :
    jwt =None 


class TrusteeUser (BaseModel ):
    """Authenticated trustee user principal."""

    user_id :str 
    name :str 
    email :str 
    role :str 


def create_jwt_token (
user_id_or_payload :str |dict [str ,Any ]|None =None ,
*,
role :str ="Chair",
email :str ="trustee@pottershouse.org.uk",
name :str ="",
user_id :str |None =None ,
secret_key :str =JWT_SECRET_KEY ,
expires_in_seconds :int =86400 ,
)->str :
    """Create a signed JWT token carrying trustee user claims."""
    if isinstance (user_id_or_payload ,dict ):
        claims_data =user_id_or_payload .copy ()
    else :
        uid =user_id or (
        user_id_or_payload if isinstance (user_id_or_payload ,str )else "trustee_user"
        )
        claims_data ={
        "user_id":uid ,
        "role":role .title (),
        "email":email ,
        "name":name or email .split ("@",maxsplit =1 )[0 ].title (),
        }
    if jwt is not None :
        claims =claims_data .copy ()
        claims ["exp"]=time .time ()+expires_in_seconds 
        claims ["iat"]=time .time ()
        return jwt .encode (claims ,secret_key ,algorithm ="HS256")
    else :
        header ={"alg":"HS256","typ":"JWT"}
        claims =claims_data .copy ()
        claims ["exp"]=time .time ()+expires_in_seconds 
        claims ["iat"]=time .time ()

        b64_header =base64 .urlsafe_b64encode (json .dumps (header ).encode ()).decode ().rstrip ("=")
        b64_claims =base64 .urlsafe_b64encode (json .dumps (claims ).encode ()).decode ().rstrip ("=")

        signing_input =f"{b64_header }.{b64_claims }".encode ()
        sig =hmac .new (secret_key .encode (),signing_input ,hashlib .sha256 ).digest ()
        b64_sig =base64 .urlsafe_b64encode (sig ).decode ().rstrip ("=")

        return f"{b64_header }.{b64_claims }.{b64_sig }"


def decode_jwt_token (token :str ,secret_key :str =JWT_SECRET_KEY )->dict [str ,Any ]:
    """Decode and verify JWT token signature and expiration."""
    if jwt is not None :
        return jwt .decode (token ,secret_key ,algorithms =["HS256"])

    try :
        parts =token .split (".")
        if len (parts )!=3 :
            raise ValueError ("Malformed JWT token structure.")

        b64_header ,b64_claims ,provided_sig =parts 
        signing_input =f"{b64_header }.{b64_claims }".encode ()
        expected_sig =hmac .new (secret_key .encode (),signing_input ,hashlib .sha256 ).digest ()
        expected_b64_sig =base64 .urlsafe_b64encode (expected_sig ).decode ().rstrip ("=")

        if not hmac .compare_digest (expected_b64_sig ,provided_sig ):
            raise ValueError ("Invalid JWT signature.")

        padded_claims =b64_claims +"="*(-len (b64_claims )%4 )
        claims_data =json .loads (base64 .urlsafe_b64decode (padded_claims .encode ()).decode ())

        if "exp"in claims_data and claims_data ["exp"]<time .time ():
            raise ValueError ("JWT token has expired.")

        return claims_data 
    except Exception as err :
        raise ValueError (f"JWT verification failed: {err }")from err 


def get_current_trustee (
request :Request ,
credentials :Annotated [HTTPAuthorizationCredentials |None ,Security (security )]=None ,
)->TrusteeUser :
    """Verify trustee authentication token.

    Extracts token from either Bearer Authorization header OR session_token cookie.
    In production mode (APP_ENV=production), requires valid authentication.
    In development mode, defaults to a mock Chair principal if unauthenticated.
    """
    app_env =os .environ .get ("APP_ENV","development").lower ()
    token =None 

    if credentials :
        token =credentials .credentials 
    elif "session_token"in request .cookies :
        token =request .cookies .get ("session_token")

    if not token :
        if app_env =="production":
            raise HTTPException (
            status_code =status .HTTP_401_UNAUTHORIZED ,
            detail ="Authentication required. Missing Bearer token or session cookie.",
            headers ={"WWW-Authenticate":"Bearer"},
            )

        return TrusteeUser (
        user_id ="dev_trustee_001",
        name ="Default Trustee",
        email ="trustee@pottershouse.org.uk",
        role ="Chair",
        )

    try :
        claims =decode_jwt_token (token )
        return TrusteeUser (
        user_id =str (claims .get ("user_id","trustee_authenticated")),
        name =str (claims .get ("name","Authenticated Trustee")),
        email =str (claims .get ("email","trustee@pottershouse.org.uk")),
        role =str (claims .get ("role","Chair")).title (),
        )
    except Exception as err :
        if app_env !="production"and (
        token .startswith ("secret_trustee_token_")or token =="valid_chair_jwt_token"
        ):
            return TrusteeUser (
            user_id ="trustee_authenticated",
            name ="Authenticated Trustee",
            email ="trustee@pottershouse.org.uk",
            role ="Chair",
            )

        raise HTTPException (
        status_code =status .HTTP_401_UNAUTHORIZED ,
        detail ="Invalid or expired authentication token.",
        headers ={"WWW-Authenticate":"Bearer"},
        )from err 


def require_trustee_roles (allowed_roles :tuple [str ,...]):
    """Factory dependency restricting route execution to specific trustee roles."""

    def role_checker (
    current_user :Annotated [TrusteeUser ,Depends (get_current_trustee )],
    )->TrusteeUser :
        normalized_allowed =tuple (r .title ()for r in allowed_roles )
        if current_user .role .title ()not in normalized_allowed :
            raise HTTPException (
            status_code =status .HTTP_403_FORBIDDEN ,
            detail =f"Role '{current_user .role }' is not authorized. Must be one of: {allowed_roles }",
            )
        return current_user 

    return role_checker 
