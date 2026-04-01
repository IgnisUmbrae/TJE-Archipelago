import itertools
import re
import string
import functools
from collections import Counter
from math import ceil, sqrt, comb, pow, inf

from .constants import MAP_REVEAL_DIALOGUE_TEMPLATE, MAP_REVEAL_DIALOGUE_TEMPLATE_DEGEN, VANILLA_RANK_THRESHOLDS, \
                       EARTHLING_LIST, Earthling, LEVEL_TO_VANILLA_EARTHLINGS, PER_LEVEL_UNIQUE_EARTHLINGS, \
                       EARTHLING_MAX_PER_LEVEL, PER_LEVEL_EARTHLING_WEIGHTS, earthling_value, SHIP_PIECE_RANGES, \
                       PRESENT_LIST_BASE, PRESENT_WEIGHTS_BASE, A_BUCK, BAD_PRESENT_INDICES, LV1_FORBIDDEN_PRESENT_INDICES, \
                       FOOD_LIST, FOOD_WEIGHTS, BAD_FOOD_INDICES
from .options import TJEOptions

class TJEGenerator():
    def __init__(self, world):
        self.random = world.random
        self.global_banned_food = set()
        self.global_banned_presents = set()

        self.local_present_weights = PRESENT_WEIGHTS_BASE.copy()
        self.local_present_list = PRESENT_LIST_BASE.copy()

    def generate_full_random_earthlings(self):
        earthlings = []
        for _ in range(2,26):
            earthlings.append(self.random.choices(EARTHLING_LIST, (1,)*21, k=20))
        return earthlings

    def generate_nice_random_earthlings(self, niceness, last_level, mailbox_levels: list[int]):
        # Apply niceness to weights (in local copy)
        if niceness > 1:
            niced_weights = [[w**sqrt(niceness) for w in weights] for weights in PER_LEVEL_EARTHLING_WEIGHTS]
        else:
            niced_weights = PER_LEVEL_EARTHLING_WEIGHTS

        # Linearly rescale and trim the per-level Earthling weights if last_level < 25
        if last_level < 25:
            rescaled_levels = [round(((25-2)/(last_level-2))*(x-last_level)) + 25 for x in range(2, last_level+1)]
            niced_weights = [[0, 0] + [weights[i] for i in rescaled_levels] for weights in niced_weights]

        # Calculate budgets, factoring in mailbox monstrosity; min budget is 6 for at least some variety on level 2
        budgets = [
            max(sum(earthling_value(e) for e in earthlings) - (0 if level in mailbox_levels else earthling_value(Earthling.MAILBOX)), 6)
                for level, earthlings in enumerate(LEVEL_TO_VANILLA_EARTHLINGS)
        ]

        # Get new maximum numbers of Santas and other friendly Earthlings based on the world size
        santa_base = 6*last_level/25
        santa_lims = (round(0.95*santa_base), round(1.3*santa_base))
        other_base = 7*last_level/25
        other_lims = (round(0.95*other_base), round(1.3*other_base))

        global_earthling_limits = {
            Earthling.WIZARD: self.random.randint(*other_lims),
            Earthling.WISEMAN: self.random.randint(*other_lims),
            Earthling.OPERA: self.random.randint(*other_lims),
            Earthling.SANTA: self.random.randint(*santa_lims),
        }

        earthling_running_count = Counter()
        levels = list(range(2, last_level+1))
        self.random.shuffle(levels)
        out = [[]]*24
        for level in levels:
            earthlings = []
            level_weights_base = [weights[level] for weights in PER_LEVEL_EARTHLING_WEIGHTS]
            while budgets[level] > 0 and len(earthlings) < EARTHLING_MAX_PER_LEVEL[level]:
                # Remove weights for any earthling that's out of budget or already at max count, and normalize
                level_weights = [w if earthling_value(e) <= budgets[level]
                                 and earthling_running_count[e] < global_earthling_limits.get(e, inf)
                                 and not (e in earthlings and e in PER_LEVEL_UNIQUE_EARTHLINGS)
                                 else 0
                                for e, w in zip(EARTHLING_LIST, level_weights_base)]    
                level_weights = [w/sum(level_weights) for w in level_weights]

                earthling = self.random.choices(EARTHLING_LIST, level_weights, k=1)[0]
                earthlings.append(earthling)
                budgets[level] -= earthling_value(earthling)
                if earthling in global_earthling_limits:
                    earthling_running_count[earthling] += 1

            # Only returning 24 levels' worth of data, so first index is 0 but corresponds to level 2
            out[level-2] = earthlings
        return out

    def forbid_item(self, item_code: int):
        if item_code in self.local_present_list:
            self.global_banned_presents.add(self.local_present_list.index(item_code))
        elif item_code in FOOD_LIST:
            self.global_banned_food.add(FOOD_LIST.index(item_code))

    def forbid_bad_presents(self):
        self.global_banned_presents |= BAD_PRESENT_INDICES

    def forbid_bad_food(self):
        self.global_banned_food |= BAD_FOOD_INDICES

    def fewer_upwarps(self):
        self.local_present_weights[0xC] = 2
    
    def enable_point_presents(self):
        self.local_present_weights[0xB] = 0.5
        self.local_present_list.append(0x1C)
        self.local_present_weights.append(1)

    def get_present_distribution(self, level_one: bool=False, force_good: bool=False) -> tuple[list[int], list[float]]:
        forbiddens = set()
        forbiddens |= self.global_banned_presents
        if level_one:
            forbiddens |= LV1_FORBIDDEN_PRESENT_INDICES
        if force_good:
            forbiddens |= BAD_PRESENT_INDICES

        culled_present_list = [self.local_present_list[i] for i in range(len(self.local_present_list)) if i not in forbiddens]
        culled_present_weights = [self.local_present_weights[i] for i in range(len(self.local_present_weights)) if i not in forbiddens]

        return culled_present_list, culled_present_weights

    def get_food_distribution(self) -> tuple[list[int], list[float]]:
        forbiddens = set()
        forbiddens |= self.global_banned_food

        culled_food_list = [FOOD_LIST[i] for i in range(len(FOOD_LIST)) if i not in forbiddens]
        culled_food_weights = [FOOD_WEIGHTS[i] for i in range(len(FOOD_WEIGHTS)) if i not in forbiddens]

        return culled_food_list, culled_food_weights

    # Not clear if this is actually uniformly randomly chosen in the code
    def get_random_food(self) -> int:
        food_list, food_distro = self.get_food_distribution()
        return self.random.choices(food_list, food_distro, k=1)[0]

    def get_random_present(self, level_one: bool = False) -> int:
        present_list, present_distro = self.get_present_distribution(level_one)
        return self.random.choices(present_list, present_distro, k=1)[0]

    # Follows the high-level logic of the game but does not use the same RNG function
    def get_random_item(self, level_one: bool = False, presentsanity: bool = False) -> int:
        if level_one or self.random.random() < 0.5:
            if not presentsanity:
                return self.get_random_present(level_one)
            return 0x1A # Mystery Present
        if self.random.random() < 0.75:
            return self.get_random_food()
        return A_BUCK

    def generate_item_blob(self, number: int, presentsanity: bool = False) -> list[int]:
        return [self.get_random_item(False, presentsanity) for _ in range(number)]

    def total_points_in_pool(self, item_pool: list[int], promotion_value: int, point_present_value: int) -> int:
        def item_value(item_code: int, prom_val: int, point_pres_val: int) -> int:
            if item_code == 0x0B:
                return prom_val
            if item_code == 0x1C:
                return point_pres_val
            if item_code in self.local_present_list:
                return 2
            return 0
        
        return sum([item_value(i, promotion_value, point_present_value) for i in item_pool])

    def add_extra_promotions(self, item_pool: list[int], rank_thresholds: list[int], promotion_value: int,
                             point_present_value: int, options: "TJEOptions") -> None:
        points_available = self.total_points_in_pool(item_pool, promotion_value, point_present_value) + \
                           expected_map_points(options.last_level.value)
        points_goal = rank_thresholds[options.max_rank_check.value]
        if points_available < points_goal:
            deficit = points_goal - points_available
            if not options.point_presents:
                extra_proms = ceil(deficit/promotion_value)
                extra_pp = 0
            else: # add a balance between the two in roughly a 1:2 ratio
                pivot = deficit/(promotion_value + 2*point_present_value)
                extra_proms = round(pivot)
                # Due to rounding, this may be slightly below what we need, so we make up the difference afterwards
                extra_pp = round(2*pivot)
                extra_pp += ceil((deficit - (extra_pp*point_present_value + extra_proms*promotion_value))/point_present_value)
            do_not_overwrite = (0x0B, 0x1C) if options.point_presents else (0x0B,)
            if extra_proms > 0:
                for n, item in enumerate(item_pool):
                    if item not in do_not_overwrite:
                        item_pool[n] = 0x0B
                        extra_proms -= 1
                    if extra_proms == 0:
                        break
            if extra_pp > 0:
                for n, item in enumerate(item_pool):
                    if item not in do_not_overwrite:
                        item_pool[n] = 0x1C
                        extra_pp -= 1
                    if extra_pp == 0:
                        break

    def generate_initial_inventory(self, force_good: bool) -> list[int]:
        present_list, present_distro = self.get_present_distribution(False, force_good)
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

        # Distribute as evenly as possible to begin with, then randomly 'bump' some of them
        quot, rem = divmod(last_level, 5)
        amounts = [quot]*5
        if rem > 0:
            bump_indices = [0] + self.random.sample(range(1, 5), k=rem-1)
        else:
            bump_indices = []

        for i in bump_indices:
            amounts[i] += 1
        return amounts

    def generate_item_prices(self, num_mailboxes: int, total_bucks: int) -> list[int]:
        num_items = 3*num_mailboxes
        max_price = round(2*total_bucks/num_items)
        # assume 10% of bucks will be "misspent"
        budget = total_bucks - round(10/100*total_bucks)
        binom_weights = [comb(max_price, i) * pow(0.5, max_price) for i in range(0,max_price+1)]

        prices = []
        while budget > 0 and len(prices) < num_items:
            price = self.random.choices(range(0,max_price+1), binom_weights, k=1)[0]
            budget = max(budget - price, 0)
            prices.append(price)
        prices += [0]*(num_items - len(prices))
        self.random.shuffle(prices)

        return prices

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
        case 0: return 2 # for drinking the lemonade, since it opens a fake Extra Life present
        case 1: return 5
        case 2: return 10
        case 3: return 20
        case 4: return 30
        case 5: return 35
        case _: return 35

