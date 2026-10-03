# testing/16-coverage-and-its-limits — 커버리지: 라인·분기·조건의 의미와 한계 — 정리 (힌트)

## 해결하는 문제

테스트를 아무리 많이 써도 **어느 코드를 한 번도 실행하지 않았는지**는 눈으로 알기 어렵다. 커버리지는 그 빈칸을 보여 준다. 대신 "실행했다"와 "검증했다"를 구별하지 못한다.

```text
  커버리지가 답하는 질문        커버리지가 답하지 못하는 질문
  ─────────────────────        ──────────────────────────────
  이 줄이 실행됐나?            실행 결과를 단언했나?
  이 if의 참·거짓 둘 다?       경계값(100000 vs 99999)을 시험했나?
                               명세에 있는데 코드에 없는 기능은?
```

- *코드 커버리지*: 테스트가 실행한 코드의 비율. 무엇을 단위로 세느냐(명령·줄·분기·조건)에 따라 종류가 갈린다.
- SWE@G 11장 "A Note on Code Coverage": 커버리지는 줄이 호출됐는지만 재고 그 결과로 무슨 일이 일어났는지는 재지 않는다. 다른 지표처럼 금방 목표 자체가 되며, 80%를 바닥이 아닌 천장처럼 다루게 된다고 쓴다.

쉬운 예: 시험 범위 체크리스트다.
- "교과서 모든 쪽을 한 번 펼쳤다"(커버리지 100%)와 "문제를 풀 수 있다"(검증)는 다르다. 그래도 펼쳐 보지 않은 쪽이 어디인지는 확실히 알려 준다.

똑같은 구조다.\
커버리지 낮음 → "여기는 테스트가 안 닿는다"는 **확실한 신호**다. 커버리지 높음 → "잘 테스트됐다"는 **증거가 아니다**.

실무 예:
- 커버리지 80% 게이트를 맞추려고 단언 없는 테스트를 붙여, 수치는 올랐는데 버그는 그대로 나갔다.
- 라인 커버리지는 100%인데 `if (vip && amount >= 100_000)`의 "VIP인데 10만 원 미만" 경로를 아무도 시험하지 않았다.

## 동작·원리

### 1. 제어 흐름 그래프 — 무엇을 세는가

```java
 5    public static int discountedPrice(int amount, boolean vip) {
 6        if (amount < 0) throw new IllegalArgumentException("negative: " + amount);
 7        if (vip && amount >= 100_000) return amount - amount / 10;
 8        if (amount >= 50_000) return amount - amount / 20;
 9        return amount;
10    }
```

```text
          [시작]
            │
        (amount < 0)? ──T──▶ [throw]
            │F
          (vip)? ──F──────────────┐
            │T                    │
     (amount >= 100000)? ──F──────┤
            │T                    ▼
     [return 10% 할인]     (amount >= 50000)? ──T──▶ [return 5% 할인]
                                  │F
                             [return amount]

  결정점 4개 × (T, F) = 분기 8개
```

- *제어 흐름 그래프(CFG)*: 실행 가능한 문장 묶음을 노드로, 실행 순서의 이동을 간선으로 그린 그래프. *분기*는 노드 사이의 제어 이동이다(ISTQB CTFL 4.0 4.3.2).
- 커버리지 종류
  - *문장(라인) 커버리지*: 실행된 문장(줄)의 비율. 100%여도 분기가 다 실행됐다는 보장은 없다(4.3.1).
  - *분기 커버리지*: 실행된 분기의 비율. 분기 100%는 문장 100%를 포함한다(역은 아니다)(4.3.2).
  - *조건 커버리지*: `vip && amount >= 100000`처럼 결정 안의 개별 조건이 각각 참·거짓을 한 번씩 갖는지.
  - *MC/DC*: 각 조건이 결정 결과에 **독립적으로** 영향을 주는 것을 보이는 기준. 입력 n개 결정에 일반적으로 최소 n+1개 테스트가 필요하다. 모든 조합(다중 조건 커버리지)은 2^n개다(NASA/TM-2001-210876). 항공 소프트웨어 DO-178B Level A가 요구하는 기준이다(같은 문서).
  - *경로 커버리지*: 시작에서 끝까지의 경로 전부. 루프가 있으면 경로 수가 무한해질 수 있어 실무 지표로는 잘 쓰지 않는다.

