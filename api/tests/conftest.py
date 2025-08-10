import pytest
import os
import boto3
from moto import mock_dynamodb, mock_s3, mock_sqs, mock_cognito_idp
from fastapi.testclient import TestClient
from api.app import app
from pantry.pantry_service import get_user, get_user_id_from_token
import tempfile
from unittest.mock import patch

class MockUser:
    def __init__(self, user_id="testuser", email="test@example.com"):
        self.id = user_id
        self.email = email
        self.username = user_id

@pytest.fixture(scope="session")
def mock_user():
    return MockUser()

@pytest.fixture(scope="session")
def override_dependencies():
    """Override FastAPI dependencies for testing"""
    def override_get_user():
        return MockUser()

    def override_get_user_id_from_token():
        return "testuser"

    app.dependency_overrides[get_user] = override_get_user
    app.dependency_overrides[get_user_id_from_token] = override_get_user_id_from_token
    
    yield
    
    # Clean up
    app.dependency_overrides.clear()

@pytest.fixture(scope="session")
def test_client(override_dependencies):
    """FastAPI test client with dependency overrides"""
    return TestClient(app)

@pytest.fixture(scope="function")
def mock_aws_services():
    """Mock AWS services for testing"""
    with mock_dynamodb(), mock_s3(), mock_sqs(), mock_cognito_idp():
        # Set up test environment variables
        os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
        os.environ['MACRO_QUEUE_URL'] = 'https://sqs.us-east-1.amazonaws.com/123456789/test-queue'
        os.environ['IMAGE_QUEUE_URL'] = 'https://sqs.us-east-1.amazonaws.com/123456789/test-image-queue'
        os.environ['IMAGE_BUCKET_NAME'] = 'test-bucket'
        
        # Create mock DynamoDB tables
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        
        # PantryPal table
        pantry_table = dynamodb.create_table(
            TableName='PantryPal',
            KeySchema=[
                {'AttributeName': 'PK', 'KeyType': 'HASH'},
                {'AttributeName': 'SK', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'PK', 'AttributeType': 'S'},
                {'AttributeName': 'SK', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Auth table
        auth_table = dynamodb.create_table(
            TableName='AuthTable',
            KeySchema=[
                {'AttributeName': 'username', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'username', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Create mock S3 bucket
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='test-bucket')
        
        # Create mock SQS queues
        sqs = boto3.client('sqs', region_name='us-east-1')
        sqs.create_queue(QueueName='test-queue')
        sqs.create_queue(QueueName='test-image-queue')
        
        yield {
            'dynamodb': dynamodb,
            's3': s3,
            'sqs': sqs,
            'pantry_table': pantry_table,
            'auth_table': auth_table
        }

@pytest.fixture
def sample_pantry_item():
    """Sample pantry item for testing"""
    return {
        "name": "Test Apple",
        "quantity": 5,
        "unit": "pieces",
        "expiration_date": "2024-12-31",
        "category": "fruit",
        "barcode": "123456789",
        "nutritional_info": {
            "calories": 52,
            "protein": 0.3,
            "carbs": 13.8,
            "fat": 0.2
        }
    }

@pytest.fixture
def sample_recipe():
    """Sample recipe for testing"""
    return {
        "title": "Test Apple Pie",
        "ingredients": ["6 apples", "2 cups flour", "1 cup sugar"],
        "instructions": ["Peel apples", "Make dough", "Bake at 350F"],
        "prep_time": 30,
        "cook_time": 60,
        "servings": 8,
        "tags": ["dessert", "fruit"]
    }

@pytest.fixture
def auth_headers():
    """Mock authorization headers"""
    return {"Authorization": "Bearer mock.jwt.token"}

@pytest.fixture
def temp_image_file():
    """Create a temporary image file for testing"""
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        # Write some dummy image data
        f.write(b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01')
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    try:
        os.unlink(temp_path)
    except OSError:
        pass

@pytest.fixture(autouse=True)
def mock_openai_calls():
    """Mock OpenAI API calls to avoid real API usage in tests"""
    with patch('openai.ChatCompletion.create') as mock_openai:
        mock_openai.return_value = {
            'choices': [{
                'message': {
                    'content': '{"calories": 100, "protein": 2, "carbs": 25, "fat": 0}'
                }
            }]
        }
        yield mock_openai