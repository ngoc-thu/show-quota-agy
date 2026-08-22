"""Parser and normalizer for Antigravity API responses."""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from ..core.models import (
    QuotaSnapshot,
    QuotaInfo,
    QuotaGroup,
    QuotaBucket,
    QuotaStatus,
    ConnectionState,
    AppSettings,
)
from ..core.logger import logger


def parse_iso_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    if not dt_str:
        return None
    try:
        clean = dt_str.replace("Z", "+00:00")
        return datetime.fromisoformat(clean)
    except Exception as e:
        logger.debug("Failed to parse datetime %s: %s", dt_str, e)
        return None


def categorize_model(model_id: str, display_name: str) -> str:
    name_lower = (model_id + " " + display_name).lower()
    if "claude" in name_lower:
        return "Claude"
    elif "gpt" in name_lower:
        return "GPT"
    elif "gemini" in name_lower:
        return "Gemini"
    return "Other"


def parse_quota_response(
    models_json: Dict[str, Any],
    summary_json: Optional[Dict[str, Any]] = None,
    settings: Optional[AppSettings] = None,
) -> QuotaSnapshot:
    """Parses raw models and summary JSON into a clean QuotaSnapshot."""
    if settings is None:
        settings = AppSettings()

    now = datetime.now(timezone.utc)
    models_dict: Dict[str, QuotaInfo] = {}

    default_model_id = models_json.get("defaultAgentModelId", "gemini-3.6-flash-high")
    raw_models = models_json.get("models", {})

    for model_id, mdata in raw_models.items():
        # Filter out purely internal/empty test slots if needed, or include all user-facing
        display_name = mdata.get("displayName", model_id)
        quota_data = mdata.get("quotaInfo", {})

        rem_frac = quota_data.get("remainingFraction")
        if rem_frac is None:
            rem_frac = 1.0
        rem_frac = max(0.0, min(1.0, float(rem_frac)))
        percentage = round(rem_frac * 100, 1)

        reset_iso = quota_data.get("resetTime")
        reset_dt = parse_iso_datetime(reset_iso)

        status = settings.compute_status(percentage)
        supports_thinking = mdata.get("supportsThinking", False)
        recommended = mdata.get("recommended", False)
        category = categorize_model(model_id, display_name)

        models_dict[model_id] = QuotaInfo(
            model_id=model_id,
            model_name=display_name,
            remaining_fraction=rem_frac,
            percentage=percentage,
            reset_time=reset_dt,
            reset_time_iso=reset_iso,
            status=status,
            supports_thinking=supports_thinking,
            recommended=recommended,
            category=category,
        )

    # Parse groups from summary_json if present
    groups_list: List[QuotaGroup] = []
    if summary_json and "groups" in summary_json:
        for gdata in summary_json.get("groups", []):
            gid = gdata.get("displayName", "Group").lower().replace(" ", "-")
            gname = gdata.get("displayName", "Quota Group")
            gdesc = gdata.get("description", "")
            buckets: List[QuotaBucket] = []

            for bdata in gdata.get("buckets", []):
                bid = bdata.get("bucketId", "bucket")
                bname = bdata.get("displayName", bid)
                window = bdata.get("window", "standard")
                b_frac = float(bdata.get("remainingFraction", 1.0))
                b_pct = round(b_frac * 100, 1)
                b_reset_iso = bdata.get("resetTime")
                b_reset_dt = parse_iso_datetime(b_reset_iso)
                b_desc = bdata.get("description", "")

                buckets.append(
                    QuotaBucket(
                        bucket_id=bid,
                        display_name=bname,
                        window=window,
                        remaining_fraction=b_frac,
                        percentage=b_pct,
                        reset_time=b_reset_dt,
                        reset_time_iso=b_reset_iso,
                        description=b_desc,
                    )
                )

            groups_list.append(
                QuotaGroup(
                    group_id=gid,
                    display_name=gname,
                    description=gdesc,
                    buckets=buckets,
                )
            )

    return QuotaSnapshot(
        timestamp=now,
        models=models_dict,
        groups=groups_list,
        default_model_id=default_model_id,
        connection_state=ConnectionState.CONNECTED,
        is_stale=False,
        last_updated_str=now.strftime("%H:%M:%S"),
    )
