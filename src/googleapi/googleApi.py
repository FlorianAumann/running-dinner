"""This class handles all request to the google API"""
import json
import urllib

import httplib2

from src.data.geoLocation import GeoLocation


"""Helper method for download_path_map"""
def geoloc_to_string(geolocation: GeoLocation):
    return str(geolocation.latitude) + "," + str(geolocation.longitude)


class GoogleApi:
    __api_key: str

    def __init__(self, api_key: str):
        """
        @param: api_key The api_key used for connection to google API
        """
        self.__api_key = api_key

    def get_walking_duration(self, str_from, str_to):
        """ Requests the walking duration in seconds between two places

        @param: str_from The starting location
        @param: str_to The goal location
        """
        # Create url for request
        url = "https://maps.googleapis.com/maps/api/distancematrix/json?units=metric&mode=walking&origins=" + str_from + "&destinations=" + str_to + "&key=" + self.__api_key
        h = httplib2.Http()
        resp, content = h.request(url, "GET")
        if resp.status != 200:
            raise Exception('get_walking_distance: Invalid response: ' + str(resp.status))

        json_obj = json.loads(content)

        status = json_obj["status"]
        if status is None:
            raise Exception('Field "status" not found')

        # Sanity check return status
        if status != "OK":
            error_msg = json_obj["error_message"]
            raise Exception(f'Invalid status with message \"{error_msg}\"')

        rows = json_obj["rows"]
        if rows is None:
            raise Exception('Field "rows" not found')
        first_row = rows[0]

        if first_row is None:
            raise Exception('No rows found')

        elements = first_row["elements"]
        if elements is None:
            raise Exception('Field "elements" not found')

        first_element = elements[0]
        if first_element is None:
            raise Exception('No elements found')

        duration = first_element["duration"]
        if duration is None:
            raise Exception('Field "duration" not found')

        status = first_element["status"]
        if status is None:
            raise Exception('Element field "status" not found')

        # Sanity check element status
        if status != "OK":
            if status == "NOT_FOUND":
                raise Exception('Address ' + str_from + ' or ' + str_to + ' could not be found!')
            else:
                raise Exception('Invalid status')

        # Duration in seconds
        duration_value = duration["value"]
        if duration_value is None:
            raise Exception('Field "value" of "duration" not found')

        return duration_value

    def get_geolocation_from_address(self, address) -> GeoLocation:
        """ Retrieves geolocation (Latitude / longitude) for a given address

        @param: address The address as string
        """
        url = "https://maps.googleapis.com/maps/api/geocode/json?address=" + address + "&key=" + self.__api_key
        h = httplib2.Http()
        resp, content = h.request(url, "GET")
        if resp.status != 200:
            raise Exception('getGeoLocationFromAddress: Invalid response: ' + str(resp.status))

        json_obj = json.loads(content)

        status = json_obj["status"]
        if status is None:
            raise Exception('Field "status" not found')

        # Sanity check return status
        if status != "OK":
            error_msg = json_obj["error_message"]
            raise Exception(f'Invalid status with message \"{error_msg}\"')

        results = json_obj["results"]
        if results is None:
            raise Exception('Field "results" not found')
        first_row = results[0]

        if first_row is None:
            raise Exception('FirstRow not found')

        geometry = first_row["geometry"]
        if geometry is None:
            raise Exception('Field "geometry" not found')

        location = geometry["location"]
        if location is None:
            raise Exception('Field "location" not found')

        latitude = location["lat"]
        longitude = location["lng"]
        if latitude is None or longitude is None:
            raise Exception('Field "latitude" or "longitude" not found')

        return GeoLocation(latitude, longitude)

    def download_path_map(self, locations: [GeoLocation], color: str, active_index: int, dest_path: str):
        """ Creates a map visualizing a path through all given locations
        Will create a path with the given color
        Will store the retrieved map file under the given file destination

        @param: locations All locations of the path
        @param: color The color of the path, as string with color name
        @param: active_index The index of the location in locations to highlight
        @param: dest_path The file location to store the result to
        """
        url = "https://maps.googleapis.com/maps/api/staticmap?size=1000x1000&scale=2"
        url += "&path=color:0x" + color + "|weight:3"
        for location in locations:
            url += "|" + geoloc_to_string(location)

        # Add label to each location, mark the active one in a different color
        for i in range(len(locations)):
            if i == active_index:
                url += "&markers=color:red"
            else:
                url += "&markers=color:blue"
            url += "%7Clabel:" + str(i + 1) + "%7C" + geoloc_to_string(locations[i])

        url += "&key=" + self.__api_key
        # Retrieve map and save as image file under give path
        urllib.request.urlretrieve(url, dest_path)
