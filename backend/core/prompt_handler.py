import re
from typing import Any


def normalize_prompt(prompt: str | list[dict[str, Any]]) -> str:
    """
    Extracts the textual representation of a prompt for hashing, token estimation,
    or complexity checks.
    """
    if isinstance(prompt, str):
        return prompt
    elif isinstance(prompt, list) and len(prompt) > 0:
        return str(prompt[-1].get("content", ""))
    return ""


def estimate_tokens(text: str | list[dict[str, Any]]) -> int:
    """
    Estimates the number of tokens in a prompt (rough estimate: 4 chars = 1 token).
    """
    normalized_text = normalize_prompt(text)
    return len(normalized_text) // 4


def format_unified_chat_prompt(message: str, history: list[dict[str, str]] | None = None) -> str:
    """
    Centralized prompt builder for unifying chat history with the current task.
    Prevents context loss and DRY violations across multiple routers.
    """
    if not history:
        return message

    formatted_prompt = ""
    for msg in history:
        role = "User" if msg.get("role") == "user" else "Assistant"
        formatted_prompt += f"{role}: {msg.get('content', '')}\n"
    formatted_prompt += f"User: {message}\nAssistant:"
    return formatted_prompt


def compress_prompt_text(text: str) -> str:
    """
    OmniRoute-inspired 'Caveman-lite' compression.
    Removes HTML/Markdown comments and collapses duplicate whitespaces/newlines.
    """
    if not isinstance(text, str):
        return text
    # Remove HTML/Markdown comments (e.g., <!-- comment -->)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    # Collapse 3 or more newlines into 2 newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Collapse 2 or more spaces into a single space, but leave newlines intact
    text = re.sub(r"[^\S\r\n]{2,}", " ", text)
    return text.strip()


def compress_prompt_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Applies Caveman-lite compression to a list of message dicts to save tokens.
    """
    compressed_messages = []
    for msg in messages:
        new_msg = msg.copy()
        if "content" in new_msg and isinstance(new_msg["content"], str):
            new_msg["content"] = compress_prompt_text(new_msg["content"])
        compressed_messages.append(new_msg)
    return compressed_messages
