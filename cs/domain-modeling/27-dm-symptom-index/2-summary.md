# domain-modeling/27-dm-symptom-index — 증상 사전: 불법 상태·틀린 숫자·바뀐 과거·어긋난 시각·중복과 유실·예외 메시지 → 모델링 원인·첫 진단·leaf — 정리 (힌트)

## 해결하는 문제

도메인 모델링 영역의 다른 노트는 **원인에서 증상으로** 간다.\
"setter가 공개돼 있다 → 배치가 서비스를 거치지 않고 쓴다 → 결제 안 된 주문이 배송됨"처럼 쓴다.\
현장에서는 반대 방향이 필요하다.\
손에 든 것은 고객 문의 한 건("더치페이 했는데 1원이 비어요"), 대사 배치의 불일치 행, 로그 한 줄(`OptimisticLockException`)뿐이다.

이 노트는 그 **역방향 색인**이다.

```text
  다른 노트 (정방향)                                  이 노트 (역방향)
  모델링 결정 --> 깨지는 규칙 --> 보이는 증상            증상 --> 어떤 모양인가 --> 흔한 모델링 원인 --> 첫 진단 --> leaf
  "배분을 나눗셈 후 각자 반올림으로 했다"              "합이 9,999원이다. 배분인가, 반올림 위치인가, 두 계산의 반올림 방식이 다른가부터"
```

쉬운 예: 병원의 문진표다.\
"배가 아프다"만으로 수술하지 않는다. 문진표가 "어디가, 언제부터, 무엇을 먹은 뒤"를 먼저 묻게 한다.\
문진표는 치료하지 않는다. **어디를 먼저 볼지**만 정한다.

똑같은 구조다.\
"합계가 1원 다르다"라면 먼저 두 숫자가 각각 어디서 왔는지 가른다.\
몫을 각자 반올림해 더했다면 **배분**이 원인이다([14-1](../14-money-arithmetic-rounding-allocation/2-summary.md)).\
한쪽은 줄마다, 다른 쪽은 합계에 반올림했다면 **반올림 위치**가 원인이다([12-1](../12-time-money-and-units/2-summary.md) · [14-2](../14-money-arithmetic-rounding-allocation/2-summary.md)).\
두 계산이 서로 다른 반올림 방식을 썼다면(앱 `HALF_EVEN` vs PostgreSQL `numeric` 반올림, 조용히 자르는 `longValue()`) **반올림 방식 불일치**가 원인이다([14 §3](../14-money-arithmetic-rounding-allocation/2-summary.md)).\
같은 "1원"인데 고치는 자리가 다르다.

실무 예:
- 도메인 모델링 결함은 대개 **예외 없이** 보인다. 불법 상태 행, 1원 차이, 1시간 어긋난 예약, 두 번 적립된 포인트다. 이 영역 leaf 장애 시나리오의 상당수가 "보이는 형태"에 "에러 없음"·"예외 없음"을 적었다(아래 §0).
- 그래서 발견 경로가 늦다. 고객 문의, 정산 대사, 월말 시산표, 감사에서 처음 드러난다.
- 같은 모양의 증상이 서로 다른 층에서 나온다. "목록에 방금 주문이 없다"는 읽기 모델 지연([21-1](../21-cqrs/2-summary.md))일 수도, 시퀀스 구멍([21-2](../21-cqrs/2-summary.md))일 수도 있다. 앞은 기다리면 풀리고 뒤는 영영 안 풀린다.

  - *역색인(inverted index)*: "문서 → 단어" 목록을 뒤집어 "단어 → 문서" 목록으로 만든 것이다. 여기서는 "leaf → 증상"을 "증상 → leaf"로 뒤집었다.
  - *leaf 표기 `NN-k`*: `NN`번 노트 「장애 시나리오와 대처」의 `k`번째 시나리오다. 예: `05-1` = 05번 노트의 시나리오 1(거대 애그리거트의 낙관적 잠금 충돌).
  - *층*: 결함이 사는 곳이다. 이 노트는 열 개로 나눈다 — 진입점·서비스 계층 / 도메인 객체 / 애그리거트·동시성 / 영속(ORM·저장소) / 값(시간·금액·단위) / 이벤트·읽기 모델 / 규칙 버전·결정 기록 / 원장·대사 / 컨텍스트 경계 / 과정·조직.

## 동작·원리

### 0. 증상의 모양 — 대부분 "에러 없음"

```text
  결함이 생긴 뒤 처음 보이는 곳                                      발견 비용
  ┌───────────────────────────────────────────────────────────┐
  │ ① 컴파일·기동      switch 식 망라성 오류, 정책 등록 검사 실패 │   싸다
  │ ② 예외·로그        OptimisticLockException, LazyInit…, 23505 │
  │ ③ 불법 상태 행     "배송됐는데 미결제", 음수 잔액, 용량 초과   │
  │ ④ 숫자 불일치      1원 차이, 합계 0원, 100배 금액            │
  │ ⑤ 시각 어긋남      1시간, 하루 전, 2월 결제 누락             │
  │ ⑥ 중복·유실·유령   포인트 두 번, 롤백됐는데 나간 메일         │
  │ ⑦ 외부와 다름      대사 불일치, 고객 민원, 감사 지적          │
  │ ⑧ 변경 비용·충돌   규칙 사본 N곳, 팀 간 배포 의존             │   비싸다(누적)
  └───────────────────────────────────────────────────────────┘
```

- ③~⑦은 **로그에 아무것도 남지 않는** 경우가 많다. 그래서 첫 진단이 로그 검색이 아니라 **데이터 쿼리**가 된다.
- 좋은 모델링 결정의 상당수는 결함을 위 칸으로 끌어올린다. leaf에서 확인한 예:

| 결함 | 아래 칸에서 보일 때 | 위 칸으로 당긴 모델링 | 당긴 뒤 보이는 형태 | leaf |
|---|---|---|---|---|
| 상태를 추가했는데 분기 하나를 빠뜨림 | ③ 보류 중 주문이 출고됨 | 기본 거부 전이 표, `default` 없는 `switch` 식 | ① 컴파일 오류(Java 14+ switch 식, JLS 15.28.1) | [11-3](../11-state-machines-in-domain/2-summary.md) |
| 새 상품 유형의 정책을 등록 안 함 | ② 운영에서 NPE·500 | 모든 enum 값에 정책이 있는지 시작 시점·테스트 검사 | ① 시작 실패·테스트 실패 | [08-3](../08-domain-services-and-policies/2-summary.md) |
| setter로 불법 상태 저장 | ③ 감사 쿼리에 행 | 의도 메서드 + DB `CHECK` | ② 저장 시 제약 위반 | [06-1](../06-anemic-vs-rich-model/2-summary.md) |
| 통화가 다른 금액 덧셈 | ④ 정산 합계가 터무니없음 | `Money.plus`가 통화 불일치를 거부 | ② 즉시 예외 | [04-2](../04-entities-and-value-objects/2-summary.md) · [12-4](../12-time-money-and-units/2-summary.md) |
| 외부 코드값 변경 | ⑦ 결제가 "실패"로 쌓이고 돈은 빠짐 | ACL 한 곳에서 번역, 모르는 코드는 예외 | ② 번역 실패 예외 | [19-1](../19-anti-corruption-layer/2-summary.md) · [19-2](../19-anti-corruption-layer/2-summary.md) |
| 차대 합이 0이 아닌 전표 | ⑦ 월말 시산표가 0이 아님 | 한 트랜잭션 + 지연 제약 트리거 | ② 커밋 거절 | [24-3](../24-double-entry-ledger/2-summary.md) |
| 판 사이 빈틈 | ④ 정산에서 주문이 조용히 빠짐 | 판을 못 찾으면 예외(`FeeSchedule.at`) | ② 계산 시 예외 | [23-4](../23-versioned-rules-and-effective-dating/2-summary.md) |

- 색인을 쓰기 전에 두 가지를 확보한다.
  - **원본 숫자·행**: 틀린 값 하나가 아니라 "기대값, 실제값, 차이, 같은 차이가 난 건수".
  - **시점**: 언제부터인가. 배포, 규칙(요율) 개정, tzdata 갱신, 월말·윤일·DST 전환일, 외부 시스템 변경과 겹치나.

### 커리큘럼 ⚠ 증상 → 이 노트의 절

| 커리큘럼이 든 증상 | 절 | 대표 leaf |
|---|---|---|
| 불법 상태 데이터 | §1 | [06-1](../06-anemic-vs-rich-model/2-summary.md) · [11-1](../11-state-machines-in-domain/2-summary.md) · [05-2](../05-aggregates-and-invariants/2-summary.md) |
| 1원 정산 차이 | §2 | [12-1](../12-time-money-and-units/2-summary.md) · [14-2](../14-money-arithmetic-rounding-allocation/2-summary.md) |
| 1원 배분 소실 | §2 | [14-1](../14-money-arithmetic-rounding-allocation/2-summary.md) · [15-2](../15-basic-modeling-exercises/2-summary.md) |
| 같은 규칙 N벌 | §7 | [01-1](../01-domain-vs-application-logic/2-summary.md) · [07-1](../07-domain-logic-patterns-and-service-layer/2-summary.md) · [06-3](../06-anemic-vs-rich-model/2-summary.md) |
| 거대 트랜잭션 락 | §6 · §7 | [05-1](../05-aggregates-and-invariants/2-summary.md) · [05-4](../05-aggregates-and-invariants/2-summary.md) |
| 팀 간 모델 충돌 | §7 | [16-1](../16-bounded-contexts/2-summary.md) · [18-1](../18-context-mapping/2-summary.md) |
| 미래 예약 1시간 어긋남 · DST 알람 누락/중복 | §4 | [13-1](../13-instant-vs-local-time-and-tz-rules/2-summary.md) · [13-3](../13-instant-vs-local-time-and-tz-rules/2-summary.md) |
| 과거 금액 재계산 불일치 | §3 | [23-1](../23-versioned-rules-and-effective-dating/2-summary.md) · [22-1](../22-decision-log-and-provenance/2-summary.md) · [22-3](../22-decision-log-and-provenance/2-summary.md) |
| 잔액 원인 불명 | §3 | [24-1](../24-double-entry-ledger/2-summary.md) · [24-2](../24-double-entry-ledger/2-summary.md) |
| 504인데 결제됨(대사) | §5 | [25-1](../25-reconciliation/2-summary.md) · [26-2](../26-advanced-modeling-exercises/2-summary.md) |

