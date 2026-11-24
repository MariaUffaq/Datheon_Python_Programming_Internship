import json
import random
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_FILES = ["sample_faq.json", "faq.json"]   # first one found is used

EXIT_WORDS = {"bye", "exit", "quit"}
GREETING_REGEX = r"\b(hi|hello|hey|salam|good (morning|afternoon|evening))\b"
GREETING_REPLIES = [
    "Hello! How can I help you today?",
    "Hi there! Ask me about our hours, products, shipping or returns.",
]
FALLBACKS = [
    "Sorry, I didn't understand that. Could you rephrase?",
    "I'm not sure about that. Try asking about hours, products, prices or returns.",
    "Hmm, I don't have an answer for that yet. Type 'bye' to leave.",
]
STOPWORDS = {
    "what", "when", "where", "which", "who", "whom", "why", "how", "your",
    "you", "the", "are", "is", "do", "does", "can", "could", "would", "about",
    "have", "has", "with", "for", "and", "our", "any", "there", "this", "that",
    "from", "get", "tell", "please", "want", "need", "know", "me", "my",
}

# Conversation states
GREETING, ASSISTING, EXIT = "GREETING", "ASSISTING", "EXIT"


# ---------------------------------------------------------------- helpers
def normalize(text: str) -> str:
    """Lowercase, strip, remove punctuation, collapse spaces."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s']", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def keywords(text: str) -> set:
    """Meaningful words of a sentence (no stopwords, no tiny words)."""
    return {w for w in normalize(text).split() if len(w) > 2 and w not in STOPWORDS}


def load_data():
    """Load the first dataset file that exists."""
    for name in DATA_FILES:
        path = BASE_DIR / name
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                sys.exit(f"Error: {name} is not valid JSON ({e}).")
    sys.exit(f"Error: none of {DATA_FILES} found in {BASE_DIR}")


def build_intents(data) -> list:
    """Convert whatever JSON layout we got into a uniform list of intents.

    Each intent: {"type": "regex"|"faq", "patterns": [...], "keywords": set,
                  "responses": [...]}
    """
    intents = []

    # Layout 1: {"intents": [...]}
    if isinstance(data, dict) and "intents" in data:
        for item in data["intents"]:
            responses = item.get("responses") or item.get("response") or []
            if isinstance(responses, str):
                responses = [responses]
            patterns = item.get("patterns") or item.get("keywords") or []
            if isinstance(patterns, str):
                patterns = [patterns]
            if patterns and responses:
                intents.append({"type": "regex", "patterns": patterns,
                                "keywords": set(), "responses": responses})
        return intents

    # Layout 2 / 3: list of Q&A pairs (maybe inside a dict)
    items = data
    if isinstance(data, dict):
        for key in ("faqs", "faq", "questions", "data", "entries", "items"):
            if key in data:
                items = data[key]
                break
        else:
            # dict of {"question": "answer"} pairs
            items = [{"question": q, "answer": a} for q, a in data.items()
                     if isinstance(a, str)]

    for item in items:
        if not isinstance(item, dict):
            continue
        q = item.get("question") or item.get("q") or item.get("query") or ""
        a = item.get("answer") or item.get("a") or item.get("response") or ""
        kw = keywords(q)
        if kw and a:
            intents.append({"type": "faq", "patterns": [], "keywords": kw,
                            "responses": [a]})
    return intents


def regex_hit(pattern: str, text: str) -> bool:
    """Match a pattern as regex; if it isn't valid regex, match as plain text."""
    try:
        return re.search(pattern, text) is not None
    except re.error:
        return re.escape(pattern.lower()) in text or pattern.lower() in text


def find_responses(text: str, intents: list) -> list:
    """Return a list of answers (multi-intent aware)."""
    answers = []

    # 1) regex intents: every intent that matches is answered
    for intent in intents:
        if intent["type"] == "regex" and any(regex_hit(p, text) for p in intent["patterns"]):
            answers.append(random.choice(intent["responses"]))

    # 2) FAQ intents: take the best-scoring question(s) by keyword overlap
    user_words = keywords(text)
    scored = []
    for intent in intents:
        if intent["type"] == "faq":
            score = len(user_words & intent["keywords"])
            if score:
                scored.append((score, intent))
    if scored:
        best = max(s for s, _ in scored)
        for score, intent in scored:
            # need a decent overlap (at least half of the question's keywords)
            # or the top score, to avoid weak accidental matches
            if score == best and score >= max(1, len(intent["keywords"]) // 2):
                answers.append(random.choice(intent["responses"]))

    # remove duplicates, keep order
    seen, unique = set(), []
    for a in answers:
        if a not in seen:
            seen.add(a)
            unique.append(a)
    return unique


def is_greeting(text: str) -> bool:
    return re.search(GREETING_REGEX, text) is not None


def is_exit(text: str) -> bool:
    return any(word in EXIT_WORDS for word in text.split())


# ------------------------------------------------------------------- main
def main() -> None:
    data = load_data()
    intents = build_intents(data)
    if not intents:
        sys.exit("Error: could not read any questions/intents from the JSON file.")

    name = data.get("business_name", "Customer Support") if isinstance(data, dict) else "Customer Support"
    state = GREETING

    print(f"=== {name} Assistant === (type 'bye', 'exit' or 'quit' to leave)\n")

    while state != EXIT:
        try:
            raw = input("You: ")
        except (EOFError, KeyboardInterrupt):
            print("\nBot: Goodbye!")
            break

        text = normalize(raw)

        if not text:
            print("Bot: Please type something so I can help.")
            continue

        if is_exit(text):
            print("Bot: Thanks for chatting. Goodbye!")
            state = EXIT
            continue

        answers = find_responses(text, intents)

        # GREETING state: respond to hello, then move on to assisting
        if state == GREETING and is_greeting(text) and not answers:
            print(f"Bot: {random.choice(GREETING_REPLIES)}")
            state = ASSISTING
            continue

        state = ASSISTING

        if answers:
            print("Bot: " + "\nBot: ".join(answers))
        elif is_greeting(text):
            print(f"Bot: {random.choice(GREETING_REPLIES)}")
        else:
            print(f"Bot: {random.choice(FALLBACKS)}")


if __name__ == "__main__":
    main()