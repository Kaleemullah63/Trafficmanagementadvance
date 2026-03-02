import streamlit as st
import time
from collections import deque
from groq import Groq
import random

# ==================================================
# Page Config
# ==================================================
st.set_page_config(
    page_title="Worldwide AI Traffic Route Prediction",
    layout="wide"
)

GROQ_API_KEY = "API_KEY"

# ==================================================
# UI Style
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
# Country → City → Waypoints (city-specific accurate sample)
# ==================================================
CITY_WAYPOINTS = {
    "Multan": ["Gulgasht", "9 Number Chowk", "Kumharawala Chowk", "Vehari Chowk", "Dolat Gate", "BCG Chowk", "Market Road", "Station Chowk"],
    "Lahore": ["Model Town", "Shadman", "Ferozepur Road", "Township", "Shalimar", "Gulberg", "Liberty Market", "Iqbal Town"],
    "Karachi": ["Clifton", "Saddar", "Gulshan-e-Iqbal", "Korangi", "North Nazimabad", "Malir", "PECHS", "Bahadurabad"],
    "Delhi": ["Connaught Place", "Karol Bagh", "Rajouri Garden", "Hauz Khas", "Lajpat Nagar", "Vasant Kunj", "Saket", "Dwarka"],
    "Mumbai": ["Andheri", "Bandra", "Juhu", "Dadar", "Colaba", "Fort", "Kurla", "Malad"],
    "New York": ["Manhattan", "Brooklyn", "Queens", "Bronx", "Harlem", "Chelsea", "Times Square", "Central Park"],
    "London": ["Camden", "Soho", "Greenwich", "Chelsea", "Kensington", "Shoreditch", "Mayfair", "Notting Hill"]
}

COUNTRY_CITY_MAP = {
    "Pakistan": ["Multan","Lahore","Karachi"],
    "India": ["Delhi","Mumbai"],
    "United States": ["New York"],
    "United Kingdom": ["London"]
}

# ==================================================
# Traffic Estimation
# ==================================================
def estimate_traffic(distance, time_type, weather):
    base = distance * 15
    time_mul = 1.5 if time_type=="Peak" else 1.0
    weather_mul = {"Clear":1.0,"Rainy":1.2,"Foggy":1.3}[weather]
    cars = int(base*time_mul*weather_mul)
    return cars

def congestion_percentage(cars):
    percent = min(100, int((cars/50)*10))
    if percent<40:
        return percent,"Low","🟢"
    elif percent<70:
        return percent,"Medium","🟠"
    else:
        return percent,"High","🔴"

# ==================================================
# Dynamic Graph / Route Generation
# ==================================================
def generate_graph(waypoints):
    edges = {}
    for i in range(len(waypoints)-1):
        edges[(waypoints[i], waypoints[i+1])] = round(random.uniform(1.0,3.5),2)
    for _ in range(5):
        a,b = random.sample(waypoints,2)
        if a!=b and (a,b) not in edges and (b,a) not in edges:
            edges[(a,b)] = round(random.uniform(1.0,4.0),2)
    return edges

def find_routes(graph, start, end, max_paths=3):
    queue = deque([[start]])
    routes = []
    while queue and len(routes)<max_paths:
        path = queue.popleft()
        last = path[-1]
        if last==end:
            routes.append(path)
        else:
            neighbors = [b for (a,b) in graph if a==last] + [a for (a,b) in graph if b==last]
            for n in neighbors:
                if n not in path:
                    queue.append(path+[n])
    return routes

# ==================================================
# AI Suggestions
# ==================================================
def ai_suggestions(prompt):
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
st.title("🚦 Worldwide Dynamic AI Traffic & Route Prediction")

st.markdown('<div class="card">', unsafe_allow_html=True)

country = st.selectbox("🌍 Country", list(COUNTRY_CITY_MAP.keys()))
city = st.selectbox("🏙 City", COUNTRY_CITY_MAP[country])

source = st.text_input("🚩 Source Location")
destination = st.text_input("🏁 Destination Location")

time_type = st.radio("⏰ Time", ["Peak","Non-Peak"])
weather = st.selectbox("🌦 Weather", ["Clear","Rainy","Foggy"])

st.markdown('</div>', unsafe_allow_html=True)

if st.button("🔍 Generate Routes") and source and destination:
    with st.spinner("Generating routes..."):
        time.sleep(1)
        waypoints = CITY_WAYPOINTS.get(city, ["Central","Main Chowk","Station","Market","Hospital","Mall","Bridge","Park"])
        if source not in waypoints: waypoints[0]=source
        if destination not in waypoints: waypoints[-1]=destination

        graph = generate_graph(waypoints)
        routes = find_routes(graph, source, destination, max_paths=3)

        st.subheader("🛣 Alternative Routes")
        route_info = []

        for path in routes:
            segments=[]
            total_distance=0
            for i in range(len(path)-1):
                a,b = path[i], path[i+1]
                dist = graph.get((a,b)) or graph.get((b,a)) or round(random.uniform(1.0,4.0),2)
                total_distance+=dist
                cars = estimate_traffic(dist,time_type,weather)
                percent,level,icon = congestion_percentage(cars)
                segments.append({
                    "segment":f"{a} → {b}",
                    "distance":round(dist,2),
                    "time":int(dist*2),
                    "congestion":f"{percent}% {icon} ({level})"
                })
            route_info.append({"path":path,"segments":segments,"total_distance":round(total_distance,2)})

        best_route = min(route_info,key=lambda x: sum([int(s['congestion'].split('%')[0]) for s in x['segments']]))

        for r in route_info:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.write("Waypoints: ", " → ".join(r["path"]))
            st.write(f"Total Distance: {r['total_distance']} km")
            total_time=sum([s['time'] for s in r['segments']])
            st.write(f"Estimated Time: {total_time} minutes")
            st.subheader("Segments:")
            for s in r["segments"]:
                st.write(f"{s['segment']} | {s['distance']} km | {s['time']} min | Congestion: {s['congestion']}")
            if r==best_route:
                st.success("✅ Recommended Route (Lowest Congestion)")
            st.markdown('</div>', unsafe_allow_html=True)

        prompt = f"City: {city}, Source: {source}, Destination: {destination}, Time: {time_type}, Weather: {weather}. Provide traffic improvement suggestions and alternative path advice."
        st.subheader("🤖 AI Suggestions")
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.write(ai_suggestions(prompt))
        st.markdown('</div>', unsafe_allow_html=True)
