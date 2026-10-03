import pytest

import fastmath


def naive_primes(n):
    return [k for k in range(2, n + 1) if all(k % d for d in range(2, int(k**0.5) + 1))]


def test_fib():
    assert [fastmath.fib(i) for i in range(10)] == [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
    assert fastmath.fib(100) == 354224848179261915075


def test_fib_negative():
    with pytest.raises(ValueError):
        fastmath.fib(-1)


def test_is_prime():
    assert [n for n in range(-5, 50) if fastmath.is_prime(n)] == naive_primes(49)
    assert fastmath.is_prime(2_147_483_647)
    assert not fastmath.is_prime(2_147_483_649)


@pytest.mark.parametrize("n", [0, 1, 2, 3, 10, 100, 1000])
def test_primes_up_to(n):
    assert fastmath.primes_up_to(n) == naive_primes(n)


def test_sum_of_squares():
    for n in (0, 1, 2, 10, 1000):
        assert fastmath.sum_of_squares(n) == n * (n + 1) * (2 * n + 1) // 6
    with pytest.raises(ValueError):
        fastmath.sum_of_squares(-1)
