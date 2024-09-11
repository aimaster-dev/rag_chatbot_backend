from transformers import AutoTokenizer, AutoModelForCausalLM
import re

tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-2-7b-chat-hf")
model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-2-7b-chat-hf")

async def generate_response(query: str, documents: list):
    context = ""
    for doc in documents:
        context += doc["metadata"]["text"] + "\n"
    input_text = f"""
    Use the following pieces of information to answer the user's question.
    If you don't know the answer, just say that you don't know, don't try to make up an answer.
    Context: {context}
    Question: {query}
    
    Only return the helpful answer below and nothing else.
    Helpful answer:
    """
    inputs = tokenizer(input_text, return_tensors="pt")
    outputs = model.generate(**inputs, max_length = 200)
    response = tokenizer.decode(outputs[0], skip_special_tokens = True)

    pattern = r"Helpful answer:\s*(.*)"
    match = re.search(pattern, response)

    if match:
        response = match.group(1).strip()

    if "not available" not in response and not any(keyword in response for keyword in context.split()):
        response = "The information is not available in the context."
    
    return response