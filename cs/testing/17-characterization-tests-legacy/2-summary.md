# testing/17-characterization-tests-legacy — 레거시의 안전망: 특성 테스트·골든 마스터·이음새 찾기 — 정리 (힌트)

## 해결하는 문제

쉬운 예부터 보자.

- 배선 도면이 없는 오래된 집의 전기 공사를 맡았다.
- 먼저 스위치를 하나씩 켜 보며 "이 스위치 → 거실 등, 저 스위치 → 아무것도 안 켜짐"을 표로 적는다. 아무것도 안 켜지는 스위치가 사실은 지하실 펌프를 돌리고 있을 수도 있다.
- 공사 뒤 같은 표를 다시 확인한다. 달라진 줄이 있으면 무언가를 건드린 것이다.

똑같은 구조다.

- 명세 문서도 테스트도 없는 레거시 코드를 고쳐야 한다. 이 코드가 **원래 무엇을 해야 하는지** 아는 사람은 없다.
- 그래도 **지금 무엇을 하는지**는 실행해 보면 안다. 그것을 테스트로 적어 고정한 뒤 고친다.
  - *특성 테스트(characterization test)*: 코드가 해야 할 일이 아니라 **지금 실제로 하는 일**을 기록해, 바뀌면 알려 주는 테스트. Michael Feathers가 만든 용어다(2차 출처 Wikipedia 「Characterization test」가 WELC를 근거로 적는다).

실무 예:

- 10년 된 요금·정산 계산을 리팩터링한다. 반올림·음수·정렬 같은 문서화 안 된 동작이 고객 청구서에 그대로 나간다.
- 시스템을 새 구현으로 옮긴다([software-design/50](../../software-design/50-legacy-migration-strangler-fig/2-summary.md)). 옮기기 전에 옛 동작을 고정해 둬야 비교할 수 있다.

Feathers의 레거시 정의도 여기서 나온다.

- WELC 머리말(출판사 공개 샘플로 확인): "To me, legacy code is simply code without tests." 이유도 같은 곳에 있다 — 테스트가 있으면 동작을 빠르고 검증 가능하게 바꿀 수 있고, 없으면 코드가 나아지는지 나빠지는지 알 수 없다.

## 동작·원리

### 1. 명세 테스트와 특성 테스트는 기대값의 출처가 다르다

```text
 명세 테스트 (보통의 테스트)                 특성 테스트
 ┌────────┐   기대값                          ┌────────┐  실행    ┌──────────┐  기대값
 │  명세  │ ───────▶ assertEquals(900, …)     │  코드  │ ──────▶ │ 관찰값 -41│ ──────▶ assertEquals("S|101|-41", …)
 └────────┘                                    └────────┘         └──────────┘
  "맞는가?"를 묻는다                            "바뀌었나?"를 묻는다
```

- Feathers, "Characterization Testing"(2016-08-08 블로그): 특성 테스트의 목적은 "시스템의 실제 동작을 문서화하는 것이지, 바라는 동작을 확인하는 것이 아니다".
- 같은 글: "시스템이 운영에 들어가면, 어떤 의미에서 그 시스템이 자기 자신의 명세가 된다. 우리는 그것이 옳다고 생각하든 아니든 기존 동작을 바꾸고 있는지 알아야 한다."
- 그래서 특성 테스트는 버그도 기록한다. 버그를 고칠지는 따로 정한다. 같은 글에서 Feathers는 개발자가 버그라 여긴 동작을 사용자는 "기능"으로 여기던 사례를 든다.

### 2. 특성 테스트를 쓰는 절차

```text
 ① 코드를 테스트 하네스에 올린다 (필요하면 이음새로 의존을 끊는다)
 ② 기대값 자리에 일부러 틀린 값을 둔다:  assertEquals("?", f(x))
 ③ 돌린다 → 실패 메시지가 실제 값을 알려 준다:  expected <?> but was <S|101|-41>
 ④ 실제 값을 기대값으로 옮기고, 무엇을 알게 됐는지 테스트 이름에 적는다
 ⑤ 다음 입력으로 반복 — 바꿀 부분 근처를 집중해서
```

