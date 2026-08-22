# Antigravity Protocol & API Architecture

This document specifies the communication mechanisms, authentication discovery, and live quota endpoints used by Google Antigravity on Linux / Ubuntu.

---

## 1. Authentication Discovery

Antigravity uses the freedesktop.org Secret Service API over DBus (`org.freedesktop.secrets`) to store and retrieve credentials:

- **Service Name**: `gemini`
- **Username / Account**: `antigravity`
- **Schema**: `org.freedesktop.Secret.Generic`

The secret value is a JSON payload:
```json
{
  "token": {
    "access_token": "ya29.a0...",
    "token_type": "Bearer",
    "refresh_token": "1//04...",
    "expiry": "2026-08-21T17:39:28.948475876+07:00"
  },
  "auth_method": "consumer"
}
```

Fallback credential locations:
- `~/.gemini/antigravity-cli/`
- Local CLI session tokens

---

## 2. API Endpoints

Antigravity communicates with Google CloudCode PA (Prediction Service) backend:

### 2.1 Available Models & Quotas
- **URL**: `https://cloudcode-pa.googleapis.com/v1internal:fetchAvailableModels`
- **Method**: `POST`
- **Headers**:
  - `Authorization: Bearer <access_token>`
  - `Content-Type: application/json`
  - `User-Agent: antigravity-cli/1.0`
- **Body**: `{}`
- **Response**:
```json
{
  "models": {
    "claude-opus-4-6-thinking": {
      "displayName": "Claude Opus 4.6 (Thinking)",
      "quotaInfo": {
        "remainingFraction": 0.7865556,
        "resetTime": "2026-08-21T14:05:16Z"
      },
      "supportsThinking": true,
      "recommended": true
    },
    "gemini-3.6-flash-high": {
      "displayName": "Gemini 3.6 Flash (High)",
      "quotaInfo": {
        "remainingFraction": 0.8875201,
        "resetTime": "2026-08-21T12:51:42Z"
      }
    }
  },
  "defaultAgentModelId": "gemini-3.6-flash-high"
}
```

### 2.2 Quota Summary & Rate Limit Groups
- **URL**: `https://cloudcode-pa.googleapis.com/v1internal:retrieveUserQuotaSummary`
- **Method**: `POST`
- **Body**: `{}`
- **Response**:
```json
{
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
          "remainingFraction": 0.8222208
        },
        {
          "bucketId": "gemini-5h",
          "displayName": "Five Hour Limit Remaining",
          "window": "5h",
          "resetTime": "2026-08-21T12:51:42Z",
          "remainingFraction": 0.8875201
        }
      ]
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
          "remainingFraction": 0.9198667
        },
        {
          "bucketId": "3p-5h",
          "displayName": "Five Hour Limit Remaining",
          "window": "5h",
          "resetTime": "2026-08-21T14:05:16Z",
          "remainingFraction": 0.7865556
        }
      ]
    }
  ]
}
```

---

## 3. Process & Bridge Detection

The monitor detects running Antigravity instances through:
1. `agy` CLI processes (`ps aux | grep agy`)
2. Antigravity IntelliJ Companion Bridge (`dev.matasar.antigravity.bridge.StdioBridge`)
3. Open sockets on localhost.
