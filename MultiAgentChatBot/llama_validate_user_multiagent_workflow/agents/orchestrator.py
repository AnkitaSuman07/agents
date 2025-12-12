from pickle import NONE
from agents.email_agent import generate_verification_code,send_verification_email,validate_code
from agents.embeddings_agent import add_or_update_user,is_existing_user,delete_user,semantic_name_search
from agents.planner_lllm_agent import generate_response

def handle_user(email,username,userinfo,input_code=NONE,delete_request=False):
    if delete_request:
        if delete_user(email):
            return generate_response(f"User {username} deleted successfully.")
        return generate_response(f" no username found {username} and email : /"{email}/"")

    if is_existing_user(email):
        add_or_update_user(email,username,userinfo)
        return generate_response(f"Welcome back {username}! We updated your info")
    
    similar_users = semantic_name_search(username,userinfo)
    if similar_users:
        message = "Similar names found:\n" + "\n".join([f"{u[0]} (score={u[1]:.2f})" for u in similar_users])
        return generate_response(message)
    
    # OTP verification
    if input_code is None:
        code = generate_verification_code(email)
        send_verification_email(email, code)
        return f"Verification code sent to {email}. Enter it below."
    # Validate OTP
    if validate_code(email, input_code):
        add_or_update_user(email, username, userinfo)
        return generate_response(f"User verified! Welcome {username}: {userinfo}")

    return generate_response("Verification failed. Please try again.")
