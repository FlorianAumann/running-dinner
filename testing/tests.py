import unittest

from src.config import ConfigManager
from src.googleapi.googleApi import GoogleApi


class TestGoogleAPI(unittest.TestCase):
    def setUp(self):
        config_manager = ConfigManager()
        self.config = config_manager.load_config()
        self.google_api = GoogleApi(self.config.google_api_key)

    def test_walking_duration(self):
        distance = self.google_api.get_walking_duration("Pl. de l'Église, 03390 Montmarault, France", "Rue Joliot Curie, 03390 Montmarault, France")
        self.assertGreater(distance, 0)
