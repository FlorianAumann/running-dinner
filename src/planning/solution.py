from copy import deepcopy

from numpy import array_equal


class DinnerGroup(object):
    def __init__(self, cooking_team: int, guest_indices: [int]):
        """
        Represents a single dinner group that will cook and eat together
        A dinner group contains the number of the dinner team in charge of cooking as well as an index list
        of guests that join the cooking team for this course. The indices in this list refer to the list for the other
        courses, where the actual team number can be found

        :param cooking_team: Number of the cooking team in this dinner group
        :param guest_indices: List of indices of the joining guest teams in this group. Refers to the cooking_team
                              indices in the other course of a Solution
        """
        self.cooking_team = cooking_team
        self.guest_indices = guest_indices

    def __eq__(self, other):
        return (self.cooking_team == other.cooking_team) and array_equal(self.groups_per_course, other.groups_per_course)

    def __copy__(self):
        return type(self)(self.cooking_team, self.guest_indices)

    def __deepcopy__(self, memo):
        id_self = id(self)
        _copy = memo.get(id_self)
        if _copy is None:
            _copy = type(self)(self.cooking_team, deepcopy(self.guest_indices, memo))
            memo[id_self] = _copy
        return _copy


class Solution(object):
    def __init__(self, groups_per_course: [[DinnerGroup]]):
        """
        Represents a single solution for the dinner scheduling.
        For each course, defines a list of dinner groups that will cook and eat together
        Each dinner group contains the number of the dinner team in charge of cooking as well as an index list
        of guests that join the cooking team for this course. The indices in this list refer to the list for the other
        courses, where the actual team number can be found

        The representation of a solution is kept in a way where the solution can be changed via simple permutation of
        indices and will always still stay a valid solution, allowing for easy mutation of a solution to arrive at new
        versions of it for our genetic algorithm.

        :param groups_per_course: For each course, defines the dinner groups which will cook and eat together
                                  Dimensions: courses x group
        """
        self.groups_per_course = groups_per_course
        courses = len(groups_per_course)
        if not courses:
            raise TypeError("groups_per_course may not be empty!")
        # Sanity check groups_per_course dimensions
        for course_idx in range(len(groups_per_course)):
            for host_idx in range(len(groups_per_course[course_idx])):
                if len(groups_per_course[course_idx][host_idx].guest_indices) != (courses - 1):
                    raise TypeError("Guest index list must be number of courses minus one!")

    def get_paths_per_host(self) -> {int: [int]}:
        """
        From the internal representation of the solution, create a readable representation of dinner paths per host
        A dinner path consists of a list of host numbers that describe where a team will eat for each course

        :return Returns a map that contains the dinner paths for each host :
        """
        paths_per_host = {}
        # For the cooking hosts in the first course group, we just use the indices the following courses to get their path
        for group_idx in range(len(self.groups_per_course[0])):
            paths_per_host[self.groups_per_course[0][group_idx].cooking_team] = [self.groups_per_course[0][group_idx].cooking_team]
            for course_idx in range(1, len(self.groups_per_course)):
                paths_per_host[self.groups_per_course[0][group_idx].cooking_team].append(self.groups_per_course[course_idx][group_idx].cooking_team)

        # Iterate over all remaining courses and all groups in each course
        for active_course_idx in range(1, len(self.groups_per_course)):
            for group_idx in range(len(self.groups_per_course[active_course_idx])):
                # For each of the cooking hosts in there, create a new empty list
                host = self.groups_per_course[active_course_idx][group_idx].cooking_team
                paths_per_host[host] = []
                # Now iterate over all courses again to fill the path list for the current host
                for course_idx in range(len(self.groups_per_course)):
                    if course_idx == active_course_idx:
                        # In case the current course is also the active course index, the current team will be the one cooking
                        # -> Simply add its own index to the list
                        paths_per_host[host].append(host)
                    else:
                        # Look up the host_index under where to find the actual guest number in the other courses
                        # Since the current course is not part of the groups_per_course list, we need to decrement
                        # all indices above the current one by one
                        if active_course_idx < course_idx:
                            guest_course_idx = active_course_idx
                        else:
                            guest_course_idx = active_course_idx - 1
                        host_index = self.groups_per_course[course_idx][group_idx].guest_indices[guest_course_idx]
                        # Using this host index, look up which cooking team the current host will join for this course
                        paths_per_host[host].append(self.groups_per_course[course_idx][host_index].cooking_team)
        return paths_per_host

    def __eq__(self, other):
        return array_equal(self.groups_per_course, other.groups_per_course)

    def __copy__(self):
        return type(self)(self.groups_per_course)

    def __deepcopy__(self, memo):
        id_self = id(self)
        _copy = memo.get(id_self)
        if _copy is None:
            _copy = type(self)(
                deepcopy(self.groups_per_course, memo))
            memo[id_self] = _copy
        return _copy


class SolutionWithScore(object):
    def __init__(self, solution: Solution, score: float):
        """ A single solution with its assigned score value

        :param solution: The solution itself
        :param score: The score of this solution
        """
        self.solution = solution
        self.score = score
