import unittest
from unittest import mock

from helpers import la
import net
import weather


def payload(temps, rains, days=("2026-10-05",)):
    """A minimal Open-Meteo response: one temps/rains list (24 values) per day."""
    hourly = {"time": [], "temperature_2m": [], "precipitation_probability": [], "weather_code": [], "is_day": []}
    for d, t_list, r_list in zip(days, temps, rains):
        for h in range(24):
            hourly["time"].append(f"{d}T{h:02d}:00")
            hourly["temperature_2m"].append(t_list[h])
            hourly["precipitation_probability"].append(r_list[h])
            hourly["weather_code"].append(0)
            hourly["is_day"].append(1 if 7 <= h <= 18 else 0)
    n = len(days)
    daily = {"time": list(days), "temperature_2m_max": [78.4] * n, "temperature_2m_min": [51.6] * n,
             "weather_code": [61] * n, "precipitation_probability_max": [40] * n,
             "sunrise": [f"{d}T06:59" for d in days], "sunset": [f"{d}T18:35" for d in days]}
    return {"hourly": hourly, "daily": daily}


WARM = [50, 50, 50, 50, 50, 50, 52, 54, 56, 60, 64, 68, 72, 76, 78, 80, 84, 86, 82, 70, 60, 55, 52, 50]
DRY = [0] * 24


class WeatherTest(unittest.TestCase):
    def test_nice_window_needs_daylight_temperature_and_dry(self):
        day = weather.parse(payload([WARM], [DRY]), la(2026, 10, 5, 7))["days"][0]
        # 08:00 (56°) through 16:00 (84°); 17:00 is 86° (too hot); 18:00 is 82° but a lone hour.
        self.assertEqual(day["nice"], [{"from": "08:00", "to": "17:00"}])

    def test_rain_breaks_the_window(self):
        rain = list(DRY)
        rain[12] = rain[13] = 60
        day = weather.parse(payload([WARM], [rain]), la(2026, 10, 5, 7))["days"][0]
        self.assertEqual(day["nice"], [{"from": "08:00", "to": "12:00"}, {"from": "14:00", "to": "17:00"}])

    def test_missing_values_are_not_nice(self):
        temps = list(WARM)
        temps[10] = None
        rains = list(DRY)
        rains[14] = None
        day = weather.parse(payload([temps], [rains]), la(2026, 10, 5, 7))["days"][0]
        self.assertEqual(day["nice"], [{"from": "08:00", "to": "10:00"}, {"from": "11:00", "to": "14:00"},
                                       {"from": "15:00", "to": "17:00"}])

    def test_daily_fields(self):
        out = weather.parse(payload([WARM], [DRY]), la(2026, 10, 5, 7))
        self.assertEqual(out["generatedAt"], "2026-10-05T14:00:00Z")
        day = out["days"][0]
        self.assertEqual((day["date"], day["high"], day["low"]), ("2026-10-05", 78, 52))
        self.assertEqual((day["summary"], day["emoji"], day["rain"]), ("Rain", "🌧️", 40))
        self.assertEqual((day["sunrise"], day["sunset"]), ("06:59", "18:35"))
        self.assertEqual(day["hours"][14], {"h": 14, "t": 78, "rain": 0})

    def test_describe(self):
        self.assertEqual(weather.describe(0), ("Clear", "☀️"))
        self.assertEqual(weather.describe(2), ("Partly cloudy", "⛅"))
        self.assertEqual(weather.describe(75), ("Snow", "🌨️"))
        self.assertEqual(weather.describe(95), ("Thunderstorms", "⛈️"))
        self.assertEqual(weather.describe(None), ("Unknown", "🌡️"))

    def test_reshaped_response_is_a_fetch_error(self):
        with mock.patch.object(net, "get_json", lambda url, **kw: {"error": True, "reason": "nope"}):
            with self.assertRaises(net.FetchError):
                weather.fetch(la(2026, 10, 5, 7))


if __name__ == "__main__":
    unittest.main()