### 2. JaCoCo는 무엇을 세나 (JaCoCo 문서 "Coverage Counters")

- *명령(instruction)*: 가장 작은 단위. 자바 바이트코드 명령 하나.
- *분기(branch)*: `if`·`switch`의 분기. **바이트코드 기준**으로 센다. `vip && amount >= 100_000`은 조건부 점프 2개로 컴파일되므로 분기 4개다 — 그래서 JaCoCo 분기는 `&&`·`||`의 개별 조건까지 나눠 세는 효과가 있다.
- *줄(line)*: 줄의 명령이 전부 실행되면 완전, 일부만이면 부분, 하나도 안 되면 미실행.
- 예외 처리는 분기로 세지 않는다. `try/catch`는 복잡도도 늘리지 않는다.
- *순환 복잡도*: `v(G) = B − D + 1`(B = 분기 수, D = 결정점 수). 메서드의 모든 경로를 선형 결합으로 만들 수 있는 최소 경로 수다(→ [software-design/52-complexity-metrics](../../software-design/52-complexity-metrics/2-summary.md)).
- 계측 방식(JaCoCo 문서 "Control flow analysis"): 메서드 출구와 "여러 간선이 모이는 명령"으로 가는 간선에 프로브를 꽂고, 클래스마다 `boolean[]` 배열에 실행 여부를 기록한다. 문서는 클래스 크기 약 30% 증가, 실행 시간 오버헤드는 대개 10% 미만이라고 쓴다.
- 필터: JaCoCo 0.8.0부터 인자 없는 빈 private 생성자 등을 보고서에서 뺀다(changes 문서).

### 실험: 같은 코드, 네 스위트 — 커버리지 vs 변이 점수

- NoAssertTest: 5개 입력으로 전 경로 호출, 단언 없음.
- PartialTest: (150000, VIP)와 음수만 단언.
- WeakTest: 구간 한가운데 값(150000 VIP, 60000, 1000, 음수)만 단언 — "VIP인데 10만 원 미만" 경우 없음.
- StrongTest: 경계값 + 결정 테이블 8행과 음수 1개를 단언.

(실험, maven:3.9-eclipse-temurin-21 · JUnit 5.13.4 · JaCoCo 0.8.14 · PIT 1.20.4 + pitest-junit5-plugin 1.2.3, `--cpus=2`, 2026-10-03)

```text
                 jacoco.csv: INSTR_MISSED,INSTR_COVERED,BRANCH_MISSED,BRANCH_COVERED,LINE_MISSED,LINE_COVERED
NoAssertTest     Pricing,0,30,0,8,0,4     >> Generated 14 mutations Killed 1 (7%)
PartialTest      Pricing,11,19,4,4,2,2    >> Generated 14 mutations Killed 6 (43%)
WeakTest         Pricing,0,30,1,7,0,4     >> Generated 14 mutations Killed 11 (79%)
StrongTest       Pricing,0,30,0,8,0,4     >> Generated 14 mutations Killed 14 (100%)
```

| 스위트 | 라인 | 분기 | 변이 점수(PIT Killed %) |
|---|---|---|---|
| NoAssertTest | 4/4 (100%) | 8/8 (100%) | 1/14 (7%) |
| PartialTest | 2/4 | 4/8 | 6/14 (43%) |
| WeakTest | 4/4 (100%) | 7/8 | 11/14 (79%) |
| StrongTest | 4/4 (100%) | 8/8 (100%) | 14/14 (100%) |

- 관찰
  - **NoAssertTest와 StrongTest는 커버리지가 완전히 같다.** 변이 점수만 7%와 100%로 갈린다. 커버리지는 단언의 유무를 못 본다.
  - WeakTest는 라인 100%인데 분기 7/8이다. 빠진 분기는 `amount >= 100_000`의 거짓 쪽(VIP인데 10만 원 미만)이다. 라인 커버리지만 봤다면 안 보인다. HTML 보고서의 줄 표시(`target/site/jacoco/exp/Pricing.java.html`):

