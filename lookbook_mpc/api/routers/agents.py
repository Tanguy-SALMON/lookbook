"""
Agent Management API Router

This router provides CRUD operations for AI agents and their rules.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import structlog
import json
from datetime import datetime

from lookbook_mpc.adapters.database import get_db_connection
from lookbook_mpc.config.settings import get_settings

logger = structlog.get_logger()
router = APIRouter(prefix="/v1/agents", tags=["agents"])

# Pydantic models
class AgentConfig(BaseModel):
    max_recommendations: Optional[int] = 5
    confidence_threshold: Optional[float] = 0.7
    enable_vision: Optional[bool] = False
    auto_response: Optional[bool] = True
    escalation_threshold: Optional[int] = 3

class AgentMetrics(BaseModel):
    total_recommendations: Optional[int] = 0
    user_satisfaction: Optional[float] = 0.0
    conversion_rate: Optional[float] = 0.0
    total_chats: Optional[int] = 0
    resolution_rate: Optional[float] = 0.0
    avg_session_duration: Optional[int] = 0
    total_analyses: Optional[int] = 0
    accuracy: Optional[float] = 0.0
    processing_time: Optional[float] = 0.0

class AgentCreate(BaseModel):
    name: str
    description: str
    status: str = "active"
    metrics: Optional[Dict[str, Any]] = {}
    config: Optional[Dict[str, Any]] = {}
    model_name: str = "qwen3"
    temperature: float = 0.7
    max_tokens: int = 1000
    system_prompt: str = ""
    capabilities: List[str] = []
    supported_intents: List[str] = []
    is_visible: bool = True
    access_level: str = "admin"
    version: str = "1.0.0"
    author: str = "AI Team"
    tags: List[str] = []

class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    config: Optional[Dict[str, Any]] = None
    model_name: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    system_prompt: Optional[str] = None
    capabilities: Optional[List[str]] = None
    supported_intents: Optional[List[str]] = None
    is_visible: Optional[bool] = None
    access_level: Optional[str] = None
    version: Optional[str] = None
    author: Optional[str] = None
    tags: Optional[List[str]] = None

class AgentResponse(BaseModel):
    id: int
    name: str
    description: str
    status: str
    metrics: Dict[str, Any]
    config: Dict[str, Any]
    total_sessions: int
    successful_sessions: int
    average_response_time: float
    success_rate: float
    model_name: str
    temperature: float
    max_tokens: int
    system_prompt: str
    capabilities: List[str]
    supported_intents: List[str]
    is_visible: bool
    access_level: str
    version: str
    author: str
    tags: List[str]
    created_at: str
    updated_at: str

    @classmethod
    def from_db(cls, agent_data: dict):
        """Create AgentResponse from database data, converting datetime to string."""
        return cls(
            id=agent_data['id'],
            name=agent_data['name'],
            description=agent_data['description'],
            status=agent_data['status'],
            metrics=agent_data['metrics'],
            config=agent_data['config'],
            total_sessions=agent_data['total_sessions'],
            successful_sessions=agent_data['successful_sessions'],
            average_response_time=agent_data['average_response_time'],
            success_rate=agent_data['success_rate'],
            model_name=agent_data['model_name'],
            temperature=agent_data['temperature'],
            max_tokens=agent_data['max_tokens'],
            system_prompt=agent_data['system_prompt'],
            capabilities=agent_data['capabilities'],
            supported_intents=agent_data['supported_intents'],
            is_visible=bool(agent_data['is_visible']),
            access_level=agent_data['access_level'],
            version=agent_data['version'],
            author=agent_data['author'],
            tags=agent_data['tags'],
            created_at=agent_data['created_at'].isoformat() if agent_data['created_at'] else None,
            updated_at=agent_data['updated_at'].isoformat() if agent_data['updated_at'] else None
        )

class RuleCreate(BaseModel):
    agent_id: int
    name: str
    rule_type: str
    conditions: Dict[str, Any]
    actions: Dict[str, Any]
    priority: int = 1
    is_active: bool = True
    description: str = ""
    author: str = "AI Team"
    version: str = "1.0.0"
    execution_order: int = 1
    timeout_seconds: int = 30
    scope: str = "global"
    target_agents: List[int] = []
    target_intents: List[str] = []
    test_cases: List[Dict[str, Any]] = []
    validation_rules: List[str] = []
    is_editable: bool = True
    access_level: str = "admin"
    tags: List[str] = []

class RuleUpdate(BaseModel):
    agent_id: Optional[int] = None
    name: Optional[str] = None
    rule_type: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None
    actions: Optional[Dict[str, Any]] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None
    author: Optional[str] = None
    version: Optional[str] = None
    execution_order: Optional[int] = None
    timeout_seconds: Optional[int] = None
    scope: Optional[str] = None
    target_agents: Optional[List[int]] = None
    target_intents: Optional[List[str]] = None
    test_cases: Optional[List[Dict[str, Any]]] = None
    validation_rules: Optional[List[str]] = None
    is_editable: Optional[bool] = None
    access_level: Optional[str] = None
    tags: Optional[List[str]] = None

class RuleResponse(BaseModel):
    id: int
    agent_id: int
    name: str
    rule_type: str
    conditions: Dict[str, Any]
    actions: Dict[str, Any]
    priority: int
    is_active: bool
    description: str
    author: str
    version: str
    execution_order: int
    timeout_seconds: int
    scope: str
    target_agents: List[int]
    target_intents: List[str]
    test_cases: List[Dict[str, Any]]
    validation_rules: List[str]
    last_tested_at: Optional[str]
    test_results: Optional[Dict[str, Any]]
    execution_count: int
    success_count: int
    average_execution_time: float
    dependencies: List[str]
    exclusions: List[str]
    is_editable: bool
    access_level: str
    tags: List[str]
    created_at: str
    updated_at: str

    @classmethod
    def from_db(cls, rule_data: dict):
        """Create RuleResponse from database data, converting datetime to string and handling None lists."""
        return cls(
            id=rule_data['id'],
            agent_id=rule_data['agent_id'],
            name=rule_data['name'],
            rule_type=rule_data['rule_type'],
            conditions=rule_data['conditions'],
            actions=rule_data['actions'],
            priority=rule_data['priority'],
            is_active=bool(rule_data['is_active']),
            description=rule_data['description'],
            author=rule_data['author'],
            version=rule_data['version'],
            execution_order=rule_data['execution_order'],
            timeout_seconds=rule_data['timeout_seconds'],
            scope=rule_data['scope'],
            target_agents=rule_data['target_agents'] or [],
            target_intents=rule_data['target_intents'] or [],
            test_cases=rule_data['test_cases'] or [],
            validation_rules=rule_data['validation_rules'] or [],
            last_tested_at=rule_data['last_tested_at'].isoformat() if rule_data['last_tested_at'] else None,
            test_results=rule_data['test_results'],
            execution_count=rule_data['execution_count'],
            success_count=rule_data['success_count'],
            average_execution_time=rule_data['average_execution_time'],
            dependencies=rule_data['dependencies'] or [],
            exclusions=rule_data['exclusions'] or [],
            is_editable=bool(rule_data['is_editable']),
            access_level=rule_data['access_level'],
            tags=rule_data['tags'] or [],
            created_at=rule_data['created_at'].isoformat() if rule_data['created_at'] else None,
            updated_at=rule_data['updated_at'].isoformat() if rule_data['updated_at'] else None
        )

@router.get("/dashboard", response_model=List[AgentResponse])
async def get_agents():
    """Get all agents from the database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM agent_dashboard ORDER BY created_at DESC")
        agents = cursor.fetchall()

        # Convert JSON fields properly
        for agent in agents:
            if isinstance(agent['metrics'], str):
                agent['metrics'] = json.loads(agent['metrics'])
            if isinstance(agent['config'], str):
                agent['config'] = json.loads(agent['config'])
            if isinstance(agent['capabilities'], str):
                agent['capabilities'] = json.loads(agent['capabilities'])
            if isinstance(agent['supported_intents'], str):
                agent['supported_intents'] = json.loads(agent['supported_intents'])
            if isinstance(agent['tags'], str):
                agent['tags'] = json.loads(agent['tags'])

        cursor.close()
        conn.close()

        return [AgentResponse.from_db(agent) for agent in agents]

    except Exception as e:
        logger.error("Error fetching agents", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch agents")

@router.get("/dashboard/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: int):
    """Get a specific agent by ID."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM agent_dashboard WHERE id = %s", (agent_id,))
        agent = cursor.fetchone()

        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        # Convert JSON fields properly
        if isinstance(agent['metrics'], str):
            agent['metrics'] = json.loads(agent['metrics'])
        if isinstance(agent['config'], str):
            agent['config'] = json.loads(agent['config'])
        if isinstance(agent['capabilities'], str):
            agent['capabilities'] = json.loads(agent['capabilities'])
        if isinstance(agent['supported_intents'], str):
            agent['supported_intents'] = json.loads(agent['supported_intents'])
        if isinstance(agent['tags'], str):
            agent['tags'] = json.loads(agent['tags'])

        cursor.close()
        conn.close()

        return agent

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching agent", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch agent")

@router.patch("/dashboard/{agent_id}", response_model=AgentResponse)
async def update_agent(agent_id: int, agent_update: AgentUpdate):
    """Update an existing agent."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if agent exists
        cursor.execute("SELECT * FROM agent_dashboard WHERE id = %s", (agent_id,))
        existing_agent = cursor.fetchone()

        if not existing_agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        # Build update query
        update_fields = []
        values = []

        for field, value in agent_update.dict(exclude_unset=True).items():
            if value is not None:
                update_fields.append(f"{field} = %s")
                values.append(value)

        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")

        values.append(agent_id)

        query = f"UPDATE agent_dashboard SET {', '.join(update_fields)} WHERE id = %s"
        cursor.execute(query, values)

        # Get updated agent
        cursor.execute("SELECT * FROM agent_dashboard WHERE id = %s", (agent_id,))
        updated_agent = cursor.fetchone()

        # Convert JSON fields properly
        if isinstance(updated_agent['metrics'], str):
            updated_agent['metrics'] = json.loads(updated_agent['metrics'])
        if isinstance(updated_agent['config'], str):
            updated_agent['config'] = json.loads(updated_agent['config'])
        if isinstance(updated_agent['capabilities'], str):
            updated_agent['capabilities'] = json.loads(updated_agent['capabilities'])
        if isinstance(updated_agent['supported_intents'], str):
            updated_agent['supported_intents'] = json.loads(updated_agent['supported_intents'])
        if isinstance(updated_agent['tags'], str):
            updated_agent['tags'] = json.loads(updated_agent['tags'])

        cursor.close()
        conn.close()

        return updated_agent

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating agent", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update agent")

@router.delete("/dashboard/{agent_id}")
async def delete_agent(agent_id: int):
    """Delete an agent and its associated rules."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if agent exists
        cursor.execute("SELECT * FROM agent_dashboard WHERE id = %s", (agent_id,))
        existing_agent = cursor.fetchone()

        if not existing_agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        # Delete associated rules first (foreign key constraint)
        cursor.execute("DELETE FROM agent_rules WHERE agent_id = %s", (agent_id,))

        # Delete agent
        cursor.execute("DELETE FROM agent_dashboard WHERE id = %s", (agent_id,))

        conn.commit()
        cursor.close()
        conn.close()

        return {"message": "Agent deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting agent", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete agent")

@router.get("/rules", response_model=List[RuleResponse])
async def get_rules(agent_id: Optional[int] = None):
    """Get all rules, optionally filtered by agent ID."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if agent_id:
            cursor.execute("SELECT * FROM agent_rules WHERE agent_id = %s ORDER BY priority, execution_order", (agent_id,))
        else:
            cursor.execute("SELECT * FROM agent_rules ORDER BY agent_id, priority, execution_order")

        rules = cursor.fetchall()

        # Convert JSON fields properly
        for rule in rules:
            if isinstance(rule['conditions'], str):
                rule['conditions'] = json.loads(rule['conditions'])
            if isinstance(rule['actions'], str):
                rule['actions'] = json.loads(rule['actions'])
            if isinstance(rule['target_agents'], str):
                rule['target_agents'] = json.loads(rule['target_agents'])
            if isinstance(rule['target_intents'], str):
                rule['target_intents'] = json.loads(rule['target_intents'])
            if isinstance(rule['test_cases'], str):
                rule['test_cases'] = json.loads(rule['test_cases'])
            if isinstance(rule['validation_rules'], str):
                rule['validation_rules'] = json.loads(rule['validation_rules'])
            if isinstance(rule['test_results'], str):
                rule['test_results'] = json.loads(rule['test_results'])
            if isinstance(rule['dependencies'], str):
                rule['dependencies'] = json.loads(rule['dependencies'])
            if isinstance(rule['exclusions'], str):
                rule['exclusions'] = json.loads(rule['exclusions'])
            if isinstance(rule['tags'], str):
                rule['tags'] = json.loads(rule['tags'])

        cursor.close()
        conn.close()

        return [RuleResponse.from_db(rule) for rule in rules]

    except Exception as e:
        logger.error("Error fetching rules", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch rules")

@router.get("/rules/{rule_id}", response_model=RuleResponse)
async def get_rule(rule_id: int):
    """Get a specific rule by ID."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM agent_rules WHERE id = %s", (rule_id,))
        rule = cursor.fetchone()

        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")

        # Convert JSON fields properly
        if isinstance(rule['conditions'], str):
            rule['conditions'] = json.loads(rule['conditions'])
        if isinstance(rule['actions'], str):
            rule['actions'] = json.loads(rule['actions'])
        if isinstance(rule['target_agents'], str):
            rule['target_agents'] = json.loads(rule['target_agents'])
        if isinstance(rule['target_intents'], str):
            rule['target_intents'] = json.loads(rule['target_intents'])
        if isinstance(rule['test_cases'], str):
            rule['test_cases'] = json.loads(rule['test_cases'])
        if isinstance(rule['validation_rules'], str):
            rule['validation_rules'] = json.loads(rule['validation_rules'])
        if isinstance(rule['test_results'], str):
            rule['test_results'] = json.loads(rule['test_results'])
        if isinstance(rule['dependencies'], str):
            rule['dependencies'] = json.loads(rule['dependencies'])
        if isinstance(rule['exclusions'], str):
            rule['exclusions'] = json.loads(rule['exclusions'])
        if isinstance(rule['tags'], str):
            rule['tags'] = json.loads(rule['tags'])

        cursor.close()
        conn.close()

        return rule

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching rule", rule_id=rule_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to fetch rule")

@router.post("/rules", response_model=RuleResponse)
async def create_rule(rule_create: RuleCreate):
    """Create a new rule."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if agent exists
        cursor.execute("SELECT * FROM agent_dashboard WHERE id = %s", (rule_create.agent_id,))
        agent = cursor.fetchone()

        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        # Insert rule
        cursor.execute("""
            INSERT INTO agent_rules
            (agent_id, name, rule_type, conditions, actions, priority, is_active, description,
             author, version, execution_order, timeout_seconds, scope, target_agents,
             target_intents, test_cases, validation_rules, is_editable, access_level, tags)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            rule_create.agent_id, rule_create.name, rule_create.rule_type,
            str(rule_create.conditions), str(rule_create.actions), rule_create.priority,
            rule_create.is_active, rule_create.description, rule_create.author,
            rule_create.version, rule_create.execution_order, rule_create.timeout_seconds,
            rule_create.scope, str(rule_create.target_agents), str(rule_create.target_intents),
            str(rule_create.test_cases), str(rule_create.validation_rules),
            rule_create.is_editable, rule_create.access_level, str(rule_create.tags)
        ))

        rule_id = cursor.lastrowid

        # Get created rule
        cursor.execute("SELECT * FROM agent_rules WHERE id = %s", (rule_id,))
        created_rule = cursor.fetchone()

        # Convert JSON fields properly
        if isinstance(created_rule['conditions'], str):
            created_rule['conditions'] = json.loads(created_rule['conditions'])
        if isinstance(created_rule['actions'], str):
            created_rule['actions'] = json.loads(created_rule['actions'])
        if isinstance(created_rule['target_agents'], str):
            created_rule['target_agents'] = json.loads(created_rule['target_agents'])
        if isinstance(created_rule['target_intents'], str):
            created_rule['target_intents'] = json.loads(created_rule['target_intents'])
        if isinstance(created_rule['test_cases'], str):
            created_rule['test_cases'] = json.loads(created_rule['test_cases'])
        if isinstance(created_rule['validation_rules'], str):
            created_rule['validation_rules'] = json.loads(created_rule['validation_rules'])
        if isinstance(created_rule['test_results'], str):
            created_rule['test_results'] = json.loads(created_rule['test_results'])
        if isinstance(created_rule['dependencies'], str):
            created_rule['dependencies'] = json.loads(created_rule['dependencies'])
        if isinstance(created_rule['exclusions'], str):
            created_rule['exclusions'] = json.loads(created_rule['exclusions'])
        if isinstance(created_rule['tags'], str):
            created_rule['tags'] = json.loads(created_rule['tags'])

        cursor.close()
        conn.close()

        return created_rule

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating rule", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create rule")

@router.patch("/rules/{rule_id}", response_model=RuleResponse)
async def update_rule(rule_id: int, rule_update: RuleUpdate):
    """Update an existing rule."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if rule exists
        cursor.execute("SELECT * FROM agent_rules WHERE id = %s", (rule_id,))
        existing_rule = cursor.fetchone()

        if not existing_rule:
            raise HTTPException(status_code=404, detail="Rule not found")

        # Build update query
        update_fields = []
        values = []

        for field, value in rule_update.dict(exclude_unset=True).items():
            if value is not None:
                if field in ['conditions', 'actions', 'target_agents', 'target_intents',
                           'test_cases', 'validation_rules', 'test_results', 'dependencies',
                           'exclusions', 'tags']:
                    update_fields.append(f"{field} = %s")
                    values.append(str(value))
                else:
                    update_fields.append(f"{field} = %s")
                    values.append(value)

        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")

        values.append(rule_id)

        query = f"UPDATE agent_rules SET {', '.join(update_fields)} WHERE id = %s"
        cursor.execute(query, values)

        # Get updated rule
        cursor.execute("SELECT * FROM agent_rules WHERE id = %s", (rule_id,))
        updated_rule = cursor.fetchone()

        # Convert JSON fields properly
        if isinstance(updated_rule['conditions'], str):
            updated_rule['conditions'] = json.loads(updated_rule['conditions'])
        if isinstance(updated_rule['actions'], str):
            updated_rule['actions'] = json.loads(updated_rule['actions'])
        if isinstance(updated_rule['target_agents'], str):
            updated_rule['target_agents'] = json.loads(updated_rule['target_agents'])
        if isinstance(updated_rule['target_intents'], str):
            updated_rule['target_intents'] = json.loads(updated_rule['target_intents'])
        if isinstance(updated_rule['test_cases'], str):
            updated_rule['test_cases'] = json.loads(updated_rule['test_cases'])
        if isinstance(updated_rule['validation_rules'], str):
            updated_rule['validation_rules'] = json.loads(updated_rule['validation_rules'])
        if isinstance(updated_rule['test_results'], str):
            updated_rule['test_results'] = json.loads(updated_rule['test_results'])
        if isinstance(updated_rule['dependencies'], str):
            updated_rule['dependencies'] = json.loads(updated_rule['dependencies'])
        if isinstance(updated_rule['exclusions'], str):
            updated_rule['exclusions'] = json.loads(updated_rule['exclusions'])
        if isinstance(updated_rule['tags'], str):
            updated_rule['tags'] = json.loads(updated_rule['tags'])

        cursor.close()
        conn.close()

        return updated_rule

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating rule", rule_id=rule_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update rule")

@router.delete("/rules/{rule_id}")
async def delete_rule(rule_id: int):
    """Delete a rule."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if rule exists
        cursor.execute("SELECT * FROM agent_rules WHERE id = %s", (rule_id,))
        existing_rule = cursor.fetchone()

        if not existing_rule:
            raise HTTPException(status_code=404, detail="Rule not found")

        # Delete rule
        cursor.execute("DELETE FROM agent_rules WHERE id = %s", (rule_id,))

        conn.commit()
        cursor.close()
        conn.close()

        return {"message": "Rule deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting rule", rule_id=rule_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete rule")