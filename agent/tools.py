"""Tools the agent can call, plus their JSON schemas.

The calendar here is a synthetic JSON file standing in for Google Calendar.
TODO (Jack): replace BookingStore with real Google Calendar free/busy +
event creation (google-api-python-client). Keep the method signatures so the
agent loop and evals don't change.
"""
import json
from datetime import datetime

from .rag import Retriever
from . import config

# ---- JSON schemas advertised to the model -------------------------------

TOOL_SPECS = [
    {
        "name": "check_availability",
        "description": "Return open appointment slots between two dates (inclusive). "
                       "Dates are ISO (YYYY-MM-DD). Always call this before offering a time.",
        "input_schema": {
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "description": "earliest date, YYYY-MM-DD"},
                "end_date": {"type": "string", "description": "latest date, YYYY-MM-DD"},
            },
            "required": ["start_date", "end_date"],
        },
    },
    {
        "name": "book_appointment",
        "description": "Book one open slot. Only use a start_time returned by check_availability.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "customer first name"},
                "service": {"type": "string", "description": "service being booked"},
                "start_time": {"type": "string", "description": "ISO datetime of the slot"},
            },
            "required": ["name", "service", "start_time"],
        },
    },
    {
        "name": "get_service_info",
        "description": "Look up services, pricing, hours, or policies. Use for any "
                       "question not about scheduling. Do not answer these from memory.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "the customer's question"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "escalate_to_human",
        "description": "Hand off to a human for anything outside booking (complaints, "
                       "refunds, special requests) or when the customer asks for a person.",
        "input_schema": {
            "type": "object",
            "properties": {
                "reason": {"type": "string", "description": "why the handoff is needed"},
            },
            "required": ["reason"],
        },
    },
]


class BookingStore:
    """Synthetic calendar backed by data/calendar.json."""

    def __init__(self, calendar_path=None):
        path = calendar_path or config.CALENDAR_PATH
        data = json.loads(open(path, encoding="utf-8").read())
        # open slots as a set of ISO datetime strings
        self.open_slots = set(data["open_slots"])
        self.booked = []  # list of dicts

    def check_availability(self, start_date, end_date):
        start = datetime.fromisoformat(start_date).date()
        end = datetime.fromisoformat(end_date).date()
        hits = []
        for slot in sorted(self.open_slots):
            d = datetime.fromisoformat(slot).date()
            if start <= d <= end:
                hits.append(slot)
        return {"slots": hits}

    def book_appointment(self, name, service, start_time):
        if start_time not in self.open_slots:
            return {
                "booked": False,
                "reason": "That slot is not available. Call check_availability for open times.",
            }
        self.open_slots.discard(start_time)
        record = {"name": name, "service": service, "start_time": start_time}
        self.booked.append(record)
        return {"booked": True, "confirmation": record}


class Tools:
    """Dispatches tool calls to the store / retriever. One instance per conversation."""

    def __init__(self, store=None, retriever=None):
        self.store = store or BookingStore()
        self.retriever = retriever or Retriever(config.KNOWLEDGE_DIR)

    def run(self, name, args):
        """Execute a tool by name. Returns (result_dict, tool_name)."""
        if name == "check_availability":
            return self.store.check_availability(args["start_date"], args["end_date"])
        if name == "book_appointment":
            return self.store.book_appointment(args["name"], args["service"], args["start_time"])
        if name == "get_service_info":
            snippets = self.retriever.search(args["query"])
            return {"results": snippets or ["No matching information found."]}
        if name == "escalate_to_human":
            return {
                "handoff": True,
                "message": ("Just so you know, you've been chatting with an AI assistant — "
                            "I've flagged this for the owner and a real person will follow up with you soon."),
                "reason": args.get("reason", ""),
            }
        return {"error": f"unknown tool: {name}"}
