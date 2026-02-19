import phonenumbers
from phonenumbers import PhoneNumberFormat, NumberParseException

def validate_and_format_egypt_phone(phone_str):
    """
    Standardizes Egyptian numbers (Landline & Mobile) to +20 international format.
    Returns: (Formatted Number, Is_Valid_Boolean, Line_Type)
    """
    if not phone_str:
        return None, False, "Unknown"

    try:
        # Parse specifically for Egypt
        parsed_number = phonenumbers.parse(phone_str, "EG")

        # Check if the number is valid
        is_valid = phonenumbers.is_valid_number(parsed_number)
        
        if not is_valid:
            return phone_str, False, "Invalid"

        # Determine if it's a mobile or a landline
        type_info = phonenumbers.number_type(parsed_number)
        line_type = "Mobile" if type_info == phonenumbers.PhoneNumberType.MOBILE else "Landline"

        # Standardize to international
        formatted = phonenumbers.format_number(parsed_number, PhoneNumberFormat.E164)
        
        return formatted, True, line_type

    except NumberParseException:
        return phone_str, False, "Error"