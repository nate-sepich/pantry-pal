export interface InventoryItemMacros {
  calories?: number;
  protein?: number;
  carbohydrates?: number;
  fiber?: number;
  sugar?: number;
  fat?: number;
  saturated_fat?: number;
  polyunsaturated_fat?: number;
  monounsaturated_fat?: number;
  trans_fat?: number;
  cholesterol?: number;
  sodium?: number;
  potassium?: number;
  vitamin_a?: number;
  vitamin_c?: number;
  calcium?: number;
  iron?: number;
}

export interface InventoryItem {
  id: string;
  user_id?: string;
  product_name: string;
  quantity?: number;
  upc?: string;
  macros?: InventoryItemMacros;
  cost?: number;
  expiration_date?: string;
  environmental_impact?: number;
  image_url?: string | null;
  imageUrl?: string | null;
  active: boolean;
}
