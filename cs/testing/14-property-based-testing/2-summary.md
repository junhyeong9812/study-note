# testing/14-property-based-testing — 속성 기반 테스트: 성질·생성기·축소 — 정리 (힌트)

## 해결하는 문제

예제 기반 테스트는 **사람이 떠올린 입력**만 시험한다. 떠올리지 못한 입력 조합의 버그는 그대로 통과한다.

```text
  예제 기반                              속성 기반
  dedup([1,1,2,3,3]) == [1,2,3]  ✔       "어떤 목록 xs든 dedup(xs)에는 중복이 없다"
  sort([3,-1,2]) == [-1,2,3]     ✔         → 생성기가 xs를 100개 뽑아 검사
  unrle(rle("aaabcc")) == ...    ✔         → 실패하면 가장 작은 반례로 줄여서 보여 준다
                                            [0,1,0]   ← 인접하지 않은 중복
  사람이 고른 3개 입력: 전부 초록
```

- 해법: 개별 입력·출력 쌍 대신 **모든 입력에 대해 성립해야 하는 성질**을 적고, 입력은 생성기가 무작위로 만든다. 실패하면 반례를 작게 줄인다.
  - *속성 기반 테스트(PBT, Property-Based Testing)*: 성질(property) + 입력 생성기(generator) + 반례 축소(shrinking)로 이루어진 테스트 방식. Claessen–Hughes의 QuickCheck(ICFP 2000)가 널리 퍼뜨렸다.

쉬운 예: "문자열을 두 번 뒤집으면 원래 문자열이다."
- 예제로는 `"abc"` 하나를 넣어 본다. 성질로 쓰면 빈 문자열·한 글자·이모지·긴 문자열까지 생성기가 넣어 본다.

똑같은 구조다.\
직렬화 → 역직렬화 왕복, 정렬 결과가 정렬돼 있는지, 새 구현과 옛 구현의 결과가 같은지 — 전부 "어떤 입력이든 성립해야 하는 관계"다.

실무 예:
- JSON 직렬화 라이브러리 교체 후, 특정 유니코드 문자열에서만 왕복이 깨진다.
- 정렬 비교자 `(a, b) -> a - b`가 큰 음수·양수 조합에서 오버플로해 정렬 결과가 틀린다.
- 압축·인코딩 함수가 10번 이상 반복되는 문자에서만 깨진다.

## 동작·원리

### 1. 한 번의 실행 — 생성 → 검사 → 축소 → 보고

```text
   seed ──▶ [생성기] ──xs₁──▶ 성질(xs₁)? ✔
                     ──xs₂──▶ 성질(xs₂)? ✔
                       ...
                     ──xsₖ──▶ 성질(xsₖ)? ✘  ← 실패 (k번째 실행)
                                  │
                                  ▼
                          [축소] 더 작은 후보를 차례로 시험
                           xsₖ = [2147483618, 0, 2147483618, ...]
                             → 원소 제거·값 줄이기 → 여전히 실패하면 채택
                           결과 = [2147483618, 0, 2147483618]
                                  │
                                  ▼
                   보고: 반례 + seed (+ 경로) → 같은 seed로 재실행하면 재현
```

- *성질(property)*: 입력 전체에 대해 참이어야 하는 불리언 조건. 코드로는 "입력을 받아 참·거짓(또는 단언)을 내는 함수"다.
- *생성기(generator, arbitrary)*: 특정 타입·분포의 무작위 값을 만드는 객체. 작은 생성기를 `map`·`tuple`·`array`로 조합해 도메인 값을 만든다.
- *축소(shrinking)*: 실패한 입력을 "더 작은" 후보로 바꿔 가며, 여전히 실패하는 가장 작은 입력을 찾는 탐색.
- *시드(seed)*: 의사난수 생성기의 시작값. 시드가 같으면 같은 입력 열이 나온다. 그래서 반례를 재현할 수 있다.

### 2. 도구별 기본값 — 확인한 범위

| 도구 | 기본 실행 횟수 | 출처 |
|---|---|---|
| QuickCheck(논문, 2000) | 100 (`OK, passed 100 tests.`) | Claessen–Hughes ICFP 2000 본문 출력 예 |
| fast-check 4.10.2 (JS/TS) | `numRuns` 100 | `fast-check.d.ts`: "Number of runs before success: 100 by default" |
| jqwik 1.10.1 (Java) | `tries` 1000 | jqwik User Guide 1.10.1 |