- ②~④는 Feathers 2016 글의 절차다. 기대값을 모르니 placeholder를 두고, 실패 메시지로 실제 동작을 배운 뒤 테스트를 고친다.
- WELC 13장 「I Need to Make a Change, but I Don't Know What Tests to Write」의 절 구성(목차로 확인): Characterization Tests · Characterizing Classes · Targeted Testing · A Heuristic for Writing Characterization Tests. 13장 본문은 공개 샘플에 없어 절 내용은 이 노트에서 단정하지 않는다.
- ⑤의 "바꿀 부분 근처를 집중"은 목차의 Targeted Testing이라는 절 제목과 위 블로그 절차에 맞춘 요약이다 [?].

### 실험 A: placeholder 기대값이 숨은 동작을 드러낸다

(실험, Maven 3.9.16 · JUnit 5.13.4 · JDK 21.0.11, `--cpus=2`, 2026-10-03)

```java
/** 레거시: 명세 문서 없음. 지금 이렇게 돈다. */
public String line(String grade, int qty, double unitPrice) {
  double total = qty * unitPrice;
  if (grade.equals("GOLD")) total = total * 0.9;
  else if (grade.equals("SILVER") && qty > 10) total = total * 0.95;
  if (qty >= 100) total -= 1000;          // 대량 할인
  return grade.charAt(0) + "|" + qty + "|" + Math.round(total);
}

@Test void silverBulk() { assertEquals("?", Invoice.of("legacy").line("SILVER", 101, 9.99)); }
```

```text
[ERROR]   CharacterizationTest.silverBulk:6 expected: <?> but was: <S|101|-41>
```

- 대량 할인이 총액보다 커서 청구액이 **음수**(-41)다. 코드를 눈으로 읽을 때는 놓치기 쉬운 동작이다.
- 특성 테스트는 이것을 `assertEquals("S|101|-41", …)`로 고정한다. 이름은 `silverBulkDiscountCanMakeTotalNegative`처럼 배운 것을 적는다. 음수가 버그인지는 업무 담당자와 따로 정한다.

### 3. 골든 마스터 — 출력 전체를 한 번에 고정

```text
 입력 조합 생성기 ──▶ 레거시 코드 ──▶ received.txt ──(사람이 검토·승인)──▶ approved.txt
                                                                            │
 리팩터링 뒤 ──▶ 새 코드 ──▶ received.txt ──── 줄 단위 diff ◀──────────────┘
                                         같으면 PASS / 다르면 FAIL + 다른 줄 목록
```

- *골든 마스터(golden master)*: 많은 입력에 대한 출력 전체를 기준 파일로 저장해 두고, 이후 출력과 비교하는 특성 테스트의 한 형태.
- *승인 테스트(approval test)*: 같은 아이디어를 라이브러리로 만든 것. ApprovalTests.Java README: 테스트가 `*.received.*` 파일을 만들고, 사람이 검토해 `*.approved.*`로 이름을 바꾸면 통과한다. approved 파일은 소스 저장소에 커밋한다.
- 손으로 고른 몇 개의 예 대신 입력 조합을 넓게 깔기 때문에, 사람이 생각하지 못한 경로까지 덮는다. 단, **깐 조합 안에서만** 덮는다(실험 B 관찰 3).

### 실험 B: 리팩터링 두 개 — 손 테스트 3개 vs 골든 마스터 105줄

(같은 환경)

- 입력: 등급 3개 × 수량 7개(0·1·10·11·99·100·101) × 단가 5개(0.5·9.99·10.0·15.5·19.99) = 105조합. 레거시 출력을 `approved.txt`로 승인했다.
- 손 테스트 3개: `G|1|900`, `S|20|1900`, `B|5|1000` — 사람이 "대표 예"로 고른 것.
- 리팩터링 A: 메서드 추출만 했다.
- 리팩터링 B: "정리하는 김에" `double`을 `BigDecimal` + `HALF_UP`로 바꾸고, 대량 할인 뒤 음수를 0으로 막았다.

