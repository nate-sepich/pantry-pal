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
    product_name: str
    quantity: Optional[int]
    upc: Optional[str] = None
    macros: Optional[InventoryItemMacros]