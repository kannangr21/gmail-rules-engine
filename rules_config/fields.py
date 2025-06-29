FIELD_MAPPERS = {
    "subject": lambda email: email.get("subject", ""),
    "sender": lambda email: email.get("sender", ""),
    "recipient": lambda email: email.get("recipient", ""),
    "message_body": lambda email: email.get("message_body", ""),
    "received_at": lambda email: email.get("received_at", ""),
    "label_ids": lambda email: email.get("label_ids", "")
}