```text
=== impl=refactorA
[INFO] Tests run: 1, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.269 s -- in legacy.GoldenMasterTest
[INFO] Tests run: 3, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.073 s -- in legacy.SpecExamplesTest
=== impl=refactorB
105줄 중 15줄 다름:
  - GOLD,100,0.5 -> G|100|-955
  + GOLD,100,0.5 -> G|100|0
  - GOLD,100,9.99 -> G|100|-101
  + GOLD,100,9.99 -> G|100|0
  - GOLD,100,10.0 -> G|100|-100
  + GOLD,100,10.0 -> G|100|0
  ...
[INFO] Tests run: 3, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.017 s -- in legacy.SpecExamplesTest
[ERROR] Tests run: 4, Failures: 1, Errors: 0, Skipped: 0
```

| | 손 테스트 3개 | 골든 마스터 105줄 |
|---|---|---|
| 리팩터링 A(동작 보존) | 통과 | 통과(0줄 다름) |
| 리팩터링 B(동작 변경) | **통과** | **실패 — 15줄 다름** |

- 관찰 1 — 손 테스트 3개는 동작을 바꾼 리팩터링 B를 못 잡았다. 셋 다 수량 100 미만이라 음수 경로를 안 지난다.
- 관찰 2 — 골든 마스터가 잡은 15줄은 전부 "음수 → 0" 변화였다(15줄을 따로 분류해 확인). 청구액이 음수인 경우가 운영에서 환불·상계로 쓰였다면, B는 조용한 장애가 된다.
- 관찰 3 — `double` → `BigDecimal` 반올림 변경 때문에 생긴 차이 줄은 **따로 없었다**(15줄 전부 음수 → 0). 이것은 "반올림이 같다"는 증거가 아니다. 105조합을 다시 훑어 보니(아래 출력) 총액이 정확히 .5인 입력이 17개 있었다.
  - 양수 .5 14개에서는 `Math.round`(+∞ 쪽으로 반올림, 2.5 → 3)와 `HALF_UP`(0에서 먼 쪽, 2.5 → 3)이 같은 값을 낸다.
  - 둘이 갈리는 곳은 음수 .5다. `Math.round(-949.5) = -949`, `HALF_UP`은 -950. 이런 입력 3개(SILVER,100,0.5 · SILVER,101,10.0 · BRONZE,101,0.5)는 B의 음수 방지가 0으로 덮어 "음수 → 0" 15줄 안에 묻혔다.
  - `double` 이진 표현 오차가 반올림 경계를 넘는 값(예: `1.005 * 100` = 100.49999999999999 → `Math.round` 100, 10진 100.5 `HALF_UP` 101)은 조합에 없었다.

(실험, JDK 21.0.12 temurin, 2026-10-03 — 코드 `scratchpad/ts/adj-09/e17/src/legacy/RoundProbe.java`, 같은 105조합을 레거시 `double` 계산과 B의 `BigDecimal` 계산(음수 방지 전)으로 나란히 계산, 발췌)

```text
SILVER,100,0.5  10진 총액=-952.5  double 총액=-952.5  Math.round=-952  HALF_UP(음수 방지 전)=-953  [정확히 .5] [둘이 다름]
SILVER,101,10.0  10진 총액=-40.5  double 총액=-40.5  Math.round=-40  HALF_UP(음수 방지 전)=-41  [정확히 .5] [둘이 다름]
BRONZE,101,0.5  10진 총액=-949.5  double 총액=-949.5  Math.round=-949  HALF_UP(음수 방지 전)=-950  [정확히 .5] [둘이 다름]
정확히 .5 총액 17개(그중 음수 3개) | 음수 방지 빼고 Math.round≠HALF_UP 3줄 | 실제 B 차이 15줄(그중 음수 총액 15줄)
참고(이진 표현): 1.005*100 double=100.49999999999999 → Math.round=100, 10진 100.5 HALF_UP=101
```

- 골든 마스터의 힘은 입력 조합의 폭만큼이다. 그리고 한 줄에 두 변화가 겹치면, 큰 변화(음수 → 0)가 작은 변화(반올림)를 가린다.

### 실험 C: 출력에 시각이 섞이면 — 매번 깨진다

(같은 환경)

```java
// 출력에 발행 시각이 붙는 레거시
return new Legacy().line(grade, qty, unitPrice) + "|issued=" + java.time.LocalTime.now();
// 비교 전 정규화(scrubber)
static String scrub(String s) { return s.replaceAll("issued=[0-9:.]+", "issued=<TIME>"); }
```

