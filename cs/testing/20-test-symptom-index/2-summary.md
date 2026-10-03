# testing/20-test-symptom-index — 증상 사전: CI 가끔 실패·리팩터링마다 대량 실패·초록인데 운영 장애·테스트 느림·커버리지 높은데 버그 → 원인·첫 진단·leaf — 정리 (힌트)

## 해결하는 문제

테스트 영역의 다른 노트는 **원인에서 증상으로** 간다.\
"공유 정적 상태가 있다 → 실행 순서에 따라 깨진다"처럼 쓴다.\
현장에서는 반대 방향이 필요하다.\
손에 든 것은 빨간 CI 한 줄(`expected: <2000> but was: <1607>`), 재실행하니 초록이 된 빌드, "테스트는 다 통과했는데 운영에서 결제가 안 된다"는 문의뿐이다.

이 노트는 그 **역방향 색인**이다.

```text
  다른 노트 (정방향)                               이 노트 (역방향)
  테스트 설계 결정 --> 결함 --> 보이는 증상          증상 --> 언제·어떤 모양으로 --> 흔한 원인 --> 첫 진단 --> leaf
  "정적 리스트를 테스트가 공유한다"                  "단독 실행은 초록, 전체 실행은 빨강. 앞에 돈 테스트부터 본다"
```

쉬운 예: 병원 응급실의 분류표다.\
"가슴이 아프다"만으로 수술하지 않는다. 표가 "먼저 심전도를 찍어라"라고 정해 준다.\
표는 치료하지 않는다. **어디를 먼저 볼지**만 정한다.

똑같은 구조다.\
"리팩터링했더니 테스트 30개가 빨갛다"라면 먼저 실패한 단언의 종류를 본다.\
`Wanted but not invoked`처럼 **호출**을 단언한 테스트라면, 테스트가 구현 세부에 묶였을 가능성이 크다([02-1](../02-good-unit-tests/2-summary.md)).\
`expected: 90000L but was: 0L`처럼 **값**을 단언한 테스트들이 한 공용 객체를 함께 실행한다면, 그 객체에 진짜 회귀가 있을 수 있다([04-3](../04-classical-vs-london/2-summary.md)).\
단, 같은 메시지가 04 실험 R2에서는 stub하지 않은 mock 메서드의 기본값 0으로 나온 거짓 경보였다([04-1](../04-classical-vs-london/2-summary.md)). 메시지만으로는 못 가르고, SUT가 mock을 거쳐 값을 받는지 함께 본다.\
같은 "대량 실패"인데 처방은 정반대다. 앞은 테스트를 고치고, 뒤는 제품 코드를 고친다.

실무 예:
- 테스트 영역에서 "깨졌다"는 두 방향이다. **거짓 경보**(동작은 맞는데 빨강)와 **놓침**(동작이 틀렸는데 초록)이다. 놓침은 CI에서 보이지 않고 운영에서 보인다.
- 같은 결함이 테스트 설계에 따라 **다른 시점**에 보인다. H2로 시험한 트랜잭션 오류 처리는 운영에서 `25P02`로, PostgreSQL 컨테이너로 시험하면 CI에서 같은 메시지로 보인다([08-1](../08-integration-tests-real-dependencies/2-summary.md)).
- 실패 위치와 원인 위치가 다를 수 있다. 순서 의존 테스트는 **피해자**가 실패하고, 원인은 앞서 돈 **오염자**에 있다([09-3](../09-flaky-tests/2-summary.md), [11-1](../11-test-data-and-fixtures/2-summary.md)).

  - *역색인(inverted index)*: "문서 → 단어" 목록을 뒤집어 "단어 → 문서" 목록으로 만든 것이다. 여기서는 "leaf → 증상"을 "증상 → leaf"로 뒤집었다.
  - *leaf 표기 `NN-k`*: 테스트 영역 `NN`번 노트의 「장애 시나리오와 대처」 `k`번째 시나리오다. 예: `09-1` = 09번 노트의 시나리오 1(재시도로 경쟁 조건 은폐).
  - *메시지 옆 버전*: 각 leaf 실험에서 실제로 찍힌 메시지다. 같은 결함이라도 도구 판이 다르면 문구가 다를 수 있다.

## 동작·원리

### 0. 테스트 결과의 네 칸 — 증상이 어느 칸인지부터

```text
                         제품 동작이 맞다            제품 동작이 틀렸다
                    ┌──────────────────────────┬──────────────────────────┐
   테스트가 빨강     │  거짓 경보 (false positive) │  제대로 잡음               │
                    │  리팩터링마다 대량 실패      │  (이 색인의 대상 아님)      │
                    │  가끔 실패(불안정)          │                          │
                    ├──────────────────────────┼──────────────────────────┤
   테스트가 초록     │  정상                      │  놓침 (false negative)     │
                    │                          │  초록인데 운영 장애         │
                    │                          │  커버리지 높은데 버그        │
                    └──────────────────────────┴──────────────────────────┘
   그리고 칸 밖의 비용:  테스트가 느리다 → 아무도 안 돌린다 → 위 두 칸이 커진다
```

- 이 노트는 Khorikov 『Unit Testing PPP』 4장의 용어를 따른다. **거짓 양성(false positive)** = 동작은 맞는데 테스트가 실패하는 거짓 경보. **거짓 음성(false negative)** = 버그가 있는데 테스트가 통과하는 놓침. 자세한 정의는 [02](../02-good-unit-tests/2-summary.md).
- 커리큘럼의 다섯 증상은 이 그림의 세 칸에 들어간다.
  - 거짓 경보 칸: "CI 가끔 실패", "리팩터링마다 대량 실패".
  - 놓침 칸: "초록인데 운영 장애", "커버리지 높은데 버그".
  - 칸 밖의 비용: "테스트 느림". 느린 테스트는 덜 돌고, 덜 돌면 두 칸 모두 늦게 드러난다.
- 거짓 경보 칸과 놓침 칸은 **처방이 반대**다. 거짓 경보는 테스트를 덜 묶고(관찰 가능한 결과로), 놓침은 테스트를 더 현실에 붙인다(실제 의존·음성 테스트·경계값). 한쪽 처방을 다른 쪽 증상에 쓰면 악화한다.

### 0-1. 증상이 드러나는 시점 — 늦을수록 비싸다

```text
  코드 변경
     │
     ▼
  ① 작성·로컬      컴파일 오류(테스트 수십 곳), 단독 실행 초록         ← 테스트 코드의 결합이 보이는 곳
     │
     ▼
  ② CI            가끔 빨강, 재실행하면 초록, Flakes: 1, 수십 분      ← 불안정·느림
     │
     ▼
  ③ 배포 단계      카나리 판정 실패, 합성 점검 실패(k6 exit=99)        ← 운영 검증이 마지막 그물
     │
     ▼
  ④ 운영 — 예외    25P02, 404, NPE, 역직렬화 오류                    ← 테스트 환경과 운영의 차이
     │
     ▼
  ⑤ 운영 — 조용함  1원 차이, 정확히 5만 원만 할인 누락, 메일 두 통     ← 대사·고객 문의로 며칠 뒤
```

- 같은 결함을 위 칸으로 끌어올리는 것이 테스트 설계의 일이다.

| 결함 | 아래 칸에서 보일 때 | 위 칸으로 당긴 테스트 | 당긴 뒤 보이는 형태 | leaf |
|---|---|---|---|---|
| 오류 뒤 같은 트랜잭션을 계속 씀 | ④ `PSQLException: ERROR: current transaction is aborted …`(25P02) | H2 → PostgreSQL 17 컨테이너 | ② 같은 메시지로 CI 빨강(PostgreSQL JDBC 42.7.13) | [08-1](../08-integration-tests-real-dependencies/2-summary.md) |
| 조립 누락(저장소 두 개) | ④ "가입은 되는데 조회 404" | 실제 앱을 띄우는 인수 테스트 | ② `expected: 200 but was: 404`(AssertJ 3.27.3) | [06-1](../06-outside-in-tdd-and-acceptance-tests/2-summary.md) |
| 제공자 필드 이름 변경 | ④ 소비자 역직렬화 오류·NPE | 소비자 주도 계약 | ② `body: $ Actual map is missing the following keys: name`(Pact JVM 4.7.5) | [13-1](../13-contract-testing/2-summary.md) |
| 경계 비교 연산자 하나 차이(`>=`↔`>`, `<=`↔`<`) | ⑤ 정확히 그 금액만 할인 누락 | 경계값 파라미터 표 | ② `[2] … expected: 3000 but was: 4000`(07 실험의 배송비 경계 표 — 구현이 `grams < 2000`, JUnit 5.13.4) | [07-1](../07-test-design-techniques/2-summary.md) |
| 운영 설정 누락 | ⑤ 200 응답인데 결제 안 됨 | 업무 결과를 단언하는 합성 점검 | ③ `thresholds on metrics 'checks' have been crossed`, k6 1.2.3 종료 코드 99 | [19-1](../19-testing-in-production/2-summary.md) |
| 서명 검증을 건너뜀 | 공격받을 때까지 안 보임 | 잘못된 서명을 넣는 음성 테스트 | ② 음성 테스트 빨강 | [21](../21-test-incidents/2-summary.md) |

