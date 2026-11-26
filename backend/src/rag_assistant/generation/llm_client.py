import os
from functools import lru_cache
from pathlib import Path
import httpx2
from dotenv import load_dotenv
from google import genai
from google.genai import errors, types
from pydantic import BaseModel

ENV_PATH=Path(__file__).resolve().parents[3]/".env" # path to backend/.env , works from any folder we run the code from
load_dotenv(ENV_PATH) # loads backend/.env into the environment , runs only once when the file is imported

MODEL_NAME=os.getenv("GEMINI_MODEL","gemini-3.5-flash-lite") # model name from .env , falls back to the default if .env does not have it
TEMPERATURE=0.3 # low value so the answers stay close to the passages
MAX_OUTPUT_TOKENS=500 # max length of the answer , around 2000 characters
TIMEOUT_MS=15_000 # how long one try waits for Gemini , 15 seconds
MAX_ATTEMPTS=2 # the SDK counts the first try too , so 1 call + 1 retry , around 30 seconds in the worst case
FALLBACK_MODEL_NAME=os.getenv("GEMINI_FALLBACK_MODEL","gemini-2.0-flash-lite")

# why not use AskResponse from ask_schema.py? LLMResponse is the answer the LLM sends , AskResponse is what the end user will receive from us
class LLMResponse(BaseModel):
    found:bool # false when the passages do not have the answer
    answer:str # the answer text with [n] citations in it
    citations:list[int] # passage numbers the answer used , e.g. [1, 3]

class RephraseResponse(BaseModel):
    questionVariants:list[str]

class DecompositionResponse(BaseModel):
    sub_questions:list[str]

class LLMRewriteResponse(BaseModel):
    new_userQuery:str

class LLMError(Exception):
    """Gemini failed: timeout, rate limit, server error, block, or a reply that does not match LLMResponse."""


@lru_cache(maxsize=1) # client is created on the first call only , after that every call gets the same client
def _get_client()->genai.Client:
    retry=types.HttpRetryOptions(
        attempts=MAX_ATTEMPTS,
        http_status_codes=[408,500,502,503,504] # retry only the errors that can fix themselves , 429 is not retried
    )
    return genai.Client( # picks up GEMINI_API_KEY from the environment
        http_options=types.HttpOptions(timeout=TIMEOUT_MS,retry_options=retry)
    )

def _call_with_fallback(fn):
    try:
        return fn(MODEL_NAME)
    except errors.APIError as e:
        if e.code not in (429, 404):
            raise LLMError(f"Primary model error {e.code}: {e.message}") from e
        if FALLBACK_MODEL_NAME is None:
            raise LLMError(f"Primary model returned {e.code} and no fallback model is configured") from e
        try:
            return fn(FALLBACK_MODEL_NAME)
        except errors.APIError as e2:
            raise LLMError(f"Fallback model error {e2.code}: {e2.message}") from e2
        except httpx2.RequestError as e2:
            raise LLMError("Fallback model did not reply (timeout or network)") from e2
    except httpx2.RequestError as e:
        raise LLMError("Primary model did not reply (timeout or network)") from e

def generate_answer(system_prompt:str,user_prompt:str)->LLMResponse:
    response = _call_with_fallback(
        lambda model_name: _get_client().models.generate_content(
            model=model_name, # wrapper picks the model (primary or fallback) and passes it as model_name — lambda receives it here and plugs it into the API call
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=TEMPERATURE,
                max_output_tokens=MAX_OUTPUT_TOKENS,
                response_mime_type="application/json",
                response_schema=LLMResponse,
            )
        )
    )
    if not isinstance(response.parsed,LLMResponse): # parsed is None when the reply is blocked , cut off or not valid JSON
        raise LLMError("Gemini reply is empty or does not match LLMResponse")
    return response.parsed


def rewrite_userQuery(model_name:str,temperature:float,max_output_tokens:int,userQuery:str,rewrite_system_prompt:str)->LLMRewriteResponse:
    # timeout / retries stay on shared _get_client ; only call-level knobs are parameters
    try:
        response=_get_client().models.generate_content(
            model=model_name,
            contents=userQuery,
            config=types.GenerateContentConfig(
                system_instruction=rewrite_system_prompt,
                temperature=temperature,
                max_output_tokens=max_output_tokens,
                response_mime_type="application/json",
                response_schema=LLMRewriteResponse,
            ),
        )
    except errors.APIError as e:
        raise LLMError(f"Gemini returned error {e.code}: {e.message}") from e
    except httpx2.RequestError as e:
        raise LLMError("No reply from Gemini (timeout or network)") from e
    if not isinstance(response.parsed,LLMRewriteResponse):
        raise LLMError("Gemini reply is empty or does not match LLMRewriteResponse")
    return response.parsed

_EXPAND_SYSTEM_PROMPT = "Given a search query, return 2 to 3 alternative phrasings that mean the same thing but use different words. Return only the variants as a JSON list."

def expand_userQuery(user_query:str)->RephraseResponse:
    response = _call_with_fallback(
        lambda model_name: _get_client().models.generate_content(
            model=model_name,
            contents=user_query,
            config=types.GenerateContentConfig(
                system_instruction=_EXPAND_SYSTEM_PROMPT,
                temperature=TEMPERATURE,
                max_output_tokens=MAX_OUTPUT_TOKENS,
                response_mime_type="application/json",
                response_schema=RephraseResponse,
            )
        )
    )
    if not isinstance(response.parsed, RephraseResponse):
        raise LLMError("Gemini reply is empty or does not match RephraseResponse")
    return response.parsed

_BREAK_QUESTION_SYSTEM_PROMPT="Break the following question into 2 to 3 independent sub-questions that together cover the full meaning. Each sub-question should be answerable on its own. Return only the sub-questions."

