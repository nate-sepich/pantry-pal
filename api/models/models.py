import uuid
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from decimal import Decimal

class UPCResponseModel(BaseModel):
    fdc_id: str

class ChatMessage(BaseModel):
    role: str
    content: str


class LLMChatRequest(BaseModel):
    messages: List[ChatMessage]

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: Optional[str] = None
    email: Optional[str] = None
    health_roi: Optional[Decimal] = 0
    financial_roi: Optional[Decimal] = 0
    environmental_roi: Optional[Decimal] = 0

class InventoryItemMacros(BaseModel):
    calories: Optional[Decimal] = 0
    protein: Optional[Decimal] = 0
    carbohydrates: Optional[Decimal] = 0
    fiber: Optional[Decimal] = 0
    sugar: Optional[Decimal] = 0
    fat: Optional[Decimal] = 0
    saturated_fat: Optional[Decimal] = 0
    polyunsaturated_fat: Optional[Decimal] = 0
    monounsaturated_fat: Optional[Decimal] = 0
    trans_fat: Optional[Decimal] = 0
    cholesterol: Optional[Decimal] = 0
    sodium: Optional[Decimal] = 0
    potassium: Optional[Decimal] = 0
    vitamin_a: Optional[Decimal] = 0
    vitamin_c: Optional[Decimal] = 0
    calcium: Optional[Decimal] = 0
    iron: Optional[Decimal] = 0
    
    @validator('calories', 'protein', 'carbohydrates', 'fiber', 'sugar', 'fat', 'saturated_fat', 'cholesterol', 'sodium', pre=True)
    def non_negative(cls, v):
        if v < 0:
            raise ValueError('Nutritional values must be non-negative')
        return v

class InventoryItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str]  # Link to the user who added the item
    product_name: str
    quantity: Optional[int] = 1
    upc: Optional[str] = None
    macros: Optional[InventoryItemMacros] = None
    cost: Optional[Decimal] = Decimal("0")  # Use Decimal for DynamoDB compatibility
    expiration_date: Optional[str] = None
    environmental_impact: Optional[Decimal] = Decimal("0")  # Use Decimal for DynamoDB compatibility
    image_url: Optional[str] = None  # Public S3 URL for item image
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
    ingredients: List[RecipeIngredientInput]
    servings: int
    
class RecipeIngredient(BaseModel):
    item: InventoryItem
    quantity: Decimal  # The amount of this ingredient used in the recipe, in grams or other units

class Recipe(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    ingredients: List[RecipeIngredient]
    servings: int
    
    @property
    def total_macros(self) -> InventoryItemMacros:
        """Aggregate macros across all ingredients, based on quantity."""
        total_macros = InventoryItemMacros()
        
        for ingredient in self.ingredients:
            if ingredient.item.macros:
                total_macros.protein += ingredient.item.macros.protein * (ingredient.quantity / 100)
                total_macros.carbohydrates += ingredient.item.macros.carbohydrates * (ingredient.quantity / 100)
                total_macros.fiber += ingredient.item.macros.fiber * (ingredient.quantity / 100)
                total_macros.sugar += ingredient.item.macros.sugar * (ingredient.quantity / 100)
                total_macros.fat += ingredient.item.macros.fat * (ingredient.quantity / 100)
                total_macros.saturated_fat += ingredient.item.macros.saturated_fat * (ingredient.quantity / 100)
                total_macros.polyunsaturated_fat += ingredient.item.macros.polyunsaturated_fat * (ingredient.quantity / 100)
                total_macros.monounsaturated_fat += ingredient.item.macros.monounsaturated_fat * (ingredient.quantity / 100)
                total_macros.trans_fat += ingredient.item.macros.trans_fat * (ingredient.quantity / 100)
                total_macros.cholesterol += ingredient.item.macros.cholesterol * (ingredient.quantity / 100)
                total_macros.sodium += ingredient.item.macros.sodium * (ingredient.quantity / 100)
                total_macros.potassium += ingredient.item.macros.potassium * (ingredient.quantity / 100)
                total_macros.vitamin_a += ingredient.item.macros.vitamin_a * (ingredient.quantity / 100)
                total_macros.vitamin_c += ingredient.item.macros.vitamin_c * (ingredient.quantity / 100)
                total_macros.calcium += ingredient.item.macros.calcium * (ingredient.quantity / 100)
                total_macros.iron += ingredient.item.macros.iron * (ingredient.quantity / 100)

        # Scale the macros to per-serving if servings > 1
        if self.servings > 1:
            total_macros = InventoryItemMacros(
                protein=total_macros.protein / self.servings,
                carbohydrates=total_macros.carbohydrates / self.servings,
                fiber=total_macros.fiber / self.servings,
                sugar=total_macros.sugar / self.servings,
                fat=total_macros.fat / self.servings,
                saturated_fat=total_macros.saturated_fat / self.servings,
                polyunsaturated_fat=total_macros.polyunsaturated_fat / self.servings,
                monounsaturated_fat=total_macros.monounsaturated_fat / self.servings,
                trans_fat=total_macros.trans_fat / self.servings,
                cholesterol=total_macros.cholesterol / self.servings,
                sodium=total_macros.sodium / self.servings,
                potassium=total_macros.potassium / self.servings,
                vitamin_a=total_macros.vitamin_a / self.servings,
                vitamin_c=total_macros.vitamin_c / self.servings,
                calcium=total_macros.calcium / self.servings,
                iron=total_macros.iron / self.servings
            )
        
        return total_macros


class RecipeModifiers(BaseModel):
    servings: Optional[int] = None
    flavorAdjustments: Optional[List[str]] = None
    removeItems: Optional[List[str]] = None
    overrides: Optional[List[str]] = None


class RecipeRequest(BaseModel):
    itemIds: List[str]
    modifiers: Optional[RecipeModifiers] = None


class RecipeResponse(BaseModel):
    recipe: dict


class ChatMeta(BaseModel):
    id: str
    title: str
    updatedAt: str
    length: int
