from validate_email_address import validate_email
from fastapi import HTTPException

def validate_email_address(email:str)->bool:
  try:
    is_valid=validate_email(email,verify=True)
  except Exception as e:
    raise HTTPException(status_code=500, detail=f"Email validation service error: {str(e)}")
  return is_valid