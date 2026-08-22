"""Mock data fixtures mimicking real Google CloudCode PA responses."""

MOCK_FETCH_MODELS_RESPONSE = {
    "defaultAgentModelId": "gemini-3.6-flash-high",
    "models": {
        "gemini-3.6-flash-high": {
            "displayName": "Gemini 3.6 Flash (High)",
            "supportsImages": True,
            "supportsThinking": True,
            "recommended": True,
            "quotaInfo": {
                "remainingFraction": 0.8875201,
                "resetTime": "2026-08-22T12:51:42Z",
            },
        },
        "gemini-3.1-pro-high": {
            "displayName": "Gemini 3.1 Pro (High)",
            "supportsImages": True,
            "supportsThinking": True,
            "recommended": True,
            "quotaInfo": {
                "remainingFraction": 0.8875201,
                "resetTime": "2026-08-22T12:51:42Z",
            },
        },
        "claude-opus-4-6-thinking": {
            "displayName": "Claude Opus 4.6 (Thinking)",
            "supportsImages": True,
            "supportsThinking": True,
            "recommended": True,
            "quotaInfo": {
                "remainingFraction": 0.425,
                "resetTime": "2026-08-22T14:05:16Z",
            },
        },
        "claude-sonnet-4-6": {
            "displayName": "Claude Sonnet 4.6 (Thinking)",
            "supportsImages": True,
            "supportsThinking": True,
            "recommended": True,
            "quotaInfo": {
                "remainingFraction": 0.425,
                "resetTime": "2026-08-22T14:05:16Z",
            },
        },
        "gpt-oss-120b-medium": {
            "displayName": "GPT-OSS 120B (Medium)",
            "supportsThinking": True,
            "recommended": False,
            "quotaInfo": {
                "remainingFraction": 0.08,
                "resetTime": "2026-08-22T14:05:16Z",
            },
        },
    },
}

MOCK_QUOTA_SUMMARY_RESPONSE = {
    "groups": [
        {
            "displayName": "Gemini Models",
            "description": "Models within this group: Gemini Flash, Gemini Pro",
            "buckets": [
                {
                    "bucketId": "gemini-weekly",
                    "displayName": "Weekly Limit Remaining",
                    "window": "weekly",
                    "resetTime": "2026-08-25T04:51:06Z",
                    "remainingFraction": 0.822,
                },
                {
                    "bucketId": "gemini-5h",
                    "displayName": "Five Hour Limit Remaining",
                    "window": "5h",
                    "resetTime": "2026-08-22T12:51:42Z",
                    "remainingFraction": 0.887,
                },
            ],
        },
        {
            "displayName": "Claude and GPT models",
            "description": "Models within this group: Claude Opus, Claude Sonnet, GPT-OSS",
            "buckets": [
                {
                    "bucketId": "3p-weekly",
                    "displayName": "Weekly Limit Remaining",
                    "window": "weekly",
                    "resetTime": "2026-08-28T09:05:16Z",
                    "remainingFraction": 0.919,
                },
                {
                    "bucketId": "3p-5h",
                    "displayName": "Five Hour Limit Remaining",
                    "window": "5h",
                    "resetTime": "2026-08-22T14:05:16Z",
                    "remainingFraction": 0.425,
                },
            ],
        },
    ]
}
