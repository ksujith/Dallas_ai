import json
import os
import textwrap
from urllib.parse import urljoin

import requests
import streamlit as st

# ---------------------------
# Helpers
# ---------------------------

def guess_api_base() -> str:
    # If you're running Streamlit on localhost, default to FastAPI's 8000
    host = os.environ.get("BOUNDLY_API_BASE")
    if host:
        return host.rstrip("/")
    return "http://localhost:8000"


def try_get(url: str, timeout: float = 3.0):
    try:
        r = requests.get(url, timeout=timeout)
        return r
    except Exception:
        return None


def health_check(base: str) -> dict:
    base = base.rstrip("/")
    # Try a few common endpoints to determine reachability
    for path in ["/health", "/", "/docs"]:
        r = try_get(base + path)
        if r and r.ok:
            try:
                data = r.json() if "application/json" in r.headers.get("content-type", "") else {}
            except Exception:
                data = {}
            return {"ok": True, "path": path, "status": data.get("status") or "reachable"}
    return {"ok": False, "path": None, "status": "unreachable"}


def post_query(base: str, question: str) -> requests.Response:
    url = base.rstrip("/") + "/boundly/query"
    payload = {"question": question}
    headers = {"Content-Type": "application/json"}
    return requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)


def parse_answer(payload: dict) -> dict:
    # Normalize answer fields from different shapes
    answer = payload.get("answer") or payload.get("result") or payload.get("output")
    parsed = None
    if isinstance(answer, str):
        try:
            parsed = json.loads(answer)
        except Exception:
            parsed = {"explanation": answer}
    elif isinstance(answer, dict):
        parsed = answer
    else:
        parsed = {}

    return {
        "decision": (parsed.get("decision") or "unknown").lower(),
        "explanation": parsed.get("explanation") or (answer if isinstance(answer, str) else ""),
        "citations": parsed.get("citations") or payload.get("citations") or [],
        "_raw": parsed or answer or payload,
    }


# ---------------------------
# UI
# ---------------------------

st.set_page_config(page_title="BoundLy H1B — UI", page_icon="🧭", layout="centered")

st.title("BoundLy H1B Assistant")
st.caption("FastAPI backend • POST /boundly/query • Docs at /docs")

with st.sidebar:
    st.header("Settings")
    api_base = st.text_input("API Base URL", value=guess_api_base(), help="Where your FastAPI is running.")
    hc = health_check(api_base)
    if hc["ok"]:
        st.success(f"API reachable via {hc['path']} (status: {hc['status']})", icon="✅")
    else:
        st.error("API unreachable — check the base URL and server status.", icon="🚨")
    docs_url = api_base.rstrip("/") + "/docs"
    st.markdown(f"[Open API docs]({docs_url})")

st.subheader("Ask a question")

examples = [
    "Is wage level 1 enough for H‑1B approval?",
    "Can a part-time job be H‑1B eligible?",
    "Does a marketing degree qualify for a software analyst role?",
]

cols = st.columns(len(examples))
for i, ex in enumerate(examples):
    if cols[i].button(ex):
        st.session_state.setdefault("question", ex)

with st.form("ask_form", clear_on_submit=False):
    question = st.text_area(
        "Question",
        value=st.session_state.get("question", ""),
        height=140,
        placeholder="e.g., Does a BA in Computer Science qualify for an H‑1B specialty occupation?",
    )
    submit = st.form_submit_button("Ask BoundLy")

if submit:
    if not question.strip():
        st.warning("Please enter a question first.")
    else:
        with st.spinner("Contacting BoundLy..."):
            try:
                resp = post_query(api_base, question.strip())
                payload = resp.json()
                if not resp.ok:
                    detail = payload.get("detail") if isinstance(payload, dict) else None
                    raise RuntimeError(detail or f"Request failed: {resp.status_code}")
                parsed = parse_answer(payload)
                st.session_state["last_raw"] = payload
                st.session_state["last_parsed"] = parsed
            except Exception as e:
                st.error(f"{type(e).__name__}: {e}")

parsed = st.session_state.get("last_parsed")
raw = st.session_state.get("last_raw")

if parsed:
    # Decision badge
    decision = str(parsed.get("decision", "unknown")).lower()
    badge = {
        "yes": ("✅ YES", "green"),
        "no": ("⛔ NO", "red"),
        "unknown": ("❓ UNKNOWN", "gray"),
    }.get(decision, (decision.upper(), "gray"))

    st.markdown(
        f"<div style='display:inline-block;padding:6px 10px;border-radius:999px;background:{badge[1]};color:white;font-weight:600;'>"
        f"Decision: {badge[0]}</div>",
        unsafe_allow_html=True,
    )

    if parsed.get("explanation"):
        st.markdown("### Explanation")
        st.write(parsed["explanation"])  # supports markdown-ish text

    citations = parsed.get("citations") or []
    if citations:
        st.markdown("### Citations")
        for i, c in enumerate(citations, 1):
            st.markdown(f"- {c}")

    # Raw + download
    with st.expander("Show raw response JSON"):
        st.code(json.dumps(raw, indent=2), language="json")
        st.download_button(
            label="Download response.json",
            data=json.dumps(raw, indent=2).encode("utf-8"),
            file_name="boundly_response.json",
            mime="application/json",
        )

st.divider()
st.caption("Built for POST /boundly/query • Health probes at /, /health, /docs • Change base URL from the sidebar.")
