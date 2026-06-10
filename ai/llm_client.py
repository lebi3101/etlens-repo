import os
import requests
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"


class OllamaClient:
    def generate(self, prompt: str) -> str:
        try:
            if not GROQ_API_KEY:
                return "Error: GROQ_API_KEY not found in environment variables."

            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1000,
                "temperature": 0.3
            }
            response = requests.post(
                GROQ_URL,
                headers=headers,
                json=payload,
                timeout=30
            )
            result = response.json()

            if "choices" in result:
                return result["choices"][0]["message"]["content"]
            else:
                return f"Error from Groq: {result}"

        except requests.exceptions.Timeout:
            return "Error: Request timed out. Please try again."
        except Exception as e:
            return f"Error generating response: {str(e)}"

# This function exists so other files can import it directly
def query_llm(prompt: str, system_prompt: str = None) -> str:
    try:
        if not GROQ_API_KEY:
            return "Error: GROQ_API_KEY not found in environment variables."

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": GROQ_MODEL,
            "messages": messages,
            "max_tokens": 1000,
            "temperature": 0.3
        }
        response = requests.post(
            GROQ_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        result = response.json()

        if "choices" in result:
            return result["choices"][0]["message"]["content"]
        else:
            return f"Error from Groq: {result}"

    except requests.exceptions.Timeout:
        return "Error: Request timed out. Please try again."
    except Exception as e:
        return f"Error generating response: {str(e)}"

if __name__ == "__main__":
    client = OllamaClient()
    result = client.generate(
        "What is an ETL script? Answer in 2 sentences."
    )
    print(result)