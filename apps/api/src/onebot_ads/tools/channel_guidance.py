DEFAULT_GUIDANCE = {
    "format_hint": "Keep the draft concise, concrete, and easy to review.",
    "copy_goal": "clear value communication",
    "default_cta": "Request a demo",
}

CHANNEL_GUIDANCE = {
    "meta": {
        "format_hint": "Lead with outcome, keep the hook fast, and make the offer explicit.",
        "copy_goal": "thumb-stopping clarity",
        "default_cta": "Book a demo",
    },
    "google": {
        "format_hint": "Use direct intent language and emphasize measurable business value.",
        "copy_goal": "high-intent conversion",
        "default_cta": "Get started",
    },
    "linkedin": {
        "format_hint": "Keep the tone credible and operator-focused.",
        "copy_goal": "professional trust",
        "default_cta": "See how it works",
    },
    "email": {
        "format_hint": "Use a tight narrative with a single clear next step.",
        "copy_goal": "reply or click intent",
        "default_cta": "Reply for a walkthrough",
    },
    "landing_page": {
        "format_hint": "Clarify problem, solution, proof, and CTA in sequence.",
        "copy_goal": "conversion framing",
        "default_cta": "Start the pilot",
    },
}


def build_channel_guidance(channels: list[str]) -> dict[str, dict[str, str]]:
    guidance = {"default": DEFAULT_GUIDANCE}
    for channel in channels:
        guidance[channel] = CHANNEL_GUIDANCE.get(channel, DEFAULT_GUIDANCE)
    return guidance


def build_default_cta(channel: str) -> str:
    return CHANNEL_GUIDANCE.get(channel, DEFAULT_GUIDANCE)["default_cta"]
