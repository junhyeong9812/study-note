# distributed/22-event-sourcing — 이벤트 소싱: 이벤트를 원천으로, 스냅샷·재생·버전 — 정리 (힌트)

## 해결하는 문제

보통 저장소는 현재 값만 둔다. `UPDATE account SET balance = 8000`을 하면 그 전 값과 바뀐 이유가 사라진다.

```text
  상태 저장                         이벤트 소싱
  account(acc-1) balance=8000       events(acc-1): v1 Opened | v2 Deposited(10000) | v3 Withdrawn(2000)
  "왜 8000?" → 답 없음                현재 상태 = 처음부터 접은(fold) 결과 = 8000
                                    "왜 8000?" → 이벤트 목록이 답
```

- *이벤트 소싱*: 상태를 바꾼 사건(이벤트)을 순서대로 붙여 저장한다(Fowler 2005 "Capture all changes to an application state as a sequence of events"). 이 노트의 구성은 이벤트 로그를 **진실의 원천**으로 삼고, 현재 상태를 이벤트를 접어 얻는 파생값으로 둔다. Fowler는 DB의 현재 상태를 정본(system of record)으로 두고 이벤트를 함께 남기는 구성도 언급한다.
- 얻는 것(Fowler 2005)
  - *Complete Rebuild*: 상태를 버리고 이벤트를 다시 돌려 재구축한다.
  - *Temporal Query*: 어느 시점의 상태든 그 시점까지만 접어 얻는다.
  - *Event Replay*: 잘못된 과거 이벤트를 고쳐 그 뒤를 다시 계산한다.

쉬운 예: 통장 거래내역이다.
- 잔액만 적은 쪽지는 "왜 이 금액인가"에 답하지 못한다. 거래내역이 있으면 위에서부터 더하면 잔액이 나온다.
- 잘못 입금된 건은 지우지 않고 반대 거래를 새로 적는다.

똑같은 구조다.\
이벤트는 고치거나 지우지 않고 붙이기만 한다. 대신 읽을 때 접는 비용, 옛 이벤트 형식을 계속 읽어야 하는 부담이 생긴다.

실무 예:
- 원장·회계: 전표가 원천이고 잔액은 집계다.
- 주문 이력: "결제 → 부분 취소 → 재결제" 흐름을 감사·분쟁 대응에 그대로 재현한다.
- git도 닮았지만, 커밋이 변경분이 아니라 트리 스냅샷을 가리키므로 "재생"은 비유다(원본 ops-patterns/16의 정정).

기초는 원본 두 편에 있다.
- [systems/event-sourcing](../../systems/event-sourcing/2-summary.md) — 얻는 것·내주는 것, `XxxUpdated` 안티패턴, 언제 거부하나, 부분 이벤트 소싱과 대사.
- [ops-patterns/16-event-sourcing](../../ops-patterns/16-event-sourcing/2-summary.md) — 명령 vs 이벤트, 재생 중 검증 금지, Opened 초기화, 낙관적 잠금 코드, 반대 이벤트.

이 노트는 분산·운영 쪽 빈 곳을 실험으로 채운다: 동시 쓰기, 재생 비용과 스냅샷, 스키마 변경, 재생의 부작용.

## 동작·원리

### 1. 쓰기 경로 — 명령 → 검증 → 기대 버전으로 붙이기

```text
  명령 "700 출금해라"
   │ ① 스트림 acc-1의 이벤트를 읽는다 (또는 스냅샷 + 그 뒤)       → 현재 version = 3
   │ ② 접어서 상태를 만든다                                      → 잔액 1000
   │ ③ 검증: 1000 ≥ 700 → 통과                                   ← 검증은 여기 한 번
   │ ④ append(acc-1, expectedVersion=3, Withdrawn(700))
   │      저장소: "지금도 version 3인가?" ─ 예 → v4로 붙임
   │                                    └ 아니오 → 충돌 → ①부터 다시
   ▼
  이벤트 저장소 (스트림별 append-only 로그)
```