- fast-check 4.10.2: 생성기는 기본이 *편향(biased)* 이다(작은 값·경계 근처 값을 더 자주 낸다 — `unbiased` 옵션 설명 "biased by default"). 재현은 `seed` + `path`로 한다(`path`: "replay a failing property directly with the counterexample").
- jqwik 1.10.1(User Guide): 축소는 기본 `BOUNDED`(최대 10초), 경계값(edge cases)은 기본 `MIXIN`(무작위 값 사이에 섞음), 실패 뒤 재실행은 기본 `SAMPLE_FIRST`(직전에 축소된 반례를 먼저 시도).

### 3. 성질을 찾는 패턴

```text
  왕복(round-trip)     decode(encode(x)) == x            직렬화·인코딩·파서
  불변식               sort(xs)는 이웃끼리 순서가 맞고,    정렬·변환
                       길이·원소 구성이 xs와 같다
  기준 구현(오라클)    fast(x) == slowButObvious(x)       최적화·리팩터링·이식
  멱등                 f(f(x)) == f(x)                    정규화·dedup·포맷터
  모델 기반            실제 객체와 단순 모델에 같은        상태 있는 API(큐·캐시)
                       명령 열을 넣고 결과 비교
```

- 이 표는 흔히 쓰이는 패턴을 정리한 것이다. QuickCheck 논문(2000)에도 "두 구현 사이의 관계를 성질로 적어 결함 3개를 찾은" 사용 사례(Gill의 pretty printer, 5.4절)가 나온다.
- 주의: 성질이 구현을 그대로 베끼면(같은 계산을 테스트에서 다시 하면) 버그도 같이 베낀다. 성질은 구현보다 **단순하거나 다른 관점**이어야 한다.

### 4. 생성기 분포 — 버그 영역에 닿아야 찾는다

- QuickCheck 논문(2.4 Monitoring Test Data): `classify`로 보니 통과한 100건 중 43%가 빈 목록("trivial")이었다. 성질이 통과해도 **무엇을 시험했는지**는 따로 봐야 한다.

### 실험: 같은 성질, 생성기만 바꾸기

버그 두 개를 심었다. `dedup`은 바로 앞 원소와만 비교한다(인접 중복만 제거). `unrle`은 반복 횟수를 한 자리 숫자로만 읽는다(10번 이상 반복이면 깨짐).

```js
// scratchpad/ts/07/fc/props.mjs 발췌 — fast-check 4.10.2
const abc = fc.constantFrom("a", "b", "c");
// 생성기 A: 문자를 하나씩 뽑는다
const chars = fc.array(abc, { maxLength: 30 }).map(cs => cs.join(""));
// 생성기 B: "(문자, 반복 수 1..15)" 묶음을 뽑아 이어 붙인다
const runs = fc.array(fc.tuple(abc, fc.integer({ min: 1, max: 15 })), { maxLength: 5 })
  .map(rs => rs.map(([c, n]) => c.repeat(n)).join(""));

fc.property(chars, s => unrle(rle(s)) === s);   // 성질: 왕복하면 원래대로
fc.property(runs,  s => unrle(rle(s)) === s);   // 같은 성질
```

(실험, node:22-alpine · Node v22.23.2 · fast-check 4.10.2, 2026-10-03 — 실행마다 시드가 다르다)

```text
example tests: pass
dedup has no duplicates: FAIL after 32 run(s), 3 shrink(s), seed=229004624
  counterexample: [[2147483618,0,2147483618]]
sort is ordered: FAIL after 1 run(s), 17 shrink(s), seed=-931046326
  counterexample: [[68330691,-2079152958]]
rle round-trip (chars): pass (numRuns=100)
rle round-trip (runs): FAIL after 1 run(s), 4 shrink(s), seed=1612407058
  counterexample: ["aaaaaaaaaa"]
dedup has no duplicates (0..3): FAIL after 1 run(s), 3 shrink(s), seed=-899640054
  counterexample: [[0,1,0]]
```

시드 1~200으로 각각 기본 100회씩 돌려 반례를 찾은 비율:

