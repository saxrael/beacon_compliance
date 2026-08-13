"""Cloudflare R2 Object Storage Manager for Beacon Compliance (r2_client.py).

Enforces AES-256-GCM encryption at rest for raw and scrubbed document artifacts.
Supports S3 API integration via boto3 when credentials are provided in production,
falling back to in-memory storage for unit tests and local development.
"""

import os 
from typing import NamedTuple 

from backend .src .core .crypto import AESGCMCipher 

try :
    import boto3 

    HAS_BOTO3 =True 
except ImportError :
    HAS_BOTO3 =False 


class R2ObjectMetadata (NamedTuple ):
    """Container for object metadata stored in R2."""

    object_key :str 
    content_type :str 
    original_size_bytes :int 
    encrypted_size_bytes :int 


class R2StorageClient :
    """Cloudflare R2 Client with AES-256-GCM encryption layer and optional S3 API backend."""

    def __init__ (self ,master_key :bytes |None =None )->None :
        if master_key is None :
            env_secret =os .environ .get ("AES_256_GCM_SECRET")
            if env_secret :
                master_key =env_secret .encode ("utf-8")[:32 ].ljust (32 ,b"\0")

        self .cipher =AESGCMCipher (key =master_key )
        self ._storage_store :dict [str ,tuple [bytes ,bytes ]]={}

        self .account_id =os .environ .get ("CLOUDFLARE_ACCOUNT_ID")
        self .bucket_name =os .environ .get ("CLOUDFLARE_R2_BUCKET_NAME","beacon-compliance-r2-prod")
        self .access_key =os .environ .get ("R2_ACCESS_KEY_ID")
        self .secret_key =os .environ .get ("R2_SECRET_ACCESS_KEY")

        self .use_s3_api =bool (
        HAS_BOTO3 and self .account_id and self .access_key and self .secret_key 
        )

        if self .use_s3_api :
            endpoint_url =f"https://{self .account_id }.r2.cloudflarestorage.com"
            self .s3_client =boto3 .client (
            "s3",
            endpoint_url =endpoint_url ,
            aws_access_key_id =self .access_key ,
            aws_secret_access_key =self .secret_key ,
            region_name ="auto",
            )
        else :
            self .s3_client =None 

    def put_object (self ,object_key :str ,data :bytes )->R2ObjectMetadata :
        """Encrypt and store an object binary in R2 storage."""
        if not object_key :
            raise ValueError ("object_key cannot be empty.")

        nonce ,ciphertext =self .cipher .encrypt (data )

        if self .use_s3_api and self .s3_client :
            payload =nonce +ciphertext 
            self .s3_client .put_object (
            Bucket =self .bucket_name ,
            Key =object_key ,
            Body =payload ,
            ContentType ="application/octet-stream",
            )
        else :
            self ._storage_store [object_key ]=(nonce ,ciphertext )

        return R2ObjectMetadata (
        object_key =object_key ,
        content_type ="application/octet-stream",
        original_size_bytes =len (data ),
        encrypted_size_bytes =len (ciphertext ),
        )

    def get_object (self ,object_key :str )->bytes :
        """Retrieve and decrypt an object binary from R2 storage."""
        if self .use_s3_api and self .s3_client :
            res =self .s3_client .get_object (Bucket =self .bucket_name ,Key =object_key )
            payload =res ["Body"].read ()
            nonce ,ciphertext =payload [:12 ],payload [12 :]
            return self .cipher .decrypt (nonce ,ciphertext )

        if object_key not in self ._storage_store :
            raise KeyError (f"Object key '{object_key }' not found in R2 storage.")

        nonce ,ciphertext =self ._storage_store [object_key ]
        return self .cipher .decrypt (nonce ,ciphertext )

    def delete_object (self ,object_key :str )->bool :
        """Delete an object from R2 storage."""
        if self .use_s3_api and self .s3_client :
            self .s3_client .delete_object (Bucket =self .bucket_name ,Key =object_key )
            return True 

        if object_key in self ._storage_store :
            del self ._storage_store [object_key ]
            return True 
        return False 