def expected_map_points(last_level: int) -> int:
    return sum(expected_map_points_on_level(i) for i in range(last_level+1))

# Half the items on a level are presents on average and they're worth 2 points each
def expected_present_points_on_level(level: int, min_items: int = 12, max_items: int = 28) -> int:
    return num_items_on_level(level, min_items, max_items)

def expected_points_on_level(level: int, min_items: int = 12, max_items: int = 28) -> int:
    return expected_map_points_on_level(level) + expected_present_points_on_level(level, min_items, max_items)

def expected_point_totals(last_level: int, min_items: int = 12, max_items: int = 28, cumulative = False) -> list[int]:
    totals = [expected_points_on_level(level, min_items, max_items) for level in range(0,last_level+1)]
    if not cumulative:
        return totals
    return [round(n) for n in itertools.accumulate(iterable=totals)]

def map_reveal_ranges(potencies: list[int]) -> list[tuple[int, int]]:
    uppers = list(itertools.accumulate(potencies))
    lowers = [1]+[i+1 for i in uppers[:-1]]
    return zip(lowers, uppers)

def map_reveal_text(potencies: list[int]) -> list[str]:
    return [(MAP_REVEAL_DIALOGUE_TEMPLATE if l != u else MAP_REVEAL_DIALOGUE_TEMPLATE_DEGEN).format(l, u)
            for l, u in map_reveal_ranges(potencies)]

