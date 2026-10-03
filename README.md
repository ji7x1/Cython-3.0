# fastmath

مكتبة صغيرة لدوال رياضية سريعة مكتوبة بـ **Cython 3.0**.

| الدالة | الوصف |
|---|---|
| `fib(n)` | رقم فيبوناتشي رقم n (دقة غير محدودة) |
| `is_prime(n)` | هل العدد أولي؟ |
| `primes_up_to(n)` | كل الأعداد الأولية حتى n (غربال إراتوستينس) |
| `sum_of_squares(n)` | مجموع مربعات الأعداد من 1 إلى n |

## التثبيت والتشغيل

```bash
pip install -e ".[test]"   # يبني امتداد Cython
python -m pytest           # الاختبارات
python bench.py            # مقارنة السرعة مع Python العادي
```

```python
>>> import fastmath
>>> fastmath.primes_up_to(30)
[2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
>>> fastmath.fib(50)
12586269025
```
