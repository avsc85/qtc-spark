import json


def parse_action(response_text: str) -> tuple[str, dict | None]:
    """
    Scan a GPT response for an ACTION line.

    Returns:
        (clean_text, action_dict)  — action_dict is None if no ACTION found.

    Example input:
        "I'll create the lead now.\nACTION: {"action": "create_lead", "data": {...}}"

    Example output:
        ("I'll create the lead now.", {"action": "create_lead", "data": {...}})
    """
    lines = response_text.splitlines()
    action_dict: dict | None = None
    clean_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("ACTION: "):
            json_part = stripped[len("ACTION: "):]
            try:
                action_dict = json.loads(json_part)
            except json.JSONDecodeError:
                pass  # malformed ACTION line — treat as plain text
        else:
            clean_lines.append(line)

    clean_text = "\n".join(clean_lines).strip()
    return clean_text, action_dict


if __name__ == "__main__":
    test = (
        'I will create the lead for you.\n'
        'ACTION: {"action": "create_lead", "data": {"customer_name": "Shelly"}}'
    )
    text, action = parse_action(test)
    print("Text:", text)
    print("Action:", action)
