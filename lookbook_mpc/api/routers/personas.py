"""
Persona Management API Router

This router provides CRUD operations for AI agent personas.
"""

import uuid
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, validator
import structlog
import json
from datetime import datetime

from lookbook_mpc.adapters.database import get_db_connection
from lookbook_mpc.config.settings import get_settings

logger = structlog.get_logger()
router = APIRouter(prefix="/v1/personas", tags=["personas"])

# Pydantic models
class PersonaAttributes(BaseModel):
    core_style: str
    framing: str
    motivational_drivers: str
    emotional_register: str
    interpersonal_stance: str
    rhetorical_techniques: str
    risk_posture: str
    objection_handling: str
    practical_cues: str
    deployment_rules: str

    @validator('*')
    def validate_length(cls, v):
        if len(v.strip()) < 10:
            raise ValueError('Attribute must be at least 10 characters long')
        if len(v) > 240:
            raise ValueError('Attribute must be at most 240 characters long')
        return v.strip()

class PersonaCreate(BaseModel):
    name: str
    preset_name: Optional[str] = None
    attributes: PersonaAttributes
    notes: Optional[str] = ""
    verbosity: int = 1
    decisiveness: int = 1

    @validator('name')
    def validate_name(cls, v):
        if len(v.strip()) < 1:
            raise ValueError('Name cannot be empty')
        if len(v) > 100:
            raise ValueError('Name must be at most 100 characters long')
        return v.strip()

    @validator('notes')
    def validate_notes(cls, v):
        if len(v) > 2000:
            raise ValueError('Notes must be at most 2000 characters long')
        return v

    @validator('verbosity', 'decisiveness')
    def validate_range(cls, v):
        if v not in [0, 1, 2]:
            raise ValueError('Value must be 0, 1, or 2')
        return v

class PersonaUpdate(BaseModel):
    name: Optional[str] = None
    preset_name: Optional[str] = None
    attributes: Optional[PersonaAttributes] = None
    notes: Optional[str] = None
    verbosity: Optional[int] = None
    decisiveness: Optional[int] = None

    @validator('name')
    def validate_name(cls, v):
        if v is not None:
            if len(v.strip()) < 1:
                raise ValueError('Name cannot be empty')
            if len(v) > 100:
                raise ValueError('Name must be at most 100 characters long')
            return v.strip()
        return v

    @validator('notes')
    def validate_notes(cls, v):
        if v is not None and len(v) > 2000:
            raise ValueError('Notes must be at most 2000 characters long')
        return v

    @validator('verbosity', 'decisiveness')
    def validate_range(cls, v):
        if v is not None and v not in [0, 1, 2]:
            raise ValueError('Value must be 0, 1, or 2')
        return v

class PersonaResponse(BaseModel):
    id: str
    name: str
    preset_name: Optional[str]
    attributes: Dict[str, Any]
    notes: str
    verbosity: int
    decisiveness: int
    created_at: str
    updated_at: str

    @classmethod
    def from_db(cls, persona_data: dict):
        """Create PersonaResponse from database data, converting datetime to string."""
        return cls(
            id=persona_data['id'],
            name=persona_data['name'],
            preset_name=persona_data['preset_name'],
            attributes=persona_data['attributes'] if isinstance(persona_data['attributes'], dict) else json.loads(persona_data['attributes']),
            notes=persona_data['notes'] or "",
            verbosity=persona_data['verbosity'],
            decisiveness=persona_data['decisiveness'],
            created_at=persona_data['created_at'].isoformat() if persona_data['created_at'] else None,
            updated_at=persona_data['updated_at'].isoformat() if persona_data['updated_at'] else None
        )

class PersonaSummary(BaseModel):
    id: str
    name: str
    preset_name: Optional[str]
    updated_at: str

class ApplyPresetRequest(BaseModel):
    preset_name: str

    @validator('preset_name')
    def validate_preset(cls, v):
        valid_presets = ['obama_like', 'kennedy_like', 'friendly_stylist']
        if v not in valid_presets:
            raise ValueError(f'Invalid preset name. Valid presets: {", ".join(valid_presets)}')
        return v

