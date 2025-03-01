# Google Form Automation API

A FastAPI-based backend service for automating Google Form filling using Selenium.

## Features

- Extract form fields from any Google Form
- Automated form filling with provided data
- Support for different input types (text, radio buttons, checkboxes)
- Headless browser operation

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the server:
```bash
uvicorn app.main:app --reload
```

## API Endpoints

### 1. Extract Form Fields
- **Endpoint**: `/extract-form-fields`
- **Method**: POST
- **Parameters**: form_url (string)
- **Returns**: Dictionary of form fields and their types

### 2. Fill Form
- **Endpoint**: `/fill-form`
- **Method**: POST
- **Body**:
```json
{
    "form_url": "https://docs.google.com/forms/...",
    "form_fields": {
        "Question 1": "Answer 1",
        "Question 2": "Answer 2"
    }
}
```

### 3. Health Check
- **Endpoint**: `/health`
- **Method**: GET
- **Returns**: Service health status

## Notes
- The service runs Chrome in headless mode
- Make sure you have Chrome browser installed
- The webdriver is automatically managed and updated
