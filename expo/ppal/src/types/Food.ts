export enum FoodCategory {
  DAIRY = 'dairy',
  MEAT = 'meat',
  SEAFOOD = 'seafood',
  CARBS = 'carbs',
  FATS = 'fats',
  VEGETABLES = 'vegetables',
  FRUITS = 'fruits',
  BEVERAGES = 'beverages',
  OTHER = 'other',
}

export interface FoodSuggestion {
  name: string;
  fdc_id?: string;
  category: FoodCategory;
}
