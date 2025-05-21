import streamlit as st
import requests
from datetime import datetime, time, timezone, timedelta
from collections import defaultdict
import pandas as pd

API_KEY = 'e70daeaec703afb866ed8107b1c6cf8b'

st.set_page_config(page_title="Weather App", layout="wide")
st.title("🌦️ Simple Weather App")

unit = st.selectbox("Select temperature unit:", ["Celsius", "Fahrenheit"])
units_param = "metric" if unit == "Celsius" else "imperial"
unit_symbol = "°C" if unit == "Celsius" else "°F"

location = st.text_input("Enter a city (London), landmark (Eiffle Tower), or GPS coordinates (lat,lon):")

if st.button("Get Weather") and location:
    try:
        def is_coordinates(input_str):
            parts = input_str.split(',')
            return len(parts) == 2 and all(
                p.strip().replace('.', '', 1).replace('-', '', 1).isdigit() for p in parts
            )

        if is_coordinates(location):
            lat, lon = location.split(',')
        else:
            nominatim_url = f"https://nominatim.openstreetmap.org/search?q={location}&format=json&limit=1"
            headers = {"User-Agent": "streamlit-weather-app"}
            geo_res = requests.get(nominatim_url, headers=headers).json()

            if geo_res:
                lat = geo_res[0]['lat']
                lon = geo_res[0]['lon']
            else:
                st.error("Location not found via Nominatim. Please try a city or known landmark.")
                st.stop()

        left_col, right_col = st.columns([1, 3], gap="small")

        with right_col:
            st.subheader("📍 Location Map")
            map_df = pd.DataFrame({"lat": [float(lat)], "lon": [float(lon)]})
            st.map(map_df, zoom=12, use_container_width=False)
            

        with left_col:
            current_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat.strip()}&lon={lon.strip()}&appid={API_KEY}&units={units_param}"
            res = requests.get(current_url)
            data = res.json()

            if data['cod'] != 200:
                st.error(f"Error: {data['message']}")
                st.stop()

            local_time = datetime.fromtimestamp(data['dt'], tz=timezone.utc).astimezone(timezone(timedelta(seconds=data['timezone']))).strftime('%A, %B %d • %I:%M %p')
            st.subheader(f"Current Weather in {data['name']}, {data['sys']['country']}")
            st.write(f"{local_time}")
            icon_code = data['weather'][0]['icon']
            st.image(f"http://openweathermap.org/img/wn/{icon_code}@2x.png")
            st.write(f"**{data['weather'][0]['main']}** - {data['weather'][0]['description'].capitalize()}")

            st.metric(label=f"Temperature ({unit_symbol})", value=f"{data['main']['temp']}{unit_symbol}")
            st.metric(label="Feels Like", value=f"{data['main']['feels_like']}{unit_symbol}")
            st.write(f"Humidity: {data['main']['humidity']}%")
            st.write(f"Wind Speed: {data['wind']['speed']} m/s")

            sunrise = datetime.fromtimestamp(data['sys']['sunrise']).strftime('%H:%M')
            sunset = datetime.fromtimestamp(data['sys']['sunset']).strftime('%H:%M')
            st.write(f"Sunrise: {sunrise} ⛅  |  Sunset: {sunset} 🌇")

            # One Call API - UV Index 
            one_call_url = f"https://api.openweathermap.org/data/2.5/onecall?lat={lat.strip()}&lon={lon.strip()}&exclude=minutely,daily,hourly&appid={API_KEY}&units={units_param}"
            one_data = requests.get(one_call_url).json()

            if 'current' in one_data and 'uvi' in one_data['current']:
                uvi = one_data['current']['uvi']
                st.write(f"🌞 UV Index: {uvi}")
            else:
                st.write("🌞 UV Index not available.")

            if 'alerts' in one_data:
                for alert in one_data['alerts']:
                    st.write(f"⚠️ {alert['event']}\n\n{alert['description']}")
            else:
                st.write("⚠️ Alerts not available.")


        st.subheader("5-Day Forecast")
        forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat.strip()}&lon={lon.strip()}&appid={API_KEY}&units={units_param}"
        forecast_data = requests.get(forecast_url).json()

        daily_forecast = defaultdict(list)

        for entry in forecast_data['list']:
            date = datetime.fromtimestamp(entry['dt']).date()
            temp = entry['main']['temp']
            condition = entry['weather'][0]['main']
            icon = entry['weather'][0]['icon']
            forecast_time = datetime.fromtimestamp(entry['dt']).time()
            daily_forecast[date].append((temp, condition, icon, forecast_time))

        cols = st.columns(5)
        for idx, (date, values) in enumerate(list(daily_forecast.items())[1:6]):
            with cols[idx]:
                temps = [v[0] for v in values]
                daytime_entry = next((v for v in values if 9 <= v[3].hour <= 15), values[0])
                main_temp, main_condition, main_icon, _ = daytime_entry

                st.markdown(f"#### {date.strftime('%a, %b %d')}")
                st.image(f"http://openweathermap.org/img/wn/{main_icon}@2x.png")
                st.write(f"{main_condition}")
                st.write(f"⬆️ {max(temps):.1f}{unit_symbol}")
                st.write(f"⬇️ {min(temps):.1f}{unit_symbol}")

    except Exception as e:
        import traceback
        st.error("An error occurred while fetching weather data.")
        st.text(traceback.format_exc())