- 그래서 색인을 쓰기 전에 두 가지를 확보한다.
  - **원문**: 실패 메시지 전체(`Caused by`까지), 도구·라이브러리 버전, 실패한 테스트 이름과 파라미터 번호(`[2]`).
  - **시점과 모양**: ①~⑤ 중 어디서 처음 보였나. 재실행하면 바뀌나. 단독 실행과 전체 실행이 다른가. 특정 변경·날짜·시각과 겹치나.

### 1. "CI가 가끔 실패한다" — 재실행하면 초록

먼저 **다시 돌려서 결과가 바뀌는지** 확인한다. 바뀌면 불안정 테스트다. 그다음 무엇에 따라 바뀌는지로 가른다.

```text
  같은 커밋, 재실행하면 결과가 다르다
     │
     ├─ 단독 실행은 초록, 전체 실행은 빨강 ─────────▶ 순서 의존(공유 상태)        09-3 · 11-1 · 11-5 · 12-5
     ├─ 바쁜 러너·혼잡 시간대에 몰림 ─────────────▶ 고정 sleep·타임아웃          09-4 · 10-1 · 18-3
     ├─ 특정 날짜·시각에 몰림(말일·자정·DST) ──────▶ 시스템 시계 직접 읽기          10-2
     ├─ 병렬 실행을 켠 뒤부터 ─────────────────────▶ 외부 자원 공유(포트·파일·행)   09-5
     ├─ 무작위 입력 테스트만 가끔 ──────────────────▶ 진짜 버그를 가끔 밟음(시드)     14-3
     ├─ 다른 팀 배포·다른 작업과 겹칠 때 ────────────▶ 공유 환경·공유 데이터        18-4 · 11-5
     └─ 동시성 테스트가 가끔 ───────────────────────▶ 제품 코드의 경쟁 조건일 수 있다  09-1 · 10-4
```

| 보이는 것 (메시지·도구 판) | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| 단독 실행 초록, `mvn test` 전체 빨강. 실패 위치(`nothingReservedYet: expected 10`)와 원인(앞서 돈 `reserveFive`·`reserveFour`)이 다름(11 실험 A). 무작위 순서 20회 중 12회 실패(09·11 실험 A 모두, JUnit 5.13.4) | 정적·`@BeforeAll`·DB에 둔 가변 상태를 여러 테스트가 고침(Interacting Tests) | 무작위 순서 + 시드 고정으로 재현 → 앞에 돈 테스트를 이분 탐색 | [09-3](../09-flaky-tests/2-summary.md) · [11-1](../11-test-data-and-fixtures/2-summary.md) · [12-5](../12-test-smells-and-xunit-patterns/2-summary.md) |
| 첫 실행 통과, 재실행에서 `duplicate key value violates unique constraint`. 병렬 작업 시간대에만 실패 | 테스트가 만든 행이 남음, 고정 키를 여러 실행이 공유(Unrepeatable Test, Test Run War) | 실패한 키가 고정값인가, 이전 실행의 행이 남았나 | [11-5](../11-test-data-and-fixtures/2-summary.md) |
| `expected: not <null>`·타임아웃·"element not found". 로컬 100번 초록, CI 하루 몇 번 빨강. 부하 4개에서 50번 중 30~32번 실패(09 실험 B, JDK 21.0.12) | 고정 sleep이 느린 러너에서 모자람 | 테스트 본문의 `Thread.sleep`·`sleep(500)` 검색. 실패 시각과 CI 혼잡도 대조 | [09-4](../09-flaky-tests/2-summary.md) · [10-1](../10-testing-time-and-concurrency/2-summary.md) · [18-3](../18-e2e-and-ui-testing/2-summary.md) |
| 실패 날짜가 31일·말일·DST 전환일·UTC 자정(KST 09:00) 근처. 다시 돌리면 초록 | 코드나 테스트가 시스템 시계를 직접 읽음. 기대값을 `now()`로 다시 계산 | `now()` 호출 위치 검색. 고정 시계로 1년을 훑는 테스트(10 실험 B: 365일 중 7일) | [10-2](../10-testing-time-and-concurrency/2-summary.md) |
| `BindException`, 같은 파일·같은 DB 행 충돌. 병렬 실행을 켠 뒤부터 | 순차 실행에서 숨던 외부 자원 공유 | 실패 테스트 쌍이 같은 포트·경로·행을 쓰나 | [09-5](../09-flaky-tests/2-summary.md) |
| 속성 테스트가 가끔 빨강, 로컬 재현 안 됨. 로그에 시드 없음 | 무작위 입력이 진짜 버그를 가끔만 밟음(14 실험: `dedup` 전체 int 범위에서 200개 시드 중 47개 — 약 4번에 1번, fast-check 4.10.2) | 시드·경로를 로그에서 찾아 그 값으로 재실행 | [14-3](../14-property-based-testing/2-summary.md) |
| "이미 존재하는 이메일", 남이 지운 테스트 상품. 다른 팀 배포와 겹침 | 밀폐되지 않은 SUT와 공유 테스트 데이터 | 실패한 데이터의 생성 주체 | [18-4](../18-e2e-and-ui-testing/2-summary.md) |
| surefire `[WARNING] Tests run: …, Flakes: 1`인데 빌드는 `BUILD SUCCESS`. 운영에서는 합계가 가끔 모자람 | 동기화 없는 공유 상태 — **제품 결함**. 재시도가 신호를 경고로 낮춤(09 실험 C: 재시도 없이 12번 중 9번 실패 → 재시도 3회로 6번 모두 성공, surefire 3.5.3) | 재시도 없이 반복 실행해 실패 비율을 잰다. 실패 값이 매번 다른가(`but was: <1607>`, `<1401>`) | [09-1](../09-flaky-tests/2-summary.md) · [10-4](../10-testing-time-and-concurrency/2-summary.md) |

- **재시도를 처방으로 쓰지 않는다.** 재시도는 불안정한 테스트와 불안정한 **제품**을 구별하지 못한다. 09 실험 C에서 재시도는 진짜 경쟁 조건을 `Flakes: 1`로 바꿨다([09-1](../09-flaky-tests/2-summary.md)).
- 빨강을 아무도 보지 않게 된 상태가 이 증상의 끝이다([09-2](../09-flaky-tests/2-summary.md), [01-1](../01-why-test-and-pyramid/2-summary.md)). SWE@G 11장은 불안정 비율이 1%에 가까워지면 테스트가 가치를 잃기 시작한다고 적는다([09-2](../09-flaky-tests/2-summary.md)에서 인용).

### 2. "리팩터링할 때마다 테스트가 대량으로 깨진다" — 동작은 그대로

먼저 **실패한 단언이 무엇을 확인하나**로 가른다.

```text
  동작 보존 리팩터링인데 빨강 N개
     │
     ├─ 컴파일 오류 (cannot find symbol, 생성자 인자 수) ──▶ 테스트가 private 도우미·생성자를 직접 부름  02-1 · 11-4
     ├─ 호출 단언 (Wanted but not invoked, No interactions wanted here) ─▶ 상호작용 과잉 검증  02-1 · 04-1
     ├─ stub하지 않은 새 메서드가 0 반환 (but was: 0L) ──▶ 같은 프로세스 협력 객체까지 mock  04-1
     ├─ UnnecessaryStubbingException ──────────────────▶ 호출 경로가 바뀌어 stub이 안 쓰임   03-4
     ├─ 선택자 실패 (Cannot read properties of null) ────▶ CSS 경로·nth-child에 묶임        18-1 · 06-2
     ├─ 골든 마스터·스냅숏 diff ─────────────────────────▶ 숨은 입력·승인 피로             17-2 · 17-4
     └─ 값 단언이 여러 모듈에서 동시에 ─────────────────▶ 진짜 회귀일 수 있다(공용 객체)    04-3
```

