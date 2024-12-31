import itertools

from .constants import MAP_REVEAL_DIALOGUE_TEMPLATE, MAP_REVEAL_DIALOGUE_TEMPLATE_DEGEN

#region Constants

PRESENT_LIST = range(0, 0x1B)
PRESENT_WEIGHTS = [4, 5, 3, 4, 3, 4, 4, 3, 4, 4, 4, 1, 5, 4, 4, 4, 3, 1, 2, 2, 2, 1, 2, 2, 2, 2, 5]
BAD_PRESENT_INDICES = set([13, 16, 18, 23, 24])
LV1_FORBIDDEN_PRESENT_INDICES = set([0, 2, 5, 16, 18, 26])
assert(len(PRESENT_LIST) == len(PRESENT_WEIGHTS))

FOOD_LIST = range(0x40, 0x50)
FOOD_WEIGHTS = [1]*len(FOOD_LIST)
BAD_FOOD_INDICES = set([11, 12, 13, 14, 15])
A_BUCK = 0x50

SHIP_PIECE_RANGES = (
    [(2, 3), (4, 5), (6, 7), (8, 9), (10, 11)], # max level 12
    [(2, 3), (4, 5), (6, 8), (9, 10), (11, 12)],
    [(2, 3), (4, 5), (6, 8), (9, 10), (11, 13)],
    [(2, 4), (5, 6), (7, 8), (9, 11), (12, 14)],
    [(2, 4), (5, 7), (8, 9), (10, 12), (13, 15)],
    [(2, 4), (5, 7), (8, 10), (11, 13), (14, 16)],
    [(2, 4), (5, 8), (9, 11), (12, 14), (15, 17)],
    [(2, 4), (5, 8), (9, 12), (13, 15), (16, 18)],
    [(2, 4), (5, 8), (9, 13), (14, 16), (17, 19)],
    [(2, 5), (6, 9), (10, 13), (14, 16), (17, 20)],
    [(2, 5), (6, 9), (10, 13), (14, 17), (18, 21)],
    [(2, 5), (6, 10), (11, 14), (15, 18), (19, 22)],
    [(2, 5), (6, 10), (11, 14), (15, 19), (20, 23)],
    [(2, 5), (6, 10), (11, 15), (16, 20), (21, 24)] # max level 25
)

#endregion

