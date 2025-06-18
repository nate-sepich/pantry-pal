import { InventoryItem } from './InventoryItem';

export interface RecipeIngredient {
  item: InventoryItem;
  quantity: number;
}

export interface Recipe {
  id: string;
  name: string;
  ingredients: RecipeIngredient[];
  servings: number;
  image_url?: string | null;
}
