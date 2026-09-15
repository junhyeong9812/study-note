# domain-modeling-basic/22-settlement — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 작성 방식: **2-summary를 닫고 기억만으로** 쓴다 → 실제 코드/원전으로 검증 → 틀린 부분만 수정.
> 기준 소스는 문서가 아니라 코드다 (`/home/jun/project/myway/domain-modeling-basic/22-settlement/impl/`).

⚠️ 정답은 Claude 초안(2026-09-15) — 원본 impl 코드·README 측정 기준. 본인 검토 후 이 줄 삭제

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. -->

### A. 과제 (Settlement.java 의 TODO 1~4)

#### 0. 한 줄 요구사항 — 안 들어 있는 결정

```text
  적혀 있는 것                     적혀 있지 않은 것 (= 내가 정해야 하는 것)
  ──────────────────────────────   ─────────────────────────────────────────
  10,000 을 셋이 나누면 1 원 남는다  "원 단위로 끊는다"가 내림인가 반올림인가?
  그 1 원을 누가 갖나 (선택지 4)     비중 합이 100이어야 하나?
  최대 잔여법이 가장 공평하다        버려진 소수가 같을 때(동점) 누가 먼저인가?
                                   잔돈이 2 원 이상이면 한 명이 다 갖나 나눠 갖나?
                                   규칙을 코드에 고정하나 호출자가 고르나?
```

- **내림인가 반올림인가**: 요구사항엔 "원 단위로 끊으면"이라고만 적혀 있다. impl은 `RoundingMode.DOWN`(내림)이고, 그 이유가 README 함정 첫 줄에 있다.
- **내림/반올림이 먼저인 이유**: 잔돈의 **부호**가 여기서 결정되기 때문이다. 내림이면 잔돈은 항상 0 이상이라 "누구에게 더 줄까"만 정하면 되지만, 반올림이면 잔돈이 음수가 될 수 있어 "누구에게서 뺄까"라는 완전히 다른 문제가 생긴다. 잔돈 규칙 네 개는 전부 "준다"는 전제 위에 있다.
- **비중 합 100**: 요구사항에 없다. impl은 `totalWeight()`로 합을 구해 나누므로 1:2:4든 10:20:40이든 같은 답이 나온다(`weighted` 테스트가 못 박음).
- **동점 처리**: 요구사항에 없다 — 그리고 이것이 측정 셋(최대 잔여법에도 편향이 남는다)의 원인이다.
- **규칙을 밖으로 꺼낸 이유**: 어느 규칙도 정답이 아니기 때문이다. 쉬움(FIRST) / 비례(LARGEST_REMAINDER) / 합계 보존(DROP만 어김) 사이의 업무 트레이드오프라서, 코드에 숨기지 않고 `enum RemainderRule`로 이름 붙여 호출자가 고르게 했다.
- **잔돈 2원 이상**: 1원 예시에는 안 드러난다. 10,001÷3이면 잔돈이 2원이고, 그때 비로소 FIRST(한 명이 2원)와 최대 잔여법(두 명이 1원씩)이 갈린다.

#### 1. TODO 1 — distribute

```java
if (total < 0) {
    throw new IllegalArgumentException("총액이 음수다: " + total);
}
if (shares.isEmpty()) {
    throw new IllegalArgumentException("배분 대상이 없다");
}
long totalWeight = totalWeight(shares);

Map<String, Long> result = new LinkedHashMap<>();
List<BigDecimal> fractions = new ArrayList<>();
long assigned = 0;
for (Share share : shares) {
    BigDecimal exact = BigDecimal.valueOf(total)
            .multiply(BigDecimal.valueOf(share.weight()))
            .divide(BigDecimal.valueOf(totalWeight), 10, RoundingMode.DOWN);
    long floor = exact.setScale(0, RoundingMode.DOWN).longValue();
    result.put(share.party(), floor);
    fractions.add(exact.subtract(BigDecimal.valueOf(floor)));   // 버려진 소수를 기억
    assigned += floor;
}

long remainder = total - assigned;
if (rule == RemainderRule.DROP) {
    return result;
}
// 잔돈이 0 이어도 그냥 넘긴다.
return giveRemainder(result, shares, fractions, remainder, rule);
```

- 정확한 몫 = **총액 × 자기 비중 ÷ 비중 합** (소수 10자리까지, 내림).
- 반올림이면 잔돈이 음수가 되는 예:

```text
  5 원을 둘이 똑같이 (비중 1:1)
    정확한 몫  2.5   2.5
    반올림     3     3     = 6  →  잔돈 = 5 - 6 = -1 원  (총액을 넘었다)
    내림       2     2     = 4  →  잔돈 = +1 원          (절대 안 넘는다)
```