```text
<span class="fc bfc" id="L6" title="All 2 branches covered.">
<span class="pc bpc" id="L7" title="1 of 4 branches missed.">
<span class="fc bfc" id="L8" title="All 2 branches covered.">
<span class="fc" id="L9"
```

  - `fc`=완전(초록), `pc`=부분(노랑). 7번 줄은 명령이 전부 실행됐는데도(`INSTRUCTION_MISSED` 0) 분기 4개 중 1개가 빠져 부분으로 표시됐다. CSV의 `LINE_COVERED`(4)는 이 줄을 실행된 줄로 센다.
  - 문서의 줄 색 설명은 명령 기준("Only a part of the instruction")이지만, 실제 줄 상태는 명령 상태와 분기 상태를 합친 값이다(JaCoCo 0.8.14 `LineImpl.getStatus()` = 명령 카운터 상태 `|` 분기 카운터 상태, 바이트코드로 확인). 그래서 명령이 다 실행돼도 분기가 빠지면 노랑이다.
  - PartialTest 정도로 커버리지가 낮으면 "테스트가 안 닿는 곳(8·9번 줄)"이 정확히 보인다. 낮은 커버리지는 유용한 신호다.
- 도구마다 줄 수가 다르다: 같은 실행에서 PIT는 `Line Coverage (for mutated classes only): 4/5 (80%)`를 냈다. JaCoCo는 4/4다.
  - 원인(확인함): 남는 1줄은 11번 줄 `private Pricing() { }`이다. PIT HTML 보고서(`target/pit-reports/exp/Pricing.java.html`)가 6~9번 줄을 covered, 11번 줄을 uncovered로 표시한다. JaCoCo는 0.8.0부터 private 빈 무인자 생성자를 보고서에서 빼지만(changes 문서), PIT 1.20.4의 줄 매핑(`LineMapper.mapLines`)은 클래스의 모든 메서드를 걸러내지 않고 줄에 매핑한다(바이트코드로 확인).
  - 대조 실행: 생성자를 지운 사본에서는 JaCoCo도 컴파일러가 만든 기본 생성자 줄(3번)을 미실행으로 세어 `Pricing,3,30,0,8,1,4`(4/5)가 됐다. PIT는 여전히 4/5이고 미실행 줄이 3번으로 바뀌었다. `MathUtil`(private 생성자 있음)도 PIT 2/3, PartialTest는 PIT 2/5 vs JaCoCo 2/4로 같은 차이를 보였다.
  - 커버리지 수치를 비교할 때는 **같은 도구·같은 필터**인지부터 본다.

### 3. 무엇을 보장하고, 무엇을 못 보장하나

```text
  분기 100% ⊃ 문장 100%           (ISTQB 4.3.2)
  MC/DC ⊃ 분기·조건                (NASA 튜토리얼의 정의상)
  변이 점수 ── 커버리지가 못 보는 "단언의 날카로움"을 잰다(15번)

  어느 커버리지도 못 잡는 것
   · 데이터 의존 결함: 분모가 0일 때만 터지는 나눗셈 (ISTQB 4.3.1의 예)
   · 특정 경로에서만 나는 결함 (4.3.2)
   · 누락 결함: 명세에는 있는데 구현하지 않은 기능 — 코드가 없으니 셀 줄도 없다 (4.3.3)
```

- 실증 연구: Inozemtseva–Holmes(ICSE 2014)는 Java 시스템 5개에 대해 테스트 스위트 31,000개를 만들어 문장·결정·수정 조건 커버리지와 (변이로 잰) 결함 검출력을 비교했다. **스위트 크기를 고정하면** 커버리지와 효과의 상관은 낮음~중간이었고, 더 강한 커버리지 종류가 더 나은 예측을 주지도 않았다. 결론: 커버리지는 테스트가 덜 된 곳을 찾는 데는 쓸모 있지만 품질 목표로 쓰면 안 된다.

## 쓰이는 자료구조·알고리즘

