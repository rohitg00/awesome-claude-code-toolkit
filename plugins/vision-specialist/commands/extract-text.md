Extract text content from images, screenshots, or diagrams for processing and analysis.

## Steps


1. Load the image using the Read tool to examine it visually.
2. Identify text regions in the image:
3. Extract text maintaining structure:
4. Handle special content:
5. Clean up the extracted text:
6. Format the output for the intended use:

## Format


```
Source: <image path>
Text Regions Found: <count>
Extracted Content:
  [Header] <text>
```


## Rules

- Preserve the original structure and hierarchy of the text.
- Flag text that is unclear or ambiguous with low confidence.
- Maintain code formatting exactly as shown in the image.

