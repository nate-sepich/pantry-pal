import pytest
import json
from unittest.mock import patch, MagicMock

def test_get_items_empty_pantry(test_client, mock_aws_services, auth_headers):
    """Test getting items from empty pantry"""
    response = test_client.get("/pantry/items", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []

def test_get_items_with_data(test_client, mock_aws_services, auth_headers, sample_pantry_item):
    """Test getting items when pantry has data"""
    # First add an item
    add_response = test_client.post(
        "/pantry/items", 
        json=sample_pantry_item,
        headers=auth_headers
    )
    assert add_response.status_code == 200
    
    # Then get items
    response = test_client.get("/pantry/items", headers=auth_headers)
    assert response.status_code == 200
    items = response.json()
    assert len(items) >= 1
    assert items[0]["name"] == sample_pantry_item["name"]

def test_create_item_success(test_client, mock_aws_services, auth_headers, sample_pantry_item):
    """Test successful item creation"""
    response = test_client.post(
        "/pantry/items",
        json=sample_pantry_item,
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == sample_pantry_item["name"]
    assert data["quantity"] == sample_pantry_item["quantity"]
    assert "id" in data

def test_create_item_invalid_data(test_client, auth_headers):
    """Test item creation with invalid data"""
    invalid_item = {"invalid": "data"}
    response = test_client.post(
        "/pantry/items",
        json=invalid_item,
        headers=auth_headers
    )
    assert response.status_code == 422

def test_update_item_success(test_client, mock_aws_services, auth_headers, sample_pantry_item):
    """Test successful item update"""
    # First create an item
    create_response = test_client.post(
        "/pantry/items",
        json=sample_pantry_item,
        headers=auth_headers
    )
    assert create_response.status_code == 200
    item_id = create_response.json()["id"]
    
    # Update the item
    updated_data = sample_pantry_item.copy()
    updated_data["quantity"] = 10
    
    response = test_client.put(
        f"/pantry/items/{item_id}",
        json=updated_data,
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["quantity"] == 10

def test_update_nonexistent_item(test_client, auth_headers, sample_pantry_item):
    """Test updating non-existent item"""
    response = test_client.put(
        "/pantry/items/nonexistent-id",
        json=sample_pantry_item,
        headers=auth_headers
    )
    assert response.status_code == 404

def test_delete_item_success(test_client, mock_aws_services, auth_headers, sample_pantry_item):
    """Test successful item deletion"""
    # First create an item
    create_response = test_client.post(
        "/pantry/items",
        json=sample_pantry_item,
        headers=auth_headers
    )
    assert create_response.status_code == 200
    item_id = create_response.json()["id"]
    
    # Delete the item
    response = test_client.delete(
        f"/pantry/items/{item_id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    
    # Verify it's deleted
    get_response = test_client.get(
        f"/pantry/items/{item_id}",
        headers=auth_headers
    )
    assert get_response.status_code == 404

def test_delete_nonexistent_item(test_client, auth_headers):
    """Test deleting non-existent item"""
    response = test_client.delete(
        "/pantry/items/nonexistent-id",
        headers=auth_headers
    )
    assert response.status_code == 404

def test_get_roi_metrics(test_client, mock_aws_services, auth_headers):
    """Test getting ROI metrics"""
    response = test_client.get("/roi/metrics", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "savings" in data or "message" in data

def test_barcode_scan_endpoint(test_client, auth_headers, temp_image_file):
    """Test barcode scanning endpoint"""
    with open(temp_image_file, 'rb') as f:
        files = {'file': ('test.jpg', f, 'image/jpeg')}
        response = test_client.post(
            "/pantry/scan-barcode",
            files=files,
            headers=auth_headers
        )
    # Should return 200 even if no barcode found
    assert response.status_code in [200, 422] 