```text
== scrub=false (승인 직후 재실행)
GOLD,0,0.5 -> G|0|0|issued=12:45:06.517203056
[ERROR] Tests run: 1, Failures: 1, Errors: 0, Skipped: 0, Time elapsed: 0.403 s <<< FAILURE! -- in legacy.GoldenMasterTest
105줄 중 105줄 다름:
== scrub=true (승인 직후 재실행)
GOLD,0,0.5 -> G|0|0|issued=<TIME>
[INFO] Tests run: 1, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 0.351 s -- in legacy.GoldenMasterTest
```

- 승인 직후 다시 돌려도 105줄 전부 달랐다. 시각은 실행마다 다른 숨은 입력이다([09](../09-flaky-tests/2-summary.md)).
- 두 가지 처방이 있다.
  - *스크러버(scrubber)*: 비교 전에 변하는 부분을 자리표시자로 바꾼다. 코드를 안 고친다. 대신 그 부분의 동작은 검증하지 못한다.
  - *이음새(seam)*: 시계를 주입할 자리를 만들어 고정 시계를 넘긴다([10](../10-testing-time-and-concurrency/2-summary.md)). 코드를 조금 고쳐야 하지만 시각 형식까지 검증한다.

### 4. 하네스에 올리기 — 이음새 찾기

특성 테스트를 쓰려면 먼저 코드를 테스트에서 **돌릴 수 있어야** 한다. 레거시는 보통 여기서 막힌다.

```text
 class BillingJob {
   void run() {
     Database db = Database.connect();   ← 테스트에서 실제 DB에 붙는다 (분리 불가)
     ...계산...
     mailer.send(report);                ← 결과를 밖으로 보내 버린다 (감지 불가)
   }
 }
```

- *이음새(seam)*: WELC 4장 정의 — "그 자리를 편집하지 않고도 프로그램의 동작을 바꿀 수 있는 곳". SWE@G 13장 「Seams」도 같은 뜻으로 "테스트 더블을 쓸 수 있게 해 코드를 테스트 가능하게 하는 방법"이라 적고, 의존성 주입을 흔한 기법으로 든다.
- 테스트 관점에서 이음새가 필요한 이유는 두 가지다.
  - **분리**: 하네스에서 아예 돌릴 수 없는 의존(실제 DB·네트워크)을 갈아 끼운다.
  - **감지**: 코드가 계산한 값이 밖으로 나가 버려 볼 수 없을 때(메일 전송), 가짜를 끼워 그 값을 붙잡는다.
  - 이 두 이유는 WELC 3장 제목(Sensing and Separation)과 같다. 3장 본문은 공개 샘플에 없어, 위 풀이는 이 노트의 요약이다 [?].
- seam 종류(preprocessing·link·object)와 enabling point, 의존 끊기 기법(인터페이스 추출·매개변수화·sprout·wrap)은 [software-design/51](../../software-design/51-legacy-change-techniques/2-summary.md)에 있다. 이 노트는 **테스트를 어디에 걸지**만 다룬다.

### 5. 테스트를 어디에 거나 — 변경 효과가 모이는 지점

```text
 바꿀 메서드 ──▶ 영향받는 값들 ──▶ … ──▶ ★ 모이는 지점(공개 메서드 하나) ──▶ 출력
               (효과 스케치)                 여기에 특성 테스트를 걸면
                                             안쪽 여러 메서드의 변화를 한 번에 감지
```

- WELC 11장(효과 추론, 「Effect Propagation」·「Tools for Effect Reasoning」)과 12장(「Interception Points」·「Judging Design with Pinch Points」)이 이 주제다(목차로 확인, 본문 미열람).
- 이 노트의 요약 [?]: 바꿀 코드에서 효과가 퍼지는 경로를 그려 보고(효과 스케치), 그 효과가 관찰 가능한 곳 중 바꿀 곳에 가까운 지점에 테스트를 건다. 여러 경로가 한 곳으로 모이는 좁은 지점이 있으면, 거기 몇 개의 테스트로 넓은 변경을 감지할 수 있다.
- 실험 B의 `line(…)`이 그런 지점이다. 할인·대량 할인·반올림 세 부분의 변화가 모두 한 줄 출력으로 모인다.

