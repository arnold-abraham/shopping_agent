import logging
import os
import tempfile

import streamlit as st

from shopping_agent.agent import build_agent
from shopping_agent.config import ConfigError, configure_logging
from shopping_agent.db import ensure_db

configure_logging()
logger = logging.getLogger(__name__)

IMAGE_PROMPT_PREFIX = "I uploaded a product image"

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="AI Shopping Assistant", page_icon="🛒", layout="wide")

st.title("🛒 AI Shopping Assistant")
st.caption("Tell me what you want — I'll search, rate, and order the best match for you.")


@st.cache_resource
def get_agent():
    ensure_db()
    return build_agent()


try:
    agent = get_agent()
except ConfigError as exc:
    st.error(str(exc))
    st.stop()


def run_agent(messages: list[dict]) -> str:
    """Invoke the agent and return its reply, or a user-facing error message."""
    try:
        result = agent.invoke({"messages": messages})
    except Exception:
        logger.exception("Agent invocation failed")
        return "Sorry, something went wrong while contacting the assistant. Please try again."
    return result["messages"][-1].content.replace("`", "")


# ---------------------------------------------------------------------------
# Chat state
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------------------------------------------------------------------
# Sidebar — new chat and shop by image
# ---------------------------------------------------------------------------
with st.sidebar:
    if st.button("🗑️ New chat", use_container_width=True, disabled=not st.session_state.messages):
        st.session_state.messages = []
        st.rerun()

    st.header("Shop by Image")
    st.caption("Upload a photo of a product and I'll find similar items in our store.")

    uploaded_file = st.file_uploader("Upload product image", type=["jpg", "jpeg", "png", "webp"])

    if uploaded_file:
        st.image(uploaded_file, use_container_width=True)

    if uploaded_file and st.button("Find similar products", use_container_width=True):
        suffix = os.path.splitext(uploaded_file.name)[1] or ".jpg"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.getvalue())
            image_path = tmp.name

        prompt = (
            f"{IMAGE_PROMPT_PREFIX}. Please analyze it and find similar products in the store. "
            f"Image path: {image_path}"
        )
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.session_state.pending_image = image_path
        st.rerun()

# ---------------------------------------------------------------------------
# Chat history
# ---------------------------------------------------------------------------
# Render history — show a friendlier label for image-search messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "user" and msg["content"].startswith(IMAGE_PROMPT_PREFIX):
            filename = msg["content"].split("Image path:")[-1].strip()
            st.markdown(f"Searching by image: **{os.path.basename(filename)}**")
        else:
            st.markdown(msg["content"].replace("$", r"\$"))

# ---------------------------------------------------------------------------
# Run agent if there's an unprocessed message (image upload triggers this)
# ---------------------------------------------------------------------------
if (
    st.session_state.messages
    and st.session_state.messages[-1]["role"] == "user"
    and "pending_image" in st.session_state
):
    image_path = st.session_state.pop("pending_image")
    try:
        with st.chat_message("assistant"):
            with st.spinner("Analyzing image and searching…"):
                response = run_agent(st.session_state.messages)
            st.markdown(response.replace("$", r"\$"))
    finally:
        # The uploaded image is only needed for this one agent run.
        if os.path.exists(image_path):
            os.remove(image_path)

    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()

# ---------------------------------------------------------------------------
# Text input
# ---------------------------------------------------------------------------
if prompt := st.chat_input("e.g. I want organic honey under $15 with 4+ rating"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            response = run_agent(st.session_state.messages)
        st.markdown(response.replace("$", r"\$"))

    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()
