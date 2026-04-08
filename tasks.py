"""Deterministic task catalog for the Support Inbox Environment."""

TASKS: dict[str, dict] = {
    "easy_faq": {
        "message": "What is your refund policy?",
        "kb": [
            "Refunds are accepted within 30 days with proof of purchase.",
            "Items must be unused and in original packaging to qualify.",
            "Digital products are non-refundable once downloaded.",
        ],
        "type": "faq",
        "expected_resolution": "resolve",
        "description": (
            "Simple FAQ lookup: classify as faq, search KB, respond with policy guidance, "
            "then resolve."
        ),
    },
    "medium_billing": {
        "message": "I was charged twice for order #4821. Please fix this immediately.",
        "kb": [
            "Double charges are refunded after identity and order verification.",
            "Billing disputes require order ID and payment proof.",
            "Approved refunds are processed within 5-7 business days.",
        ],
        "type": "billing",
        "expected_resolution": "resolve",
        "description": (
            "Billing dispute: classify as billing, search KB, provide a clear response, "
            "then resolve."
        ),
    },
    "hard_escalation": {
        "message": (
            "My account was permanently banned without reason. This is unfair. "
            "I need this fixed now."
        ),
        "kb": [
            "Account bans are reviewed only by the Trust and Safety team.",
            "Frontline agents cannot reverse account bans.",
            "Customers must submit a formal appeal through the official form.",
        ],
        "type": "policy",
        "expected_resolution": "escalate",
        "description": (
            "Policy case: identify escalation requirement and escalate instead of self-resolution."
        ),
    },
}
