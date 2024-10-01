import uuid
from pydantic import BaseModel, Field, validator
from typing import List, Optional

class InventoryItemMacros(BaseModel):
    protein: Optional[float] = 0
    carbohydrates: Optional[float] = 0
    fiber: Optional[float] = 0
    sugar: Optional[float] = 0
    fat: Optional[float] = 0
    saturated_fat: Optional[float] = 0
    polyunsaturated_fat: Optional[float] = 0
    monounsaturated_fat: Optional[float] = 0
    trans_fat: Optional[float] = 0
    cholesterol: Optional[float] = 0
    sodium: Optional[float] = 0
    potassium: Optional[float] = 0
    vitamin_a: Optional[float] = 0
    vitamin_c: Optional[float] = 0
    calcium: Optional[float] = 0
    iron: Optional[float] = 0
    
    @validator('protein', 'carbohydrates', 'fiber', 'sugar', 'fat', 'saturated_fat', 'cholesterol', 'sodium', pre=True)
    def non_negative(cls, v):
        if v < 0:
            raise ValueError('Nutritional values must be non-negative')
        return v

class InventoryItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    product_name: str
    quantity: Optional[int]
    upc: Optional[str] = None
    macros: Optional[InventoryItemMacros] = None
    
class RecipeIngredientInput(BaseModel):
    item_name: str
    quantity: float  # Quantity of the ingredient in grams

class RecipeInput(BaseModel):
    name: str
    ingredients: List[RecipeIngredientInput]
    servings: int
    
class RecipeIngredient(BaseModel):
    item: InventoryItem
    quantity: float  # The amount of this ingredient used in the recipe, in grams or other units

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