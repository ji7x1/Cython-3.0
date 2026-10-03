# cython: language_level=3, boundscheck=False, wraparound=False
"""Cython core of fastmath."""

from libc.stdlib cimport calloc, free


def fib(int n):
    """Return the n-th Fibonacci number (fib(0) == 0). Arbitrary precision."""
    if n < 0:
        raise ValueError("n must be non-negative")
    a, b = 0, 1
    cdef int i
    for i in range(n):
        a, b = b, a + b
    return a


cpdef bint is_prime(long long n):
    """Return True if n is prime (trial division by 6k +/- 1)."""
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    cdef long long i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


def primes_up_to(long n):
    """Return a list of all primes <= n (sieve of Eratosthenes)."""
    if n < 2:
        return []
    cdef char *composite = <char *>calloc(n + 1, sizeof(char))
    if composite == NULL:
        raise MemoryError()
    cdef long i, j
    result = []
    try:
        i = 2
        while i * i <= n:
            if not composite[i]:
                j = i * i
                while j <= n:
                    composite[j] = 1
                    j += i
            i += 1
        for i in range(2, n + 1):
            if not composite[i]:
                result.append(i)
    finally:
        free(composite)
    return result


def sum_of_squares(long long n):
    """Return 1^2 + 2^2 + ... + n^2 computed with a C loop."""
    if n < 0:
        raise ValueError("n must be non-negative")
    cdef long long i
    cdef long long total = 0
    for i in range(1, n + 1):
        total += i * i
    return total
