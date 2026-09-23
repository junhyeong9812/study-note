# cs/issue/database/transaction-boundary-scope — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 사건 기록 원문 대조 작성. 복습 전 읽지 말 것.

태그: —

## 정답
<!-- 질문 1:1 대응 -->

1. **rollback 은 트랜잭션 전체를 되돌린다.** 노드 INSERT 와 엣지 INSERT 가 **한 트랜잭션**이었으므로, 엣지 1건의 CHECK 위반을 잡아 `rollback()` 하자 같은 트랜잭션의 **노드 224개 INSERT 까지 전부** 되돌아갔다.\
   이후 엣지들은 이제 존재하지 않는 노드를 참조하므로 FK 위반으로 연쇄 실패했고(`skip 224`), 마지막 `commit()` 은 **빈 트랜잭션**을 커밋했다.\
   "이 한 건만 버리고 계속"이라는 의도와 달리, 넓은 경계에서의 rollback 은 "지금까지 전부 버리기"다.\
   교정: 문장 단위로 격리(autocommit)해 한 건 실패가 그 건에만 머물게 하고(한 트랜잭션을 유지해야 한다면 건마다 SAVEPOINT 를 두고 그 지점까지만 되돌리는 방법도 있다), 미정의 값은 **쓰기 전에 정규화**(normalize-on-write)해 제약 위반 자체를 줄이며, 숫자 캐스팅도 방어했다 → 253노드·357엣지 적재.
   > **원자성(atomicity)** — 트랜잭션 안의 작업이 전부 반영되거나 전부 반영되지 않는 성질. 경계가 곧 그 "전부"의 범위다.

2. **commit 성공 ≠ 적재 성공.** `commit()` 은 "그 시점 트랜잭션에 남은 것을 확정했다"만 뜻한다 — 남은 것이 없으면 빈 커밋도 성공이다.\
   그래서 적재 작업의 완료는 종료 코드나 커밋 성공이 아니라 **대상 테이블을 다시 세어(count 재조회)** 기대 건수와 대조해 확인한다.\
   같은 계열로, 벌크 색인 API 가 HTTP 200 을 돌려줘도 항목별 오류가 있을 수 있어 항목 단위 오류 필드를 확인해야 한다는 교훈도 함께 기록됐다.

3. **쪼개면 부분 성공이 생긴다.** 결제를 메시지로 분리하면 주문 처리와 결제가 **서로 다른 트랜잭션**이 된다.\
   결제 트랜잭션은 커밋됐는데 후속(보관 처리) 트랜잭션이 실패하면 "결제는 완료됐지만 후속 처리는 안 된" 불일치가 남고, 이를 되돌릴 단일 rollback 이 없다.\
   다시 묶은 방법: 요청에는 202(접수)로 즉시 응답하고, **주문 처리 전체를 한 소비자의 한 트랜잭션**으로 처리한 뒤 결과를 실시간 채널로 통지했다.\
   이 사례는 설계 단계에서 시나리오로 발견한 것이며, 외부 결제 시스템과 DB 사이의 원자성은 다루지 않았다(경계 밖의 문제로 남음).

4. **기본 롤백은 unchecked 예외만.** 선언적 트랜잭션은 기본적으로 `RuntimeException`·`Error` 에서만 롤백하고, **checked 예외는 커밋**한다.\
   업로드 메서드가 checked 예외를 던지자 트랜잭션이 커밋돼 **고아 메타데이터**가 남았다 → `rollbackFor = Exception.class` 로 명시했다.\
   같은 리뷰에서 쓰기 메서드에 트랜잭션 선언이 아예 없던 곳도 함께 보강했다.

5. **커밋 전 캐시 무효화.** 커밋은 메서드가 **반환된 뒤** 프록시에서 일어난다. 메서드 안에서 캐시를 비우면 (a) 커밋 전 틈에 들어온 동시 요청이 캐시 미스로 **아직 옛 DB 상태를 읽어 캐시에 다시 채운다**(stale 재적재), (b) 이후 트랜잭션이 롤백되면 DB 는 그대로인데 캐시는 이미 바뀐 상태가 된다 — 삭제(evict)형 무효화라면 불필요한 미스·재적재 부하 정도지만, 캐시에 새 값을 써 넣는(put) 방식이면 **DB 에 없는 값이 캐시에 남는다**.\
   무효화는 **커밋이 확정된 뒤**(`afterCommit` 콜백 등)에 해야 한다 — 이 항목은 리뷰 권고로 기록됐다.
   > **afterCommit** — 트랜잭션 동기화 콜백. 커밋이 성공한 뒤에만 실행되어 부수효과를 커밋 결과에 맞춘다.

