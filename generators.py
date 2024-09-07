import itertools
from typing import Optional

PRESENT_LIST = range(0, 0x1B)
PRESENT_WEIGHTS = [4, 5, 3, 4, 3, 4, 4, 3, 4, 4, 4, 1, 5, 4, 4, 4, 3, 1, 2, 2, 2, 1, 2, 2, 2, 2, 5]
BAD_PRESENT_INDICES = set([13, 16, 18, 23, 24])
LV1_FORBIDDEN_PRESENT_INDICES = set([0, 2, 5, 16, 18, 26])
assert(len(PRESENT_LIST) == len(PRESENT_WEIGHTS))

GOOD_FOOD_LIST = list(range(0x40, 0x4B))
BAD_FOOD_LIST = list(range(0x4B, 0x50))
A_BUCK = 0x50

# PADDING_LIST = [0x1A] + GOOD_FOOD_LIST + [A_BUCK]
# PADDING_WEIGHTS = [5] + [1]*len(GOOD_FOOD_LIST) + [5]
# assert(len(PADDING_LIST) == len(PADDING_WEIGHTS))

# With thanks to James Green for this precomputation

GAP_LISTS = [
[3,3,3,3,2,2,2,2,2,2],
[3,3,3,3,3,2,2,2,2,1],
[3,3,3,3,3,3,2,2,1,1],
[3,3,3,3,3,3,3,1,1,1],
[4,3,3,2,2,2,2,2,2,2],
[4,3,3,3,2,2,2,2,2,1],
[4,3,3,3,3,2,2,2,1,1],
[4,3,3,3,3,3,2,1,1,1],
[4,4,2,2,2,2,2,2,2,2],
[4,4,3,2,2,2,2,2,2,1],
[4,4,3,3,2,2,2,2,1,1],
[4,4,3,3,3,2,2,1,1,1],
[4,4,3,3,3,3,1,1,1,1],
[4,4,4,2,2,2,2,2,1,1],
[4,4,4,3,2,2,2,1,1,1],
[4,4,4,3,3,2,1,1,1,1],
[4,4,4,4,2,2,1,1,1,1],
[4,4,4,4,3,1,1,1,1,1],
]

# Used to make more evenly-spaced ship piece levels more likely
GAP_LIST_WEIGHTS = [5 - gaps.count(4) for gaps in GAP_LISTS]

class TJEGenerator():
    def __init__(self, world):
        self.random = world.random

    def get_present_distribution(self, level_one : bool = False, include_bad : bool = True) -> tuple[list[int], list[float]]:
        forbiddens = set()
        if level_one:
            forbiddens |= LV1_FORBIDDEN_PRESENT_INDICES
        if not include_bad:
            forbiddens |= BAD_PRESENT_INDICES

        culled_present_list = [PRESENT_LIST[i] for i in range(len(PRESENT_LIST)) if i not in forbiddens]
        culled_present_weights = [PRESENT_WEIGHTS[i] for i in range(len(PRESENT_WEIGHTS)) if i not in forbiddens]
        #assert(len(culled_present_list) == len(culled_present_weights))

        return culled_present_list, culled_present_weights

    # Not clear if this actually uniformly randomly chosen in the code
    def get_random_food(self, include_bad : bool = True) -> int:
        food_list = GOOD_FOOD_LIST+BAD_FOOD_LIST if include_bad else GOOD_FOOD_LIST
        return self.random.choices(food_list)[0]

    def get_random_present(self, level_one : bool = False, include_bad : bool = True) -> int:
        present_list, present_distro = self.get_present_distribution(level_one, include_bad)
        return self.random.choices(present_list, present_distro, k=1)[0]

    def get_random_item(self, level_one : bool = False, include_bad : bool = True) -> int:
        if level_one or self.random.random() < 0.5:
            return self.get_random_present(level_one, include_bad)
        else:
            if self.random.random() < 0.75:
                return self.get_random_food(include_bad)
            else:
                return A_BUCK

    # def generate_padding_items(self, number : int) -> list[int]:
    #     return self.random.choices(PADDING_LIST, weights=PADDING_WEIGHTS, k=number)

    def generate_items_for_level(self, level : int, singleplayer : bool = True) -> list[int]:
        if level <= 0: return []
        num_items = num_items_on_level(level, singleplayer=singleplayer)
        return [self.get_random_item(level_one=(level == 1)) for _ in range(num_items)]

    def generate_all_level_items(self, singleplayer : bool = True) -> list[list[int]]:
        return [self.generate_items_for_level(level, singleplayer=singleplayer) for level in range(0,26)]

    def generate_item_blob(self, number: int, include_bad: bool = True) -> list[int]:
        return [self.get_random_item(level_one=False, include_bad=include_bad) for _ in range(number)]

    def generate_initial_inventory(self, include_bad=False) -> list[int]:
        present_list, present_distro = self.get_present_distribution(level_one=False, include_bad=include_bad)
        return self.random.choices(present_list, present_distro, k=4)

    # This doesn't follow the code in the ROM at all, but produces extremely similar results
    def generate_ship_piece_levels(self) -> list[int]:
        gaps = self.random.choices(GAP_LISTS, GAP_LIST_WEIGHTS, k=1)[0]
        # This shuffle+flip guarantees that the first piece is on level 2 or 3
        self.random.shuffle(gaps[:-1])
        return list(itertools.accumulate(iterable=reversed(gaps), initial=1))[1:]


# Collectible items only; does not include trees
def num_items_on_level(level : int, singleplayer : bool = True) -> int:
    if level < 0:
        return 0
    if level < 2:
        return [0, 12][level]

    base = 12 if singleplayer else 16
    return min(28, base + level - 2)

def item_totals(singleplayer : bool = True) -> list[int]:
    return [num_items_on_level(level, singleplayer) for level in range(0,26)]

def num_trees_on_level(level : int) -> int:
    if level < 0:
        return 0
    if level < 2:
        return [3, 0][level]
    return 4

def get_key_levels(gap: int) -> Optional[list[int]]:
    match gap:
        case 0:
            return None
        case 1:
            return list(range(2,25))
        case _:
            return list(range(gap, 25, gap))

# How many points we reasonably expect to be able to get on each level from map exploration alone
# Values are tentative (lower than what's technically possible, just so logic is a bit nicer)
def expected_map_points_on_level(level : int) -> int:
    match level:
        case 0: return 0
        case 1: return 7
        case 2: return 14
        case 3: return 21
        case 4: return 35
        case _: return 42

# Half the items on a level are presents on average and they're worth 2 points each
# Assumes 3/4 of these presents are typically "easy" to collect
def expected_present_points_on_level(level : int) -> float:
    return 0.75*num_items_on_level(level)

def expected_point_totals(cumulative=False) -> list[float]:
    totals = [expected_map_points_on_level(level) + expected_present_points_on_level(level) for level in range(0,26)]
    if not cumulative:
        return totals
    return [round(n) for n in itertools.accumulate(iterable=totals)]

if __name__ == "__main__":
    print(item_totals(False))