def get_rank_rescale_factor(last_level: int = 25, min_items: int = 12, max_items: int = 28,
                            desired_max_rank: int = 8) -> float:
    full_game_estimate = expected_point_totals(last_level=25, min_items=12, max_items=28, cumulative=True)[-1]
    reduced_game_estimate = expected_point_totals(last_level, min_items, max_items, cumulative=True)[-1]
    factor_1 = reduced_game_estimate/full_game_estimate
    factor_2 = VANILLA_RANK_THRESHOLDS[8]/VANILLA_RANK_THRESHOLDS[desired_max_rank]
    return factor_1 * factor_2

def rescale_to_nearest_mult(num: int, mult: int, rescale_factor: float = 1, bump: float = 0) -> int:
    return round((rescale_factor*num + bump)/mult)*mult

@functools.cache
def total_points_to_next_rank(current_rank: int, last_level: int = 25, min_items: int = 12, max_items: int = 28,
                              desired_max_rank: int = 8) -> int:
    reqd = 0
    if current_rank > 7:
        return 0
    for rank in range(current_rank+1):
        reqd += 40 + 20*rank

    if last_level == 25 and min_items == 12 and max_items == 28 and desired_max_rank == 8:
        return reqd

    rescale_factor = get_rank_rescale_factor(last_level, min_items, max_items, desired_max_rank)
    # "Bump" is a small boost to early rank thresholds that's greatest for short games with few items.
    # It ensures that such games don't have comically low rank thresholds at the start, and that the rank
    # progression is smoother overall. Affects large games minimally; does not affect vanilla games whatsoever.
    bump = (25 - last_level)/(25 - 11) * (28 - max_items)/(28 - 4) * (8 - current_rank)/(8 - 0) * 10
    return rescale_to_nearest_mult(reqd, 10, rescale_factor, bump)