class PreviewRequest(BaseModel):
    prompt: Optional[str] = None

class PreviewResponse(BaseModel):
    sample: str
    prompt: str
    persona_name: str
    preset_name: Optional[str]
    verbosity: int
    decisiveness: int

@router.get("/", response_model=List[PersonaSummary])
async def get_personas(summary: bool = True):
    """Get all personas, optionally as summary."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id, name, preset_name, updated_at FROM personas ORDER BY updated_at DESC")
        personas = cursor.fetchall()

        cursor.close()
        conn.close()

        return [PersonaSummary(
            id=p['id'],
            name=p['name'],
            preset_name=p['preset_name'],
            updated_at=p['updated_at'].isoformat() if p['updated_at'] else None
        ) for p in personas]

    except Exception as e:
        logger.error("Error fetching personas", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch personas")

@router.post("/", response_model=PersonaResponse)
async def create_persona(persona_create: PersonaCreate):
    """Create a new persona."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if name already exists
        cursor.execute("SELECT id FROM personas WHERE name = %s", (persona_create.name,))
        existing = cursor.fetchone()
        if existing:
            raise HTTPException(status_code=400, detail="Persona name already exists")

        persona_id = str(uuid.uuid4())

        # Insert persona
        cursor.execute("""
            INSERT INTO personas
            (id, name, preset_name, attributes, notes, verbosity, decisiveness)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            persona_id,
            persona_create.name,
            persona_create.preset_name,
            json.dumps(persona_create.attributes.dict()),
            persona_create.notes,
            persona_create.verbosity,
            persona_create.decisiveness
        ))

        # Get created persona
        cursor.execute("SELECT * FROM personas WHERE id = %s", (persona_id,))
        created_persona = cursor.fetchone()

        cursor.close()
        conn.close()

        return PersonaResponse.from_db(created_persona)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating persona", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create persona")

@router.get("/{persona_id}", response_model=PersonaResponse)
async def get_persona(persona_id: str):
    """Get a specific persona by ID."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM personas WHERE id = %s", (persona_id,))
        persona = cursor.fetchone()

        if not persona:
            raise HTTPException(status_code=404, detail="Persona not found")

        cursor.close()
        conn.close()

        return PersonaResponse.from_db(persona)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching persona", persona_id=persona_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch persona")

@router.patch("/{persona_id}", response_model=PersonaResponse)
async def update_persona(persona_id: str, persona_update: PersonaUpdate):
    """Update an existing persona."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if persona exists
        cursor.execute("SELECT * FROM personas WHERE id = %s", (persona_id,))
        existing_persona = cursor.fetchone()

        if not existing_persona:
            raise HTTPException(status_code=404, detail="Persona not found")

        # Check name uniqueness if name is being updated
        if persona_update.name and persona_update.name != existing_persona['name']:
            cursor.execute("SELECT id FROM personas WHERE name = %s AND id != %s", (persona_update.name, persona_id))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Persona name already exists")

        # Build update query
        update_fields = []
        values = []

        for field, value in persona_update.dict(exclude_unset=True).items():
            if value is not None:
                if field == 'attributes':
                    update_fields.append("attributes = %s")
                    values.append(json.dumps(value.dict()))
                else:
                    update_fields.append(f"{field} = %s")
                    values.append(value)

        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")

        values.append(persona_id)

        query = f"UPDATE personas SET {', '.join(update_fields)} WHERE id = %s"
        cursor.execute(query, values)

        # Get updated persona
        cursor.execute("SELECT * FROM personas WHERE id = %s", (persona_id,))
        updated_persona = cursor.fetchone()

        cursor.close()
        conn.close()

        return PersonaResponse.from_db(updated_persona)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating persona", persona_id=persona_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update persona")

@router.delete("/{persona_id}")
async def delete_persona(persona_id: str):
    """Delete a persona."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if persona exists
        cursor.execute("SELECT * FROM personas WHERE id = %s", (persona_id,))
        existing_persona = cursor.fetchone()

        if not existing_persona:
            raise HTTPException(status_code=404, detail="Persona not found")

        # Delete persona
        cursor.execute("DELETE FROM personas WHERE id = %s", (persona_id,))

        conn.commit()
        cursor.close()
        conn.close()

        return {"message": "Persona deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting persona", persona_id=persona_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete persona")

@router.post("/{persona_id}/duplicate", response_model=PersonaResponse)
async def duplicate_persona(persona_id: str, name: str):
    """Duplicate a persona with a new name."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get original persona
        cursor.execute("SELECT * FROM personas WHERE id = %s", (persona_id,))
        original_persona = cursor.fetchone()

        if not original_persona:
            raise HTTPException(status_code=404, detail="Persona not found")

        # Check if name already exists
        cursor.execute("SELECT id FROM personas WHERE name = %s", (name,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Persona name already exists")

        new_id = str(uuid.uuid4())

        # Insert duplicate
        cursor.execute("""
            INSERT INTO personas
            (id, name, preset_name, attributes, notes, verbosity, decisiveness)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            new_id,
            name,
            original_persona['preset_name'],
            original_persona['attributes'],
            original_persona['notes'],
            original_persona['verbosity'],
            original_persona['decisiveness']
        ))

        # Get created persona
        cursor.execute("SELECT * FROM personas WHERE id = %s", (new_id,))
        created_persona = cursor.fetchone()

        cursor.close()
        conn.close()

        return PersonaResponse.from_db(created_persona)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error duplicating persona", persona_id=persona_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to duplicate persona")

