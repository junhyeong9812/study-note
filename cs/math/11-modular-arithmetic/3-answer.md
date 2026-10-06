# math/11-modular-arithmetic — 정답

## 정답

### 1. 세 가지 나머지 규칙

- 나눗셈 정리(MCS Theorem 9.1.4): n = q·d + r, 0 ≤ r < |d|. 나머지는 음수가 아니다.
- Java: 정수 `/`는 0 쪽으로 버린다(JLS §15.17.2). `(a/b)*b + (a%b) == a`를 지키므로 `%`는 **피제수** 부호를 따른다(§15.17.3).
- Python: `//`는 아래로 내린다(floor). 같은 항등식 `x == (x//y)*y + (x%y)`를 지키므로 `%`는 **제수** 부호를 따른다(Python 참조 6.7).
- 제수가 양수면 Python `%`·`Math.floorMod`가 수학 정의(0 ≤ r < d)와 일치한다. 제수가 음수면 floor 규칙은 0 이하를 주어 수학 정의(0 이상)와 어긋난다. 예: 7과 −3은 수학 1, Java 1, floor −2. −7과 −3은 수학 2, Java·floor 모두 −1.

### 2. 값

(실험, OpenJDK 21.0.12 / Python 3.12.3, 2026-10-07)

```text
-7 % 3 = -1, -7 / 3 = -2, floorMod(-7,3) = 2, floorDiv(-7,3) = -3, floorMod(7,-3) = -2
>>> -7 % 3, -7 // 3, 7 % -3
2 -3 -2
```

- `floorMod(7, -3) = -2`: 제수가 음수라 결과도 음수다. "floorMod는 0 이상"은 제수가 양수일 때만 맞다.

### 3. MIN_VALUE의 함정

```text
Math.abs(MIN_VALUE)=-2147483648, -MIN_VALUE=-2147483648, MIN_VALUE/-1=-2147483648, MIN_VALUE%-1=0
absExact: java.lang.ArithmeticException: Overflow to represent absolute value of Integer.MIN_VALUE
```

- `int`는 −2^31..2^31−1이라 2^31을 표현하지 못한다. 넘친 결과는 수학적 결과의 하위 32비트, 곧 mod 2^32 대표값이라 다시 −2^31이 된다.
- 예외가 없는 이유: JLS §4.2.2 "The integer operators do not indicate overflow or underflow in any way". §15.17.2도 MIN_VALUE / −1을 "넘치지만 예외 없음"으로 명시한다.
- 드러내는 메서드: `Math.absExact`(Java 15+), `Math.negateExact`, `Math.multiplyExact` 등 `*Exact` 계열.

### 4. gcd와 쓰는 칸

- n = 64 → 8칸, n = 61 → 61칸, n = 60 → 15칸(실험 출력과 같다).
- 일반식: 간격 s 키가 쓰는 칸 = **최대 n / gcd(s, n)**(키 K개면 min(K, n / gcd(s, n))). 나머지가 시작 키 a와 gcd(s, n)를 법으로 합동인 값만 나오기 때문이다(a = 0이면 gcd의 배수).
- `HashMap` 256칸에 8의 배수 `Integer` 키 150개 → 32칸(= 256/8)만 썼다(실험). `Integer.hashCode()`는 값 그대로이고, `h ^ (h >>> 16)` 섞기는 값이 0 이상 2^16 미만이면 아무것도 바꾸지 않는다. 칸 인덱스가 `(n−1) & hash` = hash mod 256이라 gcd 규칙이 그대로 적용된다.

### 5. 역원

