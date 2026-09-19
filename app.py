import io
import os
import tempfile
from pathlib import Path

import streamlit as st
from PIL import Image
from gradio_client import Client, handle_file

# ============================================================
# YOSEF AI — TRY-ON STUDIO
# Free AI backend: Hugging Face Gradio / ZeroGPU Space
# ============================================================

st.set_page_config(
    page_title="Yosef AI — Try-On Studio",
    page_icon="👕",
    layout="wide",
)

st.markdown("""
<style>
.stApp {
    background:
        radial-gradient(circle at 10% 10%, #10223d 0%, transparent 32%),
        radial-gradient(circle at 90% 10%, #182b20 0%, transparent 30%),
        #080b12;
    color: #f7f7fb;
}
.block-container {max-width: 1150px; padding-top: 2rem;}
.hero {
    padding: 28px;
    border-radius: 24px;
    border: 1px solid rgba(255,255,255,.12);
    background: rgba(16,22,34,.82);
    margin-bottom: 22px;
}
.hero h1 {font-size: 42px; margin: 0 0 8px 0;}
.hero p {color: #aeb8c8; margin: 0;}
.card {
    padding: 20px;
    border-radius: 20px;
    border: 1px solid rgba(255,255,255,.10);
    background: rgba(17,23,35,.75);
    margin-bottom: 18px;
}
.badge {
    display:inline-block;
    padding:6px 12px;
    border-radius:999px;
    background:#123d2b;
    color:#8ff0bd;
    font-size:13px;
    margin-bottom:10px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <div class="badge">● FREE AI BACKEND</div>
    <h1>👕 YOSEF AI — TRY-ON STUDIO</h1>
    <p>ارفع صورة الشخص وصورة اللبس، وسيتم تنفيذ الـ Virtual Try-On بالـAI.</p>
</div>
""", unsafe_allow_html=True)


# ----------------------------
# Backend configuration
# ----------------------------
# You can override these later from Streamlit Secrets:
# HF_SPACE_ID = "yourname/your-space"
# HF_TOKEN = "hf_..."
SPACE_ID = st.secrets.get("HF_SPACE_ID", "tryitonvirtual/virtual-tryon")
HF_TOKEN = st.secrets.get("HF_TOKEN", "")

if "client" not in st.session_state:
    st.session_state.client = None
if "api_info" not in st.session_state:
    st.session_state.api_info = None
if "api_name" not in st.session_state:
    st.session_state.api_name = None


def connect_backend():
    if st.session_state.client is None:
        st.session_state.client = Client(
            SPACE_ID,
            token=HF_TOKEN if HF_TOKEN else None,
            verbose=False,
        )
    if st.session_state.api_info is None:
        st.session_state.api_info = st.session_state.client.view_api(
            all_endpoints=True,
            print_info=False,
            return_format="dict",
        )

    named = st.session_state.api_info.get("named_endpoints", {})
    unnamed = st.session_state.api_info.get("unnamed_endpoints", {})

    # Prefer an endpoint with 2+ inputs and an image/file output.
    candidates = []

    for name, info in named.items():
        params = info.get("parameters", [])
        returns = info.get("returns", [])
        score = 0

        if len(params) >= 2:
            score += 5

        components = " ".join(
            str(p.get("component", "")).lower() for p in params
        )
        return_components = " ".join(
            str(r.get("component", "")).lower() for r in returns
        )

        if "image" in components:
            score += 3
        if "image" in return_components or "file" in return_components:
            score += 5
        if any(
            word in name.lower()
            for word in ("try", "tryon", "try-on", "generate", "predict", "inference")
        ):
            score += 4

        candidates.append((score, name, info))

    if not candidates:
        raise RuntimeError("لم يتم العثور على API مناسب داخل الـSpace.")

    candidates.sort(reverse=True, key=lambda x: x[0])
    _, api_name, info = candidates[0]

    st.session_state.api_name = api_name
    return st.session_state.client, api_name, info


def save_uploaded(uploaded, suffix=".png"):
    data = uploaded.getvalue()
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    with open(path, "wb") as f:
        f.write(data)
    return path


def choose_input_values(parameters, person_path, outfit_path):
    """
    Build arguments for the discovered Gradio endpoint.
    We map image inputs by their labels and use defaults for
    extra parameters when the Space exposes them.
    """
    values = {}

    image_slots = []
    for p in parameters:
        component = str(p.get("component", "")).lower()
        label = str(p.get("label", "")).lower()
        python_type = str(p.get("python_type", "")).lower()

        is_image = (
            component in {"image", "file"}
            or "filepath" in python_type
            or "image" in label
            or "photo" in label
            or "garment" in label
            or "cloth" in label
            or "person" in label
        )

        if is_image:
            image_slots.append(p)

    used_person = False
    used_outfit = False

    for p in parameters:
        label = str(p.get("label", "")).lower()
        component = str(p.get("component", "")).lower()
        name = p.get("parameter_name") or p.get("label")

        if not name:
            continue

        # Strong label matching first.
        if any(x in label for x in ("garment", "cloth", "clothing", "outfit", "dress")):
            values[name] = handle_file(outfit_path)
            used_outfit = True
            continue

        if any(x in label for x in ("person", "human", "model", "photo", "background", "source")):
            values[name] = handle_file(person_path)
            used_person = True
            continue

        # Defaults for common optional settings.
        if component == "checkbox":
            values[name] = True
        elif component in {"number", "slider"}:
            example = p.get("example_input")
            if isinstance(example, (int, float)):
                values[name] = example
        elif component in {"radio", "dropdown"}:
            example = p.get("example_input")
            if example not in (None, ""):
                values[name] = example

    # Fallback: map the first image-like inputs to person then outfit.
    remaining = [
        p for p in image_slots
        if (p.get("parameter_name") or p.get("label")) not in values
    ]

    if not used_person and remaining:
        name = remaining.pop(0).get("parameter_name") or remaining[0].get("label")
        values[name] = handle_file(person_path)

    if not used_outfit and remaining:
        name = remaining.pop(0).get("parameter_name") or remaining[0].get("label")
        values[name] = handle_file(outfit_path)

    # If the endpoint needs a category/type and did not provide an example,
    # use a conventional upper-body value.
    for p in parameters:
        name = p.get("parameter_name") or p.get("label")
        if not name or name in values:
            continue
        label = str(p.get("label", "")).lower()
        component = str(p.get("component", "")).lower()

        if component in {"radio", "dropdown"} and any(
            x in label for x in ("category", "type", "garment type", "clothing type")
        ):
            values[name] = "upperbody"

    return values


