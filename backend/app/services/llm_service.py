import os
from openai import OpenAI
from openai.types.chat import ChatCompletionUserMessageParam
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def choose_best_mapping(source_column, candidates, knowledge=None):

    knowledge_text = "\n".join(knowledge) if knowledge else "None"

    prompt = f"""
    You are a financial data mapping expert.

    Source column: "{source_column}"

    Candidate target columns:
    {candidates}

    Additional domain knowledge:
    {knowledge_text}

    IMPORTANT RULES:
    - The source column may be an abbreviation.
    - You MUST use domain knowledge to interpret abbreviations correctly.
    - If domain knowledge suggests a better match, IGNORE the candidates.
    - Do NOT blindly choose from candidates.

    Example:
    - "Acct No" means "Account Number"

    Task:
    Select the BEST semantic match for the source column.

    Return ONLY the correct target column name.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            ChatCompletionUserMessageParam(
                role="user",
                content=prompt
            )
        ],
        temperature=0
    )

    return response.choices[0].message.content.strip()