import streamlit as st
import pandas as pd
import time
from groq import Groq

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(
    page_title="AI Traffic & Route Prediction System",
    layout="wide"
)

# ==================================================
# API KEY (PASTE YOUR KEY)
# ==================================================
GROQ_API_KEY = "API_KEY"

# ==================================================
# MODERN UI CSS
# ==================================================
st.markdown("""
<style>
body {
    background: linear-gradient(135deg, #e0f2ff, #ede7ff);
}
.card {
    background: white;
    padding: 20px;
    border-radius: 18px;
    box-shadow: 0px 8px 20px rgba(0,0,0,0.08);
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

# ==================================================
# WORLD DATA (GENERIC & SCALABLE)
# ==================================================
WORLD_DATA = {
    "Asia": {
        "Cities": {
            "Multan": ["Gulgasht Colony", "Cantt", "Bosan Road", "Vehari Road"],
            "Tokyo": ["Shinjuku", "Shibuya", "Akihabara"],
            "Mumbai": ["Andheri", "Bandra", "Dadar"]
        }
    },
    "Europe": {
        "Cities": {
            "London": ["Camden", "Westminster", "Greenwich"],
            "Paris": ["Montmartre", "Latin Quarter"],
            "Berlin": ["Mitte", "Kreuzberg"]
        }
    },
    "North America": {
        "Cities": {
            "New York": ["Manhattan", "Brooklyn", "Queens"],
            "Toronto": ["Downtown", "Scarborough"],
            "San Francisco": ["Market Street", "Silicon Valley"]
        }
    }
}

LOCATION_TYPES = ["Downtown", "Highway", "Residential", "School Zone", "IT Park"]

# ==================================================
# TRAFFIC ESTIMATION (SYSTEM-PREDICTED)
# ==================================================
def estimate_traffic(location_type, time_type, weather, region):
    base = {
        "Downtown": (120, 60, 25),
        "Highway": (180, 40, 35),
        "Residential": (70, 50, 10),
        "School Zone": (60, 30, 15),
        "IT Park": (100, 50, 20)
    }

    time_mul = 1.5 if time_type == "Peak" else 1.0
    weather_mul = {"Clear":1.0, "Rainy":1.2, "Foggy":1.3}[weather]
    region_mul = {
        "Asia":1.3,
        "Europe":1.1,
        "North America":1.2
    }[region]

    cars, bikes, buses = base[location_type]

    return (
        int(cars*time_mul*weather_mul*region_mul),
        int(bikes*time_mul*weather_mul*region_mul),
        int(buses*time_mul*weather_mul*region_mul)
    )

# ==================================================
# CONGESTION CALCULATION
# ==================================================
def calculate_congestion(cars, bikes, buses, location_type):
    weight = {
        "Downtown":1.4,
        "Highway":1.2,
        "Residential":1.0,
        "School Zone":1.3,
        "IT Park":1.2
    }
    score = (cars*1.0 + bikes*0.5 + buses*2.5) * weight[location_type]
    return score

def classify(score):
    if score < 120:
        return "Low", "🟢", 5
    elif score < 220:
        return "Medium", "🟠", 15
    else:
        return "High", "🔴", 30

# ==================================================
# ROUTE GENERATION (GENERIC)
# ==================================================
def generate_routes(source, destination):
    return [
        {"name": f"{source} → Main Road → {destination}", "type":"Downtown"},
        {"name": f"{source} → Bypass → {destination}", "type":"Highway"},
        {"name": f"{source} → Local Streets → {destination}", "type":"Residential"}
    ]

# ==================================================
# AI SUGGESTIONS
# ==================================================
def ai_advice(text):
    try:
        client = Groq(api_key=GROQ_API_KEY)
        res = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role":"user","content":text}]
        )
        return res.choices[0].message.content
    except:
        return "AI service unavailable."

# ==================================================
# UI
# ==================================================
st.title("🚦 AI Traffic Congestion & Route Recommendation System")

st.markdown('<div class="card">', unsafe_allow_html=True)

region = st.selectbox("🌍 Region", list(WORLD_DATA.keys()))
city = st.selectbox("🏙 City", list(WORLD_DATA[region]["Cities"].keys()))
areas = WORLD_DATA[region]["Cities"][city]

source = st.selectbox("🚩 Source", areas)
destination = st.selectbox("🏁 Destination", [a for a in areas if a != source])

location_type = st.selectbox("📍 Area Type", LOCATION_TYPES)
time_type = st.radio("⏰ Time", ["Peak", "Non-Peak"])
weather = st.selectbox("🌦 Weather", ["Clear", "Rainy", "Foggy"])

st.markdown('</div>', unsafe_allow_html=True)

# ==================================================
# PREDICTION
# ==================================================
if st.button("🔍 Find Best Route"):
    with st.spinner("Analyzing routes..."):
        time.sleep(1)

        routes = generate_routes(source, destination)
        best_route = None
        best_score = float("inf")

        st.subheader("🛣 Alternative Routes")

        for r in routes:
            cars, bikes, buses = estimate_traffic(
                r["type"], time_type, weather, region
            )

            score = calculate_congestion(cars, bikes, buses, r["type"])
            level, icon, delay = classify(score)

            if score < best_score:
                best_score = score
                best_route = r["name"]

            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.write(f"**Route:** {r['name']}")
            st.write(f"Type: {r['type']}")
            st.write(f"Traffic: {icon} {level}")
            st.write(f"Estimated Delay: {delay} minutes")
            st.markdown('</div>', unsafe_allow_html=True)

        st.success(f"✅ Recommended Route (Lowest Congestion): **{best_route}**")

        prompt = f"""
        City: {city}
        Time: {time_type}
        Weather: {weather}

        Best Route: {best_route}

        Suggest:
        1. Traffic management tips
        2. Alternative travel advice
        3. Urban planning improvements
        """

        st.subheader("🤖 AI Suggestions")
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.write(ai_advice(prompt))
        st.markdown('</div>', unsafe_allow_html=True)
