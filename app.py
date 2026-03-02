import streamlit as st
import time
from groq import Groq
from collections import deque

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(page_title="Dynamic AI Traffic Route Prediction", layout="wide")

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
# COUNTRY → CITY → ROAD NETWORK (Graph)
# Each city has nodes (areas/chowks) and edges (roads with distance)
# ==================================================
CITY_ROADS = {
    "Multan": {
        "nodes": ["Gulgasht", "9 Number Chowk", "Kumharawala Chowk", "Vehari Chowk", "Dolat Gate", "BCG Chowk"],
        "edges": {
            ("Gulgasht", "9 Number Chowk"): 2.0,
            ("9 Number Chowk", "Kumharawala Chowk"): 1.5,
            ("Kumharawala Chowk", "Vehari Chowk"): 3.0,
            ("Gulgasht", "Dolat Gate"): 2.2,
            ("Dolat Gate", "BCG Chowk"): 1.8,
            ("BCG Chowk", "Vehari Chowk"): 3.2,
            ("Gulgasht", "Vehari Chowk"): 6.0
        }
    },
    "Lahore": {
        "nodes": ["Model Town", "Shadman", "Ferozepur Road", "Township", "Shalimar", "Gulberg"],
        "edges": {
            ("Model Town", "Shadman"): 3.0,
            ("Shadman", "Ferozepur Road"): 2.5,
            ("Ferozepur Road", "Township"): 4.0,
            ("Township", "Shalimar"): 3.5,
            ("Shalimar", "Gulberg"): 2.8,
            ("Model Town", "Gulberg"): 8.0
        }
    }
}

# ==================================================
# TRAFFIC ESTIMATION (SYSTEM)
# ==================================================
def estimate_traffic(distance, time_type, weather):
    base_cars = distance * 20  # cars per km
    time_mul = 1.5 if time_type=="Peak" else 1.0
    weather_mul = {"Clear":1.0,"Rainy":1.2,"Foggy":1.3}[weather]
    cars = int(base_cars * time_mul * weather_mul)
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
# FIND ROUTES USING BFS (ALTERNATIVE PATHS)
# ==================================================
def find_routes(graph, start, end, max_paths=3):
    queue = deque([[start]])
    routes = []

    while queue and len(routes)<max_paths:
        path = queue.popleft()
        last_node = path[-1]
        if last_node == end:
            routes.append(path)
        else:
            neighbors = [b for (a,b) in graph if a==last_node] + [a for (a,b) in graph if b==last_node]
            for n in neighbors:
                if n not in path:
                    queue.append(path + [n])
    return routes

# ==================================================
# AI SUGGESTIONS
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
st.title("🚦 Dynamic AI Traffic & Route Prediction System")

st.markdown('<div class="card">', unsafe_allow_html=True)

city = st.selectbox("🏙 City", list(CITY_ROADS.keys()))
nodes = CITY_ROADS[city]["nodes"]
edges = CITY_ROADS[city]["edges"]

source = st.selectbox("🚩 Source", nodes)
destination = st.selectbox("🏁 Destination", [n for n in nodes if n!=source])

time_type = st.radio("⏰ Time", ["Peak","Non-Peak"])
weather = st.selectbox("🌦 Weather", ["Clear","Rainy","Foggy"])

st.markdown('</div>', unsafe_allow_html=True)

if st.button("🔍 Show Routes"):
    with st.spinner("Calculating routes..."):
        time.sleep(1)
        routes = find_routes(edges, source, destination, max_paths=3)
        route_info = []

        st.subheader("🛣 Alternative Routes")

        for path in routes:
            total_distance = 0
            segments = []
            for i in range(len(path)-1):
                a,b = path[i], path[i+1]
                dist = edges.get((a,b)) or edges.get((b,a))
                total_distance += dist
                cars = estimate_traffic(dist, time_type, weather)
                percent, level, icon = congestion_percentage(cars)
                segments.append({
                    "segment": f"{a} → {b}",
                    "distance": dist,
                    "time": int(dist*2),  # minutes approximation
                    "congestion": f"{percent}% {icon} ({level})"
                })
            route_info.append({"path":path, "segments":segments, "total_distance":total_distance})

        best_route = min(route_info, key=lambda x: sum([int(s['congestion'].split('%')[0]) for s in x['segments']]))

        for r in route_info:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.write("Route Waypoints: ", " → ".join(r["path"]))
            st.write(f"Total Distance: {r['total_distance']} km")
            total_time = sum([s["time"] for s in r["segments"]])
            st.write(f"Estimated Time: {total_time} minutes")
            st.subheader("Segments:")
            for s in r["segments"]:
                st.write(f"{s['segment']} | {s['distance']} km | {s['time']} min | Congestion: {s['congestion']}")
            if r==best_route:
                st.success("✅ Recommended Route (Lowest Congestion)")
            st.markdown('</div>', unsafe_allow_html=True)

        # AI Suggestions
        prompt = f"City: {city}, Source: {source}, Destination: {destination}, Time: {time_type}, Weather: {weather}. Suggest traffic improvements and alternative paths."
        st.subheader("🤖 AI Suggestions")
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.write(ai_suggestions(prompt))
        st.markdown('</div>', unsafe_allow_html=True)
