import google.generativeai as genai
import json
from pydantic import BaseModel, Field
from typing import List, Dict

# Define the input and output data models
class PhysicalStats(BaseModel):
    height_cm: int
    weight_kg: float
    age: int
    gender: str
    activity_level: str
    goal: str

class DietaryRestrictions(BaseModel):
    restrictions: List[str]

class Exercise(BaseModel):
    weekly_hours: float
    intensity: str
    exercise_type: str

class InputData(BaseModel):
    physical_stats: PhysicalStats
    dietary_restrictions: DietaryRestrictions
    exercise: Exercise

class MacroPlan(BaseModel):
    calories: Dict[str, int]
    protein: float
    carbohydrates: Dict[str, float]
    fat: Dict[str, float]
    weekly_summary: Dict[str, float]
    food_sources: Dict[str, List[str]]
    practical_tips: List[str]

class GeminiOutput(BaseModel):
    macro_plan: MacroPlan

# Function to generate prompt
def generate_prompt(input_data: InputData) -> str:
    return f"""
    Please generate a detailed macro plan for a {input_data.dietary_restrictions.restrictions[0]} {input_data.physical_stats.gender}, aged {input_data.physical_stats.age}, 
    with a height of {input_data.physical_stats.height_cm} cm and a weight of {input_data.physical_stats.weight_kg} kg. The individual has a "{input_data.physical_stats.activity_level}" lifestyle, 
    exercising {input_data.exercise.weekly_hours} hours per week with {input_data.exercise.intensity} intensity, focusing on {input_data.exercise.exercise_type}. The goal is {input_data.physical_stats.goal}.

    Please include the following details in the output:

    1. Calories:
       - Calculate the Total Daily Energy Expenditure (TDEE) and suggest a calorie intake for maintenance.
       - Recommend a daily calorie surplus for muscle gain, specifying a range.

    2. Macros:
       - Protein: Provide the daily protein intake in grams, based on 1.6-2.2 grams per kilogram of body weight.
       - Carbohydrates: Suggest the daily carbohydrate intake, including a ratio of carbohydrates to protein.
       - Fat: Recommend daily fat intake in grams, with a range based on 0.3-0.5 grams per kilogram of body weight.

    3. Weekly Summary:
       - Calculate and provide a summary of the weekly macro totals for calories, protein, carbohydrates, and fat.

    4. Food Sources:
       - Suggest vegan food sources rich in protein, carbohydrates, and healthy fats.
       - Provide portion sizes for these foods to help meet daily macro goals.

    5. Practical Tips:
       - Offer practical advice for tracking intake, prioritizing whole foods, staying hydrated, and making adjustments based on how the individual feels.
    
    Encapsulate your response as a JSON Structure based on this pydantic model:
    class MacroPlan(BaseModel):
    calories: Dict[str, int] = Field(..., description="Caloric intake recommendations")
    protein: float = Field(..., description="Daily protein intake in grams")
    carbohydrates: Dict[str, float] = Field(..., description="Daily carbohydrate intake in grams and ratio")
    fat: Dict[str, float] = Field(..., description="Daily fat intake in grams with a range")
    weekly_summary: Dict[str, float] = Field(..., description="Weekly totals for calories, protein, carbohydrates, and fat")
    food_sources: Dict[str, List[str]] = Field(..., description="Recommended vegan food sources")
    practical_tips: List[str] = Field(..., description="Tips for tracking, prioritizing foods, hydration, and adjustments")
    """

# Function to interact with Gemini API and structure the output
def get_gemini_output(api_key: str, input_json: Dict) -> GeminiOutput:
    # Configure the Gemini API
    genai.configure(api_key=api_key)

    # Parse the input JSON into the Pydantic model
    input_data = InputData(**input_json)

    # Generate the prompt
    prompt = generate_prompt(input_data)

    # Call the Gemini API and get the response as text
    model = genai.GenerativeModel('gemini-1.5-pro')
    response = model.generate_content(prompt)

    # Extract the text content from the response
    response_text = response.text
    print(response_text)
    # Convert the response text to a JSON structure
    # response_json = json.loads(response_text)

    # Convert the API response into our structured output
    # macro_plan = MacroPlan(**response_json)

    # return GeminiOutput(macro_plan=macro_plan)

# Example usage
api_key = "AIzaSyAUMPfeEbTPOEiRMh5S1aaeqhvzn40_FIw"
input_json = {
    "physical_stats": {"height_cm": 195, "weight_kg": 85.5, "age": 30, "gender": "male", "activity_level": "very active", "goal": "muscle gain"},
    "dietary_restrictions": {"restrictions": ["vegan"]},
    "exercise": {"weekly_hours": 6.0, "intensity": "high", "exercise_type": "cardio and strength training"}
}

output = get_gemini_output(api_key, input_json)

# Print the structured output
print(output.json(indent=4))
