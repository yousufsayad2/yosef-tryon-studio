import streamlit as st
import time
import base64

# ============================================================
# YOSEF TRY-ON STUDIO
# Single-file Streamlit app
# ============================================================

st.set_page_config(
    page_title="Yosef Try-On Studio",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------- DESIGN --------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: Cairo, sans-serif;
}
.stApp {
    background:
      radial-gradient(circle at 12% 0%, rgba(124,58,237,.20), transparent 30%),
      radial-gradient(circle at 92% 22%, rgba(236,72,153,.13), transparent 28%),
      #07080d;
    color:#f7f7fb;
}
.block-container {
    max-width:1250px;
    padding-top:1.4rem;
}
.top {
    border:1px solid #292d3c;
    border-radius:22px;
    padding:18px 22px;
    background:linear-gradient(135deg,#11131d,#0b0d13);
    box-shadow:0 20px 60px rgba(0,0,0,.25);
}
.logo {
    width:42px;height:42px;border-radius:13px;
    display:inline-grid;place-items:center;
    background:linear-gradient(135deg,#7c3aed,#ec4899);
    font-weight:800;font-size:22px;
    vertical-align:middle;margin-left:10px;
}
.brand {font-size:28px;font-weight:800;vertical-align:middle}
.brand span {color:#a78bfa}
.sub {color:#858a9d;font-size:11px;margin-right:56px;margin-top:-4px}
.eyebrow {color:#bca7ff;font-size:12px;font-weight:800;letter-spacing:1.4px}
.hero {padding:34px 4px 12px}
.hero h1 {font-size:clamp(36px,5vw,62px);line-height:1.16;margin:9px 0}
.hero h1 span {
    background:linear-gradient(90deg,#fff,#b9a0ff,#f28cc5);
    -webkit-background-clip:text;color:transparent
}
.hero p {color:#999fb1;line-height:1.9;max-width:760px}
.card {
    background:rgba(15,17,25,.86);
    border:1px solid #292d3d;
    border-radius:22px;
    padding:21px;
    margin-top:15px;
}
.step {
    font-weight:800;font-size:15px;margin:8px 0 4px
}
.help {color:#777d90;font-size:11px;margin-bottom:10px}
div[data-testid="stFileUploader"] {
    border:1px dashed #3a3f53;
    border-radius:15px;
    padding:4px;
    background:#10131b;
}
div[data-testid="stFileUploader"]:hover {border-color:#8b5cf6}
div.stButton > button {
    border-radius:12px;
    border:1px solid #34394c;
    background:#171a24;
    color:white;
    font-family:Cairo,sans-serif;
    font-weight:700;
}
div.stButton > button[kind="primary"] {
    background:linear-gradient(90deg,#7c3aed,#ec4899);
    border:0;
}
.result {
    min-height:540px;
    border:1px solid #292d3d;
    border-radius:20px;
    background:radial-gradient(circle at 50% 20%,#25283a,#0c0e14 65%);
    padding:18px;
}
.badge {
    display:inline-block;padding:5px 10px;border-radius:999px;
    background:#1d2030;border:1px solid #3a3e52;
    color:#c8b8ff;font-size:10px;letter-spacing:1px
}
.center {text-align:center;padding:100px 20px;color:#777d90}
.center h3 {color:#e9eaf0}
.note {color:#777d90;font-size:11px;text-align:center;margin-top:10px}
.status {
    border:1px solid #292d3d;border-radius:12px;
    background:#10131b;padding:11px;margin-top:12px;
    color:#aeb3c3;font-size:11px
}
</style>
""", unsafe_allow_html=True)

# -------------------- HEADER --------------------
st.markdown("""
<div class="top">
  <span class="logo">Y</span>
  <span class="brand">Yosef <span>Try-On Studio</span></span>
  <div class="sub">AI VIRTUAL FASHION STUDIO</div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <div class="eyebrow">✦ AI VIRTUAL TRY-ON</div>
  <h1>جرّب اللبس على <span>صورتك</span><br>وشوف النتيجة بصورة أو فيديو.</h1>
  <p>
    ارفع صورتك وصورة اللبس، اختار صورة أو فيديو، وبعدها ابدأ تجربة الـAI.
    الملف ده يحتوي على الواجهة والمنطق كله في ملف Python واحد.
  </p>
</div>
""", unsafe_allow_html=True)

# -------------------- SIDEBAR --------------------
with st.sidebar:
    st.markdown("## ⚙️ إعدادات")
    mode = st.radio("نوع التجربة", ["📸 صورة", "🎬 فيديو"])
    style = st.selectbox(
        "ستايل النتيجة",
        ["Natural / Realistic", "Studio Fashion", "Streetwear", "Luxury Editorial"]
    )
    ratio = st.selectbox(
        "نسبة العرض",
        ["9:16 — Reels", "1:1 — Square", "4:5 — Feed"]
    )
    st.divider()
    st.markdown("### 🔐 AI")
    st.caption(
        "مفتاح الـAPI لا يوضع داخل الكود. عند الربط الحقيقي استخدم "
        "Streamlit Secrets."
    )

# -------------------- INPUTS --------------------
left, right = st.columns([0.88, 1.12], gap="large")

with left:
    st.markdown('<div class="card">', unsafe_allow_html=True)

    st.markdown('<div class="step">① صورتك</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="help">يفضل صورة واضحة يظهر فيها الجسم بشكل جيد.</div>',
        unsafe_allow_html=True
    )
    person = st.file_uploader(
        "ارفع صورة الشخص",
        type=["jpg", "jpeg", "png", "webp"],
        key="person_upload"
    )

    if person:
        st.image(person, caption="صورتك", use_container_width=True)

    st.markdown('<div class="step">② صورة اللبس</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="help">صورة واضحة للقطعة التي تريد تجربتها.</div>',
        unsafe_allow_html=True
    )
    outfit = st.file_uploader(
        "ارفع صورة اللبس",
        type=["jpg", "jpeg", "png", "webp"],
        key="outfit_upload"
    )

    if outfit:
        st.image(outfit, caption="اللبس", use_container_width=True)

    motion = None
    if mode.startswith("🎬"):
        st.markdown('<div class="step">③ فيديو الحركة</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="help">اختياري — يفضل فيديو قصير 5 إلى 10 ثواني.</div>',
            unsafe_allow_html=True
        )
        motion = st.file_uploader(
            "ارفع فيديو الحركة",
            type=["mp4", "mov", "webm"],
            key="motion_upload"
        )
        if motion:
            st.video(motion)

    st.markdown('</div>', unsafe_allow_html=True)

# -------------------- RESULT --------------------
with right:
    st.markdown('<div class="result">', unsafe_allow_html=True)
    st.markdown('<span class="badge">AI PREVIEW STUDIO</span>', unsafe_allow_html=True)

    if not person or not outfit:
        st.markdown("""
        <div class="center">
          <div style="font-size:48px">✦</div>
          <h3>النتيجة هتظهر هنا</h3>
          <p>ارفع صورتك وصورة اللبس ثم اضغط «جرّب اللبس بالـ AI».</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("### معاينة")
        st.image(person, caption="صورة الشخص", use_container_width=True)
        st.markdown(
            '<div class="note">الصورة الظاهرة الآن هي معاينة للواجهة. '
            'الـTry-On الحقيقي يتم بعد ربط موديل AI.</div>',
            unsafe_allow_html=True
        )

    run = st.button(
        "✨ جرّب اللبس بالـ AI",
        type="primary",
        use_container_width=True
    )

    if run:
        if not person or not outfit:
            st.warning("ارفع صورتك وصورة اللبس الأول.")
        elif mode.startswith("🎬") and not motion:
            st.info("يمكنك رفع فيديو حركة، أو تكمل بدون فيديو لو حابب.")
        else:
            bar = st.progress(0)
            steps = [
                "تحليل صورة الشخص...",
                "تحليل قطعة اللبس...",
                "تجهيز المشهد...",
                "إرسال المهمة إلى مزود الـAI...",
                "استقبال النتيجة..."
            ]
            for i, msg in enumerate(steps, 1):
                time.sleep(.35)
                bar.progress(i / len(steps), text=msg)

            st.success(
                "تم تجهيز التجربة التجريبية. الخطوة التالية هي توصيل "
                "موديل Try-On الحقيقي بنفس الزر."
            )
            st.markdown(
                f'<div class="status">Style: {style} &nbsp; • &nbsp; '
                f'Ratio: {ratio} &nbsp; • &nbsp; Mode: {mode}</div>',
                unsafe_allow_html=True
            )

    st.markdown('</div>', unsafe_allow_html=True)

# -------------------- ROADMAP --------------------
st.markdown("## 🚀 المشروع جاهز للتطوير")
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("### 01 · Upload")
    st.caption("صورة الشخص + صورة اللبس + فيديو اختياري.")
with c2:
    st.markdown("### 02 · AI")
    st.caption("نربط مزود Try-On من السيرفر باستخدام Secrets.")
with c3:
    st.markdown("### 03 · Result")
    st.caption("صورة أو فيديو قابل للعرض والحفظ والمشاركة.")

st.caption("Yosef Try-On Studio • Single-file Streamlit edition")
