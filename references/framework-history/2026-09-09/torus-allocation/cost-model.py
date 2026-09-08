from typing import Tuple
import math

slice_sizes = [(2,2,1), (2,2,2), (2,2,4), (2,4,4)]

def get_alpha_factor(slice_size: Tuple[int, int, int]) -> float:
    x, y, z = slice_size
    num_elements = x * y * z

    if x > 1 and y > 1 and z > 1:
        return math.pow(num_elements, 1/3)
    elif z == 1 and x > 1 and y > 1:
        return math.pow(num_elements, 1/2)
    else:
        return num_elements
    
def get_beta_factor(slice_size: Tuple[int, int, int]) -> float:
    x, y, z = slice_size
    num_elements = x * y * z
    dimension = 1

    if x > 1 and y > 1 and z > 1:
        dimension = 3
    if x > 1 and y > 1 and z == 1:
        dimension = 2

    return (num_elements - 1) / num_elements * (1 / dimension)

# TODO: Plug in values of alpha and beta    