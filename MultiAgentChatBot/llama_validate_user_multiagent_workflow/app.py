import gradio as gr
from agents.orchestrator import handle_user

def chatbot_interface(email, name, info, code, delete_request):
    delete_flag = delete_request.lower() == "yes"
    reply = handle_user(email, name, info, input_code=code if code else None, delete_request=delete_flag)
    return reply

with gr.Blocks() as demo:
    gr.Markdown("# Multi-Agent LLaMA Chatbot on HF Spaces")
    email = gr.Textbox(label="Email")
    name = gr.Textbox(label="Name")
    info = gr.Textbox(label="Your Info / Message")
    code = gr.Textbox(label="OTP Code (if received)")
    delete_request = gr.Textbox(label="Delete user? (yes/no)")
    output = gr.Textbox(label="Chatbot Reply")
    submit = gr.Button("Send")

    submit.click(chatbot_interface, inputs=[email, name, info, code, delete_request], outputs=[output])

demo.launch()