| 보이는 것 (메시지·도구 판) | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| `Wanted but not invoked: -> at shop.DiscountPolicy.discountRate(...)`, `verifyNoMoreInteractions` 위반(Mockito 5.18.0). 02 실험: 세부 검증 판 6개 중 R1에서 컴파일 실패 2개·R2에서 실패 1개, 결과 검증 판은 둘 다 0개 | 테스트가 내부 협력 객체 호출·private 도우미에 묶임 | 실패한 단언이 값인가 호출인가. 호출이면 그 협력 객체가 프로세스 밖인가 | [02-1](../02-good-unit-tests/2-summary.md) · [04-1](../04-classical-vs-london/2-summary.md) |
| `expected: 90000L but was: 0L` — 위임만 바꿨는데 런던파 테스트 2개 실패(04 실험 R2, Mockito 5.18.0 `mock()` 기본) | stub하지 않은 새 메서드가 Mockito 기본 응답(원시 타입 0)을 돌려줌 | 실패한 테스트의 SUT가 mock을 거쳐 값을 받나 | [04-1](../04-classical-vs-london/2-summary.md) |
| `UnnecessaryStubbingException … Unnecessary stubbings detected.`(mockito-junit-jupiter 5.24.0, 기본 `STRICT_STUBS`) | SUT 호출 경로가 바뀌어 일부 stub이 안 불림. 공유 `@BeforeEach` stub | 메시지가 가리키는 `when(...)` 줄 | [03-4](../03-test-doubles/2-summary.md) |
| `cannot find symbol`(테스트 컴파일 실패). 필수 필드 하나 추가에 직접 호출 테스트 6곳, 빌더 1곳(11 실험 B, JDK 21.0.12 javac) | 테스트가 private 도우미·생성자를 직접 부름 | 컴파일 오류가 난 파일이 테스트뿐인가 | [02-1](../02-good-unit-tests/2-summary.md) · [11-4](../11-test-data-and-fixtures/2-summary.md) |
| 공용 시드·오브젝트 마더 한 줄 추가에 무관한 테스트 여럿 실패(11 실험 C: 마더 테스트 6개 중 2개 — `MotherTest.regularHasTwoLines`, `sumsLines`) | 테스트가 공유 픽스처의 정확한 데이터·전체 개수에 기댐(Fragile Fixture, Data Sensitivity) | 깨진 테스트가 같은 픽스처를 쓰나 | [11-3](../11-test-data-and-fixtures/2-summary.md) · [12-5](../12-test-smells-and-xunit-patterns/2-summary.md) |
| `Cannot read properties of null (reading 'click')` — 동작이 같은 디자인 개편에 구조 선택자 4/4 실패, 역할·레이블 선택자 0/4(18 실험, jsdom 26.1.0 · @testing-library/dom 10.4.2) | CSS 경로·`nth-child`·클래스 이름에 묶인 선택자 | 실패 선택자가 구조인가 역할·레이블인가 | [18-1](../18-e2e-and-ui-testing/2-summary.md) |
| 경로·문구 변경 PR마다 인수 테스트 수십 개. 06 실험 B: 경로 리터럴이 Raw 본문 5곳, DSL 판은 드라이버 2곳·본문 0곳 | 인수 테스트를 UI·HTTP 조작 단계로 씀(추상화 수준 오류) | 같은 선택자·URL 리터럴이 테스트 본문 몇 곳에 있나(`grep -c`) | [06-2](../06-outside-in-tdd-and-acceptance-tests/2-summary.md) |
| 골든 마스터 승인 직후 재실행해도 실패. diff가 시각·UUID·난수 부분만(17 실험 C: 105줄 중 105줄) | 출력에 실행마다 바뀌는 숨은 입력 | diff 줄이 모두 같은 열(시각·ID)인가 | [17-2](../17-characterization-tests-legacy/2-summary.md) |
| 리팩터링마다 골든 마스터 diff 수백 줄, "update approved" 커밋 | 단계가 큼, 동작 보존과 동작 변경을 한 번에 | 동작 보존 단계의 diff가 0줄인가 | [17-4](../17-characterization-tests-legacy/2-summary.md) |
| `Money` 같은 공용 값 객체 하나 바꿨는데 여러 모듈의 **값** 단언이 동시에 빨강 | 진짜 회귀일 수 있다. 그 객체를 실행하는 고전파 테스트가 함께 결함을 봄 | 실패 테스트들이 공통으로 실행하는 클래스, 그 클래스 자체의 테스트부터 | [04-3](../04-classical-vs-london/2-summary.md) |

- 맨 아래 행은 **거짓 경보가 아니다.** 실패를 국소화하려고 mock을 늘리면 위 행들의 증상을 산다([04-3](../04-classical-vs-london/2-summary.md)).
- 리팩터링 내성이 높은 테스트는 같은 변경에 빨강이 적다. 02·04 실험에서 결과를 단언한 판은 R1·R2 모두 0개 실패였다. 대신 그 판은 버그 B1·B2에서 4개씩 빨강이 났다 — 진짜 회귀는 넓게 보인다.

### 3. "테스트는 초록인데 운영에서 장애" — 놓침

먼저 **그 경로를 실제로 실행한 테스트가 있었나**로 가른다.

```text
  운영 장애, 관련 테스트는 초록
     │
     ├─ 대역이 실제와 다르게 답함 ─────────────────▶ stub·Fake·mock 계약 불일치      02-2 · 03-1 · 03-2 · 03-3 · 03-5 · 04-2 · 04-4 · 06-5 · 10-5
     ├─ 실제 조립·환경이 한 번도 안 돎 ────────────▶ 조립 누락·테스트 DB·설정          06-1 · 06-3 · 01-2 · 01-3 · 08-1 · 08-2 · 19-1
     ├─ 서비스 사이 약속이 바뀜 ────────────────────▶ 계약 테스트 부재·의미 변경         13-1 · 13-3 · 13-5
     ├─ 테스트가 정답을 구현에서 베낌 ──────────────▶ 버그를 정답으로 고정              05-1 · 14-2 · 17-3
     ├─ 단언이 실행되지 않음·실패를 삼킴 ───────────▶ 조건부 단언·드라이버가 boolean으로   12-3 · 06-4 · 05-4
     ├─ 입력이 버그 영역에 안 닿음 ─────────────────▶ 경계·빈 입력·금지 전이·조합·분포   07-1 · 07-2 · 07-3 · 07-4 · 14-1 · 14-4 · 17-1 · 17-5
     └─ 운영에서만 보이는 것 ──────────────────────▶ 운영 검증·카나리 검출력           19-1 · 19-2
```

