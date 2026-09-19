import os
import io
import tempfile

import streamlit as st
from PIL import Image
from gradio_client import Client, handle_file

# ============================================================
# YOSEF AI — TRY-ON STUDIO
# Free backend: Hugging Face ZeroGPU / IDM-VTON
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
    padding: 30px;
    border-radius: 24px;
    border: 1px solid rgba(255,255,255,.12);
    background: rgba(16,22,34,.86);
    margin-bottom: 22px;
}
.hero h1 {font-size: 42px; margin: 0 0 8px 0;}
.hero p {color: #aeb8c8; margin: 0;}
.card {
    padding: 20px;
    border-radius: 20px;
    border: 1px solid rgba(255,255,255,.10);
    background: rgba(17,23,35,.78);
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
    <div class="badge">● FREE AI VIRTUAL TRY-ON</div>
    <h1>👕 YOSEF AI — TRY-ON STUDIO</h1>
    <p>ارفع صورة الشخص وصورة اللبس، والـAI هيعمل Virtual Try-On.</p>
</div>
""", unsafe_allow_html=True)

# Free Hugging Face Space.
# It is currently running on ZeroGPU and exposes the IDM-VTON /tryon API.
SPACE_ID = "yisol/IDM-VTON"
HF_TOKEN = st.secrets.get("HF_TOKEN", "")

def save_upload(uploaded, suffix=".png"):
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    with open(path, "wb") as f:
        f.write(uploaded.getvalue())
    return path

def run_tryon(person_path, garment_path, garment_description):
    client = Client(
        SPACE_ID,
        token=HF_TOKEN if HF_TOKEN else None,
        verbose=False,
    )

    # IDM-VTON's documented Gradio endpoint is /tryon.
    result = client.predict(
        dict={
            "background": handle_file(person_path),
            "layers": [],
            "composite": None,
        },
        garm_img=handle_file(garment_path),
        garment_des=garment_description,
        is_checked=True,
        is_checked_crop=False,
        denoise_steps=30,
        seed=42,
        api_name="/tryon",
    )

    # The first returned value is the generated try-on image.
    if isinstance(result, (list, tuple)) and len(result) > 0:
        result = result[0]

    if isinstance(result, dict):
        result = result.get("path") or result.get("url") or result.get("image")

    if not result:
        raise RuntimeError("الـAI رجّع نتيجة فارغة.")

    if isinstance(result, str) and result.startswith(("http://", "https://")):
        import requests
        response = requests.get(result, timeout=60)
        response.raise_for_status()
        data = response.content
    else:
        with open(str(result), "rb") as f:
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
        "ارفع صورة واضحة للملابس",
        type=["jpg", "jpeg", "png", "webp"],
        key="outfit",
    )
    st.markdown("</div>", unsafe_allow_html=True)

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

st.markdown('<div class="card">', unsafe_allow_html=True)

garment_type = st.selectbox(
    "👔 نوع اللبس",
    ["Upper body / قميص أو تيشيرت أو جاكيت",
     "Lower body / بنطلون أو شورت",
     "Dress / فستان"],
    index=0,
)

if garment_type.startswith("Upper"):
    garment_description = "a realistic upper-body garment, shirt, t-shirt or jacket"
elif garment_type.startswith("Lower"):
    garment_description = "realistic lower-body clothing, pants or shorts"
else:
    garment_description = "a realistic dress"

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

    person_path = save_upload(person_file)
    garment_path = save_upload(outfit_file)

    progress = st.progress(0)
    status = st.empty()

    try:
        status.info("🔗 الاتصال بمحرك الـAI المجاني...")
        progress.progress(15)

        status.info("📤 رفع الصور...")
        progress.progress(30)

        status.info("🧠 الـAI بيعمل Virtual Try-On...")
        progress.progress(45)

        result_image, result_bytes = run_tryon(
            person_path,
            garment_path,
            garment_description,
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
        st.error("❌ حصل خطأ أثناء تشغيل الـAI")
        st.code(str(e))

    finally:
        for path in (person_path, garment_path):
            try:
                os.remove(path)
            except Exception:
                pass

st.caption("YOSEF AI • Virtual Try-On • Hugging Face ZeroGPU")