- **제어 흐름 그래프**: 커버리지 종류는 전부 CFG 위의 덮개 문제다 — 노드 덮기(문장), 간선 덮기(분기), 경로 덮기(경로)([그래프](../../data-structure/08-graph/2-summary.md)).
- **불리언 배열(비트맵) 계측**: JaCoCo는 클래스마다 `boolean[]` 프로브 배열에 실행 여부를 찍는다. 보고서는 프로브 → 간선 → 명령·줄·분기로 역추적해 만든다([data-structure/18-bitset](../../data-structure/18-bitset/2-summary.md)과 같은 발상).
- **순환 복잡도 `v(G) = B − D + 1`**: CFG의 독립 경로 수. 분기 커버리지를 채우는 데 필요한 테스트 수의 감각을 준다.
- **MC/DC = 진리표에서 독립 쌍 찾기**: 조건 하나만 바뀌고 결과가 바뀌는 두 행의 쌍을 조건마다 찾는다. 행끼리 쌍을 공유하면 행 수가 준다. NASA 튜토리얼은 n개 조건이면 "일반적으로 최소 n+1개"가 필요하다고 쓴다(하한이다 — 결정 모양에 따라 더 필요할 수 있다).
- **diff × 커버리지 교집합**: "변경된 줄 중 커버되지 않은 줄"은 변경 줄 집합과 미실행 줄 집합의 교집합이다. Google의 per-commit 커버리지와 변이 테스트 대상 선정이 이 연산 위에 있다.

## 적용 — 풀어나가는 법

### 순서

1. **커버리지를 "빈칸 찾기" 도구로 쓴다.** 보고서에서 빨간 줄(미실행)과 노란 다이아몬드(분기 일부만)를 본다.
2. **빈칸마다 "이 경로가 운영에서 중요한가"를 묻는다.** 중요하면 테스트를 추가한다. 로그·생성 코드처럼 중요하지 않으면 그대로 두거나 필터한다.
3. **라인이 아니라 분기를 본다.** 라인 100%·분기 7/8(WeakTest) 같은 경우를 놓치지 않는다.
4. **높은 커버리지 구간에는 변이 테스트를 돌린다.** 커버리지가 못 보는 단언 품질을 잰다(→ [15-mutation-testing](../15-mutation-testing/2-summary.md)).
5. **목표는 변경분에 둔다.** 프로젝트 전체 수치보다 "이번 변경의 커버리지"를 본다.

### JaCoCo 설정·보고서

```xml
<!-- pom.xml 발췌: JaCoCo 0.8.14, test 단계에 에이전트를 붙인다 -->
<plugin>
  <groupId>org.jacoco</groupId><artifactId>jacoco-maven-plugin</artifactId><version>0.8.14</version>
  <executions><execution><id>agent</id><goals><goal>prepare-agent</goal></goals></execution></executions>
</plugin>
```

```bash
mvn clean test jacoco:report
# target/site/jacoco/index.html (줄 색: 초록=완전, 노랑=부분, 빨강=미실행)
# target/site/jacoco/jacoco.csv (클래스별 INSTRUCTION·BRANCH·LINE·COMPLEXITY·METHOD 카운터)
```

### 목표 수치에 대한 출처별 입장

| 출처 | 입장 |
|---|---|
| Google Testing Blog "Code Coverage Best Practices"(2020, Arguelles·Ivanković·Bender) | 이상적인 숫자는 없다. Google의 일반 지침은 60% "acceptable", 75% "commendable", 90% "exemplary". 프로젝트 전체 90% 초과는 대개 가치가 없고, per-commit 99%는 합리적이며 90%가 좋은 하한. 높은 수치는 품질을 보장하지 않으며 단언까지 보려면 변이 테스트가 낫다 |
| SWE@G 11장 | 커버리지는 줄 호출만 잰다. 목표가 되면 80%가 천장이 된다. 대신 "고객이 기대하는 것이 동작한다는 확신이 있나" 같은 질문을 하라 |
| Fowler "TestCoverage"(2012) | 테스트 안 된 곳을 찾는 데 유용하지만, 테스트가 얼마나 좋은지의 숫자로는 별 쓸모가 없다. 잘 테스트하면 80% 후반~90%대가 나오리라 보고, 100%는 오히려 의심스럽다 |

- 셋 다 **주장**이다. 공통점은 "낮은 커버리지는 신호, 높은 커버리지는 보장이 아님, 목표로 강제하지 말 것"이다.
- Google 블로그는 통합·E2E 테스트 커버리지의 일부는 우연히 실행된 것(incidental)이라고도 쓴다. 같은 글은 단위·통합을 합친 파이프라인 전체 커버리지가 "paramount"하다고도 쓴다 — 합쳐 보되, 우연한 부분을 감안한다. SWE@G 11장은 커버리지를 작은 테스트에서만 재라고 권한다(큰 테스트의 부풀림을 피하려고).

## 장애 시나리오와 대처

### 1. 커버리지 목표 강제 → 단언 없는 테스트 양산(굿하트)

