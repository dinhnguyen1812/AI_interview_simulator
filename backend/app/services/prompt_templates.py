def get_behavioral_prompt(user_response=None):
    if not user_response:
        return (
            "You're a professional behavioral interviewer. "
            "Ask the candidate a behavioral question focused on teamwork. "
            "Wait for their response."
        )
    else:
        return (
            f"The candidate responded: {user_response}\n"
            "Now give structured feedback on their answer, focusing on clarity, depth, and use of STAR method."
        )
