# Company Logo

Place your company logo file in this directory with the name:
**`company-logo.png`**

## Recommended Specifications:
- **Format**: PNG with transparent background (or JPG/JPEG)
- **Dimensions**: 
  - Width: 150-180 pixels
  - Height: 50-60 pixels
  - Aspect ratio: Approximately 3:1 (landscape)
- **File Size**: Under 200KB for optimal PDF generation
- **Resolution**: 72-150 DPI (suitable for digital/PDF use)

## Supported Formats:
- `.png` (recommended - supports transparency)
- `.jpg` or `.jpeg`
- `.svg` (may need additional configuration)

## How to Add Your Logo:
1. Save your logo file as `company-logo.png` 
2. Place it in this directory (`static/images/`)
3. The logo will automatically appear on:
   - Invoice PDFs (top right corner)
   - Estimate PDFs (top right corner)

## Note:
If you want to use a different filename or format, update the templates:
- `templates/invoices/invoice_preview.html`
- `templates/invoices/estimate_preview.html`
- `templates/invoices/preview.html`

Change this line:
```html
<img src="{% static 'images/company-logo.png' %}" alt="Company Logo" class="company-logo">
```

To match your filename, for example:
```html
<img src="{% static 'images/my-logo.jpg' %}" alt="Company Logo" class="company-logo">
```
