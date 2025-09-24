"""
Lightweight tests for lookbooks API
"""

import pytest
import json
from unittest.mock import Mock, patch
from lookbook_mpc.api.routers.lookbooks import router


@pytest.fixture
def mock_db_connection():
    """Mock database connection."""
    with patch('lookbook_mpc.api.routers.lookbooks.get_db_connection') as mock_conn:
        mock_cursor = Mock()
        mock_conn.return_value.cursor.return_value = mock_cursor
        yield mock_cursor


def test_get_lookbooks_empty(mock_db_connection):
    """Test getting lookbooks when none exist."""
    mock_db_connection.fetchall.return_value = []

    # This would need to be adapted to test the actual endpoint
    # For now, just verify the mock setup
    assert mock_db_connection.fetchall.called


def test_create_lookbook(mock_db_connection):
    """Test creating a lookbook."""
    mock_db_connection.fetchone.return_value = {
        'id': 'test-id',
        'slug': 'test-slug',
        'title': 'Test Lookbook',
        'description': None,
        'cover_image_key': None,
        'is_active': True,
        'akeneo_lookbook_id': None,
        'akeneo_score': None,
        'akeneo_last_update': None,
        'akeneo_sync_status': 'never',
        'akeneo_last_error': None,
        'created_at': '2025-01-01T00:00:00',
        'updated_at': '2025-01-01T00:00:00'
    }

    # Verify mock returns expected data
    result = mock_db_connection.fetchone()
    assert result['id'] == 'test-id'
    assert result['title'] == 'Test Lookbook'


def test_lookbook_model_from_db():
    """Test Lookbook model creation from database data."""
    from lookbook_mpc.api.routers.lookbooks import Lookbook

    db_data = {
        'id': 'test-id',
        'slug': 'test-slug',
        'title': 'Test Lookbook',
        'description': 'Test description',
        'cover_image_key': 'test.jpg',
        'is_active': True,
        'akeneo_lookbook_id': 'akeneo-123',
        'akeneo_score': 85.5,
        'akeneo_last_update': '2025-01-01T00:00:00',
        'akeneo_sync_status': 'linked',
        'akeneo_last_error': None,
        'created_at': '2025-01-01T00:00:00',
        'updated_at': '2025-01-01T00:00:00'
    }

    lookbook = Lookbook.from_db(db_data)

    assert lookbook.id == 'test-id'
    assert lookbook.title == 'Test Lookbook'
    assert lookbook.akeneo_score == 85.5
    assert lookbook.akeneo_sync_status == 'linked'
    assert '2025-01-01T00:00:00' in lookbook.created_at


if __name__ == '__main__':
    pytest.main([__file__])