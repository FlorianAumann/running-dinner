"""Geolocation of a single place"""


class GeoLocation(object):
    latitude: float
    longitude: float

    def __init__(self, latitude, longitude):
        self.latitude = latitude
        self.longitude = longitude