| 보이는 것 (메시지·도구 판) | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| Stub 테스트 초록, Fake·H2 테스트는 `expected: 300L but was: 100L`와 `NoSuchElement account nope`(03 실험, Mockito 5.24.0 · H2 2.3.232) | stub이 인터페이스의 계약(없을 때·정렬)을 제멋대로 다시 적음 | 실패 경로의 의존이 stub인가. 그 인터페이스에 계약 테스트가 있나 | [03-1](../03-test-doubles/2-summary.md) · [03-2](../03-test-doubles/2-summary.md) |
| 없는 계좌인데 `balance=0`. 예외도 실패도 없음(03 실험 `DEFAULTS balanceText(missing)=balance=0`) | stub하지 않은 원시 `long` 메서드의 Mockito 기본값 0 | 반환 타입이 "없음"을 표현하나(`Optional`) | [03-2](../03-test-doubles/2-summary.md) |
| 운영에서만 "삭제된 계좌가 조회됨". Fake 기반 테스트 초록 | Fake가 실제 구현을 못 따라감(fake drift) | Fake와 실제 구현에 같은 계약 테스트를 돌리나 | [03-3](../03-test-doubles/2-summary.md) |
| 라이브러리 업그레이드 뒤 운영 동작이 바뀌었는데 테스트 그대로 초록 | 내 것이 아닌 타입(`JdbcTemplate`·HTTP 클라이언트)을 직접 mock | mock 대상이 내 인터페이스인가 남의 클래스인가 | [03-5](../03-test-doubles/2-summary.md) · [04-4](../04-classical-vs-london/2-summary.md) |
| 10만 원 주문이 0원. 각 클래스 테스트는 모두 초록(02·04 실험 B4: 결과 검증 판 3개 빨강, 상호작용 판 0개) | stub이 상대 클래스의 옛 약속(단위·형식)을 기억 | 두 클래스의 약속(단위·null)을 실제로 묶어 실행하는 테스트가 있나 | [02-2](../02-good-unit-tests/2-summary.md) · [04-2](../04-classical-vs-london/2-summary.md) |
| 바깥에서 안으로 쓴 mock의 기대(예외·순서)와 실제 구현이 다름 | 발견 단계의 mock이 계약 확인 없이 남음 | 실제 구현이 생긴 뒤 계약 테스트를 붙였나 | [06-5](../06-outside-in-tdd-and-acceptance-tests/2-summary.md) |
| 주기 작업이 운영에서 어느 순간 멈춤. 에러 로그 없음 | 가짜 스케줄러가 `scheduleAtFixedRate`의 "예외 시 이후 실행 억제" 계약을 흉내 내지 않음 | 마지막 로그 직전의 예외, `Future` 안의 예외 | [10-5](../10-testing-time-and-concurrency/2-summary.md) |
| 조회 API 404, 단위 테스트 4개 초록(06 실험 A). 인수 테스트였다면 `expected: 200 but was: 404` | 단위 테스트는 각자 조립 — 실제 Composition Root가 안 돎 | 실제 앱을 띄우는 테스트가 그 기능에 있나 | [06-1](../06-outside-in-tdd-and-acceptance-tests/2-summary.md) |
| 계층별로 완성 후 통합 주에 연결 버그 수십 건 | 끝에서 끝까지 도는 경로가 마지막에야 생김 | 첫 통합 시점이 언제였나 | [06-3](../06-outside-in-tdd-and-acceptance-tests/2-summary.md) |
| E2E에서야 "DB 컬럼이 없다", "JSON 필드 이름이 다르다" | 의존 하나만 띄운 중간 테스트가 없음(모래시계) | 실패 위치가 늘 어댑터 경계인가 | [01-2](../01-why-test-and-pyramid/2-summary.md) |
| "최근 출고" 맨 위에 미출고 주문. PostgreSQL 17.11에서 `["o-2", "o-3"]`(01 실험) | Fake는 SQL을 실행하지 않음. PostgreSQL은 `DESC`에서 NULL을 먼저 둠 | 저장소 구현을 실제 DB로 시험하나 | [01-3](../01-why-test-and-pyramid/2-summary.md) |
| `PSQLException: ERROR: current transaction is aborted, commands ignored until end of transaction block`(25P02). H2에서는 `committed [1, 2]`(08 실험, H2 2.5.252 · PostgreSQL 17.11) | 테스트 DB가 H2 — 오류 뒤 트랜잭션 계속 허용 | 테스트 DB 엔진이 운영과 같은가 | [08-1](../08-integration-tests-real-dependencies/2-summary.md) |
| `operator does not exist: character varying > integer`(42883). H2에서는 `[10, 9]` | H2가 타입을 암묵 변환 | 같은 SQL을 실제 엔진에서 돌려 봤나 | [08-1](../08-integration-tests-real-dependencies/2-summary.md) |
| 운영 `55P03 could not obtain lock on row`, 테스트에서는 `HYT00 Timeout trying to lock table` | 재시도 분기를 SQLSTATE로 나눴는데 테스트 DB의 코드가 다름 | 재시도 분기 판정 기준이 엔진 코드인가 변환된 타입인가 | [08-2](../08-integration-tests-real-dependencies/2-summary.md) |
| 제공자 배포 직후 소비자만 `IllegalStateException: name missing` 류 | 소비자 mock이 옛 응답을 흉내. 제공자 빌드는 소비자 사용을 모름 | 제공자 빌드에서 소비자 계약을 검증하나 | [13-1](../13-contract-testing/2-summary.md) |
| 계약 검증 초록, 소비자 집계가 틀어짐 | 단위가 원 → 천 원 같은 **의미 변경**. 타입 매처로 못 잡음 | 의미가 걸린 필드에 값·범위 규칙이 있나 | [13-3](../13-contract-testing/2-summary.md) |
| 제공자를 먼저 배포했더니 운영의 옛 소비자 판과 불일치 | 최신 소비자 계약만 검증 | `can-i-deploy` 결과, `record-deployment` 기록 | [13-5](../13-contract-testing/2-summary.md) |
| 할인 1원 모자람, 테스트 기대값 `8_104`가 구현 출력과 정확히 같음. 고치면 `expected: 8104L but was: 8105L`(05 실험, AssertJ 3.27.3) | 기대값을 구현 실행 결과에서 붙여 넣음 | 그 숫자의 출처가 손 계산·명세인가 | [05-1](../05-tdd/2-summary.md) |
| 속성 테스트 초록, 성질 코드가 `expected = amount - amount * rate`로 구현과 같은 식 | 성질이 구현을 베낌 | 성질이 구현보다 단순하거나 관점이 다른가 | [14-2](../14-property-based-testing/2-summary.md) |
| 특성 테스트가 명백한 버그(대량 할인으로 청구액 -41)를 지킴 | 특성 테스트는 현재 동작을 기록 — 버그도 기록 | 업무 담당자 확인, 별도 결정 | [17-3](../17-characterization-tests-legacy/2-summary.md) |
| 영수증이 안 나오는데 테스트 초록. 테스트에 `if (x != null) { assert... }`, 빈 `catch` | 조건이 거짓이면 단언이 실행되지 않음(12 실험 b1) | 테스트 코드의 `if`·`catch` 검색 | [12-3](../12-test-smells-and-xunit-patterns/2-summary.md) |
| 서버 경로가 틀렸는데 "중복 가입 거절" 인수 테스트 초록(06 실험 B: DSL 판 3개 중 2개만 실패) | 드라이버가 응답을 `boolean`으로 줄여 404와 409가 같은 값 | 드라이버가 기대 응답이 아니면 예외를 던지나 | [06-4](../06-outside-in-tdd-and-acceptance-tests/2-summary.md) |
| `@Test`가 SUT를 부르기만 하고 단언 없음, 실패하던 단언이 지워짐 | 초록·커버리지 자체를 목표로 삼음 | 단언 없는 테스트 검색, 변이 테스트 | [05-4](../05-tdd/2-summary.md) |
| 정확히 5만 원짜리만 쿠폰 미적용. 예외 없음 | `amount > 50_000`(명세는 "이상"). 테스트는 구간 한가운데 값만 | 명세의 "이상·초과·미만·이하"가 표의 행으로 있나 | [07-1](../07-test-design-techniques/2-summary.md) |
| `IndexOutOfBoundsException: Index 0 out of bounds for length 0`, `ArithmeticException: / by zero`, 페이지 번호 하나 더 | 크기 0·1·가득 참을 분할로 보지 않음 | 빈 입력·최댓값 분할이 테스트에 있나 | [07-2](../07-test-design-techniques/2-summary.md) |
| 주문 이력에 `SHIPPED → CANCELLED`. 예외 없음 | 허용 전이만 시험, 금지 칸은 아무도 안 봄(07 실험: 12번째 행 `Expecting code to raise a throwable.`, AssertJ 3.27.6) | 상태표의 금지 칸이 파라미터 테스트에 있나 | [07-3](../07-test-design-techniques/2-summary.md) |
| 특정 브라우저 + 결제 수단에서만 실패 | 216 조합 중 "대표 하나"만 시험 | 오류 로그가 몰리는 인자 쌍 | [07-4](../07-test-design-techniques/2-summary.md) |
| 같은 문자가 10번 넘게 반복될 때만 운영 데이터 깨짐. 테스트는 매번 `pass (numRuns=100)` | 생성기 분포가 버그 영역에 안 닿음(14 실험: `chars: found in 0/200 seeds`, fast-check 4.10.2) | `fc.statistics`로 분포 측정 | [14-1](../14-property-based-testing/2-summary.md) |
| 성질은 통과하는데 실제로 검사된 입력이 거의 없음 | 사전조건 남용(QuickCheck 논문: 통과한 100건 중 43%가 빈 목록) | 버려진 입력 비율 | [14-4](../14-property-based-testing/2-summary.md) |
| "정리만 했다" 배포 뒤 청구액 변화. 손 테스트 3개 통과, 골든 마스터 15줄 실패(17 실험 B) | 숨은 경로를 지나는 입력이 손 테스트에 없음 | 바꾼 코드 근처를 골든 마스터로 고정했나 | [17-1](../17-characterization-tests-legacy/2-summary.md) |
| 골든 마스터 초록인데 특정 금액만 1원 차이(음수 반값 -40.5원, `double` 표현 오차가 반올림 경계를 넘는 x.xx5) | 변화가 드러나는 입력이 조합에 없거나 다른 변화에 가려짐 | 입력 차원에 바꾸는 부분의 경계가 있나 | [17-5](../17-characterization-tests-legacy/2-summary.md) |
| 헬스 체크·5xx 정상, `HTTP 200` + `{"status":"ERROR","reason":"payment gateway url not configured"}` | 운영 설정 누락. 헬스 체크는 프로세스 생존만 봄 | 업무 결과를 단언하는 합성 점검이 있나(19 실험: v2에서 `checkout PAID` 0/5) | [19-1](../19-testing-in-production/2-summary.md) |
| 카나리 초록, 100% 뒤 오류율 상승 | 카나리 표본이 작아 검출력 낮음(19 실험: 그룹당 200건이면 오류율 두 배인 판을 약 4분의 1만 잡음) | 카나리 표본 수·기간·시간대 | [19-2](../19-testing-in-production/2-summary.md) |

