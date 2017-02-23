

def classify(entries):
    for entry in entries:
        entry['category_id'] = 1
        entry['event_id'] = 1
    return entries
