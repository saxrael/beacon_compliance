"""FastAPI Service Dependency Providers for Beacon Compliance (dependencies.py).

Provides singleton and request-scoped dependency providers for D1DatabaseClient,
R2StorageClient, and ComplianceChatAgent.
"""

import os 
from collections .abc import Generator 

from backend .src .agents .chat_agent import ComplianceChatAgent 
from backend .src .db .d1_client import D1DatabaseClient 
from backend .src .db .r2_client import R2StorageClient 
from backend .src .db .repository import ComplianceRepository 

_d1_instance :D1DatabaseClient |None =None 
_r2_instance :R2StorageClient |None =None 
_chat_agent_instance :ComplianceChatAgent |None =None 
_repository_instance :ComplianceRepository |None =None 


def get_d1_db ()->Generator [D1DatabaseClient ,None ,None ]:
    """Dependency provider for Cloudflare D1 Database Client."""
    global _d1_instance 
    db_path =os .environ .get ("D1_DB_PATH",":memory:")
    if _d1_instance is None or getattr (_d1_instance ,"db_path",None )!=db_path :
        _d1_instance =D1DatabaseClient (db_path =db_path )
    yield _d1_instance 


def get_r2_storage ()->R2StorageClient :
    """Dependency provider for Cloudflare R2 Object Storage Client."""
    global _r2_instance 
    if _r2_instance is None :
        _r2_instance =R2StorageClient ()
    return _r2_instance 


def get_repository ()->Generator [ComplianceRepository ,None ,None ]:
    """Dependency provider for ComplianceRepository facade."""
    global _repository_instance ,_d1_instance ,_r2_instance 
    db_path =os .environ .get ("D1_DB_PATH",":memory:")
    if _d1_instance is None or getattr (_d1_instance ,"db_path",None )!=db_path :
        _d1_instance =D1DatabaseClient (db_path =db_path )
    if _r2_instance is None :
        _r2_instance =R2StorageClient ()
    _repository_instance =ComplianceRepository (db_client =_d1_instance ,r2_client =_r2_instance )
    yield _repository_instance 


def get_chat_agent ()->ComplianceChatAgent :
    """Dependency provider for Compliance Chat Agent."""
    global _chat_agent_instance 
    if _chat_agent_instance is None :
        _chat_agent_instance =ComplianceChatAgent ()
    return _chat_agent_instance 
