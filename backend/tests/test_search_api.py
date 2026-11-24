from pathlib import Path
from fastapi.testclient import TestClient
from rag_assistant.main import app

client = TestClient(app) # calls the app directly (route, validation, controller) , it does not require the server to be started

def test_k_must_be_a_number()->None:
    response = client.post('/retrieve',json={"question":"leave policy","k":"five"})
    assert response.status_code==422 # our k value is not number so 422 error is expected
    assert response.json()["detail"][0]["loc"]==["body","k"] # the error names the field that was wrong

def test_k_must_be_at_least_1()->None:
    response = client.post('/retrieve',json={"question":"leave policy","k":0})
    assert response.status_code==422 # our k value is min 1, so 422 error is expected
    assert response.json()["detail"][0]["loc"]==["body","k"] # the error names the field that was wrong

def test_question_must_not_be_empty()->None:
    response = client.post('/retrieve',json={"question":""})
    assert response.status_code==422 # our question must not be empty, so 422 error is expected
    assert response.json()["detail"][0]["loc"]==["body","question"] # the error names the field that was wrong

def test_response_shape(temp_vector_store:Path)->None:
    # WHY TEMP VECTOR STORE HERE: the question and k are correct , so the request goes all the way to the chroma database , without the temp store it would use our real data
    # WHY NOT ABOVE: the other tests send a wrong question or k , so the request is rejected with 422 before it reaches the chroma database
    question="How many leaves can I take?"
    response = client.post('/retrieve',json={"question":question,"k":5})
    assert response.status_code==200
    assert response.json()["question"]==question # the question is echoed back
    assert response.json()["results"]==[] # the temp store is empty , search_chunks returns [] before loading the model