- mod 7에서 3의 역원 = **5**(3·5 = 15 ≡ 1). 확장 유클리드: 3·(−2) + 7·1 = 1 → x = −2 → `floorMod(−2, 7) = 5`.
- mod 9에서 6의 역원은 **없다**. gcd(6, 9) = 3 ≠ 1. 6x mod 9는 0, 3, 6만 나온다.
- 조건: gcd(k, n) = 1(MCS Theorem 9.9.5). 방법: 확장 유클리드(일차결합, Theorem 9.2.2). n이 소수면 페르마 k^(n−2)도 되지만 합성수에서는 역원이 보장되지 않아 틀린 값을 조용히 줄 수 있다(n = 9, k = 8처럼 우연히 맞기도 한다).
- 없을 때: Java `BigInteger.valueOf(6).modInverse(BigInteger.valueOf(9))` → `ArithmeticException: BigInteger not invertible.` Python `pow(6, -1, 9)` → `ValueError: base is not invertible for the given modulus`(실험).

### 6. 거듭제곱 넘침 경계

- 피연산자가 m 미만이면 곱 < m². (m − 1)² ≤ 2^63 − 1 ⇔ m ≤ **3,037,000,500**(Python `math.isqrt` 계산).
- 경계를 1 넘은 m = 3,037,000,501에서 무작위 10만 건 → 틀린 건수 **0**(실험, 시드 7). 넘치려면 두 피연산자가 m 바로 아래여야 해서 무작위로 거의 안 뽑힌다.
- m = 40억에서는 87,604건 틀렸다. 경계 바로 위 버그는 경계값(a = b = m − 1) 테스트로만 잡힌다.

### 7. Java·Python 샤드 불일치

- 원인: 해시값이 음수인 키에서 Java `%`는 음수(예: −1), Python `%`는 n − 1을 준다. 같은 키가 다른 샤드로 간다. Java 쪽이 음수를 `abs`로 처리했다면 또 다른 번호가 나온다.
- 해시 함수 자체가 언어마다 다를 수도 있다(Java `String.hashCode` vs Python `hash()`는 문자열에 대해 프로세스마다 무작위화).
- 대처: 샤드 규칙을 명세로 고정한다 — 언어 중립 해시 + floor 나머지 + 샤드 수. Java는 `Math.floorMod`, Python은 `%`. 양쪽에 음수 해시를 포함한 같은 테스트 벡터를 둔다. 이미 잘못 들어간 데이터는 재배치 계획이 필요하다.

### 8. 바이트 % 10의 편향

- 256 = 25·10 + 6이라 0~5는 26/256, 6~9는 25/256 확률이다(전수 계산: `[26, 26, 26, 26, 26, 26, 25, 25, 25, 25]`). 균일하지 않다.
- 인증 코드면 추측 공격자가 0~5를 먼저 시도해 아주 조금 유리해진다. 통계 표본이면 결과가 치우친다.
- 고침: `SecureRandom`의 `nextInt(10)`을 쓴다. `SecureRandom`이 물려받은 `Random.nextInt(int bound)`는 고르지 않게 만드는 값을 버리고 다시 뽑는다(거절 표집, Java 21 `Random.nextInt(int)` 문서 "It rejects values that would result in an uneven distribution"). 직접 하려면 250 이상인 바이트를 버린다.

### 9. XID 비교와 링 버퍼

- 둘 다 **원형 공간(Z_n)**이다.
  - PostgreSQL XID: 32비트 번호를 2^32 모듈로 비교한다. 어느 XID든 앞의 약 20억 개는 과거, 뒤의 약 20억 개는 미래로 본다([database/16-mvcc](../../database/16-mvcc/2-summary.md)).
  - 링 버퍼: 위치 = 순번 mod 용량. 순번이 커져도 위치는 0..용량−1을 돈다.
- 용량을 2^k로 잡으면 `순번 & (2^k − 1)`이 `순번 mod 2^k`와 같다(순번이 0 이상일 때). 나눗셈 대신 비트 AND 한 번이고, 순번이 int 범위를 넘어 감겨도 연속성이 유지된다(2^32가 2^k의 배수). 링 버퍼 쪽 자세한 내용은 [data-structure/25-ring-buffer](../../data-structure/25-ring-buffer/2-summary.md).
