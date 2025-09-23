
FAIL = "failure"
SUCCESS = "done"
RETRY = "retry"
MORE_DATA ="need_more_data"
SPECIAL_ROUTER = ["user", "Router"]
MAX_ITERATIONS = 1000
MAX_RETRIES = 5
DEFAULT_TIMEOUT = 30 # seconds
END_POINTS = {
    "gemini": "https://generativelanguage.googleapis.com/v1beta/models/{replace_model_name}:generateContent",
}

SYSTEM_PROMPT = """[INST] <<SYS>>
{replace_system_prompt}
<</SYS>>

{replace_user_request}
[/INST]
"""