class TJEGenerator():
    def __init__(self, world):
        self.random = world.random
        self.global_banned_food = set()
        self.global_banned_presents = set()

    def forbid_item(self, item_code: int):
        if item_code in PRESENT_LIST:
            self.global_banned_presents.add(PRESENT_LIST.index(item_code))
        elif item_code in FOOD_LIST:
            self.global_banned_food.add(FOOD_LIST.index(item_code))

    def forbid_trap_presents(self):
        self.global_banned_presents |= BAD_PRESENT_INDICES

    def forbid_bad_food(self):
        self.global_banned_food |= BAD_FOOD_INDICES

    def fewer_upwarps(self):
        PRESENT_WEIGHTS[12] = 2

    def get_present_distribution(self, level_one: bool=False, include_bad: bool=True) -> tuple[list[int], list[float]]:
        forbiddens = set()
        forbiddens |= self.global_banned_presents
        if level_one:
            forbiddens |= LV1_FORBIDDEN_PRESENT_INDICES
        if not include_bad:
            forbiddens |= BAD_PRESENT_INDICES

        culled_present_list = [PRESENT_LIST[i] for i in range(len(PRESENT_LIST)) if i not in forbiddens]
        culled_present_weights = [PRESENT_WEIGHTS[i] for i in range(len(PRESENT_WEIGHTS)) if i not in forbiddens]
        #assert(len(culled_present_list) == len(culled_present_weights))

        return culled_present_list, culled_present_weights

    def get_food_distribution(self, include_bad: bool = True) -> tuple[list[int], list[float]]:
        forbiddens = set()
        forbiddens |= self.global_banned_food
        if not include_bad:
            forbiddens |= BAD_FOOD_INDICES

        culled_food_list = [FOOD_LIST[i] for i in range(len(FOOD_LIST)) if i not in forbiddens]
        culled_food_weights = [FOOD_WEIGHTS[i] for i in range(len(FOOD_WEIGHTS)) if i not in forbiddens]

        return culled_food_list, culled_food_weights

    # Not clear if this is actually uniformly randomly chosen in the code
    def get_random_food(self, include_bad: bool = True) -> int:
        food_list, food_distro = self.get_food_distribution(include_bad)
        return self.random.choices(food_list, food_distro, k=1)[0]

    def get_random_present(self, level_one: bool = False, include_bad: bool = True) -> int:
        present_list, present_distro = self.get_present_distribution(level_one, include_bad)
        return self.random.choices(present_list, present_distro, k=1)[0]

    # Follows the high-level logic of the game but does not use the same RNG function
    def get_random_item(self, level_one: bool = False, include_bad: bool = True) -> int:
        if level_one or self.random.random() < 0.5:
            return self.get_random_present(level_one, include_bad)
        if self.random.random() < 0.75:
            return self.get_random_food(include_bad)
        return A_BUCK

    # def generate_padding_items(self, number : int) -> list[int]:
    #     return self.random.choices(PADDING_LIST, weights=PADDING_WEIGHTS, k=number)

    def generate_items_for_level(self, level: int, singleplayer: bool = True) -> list[int]:
        if level <= 0:
            return []
        num_items = num_items_on_level(level, singleplayer=singleplayer)
        return [self.get_random_item(level_one=(level == 1)) for _ in range(num_items)]

    def generate_all_level_items(self, singleplayer: bool = True) -> list[list[int]]:
        return [self.generate_items_for_level(level, singleplayer=singleplayer) for level in range(0,26)]

    def generate_item_blob(self, number: int, include_bad: bool = True) -> list[int]:
        return [self.get_random_item(level_one=False, include_bad=include_bad) for _ in range(number)]

    def generate_initial_inventory(self, include_bad=False) -> list[int]:
        present_list, present_distro = self.get_present_distribution(level_one=False, include_bad=include_bad)
        return self.random.choices(present_list, present_distro, k=4)

    # Follows the same procedure as the ROM but has a slightly different distribution of results as
    # this version avoids all failure states and does not use the game's own RNG function
    def generate_ship_piece_levels(self, last_level: int = 25) -> list[int]:
        if last_level == 11:
            return list(range(2,12))
        ship_levels = [self.random.randint(i, j) for i, j in SHIP_PIECE_RANGES[last_level - 12]]
        ship_levels.extend(self.random.sample(sorted(set(range(2, last_level)) - set(ship_levels)), 5))
        ship_levels[self.random.randint(0, 9)] = last_level
        return sorted(ship_levels)

    def generate_map_reveal_potencies(self, last_level: int) -> list[int] | None:
        if last_level < 1:
            return None

        quot, rem = divmod(last_level, 5)
        if rem > 0:
            bump_indices = [0] + self.random.sample(range(1, 5), k=rem-1)
        else:
            bump_indices = []
        amounts = [quot]*5
        for i in bump_indices:
            amounts[i] += 1
        return amounts

# Collectible items only; does not include trees
def num_items_on_level(level: int, singleplayer: bool = True, min_items: int = 12, max_items: int = 28) -> int | None:
    if level < 0:
        return None
    if level == 0:
        return 0
    if level == 1:
        return min(min_items, 12)

    if min_items == 12: # Unchanged from base game
        base = 12 if singleplayer else 16
    else: # Overridden
        base = min_items

    return min(max_items, base + level - 2)

def item_totals(singleplayer: bool = True, min_items: int = 12, max_items: int = 28, last_level: int = 25) -> list[int]:
    return [num_items_on_level(level, singleplayer, min_items, max_items) for level in range(0, last_level+1)]

def num_trees_on_level(level: int) -> int:
    if level < 0:
        return 0
    if level < 2:
        return [3, 0][level]
    return 4

def get_key_levels(gap: int, last_level: int = 25) -> list[int] | None:
    match gap:
        case 0:
            return None
        case 1:
            return list(range(2, last_level))
        case _:
            return list(range(gap, last_level, gap))

