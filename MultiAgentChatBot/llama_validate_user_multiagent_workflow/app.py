import gradio as gr
import os
import uuid
from agents.orchestrator import handle_user
import redis
from utils.configs import REDIS_HOST,REDIS_PORT,REDIS_DB

# ------------------ Redis Setup ------------------


r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

SESSION_ID = str(uuid.uuid4())

# ------------------ Redis Cache Helpers ------------------
def get_history():
    return r.lrange(f"session:{SESSION_ID}:history", 0, -1)

def add_to_history(role, message):
    r.rpush(f"session:{SESSION_ID}:history", f"{role}: {message}")

def get_user_details():
    data = r.get(f"session:{SESSION_ID}:user_details")
    return eval(data) if data else None

def save_user_details(details_dict):
    r.set(f"session:{SESSION_ID}:user_details", str(details_dict))

def clear_session():
    r.delete(f"session:{SESSION_ID}:history")
    r.delete(f"session:{SESSION_ID}:user_details")

# ------------------ Chatbot Interface ------------------
def chatbot_interface(user_message):
    # Retrieve chat history
    history = get_history()
    
    # First-time launch
    if not history:
        bot_message = (
            "👋 Hello! I'm your Financial Education Assistant Chatbot. "
            "You can ask me anything about financial literacy, investments, or money management."
        )
        add_to_history("bot", bot_message)
        return bot_message

    add_to_history("user", user_message)

    # Check if user details already provided
    user_details = get_user_details()

    # Check if user message contains requested details
    if not user_details and user_message.startswith("{") and user_message.endswith("}"):
        try:
            details_dict = eval(user_message)  # Expecting format {email, username, userinfo = ...}
            # Basic validation for required keys
            if "email" in details_dict and "username" in details_dict and "userinfo" in details_dict:
                save_user_details(details_dict)
                bot_message = "✅ Thank you! Your details are saved. We can now proceed with validations and personalized guidance."
                add_to_history("bot", bot_message)
                return bot_message
            else:
                raise ValueError
        except Exception:
            bot_message = (
                "⚠️ Invalid format. Please provide details in this format:\n"
                "{email, username, userinfo = age, profession, private_id}"
            )
            add_to_history("bot", bot_message)
            return bot_message

    # If user_details exist, invoke orchestrator
    if user_details:
        bot_reply = handle_user(
            email=user_details.get("email"),
            user_name=user_details.get("username"),
            user_info=user_details.get("userinfo"),
            user_input=user_message
        )
        add_to_history("bot", bot_reply)
        return bot_reply

    # Default behavior: act as assistant chatbot
    bot_message = (
        "💡 I can help you with financial education. "
        "If you want personalized guidance or validations, "
        "please provide your details in this format:\n"
        "{email, username, userinfo = age, profession, private_id}"
    )
    add_to_history("bot", bot_message)
    return bot_message

# ------------------ Gradio App ------------------
with gr.Blocks() as demo:
    gr.Markdown("## Financial Education Chatbot (Stateful, Session-based)")

    chatbot = gr.Chatbot()
    user_input = gr.Textbox(label="Type your message")
    submit = gr.Button("Send")

    def respond(message, chat_history):
        bot_reply = chatbot_interface(message)
        chat_history.append((message, bot_reply))
        return chat_history, ""

    submit.click(respond, inputs=[user_input, chatbot], outputs=[chatbot, user_input])

# Clear session on exit
import atexit
atexit.register(clear_session)

demo.launch()
