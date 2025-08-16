import uuid
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field, validator


class UPCResponseModel(BaseModel):
    fdc_id: str


class ChatMessage(BaseModel):
    role: str
    content: str


class LLMChatRequest(BaseModel):
    messages: list[ChatMessage]


class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str | None = None
    email: str | None = None
    health_roi: Decimal | None = 0
    financial_roi: Decimal | None = 0
    environmental_roi: Decimal | None = 0


class InventoryItemMacros(BaseModel):
    calories: Decimal | None = 0
    protein: Decimal | None = 0
    carbohydrates: Decimal | None = 0
    fiber: Decimal | None = 0
    sugar: Decimal | None = 0
    fat: Decimal | None = 0
    saturated_fat: Decimal | None = 0
    polyunsaturated_fat: Decimal | None = 0
    monounsaturated_fat: Decimal | None = 0
    trans_fat: Decimal | None = 0
    cholesterol: Decimal | None = 0
    sodium: Decimal | None = 0
    potassium: Decimal | None = 0
    vitamin_a: Decimal | None = 0
    vitamin_c: Decimal | None = 0
    calcium: Decimal | None = 0
    iron: Decimal | None = 0

    @validator(
        "calories",
        "protein",
        "carbohydrates",
        "fiber",
        "sugar",
        "fat",
        "saturated_fat",
        "cholesterol",
        "sodium",
        pre=True,
    )
    def non_negative(cls, v):
        if v < 0:
            raise ValueError("Nutritional values must be non-negative")
        return v


class InventoryItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str | None  # Link to the user who added the item
    product_name: str
    quantity: int | None = 1
    upc: str | None = None
    macros: InventoryItemMacros | None = None
    cost: Decimal | None = Decimal("0")  # Use Decimal for DynamoDB compatibility
    expiration_date: str | None = None
    environmental_impact: Decimal | None = Decimal("0")  # Use Decimal for DynamoDB compatibility
    image_url: str | None = None  # Public S3 URL for item image
    active: bool = True  # Default to active

    @validator("cost", "environmental_impact", pre=True, always=True)
    def convert_to_decimal(cls, v):
        """Convert Decimal values to Decimal for DynamoDB compatibility."""
        if v is not None:
            return Decimal(str(v))
        return Decimal("0")

    def to_dynamodb_dict(self) -> dict:
        """Convert the model to a DynamoDB-compatible dictionary."""
        data = self.dict()
        data["macros"] = self.macros.dict() if self.macros else None
        return {k: v for k, v in data.items() if v is not None}


class RecipeIngredientInput(BaseModel):
    item_name: str
    quantity: Decimal  # Quantity of the ingredient in grams


class RecipeInput(BaseModel):
    name: str
    ingredients: list[RecipeIngredientInput]
    servings: int


class RecipeIngredient(BaseModel):
    item: InventoryItem
    quantity: Decimal  # The amount of this ingredient used in the recipe, in grams or other units


class Recipe(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    ingredients: list[str] | None = None
    instructions: str | None = None
    image_url: str | None = None
    cook_time: str | None = None
    tags: list[str] | None = None
    active: bool = True  # Soft delete flag


class RecipeModifiers(BaseModel):
    servings: int | None = None
    flavorAdjustments: list[str] | None = None
    removeItems: list[str] | None = None
    overrides: list[str] | None = None


class RecipeRequest(BaseModel):
    itemIds: list[str]
    modifiers: RecipeModifiers | None = None


class RecipeResponse(BaseModel):
    recipe: dict


class ChatMeta(BaseModel):
    id: str
    title: str
    updatedAt: str
    length: int


class FoodCategory(str, Enum):
    """High-level food category used for autocomplete filtering."""

    DAIRY = "dairy"
    MEAT = "meat"
    SEAFOOD = "seafood"
    CARBS = "carbs"
    FATS = "fats"
    VEGETABLES = "vegetables"
    FRUITS = "fruits"
    BEVERAGES = "beverages"
    OTHER = "other"


class FoodSuggestion(BaseModel):
    """Autocomplete suggestion with USDA id and category."""

    name: str
    fdc_id: str | None = None
    category: FoodCategory = FoodCategory.OTHER


class ItemMacroRequest(BaseModel):
    """Request model for manual item macro lookup."""

    item_name: str
    quantity: Decimal = Decimal(100)
    unit: str = "g"

    @validator("item_name")
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("item_name cannot be blank")
        return v

    @validator("quantity")
    def validate_qty(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("quantity must be positive")
        return v


class UPCLookupResponse(BaseModel):
    """Response model for UPC lookup."""

    product_name: str
    brand: str | None = None
    category: str | None = None
    image_url: str | None = None
    fdc_id: str | None = None
    ingredients: str | None = None
    source: str | None = None
