from huggingface_hub import InferenceClient
from utils.config import HF_TOKEN

client = InferenceClient(token=HF_TOKEN)

def generate_response(prompt):
    output = client.text_generation(model="meta-llama/Llama-2-7b-chat-hf", inputs=prompt, max_new_tokens=200)
    # HF returns a list with 'generated_text'
    if isinstance(output, list) and "generated_text" in output[0]:
        return output[0]["generated_text"]
    return str(output)
