export interface RecipeRequest {
  itemIds: string[];
  modifiers?: {
    servings?: number;
    flavorAdjustments?: string[];
    removeItems?: string[];
    overrides?: string[];
  };
}

export interface RecipeResponse {
  recipe: any;
}