```text
chars: found in 0/200 seeds (numRuns=100 each)
runs: found in 200/200 seeds (numRuns=100 each)
dedup full int: found in 47/200 seeds, distinct shrunk = [[-3,0,-3]] [[5,0,5]] [[-16,0,-16]] ... (37종)
dedup 0..3: found in 200/200 seeds, distinct shrunk = [[1,0,1]] [[0,1,0]] [[2,0,2]] [[3,0,3]]
```

생성기가 실제로 만든 값의 분포(`fc.statistics`, 1만 개, 시드 42):

```text
-- chars
longest run 1..9..90.10%
empty..............9.90%
-- runs
longest run >= 10..62.40%
longest run 1..9...20.00%
empty..............17.60%
```

- 관찰
  - 예제 테스트 3개는 심어 둔 버그 3개(dedup·sort·unrle)를 하나도 못 잡았다.
  - 시드 없는 실행은 결과가 매번 다르다. 같은 코드를 다시 두 번 돌리면 `dedup`(전체 int)은 두 번 다 `pass (numRuns=100)`였다. 아래 47/200 비율과 맞는 결과다.
  - 생성기 A는 1만 개 중 같은 문자 10연속을 **한 번도** 만들지 않았다. 그래서 왕복 성질이 200개 시드 전부에서 통과했다. 생성기 B는 62.4%가 10연속 이상이라 200/200으로 잡았다.
  - `dedup`은 전체 int 범위에서 47/200, 0..3 범위에서 200/200. 값 범위가 넓으면 "같은 값이 떨어져서 두 번" 나올 일이 적다.
- 해석: 성질이 옳아도 **생성기가 버그 영역에 닿지 않으면 못 찾는다**. 통과는 "이 분포에서 못 찾았다"는 뜻이다.

### 5. 축소 — 이진 탐색식으로 줄이고, 국소 최소에서 멈춘다

```text
  정수 하나 줄이기 (fast-check 4.10.2 shrinkInteger: 목표(0)까지 남은 거리를 반씩)
    현재 1000, 목표 0 → 후보: 0, 500, 750, 875, ...
    실패가 유지되는 첫 후보로 이동 → 다시 반씩

  목록 줄이기: 원소 빼기 → 남은 원소 값 줄이기

  국소 최소의 예 (dedup 버그)
    [2147483618, 0, 2147483618]
     ├─ 가운데 0 → 더 못 줄임
     ├─ 왼쪽만 줄이면 [0, 0, 2147483618] → 인접 중복이 돼서 통과 → 채택 불가
     └─ 오른쪽만 줄여도 같은 이유 → 채택 불가
    ⇒ "두 원소를 동시에 줄이는" 후보가 없으면 여기서 멈춘다
```

- fast-check 4.10.2 소스(`shrinkInteger`): 남은 거리를 `halvePosInteger(n) = floor(n / 2)`로 반씩 줄이며 후보를 낸다. 이진 탐색과 같은 모양이다.
- 축소는 *탐욕적 국소 탐색*이다. 결과는 "더 줄일 한 걸음이 없는" 반례지 전역 최소가 아니다.
  - 실험의 `sort` 반례는 실행마다 `[68330691,-2079152958]`처럼 부호가 반대이고 차이가 약 2^31(21억)인 쌍으로 남았다. 오버플로를 내려면 두 수의 차이가 커야 해서, 한쪽만 줄이면 성질이 통과하기 때문이다.
  - 쌍의 모양은 시드마다 다르다. 시드 1~30으로 다시 돌리면 30개 모두 실패했고, 그중 5개는 `[8,-2147483641]`·`[-26,2147483622]`처럼 한쪽이 0 근처까지 줄었다. 나머지 25개는 두 값이 모두 큰 수였다(재실행, 같은 환경).
  - `dedup` 전체 int 범위 반례는 `[x, 0, x]` 꼴로 37종이 나왔다. 0..3 범위에서는 4종으로 수렴했다.
- 역사: QuickCheck 논문(2000)의 본체에는 축소가 없다. 논문은 사용 사례에서 Gill이 `smaller :: a -> [a]` 메서드를 더해 "반례가 찾아지면 더 작은 것을 찾게" 확장했다고 소개한다(Claessen–Hughes 2000, 5.4절 Pretty Printing).

## 쓰이는 자료구조·알고리즘