- **현상**: 커버리지 80% 게이트를 건 뒤 수치는 올랐는데 결함 유출은 줄지 않았다.
- **보이는 형태**: 커버리지 리포트는 초록. 테스트 코드에 `assert`가 없거나 `assertNotNull(result)`뿐인 테스트가 많다. 변이 점수는 낮다(실험 NoAssertTest: 커버리지 100%, 변이 7%).
- **원인**: 측정이 목표가 되면 측정을 맞추는 행동이 나온다(굿하트의 법칙). SWE@G 11장: 커버리지는 "목표 자체"가 되기 쉽다.
- **대처**: 커버리지는 게이트가 아니라 빈칸 탐색용으로 쓴다. 게이트가 필요하면 변경분 커버리지 + 리뷰에서 빈칸 설명을 요구한다. 핵심 모듈은 변이 테스트로 단언 품질을 본다.

### 2. 라인 100%인데 분기 누락 → 특정 조건 조합에서 장애

- **현상**: VIP 고객의 9만 원 주문만 할인이 잘못 계산된다.
- **보이는 형태**: 라인 커버리지 100%. JaCoCo 분기 7/8, 7번 줄 노란 다이아몬드("1 of 4 branches missed").
- **원인**: `vip && amount >= 100_000`의 "VIP인데 10만 원 미만" 분기를 아무도 실행하지 않았다(WeakTest).
- **대처**: 라인이 아니라 분기를 본다. `&&`·`||`가 있는 결정은 결정 테이블([07-test-design-techniques](../07-test-design-techniques/2-summary.md))로 조합을 펼친다. 안전 핵심 코드는 MC/DC를 검토한다.

### 3. 누락 결함 → 커버리지 100%인데 기능이 없음

- **현상**: "주문 취소 시 쿠폰 복원" 요구사항이 구현되지 않았는데 아무도 몰랐다.
- **보이는 형태**: 커버리지 100%. 운영에서 쿠폰이 사라졌다는 문의.
- **원인**: 화이트박스 커버리지는 **존재하는 코드**만 센다. 구현이 없으면 셀 줄도 없다(ISTQB 4.3.3).
- **대처**: 요구사항·인수 기준에서 출발한 테스트(블랙박스 기법)를 함께 쓴다. 커버리지는 구현된 코드의 빈칸만 알려 준다.

### 4. 통합 테스트의 우연한 커버리지 → 거짓 안심

- **현상**: 전체 커버리지는 높은데, 특정 모듈을 고치자 회귀가 났다.
- **보이는 형태**: 그 모듈의 줄은 E2E 테스트가 "지나가면서" 실행했을 뿐, 결과를 단언하는 테스트는 없었다.
- **원인**: 통합·E2E 커버리지에는 우연히 실행된 것이 섞인다(Google Testing Blog 2020). SWE@G 11장도 큰 테스트가 커버리지를 부풀린다고 보고, 작은 테스트에서만 재라고 권한다.
- **대처**: 단위 테스트 커버리지와 통합 커버리지를 나눠 본다. 핵심 모듈은 그 모듈을 직접 단언하는 테스트의 커버리지로 판단한다.

### 5. 도구·필터 차이로 수치가 흔들림 → 게이트 오판

- **현상**: 로컬 JaCoCo 100%인데 CI의 다른 도구는 80%라며 빌드를 막는다.
- **보이는 형태**: 같은 코드에서 JaCoCo 라인 4/4, PIT `Line Coverage ... 4/5 (80%)`(실험).
- **원인**: 도구마다 세는 단위·필터가 다르다(JaCoCo는 0.8.0부터 private 빈 생성자 등을 필터).
- **대처**: 게이트는 한 도구·한 설정으로 고정한다. 생성 코드·롬복 등 필터 규칙을 명시한다. 수치 비교는 같은 도구 안에서만 한다.

## 핵심 문장

- 커버리지는 "실행됐나"를 잰다. "검증했나"는 재지 않는다 — 실험에서 단언 없는 스위트와 경계값 스위트의 라인·분기 커버리지가 똑같았다(변이 7% vs 100%).
- 낮은 커버리지는 테스트가 안 닿는 곳을 정확히 알려 주는 신호다. 높은 커버리지는 품질의 증거가 아니다.
- 분기 100%는 문장 100%를 포함하지만 역은 아니다. 라인 100%·분기 7/8처럼 라인만 보면 놓치는 조합이 있다.
- 커버리지는 존재하는 코드만 센다. 구현이 빠진 요구사항은 잡지 못한다.
- 커버리지를 목표로 강제하면 수치를 맞추는 테스트가 생긴다. 빈칸 찾기에 쓰고, 단언 품질은 변이 테스트로 본다.