def break_userQuery(user_query:str)->DecompositionResponse:
    response = _call_with_fallback(
        lambda model_name: _get_client().models.generate_content(
            model=model_name,
            contents=user_query,
            config=types.GenerateContentConfig(
                system_instruction=_BREAK_QUESTION_SYSTEM_PROMPT,
                temperature=TEMPERATURE,
                max_output_tokens=MAX_OUTPUT_TOKENS,
                response_mime_type="application/json",
                response_schema=DecompositionResponse,
            )
        )
    )
    if not isinstance(response.parsed, DecompositionResponse):
        raise LLMError("Gemini reply is empty or does not match DecompositionResponse")
    return response.parsed

def stream_answer(system_prompt:str,user_prompt:str):
    # plain text pieces for /answer/stream — no JSON schema (unlike generate_answer)
    response = _call_with_fallback(
        lambda model_name: _get_client().models.generate_content_stream(
            model=model_name, # wrapper picks the model (primary or fallback) and passes it as model_name — lambda receives it here and plugs it into the API call
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=TEMPERATURE,
                max_output_tokens=MAX_OUTPUT_TOKENS,
            )
        )
    )
    for chunk in response:
        text=chunk.text
        if text: # skip empty deltas
            yield text

# what Gemini reads to know what tools exist — no Python code is exposed, only this schema
SEARCH_TOOL = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="search_documents",  # Gemini sends this exact string back in function_call.name
            description="Search the uploaded documents for passages relevant to the question. Always call this before answering.",  # Gemini reads this to decide whether to call the tool
            parameters=types.Schema(
                type=types.Type.OBJECT,  # top-level shape is always OBJECT when you have named args
                properties={
                    "query": types.Schema(
                        type=types.Type.STRING,
                        description="The search query derived from the user's question.",  # Gemini fills this — may rephrase the user's question for better retrieval
                    ),
                },
                required=["query"],  # Gemini must always provide a query — no empty calls
            ),
        )
    ]
)

def answer_with_tools(question: str) -> tuple[dict, types.Content]:
    # CALL 1 of the tool calling loop
    # sends the user question + SEARCH_TOOL to Gemini
    # Gemini does not answer — it returns a function_call with a better search query
    # returns: tool_args (the query Gemini chose) + model_content (Gemini's raw response)
    # model_content is passed unchanged into call 2 — rebuilding it loses the thought_signature Gemini embeds
    response = _call_with_fallback(
        lambda model_name: _get_client().models.generate_content(
            model=model_name, # wrapper picks the model (primary or fallback) and passes it as model_name — lambda receives it here and plugs it into the API call
            contents=question,
            config=types.GenerateContentConfig(
                temperature=TEMPERATURE,
                max_output_tokens=MAX_OUTPUT_TOKENS,
                tools=[SEARCH_TOOL],
                tool_config=types.ToolConfig(
                    function_calling_config=types.FunctionCallingConfig(mode=types.FunctionCallingConfigMode.ANY)  # ANY = Gemini must call a tool, cannot answer directly
                ),
            ),
        )
    )
    candidate = response.candidates[0] if response.candidates else None      # first (usually only) reply
    model_content = candidate.content if candidate else None                  # the full Content object — role=model, parts=[function_call]
    parts = model_content.parts if model_content else None                    # list of Part objects inside the response
    if not parts:
        raise LLMError("Gemini did not return a function_call on the first turn")
    fc_part = next((p for p in parts if p.function_call is not None), None)  # the Part that holds the function_call
    if fc_part is None or fc_part.function_call is None:
        raise LLMError("Gemini did not return a function_call on the first turn")
    tool_args = dict(fc_part.function_call.args or {})                        # e.g. {"query": "annual leave entitlement days"}
    return tool_args, model_content  # type: ignore[return-value]


def answer_with_tool_result_and_context(question: str, model_content: types.Content, tool_result: str, system_prompt: str) -> str:
    # CALL 2 of the tool calling loop
    # sends the full conversation history to Gemini so it has context to write the grounded answer:
    #   turn 1 (user)  — the original question
    #   turn 2 (model) — Gemini's call 1 response (model_content), passed as-is to preserve thought_signature
    #   turn 3 (user)  — our function_response carrying the retrieved passages (tool_result)
    # Gemini reads all three turns and writes the final plain-text answer with [n] citations
    contents = [
        types.Content(role="user", parts=[types.Part(text=question)]),
        model_content,  # original Content object from call 1 — not rebuilt; thought_signature intact
        types.Content(
            role="user",
            parts=[types.Part(function_response=types.FunctionResponse(
                name="search_documents",
                response={"result": tool_result},  # formatted passages string — what search_documents returned
            ))]
        ),
    ]
    try:
        response = _get_client().models.generate_content(
            model=MODEL_NAME,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,  # GROUNDING_RULES — answer only from passages
                temperature=TEMPERATURE,
                max_output_tokens=MAX_OUTPUT_TOKENS,
                tool_config=types.ToolConfig(
                    function_calling_config=types.FunctionCallingConfig(mode=types.FunctionCallingConfigMode.NONE)  # NONE = must answer in text, no more tool calls
                ),
            ),
        )
    except errors.APIError as e:
        raise LLMError(f"Gemini returned error {e.code}: {e.message}") from e
    except httpx2.RequestError as e:
        raise LLMError("No reply from Gemini (timeout or network)") from e
    candidate = response.candidates[0] if response.candidates else None
    parts = candidate.content.parts if (candidate and candidate.content) else None
    text = "".join(p.text for p in parts if p.text) if parts else ""  # join all text parts — response.text can be None for multi-part replies
    if not text:
        raise LLMError("Gemini returned an empty answer on the second turn")
    return text