- 이 칸의 증상에는 **테스트 실패 메시지가 없다.** 단서는 운영 메시지·대사·고객 문의다. 그래서 첫 진단은 대개 "그 경로를 **진짜로** 실행한 테스트가 있었나"다.
- 대역(stub·mock·Fake)의 놓침은 대역 자체가 아니라 **대역과 실제 구현 사이의 계약이 고정되지 않은 것**이 원인이다. 공통 처방은 같은 계약 테스트를 대역과 실제 구현에 함께 돌리는 것이다([03-2](../03-test-doubles/2-summary.md), [03-3](../03-test-doubles/2-summary.md), [10-5](../10-testing-time-and-concurrency/2-summary.md)).

### 4. "테스트가 느리다" — 그래서 안 돌린다

| 보이는 것 | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| PR마다 CI 40분(예시), 실패 로그가 브라우저 타임아웃·요소 못 찾음. 테스트 수가 E2E에 몰림 | 아이스크림 콘 — 로직 검증을 E2E로 | 테스트 수를 크기별로 센다. E2E 단언 중 로직 단언 비율 | [01-1](../01-why-test-and-pyramid/2-summary.md) · [18-2](../18-e2e-and-ui-testing/2-summary.md) |
| "단위 테스트"인데 묶음이 수 분 | 단위 테스트가 DB·네트워크·`sleep`을 씀 — SWE@G 기준 small이 아님 | 실행 시간 상위 테스트가 무엇에 접근하나 | [02-4](../02-good-unit-tests/2-summary.md) |
| 실행 시간 상위권이 전부 sleep 테스트. 10 실험 C: TTL 캐시 시험에서 sleep 판 2101ms vs 가짜 시계 판 1.23~2.61ms(JDK 21.0.12, 7회) | 작업이 일찍 끝나도 sleep만큼 다 쉼 | 상위 테스트의 `Thread.sleep` | [10-1](../10-testing-time-and-concurrency/2-summary.md) |
| 클래스·메서드마다 `Container postgres:17 started in PT3.472551658S` 같은 기동 로그가 반복(08 실험의 한 줄, Testcontainers 2.0.5) | 인스턴스 필드 `@Container`(메서드마다 기동) 또는 클래스마다 새 컨테이너 | 기동 로그 수가 테스트 클래스 수(클래스마다 새 컨테이너)인가, 테스트 메서드 수(인스턴스 필드)인가 | [08-3](../08-integration-tests-real-dependencies/2-summary.md) |
| PIT 실행이 수십 분~수 시간, `TIMED_OUT` 변이체 | 대상 범위가 넓고 느린 통합 테스트까지 변이마다 돎 | `targetClasses`·`targetTests` 범위, 변이체 수 × 테스트 시간 | [15-4](../15-mutation-testing/2-summary.md) |
| 규칙 하나 시험에 프레임워크 컨텍스트·DB를 띄움 | Humble Object 부재 — 로직과 접착 코드가 한 객체에 | 그 클래스가 프레임워크 없이 생성되나 | [12-4](../12-test-smells-and-xunit-patterns/2-summary.md) |

- 01 실험의 자릿수: small 1,001개가 2.2~2.9초, medium 1개가 1.2~1.5초에 DB 기동 5.7초가 따로 들었다(JDK 21.0.12 · PostgreSQL 17.11, `--cpus=2`, 3회). 같은 날 재실행 3회에서는 small 2.7~3.2초, medium 1.4~1.6초, 기동 4.1초였다 — 실행마다 다르다. 개당으로 small은 수 밀리초, medium은 초 단위다([01](../01-why-test-and-pyramid/2-summary.md)).
- "느리다"의 처방은 큰 테스트를 지우는 것이 아니다. 로직 단언을 작은 테스트로 **내리고**, 큰 테스트는 조립·경계만 확인하게 남긴다. 큰 테스트를 지우면 3절(놓침) 증상이 돌아온다.

### 5. "커버리지는 높은데 버그가 나간다"

| 보이는 것 (도구 판) | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| JaCoCo 라인 4/4·분기 8/8, PIT `>> Generated 14 mutations Killed 1 (7%)`(15·16 실험 NoAssertTest, JaCoCo 0.8.14 · PIT 1.20.4) | 테스트가 호출만 하고 단언하지 않음. 커버리지 목표를 맞춘 결과(굿하트) | 변이 테스트. 단언 없는·`assertNotNull`뿐인 테스트 검색 | [15-1](../15-mutation-testing/2-summary.md) · [16-1](../16-coverage-and-its-limits/2-summary.md) · [05-4](../05-tdd/2-summary.md) · [01-4](../01-why-test-and-pyramid/2-summary.md) |
| 라인 100%인데 JaCoCo HTML의 노란 다이아몬드 `title="1 of 4 branches missed."`(16 실험 WeakTest) | `&&`의 한 조합(VIP인데 10만 원 미만)을 아무도 실행 안 함 | 라인이 아니라 분기 수치. 결정 테이블로 조합 펼치기 | [16-2](../16-coverage-and-its-limits/2-summary.md) |
| PIT 보고서 `changed conditional boundary → SURVIVED`(15 실험, 7번 줄) | 경계값 테스트 없음 — `>=`가 `>`로 바뀌어도 모름 | 생존한 경계 변이마다 경계값 ±1 추가(실험 79% → 100%) | [15-2](../15-mutation-testing/2-summary.md) · [07-1](../07-test-design-techniques/2-summary.md) |
| 요구사항이 아예 구현 안 됐는데 커버리지 100% | 화이트박스 커버리지는 존재하는 코드만 셈 | 요구사항·인수 기준에서 출발한 테스트가 있나 | [16-3](../16-coverage-and-its-limits/2-summary.md) |
| 전체 커버리지는 높은데 특정 모듈 회귀 | E2E가 지나가면서 실행한 줄 — 결과를 단언하는 테스트 없음 | 단위 커버리지와 통합 커버리지를 나눠 보기 | [16-4](../16-coverage-and-its-limits/2-summary.md) |
| 로컬 JaCoCo 라인 4/4, PIT `Line Coverage … 4/5 (80%)`(16 실험) | 도구마다 세는 단위·필터가 다름 | 게이트가 어느 도구·설정인가 | [16-5](../16-coverage-and-its-limits/2-summary.md) |

