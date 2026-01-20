# Estimate & Invoice System - Data Flow Guide

## 📝 Summary Field with Rich Text Editor

The **Summary** field now uses **Quill Rich Text Editor** for formatted content:

### Features:
- ✅ Bold, italic, underline formatting
- ✅ Numbered and bulleted lists
- ✅ Clean HTML output
- ✅ Easy to use WYSIWYG interface

### How It Works:
1. **In the Form**: You see a rich text editor where you can format text
2. **Behind the Scenes**: The HTML is stored in the database
3. **In the Preview/PDF**: The HTML is rendered with proper formatting

## 📊 Line Items Table - Data Flow

### Where Items Come From:
The table with **Description | Price | Quantity | GST % | Amount** comes from:

1. **Form Input** (`estimate_form.html`):
   - You add items using the "+ Add New Item" button
   - Each item has:
     - Description (textarea)
     - Price (unit_price)
     - Quantity
     - GST Rate (%)

2. **Submitted to Views** (`views.py`):
   ```python
   # Views collect items from form POST data
   for i in range(item_count):
       desc = request.POST.get(f"item_{i}_description")
       qty = request.POST.get(f"item_{i}_quantity")
       price = request.POST.get(f"item_{i}_unit_price")
       gst = request.POST.get(f"item_{i}_gst_rate")
       # Calculate amount = (price * qty) * (1 + gst/100)
   ```

3. **Saved to Database**:
   - `EstimateItem` model stores each line item
   - Related to the `Estimate` via foreign key
   - Properties calculate totals automatically

4. **Displayed in Preview** (`estimate_preview.html`):
   ```html
   {% for item in estimate.items %}
       <tr>
           <td>{{ item.description }}</td>
           <td>{{ item.unit_price }}</td>
           <td>{{ item.quantity }}</td>
           <td>{{ item.gst_rate }}</td>
           <td>{{ item.line_total_inc_gst }}</td>
       </tr>
   {% endfor %}
   ```

5. **Rendered in PDF**:
   - WeasyPrint converts the HTML table to PDF
   - Maintains all styling and formatting

## 🔄 Complete Data Flow

```
Form (User Input)
    ↓
JavaScript collects items
    ↓
POST to Django View
    ↓
View processes & saves to DB
    ↓
Template renders data
    ↓
WeasyPrint generates PDF
```

## 💡 Key Points

### Item Table Columns:
- **Description**: From `item.description` (can be long text)
- **Price**: From `item.unit_price` (per unit)
- **Quantity**: From `item.quantity` (number of units)
- **GST %**: From `item.gst_rate` (e.g., 10 for 10%)
- **Amount**: Calculated as `quantity × price × (1 + gst_rate/100)`

### Calculations:
- **Subtotal**: Sum of all `(quantity × price)`
- **GST Total**: Sum of all `(quantity × price × gst_rate/100)`
- **Grand Total**: `Subtotal + GST Total`

### HTML Editor Benefits:
- No need to manually write HTML tags
- Professional formatting for summaries and terms
- Clean output for PDF generation
- User-friendly interface

## 🎯 Example

If you add an item:
- Description: "Drafting services"
- Price: 25
- Quantity: 63
- GST: 10%

The table shows:
- Description: "Drafting services"
- Price: 25
- Quantity: 63
- GST %: 10
- Amount: 1732.50 (calculated: 25 × 63 × 1.10)