- *스트림*: 한 애그리게이트(계좌 하나)의 이벤트 목록. 이벤트마다 스트림 안 순번(version)이 붙는다.
- *기대 버전(expected version)*: "내가 읽은 상태는 version 3 기준이다"라는 조건. 저장소가 붙이기 직전에 확인한다. 낙관적 동시성 제어다.
- ④가 없으면 두 요청이 같은 version 3 상태를 보고 각자 검증을 통과한다. 이벤트는 둘 다 붙고 불변식(잔액 ≥ 0)이 깨진다.

#### 실험: 기대 버전 검사가 있을 때와 없을 때

- 일회용 PostgreSQL 17.11. 같은 스트림에 두 요청이 "version 3, 잔액 1000"을 보고 각자 700 출금 이벤트를 version 4로 넣는다. A는 넣고 3초 뒤 커밋, B는 1초 뒤 시작.

```sql
-- 검사 없음: 이벤트 ID만 PK
CREATE TABLE events_nover (id bigserial PRIMARY KEY, stream_id text, version int, type text, amount int);
-- 검사 있음: (스트림, 버전)이 유일 → 같은 버전으로 두 번 못 붙인다
CREATE TABLE events (stream_id text, version int, type text, amount int, PRIMARY KEY (stream_id, version));
```

```text
(실험, PostgreSQL 17.11 일회용 컨테이너, 2026-10-01)
### 테이블 events_nover — 두 요청이 같은 상태(version 3, 잔액 1000)를 읽고 각자 700 출금
 B: insert 성공 | 01:08:17
 A: 커밋  | 01:08:19
 fold 결과 잔액 = -400, 이벤트 5건

### 테이블 events
 A: insert 끝, 3초 뒤 커밋 | 01:08:19
 B: insert 시작 | 01:08:20
 A: 커밋  | 01:08:22
ERROR:  duplicate key value violates unique constraint "events_pkey"
DETAIL:  Key (stream_id, version)=(acc-1, 4) already exists.
 fold 결과 잔액 = 300, 이벤트 4건
```

- 검사 없음: 둘 다 붙어 잔액이 −400이 됐다. 이벤트 목록 자체는 문법적으로 멀쩡하다.
- 검사 있음: B가 거절됐다. B는 다시 읽으면 잔액 300을 보고 명령을 거절하게 된다.
- B는 A가 커밋할 때까지 기다린 뒤 오류를 받았다(별도 실행에서 B 시작 01:08:35 → A 커밋 01:08:37 → B 오류 뒤 01:08:38). PostgreSQL은 커밋 안 된 같은 키를 만나면 그 트랜잭션이 끝날 때까지 기다린다.

### 2. 읽기 경로 — 재생 비용과 스냅샷

```text
  처음부터:   empty ─e1─e2─e3─ ... ─e1,000,000─> 상태          (이벤트 수에 비례)
  스냅샷:     [v999,863 상태] ─e999,864─ ... ─e1,000,000─> 상태  (뒤 137건만)
              └ 스냅샷은 캐시다. 버려도 이벤트에서 다시 만든다
```

- *스냅샷*: 어느 버전까지 접은 상태를 따로 저장해 둔 것. 정본은 여전히 이벤트다(원본 systems/event-sourcing 「재생 비용과 스냅샷」).
- Fowler 2005도 같은 구조를 적는다: 밤사이 만든 스냅샷에서 시작해 메모리에 상태를 두고, 죽으면 그 뒤 이벤트를 재생한다.

#### 실험: 100만 이벤트 재생 vs 스냅샷 + 137건

- 이벤트는 JSON 문자열(`{"amountMinor":N,"currency":"KRW"}`), Jackson 2.19로 역직렬화해 접는다. 메모리 안 측정이라 DB 읽기 시간은 빠져 있다. 컨테이너 CPU 1개로 제한했다.

```java
for (String json : store) s = s.apply(M.readValue(json, Deposited.class));          // 처음부터
for (int i = snapV; i < n; i++) s2 = s2.apply(M.readValue(store.get(i), Deposited.class)); // 스냅샷 뒤만
```

