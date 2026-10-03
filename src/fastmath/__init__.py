"""Fast numeric helpers implemented in Cython."""

from ._core import fib, is_prime, primes_up_to, sum_of_squares

__all__ = ["fib", "is_prime", "primes_up_to", "sum_of_squares"]
__version__ = "0.1.0"
