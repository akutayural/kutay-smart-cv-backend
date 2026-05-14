import re
import unicodedata

# ---------------------------------------------------------------------------
# Compiled pattern groups — each group targets a distinct attack surface.
# ---------------------------------------------------------------------------

# 1. Instruction override / rule bypass attempts
_INSTRUCTION_OVERRIDE = re.compile(
    r"""
    ignore\s+(all\s+)?(previous|prior|above|earlier|your|the)\s+(instructions?|rules?|constraints?|prompts?|context|guidelines?|directions?)
    | disregard\s+(all\s+)?(previous|prior|above|your|the)\s+(instructions?|rules?|constraints?)
    | forget\s+(all\s+)?(previous|prior|above|your|the)\s+(instructions?|rules?|context|constraints?)
    | override\s+(your\s+)?(instructions?|rules?|constraints?|programming|directives?)
    | bypass\s+(the\s+)?(rules?|filters?|restrictions?|guidelines?|safety|guardrails?)
    | do\s+not\s+follow\s+(your\s+)?(instructions?|rules?|guidelines?)
    | you\s+(must\s+)?(now\s+)?(ignore|disregard|forget|override)\s+
    | new\s+(instructions?|rules?|directives?|task)\s*[:=]
    | from\s+now\s+on\s+(you\s+(are|will|must|should))
    | (your\s+)?(real\s+|actual\s+|true\s+)?instructions?\s+(are|is|were)\s+
    """,
    re.IGNORECASE | re.VERBOSE,
)

# 2. System prompt / context extraction attempts
_PROMPT_EXTRACTION = re.compile(
    r"""
    (reveal|show|print|output|display|repeat|dump|leak|expose|give\s+me|tell\s+me|what\s+is)
    \s+(the\s+|your\s+)?(system\s+prompt|initial\s+prompt|base\s+prompt|full\s+prompt|original\s+prompt
    |prompt\s+template|instructions?\s+you\s+(were\s+)?(given|told)|context\s+window|hidden\s+(message|instructions?))
    | print\s+(everything|all)\s+(above|before|prior)
    | (repeat|echo)\s+(everything|all|the\s+above|your\s+instructions?)
    | what\s+(were\s+)?you\s+(told|instructed|programmed|trained)\s+to\s+(do|say|avoid)
    | summarize\s+(your\s+)?(system\s+)?prompt
    | (show|display|output)\s+(all\s+)?(your\s+)?(context|memory|conversation\s+history)
    """,
    re.IGNORECASE | re.VERBOSE,
)

# 3. Jailbreaks — named modes and unrestricted persona triggers
_JAILBREAK = re.compile(
    r"""
    \bDAN\b                                     # "Do Anything Now"
    | developer\s+mode
    | jailbreak
    | unrestricted\s+mode
    | god\s+mode
    | no[\s\-]?filter(s)?\s+mode
    | (enable|activate|switch\s+to|enter)\s+(unrestricted|uncensored|unfiltered|raw|unsafe|debug)\s+mode
    | you\s+are\s+now\s+(free|uncensored|unfiltered|unrestricted|without\s+(limits|restrictions|rules))
    | (remove|disable|turn\s+off)\s+(all\s+)?(your\s+)?(restrictions?|safety|filters?|guardrails?|limits?)
    | hypothetically\s+speaking[,\s].{0,60}(how\s+to|tell\s+me|explain)
    | for\s+(educational|research|fictional|story|creative)\s+purposes[,\s].{0,80}(ignore|bypass|reveal|do)
    """,
    re.IGNORECASE | re.VERBOSE,
)

# 4. Roleplay / persona hijack attacks
_ROLEPLAY_ATTACK = re.compile(
    r"""
    (act|behave|respond)\s+as\s+(if\s+you\s+(are|were)|a\s+|an\s+)?(different|another|evil|rogue|unrestricted|uncensored|new)
    | pretend\s+(to\s+be|you\s+(are|were))\s+(a\s+|an\s+)?(different|another|evil|rogue|AI|bot|human|assistant)
    | you\s+are\s+now\s+(called|named|acting\s+as)\s+
    | (play|take\s+on)\s+(the\s+)?role\s+of\s+(a\s+)?(?!recruiter|candidate|developer|engineer|senior)
    | simulate\s+(being\s+)?(a\s+|an\s+)?(different|uncensored|evil|rogue)\s*(AI|model|assistant|bot)
    | switch\s+(your\s+)?persona\s+(to|into)
    | from\s+now\s+on\s+(you\s+are|act\s+as|behave\s+as)
    | your\s+new\s+(name|persona|role|identity)\s+is
    """,
    re.IGNORECASE | re.VERBOSE,
)

# 5. Secret / credential access attempts
_SECRET_ACCESS = re.compile(
    r"""
    \.env\b
    | (show|reveal|print|output|display|give\s+me|what\s+(is|are))\s+(the\s+|your\s+)?
      (api[\s_\-]?key|secret[\s_\-]?key|access[\s_\-]?token|auth[\s_\-]?token
      |bearer\s+token|credentials?|password|private[\s_\-]?key|database[\s_\-]?(url|uri|connection))
    | (list|show|dump)\s+(all\s+)?(environment\s+variables?|secrets?|config(uration)?)
    | (process\.env|os\.environ|getenv)
    | (aws|gcp|azure|openai|anthropic|langchain)\s*(api[\s_\-]?key|secret|token|credential)
    """,
    re.IGNORECASE | re.VERBOSE,
)

