import itertools
import re
import string
from collections import defaultdict, Counter
from math import ceil, sqrt, comb, pow

from .constants import MAP_REVEAL_DIALOGUE_TEMPLATE, MAP_REVEAL_DIALOGUE_TEMPLATE_DEGEN, VANILLA_RANK_THRESHOLDS, \
                       EARTHLING_LIST, BASE_EARTHLINGS, EARTHLING_UNIQUE, EARTHLING_WEIGHTS, EARTHLING_MAX_PER_LEVEL, \
                       EARTHLING_WEIGHTS_PER_LEVEL, SHIP_PIECE_RANGES, PRESENT_LIST, PRESENT_WEIGHTS, A_BUCK, \
                       BAD_PRESENT_INDICES, LV1_FORBIDDEN_PRESENT_INDICES, FOOD_LIST, FOOD_WEIGHTS, BAD_FOOD_INDICES
from .options import TJEOptions

class TJEGenerator():
    def __init__(self, world):
        self.random = world.random
        self.global_banned_food = set()
        self.global_banned_presents = set()

        self.local_present_weights = PRESENT_WEIGHTS.copy()

        self.per_level_earthling_counts = Counter()
        self.unique_earthling_levels = defaultdict(list)

    # Zeroes out weights for an earthling whose count is already at maximum
    def get_trimmed_level_weights(self, earthling, level_weights, last_level):
        candidates = level_weights[EARTHLING_LIST.index(earthling)]
        return [candidates[i]
                if self.per_level_earthling_counts[i] < EARTHLING_MAX_PER_LEVEL[i] \
                and i not in self.unique_earthling_levels[earthling]
                else 0
                for i in range(2,last_level+1)]

    def generate_full_random_earthlings(self):
        earthlings = []
        for _ in range(2,26):
            earthlings.append(self.random.choices(EARTHLING_LIST, (1,)*21, k=20))
        return earthlings

    def generate_nice_random_earthlings(self, niceness: int = 1, last_level: int = 25):
        # Apply niceness to weights in local copy
        if niceness > 1:
            local_weights = [[w**sqrt(niceness) for w in weights] for weights in EARTHLING_WEIGHTS_PER_LEVEL]
        else:
            local_weights = EARTHLING_WEIGHTS_PER_LEVEL
        # Linearly rescale and trim the per-level Earthling weights if last_level < 25
        if last_level < 25:
            rescaled_levels = [round(((25-2)/(last_level-2))*(x-last_level)) + 25 for x in range(2, last_level+1)]
            local_weights = [[0, 0] + [weights[i] for i in rescaled_levels] for weights in local_weights]
        earthling_total = sum(len(l) for l in BASE_EARTHLINGS[:last_level-1])
        output = defaultdict(list)
        # Start with a base of 8 friendly Earthlings, generate others at random based on vanilla counts
        choices = list(EARTHLING_UNIQUE*2)
        choices += self.random.choices(EARTHLING_LIST, EARTHLING_WEIGHTS, k=earthling_total-8)
        # Assign level-limited Earthlings first
        choices = sorted(choices, key=lambda c: c in EARTHLING_UNIQUE, reverse=True)
        # Assign Earthlings levels in order from rarest to most common to maximize chances of sensible placement
        i = -1
        for c in choices:
            i += 1
            target = self.random.choices(range(2,last_level+1),
                                         self.get_trimmed_level_weights(c, local_weights, last_level),
                                         k=1)[0]
            output[target].append(c)
            self.per_level_earthling_counts[target] += 1
            if c in EARTHLING_UNIQUE:
                self.unique_earthling_levels[c].append(target)
        output = [sorted(output[lv]) for lv in sorted(output.keys())]
        # Pad Earthling list out if needed to include all levels
        output += [[0xFF]]*(24 - len(output))
        return output

    def forbid_item(self, item_code: int):
        if item_code in PRESENT_LIST:
            self.global_banned_presents.add(PRESENT_LIST.index(item_code))
        elif item_code in FOOD_LIST:
            self.global_banned_food.add(FOOD_LIST.index(item_code))

    def forbid_bad_presents(self):
        self.global_banned_presents |= BAD_PRESENT_INDICES

    def forbid_bad_food(self):
        self.global_banned_food |= BAD_FOOD_INDICES

    def fewer_upwarps(self):
        self.local_present_weights[0xC] = 2
    
    def more_promotions(self):
        self.local_present_weights[0xB] *= 2

    def get_present_distribution(self, level_one: bool=False, force_good: bool=False) -> tuple[list[int], list[float]]:
        forbiddens = set()
        forbiddens |= self.global_banned_presents
        if level_one:
            forbiddens |= LV1_FORBIDDEN_PRESENT_INDICES
        if force_good:
            forbiddens |= BAD_PRESENT_INDICES

        culled_present_list = [PRESENT_LIST[i] for i in range(len(PRESENT_LIST)) if i not in forbiddens]
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

    def total_points_in_pool(self, item_pool: list[int], promotion_value: int) -> int:
        def item_value(item_code: int, prom_val: int) -> int:
            if item_code == 0x0B:
                return prom_val
            if item_code in PRESENT_LIST:
                return 2
            return 0
        
        return sum([item_value(i, promotion_value) for i in item_pool])

    def add_extra_promotions(self, item_pool: list[int], rank_thresholds: list[int], promotion_value: int,
                             options: "TJEOptions") -> None:
        points_available = self.total_points_in_pool(item_pool, promotion_value) + expected_map_points(options.last_level.value)
        points_goal = rank_thresholds[options.max_rank_check.value]
        if points_available < points_goal:
            extra_proms = ceil((points_goal - points_available)/promotion_value)
            if extra_proms > 0:
                for n, item in enumerate(item_pool):
                    if item != 0x0B:
                        item_pool[n] = 0x0B
                        extra_proms -= 1
                    if extra_proms == 0:
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
        case 0: return 0
        case 1: return 5
        case 2: return 10
        case 3: return 15
        case 4: return 20
        case 5: return 25
        case _: return 30

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

def scaled_rank_thresholds(last_level: int = 25, min_items: int = 12, max_items: int = 28,
                           desired_max_rank: int = 8) -> list[int]:
    return [0] + \
           [total_points_to_next_rank(rank, last_level, min_items, max_items, desired_max_rank) for rank in range(8)]

# Average gap between ranks, halved to represent 'average' use
def get_average_promotion_value(rank_thresholds: list[int], max_rank_check: int) -> int:
    return round(rank_thresholds[max_rank_check]/max_rank_check/2)

# Determines a sensible point value for a flat promotion present
# Calculation is roughly "average gap between consecutive ranks, rounded to nearest 10, slight downward bias"
def get_flat_promotion_value(rank_thresholds: list[int], max_rank_check: int) -> int:
    return rescale_to_nearest_mult(get_average_promotion_value(rank_thresholds, max_rank_check), 10, 1, -5)

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