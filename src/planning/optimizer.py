import sys
import logging
from abc import abstractmethod
import random
from copy import deepcopy

from src import log
from src.planning.initializer import Initializer
from src.planning.rating import SolutionRater
from src.planning.solution import Solution, SolutionWithScore

COURSE_COUNT = 3
ROUNDS_WITHOUT_CHANGE_TO_BREAK = 3
MUTATIONS_PER_SOLUTION = 5
MAX_ITERATIONS = 50
CANDIDATE_NUMBER_PER_GENERATION = 30


class Optimizer:
    """
    Parent class for all optimizers, use the optimize method to find the best solution given the criterion defined
    by the SolutionRater.
    """
    def __init__(self, initializer: Initializer, rater: SolutionRater):
        self.initializer = initializer
        self.rater = rater
        self.logger = log.setup_logger(__name__)

    @abstractmethod
    def optimize(self, team_count: int, course_count: int) -> [float]:
        pass


class GeneticOptimizer(Optimizer):
    """
    An optimizer using genetic optimization to find an optimal dinner configuration
    """
    def __init__(self, initializer: Initializer, rater: SolutionRater):
        """
        :param initializer: The initializer class to for the first solution generation
        :param rater: The rater class to calculate solution scores to optimize
        """
        super().__init__(initializer, rater)

    def optimize(self, team_count: int, course_count: int) -> Solution:
        """
        Find an optimal solution for the dinner configuration
        :param team_count: The total number of teams participating
        :param course_count: The number of dinner courses
        :return: The optimal solution after optimization
        """
        self.logger.info(f"Started optimization for {course_count} course(s) with {team_count} teams")
        # First, create initial guess for genetic algorithm
        current_generation = self._create_initial_generation(team_count, course_count)

        # Then, iterate and mutate the guess to optimize the solution
        last_best_solution = current_generation[0].solution
        no_changes_since = 0
        for iteration in range(MAX_ITERATIONS):
            current_generation = self._create_new_generation(current_generation)
            # If there is no change in n rounds, break
            if last_best_solution == current_generation[0].solution:
                if no_changes_since >= ROUNDS_WITHOUT_CHANGE_TO_BREAK:
                    self.logger.debug(f"No new solutions in {ROUNDS_WITHOUT_CHANGE_TO_BREAK} iteration(s). Exiting...")
                    break
                else:
                    no_changes_since += 1
            else:
                no_changes_since = 0
            last_best_solution = current_generation[0].solution
        self.logger.info(f"Found solution with score {current_generation[0].score} in {iteration} iteration(s)")
        # Finally, return the best solution found in the optimization
        return current_generation[0].solution

    def _rate_solution(self, solution: Solution) -> float:
        """
        Calculate a score between 0 and 1 of a given solution, using the rater member
        :param solution: The solution to rate
        :return: The score of the solution
        """
        paths_per_host = solution.get_paths_per_host()
        return self.rater.rate_solution(paths_per_host)

    @staticmethod
    def _mutate_solution(parent_solution: Solution) -> Solution:
        """
        For a given parent solution, create a random mutation of this solution and return it
        :param parent_solution: The existing solution to mutate
        :return: The mutated solution
        """
        # Deepcopy the parent solution
        mutated_solution = deepcopy(parent_solution)
        courses = len(mutated_solution.groups_per_course)
        meal_group_count = len(mutated_solution.groups_per_course[0])

        # Swap dinner hosts with a change of 1/3
        mutate_dinner_hosts = (random.randint(0, 2) > 1)
        if mutate_dinner_hosts:
            # Mutation 1: Swap dinner hosts (33% chance)
            # Pick a random course and host to swap with another course and host
            course1 = random.randint(0, courses - 1)
            host1 = random.randint(0, meal_group_count - 1)
            course2 = random.randint(0, courses - 1)
            host2 = random.randint(0, meal_group_count - 1)
            # Make sure we don't swap a dinner host with itself
            while host1 == host2 and course1 == course2:
                course2 = random.randint(0, courses - 1)
                host2 = random.randint(0, meal_group_count - 1)
            # Actually swap values
            temp = mutated_solution.groups_per_course[course1][host1].cooking_team
            mutated_solution.groups_per_course[course1][host1].cooking_team = \
                mutated_solution.groups_per_course[course2][host2].cooking_team
            mutated_solution.groups_per_course[course2][host2].cooking_team = temp
        else:
            # Mutation 2: Swap guest indices (66% chance)
            # Pick a random number of guest index mutations
            mutations_num = random.randint(1, meal_group_count)
            for i in range(mutations_num):
                # Pick a random guest to swap with another guest
                course = random.randint(0, courses - 1)
                guest1 = random.randint(0, meal_group_count - 1)
                guest2 = random.randint(0, meal_group_count - 1)
                index = random.randint(0, courses - 2)
                # Make sure we don't swap a dinner guest with itself
                while guest1 == guest2:
                    guest1 = random.randint(0, meal_group_count - 1)
                # Actually swap values
                temp = mutated_solution.groups_per_course[course][guest1].guest_indices[index]
                mutated_solution.groups_per_course[course][guest1].guest_indices[index] = \
                    mutated_solution.groups_per_course[course][guest2].guest_indices[index]
                mutated_solution.groups_per_course[course][guest2].guest_indices[index] = temp
        return mutated_solution

    @staticmethod
    def _insert_into_generation_list(generation_list: [SolutionWithScore], solution: SolutionWithScore) -> bool:
        """
        Will insert a solution into an existing generation if its score is better than any of the existing ones
        :param generation_list: The existing generation list, will be modified
        :param solution: The solution with score to insert
        :return: Returns true if the solution was inserted, false otherwise
        """
        # Find the next solution with a lower score than the new one
        i = 0
        current_score = sys.maxsize
        while i < len(generation_list) and current_score >= solution.score:
            current_score = generation_list[i].score
            i += 1

        # If this exact solution exists already in here, don't insert it
        if i > 0 and solution.solution == generation_list[i-1].solution:
            return False

        # If the solution has a better score than any of the existing solutions, insert it
        if i < len(generation_list):
            generation_list.insert(i - 1, solution)
            # Pop the last solution
            generation_list.pop()
            return True
        return False

    def _create_new_generation(self, prev_gen: [SolutionWithScore]) -> [SolutionWithScore]:
        """
        Given an existing generation, mutate the existing solutions to arrive at a new generation
        :param prev_gen: The previous generation
        :return: The new generation
        """
        new_gen = deepcopy(prev_gen)
        # Mutate each solution from the previous generation n times and sort it into the new generation
        # If it gets a better score than any of the existing solution, it will be inserted into the solution list
        for solution in prev_gen:
            for j in range(MUTATIONS_PER_SOLUTION):
                # Create a random mutation of our solution
                mutated_solution = self._mutate_solution(solution.solution)
                # Rate the new solution
                score = self._rate_solution(mutated_solution)
                # Insert into solution list (if score is better than existing one)
                self._insert_into_generation_list(new_gen, SolutionWithScore(mutated_solution, score))

        return new_gen

    def _create_initial_generation(self, team_count: int, course_count: int) -> [SolutionWithScore]:
        """
        Create the initial generation for the optimization
        :param team_count: The total number of teams participating
        :param course_count: The number of dinner courses
        :return: The initial solution generation
        """
        initial_guess = self.initializer.create_initial_solution(team_count, course_count)

        # Create a number of instances of the initial SolutionWithScore, so we can have a base generation
        initial_rating = self._rate_solution(initial_guess)
        initial_generation = [SolutionWithScore(initial_guess, initial_rating) for i in
                              range(CANDIDATE_NUMBER_PER_GENERATION)]
        self.logger.debug(f"Created {CANDIDATE_NUMBER_PER_GENERATION} initial solutions with rating {initial_rating}")
        return initial_generation
