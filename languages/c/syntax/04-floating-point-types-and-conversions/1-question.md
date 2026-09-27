# c/syntax/04 — 부동소수점 타입과 변환: 무엇이 보장이고 무엇이 UB 인가 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 **예측형 위주**다 — 아는지가 아니라 **출력을 맞힐 수 있는지**를 묻는다.
> **환경** — gcc 13.3.0 · x86-64 Linux · 기본 `-std=c17 -Wall -Wextra`.\
> 최적화 수준이나 `-ffast-math` 가 답에 영향을 주는 문항은 **문항 안에 적었다.**
> ★ **이 주제의 보장은 조건부다.** 「IEEE 754 니까 이렇게 된다」는 절반이고,\
> 「**이 구현이 IEEE 754 를 따른다고 선언했나**」까지 물어야 맞는 것이다.
> 선행 — [`02-basic-types-sizes-and-fixed-width-integers/`](../02-basic-types-sizes-and-fixed-width-integers/).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (왜) / (예측) / (경계) / (연결) -->

### 1. `0.1 + 0.2 == 0.3` (예측) ★ 절반만 맞는 고전

```c
printf("%d\n", (0.1 + 0.2) == 0.3);
printf("%.17g %.17g %.17g\n", 0.1, 0.1 + 0.2, 0.3);
printf("%g %g\n", 0.1 + 0.2, 0.3);
printf("%d\n", (0.1f + 0.2f) == 0.3f);      /* ★ float 로 바꾸면? */
printf("%d\n", (0.5 + 0.25) == 0.75);
```

- 다섯 줄은 각각 무엇을 찍는가?
- **`float` 쪽의 답이 `double` 쪽과 다른가** — 다르다면 왜인가?
- `%g` 와 `%.17g` 의 출력이 다른 이유는?
- `0.5 + 0.25 == 0.75` 가 그 값인 이유는?

### 2. 이 플랫폼의 `long double` (예측)

```c
printf("%zu %d\n", sizeof(long double), LDBL_MANT_DIG);
long double ld = 1.0L;
unsigned char raw[sizeof(long double)];
memcpy(raw, &ld, sizeof raw);
for (size_t i = 0; i < sizeof raw; i++) printf("%02x ", raw[i]);
```

- `sizeof(long double)` 과 `LDBL_MANT_DIG` 는 각각 무엇인가?
- 두 값이 안 맞는다 — 왜인가?
- 바이트 덤프에서 뒤쪽 바이트들이 그렇게 나오는 이유는?
- `sizeof(long double)` 은 어느 층인가?

### 3. `(float)16777217` (예측)

```c
printf("%.1f\n", (double)(float)16777216);
printf("%.1f\n", (double)(float)16777217);
printf("%d\n", (float)16777217 == (float)16777216);
printf("%.1f\n", (double)9007199254740993LL);
printf("%d\n", 1e16 == 1e16 + 1);
```

- 다섯 줄은 각각 무엇을 찍는가?
- `16777217` 과 `9007199254740993` 은 각각 무엇의 경계인가?
- 이 변환에 `-Wall -Wextra` 가 경고를 주는가? `-Wconversion` 은?
- 이것은 어느 층인가 — UB 인가?

### 4. 부동 → 정수 변환 (예측) ★★

```c
int to_int(double d) { return (int)d; }
unsigned to_u(double d) { return (unsigned)d; }
printf("%d %d %d %d %u\n",
       to_int(3.9), to_int(-3.9), to_int(1e10), to_int(NAN), to_u(-1.0));
```

- **`-O0`** 에서 다섯 값은? **`-O2`** 에서는? — 몇 개가 달라지는가?
- 두 실행의 **종료 코드**는?
- `(int)3.9` 가 `3` 인 것은 반올림인가 절단인가 — `(int)-3.9` 로 확인할 수 있는가?
- `-fsanitize=undefined` 로 돌리면 무엇이 나오는가?
- 안 나온다면 무엇을 더 켜야 하는가?

### 5. `NaN` 과 무한대 (예측)