- "504"는 커리큘럼의 표현이다. leaf 25는 이를 "PG 호출 타임아웃"으로 쓴다. 게이트웨이가 504를 돌려줬든 클라이언트 타임아웃이든, **요청이 상대에게 처리됐는지 모른다**는 점이 같다.

### 1. 데이터가 불법 상태다 — 예외 없이 규칙을 어긴 행

| 증상(보이는 것) | 층 | 흔한 모델링 원인 | 첫 진단 | leaf |
|---|---|---|---|---|
| **결제 안 됐는데 배송됨·취소됐는데 배송됨** | 도메인 객체 | 상태 setter가 공개돼 관리 도구·배치·스크립트가 서비스를 거치지 않고 씀 | 규칙을 `WHERE`로 옮긴 감사 쿼리(`shipped and not paid`). 행이 생긴 진입점을 쓴 주체·시각으로 추적 | [06-1](../06-anemic-vs-rich-model/2-summary.md) |
| **환불된 주문이 배송됨** | 도메인 객체 | 차단 목록식 전이 검사에 새 상태가 빠짐 | 이력 vs 허용 전이 표 `LEFT JOIN … IS NULL` | [11-1](../11-state-machines-in-domain/2-summary.md) · [11-3](../11-state-machines-in-domain/2-summary.md) |
| **CANCELLED인데 출고 지시도 나감** | 애그리거트·동시성 | 읽고 검사한 뒤 조건 없는 UPDATE | 이력에서 같은 `from_status`에서 출발한 전이 2개 | [11-2](../11-state-machines-in-domain/2-summary.md) |
| **용량 10인 스프린트에 24점·재고 음수·좌석 이중 예약** | 애그리거트·동시성 | 검사(합 읽기)와 쓰기가 다른 행 — 경계 밖 불변식 | 불변식 위반 쿼리(`HAVING sum(points) > capacity`). READ COMMITTED였나 | [05-2](../05-aggregates-and-invariants/2-summary.md) · [05-5](../05-aggregates-and-invariants/2-summary.md) |
| **주문 줄 수량 합 한도 초과, 예외 없음** | 애그리거트·동시성 / 영속 | 자식만 고쳐 루트 버전이 안 오름(자식 엔티티의 필드 변경은 자식만 dirty하게 만든다 — `mappedBy`든 소유 단방향이든 같음, JPA 3.1 §3.4.2). 줄 전용 리포지토리로 루트 우회 | 자식 수정 뒤 루트 `version`이 그대로인가. `*LineRepository` 존재 | [05-3](../05-aggregates-and-invariants/2-summary.md) · [10-2](../10-repositories-and-factories/2-summary.md) |
| **잔액 음수 계좌** | 도메인 객체 | 규칙이 한 서비스 안에만 있고 엔티티 setter가 열림(수수료 배치·관리자 조정이 우회) | `WHERE balance < 0` + 경로별 우회 테스트 | [08-1](../08-domain-services-and-policies/2-summary.md) |
| **동시 결제 두 건 승인 후 잔액 −3,000, 시산표는 정상** | 원장·대사 | 잔액 확인과 분개 기록 사이에 다른 트랜잭션이 낌. REPEATABLE READ 스냅샷에서는 행 잠금으로도 안 막힘 | 캐시 잔액 vs 원장 합, 격리 수준 확인, 동시 이체 테스트 | [24-4](../24-double-entry-ledger/2-summary.md) |
| **HTTP로는 막히는데 큐·배치로 들어오면 통과** | 진입점·서비스 계층 | 업무 불변식을 `@Valid`·컨트롤러 `if`(형식 검증 자리)에 둠 | 진입점 × 위반 입력 테스트 | [01-2](../01-domain-vs-application-logic/2-summary.md) |
| **웹에서는 막히는 작업이 배치·내부 API로 실행됨** | 진입점·서비스 계층 | 권한 검사를 컨트롤러·URL 패턴에만 둠. 메서드 보안 어노테이션 누락 | 진입점 × 권한 없는 사용자 테스트 | [07-5](../07-domain-logic-patterns-and-service-layer/2-summary.md) |
| **배포 후 옛 주문 상태가 엉뚱하게 보임** | 영속 | JPA 기본 `EnumType.ORDINAL`로 저장 중 enum 중간에 상수 삽입 | 매핑 어노테이션과 배포 전후 enum 순서 비교 | [11-4](../11-state-machines-in-domain/2-summary.md) |
| **요청하지 않은 고객 주소도 바뀜** | 영속 / 값 | 같은 가변 `@Embeddable` 인스턴스를 두 엔티티가 공유 | 감사 로그의 예상 밖 UPDATE, 임베더블이 불변인가 | [04-4](../04-entities-and-value-objects/2-summary.md) |
| **조회 API인데 행이 바뀜** | 영속 | 관리 상태 엔티티에서 상태를 바꾸는 메서드를 불러 더티 체킹이 저장 | SQL 로그에서 커밋 직전 `update`, 코드에 `save()` 없음 | [02-4](../02-pojo-and-persistence-ignorance/2-summary.md) |
| **버튼을 눌러도 상태가 안 바뀜, 에러 없음** | 영속 | 저장소 스타일 전환(JPA → Spring Data JDBC) 뒤 `save` 누락 — 더티 추적 없음 | 다시 읽어 확인하는 통합 테스트 | [10-4](../10-repositories-and-factories/2-summary.md) |
| **상태 값에 없는 경우를 운영자가 DB로 직접 고침** | 과정·조직 | 예외 경로가 현장 사람 머릿속에만 있었고 모델에 안 들어감 | 수작업 처리 티켓 주제 집계, 이벤트 스토밍 핫스폿 목록 | [20-1](../20-event-storming/2-summary.md) · [20-3](../20-event-storming/2-summary.md) |

- 불법 상태 행은 **두 가지를 함께** 고친다. 경로를 막지 않고 데이터만 고치면 다음 달 또 생긴다. 경로만 막으면 이미 저장된 행은 그대로다(아래 장애 5).

### 2. 숫자가 틀리다 — 1원·합계·배율

