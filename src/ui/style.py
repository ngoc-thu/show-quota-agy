"""Custom CSS stylesheet for Antigravity Quota Monitor."""

APPLICATION_CSS = """
/* Antigravity Quota Monitor Stylesheet */

.quota-window {
    background-color: #18181b;
}

.quota-sidebar {
    background-color: #121214;
    border-right: 1px solid #27272a;
}

.quota-card {
    background-color: #27272a;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 12px;
    border: 1px solid #3f3f46;
}

.quota-card-header {
    font-size: 1.1rem;
    font-weight: bold;
    color: #f4f4f5;
}

.quota-model-title {
    font-weight: 600;
    font-size: 1.05rem;
    color: #fafafa;
}

.quota-model-id {
    font-size: 0.82rem;
    color: #a1a1aa;
}

.quota-pct-label {
    font-size: 1.25rem;
    font-weight: 800;
    color: #f4f4f5;
}

.quota-meta-label {
    font-size: 0.85rem;
    color: #a1a1aa;
}

.quota-badge {
    border-radius: 9999px;
    padding: 2px 8px;
    font-size: 0.75rem;
    font-weight: bold;
}

.quota-badge-healthy {
    background-color: rgba(16, 185, 129, 0.2);
    color: #34d399;
}

.quota-badge-warning {
    background-color: rgba(245, 158, 11, 0.2);
    color: #fbbf24;
}

.quota-badge-critical {
    background-color: rgba(239, 68, 68, 0.2);
    color: #f87171;
}

.quota-badge-recommended {
    background-color: rgba(138, 43, 226, 0.25);
    color: #c084fc;
}

.quota-accent-button {
    background-color: #7c3aed;
    color: white;
    font-weight: bold;
    border-radius: 8px;
    padding: 6px 14px;
}

.quota-accent-button:hover {
    background-color: #6d28d9;
}

/* Custom Progress Bars */
progressbar trough {
    min-height: 10px;
    border-radius: 5px;
    background-color: #3f3f46;
}

progressbar progress {
    min-height: 10px;
    border-radius: 5px;
    background-color: #7c3aed;
}

progressbar.healthy progress {
    background-color: #10b981;
}

progressbar.warning progress {
    background-color: #f59e0b;
}

progressbar.critical progress {
    background-color: #ef4444;
}

.status-pill {
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 0.85rem;
    font-weight: 600;
}

.status-pill-connected {
    background-color: rgba(16, 185, 129, 0.15);
    color: #10b981;
}

.status-pill-offline {
    background-color: rgba(156, 163, 175, 0.15);
    color: #9ca3af;
}

.status-pill-auth {
    background-color: rgba(245, 158, 11, 0.15);
    color: #f59e0b;
}
"""
