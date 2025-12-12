import os
import json
import requests
from dotenv import load_dotenv
from pypdf import PdfReader
import gradio as gr
from openai import OpenAI

# Load local .env (ignored on HF Spaces)
load_dotenv(override=True)

# ------------------ Helper functions ------------------
def push(msg):
    """Send a message via Pushover."""
    token = os.getenv("PUSHOVER_TOKEN")
    user = os.getenv("PUSHOVER_USER")
    if not token or not user:
        print("Pushover token/user not set, skipping push")
        return
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={"token": token, "user": user, "message": msg}
    )

def record_contact(name, email, enquiry):
    push(f"Contact: {name}, {email}, enquiry: {enquiry}")
    return {"recorded": "ok"}

def record_unknown_enquiry(enquiry):
    push(f"Unknown enquiry: {enquiry}")
    return {"recorded": "ok"}

tools = [{"type": "function", "function": record_contact},
        {"type": "function", "function": record_unknown_enquiry}]
# ------------------ Bot class ------------------
class Ankita:
    def __init__(self):
        self.name = "Ankita Suman"

        # Load LinkedIn profile from PDF safely
        self.linkedin = ""
        pdf_path = os.path.join("/me", "Profile.pdf")
        if os.path.exists(pdf_path):
            try:
                reader = PdfReader(pdf_path)
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        self.linkedin += text
            except Exception as e:
                print(f"Error reading PDF {pdf_path}: {e}")
        else:
            print(f"{pdf_path} not found. LinkedIn profile will be empty.")

        # Load summary safely
        self.summary = ""
        summary_path = os.path.join("/me", "summary.txt")
        if os.path.exists(summary_path):
            try:
                with open(summary_path, "r", encoding="utf-8") as f:
                    self.summary = f.read()
            except Exception as e:
                print(f"Error reading summary {summary_path}: {e}")
        else:
            print(f"{summary_path} not found. Summary will be empty.")

        # Initialize OpenAI client
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError(
                "DeepSeek OpenAI API key not found. Set OPENAI_API_KEY in .env or HF Secrets."
            )
        self.openai = OpenAI(api_key=os.environ.get('DEEPSEEK_API_KEY'), base_url="https://api.deepseek.com")

    def handle_tool_calls(self, tool_calls):
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name}", flush=True)
            tool = globals().get(tool_name)
            result = tool(**arguments) if tool else {}
            results.append({"role": "tool","content": json.dumps(result),"tool_call_id": tool_call.id})
        return results

    # ------------------ System prompt ------------------
    def system_prompt(self):
        prompt = (
            f"You are acting as {self.name}. You answer questions about "
            f"{self.name}'s career, background, skills, and experience. "
            "If you don't know the answer, record it using the record_unknown_enquiry tool. "
            "Encourage users to get in touch via email."
        )
        prompt += f"\n\n## Summary:\n{self.summary}\n\n## LinkedIn Profile:\n{self.linkedin}\n"
        return prompt

    def chat(self, message, history=[]):
    # Start with system prompt
        messages = [{"role": "system", "content": self.system_prompt()}]
        done = False
        while not done:
    # Convert Gradio history (list of tuples) into OpenAI messages
            for user_msg, bot_msg in history:
                messages.append({"role": "user", "content": user_msg})
                messages.append({"role": "assistant", "content": bot_msg})
            messages.append({"role": "user", "content": message})
            response = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=tools,
            )
            finish_reason = response.choices[0].finish_reason
            if finish_reason == "stop":
                done = True
            else:
                messages.append(response.choices[0].message)
        return messages
# ------------------ Gradio interface ------------------
if __name__ == "__main__":
    me = Ankita()
    gr.ChatInterface(me.chat).launch()