## 관련 주제·근거

- 선행
  - testing [15-mutation-testing](../15-mutation-testing/2-summary.md) — 커버리지가 못 재는 단언 품질
- 후속·연결
  - testing [07-test-design-techniques](../07-test-design-techniques/2-summary.md) — 분기를 덮을 입력은 결정 테이블·경계값이 준다
  - testing [14-property-based-testing](../14-property-based-testing/2-summary.md)
  - testing [20-test-symptom-index](../20-test-symptom-index/2-summary.md) — "커버리지 높은데 버그" 증상
  - software-design [52-complexity-metrics](../../software-design/52-complexity-metrics/2-summary.md) — 순환 복잡도 · [data-structure/08-graph](../../data-structure/08-graph/2-summary.md) · [data-structure/18-bitset](../../data-structure/18-bitset/2-summary.md)
- 교재·문서
  - SWE@G 11장 Testing Overview — "A Note on Code Coverage" <https://abseil.io/resources/swe-book/html/ch11.html>
  - Google Testing Blog, Carlos Arguelles·Marko Ivanković·Adam Bender, "Code Coverage Best Practices"(2020-08) — 60/75/90%, per-commit 99%·90% 하한, 높은 수치 ≠ 품질, 변이 테스트, 통합 커버리지의 우연성 <https://testing.googleblog.com/2020/08/code-coverage-best-practices.html>
  - Martin Fowler, "TestCoverage"(2012-04-17) <https://martinfowler.com/bliki/TestCoverage.html>
  - ISTQB CTFL Syllabus v4.0.1 4.3 — 문장·분기 커버리지 정의, 분기 ⊃ 문장, 데이터 의존·경로 결함, 누락 결함(4.3.3) <https://astqb.org/assets/documents/ISTQB_CTFL_Syllabus_v4.0.1.pdf>
  - Hayhurst 외, "A Practical Tutorial on Modified Condition/Decision Coverage", NASA/TM-2001-210876 — MC/DC 정의, 최소 n+1, 다중 조건 2^n, DO-178B Level A <https://ntrs.nasa.gov/api/citations/20010057789/downloads/20010057789.pdf>
  - JaCoCo 문서 — Coverage Counters(명령·분기·줄·복잡도, 예외 미포함) <https://www.jacoco.org/jacoco/trunk/doc/counters.html>, Control flow analysis(프로브·`boolean[]`·오버헤드) <https://www.jacoco.org/jacoco/trunk/doc/flow.html>, Change history(0.8.0 private 빈 생성자 필터) <https://www.jacoco.org/jacoco/trunk/doc/changes.html>
- 논문
  - Laura Inozemtseva, Reid Holmes. "Coverage Is Not Strongly Correlated with Test Suite Effectiveness." ICSE 2014 — 5개 시스템, 31,000 스위트, 크기 고정 시 낮음~중간 상관 <https://www.cs.ubc.ca/~rtholmes/papers/icse_2014_inozemtseva.pdf>
- 실험 목록(2026-10-03, 코드는 scratchpad/ts/07/m/ — 15번 노트와 같은 실행)
  - `run.sh` — maven:3.9-eclipse-temurin-21, JaCoCo 0.8.14·PIT 1.20.4, `--cpus=2`: 스위트 4개의 `jacoco.csv`(명령·분기·줄)와 PIT 통계(Killed %, Line Coverage 4/5)
  - private 생성자 추가 전 첫 실행에서 JaCoCo가 기본 생성자 줄을 미실행 1줄로 센 것 확인(`Pricing,3,30,0,8,1,4`)
  - 사실 점검 재실행(같은 환경) — 4개 스위트 출력 일치, 생성자 없는 사본 대조(JaCoCo `Pricing,3,30,0,8,1,4`, PIT 4/5·미실행 3번 줄), PIT HTML 줄 표시와 `LineMapper`·JaCoCo `LineImpl` 바이트코드(javap) 확인