| 증상(보이는 것) | 층 | 흔한 모델링 원인 | 첫 진단 | leaf |
|---|---|---|---|---|
| **10,000원을 셋으로 나눴더니 합 9,999원** | 값(금액) | 배분을 "나눗셈 후 각자 반올림"으로 함 | 원금 vs 몫의 합(`HAVING sum(l.discount) <> o.discount_total`) | [14-1](../14-money-arithmetic-rounding-allocation/2-summary.md) · [15-2](../15-basic-modeling-exercises/2-summary.md) |
| **정산 리포트 수수료 합계 ≠ 거래별 수수료 합** | 값(금액) | 한쪽은 거래마다, 다른 쪽은 합계에 한 번 반올림 | 두 계산의 반올림 위치를 코드에서 찾아 대조 | [12-1](../12-time-money-and-units/2-summary.md) |
| **일부 주문만 PG가 "금액 불일치"로 거절** | 값(금액) | 주문은 줄별 세금 합, 결제 요청은 합계 기준 세금 — 각자 다시 계산 | 결제 요청 금액이 주문에 저장된 확정 금액인가, 다시 계산한 값인가 | [14-2](../14-money-arithmetic-rounding-allocation/2-summary.md) |
| **청구 + 환불 ≠ 월 요금** | 값(금액) | 두 값을 각각 계산해 각각 반올림 | 무작위 대량 입력으로 차이 건수 측정 | [15-2](../15-basic-modeling-exercises/2-summary.md) |
| **엔화 100배·디나르 1/10, 해외 통화 첫 결제에서만** | 값(금액) | `× 100`·`setScale(2)`를 통화와 무관하게 고정 | 0자리(JPY)·3자리(KWD) 통화를 테스트 데이터에 넣어 본다. `Currency.getDefaultFractionDigits()` | [14-3](../14-money-arithmetic-rounding-allocation/2-summary.md) |
| **같은 금액 중복 청구 검사가 통과 → 이중 청구** | 값(금액) | `BigDecimal.equals`가 스케일까지 비교(`1.0` ≠ `1.00`). 입력 경로마다 스케일이 다름 | 같은 금액의 `equals`·`compareTo` 결과, 입력 경로별 스케일 | [14-4](../14-money-arithmetic-rounding-allocation/2-summary.md) |
| **프런트·다른 언어 서비스에서 금액이 1단위 다름** | 값(금액) / 컨텍스트 경계 | 금액을 JSON 숫자로 보냄 — double 파서가 정밀도를 잃음 | 큰 최소 단위 정수(`9007199254740993`)와 소수(`19.99*100`) 왕복 | [14-5](../14-money-arithmetic-rounding-allocation/2-summary.md) |
| **원화 1000 + 달러 5 = 1005** | 값(금액) | 금액이 `long` — 통화가 붙어 있지 않음 | 금액 컬럼 옆에 통화 컬럼이 있나 | [04-2](../04-entities-and-value-objects/2-summary.md) · [12-4](../12-time-money-and-units/2-summary.md) |
| **값이 일정한 배율(4.45배·100배·1000배)로 틀림** | 값(단위) | 단위 없는 숫자가 경계를 넘음. 보내는 쪽·받는 쪽 단위 가정이 다름 | 틀린 비율이 알려진 환산 계수와 같은가(4.45 = lbf→N) | [12-3](../12-time-money-and-units/2-summary.md) · [03-2](../03-ubiquitous-language/2-summary.md) · [28-dm-incidents](../28-dm-incidents/2-summary.md) |
| **재시도가 너무 빨라 외부 API를 두들김** | 값(단위) | 설정 `retry.delay=5`의 단위가 어디에도 없음 | 설정 키 이름·타입에 단위가 있나 | [03-2](../03-ubiquitous-language/2-summary.md) |
| **상류 배포 뒤 주문 합계 0원, 에러 없음** | 컨텍스트 경계 | 관계 미정의 + 하류가 없는 필드를 기본값으로 덮음(`getOrDefault`) | 상류 응답 필드 변경 이력, 번역 코드의 기본값 | [18-1](../18-context-mapping/2-summary.md) · [19-2](../19-anti-corruption-layer/2-summary.md) |
| **0원·NULL·UNKNOWN 상태 행이 늘어남, ACL이 있는데도** | 컨텍스트 경계 | 번역기가 모르는 코드·없는 필드를 기본값으로 바꿈 | 번역 실패 수 지표, 기본값 분기 grep | [19-2](../19-anti-corruption-layer/2-summary.md) |
| **팀마다 "완료 주문 수"가 다름** | 과정·조직 | 한 상태 값이 두 뜻(결제 완료·배송 완료)을 겸함 | 정의를 "참이 되는 조건"으로 적어 팀별로 비교 | [03-1](../03-ubiquitous-language/2-summary.md) |
| **화면과 배치의 연체 건수가 다름** | 영속 | 연체 규칙이 엔티티 메서드와 쿼리 메서드에 따로 복제 | 메모리 판정 vs 쿼리 결과 비교 테스트 | [10-1](../10-repositories-and-factories/2-summary.md) |
| **특정 기간 주문의 수수료가 정산에 없음, 또는 0** | 규칙 버전·결정 | 판 사이 빈틈(끝을 `23:59:59`로 넣음). `EXCLUDE`는 빈틈을 막지 않음 | `LEFT JOIN … IS NULL`로 판을 못 찾은 주문 | [23-4](../23-versioned-rules-and-effective-dating/2-summary.md) |
| **근무 시간·알림 수가 실제보다 적음, 합계만 작음** | 도메인 객체 | 처리 못 한 입력을 세지 않고 건너뜀 | 버린 건수를 세는 관측 창이 있나 | [15-4](../15-basic-modeling-exercises/2-summary.md) |
| **주문 합계와 주문 줄 합이 다름** | 도메인 객체 | `getLines()`가 내부 목록을 그대로 내줌, `setTotal` 별도 호출 | `HAVING o.total <> sum(l.amount)` | [06-2](../06-anemic-vs-rich-model/2-summary.md) |

- "1원"의 흔한 원인은 셋이다: 배분, 반올림 위치, 두 계산의 반올림 방식 불일치([14 §3](../14-money-arithmetic-rounding-allocation/2-summary.md) — PostgreSQL 17.11에서 `round(2.5::numeric)` = 3인데 Java `HALF_EVEN`은 2). 반올림 모드를 다른 하나로 바꾸는 것은 앞의 둘을 고치지 못한다. 셋째도 "더 나은 모드"가 아니라 두 계산을 한 정책으로 맞춰야 풀린다(아래 장애 1).
- 스케일(14-4)과 통화 자릿수(14-3)는 보통 1원이 아니라 다른 모양으로 보인다. 앞은 같은 금액을 다르다고 판정(이중 청구), 뒤는 100배·1/10 배율이나 결제사 거절이다.
- 내부 합 검사가 0건이어도 배분 소실이 없다는 뜻은 아니다. 몫의 합(9,999)과 주문 총액(9,999)을 **같이** 틀리게 저장하면 내부 검사는 통과하고 외부 대사에서만 보인다(아래 실행 확인 (2)·(4)).

### 3. 과거가 바뀐다 — 재계산 불일치·재현 불가·잔액 원인 불명

| 증상(보이는 것) | 층 | 흔한 모델링 원인 | 첫 진단 | leaf |
|---|---|---|---|---|
| **과거 주문을 다시 계산하면 당시 청구액과 다름** | 규칙 버전·결정 | 요율표를 덮어씀 — "그때의 요율"이 없음 | 요율 테이블에 유효 기간·판 번호가 있나, 결과 행에 판 스탬프가 있나 | [23-1](../23-versioned-rules-and-effective-dating/2-summary.md) · [26-1](../26-advanced-modeling-exercises/2-summary.md) |
| **"왜 이 금액인가"를 설명 못 함** | 규칙 버전·결정 | 입력을 참조로만 남겼고 참조 데이터(등급·요율)가 덮어써짐 | 결정 레코드에 입력 스냅샷·규칙 버전이 있나 | [22-1](../22-decision-log-and-provenance/2-summary.md) · [22-3](../22-decision-log-and-provenance/2-summary.md) |
| **6개월 전 결정을 조사하려니 로그가 없음** | 규칙 버전·결정 | 업무 근거를 운영 로그에 맡김(보존 기한·샘플링·레벨) | 결정 근거가 업무 데이터로 있나 | [22-2](../22-decision-log-and-provenance/2-summary.md) |
| **일부 주문에 결정 레코드가 없음** | 규칙 버전·결정 | 결정 기록을 비동기·다른 트랜잭션에 씀 | 업무 행 `LEFT JOIN decision_log … IS NULL` | [22-5](../22-decision-log-and-provenance/2-summary.md) |
| **변조가 없는데 해시 검증이 전부 실패** | 규칙 버전·결정 | 해시 입력이 세션 설정(시간대·로캘)에 따라 달라지는 텍스트 | 실패 시작 시각과 배치 서버·DB 세션 설정 변경 시각 대조 | [22-4](../22-decision-log-and-provenance/2-summary.md) |
| **스탬프 기준 재현성 점검이 갑자기 수백 건 불일치** | 규칙 버전·결정 | 판 행을 UPDATE — "같은 판 = 같은 규칙" 전제가 깨짐 | 판 테이블 행의 최근 변경 | [23-5](../23-versioned-rules-and-effective-dating/2-summary.md) |
| **경계 시각 주문에서 고객이 구 요율 주장, 화면과 영수증이 다름** | 규칙 버전·결정 | 적용 기준 시각(주문? 결제?)이 코드 곳곳에서 암묵적으로 정해짐 | 기준 시각을 쓰는 곳 grep, 결과 행에 기준 시각이 있나 | [23-2](../23-versioned-rules-and-effective-dating/2-summary.md) |
| **개정 첫날 새벽 주문 일부가 구 요율** | 규칙 버전·결정 | 요율이 코드 상수 — 발효를 배포로 표현 | 배포 로그 시각과 요율 전환 시각이 일치하나 | [23-3](../23-versioned-rules-and-effective-dating/2-summary.md) |
| **충전한 금액 일부가 사라졌는데 어느 요청인지 모름** | 원장·대사 | 잔액 열만 UPDATE — 이동의 근거(분개)가 없음 | 잔액의 근거 행이 있나(분개·감사 로그), 로그 보존 기한 | [24-1](../24-double-entry-ledger/2-summary.md) |
| **같은 기간을 다시 조회했더니 합계가 바뀜** | 원장·대사 | 정정을 UPDATE·DELETE로 함 | 원장에 UPDATE·DELETE 권한·트리거가 열려 있나 | [24-2](../24-double-entry-ledger/2-summary.md) |
| **월말 시산표 합이 0이 아님, 언제부터인지 모름** | 원장·대사 | 합 검사가 앱 코드 한 곳에만 — 배치·수기 SQL·이관이 우회. 분개를 여러 트랜잭션에 나눔 | 불균형 전표 목록 쿼리, 검사 배치가 실제로 돌았나 | [24-3](../24-double-entry-ledger/2-summary.md) |
| **실패 응답 뒤에도 잔액이 바뀌어 있음** | 진입점·서비스 계층 | 리포지토리 호출마다 따로 커밋 — 유스케이스 단위 경계 없음 | 이체 로그 없이 잔액만 움직인 건(`LEFT JOIN transfer_log … IS NULL`) | [07-3](../07-domain-logic-patterns-and-service-layer/2-summary.md) |
| **과거 주문 화면이 현재 주소를 보여 줌** | 도메인 객체 | 주문 시점 배송지를 값으로 복사하지 않고 참조 | 주문에 배송지 스냅샷이 있나 | [04-5](../04-entities-and-value-objects/2-summary.md) |

### 4. 시각이 어긋난다

