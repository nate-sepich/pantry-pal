from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class MacroPlan(BaseModel):
    calories: Dict[str, int] = Field(..., description="Caloric intake recommendations")
    protein: float = Field(..., description="Daily protein intake in grams")
    carbohydrates: Dict[str, float] = Field(..., description="Daily carbohydrate intake in grams and ratio")
    fat: Dict[str, float] = Field(..., description="Daily fat intake in grams with a range")
    weekly_summary: Dict[str, float] = Field(..., description="Weekly totals for calories, protein, carbohydrates, and fat")
    food_sources: Dict[str, List[str]] = Field(..., description="Recommended vegan food sources")
    practical_tips: List[str] = Field(..., description="Tips for tracking, prioritizing foods, hydration, and adjustments")

class GeminiOutput(BaseModel):
    macro_plan: MacroPlan = Field(..., description="Generated macro plan from the Gemini API")

# Example structure with dummy data
example_output = GeminiOutput(
    macro_plan=MacroPlan(
        calories={
            "maintenance": 3000,
            "surplus": 3200,
        },
        protein=180.0,
        carbohydrates={
            "grams": 350.0,
            "ratio": 1.2,
        },
        fat={
            "min_grams": 80.0,
            "max_grams": 130.0,
        },
        weekly_summary={
            "total_calories": 22400,
            "total_protein": 1260.0,
            "total_carbohydrates": 2450.0,
            "total_fat": 735.0,
        },
        food_sources={
            "protein": ["Tofu", "Tempeh", "Lentils"],
            "carbohydrates": ["Whole grains", "Fruits", "Vegetables"],
            "healthy_fats": ["Avocados", "Nuts", "Olive oil"],
        },
        practical_tips=[
            "Track your intake using a food tracking app.",
            "Prioritize whole, nutrient-dense foods.",
            "Stay hydrated throughout the day.",
            "Listen to your body and adjust intake as needed."
        ]
    )
)

print(example_output.json())
