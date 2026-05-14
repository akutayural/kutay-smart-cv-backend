ANSWER_EVALSET = [
    {
        "question": "What has Kutay built with FastAPI?",
        "expected_any_groups": [
            ["FastAPI"],
            ["backend", "APIException", "financial", "fraud", "RAG", "Smart CV"],
        ],
        "forbidden_keywords": ["React Native", "Go", "Rust"],
    },
    {
        "question": "Does Kutay require visa sponsorship?",
        "expected_any_groups": [
            ["sponsorship", "sponsored"],
            ["Skilled Worker Visa", "visa transfer"],
        ],
        "forbidden_keywords": ["British citizen", "no sponsorship required", "does not require sponsorship"],
    },
    {
        "question": "What open source work has Kutay done?",
        "expected_any_groups": [
            ["APIException"],
            ["FastAPI"],
            ["open-source", "open source"],
        ],
        "forbidden_keywords": ["Django REST framework maintainer", "React maintainer"],
    },
]
