from transformers import AutoTokenizer, AutoModelForCausalLM

# tokenizer = AutoTokenizer.from_pretrained('meta-llama/Llama-2-7b-hf')
# model = AutoModelForCausalLM.from_pretrained('meta-llama/Llama-2-7b-hf')

tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-2-70b-chat-hf")
model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-2-70b-chat-hf")

# tokenizer = AutoTokenizer.from_pretrained("PisutDeekub/LLAMA3-CHATBOT-PJ")
# model = AutoModelForCausalLM.from_pretrained("PisutDeekub/LLAMA3-CHATBOT-PJ")

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
    inputs = await tokenizer(input_text, return_tensors="pt")
    outputs = await model.generate(**inputs, max_length = 200)
    response = await tokenizer.decode(outputs[0], skip_special_tokens = True)

    if "not available" not in response and not any(keyword in response for keyword in context.split()):
        response = "The information is not available in the context."
    
    return response

print(generate_response(
        "How old are you?", 
            [
                {
                    'id': '8a7e5227-a738-4422-9c25-9a6136825803',
                    'metadata': {'Header 2': 'Introduction',
                                'text': '## Introduction  \n'
                                        'Hi, I am Robel Lager from the Phoenix, AZ. I am a senior software engineer with 10 years of experience.'},
                    'score': 1.0080868,
                    'values': [
                        -0.00798303168,
                        0.00551192369,
                        -0.00463955849,
                        -0.00585730933,
                        ...
                    ]
                }
            ]
        )
    )