- **의사난수 생성기 + 시드**: 같은 시드 → 같은 입력 열. 재현의 근거다(→ math 12-randomness-and-prng, [math 영역 표](../../math/README.md)).
- **생성기 조합자**: `map`(변환), `tuple`(곱), `array`(반복), `constantFrom`(선택). 도메인 값은 작은 생성기의 합성으로 만든다. 분포는 조합 방식이 정한다(위 실험의 A vs B).
- **이진 탐색식 축소**: 정수 축소는 목표까지의 거리를 반씩 줄이는 [이진 탐색](../../algorithm/06-binary-search/2-summary.md) 모양이다.
- **탐욕적 국소 탐색**: 축소는 "실패를 유지하는 첫 후보로 이동"을 반복한다([탐욕법](../../algorithm/23-greedy/2-summary.md)). 그래서 국소 최소에서 멈춘다.
- **축소 후보 트리(지연 스트림)**: 각 값은 "더 작은 후보들"을 자식으로 가진 트리처럼 다뤄진다. fast-check는 후보를 지연 스트림(`stream(...)`)으로 낸다. 필요할 때만 만든다.
- **모델 기반 테스트의 상태 기계**: 명령 열을 생성해 실제 구현과 단순 모델(예: `ArrayList`로 만든 큐)에 함께 넣는다. 상태 기계 관점은 [07-test-design-techniques](../07-test-design-techniques/2-summary.md)의 상태 전이와 같다.

## 적용 — 풀어나가는 법

### 순서

1. **성질을 고른다.** 왕복 → 불변식 → 기준 구현 순으로 찾아본다. 구현을 베끼는 성질은 버린다.
2. **도메인 생성기를 만든다.** 타입 기본 생성기(전체 int, 임의 문자열)는 분포가 넓어 버그 영역에 안 닿을 수 있다. 위 실험처럼 "반복 묶음", "작은 값 범위", "유효한 주문" 같은 도메인 모양으로 만든다.
3. **분포를 확인한다.** fast-check `fc.statistics`, QuickCheck `classify`·`collect`로 "무엇을 만들었는지"를 본다. 빈 입력이 절반이면 생성기를 고친다.
4. **실패하면 시드로 재현한다.** 보고된 `seed`(fast-check는 `path`까지)를 고정해 다시 돌린다.
5. **축소된 반례를 예제 테스트로 고정한다.** `[0,1,0]`, `"aaaaaaaaaa"`를 회귀 테스트로 남긴다. 다음 무작위 실행이 그 입력을 다시 뽑는다는 보장이 없기 때문이다.
6. **CI에서는 실행 횟수와 시드 기록을 정한다.** 실패 로그에 시드가 남게 하고, 횟수는 실행 시간 예산에 맞춘다.

### 코드 — TypeScript(fast-check)와 Java(jqwik) 모양

```ts
// fast-check 4.x: 테스트 러너(Jest·Vitest) 안에서 fc.assert를 쓴다
import fc from "fast-check";

test("dedup 결과에는 중복이 없다", () => {
  fc.assert(
    fc.property(fc.array(fc.integer({ min: 0, max: 3 })), xs => {
      const out = dedup(xs);
      return new Set(out).size === out.length;
    })
  );
});

// 실패를 재현할 때: 보고된 seed·path를 넣는다
// fc.assert(prop, { seed: -899640054, path: "...", endOnFailure: true });
```

```java
// jqwik 1.10.x 모양(@Property 기본 tries = 1000, User Guide 1.10.1)
class DedupProperties {
    @Property
    void noDuplicates(@ForAll List<@IntRange(min = 0, max = 3) Integer> xs) {
        List<Integer> out = Lists.dedup(xs);
        assertThat(new HashSet<>(out)).hasSize(out.size());
    }
}
```

- 위 실험은 fast-check로 돌렸다. Java 코드는 jqwik User Guide의 API 모양을 옮긴 것이다(이 노트에서 실행 결과를 싣지 않았다).

### 진단: 성질이 통과할 때 확인할 것

| 질문 | 확인 방법 |
|---|---|
| 생성기가 버그 영역(긴 반복·중복·경계값)을 만드나? | `fc.statistics` / `classify`로 비율 확인 |
| 성질이 구현을 베끼고 있지 않나? | 성질 코드가 구현과 같은 계산을 하는지 비교 |
| 사전조건으로 버리는 입력이 많지 않나? | 버려진 비율(QuickCheck의 `==>`, fast-check `fc.pre`) 확인 |
| 실패를 재현할 수 있나? | 실패 로그에 seed가 남는지 |

