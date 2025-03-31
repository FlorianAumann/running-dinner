import os
import tempfile
import unittest

from src.config import ConfigManager
from src.data.geoLocation import GeoLocation
from src.googleapi.googleApi import GoogleApi
from src.xlsx.xlsxInput import read_teams_from_xlsx


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


class TestXLSXInput(unittest.TestCase):
    def test_input_file_missing(self):
        dinner_teams = read_teams_from_xlsx(os.getcwd() + "\\nonexisting.xlsx")
        self.assertIsNone(dinner_teams)

    def test_read_xlsx(self):
        dinner_teams = read_teams_from_xlsx(os.getcwd() + "\\Test.xlsx")
        self.assertEqual(3, len(dinner_teams))
        self.assertEqual("Rue Joliot Curie, 03390 Montmarault, France", dinner_teams[1].address)
        self.assertEqual("17 Rue de Montaigut, 03390 Montmarault, France", dinner_teams[2].address)
        self.assertEqual(2, len(dinner_teams[2].participants))
        self.assertEqual("George@test.com", dinner_teams[2].participants[1].email)
        self.assertEqual("George", dinner_teams[2].participants[1].firstName)
        self.assertEqual("4", dinner_teams[0].participants[1].phone)
        self.assertEqual("None", dinner_teams[1].participants[0].food_restrictions)
