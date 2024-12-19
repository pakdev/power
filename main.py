from dataclasses import dataclass
import os
import tempfile
from pypdf import PdfReader
import requests
from openai import OpenAI


@dataclass
class Plan:
    uid: str
    equation: str
    efl_url: str
    tiered: int
    term: int
    company: str
    plan_name: str
    price_500kwh: float
    price_1000kwh: float
    price_2000kwh: float
    renewable_percentage: float


def get_plans(zip_code: int, include_tiered: bool = True) -> list[Plan]:
    url = "https://www.powertochoose.org/en-us/service/v1/"
    data = {
        "method": "plans",
        "zip_code": "78728",
        "estimated_use": 1000,
        "plan_type": "1, 2",  # 1. Fixed, 0: Variable, 2: Indexed
        "include_details": True,
        "min_usage_plan": "" if include_tiered else "off",
    }
    response = requests.post(url, json=data, verify=False)
    results = response.json()

    plans = []
    for result in results:
        equation = ""  #
        plans.append(
            Plan(
                result["company_unique_id"],
                equation,
                result["fact_sheet"],
                result["plan_type"],
                result["term_value"],
                result["company_name"],
                result["plan_name"],
                result["price_kwh500"],
                result["price_kwh1000"],
                result["price_kwh2000"],
                result["renewable_energy_description"],
            )
        )

    return plans


def get_efl(efl_url: str) -> str:
    response = requests.get(efl_url)
    if response.status_code == 200:
        temp_path = tempfile.NamedTemporaryFile().name
        with open(temp_path, "wb") as file:
            file.write(response.content)
        efl_pdf = PdfReader(temp_path)
        return str.join("", [p.extract_text() for p in efl_pdf.pages])
    else:
        raise Exception("Failed to download EFL")


def main():
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)
    plans = get_plans(78728)
    for plan in plans:
        efl = get_efl(plan.efl_url)
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": f"""
                    I need Python code that calculates the total cost of electricity 
                    for a given kwh usage that follows the following pricing model:
                    
                    {efl}

                    Please output only Python code so I can send it straight to the eval function.
                    """,
                }
            ],
            model="gpt-4o-mini",
        )
        print(response.choices[0].message.content)
        break


if __name__ == "__main__":
    main()