## 쓰이는 자료구조·알고리즘

- **입력 조합 = 곱집합**: 조합 수는 각 차원 크기의 곱이다(3×7×5 = 105). 차원이 늘면 폭발하므로 각 차원은 경계값·동치 분할로 고른다([07](../07-test-design-techniques/2-summary.md)). 실험 B의 수량 0·1·10·11·99·100·101은 `> 10`·`>= 100` 경계 양쪽이다.
- **줄 단위 diff**: approved와 received를 줄 단위로 비교한다. 실험은 같은 줄 번호끼리 비교했다. 줄 수가 달라지는 출력에는 최장 공통 부분열(LCS) 기반 diff가 맞다.
- **정규화(스크러빙)**: 정규식 치환으로 변하는 필드를 자리표시자로 바꾼다. 비교 전 단계의 사상(map)이다.
- **효과 스케치 = 의존 그래프**: 노드는 변수·메서드, 간선은 "값이 영향을 줌"이다. 변경의 영향 범위는 바꾼 노드에서 도달 가능한 노드 집합(그래프 탐색)이다. 여러 경로가 거쳐 가는 좁은 지점은 그래프의 병목이다(해석: 이 그래프 용어로의 대응은 이 노트의 정리다).

## 적용 — 풀어나가는 법

### 1. 순서

1. **바꿀 지점을 정한다.** 이번 변경이 건드릴 메서드·분기.
2. **테스트 지점을 고른다.** 바꿀 지점의 효과가 관찰되는, 가까운 공개 메서드·출력.
3. **하네스에 올린다.** 막히면 이음새를 만든다(생성자 주입, 팩토리 메서드 추출 — 51번).
4. **특성 테스트를 쓴다.** placeholder → 실패 메시지 → 기대값. 바꿀 부분 근처의 경계 입력을 집중해서.
5. **넓게 필요하면 골든 마스터.** 입력 조합 생성 → 승인 → 커밋.
6. **변경한다.** 작은 단계마다 돌린다([software-design/13](../../software-design/13-refactoring/2-summary.md)).
7. **의도한 변화만 승인한다.** diff를 읽고 의도한 줄만 바뀌었는지 확인한 뒤 approved를 갱신한다. 동작 보존 커밋과 동작 변경 커밋을 나눈다.
8. **이해가 쌓이면 명세 테스트로 바꾼다.** 골든 마스터는 비계(scaffolding)다. 동작을 이해한 부분은 이름 있는 명세 테스트로 옮긴다.

### 2. 코드 — JUnit 5로 쓰는 작은 골든 마스터

```java
@Test void invoiceLinesMatchApproved() throws Exception {
  List<String> out = new ArrayList<>();
  for (String g : List.of("GOLD", "SILVER", "BRONZE"))
    for (int q : new int[]{0, 1, 10, 11, 99, 100, 101})          // 경계 양쪽
      for (double p : new double[]{0.5, 9.99, 10.0, 15.5, 19.99})
        out.add(scrub(g + "," + q + "," + p + " -> " + invoice.line(g, q, p)));
  Path approved = Path.of("src/test/resources/invoice.approved.txt");
  Files.write(Path.of("target/invoice.received.txt"), out);     // 검토용
  assertThat(out).containsExactlyElementsOf(Files.readAllLines(approved));
}
```

- ApprovalTests.Java를 쓰면 received/approved 파일 관리와 diff 도구 연결을 라이브러리가 맡는다(README의 `Approvals.verifyAll("", names)` 예).

### 3. 진단 — 골든 마스터가 충분히 넓은가

- 골든 마스터를 돌린 상태에서 커버리지를 본다. 바꿀 메서드의 분기가 덮이지 않았으면 입력 조합을 늘린다([16-coverage-and-its-limits](../16-coverage-and-its-limits/2-summary.md)).
- 더 엄격하게는 바꿀 코드에 일부러 작은 변화를 넣어(연산자 바꾸기 등) 골든 마스터가 잡는지 본다. 변이 테스트의 생각이다([15-mutation-testing](../15-mutation-testing/2-summary.md)). 실험 B 관찰 3처럼 잡지 못하는 변화가 있으면 그 경로의 입력을 추가한다.

