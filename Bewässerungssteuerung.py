import polars as pl
from wetterdienst.provider.dwd.observation import DwdObservationRequest, DwdObservationPeriod, DwdObservationResolution
import requests
import time
from datetime import datetime, timedelta, timezone

# Benutzerdefinierte Variablen
SHELLY_URL = "http://192.168.178.204/relay/0"  # Statische IP-Adresse des Shelly 1 im Netzwerk
LATITUDE = 49.XXXX  # Ersetzen Sie dies durch Ihre Breitenangabe
LONGITUDE = 8.XXXX  # Ersetzen Sie dies durch Ihre Längengabe

def get_nearest_station(lat, lon):
    request = DwdObservationRequest(
        parameter="precipitation_height",
        resolution=DwdObservationResolution.DAILY,
        period=DwdObservationPeriod.RECENT
    )
    stations = request.all().df
    schema = stations.collect_schema()
    stations = stations.with_columns(
        ((pl.col("latitude") - lat)**2 + (pl.col("longitude") - lon)**2).sqrt().alias("distance")
    )
    nearest_station = stations.sort("distance").head(1).select("station_id", "name")
    return nearest_station[0, "station_id"], nearest_station[0, "name"]

def get_historical_precipitation(station_id):
    request = DwdObservationRequest(
        parameter="precipitation_height",
        resolution=DwdObservationResolution.DAILY,
        period=DwdObservationPeriod.RECENT
    ).filter_by_station_id(station_id=[station_id])

    result = request.values.all()
    df = result.df
    df = df.with_columns(pl.col("date").cast(pl.Date))  # Konvertiere die Datumsspalte
    return df

def get_forecast_precipitation(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=precipitation"
    response = requests.get(url)
    data = response.json()
    forecast = []

    for timestamp, precipitation in zip(data['hourly']['time'], data['hourly']['precipitation']):
        try:
            date = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S').date()
        except ValueError:
            date = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M').date()
        forecast.append((date, precipitation))

    df = pl.DataFrame(forecast, schema={"date": pl.Date, "value": pl.Float64}, orient="row")
    return df

def evaluate_precipitation(historical_data, forecast_data):
    today = datetime.now(timezone.utc).date()
    three_days_ago = today - timedelta(days=3)
    two_days_ahead = today + timedelta(days=2)

    # Check historical precipitation for the last three days
    last_three_days = historical_data.filter(pl.col("date") >= three_days_ago).select(pl.col("value"))
    no_rain_last_three_days = last_three_days["value"].sum() == 0.0

    # Check forecast precipitation for the next two days
    next_two_days = forecast_data.filter((pl.col("date") >= today) & (pl.col("date") <= two_days_ahead)).select(pl.col("value"))
    no_rain_next_two_days = next_two_days["value"].sum() == 0.0

    return no_rain_last_three_days and no_rain_next_two_days

def control_pump(should_run):
    if should_run:
        print("Pumpe läuft für eine Stunde.")
        try:
            requests.get(f"{SHELLY_URL}/on")
            time.sleep(3600)  # Pumpe läuft für eine Stunde
            requests.get(f"{SHELLY_URL}/off")
            print("Pumpe ausgeschaltet.")
        except requests.exceptions.RequestException as e:
            print(f"Fehler beim Zugriff auf Shelly: {e}")
    else:
        print("Pumpe bleibt aus.")

if __name__ == "__main__":
    lat, lon = LATITUDE, LONGITUDE
    station_id, station_name = get_nearest_station(lat, lon)
    print(f"Nächste Wetterstation: {station_name} (ID: {station_id})")

    historical_data = get_historical_precipitation(station_id)
    forecast_data = get_forecast_precipitation(lat, lon)

    should_run_pump = evaluate_precipitation(historical_data, forecast_data)
    control_pump(should_run_pump)