## 장애 시나리오와 대처

### 1. 생성기 분포가 버그 영역에 닿지 않음 → 성질은 초록, 운영에서 깨짐

- **현상**: 인코딩 함수에 속성 테스트가 있는데도, 같은 문자가 10번 넘게 반복되는 입력에서 운영 데이터가 깨진다.
- **보이는 형태**: 테스트는 매번 `pass (numRuns=100)`. 운영에서는 복호화 결과 길이가 원본과 다르다는 대사 불일치.
- **원인**: 문자를 하나씩 뽑는 생성기가 10연속을 사실상 만들지 않았다(실험: 1만 개 중 0%, 200개 시드 중 0개 검출).
- **대처**: 분포를 측정하고(`fc.statistics`), 도메인 모양 생성기(반복 묶음)로 바꾼다. 같은 성질이 200/200으로 잡았다.

### 2. 성질이 구현을 베낌 → 버그를 정답으로 고정

- **현상**: 할인 계산에 속성 테스트가 있는데 금액 계산 오류가 운영에서 발견됐다.
- **보이는 형태**: 테스트는 초록. 성질 코드가 `expected = amount - amount * rate`로 구현과 같은 식이었다.
- **원인**: 같은 계산을 두 번 하면 같은 버그가 두 번 나온다. 성질이 구현보다 단순하지도, 관점이 다르지도 않았다.
- **대처**: 관계형 성질로 바꾼다. "할인 후 금액 ≤ 원래 금액", "금액이 커지면 할인 후 금액도 줄지 않는다(단조성)", "기준 구현(느리지만 명백한 표 조회)과 같다".

### 3. 시드를 기록하지 않음 → "CI가 가끔 빨갛다"

- **현상**: 속성 테스트가 가끔(실험의 `dedup`은 실행 네 번에 한 번꼴) 실패하는데 로컬에서 재현되지 않는다.
- **보이는 형태**: CI 로그에 반례만 있고 시드가 없거나, 재실행하면 초록. 팀이 "불안정한 테스트"로 분류하고 재시도를 붙인다.
- **원인**: 무작위 입력이 실행마다 달라 **진짜 버그**를 가끔만 밟는다(실험의 `dedup` 전체 int 범위: 200개 시드 중 47개, 약 23.5%).
- **대처**: 시드·경로를 로그에 남기고 그 값으로 재현한다. 재시도로 덮지 않는다(→ [09-flaky-tests](../09-flaky-tests/2-summary.md)). 축소된 반례는 예제 테스트로 고정한다.

### 4. 사전조건 남용 → 대부분의 입력이 버려짐

- **현상**: 성질은 통과하는데 실제로 검사된 입력이 거의 없다.
- **보이는 형태**: QuickCheck 논문의 예처럼 `ordered xs ==>` 조건 때문에 통과한 100건 중 43%가 빈 목록(2.4절). 논문의 QuickCheck는 후보 1000개(기본값) 안에서 조건을 만족하는 100건을 못 채우면 `Arguments exhausted after 64 tests.`처럼 실제로 검사한 수를 보고한다(2.3절).
- **원인**: 무작위 목록이 정렬돼 있을 확률은 길이가 길수록 급격히 준다. 조건을 통과하는 입력은 짧은 목록뿐이다.
- **대처**: 거르지 말고 **처음부터 조건을 만족하게 생성**한다(무작위 목록을 만든 뒤 정렬). 논문도 조건을 `forAll orderedList`(정렬된 목록 생성기)로 바꾸는 것을 "가장 좋은 해법"으로 든다(2.4절).

### 5. 축소 결과가 국소 최소 → 반례가 커서 원인을 모름

- **현상**: 반례가 `[68330691,-2079152958]`처럼 큰 수로 남아 무엇이 문제인지 바로 안 보인다.
- **보이는 형태**: 실행마다 다른 반례. 공통점은 부호가 반대이고 차이가 약 2^31이라는 것뿐이다(한쪽이 `8`처럼 작게 줄 때도 있다).
- **원인**: 축소는 탐욕적 국소 탐색이다. 두 값을 동시에 줄여야 하는 반례는 한쪽씩 줄이는 후보로는 못 줄인다.
- **대처**: 반례의 "공통 모양"을 본다(부호가 반대인 두 수의 차이가 int 범위를 넘음 → 뺄셈 오버플로). 생성기 범위를 좁혀 다시 돌리거나, 의심 모양을 예제로 직접 확인한다.

