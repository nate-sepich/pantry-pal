from pydantic import BaseModel, Field
from enum import Enum
from typing import List, Optional

class ExerciseIntensity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"

class ExerciseMetadata(BaseModel):
    weekly_hours: float = Field(..., gt=0, description="Total hours of exercise per week")
    intensity: ExerciseIntensity = Field(..., description="Overall intensity of weekly exercise")
    exercise_type: str = Field(..., description="Primary type of exercise (e.g., cardio, strength training)")

class DietaryRestrictionType(str, Enum):
    vegetarian = "vegetarian"
    vegan = "vegan"
    gluten_free = "gluten_free"
    lactose_intolerant = "lactose_intolerant"
    nut_allergy = "nut_allergy"
    shellfish_allergy = "shellfish_allergy"
    diabetic = "diabetic"
    low_sodium = "low_sodium"

class DietaryRestrictionsMetadata(BaseModel):
    restrictions: List[DietaryRestrictionType] = Field(..., description="List of dietary restrictions")

class PhysicalStatsMetadata(BaseModel):
    height_cm: int = Field(..., gt=0, description="Height in centimeters")
    weight_kg: float = Field(..., gt=0, description="Weight in kilograms")
    age: int = Field(..., gt=0, description="Age in years")
    gender: str = Field(..., description="Gender of the individual")
    activity_level: Optional[str] = Field(None, description="General activity level (e.g., sedentary, active, very active)")
    goal: Optional[str] = Field(None, description="Fitness goal (e.g., weight loss, muscle gain, maintenance)")

class UserProfile(BaseModel):
    physical_stats: PhysicalStatsMetadata
    dietary_restrictions: Optional[DietaryRestrictionsMetadata] = Field(None, description="Optional dietary restrictions")
    exercise: ExerciseMetadata = Field(..., description="High-level exercise information")

# Example usage

example_profile = UserProfile(
    physical_stats=PhysicalStatsMetadata(
        height_cm=195,
        weight_kg=85.5,
        age=30,
        gender="male",
        activity_level="very active",
        goal="muscle gain"
    ),
    dietary_restrictions=DietaryRestrictionsMetadata(
        restrictions=[DietaryRestrictionType.vegan]
    ),
    exercise=ExerciseMetadata(
        weekly_hours=6,
        intensity=ExerciseIntensity.high,
        exercise_type="cardio and strength training"
    )
)

# Using json() method
print(example_profile.json())