- 커버리지는 "실행됐나"를 재고, 변이 점수는 "틀리면 알아채나"를 잰다. 같은 커버리지(라인 4/4·분기 8/8)에서 변이 점수가 7%와 100%로 갈렸다(16 실험 NoAssertTest vs StrongTest).
- 반대 방향의 함정도 있다. 변이 점수 100%를 게이트로 걸면 등가 변이체 앞에서 억지 테스트가 생긴다(15 실험 `abs`: 5개 중 4개, 80%에서 멈춤 — [15-3](../15-mutation-testing/2-summary.md)).

### 6. 실패 메시지는 있는데 원인을 모르겠다

| 보이는 것 (메시지·도구 판) | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| `expected: <true> but was: <false>`뿐(12 실험 a4, JUnit Jupiter 5.13.4) | `assertTrue`만 씀, 단언 메시지 없음 | 단언 대상이 무엇인지 메시지에 있나 | [02-3](../02-good-unit-tests/2-summary.md) · [12-2](../12-test-smells-and-xunit-patterns/2-summary.md) |
| 결함 하나 고치고 다시 돌리면 같은 테스트가 다른 줄에서 또 실패. `expected: <1000> but was: <900>`(12 실험 a1) | Assertion Roulette — 첫 단언 실패에서 멈춰 나머지 결함을 숨김 | 한 테스트의 단언 수. `assertAll`·`SoftAssertions`로 한 번에 보기 | [12-2](../12-test-smells-and-xunit-patterns/2-summary.md) |
| 테스트를 읽어도 무엇을 확인하는지 모름. 기대값 `48_300`의 출처가 안 보임 | Obscure Test — General Fixture, Mystery Guest, 거대 `setUp()` | 결과를 좌우하는 값이 테스트 본문에 있나 | [12-1](../12-test-smells-and-xunit-patterns/2-summary.md) · [11-2](../11-test-data-and-fixtures/2-summary.md) · [02-3](../02-good-unit-tests/2-summary.md) |
| DSL 인수 테스트 `Expecting value to be true but was false`(06 실험 A) | 드라이버가 실패를 값으로 줄임 | 개선 드라이버의 메시지: `register a@x.test: expected HTTP 201 but was 404` | [06-4](../06-outside-in-tdd-and-acceptance-tests/2-summary.md) |
| 반례가 `[68330691,-2079152958]`처럼 크고 실행마다 다름(14 실험, fast-check 4.10.2) | 축소는 탐욕적 국소 탐색 — 두 값을 동시에 줄여야 하는 반례 | 반례의 공통 모양(부호가 반대인 두 수의 차이가 int 범위를 넘음 → 뺄셈 오버플로) | [14-5](../14-property-based-testing/2-summary.md) |
| 공용 값 객체 결함 하나에 빨강 수십 개, 여러 모듈에 흩어짐 | 그 객체를 실행하는 테스트가 함께 결함을 봄(역방향 도달성) | 가장 작은 범위의 실패부터 | [04-3](../04-classical-vs-london/2-summary.md) |

### 7. 테스트·도구가 아예 돌지 않는다

| 보이는 것 (메시지·도구 판) | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| `Could not find a valid Docker environment`, 또는 컨테이너는 떴는데 JDBC 연결 시간 초과 | 러너에 Docker 소켓·그룹 권한이 없음. 컨테이너 안에서 `localhost`로 형제 컨테이너를 찾음 | 소켓 마운트, `TESTCONTAINERS_HOST_OVERRIDE` | [08-4](../08-integration-tests-real-dependencies/2-summary.md) |
| CI 머신 디스크 고갈, `docker ps -a`에 테스트 컨테이너 수백 개 | Ryuk를 끄고 비정상 종료한 실행이 정리 안 됨 | `docker ps -a --filter label=org.testcontainers=true` | [08-5](../08-integration-tests-real-dependencies/2-summary.md) |
| `1 tests did not pass without mutation when calculating line coverage. Mutation testing requires a green suite.`(PIT 1.20.4) | 원본 스위트가 빨강 또는 불안정 | 변이 없이 스위트가 초록·결정적인가 | [15-5](../15-mutation-testing/2-summary.md) |
| 테스트가 끝나지 않아 CI 잡 전체 타임아웃 | `Clock.fixed`로 "시간이 흘러야 끝나는 루프"를 시험(예시, 10 실험 안 함) | 루프 조건이 시계를 읽나. `@Timeout`으로 멈춤을 실패로 | [10-3](../10-testing-time-and-concurrency/2-summary.md) |
| 테스트 20개를 먼저 써서 빨강 20개, 무엇부터 고칠지 모름 | 테스트 목록을 한꺼번에 테스트로 바꿈(Canon TDD의 실수 목록) | 목록은 글로, 테스트는 하나씩 | [05-3](../05-tdd/2-summary.md) |
| 한 테스트를 통과시키려고 한 시간째. 그 사이 다른 테스트도 깨짐 | 한 걸음이 큼, 통과 중에 리팩터링을 섞음 | 마지막 초록으로 되돌리기 | [05-5](../05-tdd/2-summary.md) |
| 새 테스트 하나 통과에 드는 시간이 점점 길어짐, 커밋에 refactor가 없음 | TDD의 리팩터링 단계 생략 | 커밋 로그의 red·green·refactor 비율 | [05-2](../05-tdd/2-summary.md) |

### 8. 배포·운영 검증 단계에서 보이는 증상

| 보이는 것 | 흔한 원인 | 첫 진단 | leaf |
|---|---|---|---|
| 카나리 실패가 잦아 팀이 판정을 건너뜀. 같은 판끼리도 40~53% "실패"(19 실험 순진 규칙, Node 22.23.2) | "카나리 오류율 > 기준 오류율" 같은 순진한 규칙, 지표 과다 | 판정 규칙이 통계 검정인가 | [19-3](../19-testing-in-production/2-summary.md) |
| 고객이 영수증 메일 두 통, 외부 결제사 호출 두 배(19 실험: 메일 10,000 → 20,000) | 섀도 판이 메일·결제·쓰기를 그대로 실행 | 섀도 판의 부수 효과 차단 여부 | [19-4](../19-testing-in-production/2-summary.md) |
| 매출 집계에 테스트 주문, 추천에 테스트 상품 | 합성 요청을 표시·필터하지 않음 | 합성 계정·표시 헤더·집계 필터 | [19-5](../19-testing-in-production/2-summary.md) |
| 소비자의 새 계약이 제공자 main 빌드를 막음 | 소비자가 아직 없는 엔드포인트를 계약에 넣음 | Pact Broker pending pacts(제공자 검증에서 `enablePending`을 켰을 때 동작) | [13-4](../13-contract-testing/2-summary.md) |
| 제공자가 무해한 값(철자·날짜)만 바꿔도 계약 검증 실패 | 소비자 테스트가 매처 없이 정확한 값을 박음, 안 쓰는 필드까지 | 계약의 필드가 소비자가 실제로 쓰는 것뿐인가 | [13-2](../13-contract-testing/2-summary.md) |

## 쓰이는 자료구조·알고리즘

- **역색인**: 이 노트 자체다. leaf의 시나리오(문서)를 증상·메시지(키)로 다시 묶었다. 한 키에 여러 문서가 걸리고(같은 증상, 다른 원인), 한 문서가 여러 키에 걸린다([04-3](../04-classical-vs-london/2-summary.md)은 2절과 6절에 모두 나온다).
- **이분 탐색 — 오염자 찾기**: 순서 의존 실패에서 피해자 앞에 돈 테스트 집합을 반으로 나눠, 피해자와 함께 돌렸을 때 실패가 재현되는 쪽만 남긴다. 테스트 n개면 대략 log₂ n번 실행으로 좁힌다([09-3](../09-flaky-tests/2-summary.md)). 같은 생각을 커밋 이력에 쓰면 `git bisect`다. [이진 탐색](../../algorithm/06-binary-search/2-summary.md).
- **반복 실행 = 베르누이 시행**: 실패 확률 p인 테스트를 n번 돌려 모두 통과할 확률은 (1 − p)^n이다(계산, Python 3).
  - p = 5%, n = 20 → 0.358. 20번 초록이어도 셋 중 하나꼴로 결함이 숨는다.
  - p = 1%, n = 100 → 0.366.
  - 95% 확률로 최소 한 번 실패를 보려면 n ≥ ln 0.05 / ln(1 − p): p = 10%면 29번, 5%면 59번, 1%면 299번.
  - 그래서 "몇 번 돌려 봤는데 괜찮다"는 p가 클 때만 뜻이 있다. 09·10 실험이 반복 횟수와 실패 횟수를 함께 적는 이유다.
