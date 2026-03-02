import streamlit as st
import time
from groq import Groq

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(
    page_title="AI Traffic Route Prediction",
    layout="wide"
)

GROQ_API_KEY = "API_KEY"

# ==================================================
# UI STYLE
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
# COUNTRY → CITY LIST (EXTENSIBLE)
# ==================================================
COUNTRY_CITY_MAP = {
    "Pakistan": [
        "Multan","Lahore","Karachi","Islamabad","Faisalabad",
        "Rawalpindi","Gujranwala","Sialkot","Bahawalpur","Rahim Yar Khan"
    ],
    "India": [
        "Delhi","Mumbai","Bangalore","Chennai","Hyderabad",
        "Pune","Ahmedabad","Jaipur","Indore","Bhopal"
    ],
    "United States": [
        "New York","Los Angeles","Chicago","Houston","Phoenix",
        "Dallas","Austin","San Jose","San Francisco","Seattle"
    ],
    "United Kingdom": [
        "London","Manchester","Birmingham","Leeds","Liverpool",
        "Sheffield","Nottingham","Derby","Leicester","Coventry"
    ]
}

# ==================================================
# TRAFFIC ESTIMATION (SYSTEM)
# ==================================================
def estimate_traffic(time_type, weather):
    base_cars = 120
    time_mul = 1.5 if time_type == "Peak" else 1.0
    weather_mul = {"Clear":1.0, "Rainy":1.2, "Foggy":1.3}[weather]
    cars = int(base_cars * time_mul * weather_mul)
    return cars

# ==================================================
# CONGESTION CALCULATION
# ==================================================
def congestion_percentage(cars):
    percent = min(100, int((cars / 250) * 100))
    if percent < 40:
        return percent, "Low", "🟢"
    elif percent < 70:
        return percent, "Medium", "🟠"
    else:
        return percent, "High", "🔴"

# ==================================================
# REALISTIC ROUTE GENERATION
# ==================================================
def generate_named_routes(source, destination):
    return [
        {
            "path": f"{source} → 9 Number Chowk → Kumharawala Chowk → {destination}",
            "distance": 6.8
        },
        {
            "path": f"{source} → Dault Gate → BCG Chowk → {destination}",
            "distance": 7.5
        },
        {
            "path": f"{source} → Internal Streets → Market Road → {destination}",
            "distance": 5.9
        }
    ]

# ==================================================
# AI SUGGESTIONS
# ==================================================
def ai_suggestions(text):
    try:
        client = Groq(api_key=GROQ_API_KEY)
        res = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role":"user","content":text}]
        )
        return res.choices[0].message.content
    except:
        return "AI suggestions currently unavailable."

# ==================================================
# UI
# ==================================================
st.title("🚦 AI Traffic Route & Congestion Prediction")

st.markdown('<div class="card">', unsafe_allow_html=True)

country = st.selectbox("🌍 Country", list(COUNTRY_CITY_MAP.keys()))
city = st.selectbox("🏙 City", COUNTRY_CITY_MAP[country])

source = st.text_input("🚩 Source Area (e.g. Gulgasht Colony)")
destination = st.text_input("🏁 Destination Area (e.g. Vehari Chowk)")

time_type = st.radio("⏰ Time", ["Peak", "Non-Peak"])
weather = st.selectbox("🌦 Weather", ["Clear", "Rainy", "Foggy"])

st.markdown('</div>', unsafe_allow_html=True)

# ==================================================
# PROCESS
# ==================================================
if st.button("🔍 Show Routes") and source and destination:
    with st.spinner("Analyzing traffic conditions..."):
        time.sleep(1)

        cars = estimate_traffic(time_type, weather)
        percent, level, icon = congestion_percentage(cars)

        routes = generate_named_routes(source, destination)

        st.subheader("🛣 Available Routes")

        for r in routes:
            avg_speed = 25 if level == "High" else 35 if level == "Medium" else 45
            time_min = int((r["distance"] / avg_speed) * 60)

            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.write(f"**Route:** {r['path']}")
            st.write(f"📏 Distance: **{r['distance']} km**")
            st.write(f"⏱ Estimated Time: **{time_min} minutes**")
            st.write(f"🚦 Congestion: **{percent}% {icon} ({level})**")
            st.markdown('</div>', unsafe_allow_html=True)

        prompt = f"""
        City: {city}
        Time: {time_type}
        Weather: {weather}
        Routes analyzed between {source} and {destination}.
        Provide traffic management and travel advice.
        """

        st.subheader("🤖 AI Traffic Insights")
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.write(ai_suggestions(prompt))
        st.markdown('</div>', unsafe_allow_html=True)
