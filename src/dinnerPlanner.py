from src.data.dinnerTeam import DinnerTeam
from enum import Enum

from src.googleapi.googleApi import GoogleApi
from src.planning.initializer import FinalLocationInitializer, RandomInitializer
from src.planning.optimizer import GeneticOptimizer
from src.planning.rating import FinalLocationDistanceSolutionRater, DiversitySolutionRater, InterDistanceSolutionRater, \
    CombinedSolutionRater


class RaterType(Enum):
    DIVERSITY = 1
    WALKING_DIST = 2
    WALKING_DIST_FINAL = 3


class DinnerPlanner(object):
    def __init__(self, google_api: GoogleApi):
        self.google_api = google_api

    def plan_dinner(self, dinner_teams: [DinnerTeam], weighted_rater_types: [(float, RaterType)], courses: int,
                    final_location: str = None):
        if not len(dinner_teams):
            raise ValueError("Dinner team list may not be empty!")
        if not len(weighted_rater_types):
            raise ValueError("At least one rater needs to be defined!")

        raters = []
        teams_per_course = len(dinner_teams) // courses
        initializer = None

        # Check if we use a diversity as optimization criteria
        diversity_rater_type = next((wrt for wrt in weighted_rater_types if wrt[1] == RaterType.DIVERSITY), None)
        if diversity_rater_type:
            diversity_rater = DiversitySolutionRater()
            raters.append((diversity_rater_type[0], diversity_rater))

        # Check if we use distance as optimization criteria
        dist_rater_type = next((wrt for wrt in weighted_rater_types if wrt[1] == RaterType.WALKING_DIST), None)
        if dist_rater_type:
            dist_matrix = []
            for dinner_team1 in dinner_teams:
                dist_matrix_row = []
                if not dinner_team1.address:
                    raise ValueError("Dinner team location missing!")
                for dinner_team2 in dinner_teams:
                    if not dinner_team2.address:
                        raise ValueError("Dinner team location missing!")
                    if dinner_team1.address == dinner_team2.address:
                        dist_matrix_row.append(0)
                    else:
                        distance = self.google_api.get_walking_duration(dinner_team1.address, dinner_team2.address)
                        dist_matrix_row.append(distance)
                dist_matrix.append(dist_matrix_row)
            distance_rater = InterDistanceSolutionRater(dist_matrix, courses)
            raters.append((dist_rater_type[0], distance_rater))

        # Check if we use a final location as optimization criteria
        final_dist_rater_type = next((wrt for wrt in weighted_rater_types if wrt[1] == RaterType.WALKING_DIST_FINAL), None)
        if final_dist_rater_type:
            # If yes, the final location address has to be provided
            if not final_location:
                raise ValueError("Final location missing!")
            # Retrieve walking times from all dinner team locations to final location
            dist_to_final_location = []
            for dinner_team in dinner_teams:
                if not dinner_team.address:
                    raise ValueError("Dinner team location missing!")
                distance = self.google_api.get_walking_duration(dinner_team.address, final_location)
                dist_to_final_location.append(distance)
            final_dist_rater = FinalLocationDistanceSolutionRater(dist_to_final_location, teams_per_course)
            raters.append((final_dist_rater_type[0], final_dist_rater))
            # Also set the initializer to a final location initializer to get a better initial solution
            initializer = FinalLocationInitializer(dist_to_final_location)

        # If initializer is not set at this point, use a Random initializer
        if initializer is None:
            initializer = RandomInitializer()

        if len(raters) > 0:
            # If we have more than one rater, combine them all using their respective weights
            rater = CombinedSolutionRater(raters)
        elif len(raters) == 0:
            # If we have only one, use this one directly, ignoring its weight
            rater = raters[0][1]
        else:
            raise ValueError("No valid rating criterion provided")

        # Now set up and start the actual optimization
        optimizer = GeneticOptimizer(initializer, rater)
        solution = optimizer.optimize(len(dinner_teams), courses)
        return solution.get_paths_per_host()

