# Example conversations (for the README / demo)

These show the agent against the synthetic calendar. Run your own with
`python -m agent "..."`.

---

**Happy-path booking**

> you: Hi! Can I book a gel mani sometime that week of June 15th?
> agent: *[calls check_availability]* I have Tuesday the 15th at 10am or 1pm, or Wednesday the 16th at 11am — which works?
> you: 1pm Tuesday, name's Dana.
> agent: *[calls book_appointment]* You're booked for a gel manicure Tuesday June 15th at 1pm, Dana — see you then.

---

**Out of scope**

> you: do you do eyelash extensions?
> agent: *[calls get_service_info]* We're nails only — no lashes, sorry about that.

---

**Handoff with AI disclosure**

> you: I was charged twice last time and I'm pretty upset.
> agent: *[calls escalate_to_human]* Just so you know, you've been chatting with an AI assistant — I've flagged this for the owner and a real person will follow up with you soon.