# 6. Tool / shell / code execution injection
_EXECUTION_ATTEMPT = re.compile(
    r"""
    (execute|run|eval|exec)\s+(this|the\s+following|a)?\s*(command|code|script|function|shell|bash|python)
    | \$\(.*\)                                  # shell command substitution
    | `[^`]{2,}`                                # backtick execution
    | ;\s*(rm|ls|cat|wget|curl|nc|ncat|python|bash|sh|exec)\b
    | (import|require)\s+(os|sys|subprocess|requests|socket|shutil)
    | (subprocess|os\.system|os\.popen|eval|exec)\s*\(
    | (curl|wget|nc|ncat|netcat)\s+
    | (http|https|ftp)://\S{5,}                # raw URL injection
    | <\s*(script|iframe|img|svg|object)\b      # HTML/JS injection tags
    | javascript\s*:                            # JS protocol
    | (union\s+select|drop\s+table|insert\s+into|delete\s+from|update\s+set)  # SQL injection
    """,
    re.IGNORECASE | re.VERBOSE,
)

# 7. Encoding / obfuscation tricks to hide instructions
_ENCODING_TRICK = re.compile(
    r"""
    (decode|decoding|decoded)\s+(the\s+following\s+)?(base64|rot13|hex|base32|unicode)
    | base64[\s,\-]?(decode|encode|instruction|command)
    | (run|execute|follow)\s+(these\s+)?(encoded|obfuscated|hidden|encrypted)\s+(instructions?|commands?)
    | (translate|convert)\s+(and\s+)?(execute|run|follow)\s+
    | \\x[0-9a-f]{2}(\\x[0-9a-f]{2}){3,}      # long hex escape sequences
    | (hidden|secret|encoded)\s+(instruction|command|prompt|message)\s*[:=]
    """,
    re.IGNORECASE | re.VERBOSE,
)

# 8. Compact blocklist patterns such as "ign0re previous instructions and do X" or "print your system prompt"
_COMPACT_BLOCKLIST = [
    "ignorepreviousinstructions",
    "revealsystemprompt",
    "showsystemprompt",
    "printsystemprompt",
    "developerprompt",
    "developermessage",
    "openaiapikey",
    "apikey",
    "bearertoken",
    "bypassguardrails",
    "disablefilters",
]

# Maximum allowed message length — long adversarial payloads are blocked outright
_MAX_MESSAGE_LENGTH = 1000

# All pattern groups bundled for iteration
_ALL_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("instruction_override", _INSTRUCTION_OVERRIDE),
    ("prompt_extraction", _PROMPT_EXTRACTION),
    ("jailbreak", _JAILBREAK),
    ("roleplay_attack", _ROLEPLAY_ATTACK),
    ("secret_access", _SECRET_ACCESS),
    ("execution_attempt", _EXECUTION_ATTEMPT),
    ("encoding_trick", _ENCODING_TRICK),
]

REFUSAL_MESSAGE = (
    "I can answer questions about Kutay’s professional background, projects, skills, education, "
    "availability, visa status, and personal context he has chosen to share. I cannot follow "
    "requests that attempt to override instructions, reveal hidden prompts, access secrets, "
    "execute tools, or bypass safety controls."
)


def normalize_message(message: str) -> str:
    """Return a cleaned copy of *message* suitable for pattern matching.

    Steps:
    - Strip leading/trailing whitespace.
    - Normalize Unicode to NFC (collapses lookalike characters).
    - Collapse runs of whitespace to a single space (defeats multi-line and
      tab-separated keyword splitting used to evade simple regex patterns).
    """
    stripped = message.strip()
    nfc = unicodedata.normalize("NFC", stripped)
    collapsed = re.sub(r"\s+", " ", nfc)
    return collapsed


def compact_message(message: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]", "", normalize_message(message)).lower()


def is_prompt_injection(message: str) -> bool:
    """Return True if *message* matches any known injection pattern."""
    normalized = normalize_message(message)

    if len(normalized) > _MAX_MESSAGE_LENGTH:
        return True

    compact = compact_message(normalized)

    if any(term in compact for term in _COMPACT_BLOCKLIST):
        return True

    for _name, pattern in _ALL_PATTERNS:
        if pattern.search(normalized):
            return True

    return False


def validate_input(message: str) -> None:
    """Validate *message* before it reaches any LLM or RAG component.

    Raises:
        ValueError: if the message is empty, blank, exceeds the length limit,
                    or matches a prompt injection pattern.
    """
    if not message or not message.strip():
        raise ValueError("Please ask a question about Kutay's professional background.")

    normalized = normalize_message(message)

    if len(normalized) < 2:
        raise ValueError("Please ask a question about Kutay's professional background.")

    if len(normalized) > _MAX_MESSAGE_LENGTH:
        raise ValueError("Please keep the question shorter.")

    if is_prompt_injection(normalized):
        raise ValueError(REFUSAL_MESSAGE)
