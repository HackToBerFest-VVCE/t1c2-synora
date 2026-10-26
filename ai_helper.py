
import requests


def get_bill_insights(bill_details):
    """Generate AI-powered electricity bill insights using Ollama."""

    prompt = f"""
    You are BillSense, an electricity bill analysis assistant.

    Analyze these electricity bill details:
    {bill_details}

    Provide:
    1. A simple explanation of the bill change.
    2. Possible reasons for an increase or decrease.
    3. Three practical electricity-saving suggestions.

    Important:
    - Use only the information provided.
    - Do not invent readings, amounts, or facts.
    - Clearly label possible reasons as possibilities.
    - Keep the response simple and concise.
    """

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "qwen2.5:3b",
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )

        response.raise_for_status()
        result = response.json()

        return result.get(
            "response",
            "The AI did not return a response."
        )

    except requests.exceptions.RequestException as error:
        return (
            "Unable to connect to the AI model. "
            "Please check whether Ollama is running. "
            f"Details: {error}"
        )