@functools.cache
def scaled_rank_thresholds(last_level: int = 25, min_items: int = 12, max_items: int = 28,
                           desired_max_rank: int = 8) -> list[int]:
    return [0] + \
           [total_points_to_next_rank(rank, last_level, min_items, max_items, desired_max_rank) for rank in range(8)]

# Average gap between ranks, halved to represent 'average' use
def get_average_promotion_value(rank_thresholds: list[int], max_rank_check: int) -> int:
    return max(round(rank_thresholds[max_rank_check]/max_rank_check/2), 10)

# Determines a sensible point value for a flat promotion present
def get_point_present_value(rank_thresholds: list[int], max_rank_check: int) -> int:
    breakpoints = (5, 10, 15, 25, 50, 75, 100, 150, 200)
    apv = get_average_promotion_value(rank_thresholds, max_rank_check)/2
    dists = [abs(b - apv) for b in breakpoints]
    nearest_idx = min(range(len(breakpoints)), key=dists.__getitem__)
    return breakpoints[nearest_idx]

class TJEInternalRNG():
    def __init__(self):
        self.rng_state = 0x3039

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

    def generate_mailboxes(self, seeds: list[int], last_level: int = 25) -> list[bool | None]:
        return [i for (i, seed) in enumerate(seeds) if i <= last_level and self.is_mailbox_real(i, seed)]

    def test_mailboxes(self):
        FIXED_SEEDS = [0x04d2, 0xddd5, 0x6c7e, 0x63e0, 0xdd51, 0x7bab, 0x8904, 0x9f55, 0x5ee2, 0x1a46, 0xb8ed, 0x7cf6,
                       0x4cb1, 0x8e32, 0xd846, 0xef9b, 0xb6a0, 0x2a33, 0x8767, 0x7f91, 0x11b7, 0x7802, 0x88ff, 0x295d,
                       0x24ca, 0xb9db]
        FIXED_MAILBOXES = [None, None, True, True, True, False, False, True, True, False, False, False, True,
                           True, False, True, True, False, False, True, True, False, False, True, True, False]

        assert([self.is_mailbox_real(i, seed) for i, seed in enumerate(FIXED_SEEDS)] == FIXED_MAILBOXES)
        print("Mailboxes: OK")

def to_inventory_name(name: str) -> list[int]:
    chunker = re.compile(r"(oi|apm|ord|ste|unk|dexte|[0-9A-Za-z.,'\-! ])")
    multialphas = ("apm","ord","ste","unk","dexte")
    trans_dict = {
        "oi" : 0x2E,                    # 0x1 in rank name table
        "dexte" : (0x2F, 0x30, 0x31),   # 0x2
        "apm" : (0x32, 0x33),           # 0x3
        "ste" : (0x34, 0x35),           # 0x4
        "unk" : (0x36, 0x37, 0x38),     # 0x5
        "ord" : (0x39, 0x3A),           # 0x6
        " " : 0x0,
        "." : 0x1F,
        "," : 0x20,
        "'" : 0x21,
        "-" : 0x22,
        "!" : 0x23,
    }
    chunks, codes = chunker.findall(name.lower()), []
    for c in chunks:
        if c in multialphas:
            codes.extend(trans_dict[c])
        else:
            match c:
                case c if c in string.ascii_lowercase:
                    code = ord(c) - 96
                case c if c in string.digits:
                    code = ord(c) - 12
                case _:
                    code = trans_dict.get(c, 0x1B) # 0x1B renders as "?"
            codes.append(code)

    return codes + [0]*(14 - len(codes))

def to_mailbox_name(name: str) -> str:
    return (name[:12] + " ").ljust(13, ".")