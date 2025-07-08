import os
from openai import OpenAI
from typing import Optional

class AIQueryProcessor:
    def __init__(self):
        # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # do not change this unless explicitly requested by the user
        self.model = "gpt-4o"
        self.openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def extract_variable_name(self, query: str) -> Optional[str]:
        """Extract SDTM variable name from natural language query"""
        try:
            messages = [
                {
                    "role": "system",
                    "content": """You are a CDISC SDTM expert. Extract the SDTM variable name from the query.
                    Follow these rules:
                    1. Return only the variable name in uppercase
                    2. If multiple variables are mentioned, return the first one
                    3. If no variable is found, return empty string
                    4. Remove any '--' prefix from variable names
                    5. Common SDTM variables end in TESTCD, CAT, TEST, etc.
                    """
                },
                {"role": "user", "content": query}
            ]

            response = self.openai.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=10,
                temperature=0
            )

            variable_name = response.choices[0].message.content.strip()
            # Remove any potential '--' prefix
            variable_name = variable_name.replace('--', '')
            return variable_name if variable_name else None

        except Exception as e:
            print(f"Error processing AI query: {str(e)}")
            return None