```text
(실험, eclipse-temurin 21 JDK, Jackson 2.19.0, --cpus=1, 2026-10-01 — 시간은 실행마다 다르다)
[replay r1] 이벤트 1,000,000건 처음부터: 1196.5 ms (잔액 50,500,000, v1000000) | 스냅샷 v999,863 + 137건: 0.086 ms (잔액 50,500,000, v1000000)
[replay r2] 이벤트 1,000,000건 처음부터: 399.6 ms (잔액 50,500,000, v1000000) | 스냅샷 v999,863 + 137건: 0.102 ms (잔액 50,500,000, v1000000)
[replay r3] 이벤트 1,000,000건 처음부터: 333.5 ms (잔액 50,500,000, v1000000) | 스냅샷 v999,863 + 137건: 0.050 ms (잔액 50,500,000, v1000000)
```

- 관찰
  - 두 방법의 결과(잔액·버전)가 같다. 스냅샷은 결과를 바꾸지 않는다.
  - 처음부터 재생은 수백 ms~1초 남짓(첫 회는 JIT 워밍업으로 더 느림), 스냅샷 뒤 137건은 0.1ms 안팎이다.
- 해석: 재생 시간은 이벤트 수에 비례한다. 요청마다 처음부터 접으면 스트림이 길어질수록 응답이 느려진다. 실제로는 DB에서 100만 행을 읽는 시간이 더해진다.

### 3. 이벤트 버전 — 옛 이벤트는 지우지 않는다

```text
  2025년에 저장: {"amount":100}                         ← v1 형식
  2026년 코드:  record Deposited(long amountMinor, String currency)   ← v2 형식
  재생 = 오늘 코드로 모든 옛 이벤트를 읽는 것
                    │
     업캐스터 없음 ──┴──> 역직렬화 실패 → 그 스트림은 재생 불가
     업캐스터 있음 ─────> v1 → v2 변환(읽을 때만) → 접기
```

- *업캐스터(upcaster)*: 옛 형식 이벤트를 읽는 순간 현재 형식으로 바꾸는 함수. 저장된 이벤트는 그대로 둔다.
- 다른 선택지
  - 관대한 읽기: 모르는 필드를 무시하고, 없는 필드에 기본값을 준다. 필드 추가는 이것으로 버틴다. 이름 변경·의미 변경은 못 버틴다.
  - 새 이벤트 타입: 의미가 바뀌면 `DepositedV2`처럼 새 타입을 만들고 둘 다 접는다.
  - 복사·변환: 새 스트림(또는 새 저장소)에 변환한 이벤트를 다시 쓰고 전환한다. 원본은 보관한다.

#### 실험: 필드 이름을 바꾼 뒤 옛 이벤트 재생

```java
public record Deposited(long amountMinor, String currency) {}     // amount → amountMinor 로 바꿈
static JsonNode upcast(JsonNode n) {                              // v1 → v2, 읽을 때만
    if (n.has("amount")) {
        ObjectNode o = M.createObjectNode();
        o.put("amountMinor", n.get("amount").asLong());
        o.put("currency", "KRW");
        return o;
    }
    return n;
}
```

```text
(실험, Jackson 2.19.0 기본 ObjectMapper, 2026-10-01)
[schema] 업캐스터 없이 재생: UnrecognizedPropertyException: Unrecognized field "amount" (class Es22$Deposited), not marked as ignorable (2 known properties: "currency", "amountMinor"])
[schema] 업캐스터를 거쳐 재생: Account[balance=300, version=2]
```

- Jackson 기본 설정(`FAIL_ON_UNKNOWN_PROPERTIES` 켜짐)에서는 옛 필드 `amount` 하나 때문에 재생 전체가 실패했다.
- 반대로 이 설정을 끄기만 하면 예외 없이 읽히지만 값이 비어 **잔액이 조용히 틀린다**.