## 장애 시나리오와 대처

### 1. 안전망 없이 레거시 수정 → 숨은 동작 파손 (⚠ 커리큘럼)

- 현상: "정리만 했다"는 배포 뒤, 일부 고객 청구액이 달라졌다.
- 보이는 형태: 대량 주문 고객의 청구액이 음수에서 0으로 바뀌어 상계·환불 처리가 빠진다. 테스트는 초록이었다.
- 원인: 손으로 고른 대표 예 몇 개만 있었고, 숨은 경로(음수 청구)를 지나는 입력이 없었다(실험 B: 손 테스트 3개 통과, 골든 마스터 15줄 실패).
- 대처: 변경 전에 바꿀 부분 근처를 특성 테스트·골든 마스터로 고정한다. 동작 보존 리팩터링과 동작 변경을 다른 커밋으로 나눈다.

### 2. 골든 마스터가 매번 깨진다

- 현상: 승인 직후 다시 돌려도 실패한다. 팀이 골든 마스터를 꺼 버린다.
- 보이는 형태: diff의 모든 줄이 시각·UUID·난수·해시 순서 부분만 다르다(실험 C: 105줄 중 105줄).
- 원인: 출력에 실행마다 바뀌는 숨은 입력이 섞였다.
- 대처: 시계·난수는 이음새로 고정하거나, 비교 전 스크러버로 정규화한다. 해시 순서는 정렬 후 기록한다.

### 3. 버그를 정답으로 고정했다

- 현상: 특성 테스트가 명백한 버그(예: 음수 청구)를 기대값으로 지키고 있다. 버그를 고치는 PR이 테스트에 막힌다.
- 보이는 형태: 수정 PR의 리뷰에서 "테스트가 실패하니 되돌려라"는 의견이 나온다.
- 원인: 특성 테스트는 원래 현재 동작을 기록한다. 버그도 기록된다.
- 대처: 버그 수정은 별도 결정으로 한다. 사용자가 그 동작에 기대고 있는지 확인한다(Feathers 2016: 버그를 기능으로 여긴 사용자 사례). 고치기로 하면 그 테스트를 의도적으로 갱신하고, 커밋 메시지에 동작 변경을 적는다.

### 4. 승인 피로 — diff를 읽지 않고 승인한다

- 현상: 리팩터링마다 골든 마스터 diff가 수백 줄이다. 개발자가 received를 통째로 approved로 덮는다.
- 보이는 형태: approved 파일의 대량 변경 커밋이 "update approved" 한 줄 메시지로 들어간다.
- 원인: 변경 단계가 크거나, 동작 보존과 동작 변경을 한 번에 했다.
- 대처: 작은 단계로 나눠 동작 보존 단계에서는 diff가 0줄이어야 한다. 동작 변경 단계의 diff만 읽고 승인한다. 출력 형식을 줄 단위로 의미 있게 만들어 diff를 읽기 쉽게 한다.

### 5. 입력 조합이 좁아 변화를 놓친다

- 현상: 골든 마스터가 초록인데 운영에서 반올림 차이가 났다.
- 보이는 형태: 특정 금액에서만 1원 차이 — 예: 음수 반값(환불 -40.5원), 또는 `double` 표현 오차가 반올림 경계를 넘는 금액(x.xx5).
- 원인: 실험 B 관찰 3처럼, 변화가 드러나는 입력이 조합에 없었거나 다른 변화에 가려졌다.
- 대처: 바꾸는 부분의 경계(.5 근처, 0, 음수, 최댓값)를 입력 차원에 추가한다. 커버리지·변이로 골든 마스터의 폭을 점검한다.

## 핵심 문장

