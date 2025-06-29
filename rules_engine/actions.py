def mark_as_read(email_id, service):
    print(f"Invoked mark as read for: {email_id}")
    service.users().messages().modify(
        userId='me',
        id=email_id,
        body={"removeLabelIds": ["UNREAD"]}
    ).execute()


def mark_as_unread(email_id, service):
    print(f"Invoked mark as unread for: {email_id}")
    service.users().messages().modify(
        userId='me',
        id=email_id,
        body={"addLabelIds": ["UNREAD"]}
    ).execute()

def move_to_label(email_id, service, label_name):
    print(f"Invoked move to label for: {email_id}")
    labels = service.users().labels().list(userId='me').execute().get('labels', [])
    label_id = next((l['id'] for l in labels if l['name'].lower() == label_name.lower()), None)
    if not label_id:
        label = service.users().labels().create(
            userId='me',
            body={"name": label_name, "labelListVisibility": "labelShow", "messageListVisibility": "show"}
        ).execute()
        label_id = label['id']
    service.users().messages().modify(
        userId='me',
        id=email_id,
        body={"addLabelIds": [label_id]}
    ).execute()

ACTIONS = {
    "mark_as_read": lambda email, svc, _: mark_as_read(email["id"], svc),
    "mark_as_unread": lambda email, svc, _: mark_as_unread(email["id"], svc),
    "move_to_label": lambda email, svc, val: move_to_label(email["id"], svc, val)
}