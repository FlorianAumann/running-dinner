import sys
from abc import abstractmethod
import random
from copy import deepcopy

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

    @abstractmethod
    def optimize(self, team_count: int, course_count: int) -> [float]:
        pass


class GeneticOptimizer(Optimizer):
    def __init__(self, initializer: Initializer, rater: SolutionRater):
        super().__init__(initializer, rater)

    def optimize(self, team_count: int, course_count: int) -> Solution:
        # First, create initial guess for genetic algorithm
        current_generation = self._create_initial_generation(team_count, course_count)

        # Then, iterate and mutate the guess to optimize the solution
        last_best_solution = current_generation[0].solution
        no_changes_since = 0
        for i in range(MAX_ITERATIONS):
            current_generation = self._create_new_generation(current_generation)
            # If there is no change in n rounds, break
            if last_best_solution == current_generation[0].solution:
                if no_changes_since >= ROUNDS_WITHOUT_CHANGE_TO_BREAK:
                    break
                else:
                    no_changes_since += 1
            else:
                no_changes_since = 0
            last_best_solution = current_generation[0].solution
        # Finally, return the best solution found in the optimization
        return current_generation[0].solution

    def _rate_solution(self, solution: Solution) -> float:
        paths_per_host = solution.get_paths_per_host()
        return self.rater.rate_solution(paths_per_host)

    @staticmethod
    def _mutate_solution(parent_solution: Solution) -> Solution:
        mutated_solution = deepcopy(parent_solution)
        courses = len(mutated_solution.groups_per_course)
        meal_group_count = len(mutated_solution.groups_per_course[0])

        mutate_dinner_hosts = (random.randint(0, 5) > 3)
        if mutate_dinner_hosts:
            course1 = random.randint(0, courses - 1)
            host1 = random.randint(0, meal_group_count - 1)
            course2 = random.randint(0, courses - 1)
            host2 = random.randint(0, meal_group_count - 1)
            while host1 == host2:
                host2 = random.randint(0, meal_group_count - 1)
            # Swap values
            temp = mutated_solution.groups_per_course[course1][host1].cooking_team
            mutated_solution.groups_per_course[course1][host1].cooking_team = \
                mutated_solution.groups_per_course[course2][host2].cooking_team
            mutated_solution.groups_per_course[course2][host2].cooking_team = temp
        else:
            mutations_num = random.randint(1, meal_group_count)
            for i in range(mutations_num):
                course = random.randint(0, courses - 1)
                host1 = random.randint(0, meal_group_count - 1)
                host2 = random.randint(0, meal_group_count - 1)
                index = random.randint(0, courses - 2)
                while host1 == host2:
                    host1 = random.randint(0, meal_group_count - 1)
                temp = mutated_solution.groups_per_course[course][host1].guest_indices[index]
                mutated_solution.groups_per_course[course][host1].guest_indices[index] = \
                    mutated_solution.groups_per_course[course][host2].guest_indices[index]
                mutated_solution.groups_per_course[course][host2].guest_indices[index] = temp
        return mutated_solution

    @staticmethod
    def _insert_into_generation_list(generation_list: [SolutionWithScore], item: Solution, rating: float) -> [
        SolutionWithScore]:
        i = 0
        current_rating = sys.maxsize
        while i < len(generation_list) and current_rating >= rating:
            current_rating = generation_list[i].score
            i += 1

        if i < len(generation_list):
            for j in range(i, len(generation_list)):
                if item == generation_list[j].solution:
                    return generation_list
            generation_list.insert(i - 1, SolutionWithScore(item, rating))
            generation_list.pop()

    def _create_new_generation(self, prev_gen: [SolutionWithScore]):
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
                self._insert_into_generation_list(new_gen, mutated_solution, score)

        return new_gen

    def _create_initial_generation(self, team_count: int, course_count: int) -> [SolutionWithScore]:
        initial_guess = self.initializer.create_initial_solution(team_count, course_count)

        # Create a number of instances of the initial SolutionWithScore, so we can have a base generation
        initial_rating = self._rate_solution(initial_guess)
        initial_generation = [SolutionWithScore(initial_guess, initial_rating) for i in
                              range(CANDIDATE_NUMBER_PER_GENERATION)]
        return initial_generation
