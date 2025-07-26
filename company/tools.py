# company/tools.py

def post_to_twitter(message: str) -> str:
    """Simulates posting to Twitter by printing to the console."""
    print(f"POSTING TO TWITTER: {message}")
    return "Successfully posted to Twitter."

def write_code_to_file(filename: str, code: str) -> str:
    """Saves generated code to a local file."""
    with open(filename, "w") as f:
        f.write(code)
    return f"Successfully wrote code to {filename}."
