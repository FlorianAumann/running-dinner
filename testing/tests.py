import os
import tempfile
import unittest

from src.config import ConfigManager
from src.data.geoLocation import GeoLocation
from src.googleapi.googleApi import GoogleApi


class TestGoogleAPI(unittest.TestCase):
    def setUp(self):
        config_manager = ConfigManager()
        self.config = config_manager.load_config()
        self.google_api = GoogleApi(self.config.google_api_key)

    def test_walking_duration(self):
        distance = self.google_api.get_walking_duration("Pl. de l'Église, 03390 Montmarault, France",
                                                        "Rue Joliot Curie, 03390 Montmarault, France")
        self.assertGreater(distance, 0)

    def test_geolocation_from_address(self):
        geolocation = self.google_api.get_geolocation_from_address("Pl. de l'Église, 03390 Montmarault, France")
        self.assertAlmostEqual(geolocation.latitude, 46.31851, places=3)
        self.assertAlmostEqual(geolocation.longitude, 2.95353, places=3)

    def test_download_path_map(self):
        locations = [GeoLocation(46.31851, 2.95353), GeoLocation(46.3146594, 2.9495854),
                     GeoLocation(46.312925, 2.947552)]
        with tempfile.TemporaryDirectory() as tempdir:
            mapfile = os.path.join(tempdir, 'map.png')
            self.google_api.download_path_map(locations, "red", 2, mapfile)
            # We can't really test a lot here, but the file should at least exist after the method execution
            self.assertTrue(os.path.isfile(mapfile))