| 증상(보이는 것) | 층 | 흔한 모델링 원인 | 첫 진단 | leaf |
|---|---|---|---|---|
| **특정 지역 예약이 1시간 다름, tzdata 갱신 뒤부터** | 값(시간) | 미래 예약을 옛 규칙으로 계산한 UTC 순간만 저장 — 현지 시각 + tz ID를 버림 | 그 지역의 IANA NEWS 항목, 저장 형식(현지 시각·tz ID가 남았나), 런타임 tzdata 판 | [13-1](../13-instant-vs-local-time-and-tz-rules/2-summary.md) |
| **DST 전환일 알람이 없거나 두 번 울림** | 값(시간) | 벽시계 일치로 실행하거나 첫 실행 순간에 24시간씩 더함 | 그날 발송 로그 0건·2건, 다음 실행 시각 계산식 | [13-3](../13-instant-vs-local-time-and-tz-rules/2-summary.md) |
| **DST 전환일 시간대별 집계 한 칸이 비거나 두 시간치** | 값(시간) | "하루 = 24시간", "모든 현지 시각은 한 번씩 존재" 가정 | 3월 둘째·11월 첫째 일요일(미국 규칙) 그래프, 그날의 실제 길이 | [12-2](../12-time-money-and-units/2-summary.md) |
| **31일 가입자의 2월 결제 누락, 또는 3월부터 28일 결제** | 값(시간) | 날짜 일치 스케줄러, 전 결제일에 1개월씩 더하는 연쇄 계산 | 월별 결제 건수의 출렁임, 기준일 저장 여부 | [13-2](../13-instant-vs-local-time-and-tz-rules/2-summary.md) |
| **해외 사용자에게 생일이 하루 전** | 값(시간) | 시각 없는 날짜를 자정 UTC 순간으로 저장 | 생일 컬럼 타입(`date`인가 `timestamptz`인가) | [13-4](../13-instant-vs-local-time-and-tz-rules/2-summary.md) |
| **윤일·연말에만 예외 또는 무한 루프** | 값(시간) | 날짜 산술을 직접 함(연도 + 1, 366번째 날 처리) | 윤일·366일째를 고정 `Clock`으로 넣은 테스트 | [13-5](../13-instant-vs-local-time-and-tz-rules/2-summary.md) · [28-dm-incidents](../28-dm-incidents/2-summary.md) |
| **계약 갱신일이 윤년마다 하루씩 밀림, 월말 마감이 2월에 어긋남** | 값(시간) | `plusDays(365)`, 월말 상수 | 달력 산술(`plusYears`·`YearMonth.atEndOfMonth`)을 쓰나 | [26-5](../26-advanced-modeling-exercises/2-summary.md) |
| **2박이 3일로 계산, 맞닿은 구간 사이에 길이 0 빈 구간** | 값(시간) | 닫힌 구간 `[start, end]` | "딱 경계" 값 테스트 | [15-1](../15-basic-modeling-exercises/2-summary.md) |
| **매일 수백 건 "내부에만 있음", 다음 날 반대쪽에서 상쇄** | 원장·대사 | 내부는 로컬 날짜, 외부 파일은 UTC 날짜로 자름 | 차이 시각이 특정 시간대(예: KST 00:00~09:00)에 몰리나, 차이가 "저절로 풀리나" | [25-4](../25-reconciliation/2-summary.md) |

- 시각이 정확히 **1시간**(30분 DST 지역이면 30분 — Australia/Lord_Howe, 12·13 실측) 어긋나면 서버 시계보다 tz 규칙·저장 형식을 먼저 본다. NTP 문제는 대개 그렇게 깔끔한 정수 시간으로 나오지 않는다(해석. 시계 동기화는 [distributed/04](../../distributed/04-physical-clocks-and-ntp/2-summary.md)).
- 시각이 정확히 **하루** 어긋나면 날짜를 순간으로 바꾼 곳(13-4)이나 구간 끝 포함 여부(15-1)를 본다.

### 5. 두 번 일어났거나 빠졌다 — 중복·유실·유령

| 증상(보이는 것) | 층 | 흔한 모델링 원인 | 첫 진단 | leaf |
|---|---|---|---|---|
| **카드에서 돈은 나갔는데 주문이 없음(타임아웃·504)** | 원장·대사 | 타임아웃을 실패로 처리하고 주문을 닫음 — 결과를 확정하는 경로 없음 | PG 조회 API로 같은 주문 ID 승인 여부, 대사 키 없는 UNKNOWN 결제 | [25-1](../25-reconciliation/2-summary.md) · [26-2](../26-advanced-modeling-exercises/2-summary.md) |
| **배치 총액이 어긋나는데 실패 건수는 0** | 원장·대사 | 응답 없음(UNKNOWN)을 성공 또는 실패 중 하나로 뭉갬 | 결과 상태가 셋(성공·실패·모름)인가 | [26-2](../26-advanced-modeling-exercises/2-summary.md) |
| **충전이 두 번 기록됨, 시산표는 정상** | 원장·대사 | 멱등 키 없음, 또는 재시도마다 새 키 | 같은 금액·시각대 전표 쌍, 업무 키 `UNIQUE` 유무 | [24-5](../24-double-entry-ledger/2-summary.md) |
| **포인트 두 번 적립** | 이벤트·읽기 모델 | outbox 릴레이는 at-least-once — 소비자 쪽 중복 제거 없음 | 같은 `eventId`로 효과 행 2개 | [09-4](../09-domain-events/2-summary.md) |
| **"주문 완료" 메일을 받았는데 주문이 없음** | 이벤트·읽기 모델 | 트랜잭션 안의 동기 리스너·직접 호출로 바깥 효과 | 메일 로그 `LEFT JOIN orders … IS NULL` | [09-1](../09-domain-events/2-summary.md) |
| **주문은 있는데 포인트가 드문드문 빠짐** | 이벤트·읽기 모델 | AFTER_COMMIT 리스너는 메모리에서 돎 — 예외 미전파, 프로세스가 죽으면 사라짐 | `afterCompletion threw exception` 로그, 커밋 직후 재시작 시각 | [09-2](../09-domain-events/2-summary.md) |
| **AFTER_COMMIT 리스너의 감사 행이 환경마다 저장되거나 안 됨** | 이벤트·읽기 모델 | 그 시점의 쓰기에 커밋이 따라오지 않음(Spring 문서) — 환경별 우연 | 리스너에 `REQUIRES_NEW`가 있나, 데이터소스 설정 차이 | [09-3](../09-domain-events/2-summary.md) |
| **방금 주문이 목록에 없음, 새로고침하면 보임** | 이벤트·읽기 모델 | 읽기 모델 비동기 갱신(지연) | `lag_events`(이벤트 끝 − 체크포인트) | [21-1](../21-cqrs/2-summary.md) |
| **극소수 주문이 목록에 영영 없음** | 이벤트·읽기 모델 | 폴링 프로젝터가 `seq > checkpoint`로 읽는데 seq는 커밋 순서가 아님 | 체크포인트 이하인데 뷰에 없는 이벤트 쿼리 | [21-2](../21-cqrs/2-summary.md) |
| **취소한 주문이 목록에 "주문 완료"로 남음** | 이벤트·읽기 모델 | 프로젝터가 이벤트 종류 하나를 처리 안 함 | 뷰 vs 쓰기 모델 양방향 `EXCEPT` | [21-3](../21-cqrs/2-summary.md) |
| **고객이 몇 주 뒤 "결제했는데 상품이 안 왔다"** | 원장·대사 | 정기 대사 절차가 없음 | 대사 배치가 있나, 돌았나 | [25-2](../25-reconciliation/2-summary.md) |
| **정산 담당자가 엑셀로 금액·시각을 눈으로 맞춤** | 원장·대사 | 외부 거래 ID를 저장하지 않음 | 결제 행에 `pg_tx_id`가 있나 | [25-3](../25-reconciliation/2-summary.md) |
| **대사표는 깨끗한데 입금이 엉뚱한 주문에 붙음** | 원장·대사 | 참조값 없이 금액으로 짝을 찾음 | 짝 키가 참조값인가 금액인가 | [26-3](../26-advanced-modeling-exercises/2-summary.md) · [25-3](../25-reconciliation/2-summary.md) |
| **GET 재시도로 쿠폰이 두 번 발급, 로그 수준에 따라 처리 건수가 다름** | 진입점·서비스 계층 | 조회 메서드가 상태도 바꿈(CQS 위반) | 값을 돌려주는 메서드 중 상태를 바꾸는 것 | [07-4](../07-domain-logic-patterns-and-service-layer/2-summary.md) |
| **쿠폰 목록에 같은 쿠폰이 두 번, 장바구니 삭제가 안 됨** | 도메인 객체 | 값 객체가 참조 동일성을 그대로 씀(`equals` 누락) | 같은 값 두 개의 `equals`, `Set.size()` | [04-1](../04-entities-and-value-objects/2-summary.md) |
| **새 줄을 저장했더니 같은 요청에서 지울 수 없음, 중복 줄** | 영속 | `@GeneratedValue` id가 저장 시 바뀌어 `hashCode`가 바뀜 | 저장 전후 `hashCode`, `contains` | [04-3](../04-entities-and-value-objects/2-summary.md) |
| **연관으로 얻은 고객과 직접 조회한 고객이 다른 사람으로 판정** | 영속 | `equals`가 `getClass()` 비교·필드 직접 접근 — 프록시에서 거짓 | 디버거의 `$HibernateProxy` 클래스 이름 | [02-3](../02-pojo-and-persistence-ignorance/2-summary.md) |
| **중복 이벤트가 성공으로도 거절로도 세짐** | 도메인 객체 | 판정 순서(같은 상태인가 → 표에 있나 → 거부)가 암묵적 | 자기 전이·중복 키 입력으로 경로별 결과 비교 | [15-3](../15-basic-modeling-exercises/2-summary.md) |