def extract_result(result):
    """Find an image/file path or URL inside Gradio's returned object."""
    if result is None:
        return None

    if isinstance(result, (str, Path)):
        value = str(result)
        if os.path.exists(value):
            return value
        if value.startswith("http://") or value.startswith("https://"):
            return value

    if isinstance(result, dict):
        for key in ("path", "url", "image", "output", "result"):
            if key in result:
                found = extract_result(result[key])
                if found:
                    return found
        for value in result.values():
            found = extract_result(value)
            if found:
                return found

    if isinstance(result, (list, tuple)):
        for item in result:
            found = extract_result(item)
            if found:
                return found

    return None


def load_result_image(result):
    path_or_url = extract_result(result)
    if not path_or_url:
        return None, None

    if path_or_url.startswith(("http://", "https://")):
        import requests
        r = requests.get(path_or_url, timeout=60)
        r.raise_for_status()
        image = Image.open(io.BytesIO(r.content)).convert("RGB")
        return image, r.content

    with open(path_or_url, "rb") as f:
        data = f.read()
    image = Image.open(io.BytesIO(data)).convert("RGB")
    return image, data


# ----------------------------
# Inputs
# ----------------------------
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 👤 1 — صورة الشخص")
    person_file = st.file_uploader(
        "ارفع صورة واضحة للشخص",
        type=["jpg", "jpeg", "png", "webp"],
        key="person",
    )
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 👕 2 — صورة اللبس")
    outfit_file = st.file_uploader(
        "ارفع صورة واضحة للملابس / القطعة",
        type=["jpg", "jpeg", "png", "webp"],
        key="outfit",
    )
    st.markdown("</div>", unsafe_allow_html=True)


# ----------------------------
# Preview
# ----------------------------
if person_file or outfit_file:
    c1, c2 = st.columns(2)
    if person_file:
        with c1:
            st.markdown("**👤 الشخص**")
            st.image(person_file, use_container_width=True)
    if outfit_file:
        with c2:
            st.markdown("**👕 اللبس**")
            st.image(outfit_file, use_container_width=True)


# ----------------------------
# Controls
# ----------------------------
st.markdown('<div class="card">', unsafe_allow_html=True)

style = st.selectbox(
    "🎨 الستايل",
    ["Realistic", "Studio", "Natural"],
    index=0,
)

ratio = st.selectbox(
    "📐 المقاس",
    ["9:16 — Reels", "1:1 — Square", "4:5 — Instagram", "16:9 — Landscape"],
    index=0,
)

st.markdown("</div>", unsafe_allow_html=True)


# ----------------------------
# Generate
# ----------------------------
if st.button("✨ جرّب اللبس بالـAI", use_container_width=True, type="primary"):

    if not person_file:
        st.error("ارفع صورة الشخص أولًا.")
        st.stop()

    if not outfit_file:
        st.error("ارفع صورة اللبس أولًا.")
        st.stop()

    person_path = save_uploaded(person_file, ".png")
    outfit_path = save_uploaded(outfit_file, ".png")

    progress = st.progress(0)
    status = st.empty()

    try:
        status.info("🔗 الاتصال بمحرك الـAI...")
        progress.progress(15)

        client, api_name, endpoint_info = connect_backend()

        status.info(f"🧠 تجهيز Virtual Try-On...  ({api_name})")
        progress.progress(30)

        parameters = endpoint_info.get("parameters", [])
        kwargs = choose_input_values(parameters, person_path, outfit_path)

        if len(kwargs) < 2:
            raise RuntimeError(
                "الـAPI لم يتعرف على صور الشخص واللبس. "
                "لو ظهر هذا الخطأ، ابعتلي صورة الخطأ وسأظبط الـmapping."
            )

        status.info("🎨 الـAI بيعمل الـTry-On الآن...")
        progress.progress(45)

        job = client.submit(
            api_name=api_name,
            **kwargs,
        )

        result = job.result()
        progress.progress(90)

        result_image, result_bytes = load_result_image(result)

        if result_image is None:
            raise RuntimeError(
                f"تم تنفيذ الـAPI لكن لم أستطع استخراج صورة النتيجة.\n\n"
                f"Raw result: {result}"
            )

        progress.progress(100)
        status.success("✅ خلصت! النتيجة جاهزة.")

        st.markdown("## ✨ النتيجة")
        st.image(result_image, use_container_width=True)

        st.download_button(
            "⬇️ حفظ الصورة",
            data=result_bytes,
            file_name="yosef_ai_tryon.png",
            mime="image/png",
            use_container_width=True,
        )

    except Exception as e:
        progress.empty()
        status.empty()
        st.error("❌ حصل خطأ أثناء تنفيذ الـAI")
        st.code(str(e))

    finally:
        for p in (person_path, outfit_path):
            try:
                os.remove(p)
            except Exception:
                pass


st.caption(
    "YOSEF AI • Virtual Try-On • Hugging Face Gradio backend"
)
