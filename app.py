import streamlit as st
import requests
from groq import Groq

# ===============================
# CONFIG
# ===============================
st.set_page_config("AI Traffic System (OSM)", layout="wide")
GROQ_API_KEY = "API_KEY"

# ===============================
# UI STYLE
# ===============================
st.markdown("""
<style>
body { background: linear-gradient(135deg,#eef2ff,#f8f6ff); }
.card {
    background:white;
    padding:20px;
    border-radius:18px;
    box-shadow:0 8px 20px rgba(0,0,0,0.08);
    margin-bottom:20px;
}
</style>
""", unsafe_allow_html=True)

# ===============================
# GEOCODING (OSM)
# ===============================
def geocode(place):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": place, "format": "json", "limit": 1}
    r = requests.get(url, params=params, headers={"User-Agent":"traffic-app"})
    data = r.json()
    if not data:
        return None
    return float(data[0]["lat"]), float(data[0]["lon"])

# ===============================
# ROUTES (OSRM)
# ===============================
def get_routes(src, dst):
    url = f"http://router.project-osrm.org/route/v1/driving/{src[1]},{src[0]};{dst[1]},{dst[0]}"
    params = {
        "alternatives": "true",
        "steps": "true",
        "overview": "false"
    }
    r = requests.get(url, params=params).json()
    return r.get("routes", [])[:3]  # Only 2–3 routes

# ===============================
# CONGESTION ESTIMATION
# ===============================
def congestion_level(distance_km, time_min):
    score = (time_min / max(distance_km, 0.1)) * 10
    if score < 30:
        return "Low 🟢", score
    elif score < 60:
        return "Medium 🟡", score
    else:
        return "High 🔴", score

# ===============================
# AI SUGGESTION
# ===============================
def ai_advice(text):
    try:
        client = Groq(api_key=GROQ_API_KEY)
        r = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role":"user","content":text}]
        )
        return r.choices[0].message.content
    except:
        return "AI service unavailable."

# ===============================
# UI
# ===============================
st.title("🌍 AI Traffic & Alternative Route Finder")

st.markdown('<div class="card">', unsafe_allow_html=True)
source = st.text_input("🚩 Source (any city/place)")
destination = st.text_input("🏁 Destination (any city/place)")
weather = st.selectbox("🌦 Weather", ["Clear", "Rainy", "Foggy"])
st.markdown('</div>', unsafe_allow_html=True)

# ===============================
# PROCESS
# ===============================
if st.button("🔍 Find Alternative Roads"):
    with st.spinner("Analyzing roads and congestion..."):
        src = geocode(source)
        dst = geocode(destination)

        if not src or not dst:
            st.error("Location not found.")
        else:
            routes = get_routes(src, dst)
            st.subheader("🛣 Best Alternative Roads (2–3)")

            for i, r in enumerate(routes, 1):
                dist_km = r["distance"] / 1000
                time_min = r["duration"] / 60
                level, score = congestion_level(dist_km, time_min)

                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.write(f"### Route {i}")
                st.write(f"📏 Distance: **{dist_km:.2f} km**")
                st.write(f"⏱ Time: **{time_min:.1f} min**")
                st.write(f"🚦 Congestion: **{level} ({score:.1f}%)**")

                st.write("**Road sequence:**")
                for leg in r["legs"]:
                    for step in leg["steps"]:
                        road = step["name"] or "Local Road"
                        st.write(f"• {road}")

                st.markdown('</div>', unsafe_allow_html=True)

            st.subheader("🤖 AI Traffic Suggestions")
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.write(ai_advice(
                f"Source: {source}, Destination: {destination}, Weather: {weather}. "
                "Suggest best route and traffic management advice."
            ))
            st.markdown('</div>', unsafe_allow_html=True)
