import os
import tempfile
import unittest

from numpy import array_equal

from src.config import ConfigManager
from src.data.geoLocation import GeoLocation
from src.googleapi.googleApi import GoogleApi
from src.planning.solution import DinnerGroup, Solution
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


class Optimizer(unittest.TestCase):
    def test_get_paths_per_host_simple(self):
        # Simple test where each column of the table eats all courses together
        groups_per_course = [[DinnerGroup(5, [0, 0]), DinnerGroup(1, [1, 1]), DinnerGroup(3, [2, 2])],
                             [DinnerGroup(6, [0, 0]), DinnerGroup(0, [1, 1]), DinnerGroup(8, [2, 2])],
                             [DinnerGroup(7, [0, 0]), DinnerGroup(4, [1, 1]), DinnerGroup(2, [2, 2])]]
        test_solution = Solution(groups_per_course)
        paths_per_host = test_solution.get_paths_per_host()
        expected_paths_per_host = {5: [5, 6, 7], 1: [1, 0, 4], 3: [3, 8, 2], 6: [5, 6, 7], 0: [1, 0, 4], 8: [3, 8, 2], 7: [5, 6, 7], 4: [1, 0, 4], 2: [3, 8, 2]}
        self.assertTrue(array_equal(expected_paths_per_host, paths_per_host))

    def test_get_paths_per_host_complex(self):
        # More complex test where groups are mixed up
        groups_per_course = [[DinnerGroup(4, [0, 0]), DinnerGroup(1, [1, 2]), DinnerGroup(3, [2, 1])],
                             [DinnerGroup(6, [1, 1]), DinnerGroup(0, [0, 2]), DinnerGroup(8, [2, 0])],
                             [DinnerGroup(7, [2, 1]), DinnerGroup(5, [1, 0]), DinnerGroup(2, [0, 2])]]
        test_solution = Solution(groups_per_course)
        paths_per_host = test_solution.get_paths_per_host()
        expected_paths_per_host = {4: [4, 6, 7], 1: [1, 0, 5], 3: [3, 8, 2], 6: [4, 6, 5], 0: [1, 0, 7], 8: [3, 8, 2], 7: [4, 0, 7], 5: [3, 8, 5], 2: [1, 6, 2]}
        print(paths_per_host)
        self.assertTrue(array_equal(expected_paths_per_host, paths_per_host))