### 6. 예외 메시지·로그에서 시작할 때

leaf 실험이 출력한 문구와 leaf가 문서로 확인한 동작만 적는다. 메시지 문구는 제품 버전마다 다를 수 있다.

| 메시지(제품) | 뜻 | 흔한 모델링 원인 | leaf |
|---|---|---|---|
| `jakarta.persistence.OptimisticLockException` / `StaleObjectStateException`(Hibernate 네이티브) — 급증 | 같은 버전 행을 둘이 고침 | 버전 단위가 업무상 독립적인 수정까지 묶는 거대 애그리거트 | [05-1](../05-aggregates-and-invariants/2-summary.md) |
| PostgreSQL `deadlock detected`(SQLSTATE 40P01) | 락 순서가 요청마다 다름 | 한 트랜잭션에서 애그리거트 여럿 수정 | [05-4](../05-aggregates-and-invariants/2-summary.md) |
| SQLSTATE `23505` 중복 키 오류 **뒤에도 잔액이 바뀜** | 앞 단계는 이미 커밋됨 | 유스케이스 트랜잭션 경계 없음 | [07-3](../07-domain-logic-patterns-and-service-layer/2-summary.md) |
| `failed to lazily initialize a collection of role: … could not initialize proxy - no Session`(Hibernate 6.6.29 실험) | 세션이 끝난 뒤 지연 연관 접근 | 도메인 메서드를 트랜잭션 밖(컨트롤러·리스너·비동기)에서 부름. 이벤트에 엔티티를 통째로 넣음 | [02-2](../02-pojo-and-persistence-ignorance/2-summary.md) · [09-5](../09-domain-events/2-summary.md) |
| `org.hibernate.InstantiationException: No default constructor for entity '<이름>'` | 프레임워크가 객체를 못 만듦 | 불변으로 만들려고 인자 없는 생성자를 지움 | [02-5](../02-pojo-and-persistence-ignorance/2-summary.md) |
| `IllegalArgumentException: 시작일이 과거: 2025-01-01`이 **조회** 경로에서 | 재구성이 생성 규칙을 탐 | 행 → 객체 변환이 공개 생성 팩토리를 씀 | [10-3](../10-repositories-and-factories/2-summary.md) |
| `NullPointerException`(정책 맵 조회 결과 null) | 정책 없음 | 새 유형을 만들고 조립 지점에 등록 안 함 | [08-3](../08-domain-services-and-policies/2-summary.md) |
| `TransactionSynchronization.afterCompletion threw exception` | AFTER_COMMIT 리스너 실패 — 호출자는 성공 | 유실되면 안 되는 일을 메모리 리스너에 맡김 | [09-2](../09-domain-events/2-summary.md) |
| `DateTimeException: Invalid date 'February 29' as '2013' is not a leap year`(JDK 21.0.12, 28 실행) | 없는 날짜 생성 | 연도 + 1 같은 직접 날짜 산술 | [13-5](../13-instant-vs-local-time-and-tz-rules/2-summary.md) · [28-dm-incidents](../28-dm-incidents/2-summary.md) |
| 컴파일 오류: switch 식이 enum 상수를 다 다루지 않음(Java 14+, JLS 15.28.1) | **좋은 신호** — 누락이 ③에서 ①로 올라옴 | (원인이 아니라 대책) | [11-3](../11-state-machines-in-domain/2-summary.md) |

- 메시지가 **없는 것**도 신호다. "에러 로그 없음"이 적힌 증상(§1~§5의 대부분)에서는 로그를 더 뒤지기보다 데이터 쿼리로 간다.

### 7. 변경할 때·팀 사이에서 보이는 증상

| 증상(보이는 것) | 층 | 흔한 모델링 원인 | 첫 진단 | leaf |
|---|---|---|---|---|
| **규칙 변경 배포 뒤 일부 경로만 옛 규칙(앱은 막히는데 배치는 취소됨)** | 도메인 객체 | 같은 규칙이 진입점마다 복사됨 — 일부만 수정 | 규칙 상수·조건식 `grep` 전수, 진입점 × 위반 입력 테스트 | [01-1](../01-domain-vs-application-logic/2-summary.md) |
| **"배송 가능" 판정이 서비스마다 다름** | 도메인 객체 | 판정이 객체가 아니라 호출자에 있어 복사·따로 수정 | 같은 조건식 사본 `grep` | [06-3](../06-anemic-vs-rich-model/2-summary.md) |
| **규칙 하나 바꾸는 PR이 스크립트 여러 개, 어떤 유스케이스는 옛 한도** | 진입점·서비스 계층 | 규칙이 늘었는데 Transaction Script 유지 | 같은 상수의 사본 수 | [07-1](../07-domain-logic-patterns-and-service-layer/2-summary.md) |
| **새 유형의 환불 수수료는 맞는데 안내 문구는 일반 기준** | 도메인 객체 | 같은 `if (type == …)` 분기가 여러 곳, 모르는 유형은 `else`로 | 유형 분기 위치 `grep \| uniq -c` | [08-2](../08-domain-services-and-policies/2-summary.md) |
| **상태를 추가했더니 엉뚱한 전이가 열림** | 도메인 객체 | 차단 목록이 새 상태를 모름 | 상태 × 이벤트 전수 테스트 | [11-3](../11-state-machines-in-domain/2-summary.md) |
| **상태 enum이 `PAID_ON_HOLD`처럼 수십 개** | 도메인 객체 | 독립적인 두 축을 한 enum에 곱함 | 상태 이름을 축별로 분해해 본다 | [11-5](../11-state-machines-in-domain/2-summary.md) |
| **필드 하나 추가에 엔티티·DTO·매퍼·리포지토리 수정** | 도메인 객체 | 불변식 없는 CRUD·지원 서브도메인에 풍부한 모델 | 엔티티 메서드가 setter와 같은 일만 하나 | [06-4](../06-anemic-vs-rich-model/2-summary.md) · [07-2](../07-domain-logic-patterns-and-service-layer/2-summary.md) · [17-3](../17-subdomains/2-summary.md) |
| **필드 하나 추가에 PR 5파일 + 재구축 + 배포 순서 조율** | 이벤트·읽기 모델 | 읽기·쓰기 모양이 같은데 CQRS | 조회가 실제로 무거운가 | [21-4](../21-cqrs/2-summary.md) |
| **재구축이 며칠 걸림** | 이벤트·읽기 모델 | 처음부터 폴드 | 스냅샷 유무 | [21-5](../21-cqrs/2-summary.md) |
| **"다른 사용자가 먼저 수정했습니다"가 서로 다른 항목을 고쳐도 남** | 애그리거트·동시성 | 거대 애그리거트 | 루트별 자식 수 분포, 갱신이 몰리는 루트 행 | [05-1](../05-aggregates-and-invariants/2-summary.md) |
| **결제 API가 피크 때 자주 전체 롤백** | 애그리거트·동시성 | 한 트랜잭션에 주문 + 재고 + 포인트 + 쿠폰 | 트랜잭션당 수정 애그리거트 수 | [05-4](../05-aggregates-and-invariants/2-summary.md) |
| **한 팀 배포 뒤 다른 팀 기능이 이상, 배포 팀 테스트는 통과** | 컨텍스트 경계 | 전사 공유 모델의 한 필드(`status`)가 여러 뜻 | 공유 필드의 해석 코드를 소비자별로 찾음 | [16-1](../16-bounded-contexts/2-summary.md) · [03-5](../03-ubiquitous-language/2-summary.md) |
| **특정 날짜 이후 하류 동작이 바뀌었는데 관련 커밋이 다른 팀 저장소** | 컨텍스트 경계 | 공유 값의 해석이 하류에 흩어짐 | 하류가 의존하는 뜻이 메시지 필드로 명시됐나 | [16-2](../16-bounded-contexts/2-summary.md) |
| **스키마 변경마다 여러 팀 공동 배포** | 컨텍스트 경계 | 코드 경계는 나눴지만 테이블 공유 | 마이그레이션 PR 승인 팀 수 | [16-3](../16-bounded-contexts/2-summary.md) |
| **기능 하나에 컨텍스트 서너 개·번역기 같이 수정** | 컨텍스트 경계 | 같은 언어가 통하는 범위를 쪼갬 | 함께 바뀌는 폴더 묶음 | [16-4](../16-bounded-contexts/2-summary.md) |
| **공유 모듈 PR 리드타임이 길고 양 팀 테스트가 깨짐** | 컨텍스트 경계 | 공유 커널이 커짐 | 공유 커널 클래스 중 한쪽만 쓰는 것 | [18-2](../18-context-mapping/2-summary.md) |
| **도메인 코드에 `resCd`·`trdDt` 같은 외부 약어** | 컨텍스트 경계 | 핵심 컨텍스트가 순응자 | 외부 버전 업그레이드 때 핵심 코드 변경량 | [18-3](../18-context-mapping/2-summary.md) · [19-1](../19-anti-corruption-layer/2-summary.md) |
| **통합 직전에 인터페이스가 안 맞음** | 과정·조직 | 상호 의존인데 따로 계획 | 출시 일정 의존 | [18-4](../18-context-mapping/2-summary.md) |
| **업무 규칙 변경인데 ACL 파일을 고침** | 컨텍스트 경계 | 번역과 결정을 구분 안 함 | ACL 안의 할인·취소 판단 | [19-3](../19-anti-corruption-layer/2-summary.md) |
| **레거시 앞 ACL 서비스가 느려지면 신 시스템 전체가 멈춤** | 컨텍스트 경계 | 독립 ACL 서비스의 지연·확장·운영 계획 누락 | ACL 지연 백분위, 타임아웃 | [19-4](../19-anti-corruption-layer/2-summary.md) |
| **자체 인증·PG·알림 유지보수에 팀 시간이 계속** | 과정·조직 | 일반 서브도메인을 직접 만듦 | 스프린트 티켓 분류 | [17-1](../17-subdomains/2-summary.md) |
| **차별화 기능이 벤더 로드맵에 막힘** | 과정·조직 | 핵심을 패키지로 처리 | "벤더 대기" 요구 수 | [17-2](../17-subdomains/2-summary.md) |
| **최고 인력이 이제 시장 표준이 된 기능을 유지보수** | 과정·조직 | 분류를 한 번만 함 | 그 기능 개선이 고객 지표를 움직이나 | [17-4](../17-subdomains/2-summary.md) |
| **한 사람이 회의마다 "개발 쪽 말로는…"** | 과정·조직 | 팀에 언어가 둘 | 요구 문서·티켓·코드 용어 차이 | [03-3](../03-ubiquitous-language/2-summary.md) |
| **회의는 "예약", 코드는 `Hold`, DB는 `reservation_tmp`** | 과정·조직 | 용어 변경을 모델 변경으로 안 봄 | 용어집 "코드 이름" 칸 vs 식별자 | [03-4](../03-ubiquitous-language/2-summary.md) |
| **워크숍 몇 달 뒤 아무도 보드를 기억 못 함, 이벤트 이름이 팀마다 다름** | 과정·조직 | 보드를 추적 가능한 산출물로 안 옮김 | 저장소에 이벤트·명령 목록이 있나 | [20-2](../20-event-storming/2-summary.md) |
| **포스트잇에 "주문 테이블" 같은 명사** | 과정·조직 | 이벤트 대신 데이터 모델부터 | 과거형 문장 비율 | [20-4](../20-event-storming/2-summary.md) |
| **도메인 규칙 테스트가 수 초, 개발자가 안 돌림** | 영속 | 규칙이 지연 연관·리포지토리·스프링 빈에 기댐 | 도메인 테스트의 `@SpringBootTest`·`@DataJpaTest` 수 | [02-1](../02-pojo-and-persistence-ignorance/2-summary.md) · [08-4](../08-domain-services-and-policies/2-summary.md) |
| **엔티티 테스트에 목이 줄줄이, 엔티티 메서드 안 HTTP 실패로 상태가 반쯤 바뀜** | 도메인 객체 | 흐름(외부 호출·알림)을 엔티티에 넣음 | `domain` 패키지의 `RestTemplate`·`@Transactional` import | [01-3](../01-domain-vs-application-logic/2-summary.md) · [06-5](../06-anemic-vs-rich-model/2-summary.md) |
| **`XxxDomainService`가 수백 줄, 엔티티는 getter·setter만** | 도메인 객체 | 한 엔티티로 판단 가능한 규칙을 서비스로 옮김 | 한 엔티티만 다루는 도메인 서비스 메서드 | [01-4](../01-domain-vs-application-logic/2-summary.md) · [08-1](../08-domain-services-and-policies/2-summary.md) |
| **쿠폰을 못 쓰는 이유를 하나씩만 알려줘 손님이 여러 번 시도** | 도메인 객체 | 답할 질문이 둘 이상인데 boolean 하나 | 반환 타입이 결과 enum·사유 목록인가 | [15-5](../15-basic-modeling-exercises/2-summary.md) |
| **유예·늦은 거래·취소 규칙이 운영에서 처음 실행됨** | 과정·조직 | 갈림을 만드는 입력이 테스트 자료에 없음 | 자료에 지연·취소·경계 시각 분포가 있나 | [26-4](../26-advanced-modeling-exercises/2-summary.md) |

