import React, { createContext, useState, useContext, ReactNode } from 'react';

// Define the context type
export interface PantryContextType {
  pantryItems: string[];
  addItem: (item: string) => void;
  removeItem: (item: string) => void;
}

// Create the context
const PantryContext = createContext<PantryContextType | undefined>(undefined);

// Define the provider component
export const PantryProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [pantryItems, setPantryItems] = useState<string[]>([]);

  const addItem = (item: string) => {
    setPantryItems((prevItems) => [...prevItems, item]);
  };

  const removeItem = (item: string) => {
    setPantryItems((prevItems) => prevItems.filter((i) => i !== item));
  };

  return (
    <PantryContext.Provider value={{ pantryItems, addItem, removeItem }}>
      {children}
    </PantryContext.Provider>
  );
};

// Custom hook to use the pantry context
export const usePantry = () => {
  const context = useContext(PantryContext);
  if (!context) {
    throw new Error('usePantry must be used within a PantryProvider');
  }
  return context;
};