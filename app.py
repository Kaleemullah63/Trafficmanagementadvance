import streamlit as st
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
# API KEY
# ==================================================
GROQ_API_KEY = "API_KEY"

# ==================================================
# MODERN UI STYLE
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
# WORLDWIDE COUNTRY → CITY DATA (≈30 CITIES EACH)
# ==================================================
COUNTRY_CITY_MAP = {
    "Pakistan": [
        "Karachi","Lahore","Islamabad","Rawalpindi","Multan","Faisalabad",
        "Gujranwala","Sialkot","Bahawalpur","Sargodha","Sheikhupura",
        "Rahim Yar Khan","Okara","Mardan","Swat","Abbottabad",
        "Peshawar","Quetta","Hyderabad","Sukkur","Larkana",
        "Mirpur","Muzaffarabad","Chaman","Khuzdar","Gwadar",
        "Kasur","Vehari","Dera Ghazi Khan"
    ],

    "India": [
        "Delhi","Mumbai","Bangalore","Chennai","Hyderabad","Kolkata",
        "Pune","Ahmedabad","Surat","Jaipur","Udaipur","Jodhpur",
        "Indore","Bhopal","Gwalior","Kanpur","Lucknow","Varanasi",
        "Patna","Ranchi","Bhubaneswar","Cuttack","Vijayawada",
        "Visakhapatnam","Tirupati","Madurai","Trichy","Coimbatore",
        "Salem","Erode"
    ],

    "United States": [
        "New York","Los Angeles","Chicago","Houston","Phoenix","San Diego",
        "Dallas","Austin","San Antonio","San Jose","San Francisco",
        "Seattle","Portland","Denver","Boulder","Las Vegas","Reno",
        "Salt Lake City","Miami","Orlando","Tampa","Atlanta","Savannah",
        "Boston","Cambridge","New Haven","Hartford","Newark","Jersey City",
        "Hoboken"
    ],

    "United Kingdom": [
        "London","Manchester","Birmingham","Leeds","Liverpool","Sheffield",
        "Nottingham","Derby","Leicester","Coventry","Oxford","Cambridge",
        "Milton Keynes","Reading","Slough","Windsor","Bristol","Bath",
        "Cardiff","Newport","Swansea","Edinburgh","Glasgow","Dundee",
        "Aberdeen","Inverness","Perth","Stirling","Falkirk","Paisley"
    ]
}

LOCATION_TYPES = ["Downtown", "Highway", "Residential", "School Zone", "IT Park"]

# ==================================================
# TRAFFIC ESTIMATION (SYSTEM BASED)
# ==================================================
def estimate_traffic(location_type, time_type, weather):
    base = {
        "Downtown": (120, 60, 25),
        "Highway": (180, 40, 35),
        "Residential": (70, 50, 10),
        "School Zone": (60, 30, 15),
        "IT Park": (100, 50, 20)
    }

    time_mul = 1.5 if time_type == "Peak" else 1.0
    weather_mul = {"Clear":1.0, "Rainy":1.2, "Foggy":1.3}[weather]

    cars, bikes, buses = base[location_type]

    return (
        int(cars * time_mul * weather_mul),
        int(bikes * time_mul * weather_mul),
        int(buses * time_mul * weather_mul)
    )

# ==================================================
# CONGESTION LOGIC
# ==================================================
def congestion_score(cars, bikes, buses, location_type):
    weight = {
        "Downtown":1.4,
        "Highway":1.2,
        "Residential":1.0,
        "School Zone":1.3,
        "IT Park":1.2
    }
    return (cars + bikes*0.5 + buses*2.5) * weight[location_type]

def classify(score):
    if score < 120:
        return "Low", "🟢", 5
    elif score < 220:
        return "Medium", "🟠", 15
    else:
        return "High", "🔴", 30

# ==================================================
# ROUTE GENERATION (GENERIC FOR ANY CITY)
# ==================================================
def generate_routes(source, destination):
    return [
        {"name": f"{source} → Main Road → {destination}", "type":"Downtown"},
        {"name": f"{source} → Ring Road → {destination}", "type":"Highway"},
        {"name": f"{source} → Local Streets → {destination}", "type":"Residential"}
    ]

# ==================================================
# AI SUGGESTIONS
# ==================================================
def ai_advice(prompt):
    try:
        client = Groq(api_key=GROQ_API_KEY)
        res = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role":"user","content":prompt}]
        )
        return res.choices[0].message.content
    except:
        return "AI service unavailable."

# ==================================================
# UI
# ==================================================
st.title("🚦 AI Traffic Congestion & Route Recommendation System")

st.markdown('<div class="card">', unsafe_allow_html=True)

country = st.selectbox("🌍 Country", list(COUNTRY_CITY_MAP.keys()))
city = st.selectbox("🏙 City", COUNTRY_CITY_MAP[country])

source = st.text_input("🚩 Source Area (street / colony / sector)")
destination = st.text_input("🏁 Destination Area")

location_type = st.selectbox("📍 Area Type", LOCATION_TYPES)
time_type = st.radio("⏰ Time", ["Peak", "Non-Peak"])
weather = st.selectbox("🌦 Weather", ["Clear", "Rainy", "Foggy"])

st.markdown('</div>', unsafe_allow_html=True)

# ==================================================
# PREDICTION
# ==================================================
if st.button("🔍 Find Best Route") and source and destination:
    with st.spinner("Analyzing routes..."):
        time.sleep(1)

        routes = generate_routes(source, destination)
        best_route = None
        best_score = float("inf")

        st.subheader("🛣 Alternative Routes")

        for r in routes:
            cars, bikes, buses = estimate_traffic(
                r["type"], time_type, weather
            )

            score = congestion_score(cars, bikes, buses, r["type"])
            level, icon, delay = classify(score)

            if score < best_score:
                best_score = score
                best_route = r["name"]

            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.write(f"**Route:** {r['name']}")
            st.write(f"Traffic: {icon} {level}")
            st.write(f"Estimated Delay: {delay} minutes")
            st.markdown('</div>', unsafe_allow_html=True)

        st.success(f"✅ Recommended Route (Lowest Congestion): **{best_route}**")

        prompt = f"""
        Country: {country}
        City: {city}
        Best Route: {best_route}
        Time: {time_type}
        Weather: {weather}

        Suggest traffic improvements and alternative travel advice.
        """

        st.subheader("🤖 AI Suggestions")
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.write(ai_advice(prompt))
        st.markdown('</div>', unsafe_allow_html=True)
