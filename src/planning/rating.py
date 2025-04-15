import collections
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
        score = reduce(lambda x, y: x + y, map(lambda item: item[0] * item[1].rate_solution(paths_per_host), self.solution_raters))
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
                    intersections = collections.Counter(paths_per_host[team1]) & collections.Counter(paths_per_host[team2])
                    # If more than one intersection exists, add additional intersection to count
                    if len(intersections) > 1:
                        overlaps += (len(intersections) - 1)
        # Calculate the maximum overlaps possible for this solution size
        course_count = len(paths_per_host[0])
        teams_per_course_count = len(paths_per_host)
        maximum_overlaps = (course_count - 1) * (course_count - 1) * teams_per_course_count
        # Normalize this score to be between 0 and 1
        # Then subtract it from 1.0, so it gets better the less overlaps we have
        # In the end, square the result so bad solutions decrease the result exponentially, not linearly
        score = (1.0 - (overlaps / maximum_overlaps)) ** 2
        return score