## 핵심 문장

- 속성 기반 테스트는 "어떤 입력이든 성립해야 하는 성질"을 적고, 입력은 생성기가 만들고, 실패하면 반례를 줄여 보여 준다.
- 성질이 통과했다는 것은 "이 생성기 분포에서 못 찾았다"는 뜻이다. 실험에서 같은 성질이 생성기만 바꾸자 0/200 → 200/200이 됐다.
- 축소는 이진 탐색식으로 값을 줄이는 탐욕적 국소 탐색이라, 전역 최소가 아닌 반례에서 멈출 수 있다.
- 실패는 시드로 재현하고, 축소된 반례는 예제 테스트로 고정한다.
- 성질은 구현보다 단순하거나 다른 관점이어야 한다. 구현을 베낀 성질은 버그도 베낀다.

## 관련 주제·근거

- 선행
  - testing [07-test-design-techniques](../07-test-design-techniques/2-summary.md) — 사람이 고르는 입력(분할·경계)과 상태 모델
- 후속·연결
  - testing [15-mutation-testing](../15-mutation-testing/2-summary.md) — 성질이 변이를 죽이는지로 성질의 판별력을 잰다
  - testing [16-coverage-and-its-limits](../16-coverage-and-its-limits/2-summary.md)
  - testing [09-flaky-tests](../09-flaky-tests/2-summary.md) — 시드 없는 무작위 테스트가 불안정 테스트로 오인되는 경로
  - testing [17-characterization-tests-legacy](../17-characterization-tests-legacy/2-summary.md) — 옛 구현을 기준 구현(오라클)으로 쓰는 경우
  - math 12-randomness-and-prng(미작성, [math 영역 표](../../math/README.md)) · [algorithm/06-binary-search](../../algorithm/06-binary-search/2-summary.md) · [algorithm/23-greedy](../../algorithm/23-greedy/2-summary.md)
- 논문
  - Koen Claessen, John Hughes. "QuickCheck: A Lightweight Tool for Random Testing of Haskell Programs." ICFP 2000, pp. 268–279 — 성질·생성기·`classify`/`collect`(2.4절, 43% trivial 예), `OK, passed 100 tests.` 출력, 사례 절의 `smaller` 확장(Gill) <https://www.cs.tufts.edu/~nr/cs257/archive/john-hughes/quick.pdf>
- 문서·소스
  - fast-check 4.10.2 `lib/fast-check.d.ts` — `numRuns` 기본 100, `seed`, `path`(반례 재현), `endOnFailure`, `unbiased`("biased by default"); `lib/fast-check.js`의 `shrinkInteger`·`halvePosInteger` <https://fast-check.dev/>
  - jqwik User Guide 1.10.1 — `tries` 기본 1000, 축소 `BOUNDED`(10초), edge cases `MIXIN`, after-failure `SAMPLE_FIRST`, 시드 보고 <https://jqwik.net/docs/current/user-guide.html>. 같은 가이드는 1.10부터 "Anti-AI Usage Clause"를 두어 AI 코딩 에이전트의 사용을 원하지 않는다고 밝힌다 — 이 노트의 실험을 fast-check(MIT)로 돌린 이유다.
- 실험 목록(2026-10-03, 코드는 scratchpad/ts/07/fc/)
  - `props.mjs` — node:22-alpine(Node v22.23.2) · fast-check 4.10.2 `node props.mjs`: 예제 3개 통과, dedup·sort·rle 성질의 실패·축소 반례·시드(4회 실행, 실행마다 다름)
  - `rate.mjs` — rle 왕복 성질을 시드 1~200, 기본 100회로: chars 생성기 0/200, runs 생성기 200/200
  - `rate2.mjs` — dedup 성질: 전체 int 47/200(축소 반례 `[x,0,x]` 37종), 0..3 범위 200/200(4종)
  - `stats.mjs` — `fc.statistics` 1만 개(시드 42): chars 생성기의 10연속 이상 0%, runs 생성기 62.4%
  - 사실 점검 재실행(같은 환경) — 위 4개 결정적 출력(시드 고정) 일치. 추가로 sort 성질을 시드 1~30으로 돌려 축소 반례 모양 확인(30/30 실패, 한쪽이 0 근처인 쌍 5개)
