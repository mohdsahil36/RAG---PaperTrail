import pytest
from rag_assistant.services.ask_service import ask_question

# live Gemini calls — run with: pytest -m regression
# paraphrased questions (different wording, same meaning as eval_baseline CASES)
# assert found=True and the right section heading appears in sources

@pytest.mark.regression
@pytest.mark.parametrize("question,expected_heading", [
    ("How many days of paid time off do I get?", "Paid time off"),
    ("Do I receive additional pay for working overtime?", "Overtime"),
    ("What is the required notice period when I want to leave the company?", "Resignation"),
    ("Who should I contact if I experience harassment at work?", "Workplace harassment"),
], ids=[
    "annual_leave",
    "overtime",
    "resignation_notice",
    "harassment_contact",
])
def test_ask_returns_correct_source(question: str, expected_heading: str) -> None:
    result = ask_question(question, k=5, document_id="employee_handbook.pdf")
    assert result.found is True
    assert any(expected_heading in s.heading for s in result.sources)


@pytest.mark.regression
def test_remote_work_returns_correct_source() -> None:
    # two possible headings in the handbook: "Remote working" and "Work from home"
    result = ask_question("What is the company policy for working remotely?", k=5, document_id="employee_handbook.pdf")
    assert result.found is True
    headings = [s.heading for s in result.sources]
    assert any("emote" in h or "ork from home" in h for h in headings)


@pytest.mark.regression
def test_unrelated_question_returns_not_found() -> None:
    # handbook has no answer — service must return found=False, not hallucinate
    result = ask_question("What is the capital of France?", k=5, document_id="employee_handbook.pdf")
    assert result.found is False
    assert result.sources == []