- 잔돈이 음수면: 누군가에게서 **1원을 빼야** 한다. "더 줄 사람 고르기"가 "뺏을 사람 고르기"로 바뀌고, 이미 지급했다면 환수가 된다.
- 함께 기억할 값: **버려진 소수(`fractions`)** — 최대 잔여법이 이걸로 순서를 정한다. 내림만 하고 버리면 다시 계산해야 한다.
- 잔돈 = **총액 − 내림 몫의 합**(`total - assigned`).
- `LinkedHashMap`인 이유: **입력 순서를 보존**해야 FIRST 규칙의 "첫 번째"와 동점 인덱스 순서가 의미를 갖는다. 보통 `HashMap`은 순서가 뒤섞여 결과가 입력 순서와 무관해진다.
- 거부 입력: **음수 총액**과 **빈 목록**. (비중 0 이하와 빈 이름은 `Share` 생성자가 막는다.)
- `remainder == 0` 분기를 따로 두면: 그 분기를 **지워도 아무 테스트가 안 깨진다.** 잔돈 0이면 FIRST/LARGEST는 0을 더하고 최대 잔여법은 루프가 안 도니 결과가 같기 때문이다 — 의미 없는 분기라 원본은 지웠다(README "변종 검증에서 고친 것").
- DROP만 잔돈 함수를 안 부르는 이유: DROP은 정의상 **아무에게도 안 준다**. 이 규칙만 `sumOf != total`이 되고, 그 사실을 드러내려고 선택지로 남겨 뒀다.

#### 2. TODO 2 — giveRemainder

```java
if (rule == RemainderRule.FIRST) {
    String party = shares.get(0).party();
    result.put(party, result.get(party) + remainder);      // 한 명이 전부
    return result;
}
if (rule == RemainderRule.LARGEST) {
    Share largest = shares.stream()
            .max(Comparator.comparingLong(Share::weight))  // 기준은 "비중"
            .orElseThrow();
    result.put(largest.party(), result.get(largest.party()) + remainder);
    return result;
}
// 최대 잔여법. 버려진 소수가 큰 순서로 1 원씩.
List<Integer> order = new ArrayList<>();
for (int i = 0; i < shares.size(); i++) {
    order.add(i);
}
order.sort(Comparator
        .comparing((Integer i) -> fractions.get(i)).reversed()   // 소수 내림차순
        .thenComparingInt(i -> i));                              // 동점이면 앞 인덱스
for (int i = 0; i < remainder; i++) {
    String party = shares.get(order.get((int) (i % shares.size()))).party();
    result.put(party, result.get(party) + 1);                    // 1 원씩
}
return result;
```

- FIRST는 잔돈 2원을 **한 명이 다** 갖는다 (10,001÷3 → 3,335 / 3,333 / 3,333).
- LARGEST의 "가장 큰"은 **비중**이다(`Comparator.comparingLong(Share::weight)`). 내림 몫이 아니다 — 다만 비중이 크면 몫도 크므로 대개 같은 사람이다.
- 비중이 고정이면 LARGEST ≈ FIRST인 이유: 비중이 안 바뀌면 **매 회차 같은 사람이 최대**다. "매번 같은 사람이 잔돈을 갖는다"는 성질이 똑같으므로 편향도 똑같이 쌓인다.
- 최대 잔여법은 **버려진 소수를 내림차순**으로 정렬한다.
- 잔돈은 **1원씩** 순서대로 나눠 준다 — 한 명이 몰아 갖지 않는다.
- 동점이면 **앞 인덱스 먼저**(`thenComparingInt(i -> i)`). 이 줄이 없어도 지금 결과가 같은 이유는 자바 `List.sort`가 **안정 정렬**이라 같은 값끼리 원래 순서가 유지되기 때문이다. 결함은 아니지만 **정렬 구현에 기대지 않으려고** 명시해 뒀다.
- `fractions`를 넘겨받는 이유: 여기서 다시 계산하면 `distribute`의 나눗셈 설정(스케일 10·DOWN)을 **두 곳에서 똑같이 유지**해야 한다. 한쪽만 고치면 정렬 순서가 조용히 달라진다.

손계산 — 100원을 1:2:4(합 7)로:

```text
  정확한 몫   A 14.2857142857   B 28.5714285714   C 57.1428571428
  내림        A 14              B 28              C 57      = 99,  잔돈 1 원
  버려진 소수   .2857             .5714             .1428

  FIRST              A 가 1 원   →  15 / 28 / 57
  LARGEST(비중 4=C)  C 가 1 원   →  14 / 28 / 58
  최대 잔여법(.5714 최대 = B)     →  14 / 29 / 57
```

