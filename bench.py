"""Compare fastmath (Cython) against equivalent pure Python."""
import timeit

import fastmath


def py_sum_of_squares(n):
    total = 0
    for i in range(1, n + 1):
        total += i * i
    return total


def py_primes_up_to(n):
    composite = bytearray(n + 1)
    i = 2
    while i * i <= n:
        if not composite[i]:
            composite[i * i :: i] = b"\x01" * len(range(i * i, n + 1, i))
        i += 1
    return [k for k in range(2, n + 1) if not composite[k]]


cases = [
    ("sum_of_squares(1_000_000)", lambda: fastmath.sum_of_squares(1_000_000), lambda: py_sum_of_squares(1_000_000)),
    ("primes_up_to(1_000_000)", lambda: fastmath.primes_up_to(1_000_000), lambda: py_primes_up_to(1_000_000)),
]

for name, cy, py in cases:
    t_cy = min(timeit.repeat(cy, number=5, repeat=3)) / 5
    t_py = min(timeit.repeat(py, number=5, repeat=3)) / 5
    print(f"{name:28} cython {t_cy*1e3:8.2f} ms   python {t_py*1e3:8.2f} ms   x{t_py/t_cy:5.1f}")
