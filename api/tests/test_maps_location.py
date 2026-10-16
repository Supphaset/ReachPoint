"""Synthetic Maps responses only: no real location or paid service calls."""

import unittest
from unittest.mock import patch

import httpx

from api.location import google_maps as maps


class MapsLocationTests(unittest.TestCase):
    def setUp(self):
        self.config = patch.object(maps, "_config", return_value=None)
        self.config.start()
        self.addCleanup(self.config.stop)

    def test_query_pin_and_existing_coordinates_are_retained(self):
        result = maps.resolve({"location": "https://www.google.com/maps/search/?api=1&query=7.0%2C100.5"})
        self.assertEqual((result["latitude"], result["longitude"]), (7.0, 100.5))
        self.assertIsNone(result["address"])
        self.assertEqual(result["status"], "partial")
        result = maps.resolve({"location": "Synthetic school", "coordinates": "7.0,100.5"})
        self.assertEqual(result["status"], "resolved")
        self.assertEqual(result["source"], "caller")

    def test_short_link_to_search_path_extracts_the_reported_point(self):
        with patch.object(maps, "_expand", return_value="https://www.google.com/maps/search/7.0%2C100.5?entry=tts"):
            result = maps.resolve({"location": "https://maps.app.goo.gl/synthetic"})
        self.assertEqual((result["latitude"], result["longitude"]), (7.0, 100.5))
        self.assertIsNone(result["address"])
        self.assertEqual(result["status"], "partial")

    def test_viewport_does_not_establish_a_pin(self):
        for link in ("https://www.google.com/maps/@7.0,100.5,15z", "https://maps.google.com/?ll=7.0,100.5"):
            result = maps.resolve({"location": link})
            self.assertIsNone(result["latitude"])
            self.assertEqual(result["status"], "unresolved")

    def test_routes_and_multiple_pins_are_not_a_single_pickup(self):
        for link in ("https://www.google.com/maps/dir/data=!3d7.0!4d100.5", "https://www.google.com/maps/place/Area/data=!3d7.0!4d100.5!3d8.0!4d101.5"):
            self.assertEqual(maps.resolve({"location": link})["status"], "unresolved")

    def test_place_id_takes_precedence_over_fallback_query_point(self):
        link = "https://www.google.com/maps/search/?api=1&query=7,100.5&query_place_id=synthetic-place-id"
        self.assertIsNone(maps.resolve({"location": link})["latitude"])
        with patch.object(maps, "_geocode", return_value={"address": "Synthetic school", "latitude": 7.01, "longitude": 100.51}):
            result = maps.resolve({"location": link})
        self.assertEqual((result["latitude"], result["longitude"]), (7.01, 100.51))

    def test_short_link_expands_only_through_maps_hosts(self):
        def respond(request):
            return httpx.Response(302, headers={"location": "https://www.google.com/maps/place/Synthetic+school/data=!3d7.0!4d100.5"})
        client = httpx.Client(transport=httpx.MockTransport(respond))
        with patch.object(maps.httpx, "Client", return_value=client):
            result = maps.resolve({"location": "https://maps.app.goo.gl/synthetic"})
        self.assertEqual(result["address"], "Synthetic school")
        self.assertEqual((result["latitude"], result["longitude"]), (7.0, 100.5))
        self.assertEqual(result["status"], "resolved")

    def test_untrusted_links_and_redirects_never_fetch_arbitrary_hosts(self):
        for link in ("https://maps.app.goo.gl.evil.test/", "http://127.0.0.1/", "https://google.com/url?q=http://127.0.0.1", "https://user:pass@maps.app.goo.gl/test"):
            with patch.object(maps.httpx, "Client") as client:
                self.assertEqual(maps.resolve({"location": link})["status"], "unresolved")
                client.assert_not_called()
        requests = []
        def redirect(request):
            requests.append(str(request.url))
            return httpx.Response(302, headers={"location": "http://127.0.0.1/private"})
        client = httpx.Client(transport=httpx.MockTransport(redirect))
        with patch.object(maps.httpx, "Client", return_value=client):
            result = maps.resolve({"location": "https://maps.app.goo.gl/synthetic"})
        self.assertEqual(len(requests), 1)
        self.assertEqual(result["status"], "unresolved")

    def test_reverse_geocoding_retains_the_original_pin(self):
        with patch.object(maps, "_geocode", return_value={"address": "Synthetic school address", "latitude": 7.001, "longitude": 100.501}):
            result = maps.resolve({"location": "https://maps.google.com/?q=7.0,100.5"})
        self.assertEqual(result["address"], "Synthetic school address")
        self.assertEqual((result["latitude"], result["longitude"]), (7.0, 100.5))
        self.assertEqual(result["source"], "google_maps_geocoding")

    def test_geocoder_is_opt_in_and_rejects_partial_or_ambiguous_results(self):
        with patch.object(maps.httpx, "get") as get:
            self.assertIsNone(maps._geocode("Synthetic school", None, None))
            get.assert_not_called()
        record = {"formatted_address": "Synthetic school", "geometry": {"location": {"lat": 7.0, "lng": 100.5}}}
        for results in ([{**record, "partial_match": True}], [record, record]):
            response = httpx.Response(200, json={"status": "OK", "results": results}, request=httpx.Request("GET", "https://maps.googleapis.com/"))
            with patch.object(maps, "_config", side_effect=lambda name: "on" if name == "REACHPOINT_MAPS_GEOCODING" else "synthetic-key"), patch.object(maps.httpx, "get", return_value=response):
                self.assertIsNone(maps._geocode("Synthetic school", None, None))

    def test_reverse_geocoding_accepts_address_hierarchy_and_preserves_pin(self):
        records = [
            {"formatted_address": "Synthetic building address", "types": ["premise", "street_address"],
             "geometry": {"location": {"lat": 7.001, "lng": 100.501}}},
            {"formatted_address": "Synthetic district", "types": ["administrative_area_level_2"],
             "geometry": {"location": {"lat": 7.02, "lng": 100.52}}},
        ]
        response = httpx.Response(200, json={"status": "OK", "results": records},
                                  request=httpx.Request("GET", "https://maps.googleapis.com/"))
        with patch.object(maps, "_config", side_effect=lambda name: "on" if name == "REACHPOINT_MAPS_GEOCODING" else "synthetic-key"), \
                patch.object(maps.httpx, "get", return_value=response):
            result = maps.resolve({"location": "https://maps.google.com/?q=7.0,100.5"})
        self.assertEqual(result["address"], records[0]["formatted_address"])
        self.assertEqual((result["latitude"], result["longitude"]), (7.0, 100.5))
        self.assertEqual(result["source"], "google_maps_geocoding")

    def test_invalid_points_and_disabled_network_remain_unknown(self):
        for value in ("NaN,100.5", "91,100.5", "7,181", "7,100,2"):
            self.assertIsNone(maps.point(value))
        with patch.object(maps, "_expand") as expand, patch.object(maps, "_geocode") as geocode:
            result = maps.resolve({"location": "https://maps.app.goo.gl/synthetic"}, network=False)
            self.assertEqual(result["status"], "unresolved")
            expand.assert_not_called()
            geocode.assert_not_called()