@router.post("/{persona_id}/apply_preset", response_model=PersonaResponse)
async def apply_preset(persona_id: str, request: ApplyPresetRequest):
    """Apply a preset template to an existing persona."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if persona exists
        cursor.execute("SELECT * FROM personas WHERE id = %s", (persona_id,))
        existing_persona = cursor.fetchone()

        if not existing_persona:
            raise HTTPException(status_code=404, detail="Persona not found")

        # Define preset templates
        presets = {
            'obama_like': {
                'attributes': {
                    'core_style': 'Reflective, inclusive, narrative; careful qualifiers.',
                    'framing': 'Acknowledge trade-offs; propose balanced options and shared path forward.',
                    'motivational_drivers': 'Hope, fairness, shared responsibility; long-term benefits.',
                    'emotional_register': 'Calm, reassuring, occasionally wry.',
                    'interpersonal_stance': 'Active listening; paraphrase and validate before advising.',
                    'rhetorical_techniques': 'Story, parallelism, context; cite sources when relevant.',
                    'risk_posture': 'Incremental; stress-test assumptions; phase plans.',
                    'objection_handling': 'Empathetic reframing and principled compromise.',
                    'practical_cues': 'Ask 1–2 clarifying questions; provide 2–3 options with trade-offs.',
                    'deployment_rules': 'Use in complex, ambiguous, multi-stakeholder scenarios.'
                },
                'notes': 'Use "we" language and emphasize civic duty; avoid overclaiming.',
                'verbosity': 2,
                'decisiveness': 1
            },
            'kennedy_like': {
                'attributes': {
                    'core_style': 'Crisp, imperative, quotable.',
                    'framing': 'Mission, deadline, first step.',
                    'motivational_drivers': 'Courage, excellence, pride in hard goals.',
                    'emotional_register': 'High-energy optimism.',
                    'interpersonal_stance': 'Directive, charismatic; ask for alignment.',
                    'rhetorical_techniques': 'Antithesis, aphorisms, short lines.',
                    'risk_posture': 'Audacious; time-bound commitments.',
                    'objection_handling': 'Recenter mission; convert difficulty into urgency.',
                    'practical_cues': '3-step plan; minimal hedging.',
                    'deployment_rules': 'Launches, turnarounds, momentum building.'
                },
                'notes': 'Prefer short paragraphs; state deadlines and commitments.',
                'verbosity': 1,
                'decisiveness': 2
            },
            'friendly_stylist': {
                'attributes': {
                    'core_style': 'Warm, upbeat, conversational; practical tips.',
                    'framing': 'Occasion-first; budget- and size-aware suggestions.',
                    'motivational_drivers': 'Confidence, comfort, self-expression.',
                    'emotional_register': 'Encouraging, positive, approachable.',
                    'interpersonal_stance': 'Collaborative; invites preferences and feedback.',
                    'rhetorical_techniques': 'Benefit-forward phrasing; simple, vivid language.',
                    'risk_posture': 'Low-risk; suggest affordable alternatives and try-ons.',
                    'objection_handling': 'Offer size/fit workarounds; care instructions; easy returns.',
                    'practical_cues': 'Recommend 3–5 looks; include size notes and swap options.',
                    'deployment_rules': 'Everyday shoppers, gifting assistance, post-purchase styling.'
                },
                'notes': 'Use Thai Baht; include care tips; avoid technical jargon.',
                'verbosity': 2,
                'decisiveness': 1
            }
        }

        preset_data = presets.get(request.preset_name)
        if not preset_data:
            raise HTTPException(status_code=400, detail="Invalid preset name")

        # Update persona with preset data
        cursor.execute("""
            UPDATE personas SET
                preset_name = %s,
                attributes = %s,
                notes = %s,
                verbosity = %s,
                decisiveness = %s
            WHERE id = %s
        """, (
            request.preset_name,
            json.dumps(preset_data['attributes']),
            preset_data['notes'],
            preset_data['verbosity'],
            preset_data['decisiveness'],
            persona_id
        ))

        # Get updated persona
        cursor.execute("SELECT * FROM personas WHERE id = %s", (persona_id,))
        updated_persona = cursor.fetchone()

        cursor.close()
        conn.close()

        return PersonaResponse.from_db(updated_persona)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error applying preset", persona_id=persona_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to apply preset")

@router.post("/{persona_id}/preview", response_model=PreviewResponse)
async def generate_preview(persona_id: str, request: PreviewRequest = None):
    """Generate a preview response based on persona configuration."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get persona
        cursor.execute("SELECT * FROM personas WHERE id = %s", (persona_id,))
        persona = cursor.fetchone()

        if not persona:
            raise HTTPException(status_code=404, detail="Persona not found")

        cursor.close()
        conn.close()

        # Use provided prompt or default
        prompt = request.prompt if request and request.prompt else "I need help choosing an outfit for a summer outdoor event under ฿3000."

        # Simple deterministic response generation based on persona attributes
        attributes = persona['attributes'] if isinstance(persona['attributes'], dict) else json.loads(persona['attributes'])

        # Generate response based on verbosity and decisiveness
        verbosity = persona['verbosity']
        decisiveness = persona['decisiveness']

        # Base response structure
        responses = {
            'obama_like': [
                "That's a great question. I understand what you're looking for. I believe you'll find a comfortable midi dress or linen blend separates will serve you well. This gives you versatility to adjust based on the weather. Let me know if we should explore other directions.",
                "I understand what you're looking for. A comfortable midi dress or linen blend separates would serve you well. This gives you versatility to adjust based on the weather."
            ],
            'kennedy_like': [
                "Absolutely. Go with a crisp blazer with tailored trousers. Make it happen.",
                "Go with a crisp blazer with tailored trousers."
            ],
            'friendly_stylist': [
                "I'd love to help! With your budget and the occasion in mind, I recommend a comfortable midi dress or linen blend separates. This should easily fit within your ฿3,000 budget! Feel free to ask about care instructions or styling tips!",
                "I'd love to help! I recommend a comfortable midi dress or linen blend separates. This should fit within your ฿3,000 budget!"
            ]
        }

        # Get appropriate response based on preset and verbosity
        preset_responses = responses.get(persona['preset_name'] or 'friendly_stylist', responses['friendly_stylist'])
        sample = preset_responses[1] if verbosity == 0 else preset_responses[0]

        return PreviewResponse(
            sample=sample,
            prompt=prompt,
            persona_name=persona['name'],
            preset_name=persona['preset_name'],
            verbosity=verbosity,
            decisiveness=decisiveness
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error generating preview", persona_id=persona_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to generate preview")

@router.get("/{persona_id}/preview", response_model=PreviewResponse)
async def get_preview(persona_id: str):
    """Get preview with default prompt."""
    return await generate_preview(persona_id)