### 8. 흔한 오독 — 증상을 보고 잘못 내리는 결론

| 오독 | 왜 틀리나 | 먼저 볼 것 | leaf |
|---|---|---|---|
| "1원 차이니 반올림 모드를 바꾸자" | 배분·반올림 위치가 원인이면 모드를 바꿔도 그대로다. 모드가 원인인 경우는 두 계산의 모드가 **서로 다를** 때이고, 그때도 답은 한 정책으로 맞추는 것이다 | 두 숫자의 출처, 각자 반올림한 위치와 방식 | [14-1](../14-money-arithmetic-rounding-allocation/2-summary.md) · [14-2](../14-money-arithmetic-rounding-allocation/2-summary.md) · [14 §3](../14-money-arithmetic-rounding-allocation/2-summary.md) |
| "`OptimisticLockException`이 늘었으니 재시도를 늘리자" | 버전 단위가 독립 수정을 묶으면 재시도는 부하만 늘린다 | 루트별 자식 수, 충돌하는 수정이 같은 불변식을 건드리나 | [05-1](../05-aggregates-and-invariants/2-summary.md) |
| "낙관적 잠금 충돌이 귀찮으니 버전 열을 빼자" | 예외(②)가 불변식 위반 행(③)으로 내려간다 | 그 버전이 지키던 불변식 | [05-2](../05-aggregates-and-invariants/2-summary.md) · [11-2](../11-state-machines-in-domain/2-summary.md) |
| "시산표가 0이니 원장은 정상" | 이중 기록·음수 잔액은 균형 잡힌 전표 둘로 생긴다 | 업무 키 중복, 캐시 잔액 vs 원장, 외부 대사 | [24-4](../24-double-entry-ledger/2-summary.md) · [24-5](../24-double-entry-ledger/2-summary.md) |
| "대사 차이 0건이니 정상" | 차이를 자동 보정했거나 금액으로 짝을 지었을 수 있다 | 설명 없는 조정 분개 수, 짝 키 | [25-5](../25-reconciliation/2-summary.md) · [26-3](../26-advanced-modeling-exercises/2-summary.md) |
| "타임아웃이니 결제 실패" | 상대는 처리했을 수 있다 | 조회 API·대사로 확정 | [25-1](../25-reconciliation/2-summary.md) |
| "목록에 없으니 저장 실패" | 지연(기다리면 풀림)과 구멍(안 풀림)이 다르다 | `lag_events`, 시퀀스 구멍 쿼리 | [21-1](../21-cqrs/2-summary.md) · [21-2](../21-cqrs/2-summary.md) |
| "1시간 차이니 서버 시계 문제" | tz 규칙·저장 형식이 원인인 경우가 많다(해석) | 그 지역 tz 규칙 변경, 저장 형식 | [13-1](../13-instant-vs-local-time-and-tz-rules/2-summary.md) |
| "에러 로그가 없으니 우리 쪽 문제 아님" | 기본값 번역(`getOrDefault`)은 오류를 지운다 | 0원·UNKNOWN 행 추이, 번역 실패 수 | [18-1](../18-context-mapping/2-summary.md) · [19-2](../19-anti-corruption-layer/2-summary.md) |

## 쓰이는 자료구조·알고리즘

- **역색인**: 이 노트 자체. leaf별 시나리오 목록(정방향)을 증상 키로 뒤집었다.
- **첫 진단 쿼리의 네 모양** — leaf의 진단 쿼리 대부분이 이 넷 중 하나다.

| 모양 | 질문 | SQL 형태 | 쓰는 leaf |
|---|---|---|---|
| (1) 규칙 → `WHERE` | 규칙을 어긴 행이 있나 | `SELECT … WHERE <규칙의 부정>` | 05 · 06 · 08 · 11 |
| (2) 부모 vs 자식 합 | 합계가 맞나 | `GROUP BY 부모 HAVING 부모값 <> sum(자식)` | 06 · 14 · 24 |
| (3) 키당 2건 이상 | 중복인가 | `GROUP BY 업무키 HAVING count(*) > 1` | 09 · 24 · 25 |
| (4) 양쪽 대조 | 한쪽에만 있나, 값이 다른가 | `LEFT JOIN … IS NULL`(anti-join), `FULL OUTER JOIN`, 양방향 `EXCEPT` | 09 · 21 · 22 · 23 · 25 |

  - *anti-join*: "짝이 없는 행"만 남기는 조인이다. `LEFT JOIN`한 뒤 오른쪽 키가 `NULL`인 행을 고른다.
  - `EXCEPT`는 조인이 아니라 집합 연산이다. 21의 EXPLAIN(PostgreSQL 17.11)에서 `EXCEPT`는 `HashSetOp Except`, 같은 대조를 `NOT EXISTS`로 쓰면 `Hash Anti Join`이었다.
- **차대 합 0 검사**, **전이 표 대조**, **반열린 구간 `[from, to)` 조회**, **버전 번호 비교**, **최대 잔여 배분**: 각각 [24](../24-double-entry-ledger/2-summary.md), [11](../11-state-machines-in-domain/2-summary.md), [23](../23-versioned-rules-and-effective-dating/2-summary.md), [05](../05-aggregates-and-invariants/2-summary.md), [14](../14-money-arithmetic-rounding-allocation/2-summary.md)에서 다룬다.
- 조인 알고리즘(해시 조인 등)은 [database](../../database/README.md) 영역에서 다룬다.

## 적용 — 풀어나가는 법

### 1. 모양으로 1차 분류한다

