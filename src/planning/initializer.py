from abc import abstractmethod
import random

from src.planning.solution import Solution, DinnerGroup


class Initializer:
    """
    Abstract parent class for a solution initializer
    These classes are used to create an initial guess for a solution of the running dinner
    """
    @abstractmethod
    def create_initial_solution(self, team_count: int, course_count: int) -> Solution:
        """
        Creates an initial solution for the running dinner
        :param team_count: The total number of teams participating
        :param course_count: The number of courses of the running dinner
        :return: The initial solution
        """
        pass


class RandomInitializer(Initializer):
    """
    Initializes a solution at random
    """
    def create_initial_solution(self, team_count: int, course_count: int) -> Solution:
        # First, calculate number of parallel meal groups
        # each team has to host one course, so divide by number of courses
        meal_group_count = (team_count // course_count)
        # Create an initial vector
        random_indices = [i for i in range(team_count)]
        random.shuffle(random_indices)

        # Create initial solution guess
        groups_per_course = []
        host_index = 0
        for course in range(course_count):
            groups_per_course.append([])
            for meal_group in range(meal_group_count):
                guest_indices = [meal_group for i in range(course_count - 1)]
                groups_per_course[course].append(DinnerGroup(random_indices[host_index], guest_indices))
                host_index += 1
        return Solution(groups_per_course)


class FinalLocationInitializer(Initializer):
    """
    Initializes a solution where the cooking teams are already sorted by their distance to the final location
    The last course will be done by the teams closest to the final location, the first by the farthest teams
    This way, the solution will already satisfy the FinalLocationDistanceSolutionRater's score quite well
    """

    def __init__(self, dist_to_final_loc: [float]):
        """
        :param dist_to_final_loc: Distance vector for each team's location to the final location
        """
        self.dist_to_final_loc = dist_to_final_loc

    def create_initial_solution(self, team_count: int, course_count: int) -> Solution:
        if team_count != len(self.dist_to_final_loc):
            raise ValueError('Team count must match distance to final location vector!')
        # First, calculate number of parallel meal groups
        # each team has to host one course, so divide by number of courses
        meal_group_count = (team_count // course_count)
        # Create an initial vector
        unsorted_indices = [i for i in range(team_count)]
        # Sort indices by distances to final location in descending order
        sorted_indices = sorted(unsorted_indices, key=lambda i: -self.dist_to_final_loc[i])

        # Create initial solution guess
        groups_per_course = []
        host_index = 0
        for course in range(course_count):
            groups_per_course.append([])
            for meal_group in range(meal_group_count):
                guest_indices = [meal_group for i in range(course_count - 1)]
                groups_per_course[course].append(DinnerGroup(sorted_indices[host_index], guest_indices))
                host_index += 1
        return Solution(groups_per_course)
