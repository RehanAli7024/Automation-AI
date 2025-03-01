from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pydantic import BaseModel
from typing import Dict, Optional, List
import logging
import traceback
import time
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Google Form Automation API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class FormField(BaseModel):
    question_text: str
    field_type: str
    required: bool = False

class FormData(BaseModel):
    form_url: str
    form_fields: Dict[str, str]

def setup_driver():
    """Setup and return a Chrome WebDriver configured for Render"""
    try:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--remote-debugging-port=9222')
        
        if os.environ.get('RENDER'):
            chrome_options.binary_location = "/usr/bin/chromium-browser"
        
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        logger.error(f"Failed to setup driver: {str(e)}")
        logger.error(traceback.format_exc())
        raise Exception(f"Failed to initialize Chrome driver: {str(e)}")

@app.post("/extract-form-fields")
async def extract_form_fields(form_url: str = Query(..., description="The Google Form URL to extract fields from")):
    """Extract form fields from a Google Form"""
    logger.info(f"Attempting to extract fields from form: {form_url}")
    driver = None
    try:
        driver = setup_driver()
        logger.info("Chrome driver setup successful")
        
        driver.get(form_url)
        logger.info("Navigated to form URL")
        
        # Wait for form to load
        time.sleep(5)
        
        form_fields = {}
        
        # Extract name field
        name_input = driver.find_element(By.CSS_SELECTOR, 'input[aria-labelledby]')
        name_label = driver.find_element(By.CSS_SELECTOR, 'div[role="heading"][aria-describedby] span.M7eMe').text
        form_fields[name_label] = {
            "type": "text",
            "required": True
        }
        logger.info(f"Found name field: {name_label}")
        
        # Extract all questions
        questions = driver.find_elements(By.CSS_SELECTOR, 'div[role="listitem"]')
        logger.info(f"Found {len(questions)} questions")
        
        for index, question in enumerate(questions):
            try:
                question_text = question.find_element(By.CSS_SELECTOR, 'span.M7eMe').text
                
                # Determine field type
                if question.find_elements(By.CSS_SELECTOR, 'div[role="radiogroup"]'):
                    # Get radio options
                    radio_group = question.find_element(By.CSS_SELECTOR, 'div[role="radiogroup"]')
                    options = radio_group.find_elements(By.CSS_SELECTOR, 'div[role="radio"]')
                    option_values = [opt.get_attribute('data-value') for opt in options]
                    
                    form_fields[question_text] = {
                        "type": "radio",
                        "options": option_values,
                        "required": True
                    }
                
                logger.info(f"Processed question {index + 1}: {question_text}")
                
            except Exception as e:
                logger.error(f"Error processing question {index + 1}: {str(e)}")
                logger.error(traceback.format_exc())
                continue
        
        if driver:
            driver.quit()
        logger.info("Successfully extracted all form fields")
        return {"fields": form_fields}
    
    except Exception as e:
        logger.error(f"Error extracting form fields: {str(e)}")
        logger.error(traceback.format_exc())
        if driver:
            driver.quit()
        raise HTTPException(status_code=500, detail=f"Failed to extract form fields: {str(e)}")

@app.post("/fill-form")
async def fill_form(form_data: FormData):
    """Fill a Google Form with provided data"""
    logger.info(f"Attempting to fill form: {form_data.form_url}")
    driver = None
    try:
        driver = setup_driver()
        driver.get(form_data.form_url)
        time.sleep(5)  # Wait for form to load
        
        # Fill name field
        name_input = driver.find_element(By.CSS_SELECTOR, 'input[aria-labelledby]')
        name_label = driver.find_element(By.CSS_SELECTOR, 'div[role="heading"][aria-describedby] span.M7eMe').text
        if name_label in form_data.form_fields:
            name_input.send_keys(form_data.form_fields[name_label])
            logger.info(f"Filled name field: {form_data.form_fields[name_label]}")
        
        # Fill other questions
        questions = driver.find_elements(By.CSS_SELECTOR, 'div[role="listitem"]')
        for question in questions:
            try:
                question_text = question.find_element(By.CSS_SELECTOR, 'span.M7eMe').text
                if question_text in form_data.form_fields:
                    # Handle radio buttons
                    if question.find_elements(By.CSS_SELECTOR, 'div[role="radiogroup"]'):
                        radio_group = question.find_element(By.CSS_SELECTOR, 'div[role="radiogroup"]')
                        value = form_data.form_fields[question_text].lower()
                        radio = radio_group.find_element(By.CSS_SELECTOR, f'div[role="radio"][data-value="{value}"]')
                        radio.click()
                        logger.info(f"Selected radio option '{value}' for question: {question_text}")
            
            except Exception as e:
                logger.error(f"Error filling field {question_text}: {str(e)}")
                continue
        
        # Submit form
        submit_button = driver.find_element(By.XPATH, '//div[@role="button"]//span[text()="Submit"]')
        submit_button.click()
        time.sleep(3)  # Wait for submission
        
        if driver:
            driver.quit()
        return {"message": "Form submitted successfully"}
    
    except Exception as e:
        logger.error(f"Error filling form: {str(e)}")
        if driver:
            driver.quit()
        raise HTTPException(status_code=500, detail=f"Failed to fill form: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