```text
  증상 하나
    │
    ├─ 예외·로그가 있다 ──────────────▶ §6 메시지 표
    │
    └─ 없다
         ├─ 상태가 말이 안 된다 ────────▶ §1  (쿼리 모양 1)
         ├─ 숫자가 틀리다
         │    ├─ 1원·몇 원 ────────────▶ §2  배분 / 반올림 위치 / 반올림 방식 불일치
         │    ├─ 일정한 배율 ───────────▶ §2  단위·통화
         │    └─ 과거 값이 바뀜 ────────▶ §3  덮어쓰기·참조 입력
         ├─ 시각이 틀리다
         │    ├─ 정확히 1시간 ──────────▶ §4  tz 규칙·DST
         │    └─ 정확히 하루·한 달 ─────▶ §4  날짜↔순간 변환·구간 끝·달력 산술
         ├─ 두 번 / 빠짐 / 유령 ────────▶ §5  (쿼리 모양 3·4)
         └─ 변경·팀 사이가 힘들다 ──────▶ §7
```

- 다음으로 **시점**을 겹쳐 본다: 배포, 요율 개정(23), tzdata 갱신(13), 월말·윤일·DST 전환일(13), 상류 배포(18·19), 저장소·프레임워크 교체(10).

### 2. 첫 진단 세트

```bash
# 같은 규칙의 사본 — 규칙 상수·조건식 (01·06·07·08)
grep -rn "1_000_000" src/main/java                      # 예: 한도 상수
grep -rn --include=*.java -E 'equals\("(PROMO|SUB|NORMAL)"\)|case (PROMO|SUB|NORMAL)' src | cut -d: -f1 | sort | uniq -c
# 루트 우회 경로 (10)
grep -rln --include=*.java -E 'interface \w*(Line|Item|Detail)\w*Repository' src
# 도메인이 흐름·인프라를 아는가 (01·06·08)
grep -rlE 'import .*(RestTemplate|KafkaTemplate|EntityManager|Transactional)' --include=*.java src/main/java | grep '/domain/'
```

```java
// 런타임 tzdata 판 (13) — JDK 21
java.time.zone.ZoneRulesProvider.getVersions("UTC").lastEntry().getKey();
```

- grep 명령은 leaf 진단 절의 것을 모았다. 경로·패턴은 저장소에 맞게 바꾼다.

### 실행 확인: 쿼리 네 모양

장난감 스키마에 이상 행을 심고 네 모양을 돌렸다.

(실험, PostgreSQL 17.11 일회용 컨테이너 `--cpus=2 --network none`, 2026-10-03)

```sql
INSERT INTO orders VALUES (1,10000,'PAID',true,false),(2,9999,'PAID',true,false),
  (3,5000,'SHIPPED',false,true),(4,7000,'PAID',true,false),(6,12000,'PAID',true,false);
INSERT INTO order_line VALUES (1,3333),(1,3333),(1,3334),(2,3333),(2,3333),(2,3333),
  (3,5000),(4,7000),(6,6000),(6,5000);
INSERT INTO payment VALUES (1,'T1',10000),(2,'T2',9999),(4,NULL,7000);          -- 내부
INSERT INTO pg_settlement VALUES (1,'T1',10000),(2,'T2',10000),(4,'T4',7000),
  (4,'T5',7000),(5,'T6',3000);                                                  -- 외부(PG)
-- (4) 양쪽 대조
SELECT coalesce(i.order_id, e.order_id) AS order_id, i.amount AS internal, e.amount AS external,
  CASE WHEN i.order_id IS NULL THEN 'EXTERNAL_ONLY' WHEN e.order_id IS NULL THEN 'INTERNAL_ONLY'
       WHEN i.amount <> e.amount THEN 'AMOUNT_MISMATCH' END AS kind
FROM payment i FULL OUTER JOIN pg_settlement e ON e.pg_tx_id = i.pg_tx_id
WHERE i.order_id IS NULL OR e.order_id IS NULL OR i.amount <> e.amount ORDER BY 1, 4;
```

```text
-- (1) 불변식 위반 행: 규칙을 WHERE로 옮겨 센다 (배송됐는데 미결제)
 id | status  
----+---------
  3 | SHIPPED
(1 row)

-- (2) 합계 불일치: 부모 값 vs 자식 합 (HAVING)
 id | total | lines 
----+-------+-------
  6 | 12000 | 11000
(1 row)

-- (3) 같은 키 2건 이상: 중복
 order_id | count | string_agg 
----------+-------+------------
        4 |     2 | T4,T5
(1 row)

-- (4) 양쪽 대조: 한쪽에만 있음 + 금액 불일치 (FULL OUTER JOIN)
 order_id | internal | external |      kind       
----------+----------+----------+-----------------
        2 |     9999 |    10000 | AMOUNT_MISMATCH
        4 |          |     7000 | EXTERNAL_ONLY
        4 |          |     7000 | EXTERNAL_ONLY
        4 |     7000 |          | INTERNAL_ONLY
        5 |          |     3000 | EXTERNAL_ONLY
(5 rows)
```

관찰:
- 주문 2는 줄 합(9,999)과 총액(9,999)이 **같이** 틀려 (2)에 나오지 않았다. 외부 대조 (4)에서만 `AMOUNT_MISMATCH`로 보였다. 배분 소실(14-1)이 일관되게 저장되면 내부 검사는 통과한다.
- 이 쿼리의 `EXTERNAL_ONLY`·`INTERNAL_ONLY`는 25 실험 분류의 `MISSING_INTERNAL`(외부에만 있음)·`MISSING_EXTERNAL`(내부에만 있음)에 해당한다. 이름만 다르다.
- 주문 4는 내부 결제에 외부 거래 ID가 없어(`pg_tx_id` NULL) 한쪽에만 있는 행 셋으로 갈렸다. 거래 ID를 저장하지 않으면(25-3) 키 대조가 깨지고 금액 매칭에 기대게 된다(26-3).
- 외부에는 같은 주문 ID의 승인이 둘(T4·T5)이다. 25의 대사 분류로는 DUPLICATE_EXTERNAL(재시도에 멱등 키 없음)의 모양이다. 고객이 **새 주문으로** 다시 결제한 경우(25-1)는 주문 ID가 달라 이 모양으로 나오지 않는다. 25-1은 그 경우를 같은 고객·금액·가까운 시각으로 따로 묶어 찾는다.
- 장난감 데이터라 건수에 의미는 없다. 쿼리 모양이 어떤 증상을 잡고 어떤 증상을 놓치는지만 본다.

### 3. leaf로 간다

- §1~§8에서 후보 leaf를 고른다. 후보가 여럿이면 각 leaf 시나리오의 "보이는 형태"와 내 관찰을 대조해 지운다.
- 원인이 도메인 모델 밖이면 다른 색인으로 간다.
  - 설계 일반(결합·추상화·DI·프록시): [software-design/55-design-symptom-index](../../software-design/55-design-symptom-index/2-summary.md)
  - SQLSTATE·풀·ORM·격리 수준: [database/56-db-symptom-index](../../database/56-db-symptom-index/2-summary.md)
  - 메시지 중복·사가·시계: [distributed/35-distributed-symptom-index](../../distributed/35-distributed-symptom-index/2-summary.md)
  - 타임아웃·재시도·배포·관측: [reliability/52-reliability-symptom-index](../../reliability/52-reliability-symptom-index/2-summary.md)
- 실제 사건에서 이 증상들이 어떻게 이어졌는지는 [28-dm-incidents](../28-dm-incidents/2-summary.md)에 있다(단위 불일치, 회계 불일치, 윤일, 시간대 규칙 변경).

## 장애 시나리오와 대처

이 절은 **색인을 읽는 실수**를 다룬다. 증상 자체는 위 표와 leaf에 있다.

### 1. 1원 차이를 반올림 모드 변경으로 닫는다

- **현상**: 더치페이 합이 9,999원이라는 문의가 왔다. `HALF_UP`을 `HALF_EVEN`으로 바꿔 배포했다. 다른 금액에서 같은 문의가 계속 온다.
- **보이는 형태**: 원장 대사의 1원 차액 행이 줄지 않는다. 금액에 따라 차이가 나는 건과 안 나는 건이 바뀔 뿐이다.
- **원인**: 원인이 배분(나눗셈 후 각자 반올림)이었다. 3,333.33…을 가장 가까운 값으로 보내는 모드(`HALF_UP`·`HALF_EVEN`·`HALF_DOWN`)는 모두 3,333을 내고 합은 9,999다. 내림 계열(`DOWN`·`FLOOR`)도 9,999다. 올림 계열(`UP`·`CEILING`)로 바꾸면 3,334씩 합 10,002로 반대쪽에 틀린다(실험, JDK 21.0.12 `Modes.java` — 일곱 모드 모두 합이 10,000이 아니었다. 14-1). 반올림 위치(14-2)도 모드 하나를 바꿔서는 풀리지 않는다. 모드가 원인인 경우는 대개 두 계산이 서로 다른 모드를 쓸 때다(14 §3).
- **대처**: 두 숫자의 출처를 먼저 가른다(§2). 배분이면 배분기와 "합 == 원금" 불변식(14-1), 위치면 계산 정책 하나로 모으고 확정 금액 재사용(14-2), 방식 불일치면 앱·DB가 같은 반올림 정책을 쓰게 하거나 한쪽에서만 반올림한다(14 §3).

### 2. 버전 충돌 예외를 재시도·잠금 해제로 덮는다

