import collections
import sys
from enum import Enum
from typing import Callable
from abc import abstractmethod
from functools import reduce


class SolutionRater(object):
    """
    Abstract parent class for all rating classes, to derive a score between 0 and 1 for a given solution
    """

    @abstractmethod
    def rate_solution(self, paths_per_host: {int: [int]}) -> float:
        """
        Rate a given solution and assign it a score between 0 and 1

        :param paths_per_host: The solution to rate
        :return: A score between 0 and 1
        """
        pass


class CombinedSolutionRater(SolutionRater):
    """
    Combines multiple weighted solution raters together
    """

    def __init__(self, solution_raters: [(float, SolutionRater)]):
        """
        :param solution_raters: A list of solution raters together with their respective weights
        """
        if not solution_raters:
            raise ValueError("List of solution raters can not be empty!")
        self.solution_raters = solution_raters
        # Make sure all weights are positive floating point numbers
        if next(weight <= 0 for (weight, rater) in solution_raters):
            raise ValueError("All weights must be positive numbers!")
        # Pre-calculate the total sum of all weights so we don't have to calculate it on every pass
        self.total_weight = reduce(lambda x, y: x + y, map(lambda item: item[0], solution_raters))

    def rate_solution(self, paths_per_host: {int: [int]}) -> float:
        """
        Rate a given solution using all the raters and assign it a score between 0 and 1

        :param paths_per_host: The solution to rate
        :return: A score between 0 and 1
        """
        # Pass the solution through each solution rater and multiply the score by the raters weight
        # Then add together all the weighted ratings
        score = reduce(lambda x, y: x + y,
                       map(lambda item: item[0] * item[1].rate_solution(paths_per_host), self.solution_raters))
        # Divide by total weight again to get a score in [0,1] and return
        return score / self.total_weight


class DiversitySolutionRater(SolutionRater):
    """
    Rates dinner group diversity of a given solution. The more different teams each team meets along the way, the
    better the score
    """

    def rate_solution(self, paths_per_host: {int: [int]}) -> float:
        """
        Rate a given solution and assign it a score between 0 and 1

        :param paths_per_host: The solution to rate
        :return: A score between 0 and 1
        """
        # Iterate over all teams and count the overlaps with other teams (one overlap is always accepted)
        overlaps = 0
        for team1 in range(len(paths_per_host)):
            for team2 in range(len(paths_per_host)):
                if team1 != team2:
                    # Get intersection between both team's paths
                    intersections = collections.Counter(paths_per_host[team1]) & collections.Counter(
                        paths_per_host[team2])
                    # If more than one intersection exists, add additional intersection to count
                    if len(intersections) > 1:
                        overlaps += (len(intersections) - 1)
        # Calculate the maximum overlaps possible for this solution size
        course_count = len(paths_per_host[0])
        teams_per_course_count = len(paths_per_host)
        maximum_overlaps = (course_count - 1) * (course_count - 1) * teams_per_course_count
        # Normalize this score to be between 0 and 1
        # Then subtract it from 1.0, so it gets better the fewer overlaps we have
        # In the end, square the result so bad solutions decrease the result exponentially, not linearly
        score = (1.0 - (overlaps / maximum_overlaps)) ** 2
        return score


class FinalLocationDistanceSolutionRater(SolutionRater):
    """
    Rates a solution based on the distances the teams have to walk from their last course location to a final location
    """

    def __init__(self, dist_to_final_loc: [float], teams_per_course: int):
        self.dist_to_final_loc = dist_to_final_loc
        # Calculate theoretical best and worst case squared distances already
        # Those will be required later on to normalize the rating to a value between 0 and 1
        dist_to_final_loc_tmp = dist_to_final_loc.copy()
        self.min_squared_distance = 0
        # For each dinner group in the last course, select the next best distance and remove this location
        for i in range(teams_per_course):
            min_val = min(dist_to_final_loc_tmp)
            dist_to_final_loc_tmp.remove(min_val)
            self.min_squared_distance += (min_val ** 2) * teams_per_course
        dist_to_final_loc_tmp = dist_to_final_loc.copy()
        self.max_squared_distance = 0
        # For each dinner group in the last course, select the next worst distance and remove this location
        for i in range(teams_per_course):
            max_val = max(dist_to_final_loc_tmp)
            dist_to_final_loc_tmp.remove(max_val)
            self.max_squared_distance += (max_val ** 2) * teams_per_course

    def rate_solution(self, paths_per_host: {int: [int]}) -> float:
        """
        Rate a given solution and assign it a score between 0 and 1

        :param paths_per_host: The solution to rate
        :return: A score between 0 and 1
        """
        squared_distance = 0
        for team in paths_per_host:
            path = paths_per_host[team]
            last_location = path[-1]
            squared_distance += self.dist_to_final_loc[last_location] ** 2
        # Normalize this score to be between 0 and 1
        # Then subtract it from 1.0, so it gets better the shorter the squared distances
        return 1.0 - ((squared_distance - self.min_squared_distance) / (
                self.max_squared_distance - self.min_squared_distance))


