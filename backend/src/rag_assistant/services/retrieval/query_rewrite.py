from rag_assistant.generation.llm_client import LLMError, MODEL_NAME, rewrite_userQuery

REWRITE_SYSTEM_PROMPT=(
    "Rewrite for searching internal policy documents. Keep the same meaning. Do not answer. "
    "One short question only. Prefer clear words for the topic (e.g. leave, time off, vacation days). "
    "Do not use account, balance, or payroll wording unless the user asked about pay."
)
TEMPERATURE=0.3
MAX_OUTPUT_TOKENS=60

def rewrite_query(question:str)->str | None:
    try:
        result=rewrite_userQuery(
            model_name=MODEL_NAME,
            temperature=TEMPERATURE,
            max_output_tokens=MAX_OUTPUT_TOKENS,
            userQuery=question,
            rewrite_system_prompt=REWRITE_SYSTEM_PROMPT,
        )
    except LLMError:
        return None
    text=result.new_userQuery.strip()
    return text or None