- 특성 테스트는 코드가 해야 할 일이 아니라 지금 하는 일을 기록해, "맞는가"가 아니라 "바뀌었나"를 묻는다.
- 기대값을 모르면 일부러 틀린 값을 넣고, 실패 메시지가 알려 주는 실제 값을 기대값으로 옮긴다.
- 골든 마스터는 넓은 입력 조합의 출력 전체를 고정해, 손으로 고른 예가 놓친 숨은 경로의 변화를 잡는다. 단, 깐 조합 안에서만 잡는다.
- 출력에 시각·난수가 섞이면 이음새로 고정하거나 스크러버로 정규화해야 골든 마스터가 쓸모 있다.
- 레거시를 하네스에 올리려면 의존을 분리하고 결과를 감지할 이음새가 필요하고, 테스트는 변경 효과가 모이는 가까운 지점에 건다.

## 관련 주제·근거

- 선행·연결
  - [07-test-design-techniques](../07-test-design-techniques/2-summary.md) — 입력 조합을 경계값·동치 분할로 고르기
  - [software-design/13-refactoring](../../software-design/13-refactoring/2-summary.md) — 동작 보존 변환, 테스트 안전망
  - [software-design/51-legacy-change-techniques](../../software-design/51-legacy-change-techniques/2-summary.md) — seam 종류·enabling point·sprout/wrap·의존 끊기(변경 기법)
  - [software-design/50-legacy-migration-strangler-fig](../../software-design/50-legacy-migration-strangler-fig/2-summary.md) — 시스템 단위의 병행 실행·결과 비교
  - [09-flaky-tests](../09-flaky-tests/2-summary.md) · [10-testing-time-and-concurrency](../10-testing-time-and-concurrency/2-summary.md) — 출력의 숨은 입력(시각)
  - [15-mutation-testing](../15-mutation-testing/2-summary.md) — 골든 마스터의 판별력 점검
  - [16-coverage-and-its-limits](../16-coverage-and-its-limits/2-summary.md) — 골든 마스터의 폭 점검
- 교재·문서
  - Michael Feathers, 『Working Effectively with Legacy Code』, Prentice Hall, 2004 — 출판사 공개 샘플(목차·머리말·1장·4장·색인)로 확인: 레거시 = 테스트 없는 코드(머리말), seam 정의(4장), 11장 효과 추론·12장 Interception Points·Pinch Points·13장 Characterization Tests 절 구성(목차). 2·3·11·12·13장 본문은 미열람 <https://ptgmedia.pearsoncmg.com/images/9780131177055/samplepages/0131177052.pdf>
  - Michael Feathers, "Characterization Testing", 2016-08-08 <https://michaelfeathers.silvrback.com/characterization-testing>
  - Wikipedia 「Characterization test」(2차 출처 — 용어를 Feathers가 만들었다는 서술) <https://en.wikipedia.org/wiki/Characterization_test>
  - ApprovalTests.Java README(received/approved 파일, approved 커밋) <https://github.com/approvals/ApprovalTests.Java>
  - 『Software Engineering at Google』 13장 「Test Doubles」 — Seams <https://abseil.io/resources/swe-book/html/ch13.html>
- 실험 목록(코드: `scratchpad/ts/09/e17/` — `src/main/java/legacy/Invoice.java`, `src/test/java/legacy/{CharacterizationTest,GoldenMasterTest,SpecExamplesTest}.java`, maven:3.9-eclipse-temurin-21(Maven 3.9.16, JDK 21.0.11), JUnit 5.13.4·surefire 3.5.3, `--cpus=2`, 2026-10-03)
  - A — placeholder 기대값. `mvn test` → `expected: <?> but was: <S|101|-41>`.
  - B — 골든 마스터 105조합. 레거시 출력 승인 후 `mvn test -Dimpl=refactorA|refactorB -Dtest='GoldenMasterTest,SpecExamplesTest'` → A 0줄, B 15줄 다름(전부 음수→0), 손 테스트 3개는 둘 다 통과.
  - B' — 반올림 재검(`scratchpad/ts/adj-09/e17/src/legacy/RoundProbe.java`, `javac` + `java`, eclipse-temurin:21-jdk JDK 21.0.12): 정확히 .5 총액 17개(음수 3개), 음수 방지를 빼면 `Math.round`≠`HALF_UP` 3줄(전부 음수 .5), 실제 B 차이 15줄 전부 음수.
  - C — 출력에 시각. `-Dimpl=stamped -Dscrub=false|true -Dapproved=approved-s.txt` → 105줄 중 105줄 다름 / 스크러버 적용 시 통과.
