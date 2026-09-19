import streamlit as st
import time
import subprocess
import sys

# ============================================================
# YOSEF AI TRY-ON STUDIO — Single-file Streamlit app
# Higgsfield API integration
# ============================================================

st.set_page_config(
    page_title="Yosef AI — Try-On Studio",
    page_icon="👕",
    layout="wide",
)

# Install the official Higgsfield Python SDK automatically.
# This keeps the project as a single app.py file.
try:
    import higgsfield_client
except ImportError:
    with st.spinner("جاري تجهيز Higgsfield API لأول تشغيل..."):
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-q", "higgsfield-client"]
        )
    import higgsfield_client

# -----------------------------
# Styling
# -----------------------------
st.markdown("""
<style>
    .stApp {
        background:
            radial-gradient(circle at 15% 0%, rgba(125, 72, 255, .18), transparent 28%),
            radial-gradient(circle at 90% 10%, rgba(0, 220, 170, .12), transparent 25%),
            #090b12;
        color: #f7f7fb;
    }

    section[data-testid="stSidebar"] {
        background: #10131c;
    }

    .hero {
        padding: 28px 10px 18px 10px;
        text-align: center;
    }

    .hero h1 {
        font-size: 42px;
        margin-bottom: 5px;
        font-weight: 800;
        letter-spacing: -1px;
    }

    .hero p {
        color: #a7a9b6;
        font-size: 16px;
    }

    .card {
        background: rgba(25, 28, 39, .78);
        border: 1px solid rgba(255,255,255,.08);
        border-radius: 22px;
        padding: 22px;
        margin-bottom: 18px;
        box-shadow: 0 15px 45px rgba(0,0,0,.20);
    }

    .badge {
        display: inline-block;
        padding: 7px 12px;
        border-radius: 999px;
        background: rgba(142, 92, 255, .16);
        color: #cbb7ff;
        font-size: 13px;
        font-weight: 700;
        margin-bottom: 8px;
    }

    .small {
        color: #9fa3b5;
        font-size: 13px;
    }

    div.stButton > button {
        width: 100%;
        border-radius: 14px;
        min-height: 50px;
        font-weight: 800;
    }

    .success-box {
        border: 1px solid rgba(52, 211, 153, .35);
        background: rgba(16, 185, 129, .08);
        padding: 14px 16px;
        border-radius: 14px;
        margin: 10px 0;
    }

    .warning-box {
        border: 1px solid rgba(251, 191, 36, .35);
        background: rgba(245, 158, 11, .08);
        padding: 14px 16px;
        border-radius: 14px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Helpers
# -----------------------------
def get_credentials():
    """Support the common secret names so the app works with the keys already added."""
    candidates = [
        ("HF_API_KEY_ID", "HF_API_KEY_SECRET"),
        ("HF_API_KEY", "HF_API_SECRET"),
    ]

    for key_name, secret_name in candidates:
        try:
            key_id = st.secrets.get(key_name)
            key_secret = st.secrets.get(secret_name)
        except Exception:
            key_id = None
            key_secret = None

        if key_id and key_secret:
            return str(key_id).strip(), str(key_secret).strip()

    # Also support a single HF_KEY / HF_CREDENTIALS value:
    for single_name in ("HF_KEY", "HF_CREDENTIALS"):
        try:
            value = st.secrets.get(single_name)
        except Exception:
            value = None

        if value and ":" in str(value):
            a, b = str(value).split(":", 1)
            if a.strip() and b.strip():
                return a.strip(), b.strip()

    return None, None


def upload_bytes(data, content_type):
    """Upload user media through the official Higgsfield SDK and return a public URL."""
    return higgsfield_client.upload(data, content_type)


def result_image_url(result):
    if isinstance(result, dict):
        images = result.get("images")
        if isinstance(images, list) and images:
            first = images[0]
            if isinstance(first, dict):
                return first.get("url") or first.get("image_url")
            if isinstance(first, str):
                return first

        for key in ("image", "image_url", "url"):
            if isinstance(result.get(key), str):
                return result[key]

    return None


def result_video_url(result):
    if isinstance(result, dict):
        video = result.get("video")

        if isinstance(video, dict):
            return video.get("url") or video.get("video_url")

        if isinstance(video, str):
            return video

        for key in ("video_url", "output_url", "url"):
            if isinstance(result.get(key), str):
                return result[key]

    return None


def make_prompt(style):
    return f"""
Create a photorealistic fashion virtual try-on image.

IMPORTANT:
- The FIRST reference image is the person/model.
- The SECOND reference image is the clothing/outfit/product that the person should wear.
- Put the exact clothing from the second image onto the person from the first image.
- Preserve the person's face, identity, body proportions, pose, skin tone and natural appearance.
- Preserve the garment's design, color, pattern, material, logos and important details.
- Make the clothing fit naturally with realistic folds, shadows and lighting.
- Do not change the person's face or hairstyle.
- Do not add extra people.
- Full-body fashion photography when possible.
- Style: {style}.
- Clean realistic background and professional fashion photography.
""".strip()


# -----------------------------
# Header
# -----------------------------
st.markdown("""
<div class="hero">
    <div class="badge">✨ REAL AI FASHION TRY-ON</div>
    <h1>YOSEF AI — TRY-ON STUDIO</h1>
    <p>ارفع صورة الشخص + صورة اللبس، وخلي Higgsfield ينفذ التجربة بالـAI.</p>
</div>
""", unsafe_allow_html=True)

# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    st.markdown("## ⚙️ إعدادات التجربة")

    mode = st.radio(
        "نوع التجربة",
        ["📸 صورة", "🎬 فيديو"],
        index=0,
    )

    style = st.selectbox(
        "ستايل النتيجة",
        [
            "Natural / Realistic",
            "Studio Fashion",
            "Streetwear",
            "Luxury Fashion",
            "E-commerce",
        ],
    )

    ratio = st.selectbox(
        "نسبة العرض",
        [
            "9:16 — Reels",
            "1:1 — Square",
            "4:5 — Instagram",
            "16:9 — Landscape",
        ],
    )

    st.markdown("---")
    st.markdown("### 🔐 AI")
    key_id, key_secret = get_credentials()

    if key_id and key_secret:
        st.success("Higgsfield API متصل")
    else:
        st.warning("أضف HF_API_KEY_ID و HF_API_KEY_SECRET في Streamlit Secrets.")

    st.markdown(
        '<div class="small">المفتاح لا يتم وضعه داخل app.py ولا يظهر للمستخدم.</div>',
        unsafe_allow_html=True,
    )

# -----------------------------
# Inputs
# -----------------------------
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown("### 👤 1 — صورة الشخص")
person_file = st.file_uploader(
    "ارفع صورة واضحة للشخص",
    type=["jpg", "jpeg", "png", "webp"],
    key="person",
)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown("### 👕 2 — صورة اللبس")
outfit_file = st.file_uploader(
    "ارفع صورة واضحة للملابس / اللوك",
    type=["jpg", "jpeg", "png", "webp"],
    key="outfit",
)
st.markdown("</div>", unsafe_allow_html=True)

motion_file = None
if mode == "🎬 فيديو":
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 🎥 3 — فيديو الحركة")
    motion_file = st.file_uploader(
        "ارفع فيديو قصير للحركة (يفضل 3–10 ثوانٍ)",
        type=["mp4", "mov", "webm"],
        key="motion",
    )
    st.markdown("</div>", unsafe_allow_html=True)

# Preview
if person_file or outfit_file:
    cols = st.columns(2)

    if person_file:
        with cols[0]:
            st.markdown("**👤 الشخص**")
            st.image(person_file, use_container_width=True)

    if outfit_file:
        with cols[1]:
            st.markdown("**👕 اللبس**")
            st.image(outfit_file, use_container_width=True)

if motion_file:
    st.video(motion_file)

# -----------------------------
# Generate
# -----------------------------
st.markdown('<div class="card">', unsafe_allow_html=True)

if mode == "📸 صورة":
    button_text = "✨ جرّب اللبس بالـAI"
else:
    button_text = "🎬 اصنع فيديو الـTry-On"

if st.button(button_text, type="primary", use_container_width=True):
    if not key_id or not key_secret:
        st.error(
            "مفتاح Higgsfield غير موجود. افتح Streamlit → Manage app → Settings → Secrets."
        )
        st.stop()

    if not person_file:
        st.error("ارفع صورة الشخص أولًا.")
        st.stop()

    if not outfit_file:
        st.error("ارفع صورة اللبس أولًا.")
        st.stop()

    if mode == "🎬 فيديو" and not motion_file:
        st.error("ارفع فيديو الحركة أولًا.")
        st.stop()

    try:
        # Set credentials for the official SDK.
        # This stays server-side on Streamlit.
        import os
        os.environ["HF_API_KEY"] = key_id
        os.environ["HF_API_SECRET"] = key_secret
        os.environ["HF_KEY"] = f"{key_id}:{key_secret}"

        progress = st.progress(0)
        status = st.empty()

        status.info("📤 جاري رفع الملفات إلى Higgsfield...")
        progress.progress(15)

        person_url = upload_bytes(
            person_file.getvalue(),
            person_file.type or "image/jpeg",
        )

        outfit_url = upload_bytes(
            outfit_file.getvalue(),
            outfit_file.type or "image/jpeg",
        )

        progress.progress(35)

        # Aspect ratio mapping
        ratio_map = {
            "9:16 — Reels": "9:16",
            "1:1 — Square": "1:1",
            "4:5 — Instagram": "4:5",
            "16:9 — Landscape": "16:9",
        }
        aspect = ratio_map.get(ratio, "9:16")

        if mode == "📸 صورة":
            status.info("🧠 Higgsfield بيعمل الـAI Try-On...")
            progress.progress(50)

            result = higgsfield_client.subscribe(
                "marketing-studio/image",
                arguments={
                    "prompt": make_prompt(style),
                    "image_urls": [person_url, outfit_url],
                    "resolution": "2k",
                    "aspect_ratio": aspect,
                    "enhance_prompt": False,
                },
            )

            progress.progress(90)
            image_url = result_image_url(result)

            if not image_url:
                st.error("تم إرسال الطلب لكن لم يتم العثور على رابط الصورة في النتيجة.")
                st.code(str(result))
                st.stop()

            progress.progress(100)
            status.success("✅ النتيجة جاهزة!")

            st.markdown("## ✨ النتيجة")
            st.image(image_url, use_container_width=True)

            st.markdown(
                f'<div class="success-box">تم تنفيذ الطلب عبر Higgsfield AI — جرّب صورًا أوضح للشخص واللبس للحصول على نتيجة أفضل.</div>',
                unsafe_allow_html=True,
            )

        else:
            status.info("🎬 جاري رفع فيديو الحركة...")
            progress.progress(45)

            motion_url = upload_bytes(
                motion_file.getvalue(),
                motion_file.type or "video/mp4",
            )

            status.info("🧠 جاري تنفيذ Motion Transfer...")
            progress.progress(55)

            result = higgsfield_client.subscribe(
                "higgsfiled/genjutsu/motion-transfer/v1.0",
                arguments={
                    "prompt": (
                        "Photorealistic fashion try-on. "
                        "Use the person and clothing references faithfully. "
                        "Keep the person's face and identity consistent. "
                        "Transfer the motion from the reference video naturally. "
                        f"Style: {style}."
                    ),
                    "video_url": motion_url,
                    "image_urls": [person_url, outfit_url],
                    "resolution": "720p",
                },
            )

            progress.progress(90)
            video_url = result_video_url(result)

            if not video_url:
                st.error("تم إرسال الطلب لكن لم يتم العثور على رابط الفيديو في النتيجة.")
                st.code(str(result))
                st.stop()

            progress.progress(100)
            status.success("✅ الفيديو جاهز!")

            st.markdown("## 🎬 النتيجة")
            st.video(video_url)

            st.markdown(
                '<div class="success-box">تم تنفيذ الفيديو باستخدام Genjutsu Motion Transfer.</div>',
                unsafe_allow_html=True,
            )

    except Exception as e:
        st.error("حصل خطأ أثناء تنفيذ الـAI.")
        st.code(str(e))
        st.info(
            "لو الخطأ متعلق بالرصيد، لازم يكون في رصيد API في Higgsfield. "
            "ولو الخطأ متعلق بالموديل، ابعتلي نص الخطأ كما هو."
        )

st.markdown("</div>", unsafe_allow_html=True)

st.caption(
    "Powered by Higgsfield API • لا تضع مفاتيح API داخل GitHub أو داخل الكود."
)