6. **보상의 시점이 커밋보다 앞선다.** 메서드 안의 try/catch 보상은 **메서드 실행 중** 예외만 본다. 커밋은 메서드 반환 후 일어나므로, 커밋 시점 실패(제약 검사·연결 끊김 등)에는 보상이 이미 지나가 **디스크에 고아 파일**이 남는다 → 파일 정리를 커밋 결과에 묶거나(afterCommit/afterCompletion) outbox 로.\
   일회용 토큰을 **별도 저장소**에서 먼저 소비하고 사용자 조회에서 실패하면, DB 트랜잭션은 롤백돼도 외부 저장소의 소비는 롤백되지 않아 **토큰이 영구 소실**된다 → 소비는 모든 검증이 끝난 뒤로.\
   (파일·토큰 항목은 리뷰 권고로 기록됐고 적용 여부는 기록에 없다.)

7. **outbox 와 영속 스트림.** outbox 는 "발행할 메시지"를 **DB 행(pending)으로 업무 데이터와 같은 트랜잭션에** 쓴다 — 둘 다 커밋되거나 둘 다 롤백된다. 별도 워커가 주기적(예: 2초)으로 pending 행을 읽어 브로커에 발행하고 `published` 로 표시한다.\
   이 사례의 Pub/Sub(Redis Pub/Sub)은 메시지를 **저장하지 않고** 그 순간 연결된 구독자에게만 전달하므로(fire-and-forget — 관리형 Pub/Sub 서비스 중엔 구독별로 메시지를 보존하는 것도 있어 "Pub/Sub = 무저장"은 제품마다 다르다), 구독자가 없거나 끊겨 있던 동안의 메시지는 사라진다.\
   그래서 로그형 영속 스트림에 추가하고(append), 소비자 그룹이 읽은 뒤 확인(ack)하는 방식으로 바꿔 "발행됐지만 아무도 못 받은" 메시지가 남아 있게 했다.
   > **transactional outbox** — DB 쓰기와 메시지 발행의 원자성을, 메시지를 같은 DB 트랜잭션의 행으로 먼저 저장하는 것으로 얻는 패턴.

## 문제 구조 (추상화 코드)

### 변형 A — 너무 넓은 경계에서의 부분 rollback
```python
# ① 문제
conn = connect(); cur = conn.cursor()
for n in nodes:
    cur.execute("INSERT INTO nodes(...) VALUES (...)", n)
for e in edges:
    try:
        cur.execute("INSERT INTO edges(...) VALUES (...)", e)
    except Exception:
        conn.rollback(); skipped += 1; continue      # ← 노드까지 롤백
conn.commit()                                          # 빈 트랜잭션 커밋

# ② 고친 코드
conn.autocommit = True                                 # 문장 단위 격리
for e in edges:
    e.type = normalize_type(e.type)                    # 쓰기 전 정규화
    try:
        cur.execute("INSERT INTO edges(...) VALUES (...)", e)
    except IntegrityError:
        skipped.append(e)                              # 그 건만 실패 — 기록하고 계속
    # ...
assert count("nodes") == expected_nodes                # 완료 = 재조회로 확인
```
무엇이 깨졌나: 한 건의 제약 위반이 전체 적재를 0건으로 만들고도 에러 없이 끝남.

### 변형 B — 한 비즈니스 단위를 메시지 경계로 쪼갬
```java
// ① 문제
@Transactional void placeOrder(...) { saveOrder(); publish(PAYMENT_REQUESTED); }
@Listener @Transactional void onPayment(...) { pay(); }            // 별도 트랜잭션
@Listener @Transactional void onPaid(...) { reserveStorage(); }     // 여기서 실패 → 결제만 완료

// ② 고친 코드
ResponseEntity<?> placeOrder(...) { publish(ORDER_REQUESTED); return accepted(); }  // 202
@Listener @Transactional
void handleOrder(OrderEvent ev, Ack ack) {       // 주문 처리 전체를 한 트랜잭션
    saveOrder(); pay(); reserveStorage();
    // ... 결과 통지
}
```
무엇이 깨졌나: 쪼갠 조각마다 별도 커밋 → 부분 성공 불일치(설계 단계 발견).