- **혼동 행렬(2×2)**: 0절의 네 칸. 거짓 경보율과 놓침률은 한쪽을 낮추면 다른 쪽이 오르기 쉽다. 카나리 판정에서 이 교환이 숫자로 보인다(19 실험, 시드 42). 같은 표본(그룹당 200건)에서 규칙만 바꾸면 순진 규칙은 거짓 경보 40.7%·검출 71.4%, 통계 판정은 5.5%·23.7%다. 교환을 벗어나는 길은 표본이다 — 20,000건이면 통계 판정의 거짓 경보는 5.5%로 그대로이고 검출은 100%다.
- **결정 트리**: 1~3절의 갈래 그림은 "재실행하면 바뀌나 → 단독 실행은? → 날짜와 겹치나" 순으로 묻는 결정 트리다. 싼 질문을 먼저 둔다.

## 적용 — 풀어나가는 법

### 1. 빨강·이상 신호를 받았을 때의 순서

1. **원문 확보**: 실패 메시지 전체, 테스트 이름과 파라미터 번호(`[2]`), 도구 판, 커밋 해시, 러너 이름, 시각.
2. **네 칸 분류**: 재실행하면 바뀌나(불안정) / 제품 동작이 실제로 바뀌었나(거짓 경보 vs 진짜 회귀) / 운영 증상인데 테스트는 초록인가(놓침).
3. **싼 재현부터**: 단독 실행 → 같은 순서로 전체 실행 → 무작위 순서·시드 고정 → 반복 실행으로 실패 비율 측정.
4. **색인에서 갈래를 고른다** → leaf의 시나리오에서 처방을 읽는다.
5. **고친 뒤 같은 재현으로 확인한다**: 반복 실행 실패 0, 무작위 순서 실패 0, 음성 테스트 빨강→초록.

### 2. 첫 진단 명령 모음 (Maven·JUnit 5 기준)

```bash
# 한 테스트만 (단독 실행 vs 전체 실행 비교)
mvn test -Dtest=OrderServiceTest

# 무작위 순서 + 시드 고정 — 순서 의존 재현 (09·11 노트에서 실행)
mvn test -Djunit.jupiter.testmethod.order.default='org.junit.jupiter.api.MethodOrderer$Random' \
         -Djunit.jupiter.execution.order.random.seed=7

# 재시도 없이 N번 — 불안정 비율 측정 (09 실험 C 방식)
for i in $(seq 1 12); do mvn -q test -Dtest=RaceTest > run-$i.log 2>&1; echo "run $i exit=$?"; done

# 재시도가 숨긴 것 보기 — surefire 보고의 Flakes 줄
grep -A3 'Flakes' target/surefire-reports/*.txt
```

- `junit.jupiter.testmethod.order.default`는 JUnit 5.13.4 User Guide 「Test Execution Order」의 설정 키이고, `junit.jupiter.execution.order.random.seed`는 `MethodOrderer.Random` javadoc(5.13.4)에 적힌 키다. 11 노트가 JUnit 5.13.4에서 Maven 명령줄로 실행해 확인했다.
- `| tail` 같은 파이프로 종료 코드를 가리지 않는다. 위 반복문은 `$?`를 각 실행에서 따로 남긴다.

### 3. 증상별 "하지 말 것" 한 줄

| 증상 | 하지 말 것 | 왜 | leaf |
|---|---|---|---|
| CI 가끔 실패 | 재시도·`@Disabled`로 덮기 | 제품의 경쟁 조건을 경고로 낮춘다 | [09-1](../09-flaky-tests/2-summary.md) |
| 리팩터링마다 대량 실패 | 실패 테스트의 기대값·`verify`를 새 구현에 맞춰 일괄 갱신 | 같은 결합을 새 구현에 다시 새긴다 | [02-1](../02-good-unit-tests/2-summary.md) · [17-4](../17-characterization-tests-legacy/2-summary.md) |
| 초록인데 운영 장애 | mock을 더 정교하게 만들기 | 대역이 실제와 다른 것이 원인이다. 계약 테스트·실제 의존으로 | [03-2](../03-test-doubles/2-summary.md) · [08-1](../08-integration-tests-real-dependencies/2-summary.md) |
| 테스트 느림 | 큰 테스트를 통째로 삭제 | 조립·경계 놓침이 돌아온다 | [01-2](../01-why-test-and-pyramid/2-summary.md) · [06-1](../06-outside-in-tdd-and-acceptance-tests/2-summary.md) |
| 커버리지 높은데 버그 | 커버리지 목표를 더 올리기 | 단언 없는 테스트가 더 늘어난다 | [16-1](../16-coverage-and-its-limits/2-summary.md) |

## 장애 시나리오와 대처

### 1. 증상만 끄는 처방 — 재시도·비활성화·기대값 갱신

- **현상**: CI가 몇 달째 초록이다. 그런데 운영에서 합계가 가끔 모자라고, 할인이 1원씩 틀린다.
- **보이는 형태**: surefire `Flakes: 1`이 경고로만 남는다. `@Disabled("flaky")`가 늘어난다. "테스트 수정" 커밋이 기대값만 바꾼다.
- **원인**: 증상(빨강)을 없애는 것과 원인을 고치는 것을 혼동했다. 재시도는 경쟁 조건을 숨기고([09-1](../09-flaky-tests/2-summary.md)), 기대값 붙여 넣기는 버그를 정답으로 고정한다([05-1](../05-tdd/2-summary.md)).
- **대처**: 빨강을 끄는 변경은 리뷰에서 원인 설명을 요구한다. `Flakes`를 실패처럼 수집한다(`failOnFlakeCount`, surefire 3.0.0-M6+). 기대값의 출처(손 계산·명세)를 테스트에 남긴다.

### 2. 같은 증상에 반대 처방 — 대량 실패의 두 원인을 섞음

- **현상**: 리팩터링 PR에 테스트 30개가 빨갛다. 팀이 "테스트가 구현에 묶였다"며 30개의 기대값을 새 출력에 맞춘다. 배포 뒤 금액 오류가 난다.
- **보이는 형태**: 실패 단언이 **호출**이 아니라 **값**이었다. 실패 테스트들이 같은 공용 객체를 실행했다.
- **원인**: 거짓 경보([02-1](../02-good-unit-tests/2-summary.md), [04-1](../04-classical-vs-london/2-summary.md))와 진짜 회귀의 넓은 파급([04-3](../04-classical-vs-london/2-summary.md))을 구별하지 않았다.
- **대처**: 먼저 실패 단언의 종류를 센다. 호출 단언이면 테스트를 관찰 가능한 결과로 옮긴다. 값 단언이 한 객체로 모이면 그 객체의 가장 작은 테스트부터 본다.

### 3. 실패 위치를 원인 위치로 착각

- **현상**: `nothingReservedYet`이 실패해서 그 테스트를 고쳤는데, 다음 날 다른 테스트가 같은 식으로 실패한다.
- **보이는 형태**: 단독 실행은 초록이다. 실패하는 테스트가 순서에 따라 바뀐다(11 실험 A: 20회 중 12회).
- **원인**: 순서 의존에서 실패하는 쪽은 피해자다. 원인은 앞서 돈 오염자의 공유 상태다([11-1](../11-test-data-and-fixtures/2-summary.md), [09-3](../09-flaky-tests/2-summary.md)). 고전파 테스트의 넓은 파급도 같은 구조다([04-3](../04-classical-vs-london/2-summary.md)).
- **대처**: 무작위 순서·시드 고정으로 재현하고, 오염자를 이분 탐색으로 찾는다. 공유 가변 상태를 테스트마다 새로 만든다.

### 4. 테스트 환경이 운영과 다르다는 사실을 모름

