import streamlit as st
import requests
from groq import Groq

# ==================================================
# CONFIG
# ==================================================
st.set_page_config(
    page_title="AI Traffic & Route Finder",
    layout="wide"
)

GROQ_API_KEY = "API_KEY"

# ==================================================
# MODERN UI STYLE
# ==================================================
st.markdown("""
<style>
body {
    background: linear-gradient(135deg, #eef2ff, #f8f6ff);
}
.card {
    background: white;
    padding: 22px;
    border-radius: 18px;
    box-shadow: 0 10px 24px rgba(0,0,0,0.08);
    margin-bottom: 20px;
}
.route-title {
    font-size: 22px;
    font-weight: 700;
}
.path {
    font-size: 16px;
    color: #333;
}
.badge {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 10px;
    background: #e0e7ff;
    font-size: 13px;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

# ==================================================
# GEOCODING (OpenStreetMap - Nominatim)
# ==================================================
def geocode(place):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": place, "format": "json", "limit": 1}
    r = requests.get(url, params=params, headers={"User-Agent": "traffic-app"})
    data = r.json()
    if not data:
        return None
    return float(data[0]["lat"]), float(data[0]["lon"])

# ==================================================
# ROUTING (OSRM)
# ==================================================
def get_routes(src, dst):
    url = f"http://router.project-osrm.org/route/v1/driving/{src[1]},{src[0]};{dst[1]},{dst[0]}"
    params = {
        "alternatives": "true",
        "steps": "true",
        "overview": "false"
    }
    r = requests.get(url, params=params).json()
    return r.get("routes", [])[:3]  # Only 2–3 routes

# ==================================================
# CLEAN ROAD SUMMARY (HCI FIX)
# ==================================================
def summarize_route(legs):
    roads = []
    for leg in legs:
        for step in leg["steps"]:
            name = step["name"]
            if (
                name
                and name != "Local Road"
                and name not in roads
            ):
                roads.append(name)
    return roads[:5]  # Only key roads

# ==================================================
# CONGESTION ESTIMATION
# ==================================================
def congestion_level(distance_km, time_min):
    score = (time_min / max(distance_km, 0.1)) * 10
    if score < 30:
        return "Low 🟢", score
    elif score < 60:
        return "Medium 🟡", score
    else:
        return "High 🔴", score

# ==================================================
# AI TRAFFIC ADVICE (OPTIONAL)
# ==================================================
def ai_advice(text):
    try:
        client = Groq(api_key=GROQ_API_KEY)
        r = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": text}]
        )
        return r.choices[0].message.content
    except:
        return "AI suggestions are temporarily unavailable."

# ==================================================
# UI
# ==================================================
st.title("🌍 AI Traffic & Alternative Route Finder")

st.markdown('<div class="card">', unsafe_allow_html=True)
source = st.text_input("🚩 Source (any city / area / landmark)")
destination = st.text_input("🏁 Destination (any city / area / landmark)")
weather = st.selectbox("🌦 Weather", ["Clear", "Rainy", "Foggy"])
st.markdown('</div>', unsafe_allow_html=True)

# ==================================================
# PROCESS
# ==================================================
if st.button("🔍 Find Best Routes"):
    with st.spinner("Analyzing real roads and traffic conditions..."):
        src = geocode(source)
        dst = geocode(destination)

        if not src or not dst:
            st.error("❌ Location not found. Please enter a clearer place name.")
        else:
            routes = get_routes(src, dst)

            st.subheader("🛣 Recommended Alternative Routes")

            for i, r in enumerate(routes, 1):
                dist_km = r["distance"] / 1000
                time_min = r["duration"] / 60
                level, score = congestion_level(dist_km, time_min)

                roads = summarize_route(r["legs"])
                path = " → ".join(roads)

                badge = "⭐ Recommended" if i == 1 else "🔁 Alternative"

                st.markdown(f"""
                <div class="card">
                    <div class="route-title">Route {i} <span class="badge">{badge}</span></div>
                    <p class="path"><b>Path:</b> {path}</p>
                    <p>📏 <b>{dist_km:.2f} km</b> &nbsp; ⏱ <b>{time_min:.1f} min</b></p>
                    <p>🚦 <b>{level}</b> ({score:.1f}%)</p>
                </div>
                """, unsafe_allow_html=True)

            st.subheader("🤖 AI Traffic Intelligence")
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.write(ai_advice(
                f"Source: {source}, Destination: {destination}, Weather: {weather}. "
                "Suggest the best route and traffic optimization advice."
            ))
            st.markdown('</div>', unsafe_allow_html=True)