# How many points we reasonably expect to be able to get on each level from map exploration alone
# Values are tentative (lower than what's technically possible, just so logic is a bit nicer)
def expected_map_points_on_level(level: int) -> int:
    match level:
        case 0: return 0
        case 1: return 7
        case 2: return 14
        case 3: return 21
        case 4: return 35
        case _: return 42

# Half the items on a level are presents on average and they're worth 2 points each
# Assumes 3/4 of these presents are typically "easy" to collect
def expected_present_points_on_level(level: int) -> float:
    return 0.75*num_items_on_level(level)

def expected_point_totals(cumulative=False) -> list[float]:
    totals = [expected_map_points_on_level(level) + expected_present_points_on_level(level) for level in range(0,26)]
    if not cumulative:
        return totals
    return [round(n) for n in itertools.accumulate(iterable=totals)]

def map_reveal_text(potencies: list[int]) -> list[str]:
    uppers = list(itertools.accumulate(potencies))
    lowers = [1]+[i+1 for i in uppers[:-1]]
    return [(MAP_REVEAL_DIALOGUE_TEMPLATE if l != u else MAP_REVEAL_DIALOGUE_TEMPLATE_DEGEN).format(l, u)
            for l, u in zip(lowers, uppers)]

# def sign(num):
#     return (num > 0) - (num < 0)

# def sborrow(x, y) -> bool:
#     return sign(x) != sign(y) and sign(x-y) != sign(x)

class TJEInternalRNG():
    rng_state = 0x3039

    def __init__(self):
        pass

    def test_rng(self):
        pregenned_random_sequence = [self.get_random_number() for _ in range(59)]
        assert(pregenned_random_sequence == [60975, 22016, 20672, 43896, 21923, 16663, 20572, 64074, 13996, 37431,
                                             35926, 30713, 35134, 22268, 61038, 47194, 9852, 44328, 8021, 5869,
                                             11416, 59367, 64619, 4347, 56933, 62965, 58690, 25646, 12631, 26719,
                                             16886, 47427, 62383, 42660, 38736, 16973, 53404, 61022, 38805, 52891,
                                             10512, 1809, 4962, 38620, 20783, 9754, 35105, 63580, 36504, 50392,
                                             24999, 13250, 11483, 62265, 21191, 36633, 54578, 51549, 7650])
        print("Pre-generated random sequence: OK")

    def get_random_number(self) -> int:
        rand_one = self.rng_state // 0x1F31D
        rand_two = self.rng_state % 0x1F31D
        rand_two = 0x41A7 * rand_two
        rand_one = 0xB14 * rand_one

        self.rng_state = rand_two - rand_one
        if self.rng_state == 0 or rand_two < rand_one:
            self.rng_state = self.rng_state + 0x7FFFFFFF

        return self.rng_state & 0xFFFF

    def set_random_seed(self, seed: int) -> int:
        temp = self.rng_state

        if seed < 0:
            seed = -seed
        if seed > 0x7FFFFFFE:
            seed = seed - 0x7FFFFFFF
        if seed == 0:
            seed = 1

        self.rng_state = seed
        return temp

    def is_mailbox_real(self, level_num: int, level_seed: int) -> bool | None:
        if level_num in [0, 1]:
            return None
        if level_num in [2, 3, 12]:
            return True
        self.set_random_seed(level_seed)
        return (self.get_random_number() & 0xFFFF) % 100 > 49

    def test_mailboxes(self):
        FIXED_SEEDS = [0x04d2, 0xddd5, 0x6c7e, 0x63e0, 0xdd51, 0x7bab, 0x8904, 0x9f55, 0x5ee2, 0x1a46, 0xb8ed, 0x7cf6,
                       0x4cb1, 0x8e32, 0xd846, 0xef9b, 0xb6a0, 0x2a33, 0x8767, 0x7f91, 0x11b7, 0x7802, 0x88ff, 0x295d,
                       0x24ca, 0xb9db]
        FIXED_MAILBOXES = [None, None, True, True, True, False, False, True, True, False, False, False, True,
                           True, False, True, True, False, False, True, True, False, False, True, True, False]

        assert([self.is_mailbox_real(i, seed) for i, seed in enumerate(FIXED_SEEDS)] == FIXED_MAILBOXES)
        print("Mailboxes: OK")
