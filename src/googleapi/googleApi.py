"""This class handles all request to the google API"""
import json
import httplib2


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