```text
(실험, Jackson 2.19.0, FAIL_ON_UNKNOWN_PROPERTIES=false)
[lenient] FAIL_ON_UNKNOWN_PROPERTIES=false 로 v1 읽기 → Deposited[amountMinor=0, currency=null]
```

- 실패가 드러나는 쪽이 낫다. 이름 변경은 업캐스터로 명시적으로 옮긴다.

### 4. 재생과 외부 세계

```text
  이벤트 ──> 프로젝션(읽기 모델): 잔액 테이블, 검색 인덱스     ← 지우고 다시 만들어도 된다
        └──> 외부 부작용: 메일 발송, 결제 API, 다른 서비스 통지  ← 재생 때 다시 하면 사고
```

- *프로젝션*: 이벤트를 구독해 조회용 상태(읽기 모델)를 만드는 부품. 이벤트를 다시 흘려 언제든 재구축한다.
- Fowler 2005 "External Updates": 재생이 외부 시스템에 갱신을 보내면 외부는 진짜 처리와 재생을 구별하지 못한다. 외부 호출을 게이트웨이로 감싸 재생 중에는 끈다.
- 같은 글 "External Queries": 12월 5일 이벤트를 12월 20일에 재생하면 그날 환율이 아니라 12월 5일 환율이 필요하다. Fowler의 처방은 외부 시스템에 그 날짜의 값을 묻거나, 게이트웨이가 질의 응답을 기억해 두었다가 재생 때 돌려주는 것이다. 결정에 쓴 외부 값을 이벤트 안에 담아 두는 것도 같은 효과를 낸다(원본 ops-patterns/16 장애 2).
- 프로젝션은 이벤트보다 늦다. 명령 직후 읽기 모델을 조회하면 방금 쓴 것이 안 보일 수 있다(최종 일관성, 07번).

### 5. 로그 기반 브로커를 이벤트 저장소로 쓸 때

- DDIA 11장은 이벤트 소싱과 변경 로그(CDC)를 나란히 놓는다. 둘 다 변경을 로그로 흘려 파생 상태를 만든다. 차이도 있다. 이벤트 소싱은 불변 이벤트 로그를 정본으로 설계할 수 있다. CDC는 원천 DB를 평소처럼 고쳐 쓰고, 그 DB의 변경을 뽑아 다른 시스템을 갱신한다(원천은 DB다).
- Kafka 토픽을 이벤트 저장소로 쓰려면 빈 곳을 알아야 한다.
  - 스트림(애그리게이트)별 기대 버전으로 붙이는 조건부 쓰기가 없다. §1의 불변식 보호를 다른 곳(단일 작성자, DB)에서 해야 한다.
  - 기본 보존은 시간 기준(`retention.ms` 7일)으로 오래된 세그먼트를 지운다. 크기 한도 `retention.bytes`는 기본 −1(무제한)이라 따로 줄 때만 적용된다(21번). 영구 보관하려면 `retention.ms=-1` 같은 설정이 필요하다. compaction은 키별로 **적어도** 마지막 값을 남기고, 같은 키의 옛 값은 지울 수 있다. 그래서 이력 보존 수단으로 가정하면 안 된다(Kafka 4.1 Design "Log Compaction").
  - 한 애그리게이트의 이벤트만 읽으려면 파티션 전체를 훑어야 한다.
- 흔한 구성: 이벤트 저장은 DB(스트림·버전 유일 제약)에, 전파는 아웃박스·CDC로 Kafka에(16번).

## 쓰이는 자료구조·알고리즘

