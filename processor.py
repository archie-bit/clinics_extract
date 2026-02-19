from google import genai
from google.genai import types
import json
import os
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from clean_phonenum import validate_and_format_egypt_phone

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)


# @retry(
#     stop=stop_after_attempt(3),
#     wait=wait_exponential(multiplier=2, min=5, max=30),
#     before_sleep=lambda retry_state: print(f"Rate limited. Retrying in {retry_state.next_action.sleep}s...")
# )
def filter_clinics_batch(business_list):
    """
    Takes a list of business dictionaries and returns only the ones
    that pass the 'Private Clinic' criteria.
    """
    if not business_list:
        return []

    # Prepare a simple numbered list of names for the LLM
    input_data = "\n".join([f"{i}. {b['clinic_name']}" for i, b in enumerate(business_list)])

    prompt = f"""
    You are an expert Egyptian medical directory auditor. 
    Analyze the following list of medical entity names: {json.dumps(input_data)}

    STRICT FILTERING RULES:
    1. KEEP: Only Solo/Group Private Clinics (Iyada). 
       Note: "Dr. [Name] Center" is usually a private clinic. 
    2. DISCARD: Hospitals (Mustashfa), Multi-specialty Corporate Centers (e.g., "Cairo Medical Center"), Labs (Ma3mal), and Pharmacies.

    TASK:
    - Determine if we should KEEP or DISCARD.
    - If KEEP: Extract the 'doctor_name' from the clinic title if a personal name is present.
    - Assign a 'confidence_score': 
        - High: Explicitly "Clinic" or "Dr. [Name]".
        - Medium: "Center" but associated with a single doctor's name.
        - Low: Ambiguous names.

    OUTPUT FORMAT:
    Return a JSON object where the key is the 'id' and the value is an object:
    {{"0": {{"decision": "KEEP", "doctor_name": "Ahmed", "confidence_score": "High"}}, ...}}
    Respond ONLY with JSON.
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type='application/json', # <--- Forces valid JSON
            )
        )
        ai_decisions = json.loads(response.text)
        # Clean potential markdown wrapping
        # json_str = response.text.replace('```json', '').replace('```', '').strip()
        # ai_decisions = json.loads(json_str)

        final_leads = []
        for i, raw_biz in enumerate(business_list):
            final_number, is_valid, line_type = validate_and_format_egypt_phone(raw_biz['phone_number'])
            if is_valid:
                raw_biz['phone_number'] = final_number
                raw_biz['line_type'] = line_type  # Adds a "Landline" or "Mobile" column
            else:
                # If the number is garbage, manually check
                raw_biz['phone_number'] = "Manual Check Required"

            decision_data = ai_decisions.get(str(i))
            # if decision_data and decision_data['decision'] == "KEEP":
            if decision_data:
                # Merge original data with AI-extracted data
                raw_biz['doctor_name'] = decision_data.get('doctor_name', '')
                raw_biz['confidence_score'] = decision_data.get('confidence_score', 'Low')
                raw_biz['decision'] = decision_data.get('decision', '')
                
                # # Clean Phone Number
                # raw_biz['phone_number'] = clean_phone(raw_biz['phone_number'])
                final_leads.append(raw_biz)
        
        return final_leads

    except Exception as e:
        print(f"AI Processing Error: {e}")
        return []