#### 3. TODO 3 — totalWeight

```java
long sum = 0;
for (Share share : shares) {
    sum += share.weight();
}
return sum;
```

- `long`인 이유: `Share.weight`가 `long`이고 참여자가 많으면 합이 `int` 범위를 넘을 수 있다. 그리고 `총액 × 비중`을 다룰 때 같은 폭을 유지해야 중간에 넘치지 않는다.
- 1:2:4와 10:20:40이 같은 답인 이유: 정확한 몫이 `총액 × w / Σw`인데, 모든 비중을 10배 하면 분자와 분모가 **똑같이 10배**가 되어 값이 변하지 않는다.

```text
  1:2:4  →  100 × 2 / 7  = 28.571...
  10:20:40 → 100 × 20 / 70 = 28.571...   같다
```

#### 4. TODO 4 — deviationFromExact

```java
long totalWeight = totalWeight(shares);
Map<String, BigDecimal> deviation = new LinkedHashMap<>();
for (Share share : shares) {
    BigDecimal exact = BigDecimal.valueOf(total)
            .multiply(BigDecimal.valueOf(share.weight()))
            .divide(BigDecimal.valueOf(totalWeight), 10, RoundingMode.HALF_UP);
    deviation.put(
            share.party(),
            BigDecimal.valueOf(distribution.get(share.party())).subtract(exact));
}
return deviation;
```

- **실제로 받은 금액 − 이상적인(소수 그대로의) 몫**. 양수면 더 받은 것이다.
- `BigDecimal`인 이유: 이상적인 몫이 **소수**(3,333.3333…)라서 정수로는 차이를 표현할 수 없다. 그리고 그 차이가 1원 미만 단위로 쌓이는 것을 재는 게 목적이라 오차가 있으면 안 된다.
- 이 함수 없이는 측정 셋을 못 재는 이유: 편향은 "받은 금액"이 아니라 **"받은 금액과 받았어야 할 금액의 차이"**가 쌓인 것이다. 365회를 더해야 A +266 / B −133 같은 수가 나온다.
- 스케일 10에서 DOWN(배분)과 HALF_UP(편차)의 차이: 소수 **11번째 자리 이하**에서만 갈리므로 실질 차이가 없다. 배분 쪽은 "내림이 계약"이라 DOWN을 쓰고, 편차 쪽은 "이상적인 값에 가장 가깝게"가 목적이라 HALF_UP을 썼다. (원본이 그 이유를 적어 두진 않았다 — 내 추론.)

### B. 개념

#### 5. 잔돈은 예외가 아니라 일상이다 (측정 하나)

- 무작위 10,000건 중 **7,743건**에서 잔돈이 남는다(버려진 금액 합 21,289원 — MeasurementTest).
- 딱 떨어지는 경우는 **23퍼센트**뿐.
- 위험한 이유: 예제는 대개 딱 떨어지게 만드는데, 그 23%짜리 세계에서는 **네 규칙이 전부 같은 답**을 낸다. 규칙을 안 정해도 예제가 다 통과하고, 77%짜리 현실은 운영에서 처음 만난다.

#### 6. 1원이 쌓인다 (측정 둘)

```text
  똑같이 나누는 셋에게 365 일 정산
                A            B            C
  FIRST       66,135,650   66,135,251   66,135,251     ← A 가 399 원 더
  최대 잔여법  66,135,519   66,135,382   66,135,251
```

- FIRST에서 A는 B보다 **399원** 더 받는다.
- 참여자가 100명이면 그 수가 **100배**가 된다(한 번의 잔돈이 최대 99원까지 커지므로).
- 최대 잔여법으로 바꾸면 A−C가 **268원**, A−B가 **137원** — 쏠림이 줄지만 사라지지는 않는다.

#### 7. 가장 공평한 규칙에도 편향이 남는다 (측정 셋)

```text
  365 일 누적 편차 (이상적 몫과의 차이)
                 A       B       C
  FIRST        +266    -133    -133
  최대 잔여법   +135      -2    -133
```

- 최대 잔여법의 편향이 0이 아닌 이유: **똑같이 나누면 버려진 소수가 셋 다 같다.** 그러면 정렬이 아무것도 못 하고 동점을 **인덱스 순서**로 끊게 되어, 앞쪽(A)이 계속 먼저 받는다.
- 없애려면: **회차마다 순서를 돌려야** 한다(round-robin). 즉 "누가 먼저였는지"를 회차 밖에 기억해야 한다.

