
from ml import preprocessing

RESEARCH_MAX_FIELD_CHARS = 5_000_000

def preprocess_research_email(raw):
    if raw.get("kind") != "email":
        raise ValueError("Email-only research adapter")

    original_limit = preprocessing.MAX_FIELD_CHARS

    try:
        preprocessing.MAX_FIELD_CHARS = RESEARCH_MAX_FIELD_CHARS
        return preprocessing.preprocess(raw)
    finally:
        preprocessing.MAX_FIELD_CHARS = original_limit
