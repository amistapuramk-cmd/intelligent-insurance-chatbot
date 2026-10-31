"""
Intelligent Insurance Chatbot  (simple base project)
----------------------------------------------------
Features:
  1. Intent detection (keyword scoring + fuzzy matching for typos)
  2. FAQ answers: policy types, claims, documents, renewal, contact
  3. Multi-step premium quote flow (remembers conversation state)
  4. Runs in the terminal, no external libraries needed (Python 3.8+)

Run:  python insurance_chatbot.py
"""

import re
from difflib import get_close_matches

# ---------------------------------------------------------------
# 1. KNOWLEDGE BASE  (add or edit intents here to extend the bot)
# ---------------------------------------------------------------
INTENTS = {
    "greeting": {
        "keywords": ["hi", "hello", "hey", "namaste", "morning", "evening"],
        "response": "Hello! I'm InsureBot. I can help with policy info, "
                    "premium quotes, claims and renewals. What do you need?",
    },
    "policy_types": {
        "keywords": ["policy", "policies", "types", "plans", "insurance", "offer", "available"],
        "response": (
            "We offer these insurance plans:\n"
            "  1. Health  - hospital & treatment expenses\n"
            "  2. Life    - financial security for your family\n"
            "  3. Motor   - car / bike damage & third-party cover\n"
            "  4. Travel  - trip cancellation, medical & baggage cover\n"
            "  5. Home    - fire, theft & natural calamity cover\n"
            "Type 'quote' to get a premium estimate."
        ),
    },
    "claim_process": {
        "keywords": ["claim", "claims", "reimbursement", "settle", "settlement", "accident", "file"],
        "response": (
            "To file a claim:\n"
            "  1. Intimate us within 48 hours (call or app).\n"
            "  2. Submit the claim form with required documents.\n"
            "  3. Our surveyor / medical team verifies the claim.\n"
            "  4. Approved claims are settled in 7-15 working days."
        ),
    },
    "documents": {
        "keywords": ["document", "documents", "papers", "proof", "required", "kyc"],
        "response": (
            "Commonly required documents:\n"
            "  - Photo ID & address proof (Aadhaar / PAN / Passport)\n"
            "  - Filled claim form & policy number\n"
            "  - Bills / FIR / hospital discharge summary (as applicable)\n"
            "  - Bank details for settlement"
        ),
    },
    "renewal": {
        "keywords": ["renew", "renewal", "expire", "expiry", "lapse", "lapsed", "extend"],
        "response": "You can renew online using your policy number. A grace period of "
                    "30 days applies; after that the policy may lapse and need re-underwriting.",
    },
    "contact": {
        "keywords": ["contact", "call", "phone", "agent", "support", "human", "email", "helpline"],
        "response": "Reach our support team at 1800-000-0000 (toll-free, 9am-6pm) "
                    "or support@insurebot.example.",
    },
    "goodbye": {
        "keywords": ["bye", "goodbye", "exit", "quit", "thanks", "thank"],
        "response": "Thank you for chatting with InsureBot. Stay protected!",
    },
}

# Base annual premium (INR) per policy type, used by the quote calculator
BASE_PREMIUM = {"health": 5000, "life": 8000, "motor": 6000, "travel": 1500, "home": 3000}


# ---------------------------------------------------------------
# 2. NLP HELPERS
# ---------------------------------------------------------------
def tokenize(text):
    return re.findall(r"[a-z]+", text.lower())


def detect_intent(text):
    """Score every intent by keyword overlap (fuzzy to tolerate typos)."""
    tokens = tokenize(text)
    best_intent, best_score = None, 0
    for name, data in INTENTS.items():
        score = 0
        for tok in tokens:
            if tok in data["keywords"]:
                score += 2
            elif get_close_matches(tok, data["keywords"], n=1, cutoff=0.8):
                score += 1
        if score > best_score:
            best_intent, best_score = name, score
    return best_intent


def extract_number(text):
    m = re.search(r"\d[\d,]*", text)
    return int(m.group().replace(",", "")) if m else None


# ---------------------------------------------------------------
# 3. PREMIUM QUOTE LOGIC
# ---------------------------------------------------------------
def calculate_premium(policy, age, cover):
    base = BASE_PREMIUM[policy]
    age_factor = 1.0 if age < 30 else 1.3 if age < 45 else 1.7 if age < 60 else 2.2
    cover_factor = cover / 500000          # relative to a 5 lakh cover
    return round(base * age_factor * max(cover_factor, 0.5))


# ---------------------------------------------------------------
# 4. CHATBOT CLASS (keeps conversation state)
# ---------------------------------------------------------------
class InsuranceChatbot:
    def __init__(self):
        self.state = None        # None | "ask_policy" | "ask_age" | "ask_cover"
        self.quote = {}

    def reply(self, user_text):
        text = user_text.strip()
        if not text:
            return "Please type something so I can help."

        # --- continue an ongoing quote conversation ---
        if self.state:
            return self._handle_quote_step(text)

        # --- start the quote flow ---
        if any(w in tokenize(text) for w in ("quote", "premium", "price", "cost", "calculate")):
            self.state = "ask_policy"
            return "Sure! Which policy? (health / life / motor / travel / home)"

        # --- normal intent handling ---
        intent = detect_intent(text)
        if intent:
            return INTENTS[intent]["response"]
        return ("Sorry, I didn't understand that. You can ask about policy types, "
                "claims, documents, renewal, or type 'quote' for a premium estimate.")

    def _handle_quote_step(self, text):
        if self.state == "ask_policy":
            match = get_close_matches(text.lower(), BASE_PREMIUM.keys(), n=1, cutoff=0.6)
            if not match:
                return "Please choose one: health / life / motor / travel / home"
            self.quote["policy"] = match[0]
            self.state = "ask_age"
            return "Got it. What is your age?"

        if self.state == "ask_age":
            age = extract_number(text)
            if age is None or not (18 <= age <= 90):
                return "Please enter a valid age between 18 and 90."
            self.quote["age"] = age
            self.state = "ask_cover"
            return "What cover amount do you need (in INR)? e.g. 500000"

        if self.state == "ask_cover":
            cover = extract_number(text)
            if cover is None or cover < 50000:
                return "Please enter a cover amount of at least 50,000."
            q = self.quote
            premium = calculate_premium(q["policy"], q["age"], cover)
            self.state, self.quote = None, {}
            return (f"Estimated yearly premium for {q['policy'].title()} insurance "
                    f"(age {q['age']}, cover Rs.{cover:,}): Rs.{premium:,}\n"
                    "(Illustrative estimate only. Final premium depends on underwriting.)")


# ---------------------------------------------------------------
# 5. TERMINAL INTERFACE
# ---------------------------------------------------------------
def main():
    bot = InsuranceChatbot()
    print("=" * 55)
    print("  InsureBot - Intelligent Insurance Chatbot")
    print("  Type 'bye' to exit.")
    print("=" * 55)
    while True:
        user = input("\nYou : ")
        answer = bot.reply(user)
        print(f"Bot : {answer}")
        if detect_intent(user) == "goodbye" and bot.state is None:
            break


if __name__ == "__main__":
    main()