#### 8. 참여자가 많을수록 잔돈이 크다 (측정 넷)

```text
  참여자 │ 잔돈이 생긴 건 (2,000 중) │ 잔돈 합
  ───────┼──────────────────────────┼──────────
    2    │        1,085             │   1,085
    3    │        1,417             │   1,958
   10    │        1,763             │   8,558
  100    │        1,971             │  97,474
```

- 100명이면 한 번에 **99원까지** 남는다.
- 불변식이 성립하는 이유: 각자 내림을 하므로 **각자 버리는 양이 1원 미만**이다. n명이면 버려진 합 < n × 1원 = n원 — 즉 잔돈은 언제나 참여자 수보다 작다. (그리고 내림이라 음수도 아니다.)

#### 9. 딱 떨어지는 예제의 함정 (측정 다섯 + 변종 검증)

- 9,000÷3, 10,000÷4, 12,000÷6 — **네 규칙이 전부 같은 답**을 낸다(잔돈이 0이라 잔돈 코드가 아예 안 갈린다).
- "규칙을 안 정해도 예제가 다 통과한다": 잔돈 규칙을 아무거나 넣어도, 심지어 DROP으로 둬도 딱 떨어지는 예제에서는 테스트가 초록색이다. **결함이 테스트를 통과한다.**
- 균등 비중만 쓰면: 버려진 소수가 셋 다 같아서 최대 잔여법의 **정렬이 아무 일도 안 한다** — 정렬 방향을 뒤집어도 결과가 같다.
- 1:2:4로 바꾸면 소수가 `.2857 / .5714 / .1428`로 갈려서 ①**정렬을 뒤집는 변종** ②**소수를 안 남기는(fractions를 안 모으는) 변종** 둘이 잡힌다.
- `remainder == 0` 분기를 지운 이유: 1번 답 참조 — 0을 더하거나 루프가 안 돌 뿐이라 **의미가 없는 분기**였다(지워도 테스트가 안 깨지는 코드는 없는 게 낫다).
- 동점 처리를 지운 변종이 결함이 아닌 이유: 자바 정렬이 **안정적**이라 결과가 같다. 그래도 명시한 이유는 **정렬 구현에 기대고 싶지 않아서** — 언어/라이브러리가 바뀌면 조용히 달라질 수 있는 종류의 의존이다.

#### 10. 생각해볼 것 (원본 README — 답이 적혀 있지 않다. 아래는 내 추론)

- **순서 돌리기**: 편향은 사라진다(모두가 돌아가며 먼저 받으므로 장기적으로 0에 수렴). 대신 "다음 차례가 누구인지"가 **정산 회차 밖의 상태**가 된다 — 참여자 목록과 함께 저장해야 하고, 재실행·롤백 시 그 상태도 함께 되돌려야 한다. 상태 없이 하려면 회차 번호를 시드로 써서 `순서 = (인덱스 + 회차) % n` 같은 결정적 규칙을 쓰는 방법이 있다.
- **참여자 추가**: 인덱스 기반 순서가 통째로 밀린다. 누적 편차를 참여자별로 들고 있다가 **편차가 가장 음수인 쪽에 먼저 주는** 방식으로 바꾸면 인원이 바뀌어도 이어갈 수 있다.
- **회사가 잔돈을 갖는 것**: 회계는 닫힌다(잔돈도 어딘가로 갔으니까). 다만 그것은 **수익**이라서 그렇게 회계 처리하고 고지해야 한다. 규모는 측정 넷 기준으로 2,000건·100명에서 97,474원 — 작지 않다.
- **17번 할인 배분과 규칙이 다르면**: 같은 금액을 두 곳에서 다르게 쪼개게 되어 **주문 합계와 품목별 합계가 안 맞는다.** 환불 때 특히 드러난다 — 할인은 최대 잔여법으로 쪼갰는데 정산은 FIRST로 쪼개면 품목별 환불액 합이 원래 결제액과 1원씩 어긋난다.

## 근거

- 기준 소스: `/home/jun/project/myway/domain-modeling-basic/22-settlement/impl/com/domain/settlement/Settlement.java`
- 문제 원문: `src/main/java/com/domain/settlement/Settlement.java`(TODO 1~4), `Share.java`(계약), `README.md`
- 측정 수치: `README.md` "측정이 알려준 것" 하나~다섯 + "변종 검증에서 고친 것", `src/test/java/com/domain/settlement/MeasurementTest.java`
- 계약 테스트: `src/test/java/com/domain/settlement/SettlementTest.java`
