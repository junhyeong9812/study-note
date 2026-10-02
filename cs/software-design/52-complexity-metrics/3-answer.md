# software-design/52-complexity-metrics — 정답

## 정답

### 1. if 두 개

```text
 [N1: member?] → N2(then) / N3(else) → [N4: coupon?] → N5(then) / N6(else) → [N7: return]
 N = 7, E = 8, P = 1
 V = 8 − 7 + 2 = 3   (= 결정 2 + 1)
```

- NPath = 2 × 2 = 4(나란한 블록은 곱한다). PMD 실험 d 출력도 순환 3, NPath 4였다.

### 2. 최소 테스트 수의 뜻

- 기저 경로 테스트 기준이다. v(G)는 선형 독립 경로의 최대 수, 곧 기저 집합의 크기다.
- McCabe 1976: "v is only the minimal number of independent paths that should be tested. There are often additional paths to test."
- 분기 커버리지는 v보다 적은 테스트로 채울 수 있고, 모든 경로는 v보다 많을 수 있다.

### 3. 실험 d

(실험, PMD 7.28.0·JDK 21.0.12 temurin, 2026-10-02)

```text
분기 커버리지 최소(TF,FT)          테스트 2개, 분기 커버 4/4, 버그 발견 아니오
기저 경로 3개(FF,TF,FT)         테스트 3개, 분기 커버 4/4, 버그 발견 아니오
모든 경로(TT,TF,FT,FF)         테스트 4개, 분기 커버 4/4, 버그 발견 예
```

- 버그는 두 결정이 모두 참(TT)일 때만 드러난다(3,000 − 1,000 − 1,500 = 500 < 하한 1,000). 분기 커버리지 최소 세트와 이 기저 경로 세트에는 TT가 없다.

### 4. 인지 복잡도 규칙

1. 여러 문장을 하나로 줄이는 축약은 무시한다(메서드 자체, null 병합).
2. 선형 흐름이 끊길 때마다 +1.
3. 흐름을 끊는 구조가 중첩되면 중첩 깊이만큼 더한다.

- `switch`: case 수와 관계없이 +1.
- 같은 종류 논리 연산자 열(`a && b && c`): +1 한 번. 종류가 바뀔 때마다 다시 +1.
- 조기 `return`·일반 `break`/`continue`: 더하지 않는다.
- 레이블로 점프하는 `continue OUT`: +1.

### 5. 백서 예제와 중첩 vs 가드 절

```text
Paper.java:3:	CognitiveComplexity:	The method 'sumOfPrimes(int)' has a cognitive complexity of 7,
Paper.java:3:	CyclomaticComplexity:	The method 'sumOfPrimes(int)' has a cyclomatic complexity of 4.
Paper.java:16:	CognitiveComplexity:	The method 'getWords(int)' has a cognitive complexity of 1,
Paper.java:16:	CyclomaticComplexity:	The method 'getWords(int)' has a cyclomatic complexity of 4.
Shipping.java:3:	CognitiveComplexity:	The method 'feeNested(Order)' has a cognitive complexity of 11,
Shipping.java:19:	CognitiveComplexity:	The method 'feeGuarded(Order)' has a cognitive complexity of 4,
```

- `sumOfPrimes` 순환 4·인지 7, `getWords` 순환 4·인지 1(백서 값과 같다).
- 중첩판·가드 절판 모두 순환 5. 인지는 중첩판 11(+1+2+3+4, else +1), 가드 절판 4.

### 6. 게이트 게이밍

```text
### c (PMD 7.28.0 기본 임계)
Approval.java:3:	CyclomaticComplexity:	The method 'decide(long, int, boolean, boolean, String, int)' has a cyclomatic complexity of 14.
```

- 기본 임계에서는 원본 `Approval.decide`(순환 14)만 보고되고, 쪼갠 쪽(메서드 최대 7)은 통과한다.
- 쪼갠 쪽 클래스 합계는 19로 원본 14보다 늘었다. 인지 복잡도는 원본 13 → 쪼갠 쪽 합 15(2·3·6·4).
- 원본 인지 13은 기본 임계 15 아래라 인지 복잡도 규칙에는 걸리지 않았다.

### 7. 기본 임계

| 규칙 | PMD 7.28.0 기본 | 비교 |
|---|---|---|
| CyclomaticComplexity | 메서드 10, 클래스 80 | ≥ |
| CognitiveComplexity | 15 | ≥ |
| NPathComplexity | 200 | ≥ |
| AvoidDeeplyNestedIfStmts | problemDepth 3 | — |

- 근거: PMD 7.28.0 규칙 소스 `defaultValue(...)`와 `if (... >= reportLevel)`.
- Sonar Java: S3776(인지) 기본 15, S1541(순환) 기본 10, 둘 다 `> max`일 때 보고한다. 같은 15라도 PMD는 15에서, Sonar는 16부터 보고한다.

### 8. 순환 복잡도 40의 반복 버그

- 원인: 독립 경로만 40개이고 조합 경로는 훨씬 많다. 분기 커버리지가 높아도 결정끼리 겹치는 조합은 시험되지 않는다(실험 d와 같은 구조).
- 대처: 기저 경로부터 테스트를 채우고, 조합은 결정 테이블·경계값으로 고른다. 결정들을 이름 붙은 규칙 객체나 테이블로 나눠 각자 테스트한다.

### 9. 큰 case 문

- McCabe 1976: 상한 10이 불합리해 보인 유일한 경우로 큰 case 문(선택 함수 뒤 독립된 case가 많은 경우)을 들었다.
- 이런 `switch`는 순환 복잡도는 높아도 인지 복잡도는 1이다(`switch`는 +1).
- 대처: 인지 복잡도로 판단하거나, 억제 주석에 이유를 남긴다. 가능하면 `EnumMap`·enum 필드로 옮겨 분기를 없앤다. 임계를 몰래 올리지 않는다.