## 검증 기록
- 2026-09-24: 사건 기록 대조·추상화(Claude 초안)

## 방안 비교

같은 원리(트랜잭션 경계가 원자성 단위다)에서, 경계 **밖**의 부수효과를 커밋 결과와 맞추는 두 방안이 있었다.

### 방안 1 — 트랜잭션 밖 부수효과를 커밋 결과에 동기화
```java
// ① 문제
@Transactional
public Result save(Command c) {
    Entity e = repository.save(...);
    cache.clear();                                    // 커밋 전 실행
    return ...;
}
@Transactional public void upload(...) throws IOException { ... }   // checked 예외 → 커밋됨

// ② 고친 코드
@Transactional(rollbackFor = Exception.class)
public Result save(Command c) {
    Entity e = repository.save(...);
    TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
        public void afterCommit() { cache.clear(); }  // 커밋 확정 후
    });
    return ...;
}
```
무엇이 깨졌나: 커밋 전 무효화 → stale 재적재·롤백 시 불일치; checked 예외 커밋 → 고아 메타데이터.\
같은 구조: 파일 쓰기 + DB insert 에서 메서드 내 보상만 → 커밋 시점 실패 시 고아 파일(권고: afterCommit/outbox).\
같은 구조: 외부 저장소 토큰을 먼저 consume → 이후 실패 시 토큰 영구 소실(권고: 검증 후 consume).

### 방안 2 — DB 쓰기와 발행을 outbox 로 한 트랜잭션에
```java
// ① 문제
@Transactional void handle(...) { repository.save(...); broker.publish(msg); }  // 둘 중 하나만 성공 가능
// 브로커가 저장 없는 Pub/Sub 이면 구독자 부재 중 메시지 소실

// ② 고친 코드
@Transactional void handle(...) {
    repository.save(...);
    outbox.insert(new OutboxRow(msg, PENDING));        // 같은 트랜잭션
}
@Scheduled(fixedDelay = 2000) void relay() {
    for (OutboxRow r : outbox.findPending()) {
        stream.append(r.payload());                   // 영속 스트림에 추가
        outbox.markPublished(r);
    }
}
// 소비: consumer group 으로 읽고 처리 후 ack
```
무엇이 깨졌나: 저장·발행이 따로 커밋되어 한쪽만 성공, 저장 없는 전달로 메시지 소실. (도입 중 NOT NULL 위반 등 구현 이슈 2건이 별도 기록됨)

| | 방안 1: afterCommit 동기화 | 방안 2: outbox |
|---|---|---|
| 전제 | 부수효과가 같은 프로세스 안에서 즉시 실행 가능(캐시·로컬 파일) | 부수효과가 외부 시스템 발행이며 유실되면 안 됨 |
| 비용 | 콜백 등록 코드, 추가 인프라 없음 | outbox 테이블·릴레이 워커·폴링 지연(초 단위) |
| 실패 모드 | 커밋 후 콜백 실행 중 프로세스가 죽으면 부수효과 누락(재시도 없음) | 릴레이가 발행 후 표시 전에 죽으면 중복 발행 → 소비자 멱등 필요 |
| 맞는 조건 | 누락돼도 다음 조회·TTL 로 회복되는 캐시 무효화 등 | 반드시 한 번 이상 전달돼야 하는 이벤트·알림 |

결론: 부수효과가 "놓쳐도 회복 가능한 로컬 상태"면 방안 1 이 가볍고 충분하다.\
부수효과가 "놓치면 안 되는 외부 전달"이면 커밋과 발행 사이의 틈을 방안 1 로는 닫을 수 없으므로 방안 2 가 맞다 — 대신 중복 전달을 소비자 멱등으로 흡수해야 한다.\
실패 모드 두 칸은 각 패턴의 일반 성질이며, 이 사례 기록에서 실측된 것은 아니다.
