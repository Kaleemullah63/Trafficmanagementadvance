import streamlit as st
import requests
import time
from groq import Groq

# ===============================
# CONFIG
# ===============================
st.set_page_config(page_title="AI Traffic System (OpenStreetMap)", layout="wide")

GROQ_API_KEY = "API_KEY"

# ===============================
# STYLE (Gen-Z UI)
# ===============================
st.markdown("""
<style>
body { background: linear-gradient(135deg,#e8f0ff,#f4ecff); }
.card {
    background:white;
    padding:20px;
    border-radius:18px;
    box-shadow:0 8px 18px rgba(0,0,0,0.08);
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
    params = {"overview":"false", "alternatives":"true", "steps":"true"}
    r = requests.get(url, params=params).json()
    return r.get("routes", [])

# ===============================
# AI SUGGESTIONS
# ===============================
def ai_summary(text):
    try:
        client = Groq(api_key=GROQ_API_KEY)
        r = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role":"user","content":text}]
        )
        return r.choices[0].message.content
    except:
        return "AI service temporarily unavailable."

# ===============================
# UI
# ===============================
st.title("🌍 AI Traffic & Route Prediction (OpenStreetMap Powered)")

st.markdown('<div class="card">', unsafe_allow_html=True)
source = st.text_input("🚩 Source (any city/place/address worldwide)")
destination = st.text_input("🏁 Destination (any city/place/address worldwide)")
weather = st.selectbox("🌦 Weather", ["Clear","Rainy","Foggy"])
st.markdown('</div>', unsafe_allow_html=True)

# ===============================
# PROCESS
# ===============================
if st.button("🔍 Find Real Routes"):
    with st.spinner("Finding real roads using OpenStreetMap..."):
        src = geocode(source)
        dst = geocode(destination)

        if not src or not dst:
            st.error("Location not found. Try a clearer name.")
        else:
            routes = get_routes(src, dst)

            st.subheader("🛣 Alternative Real Routes")

            for i, r in enumerate(routes, 1):
                dist_km = r["distance"] / 1000
                time_min = r["duration"] / 60
                congestion = min(int(time_min / dist_km * 10), 100)

                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.write(f"### Route {i}")
                st.write(f"📏 Distance: **{dist_km:.2f} km**")
                st.write(f"⏱ Estimated Time: **{time_min:.1f} min**")
                st.write(f"🚦 Congestion: **{congestion}%**")

                st.write("**Road-by-road path:**")
                for leg in r["legs"]:
                    for step in leg["steps"]:
                        road = step["name"] or "Unnamed Road"
                        step_km = step["distance"] / 1000
                        step_min = step["duration"] / 60
                        step_cong = min(int(step_min / max(step_km,0.1)*10),100)
                        st.write(f"• {road} → {step_km:.2f} km | {step_min:.1f} min | {step_cong}%")

                st.markdown('</div>', unsafe_allow_html=True)

            prompt = f"""
            Source: {source}
            Destination: {destination}
            Weather: {weather}
            Provide traffic optimization and alternative route suggestions.
            """

            st.subheader("🤖 AI Traffic Intelligence")
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.write(ai_summary(prompt))
            st.markdown('</div>', unsafe_allow_html=True)