- **append-only 로그** — 스트림별로 붙이기만 한다. 17·21번의 로그와 같은 구조이고, 여기서는 그 로그가 정본이다.
- **fold(왼쪽 접기)** — `state = events.reduce(empty, apply)`. `apply`는 결정적이어야 한다(시각·난수·외부 호출 금지).
- **(stream_id, version) 유일 인덱스** — B+Tree 유일 인덱스가 "같은 버전에 두 번 붙이기"를 막는 compare-and-set 역할을 한다. 실험의 `events_pkey`.
- **스냅샷 = 체크포인트·메모이제이션** — 접은 중간 결과를 저장해 재계산을 건너뛴다. WAL 복구의 체크포인트와 같은 발상이다([database/19-wal-and-logging](../../database/19-wal-and-logging/2-summary.md)).
- **업캐스터 체인** — v1→v2→v3 변환 함수를 이어 붙인 함수 합성. 이벤트 버전마다 한 단계만 구현한다.
- **영속 자료구조와 같은 발상** — 고치지 않고 새 버전을 쌓아 과거를 그대로 읽는다. [data-structure/26-persistent](../../data-structure/26-persistent/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 도입 판단 (원본 systems/event-sourcing 「판별 기준」 요약)

- "왜 이 값인가", "그때 상태는?"이 업무 요구이면 맞다(원장·주문·계약).
- 모델이 아직 흔들리면 이르다. 이벤트 형식이 굳으면 이후 변경마다 업캐스터가 쌓인다.
- 전부가 아니라 한 컨텍스트만 이벤트로 두는 부분 도입이 흔하다. 이때 상태와 이벤트의 대사가 따라온다.

### 2. 저장소 스키마 (PostgreSQL)

```sql
CREATE TABLE events (
    stream_id   text        NOT NULL,
    version     int         NOT NULL,
    type        text        NOT NULL,
    schema_ver  int         NOT NULL,          -- 업캐스터가 볼 형식 버전
    payload     jsonb       NOT NULL,
    occurred_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (stream_id, version)           -- 중복 버전 차단 = 읽은 version+1로만 붙이면 기대 버전 검사
);
CREATE TABLE snapshots (
    stream_id text PRIMARY KEY, version int NOT NULL, schema_ver int NOT NULL, state jsonb NOT NULL
);
```

### 3. 붙이기와 재시도 (Java, Spring JDBC)

```java
public void withdraw(String accountId, long amount) {
    for (int attempt = 1; ; attempt++) {
        Loaded acc = repo.load(accountId);                    // 스냅샷 + 그 뒤 이벤트 → 상태, version
        if (acc.state().balance() < amount) throw new RejectedException("잔액 부족");
        try {
            repo.append(accountId, acc.version() + 1, new Withdrawn(amount));   // INSERT (stream_id, version)
            return;
        } catch (DuplicateKeyException conflict) {            // 남이 먼저 붙였다
            if (attempt == 3) throw new ConcurrencyConflict(accountId);
        }                                                     // 다시 읽고 다시 판단
    }
}
```

- 실험의 B가 이 `catch`에 해당한다. 다시 읽으면 잔액 300을 보고 `RejectedException`이 난다.
- 유일 제약은 같은 (stream_id, version)의 중복만 막는다. 버전을 건너뛴 삽입(현재 3인데 5)은 막지 않는다. 그래서 모든 작성자가 이 경로(읽은 version + 1)로만 붙여야 기대 버전 검사가 된다.
- 스냅샷은 N개 이벤트마다(예시: 500) 비동기로 만든다. 스냅샷 형식이 바뀌면 지우고 다시 만든다(정본이 아니므로).

### 4. 진단 쿼리

```sql
-- 긴 스트림 상위 (스냅샷 필요 후보)
SELECT stream_id, max(version) AS len FROM events GROUP BY stream_id ORDER BY len DESC LIMIT 10;
-- 스냅샷이 얼마나 뒤처졌나
SELECT e.stream_id, max(e.version) - coalesce(s.version, 0) AS tail
FROM events e LEFT JOIN snapshots s USING (stream_id)
GROUP BY e.stream_id, s.version ORDER BY tail DESC LIMIT 10;
-- 아직 남아 있는 옛 형식 이벤트 수 (업캐스터를 지워도 되나)
SELECT type, schema_ver, count(*) FROM events GROUP BY type, schema_ver ORDER BY 1, 2;
```

## 장애 시나리오와 대처

### 1. 이벤트 스키마 변경 → 재생 실패 (⚠)

- **현상**: 배포 직후 일부(오래된) 계좌 조회와 프로젝션 재구축이 실패한다.
- **보이는 형태**: `UnrecognizedPropertyException: Unrecognized field "amount" ...`(실험) 또는, 모르는 필드를 무시하는 설정이면 예외 없이 `amountMinor=0, currency=null`로 읽혀 잔액이 틀린다(실험).
- **원인**: 이벤트는 지우지 않아 계속 남는데 코드의 이벤트 클래스를 바꿨다. 오늘 코드가 모든 옛 형식을 읽어야 한다는 약속이 없었다.
- **대처**: 이벤트에 `schema_ver`를 넣고 읽기 경로에 업캐스터를 둔다. 필드는 추가만(기본값 필수), 이름·의미 변경은 업캐스터나 새 타입으로. 배포 전에 운영 이벤트 표본을 새 코드로 재생하는 테스트를 돌린다.

### 2. 스냅샷 없음 → 재생 시간 폭증 (⚠)

- **현상**: 오래된 계좌일수록 조회·명령 처리가 느리고, 몇 년 된 계좌는 타임아웃이 난다.
- **보이는 형태**: 지연이 스트림 길이에 비례한다. 위 진단 쿼리에서 긴 스트림이 보인다. 실험에서 100만 건 재생은 수백 ms~1초(메모리 안), 스냅샷 뒤 137건은 0.1ms 안팎이었다.
- **원인**: 요청마다 처음부터 접는다.
- **대처**: N개마다 스냅샷을 만들고 "스냅샷 + 그 뒤"만 읽는다. 스냅샷 경계(`version > snapshot.version`)를 한 칸 틀리면 이벤트가 하나 빠지거나 두 번 접힌다. 처음부터 접은 결과와 비교하는 검증을 둔다. 스트림이 끝없이 길어지는 모델이면 기간별로 스트림을 끊는다(예: 회계 연도 마감 이벤트).

### 3. 기대 버전 검사 없이 붙여 불변식이 깨진다

- **현상**: 잔액이 음수인 계좌가 생긴다. 이벤트 목록에는 이상한 이벤트가 없다.
- **보이는 형태**: 같은 시각 근처에 같은 이전 상태를 보고 만든 이벤트 둘. 실험에서 잔액 −400.
- **원인**: 두 명령이 같은 상태를 읽고 각자 검증을 통과했다. 저장소가 "내가 본 버전"을 확인하지 않았다.
- **대처**: (stream_id, version) 유일 제약 또는 저장소의 expected version API. 충돌 시 다시 읽고 다시 판단한다. 한 스트림에 쓰기가 몰리면 충돌이 폭증하므로 스트림을 나누거나 그 스트림을 단일 작성자로 직렬화한다(원본 ops-patterns/16 장애 3).

### 4. 프로젝션 재구축이 메일을 다시 보낸다

- **현상**: 읽기 모델 버그를 고치려고 이벤트를 처음부터 다시 흘렸더니 고객들이 1년 치 알림 메일을 받았다.
- **보이는 형태**: 재구축 시각에 외부 발송 API 호출이 폭증한다.
- **원인**: 부작용이 있는 구독자와 순수 프로젝션을 구별하지 않았다. 외부 시스템은 재생과 실제 처리를 구별하지 못한다(Fowler "External Updates").
- **대처**: 프로젝션과 부작용 핸들러를 분리한다. 부작용은 게이트웨이로 감싸 재생 모드에서 끄고, 멱등 키로 이중 발송을 막는다. 재구축은 새 테이블에 만들고 다 되면 바꾼다.

### 5. "주문했는데 목록에 없다" — 프로젝션 지연

- **현상**: 명령은 성공했는데 바로 조회하면 반영이 안 돼 있다.
- **보이는 형태**: 프로젝션 구독자의 lag(마지막 처리 version·오프셋과 최신의 차이)이 커져 있다.
- **원인**: 읽기 모델은 이벤트를 비동기로 따라간다(최종 일관성).
- **대처**: 명령 응답에 새 version을 주고, 조회 쪽이 그 version 이상이 될 때까지 기다리거나 그 애그리게이트만 이벤트에서 직접 접어 응답한다. 프로젝션 lag에 경보를 건다.

## 핵심 문장

- 이벤트 소싱은 상태를 바꾼 사건을 차례로 붙여 둔다. 이 노트의 구성처럼 이벤트 로그를 정본으로 삼으면 현재 상태는 접어서 얻는다.
- 같은 상태를 본 두 명령이 둘 다 붙으면 불변식이 깨진다. (스트림, 버전) 유일 제약이 기대 버전 검사 역할을 했고, 실험에서 잔액 −400과 300을 갈랐다.
- 재생 시간은 이벤트 수에 비례한다. 스냅샷은 그 비용을 줄이는 캐시이고, 버려도 이벤트에서 다시 만든다.
- 옛 이벤트는 지우지 않고 계속 남으므로 오늘 코드가 모든 옛 형식을 읽어야 한다. 이름을 바꾼 필드 하나로 재생 전체가 실패했다.
- 재생은 순수해야 한다. 외부 부작용은 게이트웨이로 감싸고, 결정에 쓴 외부 값은 이벤트에 담는다.

## 관련 주제·근거

- 선행
  - [17-queues-logs-and-delivery-semantics](../17-queues-logs-and-delivery-semantics/2-summary.md) — 로그와 오프셋, 멱등 소비
  - 원본 [systems/event-sourcing](../../systems/event-sourcing/2-summary.md) · [ops-patterns/16-event-sourcing](../../ops-patterns/16-event-sourcing/2-summary.md)
- 연결
  - [16-outbox-and-dual-write](../16-outbox-and-dual-write/2-summary.md) — 이벤트를 다른 서비스로 전파하기
  - [07-consistency-models](../07-consistency-models/2-summary.md) — 프로젝션의 최종 일관성
  - [21-kafka-internals](../21-kafka-internals/2-summary.md) — 보존·compaction이 이력을 지운다
  - [20-data-ownership-and-cross-service-queries](../20-data-ownership-and-cross-service-queries/2-summary.md) — 프로젝션·Materialized View
  - [database/19-wal-and-logging](../../database/19-wal-and-logging/2-summary.md) — 로그 + 체크포인트
  - [data-structure/26-persistent](../../data-structure/26-persistent/2-summary.md)
- 근거
  - Martin Fowler, "Event Sourcing", 2005-12-12 — 정의, Complete Rebuild·Temporal Query·Event Replay, 스냅샷, External Updates·External Queries <https://martinfowler.com/eaaDev/EventSourcing.html>
  - DDIA 1판 11장 Stream Processing — 이벤트 소싱, 변경 데이터 캡처, 상태·스트림·불변성
  - PostgreSQL 17 문서 — 유일 인덱스 삽입 시 커밋 안 된 충돌 행을 기다리는 동작(62.5 Index Uniqueness Checks) <https://www.postgresql.org/docs/17/index-unique-checks.html>
  - Jackson 2.19 `DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES`(기본 켜짐) — 실험 출력으로 확인
- 실험 목록
  - 일회용 `sn-dw-w17-pg`(PostgreSQL 17.11): 기대 버전 검사 없음(잔액 −400·이벤트 5건) vs (stream_id, version) PK(23505, 잔액 300·이벤트 4건), B가 A 커밋까지 대기 후 오류
  - `Es22.java`(eclipse-temurin 21 JDK, Jackson 2.19.0, `--cpus=1`): 100만 이벤트 재생 333~1196ms vs 스냅샷 + 137건 0.05~0.10ms, 결과 동일 / 필드 이름 변경 → `UnrecognizedPropertyException`, 업캐스터 → 잔액 300
  - `Lenient22.java`: `FAIL_ON_UNKNOWN_PROPERTIES=false`로 v1 이벤트 → `amountMinor=0, currency=null`(예외 없음)
