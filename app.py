
from flask import Flask, render_template, request, jsonify
import requests
import os
from dotenv import load_dotenv
from collections import defaultdict
from datetime import datetime

load_dotenv()

app = Flask(__name__)

API_KEY = os.getenv("WEATHER_API_KEY")
BASE_URL = "https://api.openweathermap.org/data/2.5"


@app.route("/city-suggestions")
def city_suggestions():
    query = request.args.get("q", "").strip()

    if len(query) < 2 or not API_KEY:
        return jsonify([])

    try:
        url = "https://api.openweathermap.org/geo/1.0/direct"

        params = {
            "q": query,
            "limit": 6,
            "appid": API_KEY
        }

        response = requests.get(
            url,
            params=params,
            timeout=5
        )

        response.raise_for_status()
        data = response.json()

        suggestions = []

        for city in data:
            suggestions.append({
                "name": city.get("name", ""),
                "state": city.get("state", ""),
                "country": city.get("country", ""),
                "lat": city.get("lat"),
                "lon": city.get("lon")
            })

        return jsonify(suggestions)

    except requests.exceptions.RequestException:
        return jsonify([])



@app.route("/", methods=["GET", "POST"])
def home():
    weather = None
    forecast = []
    error = None

    if request.method == "POST":
        city = request.form.get("city", "").strip()

        if not city:
            error = "Please enter a city name."
            return render_template(
                "index.html", error=error
            )

        try:
            # Current weather
            url = f"{BASE_URL}/weather"

            params = {
                "q": city,
                "appid": API_KEY,
                "units": "metric"
            }

            response = requests.get(
                url, params=params, timeout=10
            )
            response.raise_for_status()

            data = response.json()

            weather = {
                "city": data["name"],
                "country": data["sys"]["country"],
                "temperature": round(data["main"]["temp"]),
                "feels_like": round(data["main"]["feels_like"]),
                "humidity": data["main"]["humidity"],
                "wind": data["wind"]["speed"],
                "description": data["weather"][0]["description"].title(),
                "icon": data["weather"][0]["icon"]
            }

            # Five-day forecast
            forecast_url = f"{BASE_URL}/forecast"

            forecast_response = requests.get(
                forecast_url,
                params=params,
                timeout=10
            )
            forecast_response.raise_for_status()

            forecast_data = forecast_response.json()

            daily = defaultdict(list)

            for item in forecast_data["list"]:
                date = item["dt_txt"].split(" ")[0]
                daily[date].append(item)

            for date, items in list(daily.items())[:5]:
                selected = min(
                    items,
                    key=lambda x: abs(
                        datetime.strptime(
                            x["dt_txt"], "%Y-%m-%d %H:%M:%S"
                        ).hour - 12
                    )
                )

                forecast.append({
                    "date": date,
                    "temp": round(selected["main"]["temp"]),
                    "description": selected["weather"][0]["description"].title(),
                    "icon": selected["weather"][0]["icon"]
                })

        except requests.exceptions.HTTPError:
            error = "City not found. Please try another city."

        except requests.exceptions.RequestException:
            error = "Unable to connect to weather service."

        except (KeyError, ValueError):
            error = "Unexpected weather data received."

    return render_template(
        "index.html",
        weather=weather,
        forecast=forecast,
        error=error
    )


if __name__ == "__main__":
    app.run(debug=True)
