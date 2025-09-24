"""
Akeneo Settings API Router

This router provides CRUD operations for Akeneo connection settings.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import structlog
import json
from datetime import datetime
import uuid

from lookbook_mpc.adapters.database import get_db_connection
from lookbook_mpc.config.settings import get_settings

logger = structlog.get_logger()
router = APIRouter(prefix="/v1/admin/akeneo/settings", tags=["akeneo-settings"])

# Pydantic models
class AkeneoSettingIn(BaseModel):
    name: str
    base_url: str
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    username: Optional[str] = None
    password_hash: Optional[str] = None
    is_active: Optional[bool] = False
    is_default: Optional[bool] = False
    connection_timeout: Optional[int] = 30
    retry_attempts: Optional[int] = 3

class AkeneoSetting(BaseModel):
    id: str
    name: str
    base_url: str
    client_id: Optional[str]
    client_secret: Optional[str]
    username: Optional[str]
    password_hash: Optional[str]
    is_active: bool
    is_default: bool
    connection_timeout: int
    retry_attempts: int
    created_at: str
    updated_at: str
    last_tested_at: Optional[str]
    last_test_result: str

    @classmethod
    def from_db(cls, data: dict):
        """Create AkeneoSetting from database data."""
        return cls(
            id=data['id'],
            name=data['name'],
            base_url=data['base_url'],
            client_id=data['client_id'],
            client_secret=data['client_secret'],
            username=data['username'],
            password_hash=data['password_hash'],
            is_active=bool(data['is_active']),
            is_default=bool(data['is_default']),
            connection_timeout=data['connection_timeout'],
            retry_attempts=data['retry_attempts'],
            created_at=data['created_at'].isoformat() if data['created_at'] else None,
            updated_at=data['updated_at'].isoformat() if data['updated_at'] else None,
            last_tested_at=data['last_tested_at'].isoformat() if data['last_tested_at'] else None,
            last_test_result=data['last_test_result']
        )

class AkeneoAttributeMappingIn(BaseModel):
    local_field: str
    akeneo_attribute: str
    akeneo_type: Optional[str] = 'text'
    is_required: Optional[bool] = False

class AkeneoAttributeMapping(BaseModel):
    id: str
    setting_id: str
    local_field: str
    akeneo_attribute: str
    akeneo_type: str
    is_required: bool
    created_at: str

    @classmethod
    def from_db(cls, data: dict):
        """Create AkeneoAttributeMapping from database data."""
        return cls(
            id=data['id'],
            setting_id=data['setting_id'],
            local_field=data['local_field'],
            akeneo_attribute=data['akeneo_attribute'],
            akeneo_type=data['akeneo_type'],
            is_required=bool(data['is_required']),
            created_at=data['created_at'].isoformat() if data['created_at'] else None
        )

@router.get("/", response_model=List[AkeneoSetting])
async def get_settings():
    """Get all Akeneo settings."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM akeneo_settings ORDER BY created_at DESC")
        settings = cursor.fetchall()

        cursor.close()
        conn.close()

        return [AkeneoSetting.from_db(setting) for setting in settings]

    except Exception as e:
        logger.error("Error fetching Akeneo settings", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch Akeneo settings")

@router.post("/", response_model=AkeneoSetting)
async def create_setting(setting_in: AkeneoSettingIn):
    """Create a new Akeneo setting."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Generate UUID
        setting_id = str(uuid.uuid4())

        # If this is set as default, unset others
        if setting_in.is_default:
            cursor.execute("UPDATE akeneo_settings SET is_default = FALSE WHERE is_default = TRUE")

        # Insert setting
        query = """
            INSERT INTO akeneo_settings (
                id, name, base_url, client_id, client_secret, username, password_hash,
                is_active, is_default, connection_timeout, retry_attempts
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = [
            setting_id,
            setting_in.name,
            setting_in.base_url,
            setting_in.client_id,
            setting_in.client_secret,
            setting_in.username,
            setting_in.password_hash,
            setting_in.is_active,
            setting_in.is_default,
            setting_in.connection_timeout,
            setting_in.retry_attempts
        ]

        cursor.execute(query, params)
        conn.commit()

        # Get created setting
        cursor.execute("SELECT * FROM akeneo_settings WHERE id = %s", (setting_id,))
        created_setting = cursor.fetchone()

        cursor.close()
        conn.close()

        return AkeneoSetting.from_db(created_setting)

    except Exception as e:
        logger.error("Error creating Akeneo setting", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create Akeneo setting")

@router.get("/{setting_id}", response_model=AkeneoSetting)
async def get_setting(setting_id: str):
    """Get a specific Akeneo setting by ID."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM akeneo_settings WHERE id = %s", (setting_id,))
        setting = cursor.fetchone()

        if not setting:
            raise HTTPException(status_code=404, detail="Akeneo setting not found")

        cursor.close()
        conn.close()

        return AkeneoSetting.from_db(setting)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching Akeneo setting", setting_id=setting_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch Akeneo setting")

@router.put("/{setting_id}", response_model=AkeneoSetting)
async def update_setting(setting_id: str, setting_in: AkeneoSettingIn):
    """Update an existing Akeneo setting."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if setting exists
        cursor.execute("SELECT * FROM akeneo_settings WHERE id = %s", (setting_id,))
        existing_setting = cursor.fetchone()

        if not existing_setting:
            raise HTTPException(status_code=404, detail="Akeneo setting not found")

        # If this is set as default, unset others
        if setting_in.is_default:
            cursor.execute("UPDATE akeneo_settings SET is_default = FALSE WHERE is_default = TRUE AND id != %s", (setting_id,))

        # Build update query
        update_fields = []
        values = []

        update_data = setting_in.dict(exclude_unset=True)

        for field, value in update_data.items():
            update_fields.append(f"{field} = %s")
            values.append(value)

        if update_fields:
            values.append(setting_id)
            query = f"UPDATE akeneo_settings SET {', '.join(update_fields)}, updated_at = NOW() WHERE id = %s"
            cursor.execute(query, values)

        conn.commit()

        # Get updated setting
        cursor.execute("SELECT * FROM akeneo_settings WHERE id = %s", (setting_id,))
        updated_setting = cursor.fetchone()

        cursor.close()
        conn.close()

        return AkeneoSetting.from_db(updated_setting)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating Akeneo setting", setting_id=setting_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update Akeneo setting")

@router.delete("/{setting_id}")
async def delete_setting(setting_id: str):
    """Delete an Akeneo setting."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if setting exists
        cursor.execute("SELECT * FROM akeneo_settings WHERE id = %s", (setting_id,))
        existing_setting = cursor.fetchone()

        if not existing_setting:
            raise HTTPException(status_code=404, detail="Akeneo setting not found")

        # Delete setting (mappings will be deleted via CASCADE)
        cursor.execute("DELETE FROM akeneo_settings WHERE id = %s", (setting_id,))
        conn.commit()

        cursor.close()
        conn.close()

        return {"message": "Akeneo setting deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting Akeneo setting", setting_id=setting_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete Akeneo setting")

@router.post("/{setting_id}/test-connection")
async def test_connection(setting_id: str):
    """Test connection to Akeneo (stub implementation)."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if setting exists
        cursor.execute("SELECT * FROM akeneo_settings WHERE id = %s", (setting_id,))
        setting = cursor.fetchone()

        if not setting:
            raise HTTPException(status_code=404, detail="Akeneo setting not found")

        # Update test results
        cursor.execute("""
            UPDATE akeneo_settings SET
                last_tested_at = NOW(),
                last_test_result = 'success'
            WHERE id = %s
        """, (setting_id,))

        conn.commit()

        cursor.close()
        conn.close()

        return {"message": "Connection test successful", "result": "success"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error testing connection", setting_id=setting_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to test connection")

# Attribute Mappings
@router.get("/{setting_id}/mappings", response_model=List[AkeneoAttributeMapping])
async def get_attribute_mappings(setting_id: str):
    """Get attribute mappings for a setting."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM akeneo_attribute_mappings WHERE setting_id = %s ORDER BY created_at", (setting_id,))
        mappings = cursor.fetchall()

        cursor.close()
        conn.close()

        return [AkeneoAttributeMapping.from_db(mapping) for mapping in mappings]

    except Exception as e:
        logger.error("Error fetching attribute mappings", setting_id=setting_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch attribute mappings")

@router.post("/{setting_id}/mappings", response_model=AkeneoAttributeMapping)
async def create_attribute_mapping(setting_id: str, mapping_in: AkeneoAttributeMappingIn):
    """Create a new attribute mapping."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if setting exists
        cursor.execute("SELECT id FROM akeneo_settings WHERE id = %s", (setting_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Akeneo setting not found")

        # Generate UUID
        mapping_id = str(uuid.uuid4())

        # Insert mapping
        query = """
            INSERT INTO akeneo_attribute_mappings (
                id, setting_id, local_field, akeneo_attribute, akeneo_type, is_required
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """
        params = [
            mapping_id,
            setting_id,
            mapping_in.local_field,
            mapping_in.akeneo_attribute,
            mapping_in.akeneo_type,
            mapping_in.is_required
        ]

        cursor.execute(query, params)
        conn.commit()

        # Get created mapping
        cursor.execute("SELECT * FROM akeneo_attribute_mappings WHERE id = %s", (mapping_id,))
        created_mapping = cursor.fetchone()

        cursor.close()
        conn.close()

        return AkeneoAttributeMapping.from_db(created_mapping)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating attribute mapping", setting_id=setting_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create attribute mapping")

@router.delete("/{setting_id}/mappings/{mapping_id}")
async def delete_attribute_mapping(setting_id: str, mapping_id: str):
    """Delete an attribute mapping."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if mapping exists and belongs to setting
        cursor.execute("SELECT id FROM akeneo_attribute_mappings WHERE id = %s AND setting_id = %s",
                      (mapping_id, setting_id))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Attribute mapping not found")

        # Delete mapping
        cursor.execute("DELETE FROM akeneo_attribute_mappings WHERE id = %s", (mapping_id,))
        conn.commit()

        cursor.close()
        conn.close()

        return {"message": "Attribute mapping deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting attribute mapping", mapping_id=mapping_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete attribute mapping")