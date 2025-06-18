export interface Recipe {
  id: string;
  name: string;
  ingredients?: string[];
  instructions?: string | null;
  cook_time?: string | null;
  tags?: string[];
  image_url?: string | null;
}