class InterDistanceSolutionRater(SolutionRater):
    """
    Rates a solution based on the distances the teams have to walk between each course. The higher the overall distances,
    the lower the rating will be
    """

    class ExtremaType(Enum):
        """
        Helper enum for the _find_distance_extremas method
        """
        MINIMUM = 1
        MAXIMUM = 2

    def _find_distance_extremas(self, courses: int, extrema_type: ExtremaType):
        """
        Helper function to determine the extreme distance values for paths along the given distance matrix
        Using the
        :param courses: Number of courses of this dinner
        :param comparator: A function to compare distances, should favor the lower of the higher distance
        :param init_extrema_value:
        :return:
        """
        # Depending on if we're looking for the MINIMUM or MAXIMUM distance, set the comparator and initial value
        if extrema_type == self.ExtremaType.MINIMUM:
            def comparator(x, y):
                return x > y
            init_extrema_value = sys.maxsize
        else:
            def comparator(x, y):
                return x < y
            init_extrema_value = 0

        # Now find the longest / shortest paths through the distance matrix
        sum_of_square_distances = 0
        locations_used = []
        for team in range(len(self.distance_matrix) // courses):
            # Find the first and second locations for these groups, with the shortest / longest distance
            distance_extrema = init_extrema_value
            current_location = -1
            last_location = -1
            for location1 in range(len(self.distance_matrix)):
                if not any(x == location1 for x in locations_used):
                    for location2 in range(len(self.distance_matrix)):
                        if location1 != location2 and not any(x == location2 for x in locations_used) \
                                and comparator(distance_extrema, self.distance_matrix[location1][location2]):
                            distance_extrema = self.distance_matrix[location1][location2]
                            current_location = location1
                            last_location = location2
            # Add first and second location to the list of traversed locations and add the squared distance
            locations_used.append(current_location)
            locations_used.append(last_location)
            sum_of_square_distances += distance_extrema ** 2
            # Now complete the rest of this path, adding the squared distance each time
            for course in range(courses - 2):
                current_location = last_location
                distance_extrema = init_extrema_value
                for location2 in range(len(self.distance_matrix)):
                    if current_location != location2 and not any(x == location2 for x in locations_used) \
                            and comparator(distance_extrema, self.distance_matrix[current_location][location2]):
                        distance_extrema = self.distance_matrix[current_location][location2]
                        last_location = location2
                locations_used.append(last_location)
                sum_of_square_distances += distance_extrema ** 2
        # We assume the number of courses is also the number of groups that travel together, so multiply it by this
        return courses * sum_of_square_distances

    def __init__(self, distance_matrix: [[float]], courses: int):
        """
        :param distance_matrix: An n x n matrix describing the distance from each location to each other location
        :param courses: Number of courses of this dinner
        """
        if len(distance_matrix) == 0:
            raise ValueError("Distance matrix may not be empty!")
        if len(distance_matrix) != len(distance_matrix[0]):
            raise ValueError("Distance matrix must be a square matrix!")
        self.distance_matrix = distance_matrix
        # Try to estimate the upper and lower bounds for squared distances that can occur in this distance matrix
        self.min_square_distance = self._find_distance_extremas(courses, self.ExtremaType.MINIMUM)
        self.max_square_distance = self._find_distance_extremas(courses, self.ExtremaType.MAXIMUM)

    def rate_solution(self, paths_per_host: {int: [int]}) -> float:
        """
        Rate a given solution and assign it a score between 0 and 1

        :param paths_per_host: The solution to rate
        :return: A score between 0 and 1
        """
        if len(self.distance_matrix) != len(paths_per_host):
            raise ValueError("Paths per host size does not match distance matrix dimension!")
        squared_distances = 0.0
        for (host, path) in paths_per_host.items():
            for i in range(1, len(path)):
                start_location = path[i - 1]
                end_location = path[i]
                squared_distances += self.distance_matrix[start_location][end_location] ** 2
        # Normalize this score to be between 0 and 1
        # Then subtract it from 1.0, so it gets better the shorter the squared distances
        return 1.0 - (squared_distances - self.min_square_distance) / (self.max_square_distance - self.min_square_distance)