- **현상**: "다른 사용자가 먼저 수정했습니다"가 잦아 재시도 횟수를 3 → 10으로 올렸다. 응답 시간이 더 늘었다. 결국 `@Version`을 뺐다. 이번엔 스프린트 용량 초과 행이 생긴다.
- **보이는 형태**: 처음에는 `OptimisticLockException`과 재시도 로그 급증(05-1). `@Version`을 뺀 뒤에는 예외 없는 위반 데이터(05-2).
- **원인**: 버전 단위가 업무상 독립적인 수정까지 묶는 거대 애그리거트였다. 재시도는 같은 충돌을 반복하고, 잠금 해제는 ②의 예외를 ③의 조용한 위반으로 내렸다.
- **대처**: 진짜 불변식을 다시 적고, 그 불변식이 걸치지 않는 자식을 별도 애그리거트로 떼어 ID로 참조한다. 쪼갠 뒤 같은 시나리오로 충돌 수를 다시 잰다(05-1). 너무 잘게 쪼개지 않는다(05-5).

### 3. "시산표 0·대사 0건"을 정상의 증거로 읽는다

- **현상**: 월말 시산표가 0이고 대사 차이도 0건이다. 그런데 감사에서 이중 충전 전표와 내부 금액이 외부 값으로 덮어써진 흔적이 나온다.
- **보이는 형태**: 같은 금액·같은 시각대의 균형 잡힌 전표 쌍(24-5). 설명 없는 조정 분개가 많다(25-5). 금액 매칭으로 짝지은 줄이 엉뚱한 주문에 붙어 있다(26-3).
- **원인**: 시산표는 "각 전표의 차대 합이 0"만 본다. 중복·음수 잔액은 균형 잡힌 전표로도 생긴다(24-4·24-5). 대사 0건은 자동 보정이나 금액 매칭이 차이를 지운 결과일 수 있다.
- **대처**: 지표가 0일 때도 세 가지를 따로 본다. 업무 키 중복(쿼리 모양 3), 설명 없는 조정 분개 수, 짝 키가 참조값인가. 대사 차이는 먼저 사건으로 남기고, 자동 처리는 원인이 정해진 분류만 한다(25-5).

### 4. 1시간 어긋남을 서버 시계 문제로 본다

- **현상**: 한 지역 고객의 예약 알림이 1시간 늦게 간다. 팀은 NTP 동기화를 점검하고 서버 시계를 맞췄다. 그대로다.
- **보이는 형태**: 에러 없음. 그 지역 예약에서만, JDK·OS 업데이트(tzdata 갱신) 뒤부터 생긴다(13-1).
- **원인**: 미래 예약을 옛 규칙으로 계산한 UTC 순간으로만 저장했다. 규칙이 바뀐 뒤에도 옛 순간이 그대로 남았다. 시계는 맞았고 **규칙**이 바뀌었다.
- **대처**: 증상이 특정 지역·특정 날짜 이후에만 있고 어긋남이 그 지역 DST 폭(대개 1시간, Lord_Howe는 30분)과 같으면 tz 규칙부터 본다(IANA NEWS). 원본을 현지 시각 + tz ID로 저장하고 규칙 판을 기록해 갱신 때 재계산한다(13-1). 시계 동기화 문제의 모양은 [distributed/04](../../distributed/04-physical-clocks-and-ntp/2-summary.md).

### 5. 불법 상태 행을 SQL로만 고친다 — 또는 UPDATE로 고쳐 흔적을 지운다

- **현상**: "결제 안 됐는데 배송됨" 행을 SQL로 고쳤다. 다음 달 같은 행이 또 생긴다. 다른 팀은 잘못 들어간 전표 금액을 UPDATE로 고쳤다. 다음 달 정산 보고서가 이미 보낸 보고서와 다르다.
- **보이는 형태**: 정합성 쿼리 결과가 매달 0이 아니다(06-1). 같은 기간을 다시 조회했더니 합계가 바뀌었고 원장에 흔적이 없다(24-2).
- **원인**: 결과(데이터)만 고치고 경로(공개 setter·우회 진입점)를 그대로 뒀다. 원장에서는 정정을 덮어쓰기로 해 과거 보고서의 근거를 지웠다.
- **대처**: 경로와 데이터를 **둘 다** 고친다. 경로는 의도 메서드·DB `CHECK`·전이 표로 막는다(06-1·11-1). 데이터는 원천 기록(결제·배송 이벤트)으로 판정해 업무 담당자와 정정한다. 원장은 역분개 + 재분개로 고치고 원 전표를 가리킨다(24-2).

## 핵심 문장

- 이 노트는 **증상 → 모양 → 흔한 모델링 원인 → 첫 진단 → leaf** 순서의 역색인이다. 고치지 않고 어느 노트로 갈지 정한다.
- 도메인 모델링 결함은 대개 예외 없이 불법 상태 행·틀린 숫자·어긋난 시각·중복으로 보인다. 그래서 첫 진단은 로그 검색보다 데이터 쿼리다.
- 첫 진단 쿼리는 대부분 네 모양이다: 규칙을 `WHERE`로, 부모 vs 자식 합, 키당 2건 이상, 양쪽 대조(anti-join·FULL OUTER JOIN·EXCEPT).
- "1원"의 흔한 원인은 배분·반올림 위치·두 계산의 반올림 방식 불일치이고, "정확히 1시간"은 대개 tz 규칙·저장 형식이다. 숫자의 모양이 원인을 좁힌다.
- 시산표 0·대사 0건·에러 로그 0건은 정상의 증거가 아니다. 균형 잡힌 중복, 자동 보정, 기본값 번역이 차이를 지울 수 있다.
- 좋은 모델링 결정의 상당수는 결함을 더 이른 칸(컴파일·저장 시 제약·즉시 예외)으로 끌어올린다. 그 신호를 재시도·잠금 해제·기본값으로 덮지 않는다.

## 관련 주제·근거

- 선행: 도메인 모델링 영역 전체([../curriculum.md](../curriculum.md)). 이 노트의 `NN-k` 링크는 각 leaf의 「장애 시나리오와 대처」 시나리오를 가리킨다(2026-10-03 판을 읽고 대조).
- 특히 자주 가리키는 leaf
  - [05-aggregates-and-invariants](../05-aggregates-and-invariants/2-summary.md) · [06-anemic-vs-rich-model](../06-anemic-vs-rich-model/2-summary.md) · [11-state-machines-in-domain](../11-state-machines-in-domain/2-summary.md) — 불법 상태, 경계 밖 불변식, 불법 전이
  - [12-time-money-and-units](../12-time-money-and-units/2-summary.md) · [13-instant-vs-local-time-and-tz-rules](../13-instant-vs-local-time-and-tz-rules/2-summary.md) · [14-money-arithmetic-rounding-allocation](../14-money-arithmetic-rounding-allocation/2-summary.md) — 1원·배율·1시간·하루
  - [22-decision-log-and-provenance](../22-decision-log-and-provenance/2-summary.md) · [23-versioned-rules-and-effective-dating](../23-versioned-rules-and-effective-dating/2-summary.md) · [24-double-entry-ledger](../24-double-entry-ledger/2-summary.md) · [25-reconciliation](../25-reconciliation/2-summary.md) — 바뀐 과거, 잔액 원인 불명, 504인데 결제됨
  - [16-bounded-contexts](../16-bounded-contexts/2-summary.md) · [18-context-mapping](../18-context-mapping/2-summary.md) · [19-anti-corruption-layer](../19-anti-corruption-layer/2-summary.md) — 팀 간 모델 충돌, 기본값 번역
- 후속: [28-dm-incidents](../28-dm-incidents/2-summary.md) — 실사건(Mars Climate Orbiter 1999, Post Office Horizon, Azure 2012 윤일, 시간대 규칙 변경)
- 다른 영역 색인: [software-design/55-design-symptom-index](../../software-design/55-design-symptom-index/2-summary.md) · [database/56-db-symptom-index](../../database/56-db-symptom-index/2-summary.md) · [distributed/35-distributed-symptom-index](../../distributed/35-distributed-symptom-index/2-summary.md) · [reliability/52-reliability-symptom-index](../../reliability/52-reliability-symptom-index/2-summary.md)
- 기존 연습 컬렉션: [../basic/](../basic/) · [../advanced/](../advanced/) — 연습에서 자주 틀리는 실수는 [15-basic-modeling-exercises](../15-basic-modeling-exercises/2-summary.md) · [26-advanced-modeling-exercises](../26-advanced-modeling-exercises/2-summary.md)의 장애 절
- 근거 문서
  - 커리큘럼 §13 27행(⚠ 증상 목록) — `docs/plans/2026-09-27/cs-fundamentals-roadmap/curriculum.md`
  - 메시지·동작은 각 leaf의 실험·문서를 따른다: Hibernate 6.6.29(02 실험), JPA 3.1 §2.6·§3.4.2(04·05), JLS 15.28.1(11), `BigDecimal.equals` javadoc(14), Spring `@TransactionalEventListener` 문서(09), Spring Data JDBC 문서(10), IANA tz NEWS(13)
- 실험 목록
  - 반올림 모드와 3등분: `scratchpad/dm/27/e27/Modes.java` — `10000/3`을 일곱 모드로 `setScale(0)` 후 ×3. JDK 21.0.12 temurin 일회용 컨테이너(`--cpus=2 --network none`). 출력 `modes-out.txt`: HALF_UP·HALF_EVEN·HALF_DOWN·DOWN·FLOOR 9999, UP·CEILING 10002.
  - 쿼리 네 모양: `scratchpad/dm/27/e27/shapes.sql` — PostgreSQL 17.11 일회용 컨테이너(`sn-dm-w27-pg`, `--cpus=2 --network none`, 실행 뒤 `docker rm -fv`). `docker exec sn-dm-w27-pg psql -U postgres -q -f /w/shapes.sql`. 출력 `e27/out.txt`.