- **현상**: 테스트가 다 통과했는데 운영에서만 `25P02`, 404, `name missing`, "결제 게이트웨이 URL 없음"이 난다.
- **보이는 형태**: 같은 기능의 테스트는 H2·stub·Fake·테스트 설정으로 돌았다. 운영 엔진·실제 조립·제공자 실제 응답·운영 설정을 실행한 테스트가 없다.
- **원인**: 테스트가 실행한 것과 운영이 실행하는 것이 다르다([08-1](../08-integration-tests-real-dependencies/2-summary.md), [06-1](../06-outside-in-tdd-and-acceptance-tests/2-summary.md), [13-1](../13-contract-testing/2-summary.md), [19-1](../19-testing-in-production/2-summary.md)).
- **대처**: "운영에서 실행되는 것 중 어떤 테스트도 실행하지 않은 것"을 목록으로 만든다 — DB 엔진, 조립 코드, 외부 계약, 설정 값. 각각 실제 의존 테스트·인수 테스트·계약 테스트·합성 점검으로 덮는다.

### 5. 지표를 게이트로 걸었더니 지표만 좋아짐

- **현상**: 커버리지 80% 게이트, 변이 점수 100% 게이트, "카나리 오류율 > 기준" 규칙을 걸었다. 수치는 좋아졌는데 결함 유출은 그대로이거나, 좋은 판이 자꾸 막힌다.
- **보이는 형태**: 단언 없는 테스트 증가([16-1](../16-coverage-and-its-limits/2-summary.md)), 등가 변이체 앞에서 억지 테스트([15-3](../15-mutation-testing/2-summary.md)), 카나리 판정을 건너뛰는 팀([19-3](../19-testing-in-production/2-summary.md)).
- **원인**: 측정이 목표가 되면 측정을 맞추는 행동이 나온다(굿하트). 각 지표가 재는 것이 좁다.
- **대처**: 지표는 "어디를 볼지" 정하는 데 쓴다. 게이트가 필요하면 변경분 기준, 사람이 검토하는 생존 변이체, 통계 판정처럼 우연을 거르는 형태로 건다.

## 핵심 문장

- 이 노트는 **증상 → 네 칸 분류 → 드러난 시점 → 흔한 원인 → 첫 진단 → leaf** 순서의 역색인이다. 고치지 않고 어느 노트로 갈지 정한다.
- 테스트의 실패는 두 방향이다. 동작이 맞는데 빨강(거짓 경보)과 동작이 틀렸는데 초록(놓침). 두 방향의 처방은 반대다.
- "CI 가끔 실패"는 먼저 재실행·단독 실행·무작위 순서로 무엇에 따라 바뀌는지 가른다. 재시도는 제품의 경쟁 조건까지 숨길 수 있다.
- "리팩터링마다 대량 실패"는 실패 단언이 호출인지 값인지부터 센다. 값 단언이 한 객체로 모이면 진짜 회귀일 수 있다.
- "초록인데 운영 장애"의 첫 질문은 "그 경로를 진짜로 실행한 테스트가 있었나"다. 대역·테스트 DB·테스트 설정이 운영과 다른 지점이 단서다.
- 커버리지는 실행을, 변이 점수는 판별력을 잰다. 어느 지표든 목표로 걸면 지표를 맞추는 테스트가 생긴다.

## 관련 주제·근거

- 선행: 테스트 영역 전체([../README.md](../README.md)). 이 노트의 `NN-k` 링크는 각 leaf 「장애 시나리오와 대처」의 시나리오를 가리킨다(2026-10-03 판을 읽고 대조, 링크는 스크립트로 확인).
- leaf 노트
  - [01-why-test-and-pyramid](../01-why-test-and-pyramid/2-summary.md) · [02-good-unit-tests](../02-good-unit-tests/2-summary.md) · [03-test-doubles](../03-test-doubles/2-summary.md) · [04-classical-vs-london](../04-classical-vs-london/2-summary.md) — 피라미드, 네 기둥, 대역, 학파
  - [05-tdd](../05-tdd/2-summary.md) · [06-outside-in-tdd-and-acceptance-tests](../06-outside-in-tdd-and-acceptance-tests/2-summary.md) · [07-test-design-techniques](../07-test-design-techniques/2-summary.md) — TDD, 인수 테스트, 설계 기법
  - [08-integration-tests-real-dependencies](../08-integration-tests-real-dependencies/2-summary.md) · [09-flaky-tests](../09-flaky-tests/2-summary.md) · [10-testing-time-and-concurrency](../10-testing-time-and-concurrency/2-summary.md) — 실제 의존, 불안정성, 시간·동시성
  - [11-test-data-and-fixtures](../11-test-data-and-fixtures/2-summary.md) · [12-test-smells-and-xunit-patterns](../12-test-smells-and-xunit-patterns/2-summary.md) — 픽스처, 스멜
  - [13-contract-testing](../13-contract-testing/2-summary.md) · [14-property-based-testing](../14-property-based-testing/2-summary.md) · [15-mutation-testing](../15-mutation-testing/2-summary.md) · [16-coverage-and-its-limits](../16-coverage-and-its-limits/2-summary.md) — 계약, 속성, 변이, 커버리지
  - [17-characterization-tests-legacy](../17-characterization-tests-legacy/2-summary.md) · [18-e2e-and-ui-testing](../18-e2e-and-ui-testing/2-summary.md) · [19-testing-in-production](../19-testing-in-production/2-summary.md) — 레거시, E2E, 운영 검증
- 후속: [21-test-incidents](../21-test-incidents/2-summary.md) — 실사건(Apple goto fail 2014, CrowdStrike 2024)에서 놓침이 어떻게 생겼나
- 다른 영역 색인: [software-design/55-design-symptom-index](../../software-design/55-design-symptom-index/2-summary.md)(2절 "테스트에서 보이는 증상"이 설계 원인 쪽) · [reliability/52-reliability-symptom-index](../../reliability/52-reliability-symptom-index/2-summary.md) · [database/56-db-symptom-index](../../database/56-db-symptom-index/2-summary.md) · [distributed/35-distributed-symptom-index](../../distributed/35-distributed-symptom-index/2-summary.md) · [os/37-os-symptom-index](../../os/37-os-symptom-index/2-summary.md)
- 근거 문서
  - Khorikov 『Unit Testing Principles, Practices, and Patterns』(Manning 2020) 4장 — 거짓 양성·거짓 음성 용어(02 노트에서 확인한 범위)
  - SWE@G 11장 — 불안정 비율 1% 언급(09 노트에서 인용)
  - JUnit 5.13.4 User Guide 「Test Execution Order」 <https://docs.junit.org/5.13.4/user-guide/index.html> — `junit.jupiter.testmethod.order.default`. 시드 키는 `MethodOrderer.Random` javadoc <https://docs.junit.org/5.13.4/api/org.junit.jupiter.api/org/junit/jupiter/api/MethodOrderer.Random.html>
  - Maven Surefire 「Rerun Failing Tests」 <https://maven.apache.org/surefire/maven-surefire-plugin/examples/rerun-failing-tests.html> — `rerunFailingTestsCount`, `failOnFlakeCount`(3.0.0-M6+)
  - 메시지는 각 leaf의 실험 출력을 따른다: JUnit 5.13.4·surefire 3.5.3(07·09), Mockito 5.18.0(02·04)·5.24.0(03), AssertJ 3.27.3(03·05·06)·3.27.6(07), H2 2.3.232(03)·2.5.252(08), PostgreSQL 17.11·JDBC 42.7.13·Testcontainers 2.0.5(08), Pact JVM 4.7.5(13), fast-check 4.10.2(14), PIT 1.20.4·JaCoCo 0.8.14(15·16), jsdom 26.1.0·@testing-library/dom 10.4.2(18), k6 1.2.3(19)
- 실험 목록
  - 이 노트는 새 실험을 돌리지 않았다(종합 노트 — 브리핑 §5에서 선택). 메시지·수치는 leaf 01~19의 실험 출력에서 옮겼다.
  - 반복 실행 확률 계산: Python 3 `(1-p)**n`, `ceil(log(0.05)/log(1-p))` — 결과 0.358·0.366, 29·59·299.
  - 사실 점검 대조(2026-10-03): leaf 01~19의 「장애 시나리오와 대처」를 다시 뽑아 90개 시나리오 제목과 이 노트의 `NN-k` 링크를 맞추고, 표의 메시지·수치를 각 leaf 실험 출력과 대조했다.
  - 링크 검증: `scratchpad/ts/20/render20.py`가 leaf 「장애 시나리오와 대처」의 `### k.` 목록을 다시 뽑아, 이 노트에 90개 시나리오가 모두 `[NN-k](../NN-slug/2-summary.md)`로 걸렸는지와 링크 경로가 실재하는지 확인.
