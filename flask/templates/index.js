const express = require('express');
const app = express();
const port = 3000;
app.use(express.json());

let pantryItems = [];
let nextId = 1;

app.get('/pantry', (req, res) => {
  res.json(pantryItems);
});

app.post('/pantry', (req, res) => {
  const item = { id: nextId++, ...req.body };
  pantryItems.push(item);
  res.status(201).json(item);
});

app.put('/pantry/:id', (req, res) => {
  const { id } = req.params;
  const index = pantryItems.findIndex(item => item.id == id);
  if (index !== -1) {
    pantryItems[index] = { id: parseInt(id), ...req.body };
    res.json(pantryItems[index]);
  } else {
    res.status(404).send('Item not found');
  }
});

app.delete('/pantry/:id', (req, res) => {
  const { id } = req.params;
  pantryItems = pantryItems.filter(item => item.id != id);
  res.status(204).end();
});

app.listen(port, () => {
  console.log(`Server running on http://localhost:${port}`);
});