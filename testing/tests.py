import os
import tempfile
import unittest

from numpy import array_equal

from src.config import ConfigManager
from src.data.geoLocation import GeoLocation
from src.googleapi.googleApi import GoogleApi
from src.planning.optimizer import GeneticOptimizerWithFinalLocation, COURSE_COUNT
from src.planning.rating import DiversitySolutionRater, SolutionRater, CombinedSolutionRater, \
    FinalLocationDistanceSolutionRater, InterDistanceSolutionRater
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
        expected_paths_per_host = {4: [4, 6, 7], 1: [1, 0, 5], 3: [3, 8, 2], 6: [4, 6, 5], 0: [1, 0, 7], 8: [3, 8, 2],
                                   7: [4, 0, 7], 5: [3, 8, 5], 2: [1, 6, 2]}
        print(paths_per_host)
        self.assertTrue(array_equal(expected_paths_per_host, paths_per_host))


class Rating(unittest.TestCase):
    def test_rate_combined(self):
        # Test 1 error on empty list
        self.assertRaises(ValueError, CombinedSolutionRater, [])

        # Test 2 Default use case
        # Create a dummy rater class that always returns a fixed
        class DummySolutionRater(SolutionRater):
            def __init__(self, value: float):
                self.value = value

            def rate_solution(self, paths_per_host: {int: [int]}) -> float:
                return self.value

        raters = [(1, DummySolutionRater(1)), (4, DummySolutionRater(0.5)), (15, DummySolutionRater(0))]
        rater = CombinedSolutionRater(raters)
        # Rate a solution with the dummy raters and check against expected value
        paths_per_host = {0: [0, 1], 1: [0, 1], 2: [2, 3], 3: [2, 3]}
        self.assertAlmostEqual(rater.rate_solution(paths_per_host), 0.15, places=3)

    def test_rate_diversity(self):
        rater = DiversitySolutionRater()
        # Test #1 Rate worst case 2 courses
        paths_per_host = {0: [0, 1], 1: [0, 1], 2: [2, 3], 3: [2, 3]}
        self.assertAlmostEqual(rater.rate_solution(paths_per_host), 0, places=3)
        # Test #2 Rate best case 2 courses
        paths_per_host = {0: [0, 1], 1: [2, 1], 2: [2, 3], 3: [0, 3]}
        self.assertAlmostEqual(rater.rate_solution(paths_per_host), 1, places=3)
        # Test #3 Rate worst case 3 courses
        paths_per_host = {5: [5, 6, 7], 1: [1, 0, 4], 3: [3, 8, 2], 6: [5, 6, 7], 0: [1, 0, 4], 8: [3, 8, 2],
                          7: [5, 6, 7], 4: [1, 0, 4], 2: [3, 8, 2]}
        self.assertAlmostEqual(rater.rate_solution(paths_per_host), 0, places=3)
        # Test #4 Rate best case 3 courses
        paths_per_host = {0: [0, 1, 2], 1: [3, 1, 4], 2: [3, 5, 2], 3: [3, 6, 8], 4: [0, 5, 4], 5: [7, 5, 8],
                          6: [0, 6, 8], 7: [7, 1, 4], 8: [7, 6, 2]}
        self.assertAlmostEqual(rater.rate_solution(paths_per_host), 1, places=3)

    def test_rate_inter_distance(self):
        distance_matrix = [[0, 1, 2, 24, 35, 5, 22, 5, 1],
                           [1, 0, 9, 9, 9, 9, 99, 9, 9],
                           [2, 9, 0, 97, 97, 87, 97, 2, 33],
                           [24, 9, 97, 0, 8, 8, 8, 8, 8],
                           [35, 9, 97, 8, 0, 53, 63, 63, 63],
                           [5, 9, 87, 8, 63, 0, 55, 54, 5],
                           [22, 9, 97, 8, 63, 55, 0, 25, 99],
                           [5, 9, 2, 8, 63, 54, 25, 0, 51],
                           [1, 9, 33, 8, 63, 5, 99, 51, 0]]
        rater = InterDistanceSolutionRater(distance_matrix, 3)
        # Test #1 Rate worst case 3 courses
        paths_per_host = {0: [2, 3, 0], 1: [1, 6, 8], 2: [2, 3, 0], 3: [2, 3, 0], 4: [4, 7, 5], 5: [4, 7, 5],
                          6: [1, 6, 8], 7: [4, 7, 5], 8: [1, 6, 8]}
        self.assertAlmostEqual(rater.rate_solution(paths_per_host), 0, places=3)
        # Test #2 Rate best case 3 courses
        paths_per_host = {0: [0, 1, 2], 1: [0, 1, 2], 2: [0, 1, 2], 3: [5, 8, 3], 4: [6, 7, 4], 5: [5, 8, 3],
                          6: [6, 7, 4], 7: [6, 7, 4], 8: [5, 8, 3]}
        self.assertAlmostEqual(rater.rate_solution(paths_per_host), 1, places=3)

    def test_rate_dist_to_final_location(self):
        dst_to_final_location = [63, 95, 96, 8, 99, 78, 63, 105, 52]
        rater = FinalLocationDistanceSolutionRater(dst_to_final_location, 3)
        # Test #1 Rate worst case 3 courses
        paths_per_host = {5: [5, 6, 7], 1: [1, 0, 4], 3: [3, 8, 2], 6: [5, 6, 7], 0: [1, 0, 4], 8: [3, 8, 2],
                          7: [5, 6, 7], 4: [1, 0, 4], 2: [3, 8, 2]}
        self.assertAlmostEqual(rater.rate_solution(paths_per_host), 0, places=3)
        # Test #2 Rate best case 3 courses
        paths_per_host = {5: [5, 6, 0], 1: [1, 7, 3], 4: [4, 2, 8], 6: [5, 6, 0], 7: [1, 7, 3], 2: [4, 2, 8],
                          0: [5, 6, 0], 3: [1, 7, 3], 8: [4, 2, 8]}
        self.assertAlmostEqual(rater.rate_solution(paths_per_host), 1, places=3)
