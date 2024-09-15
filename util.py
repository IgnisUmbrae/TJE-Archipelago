from itertools import accumulate, chain
from functools import partial
from math import floor
# import random

ITEM_NAME_TO_HP_VALUE: dict[str, int] = {
    "Candy Cane": 4,
    "Watermelon": 4,
    "Bacon & Eggs": 4,
    "Cereal": 4,
    "Fries": 8,
    "Pancake": 8,
    "Cherry Pie": 8,
    "Pizza": 8,
    "Burger": 12,
    "Fudge Sundae": 12,
    "Fudge Cake": 12,
    "Moldy Cheese": -4,
    "Moldy Bread": -4,
    "Slimy Fungus": -4,
    "Fish Bones": -8,
    "Old Cabbage": -12
}

HP_VALUE_TO_ITEMS: dict[int, list[str]] = {
    4: ["Candy Cane", "Watermelon", "Bacon & Eggs", "Cereal"],
    8: ["Fries", "Pancake", "Cherry Pie", "Pizza"],
    12: ["Burger", "Fudge Sundae", "Fudge Cake"],
    -4: ["Moldy Cheese", "Moldy Bread", "Slimy Fungus"],
    -8: ["Fish Bones"],
    -12: ["Old Cabbage"]
}

FOOD_BASIS = [12, 8, 4]

def sign(num: int) -> int:
    return (num > 0) - (num < 0)

def clamped_add_and_revive(x, y, max_hp):
    if x == 0:
        x = max_hp
    return max(min(x+y, max_hp), 0)

def split_at_zero(queue: list[int]):
    if 0 in queue:
        index = queue.index(0)
        yield from chain(split_at_zero(queue[:index]), split_at_zero(queue[index+1:]))
    else:
        yield queue

def greedy_partition(num: int, last: int = 0):
    if last < len(FOOD_BASIS):
        divisor = FOOD_BASIS[last]
        k = floor(num/divisor)
        yield from chain([k], greedy_partition(num - k*divisor, last+1))

def express_in_basis(num: int) -> list[int]:
    return [i*FOOD_BASIS[n]*sign(num) for n, i in enumerate(greedy_partition(abs(num))) if i > 0]

def simplify_queue(queue: list[int], current_hp: int, max_hp: int) -> tuple[int, list[int]]:
    accumed_list = list(accumulate(queue, func=partial(clamped_add_and_revive, max_hp=max_hp), initial=current_hp))
    split_list = list(split_at_zero(accumed_list))
    total_subchains = len(split_list)

    death_count = 0
    leftover_queue = []
    for n, x in enumerate(split_list):
        if n < total_subchains - 1:
            death_count += 1
        else:
            if (x and x[-1] == max_hp) or not x:
                leftover_queue = []
            else:
                base = max_hp if death_count > 0 else current_hp
                leftover_queue = express_in_basis(x[-1] - base)

    return death_count, leftover_queue

# spawn_queue: list[int] = random.choices([4, 8, 12, -4, -8, -12], k=random.randint(4, 10))

# print(f"Spawn queue: {spawn_queue}")

# deaths, final = simplify_queue(spawn_queue, current_hp=7, max_hp=17)

# print(f"Total deaths: {deaths}")
# print(f"Leftover queue: {final}")