```c
double z = 0.0, inf = 1.0/z, nan_ = z/z;
printf("%f %d\n", inf, isinf(inf));
printf("%f %d\n", nan_, isnan(nan_));
printf("%d %d %d %d\n", nan_ == nan_, nan_ != nan_, nan_ < 1.0, nan_ >= 1.0);
printf("%f %d %f\n", inf - inf, -0.0 == 0.0, 1.0 / -0.0);
```

- 각 줄은 무엇을 찍는가?
- `nan < 1.0` 과 `nan >= 1.0` 이 **둘 다 거짓**인가 — 그렇다면 어떤 추론이 깨지는가?
- `-0.0 == 0.0` 이 참인데 `1.0 / -0.0` 은 왜 `-inf` 인가?
- 이 동작들은 **어느 조건이 만족될 때만** 보장되는가?

### 6. `-ffast-math` 를 켜면 (예측) ★★

위 5번의 코드를 `-O2 -ffast-math` 로 컴파일한다.

- `0.0 / 0.0` 은 무엇이 되는가?
- `isnan(nan_)` 과 `isinf(inf)` 는 무엇을 돌려주는가?
- `nan == nan` 은?
- `inf - inf` 는?
- **컴파일러가 이 사실을 알려 주는 방법**이 있는가 — 매크로 두 개로 확인할 수 있는가?
- `-O3` 와 `-Ofast` 중 어느 쪽이 이 일을 일으키는가?

### 7. `float` 이 `double` 이 되는 자리 (경계)

```c
float a = 0.1f, b = 0.2f;
printf("%zu %zu\n", sizeof(a + b), sizeof(a + 0.2));
printf("%.9g %.17g %.17g\n", (double)(a+b), (double)a + (double)b, a + 0.2);
printf("%f\n", a);
```

- `sizeof(a + b)` 와 `sizeof(a + 0.2)` 는 각각 무엇인가?
- 세 개의 `0.3` 근사값이 전부 다르다 — 왜인가?
- `printf("%f", a)` 가 되는 이유는 무엇이고, 그렇다면 `%f` 는 어느 타입용인가?
- 가변 인자 함수에서 `va_arg(ap, float)` 는 맞는 코드인가?

### 8. `FLT_EVAL_METHOD` 가 무엇인가 (경계)

- 이 환경에서 `FLT_EVAL_METHOD` 는 무엇인가?
- 0·1·2 는 각각 무슨 뜻인가?
- 이 값이 2 인 플랫폼에서는 무엇이 달라지는가?
- 이 값은 어느 층인가?

### 9. `__STDC_IEC_559__` 는 무엇을 보장하나 (경계)

- 이 매크로가 정의되어 있으면 무엇이 보장되는가?
- 정의되어 있지 않은 구현에서 `1.0/0.0` 은 무엇인가?
- `-ffast-math` 는 이 매크로를 어떻게 하는가?
- 이식성이 걸린 코드에서 이 매크로를 어떻게 쓰는가?

### 10. 어떻게 비교해야 하나 (연결)

```c
double a = 0.1 + 0.2, b = 0.3;
double big1 = 1e16, big2 = 1e16 + 1.0;
```

- `a` 와 `b` 를 `fabs(a-b) < 1e-9` 로 비교하면 맞는가?
- 같은 방법을 `big1`·`big2` 에 쓰면 무엇이 문제인가?
- 상대 오차 비교는 어떻게 쓰는가?
- `%.17g` 와 `%.15g` 중 왕복하는 것은 어느 쪽이고, `DBL_DIG` 와 `DBL_DECIMAL_DIG` 는 어떻게 다른가?

### 11. 그래서 무엇을 고르나 (연결)

- 금액 계산에 `double` 을 쓰면 안 되는 이유를 이 주제의 실측 하나로 설명할 수 있는가?
- `float` 를 고르는 것이 옳은 상황 두 가지는?
- 부동 → 정수 변환을 안전하게 쓰는 형태는 — **NaN 까지 거르려면** 조건을 어떻게 쓰는가?
- 이 주제의 결론을 빌드 플래그 한 줄로 쓰면?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
