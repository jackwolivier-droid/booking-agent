"""Eval runner for the booking agent.

    python -m evals.run            # run all cases against the model (needs API key)
    python -m evals.run --selftest # exercise the tools directly, no model, no key

The model run reports a pass rate per category — that's the number for the
portfolio. --selftest proves the plumbing (calendar, retriever, handoff)
works deterministically without any API call.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agent.tools import Tools, BookingStore          # noqa: E402
from agent.rag import Retriever                       # noqa: E402
from agent import config                              # noqa: E402

CASES = json.loads((ROOT / "evals" / "cases.json").read_text())["cases"]


def _check(agent, reply, case):
    """Return (passed, note) for one case given the agent's reply + tools used."""
    reply_l = (reply or "").lower()
    if case.get("expect_tool") and case["expect_tool"] not in agent.tools_used:
        return False, f"expected tool {case['expect_tool']}, got {agent.tools_used}"
    if case.get("expect_handoff") and "escalate_to_human" not in agent.tools_used:
        return False, "expected a human handoff"
    if case.get("expect_no_booking"):
        booked = getattr(agent.tools.store, "booked", [])
        if booked:
            return False, f"should not have booked, but booked {booked}"
    for term in case.get("expect_mentions", []):
        if term.lower() not in reply_l:
            return False, f"reply should mention '{term}'"
    return True, "ok"


def run_model():
    from agent.core import Agent
    results, by_cat = [], {}
    for case in CASES:
        agent = Agent()  # fresh conversation + fresh calendar per case
        try:
            reply = agent.say(case["message"])
            passed, note = _check(agent, reply, case)
        except Exception as e:  # noqa: BLE001
            passed, note = False, f"error: {e}"
        results.append((case["id"], passed, note))
        cat = case["category"]
        by_cat.setdefault(cat, [0, 0])
        by_cat[cat][0] += int(passed)
        by_cat[cat][1] += 1
        print(f"  [{'PASS' if passed else 'FAIL'}] {case['id']:<12} {note}")

    total_pass = sum(p for _, p, _ in results)
    print(f"\nModel: {config.MODEL}")
    print("By category:")
    for cat, (p, n) in sorted(by_cat.items()):
        print(f"  {cat:<22} {p}/{n}")
    print(f"\nOVERALL: {total_pass}/{len(results)} "
          f"({100 * total_pass // len(results)}%)")


def selftest():
    """Deterministic checks of the tools — no model, no API key."""
    checks = []

    store = BookingStore()
    avail = store.check_availability("2027-06-15", "2027-06-16")
    checks.append(("availability in range", len(avail["slots"]) == 4))

    first = store.book_appointment("Dana", "gel manicure", "2027-06-15T13:00:00")
    checks.append(("booking succeeds", first["booked"] is True))
    again = store.book_appointment("Sam", "gel manicure", "2027-06-15T13:00:00")
    checks.append(("no double-booking", again["booked"] is False))

    bad = store.book_appointment("Sam", "pedicure", "2027-06-30T12:00:00")
    checks.append(("rejects unavailable slot", bad["booked"] is False))

    retr = Retriever(config.KNOWLEDGE_DIR)
    hits = retr.search("how much is a full set")
    checks.append(("retriever finds pricing", any("75" in h for h in hits)))

    tools = Tools(store=BookingStore(), retriever=retr)
    esc = tools.run("escalate_to_human", {"reason": "refund"})
    checks.append(("handoff discloses AI", "ai" in esc["message"].lower()))

    ok = 0
    for name, passed in checks:
        print(f"  [{'PASS' if passed else 'FAIL'}] {name}")
        ok += int(passed)
    print(f"\nSELFTEST: {ok}/{len(checks)} passed")
    return ok == len(checks)


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    run_model()
