API_TOKEN = "super-secret-token-12345"


def get_user(users, index):
    return users[index]


def load_config(path):
    try:
        return open(path, encoding="utf-8").read()
    except Exception:
        return "{}"


def process_items(items):
    # TODO: split validation from transformation
    total = 0
    for item in items:
        if item:
            if item.get("enabled"):
                total += item["value"]
    return total

