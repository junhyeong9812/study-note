# 08-01 WAL & Recovery — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 서술하고, Claude가 빠진 곳을 짚는다. 객체·메서드 설명은 내가 자연어로 쓰고 Claude가 코드 기준으로 검증한다.

## 전체 워크플로우

<!-- 1회차 서술(2026-08-18) + 채점 반영. 채점에서 고친 곳은 [교정] 표시. -->

1. **시동** — LogManager가 열리면 파일을 처음부터 스캔한다. 레코드마다 길이 접두(int)를 읽고, 헤더 9바이트(tag + txId)를 읽은 뒤 나머지 본문은 skip한다. [교정: 파일 전체를 읽는 게 아니라 길이 접두 + 헤더만 읽고 건너뛴다]
2. 스캔하면서 본 **최대** txId를 `maxTxIdSeen`에 유지하고(로그는 tx가 섞여 있어 마지막 레코드가 최대라는 보장이 없다 [교정: "맨 마지막"이 아니라 max]), 레코드 개수로 `nextLsn = count + 1`을 복원하고, 포인터를 파일 끝에 둔다.
3. TransactionManager가 만들어질 때 `logManager.maxTxId() + 1`을 nextTxId 시작값으로 받는다. 재시작 후에도 txId가 이어진다(CI-4).
4. `begin()`이 그 카운터로 Transaction을 발급한다. Transaction은 생성 즉시 BeginTx를 로그에 쓴다.
5. **insert** — 로그에 InsertRow를 append하고 pending에 (heap, tuple)을 보관만 한다. 힙은 건드리지 않는다(deferred-apply). **commit** — CommitTx를 append하고 `sync()`(fsync)로 디스크에 박는다. 이 순간이 커밋 확정이다. 그다음에야 pending을 힙에 반영한다. **abort** — AbortTx를 append하고 pending을 버린다. 힙에 쓴 게 없으니 undo가 없다. State(ACTIVE/COMMITTED/ABORTED)는 트랜잭션의 운명을 결정하는 게 아니라 "커밋된 tx에 또 insert" 같은 실수를 막는 런타임 가드다.
6. **크래시 후 복구** — Recovery가 replay로 로그를 처음부터 다시 읽는다. **1패스**: txId별 인서트 목록(`perTxInserts`)과 `committed`/`aborted` 집합을 모은다. **2패스**: `committed에 있고 aborted에 없는` 트랜잭션만 골라, 테이블 이름으로 힙을 찾고 → 바이트를 힙 스키마로 decode해 Tuple로 복원하고 → heap.insert한다. 커밋 증거가 없는 tx(크래시로 결말이 안 찍힌 것 포함)는 자연히 걸러진다.
7. **한계** — 지금은 커밋된 걸 전부 다시 넣는다(redo-only, 비멱등). "이미 힙에 반영됐나"를 알 방법이 없어서다. 그래서 테스트는 힙 파일을 지우고 복구를 돌린다. 반영 여부를 알려면 순번(LSN)과 기록 시점(Checkpoint)이 필요하다 → 08-02.

## 의존성 구조

```
                ┌───────────────────────┐
                │   TransactionManager  │  txId 발급 (maxTxId()+1 부터)
                └───────────┬───────────┘
                            │ begin() → 생성
                            ▼
                ┌───────────────────────┐
                │      Transaction      │  insert / commit / abort
                │  pending: (heap,tuple)│  State = 런타임 가드
                └─────┬───────────┬─────┘
       append(Begin/  │           │ commit 시 pending → heap.insert
       Insert/Commit/ │           ▼
       Abort)         │     ┌───────────┐
                      │     │ TableHeap │  (02장 스토리지 — 실제 디스크 페이지)
                      ▼     └───────────┘
                ┌───────────────────────┐        ▲
                │      LogManager       │        │ heap.insert (복구 시 재반영)
                │  encode/decode        │        │
                │  append / sync        │        │
                │  replay               │        │
                │  init: nextLsn·maxTxId│        │
                └─────┬────────▲────────┘        │
     encode / decode  │        │ replay { rec -> … }
                      ▼        │                 │
                ┌───────────┐  │       ┌─────────┴─────────┐
                │ LogRecord │  └───────┤      Recovery     │
                │ (sealed)  │          │ 1패스: 수집        │
                │ Begin/    │          │ 2패스: committed만 │
                │ Insert/   │          │       heap에 반영  │
                │ Commit/   │          └───────────────────┘
                │ Abort/    │
                │ Checkpoint│
                └───────────┘

방향 규칙: 화살표는 "누가 누구를 쓰는가". LogManager는 위쪽(Transaction·Recovery)을 모른다.
쓰기 경로: Transaction → LogManager → 파일.   읽기 경로: Recovery → LogManager.replay → 파일.
LogRecord는 양쪽이 공유하는 "로그의 문법"이고, 아무도 의존하지 않는다(순수 데이터).
```

이때 init이 있는 LogManager는 파일에 관한 사실은 파일 형식을 아는 자만 읽을 수 있어서다. 제어는 여전히 트랜잭션이 관리하고 위층이 로그에게
그게 맞는 지 맞는구조이다.

## 객체별 설명 (직접 자연어로 작성 → Claude가 코드 기준으로 검증)

<!-- 규칙: 코드를 안 보고 기억으로 쓴다. 각 객체는 ①역할 한 줄 ②내부 상태(필드) ③메서드별 동작.
     검증 후 틀린 곳은 [교정] 표시로 남긴다 — 지우지 않는다. 다음 복습 때 그 자리가 약점이다. -->

### LogRecord

- 역할: 트랜잭션 상태를 로그 레코드로 기록하기 위한 객체
- 내부 구조: 로그 레코드의 동작을 기록하는 데이터 객체들을 정의해놓은 구조
- 메서드/특이점: 
  - 각 객체들 명 자체가 트랜잭션의 상태를 의미하며, 열을 저장하는 트랜잭션일 경우 저장하는 로우에 대한 트랜잭션 중복 여부를 검사하고 일치여부를 검사한다.
    [교정: InsertRow의 equals/hashCode는 중복·무결성 검사가 아니다 — ByteArray 필드가 있으면 data class의 자동 equals가 **참조 비교**를 해서 내용이 같아도 다르다고 판정하므로, `contentEquals`로 **내용 동등성** 비교가 되게 손으로 고쳐 쓴 것. 용도는 왕복 검증(원본 == decode(encode(원본)))]
  - 또한 내부에 각 태크 번호를 바이트로 정의해놓은 명세서 객체이다.
  - [보충: sealed class라 하위 타입이 5개로 닫혀 있어 when 누락을 컴파일러가 잡는다 · `abstract val txId`가 [tag][txId] 헤더 규칙을 모든 레코드에 강제 · Checkpoint는 소속 tx가 없어 `txId = 0L` override(placeholder)]

### LogManager

- 역할: 트랜잭션 관련 로그를 만들고 관리하는 객체
- 내부 상태: 로그 초기화 상태, 로그를 추가할 수 있는 nextLsn객체 상태 유지, maxTxIdSeen를 이용한 트랜잭션 스캔값을 미리 확인하기 위한 상태
          [교정: 첫 번째는 "초기화 상태"가 아니라 **파일 핸들**(`val file = RandomAccessFile(path, "rw")`) — 모든 읽기/쓰기가 지나가는 통로. nextLsn·maxTxIdSeen은 객체가 아니라 **Long 카운터**(`@Volatile var`). @Volatile이 카운터 둘에만 붙는 이유: 값이 변하고 다른 스레드가 그 최신값을 봐야 해서 — file은 val이라 참조가 안 변하니 불필요]
- `init`: 트랜잭션 로그 파일을 찾고, 반복을 통해 파일 포인터를 파일 길이만큼 반복하며, 트랜잭션id를 읽고 이게 maxTxIdSeen에 저장하며 반복하며 포인터를 옮기고, 본문은 건너뛰며 카운트를 증가시켜 마지막까지 진행
          다음 Lsn카운트까지 기록하고 포인터를 맨끝으로 옮긴다.
          [교정: "저장"이 아니라 **기존 값보다 클 때만 갱신**(`if (txId > maxTxIdSeen)`) — 유지하는 건 '마지막'이 아니라 '최대']
- `append`: 엔코드를 통해 레코드 자체를 직렬화하고 이를 기반으로 파일 자체에 append-only로 추가하고 Lsn을 증가시키고 해당값을 반환
          [교정 2건: ① 본문 앞에 **길이 접두**(`writeInt(payload.size)`)를 먼저 쓴다 — init/replay가 스캔할 수 있는 이유 ② 반환값은 증가 **전**의 LSN(이번 레코드에 부여된 번호)]
- `sync`: 파일에 직접 바로 기록하여 저장시킬 수 있도록 하는 메서드
          [교정: 기록 자체는 append가 이미 했다 — sync(fsync)는 OS 캐시 내용을 **물리 디스크까지 내려쓰도록 강제**하는 것. commit의 확정(durability) 지점]
- `currentLsn`: 현재 nextLsn 위치를 반환한다.
          [교정: `nextLsn - 1` — 다음에 쓸 번호가 아니라 **마지막으로 발급된** LSN]
- `replay` / `replayWithLsn`: 핸들러 메서드를 통해 유닛으로 처리하는데,파일을 읽고 바이트 배열들을 역직렬화하여 메모리 객체에 올려서 객체 로드를 진행한다.
          [교정: "메모리에 올려 로드"하지 않는다 — decode한 레코드를 **핸들러에게 넘기기만** 하고, 뭘 할지는 호출자(Recovery 등)의 몫. replay는 replayWithLsn의 래퍼(LSN을 `_`로 버림). 끝나면 포인터를 파일 끝으로 되돌려 append 위치 복원]
- `maxTxId`: 마지막 트랜잭션 id를 반환하여 트랜잭션 메니저의 트랜잭션 id 시작값을 동기화
          [교정: '마지막'이 아니라 스캔에서 본 **최대** txId — ⚠️ 같은 오답 3회째(8/18 워크플로우, 오늘 init·여기). 복습 카드 확정감]
- `encode` / `decode`: 해당 트랜잭션 레코드의 상태값에 따라서 
  - Begin이면 트랜잭션 비긴 플래그를 넣고 버퍼에 기록한다. 디코드일때는 해당 태그값이 비긴값과 같으면 해당 로그 객체를 생성
  - 커밋이면 해당 트랜잭션id에 대해 태그 커밋을 붙이고 기록 디코드는 해당 객체를 생성
  - Abort라면 어볼트 플래그 값을 넣고 버퍼에 저장 디코드일때 해당 객체를 해당 txid로 생성
  - 인서트라면, 테이블 이름을 바이트어레이로 만들고 버퍼에 해당 객체 내용을 기반으로 버퍼에 데이터를 기록한다. 디코드에서 이름 길이와 이름 바이트 객체 값을 기반으로 각 객체에 담아서 인서트 로우를 다시 만들어낸다.
  - 체크포인트인 경우 현재 활서오하된 트랜잭션 버퍼를 찾고 이를 바탕으로 체크포인트 위치와 함꼐 버퍼 내에 체크포인트를 기록한다. 체크포인트는 트랜잭션이 없으니 0으로, 디코드일떄도 바이트를 읽어서 이를 기반으로 엑티브까지 된 객체까지 체크포이트 생성.
    [교정: 활성 tx를 "찾지" 않는다 — 목록은 레코드가 이미 들고 온 필드(activeTxs)이고, encode는 그걸 안쪽 버퍼에 [개수][id...]로 채운 뒤 바깥 버퍼([tag][txId=0][checkpointLsn])에 이어붙일 뿐. 누가 활성인지 아는 건 상위(체크포인트를 찍는 쪽)의 일]
  - [보충: decode는 타입 무관하게 **[tag][txId] 헤더를 무조건 먼저** 읽고 tag로 분기 · InsertRow 디코드는 이름(길이+바이트) 다음 **튜플(길이+바이트)**도 읽는다 · 모르는 태그면 `error(...)`로 즉시 실패]
  
### Transaction

- 역할: 현재 트랜잭션 자체의 상태를 관리한다.
- 내부 상태: 활성,커밋,롤백 3가지 상태를 지닌다.
          [교정: State 외에 핵심 필드 하나 누락 — **`pending: MutableList<Pair<TableHeap, Tuple>>`**. deferred-apply의 실체로, insert가 쌓아두고 commit이 힙에 붓고 abort가 버리는 그 버퍼. 이게 없으면 이 클래스 동작의 절반이 설명 안 된다. (+ id, logManager도 생성자 필드)]
- `init`: 처음 생생되면 로그레코드에 시작 레코드를 등록한다.
- `insert`: 상태가 엑티브인지 확인하고 튜플과 힙 자체의 스키마값이 일치하는 지 비교해서 실제 테이블과 입력하는 스키마가 같은 지 확인 후 맞으면 인서트 로우를 생성하고 힙과 튜플 페어로 서로 매핑시켜놓는다.
- `commit`: 커밋 레코드로 확정하고 로그메니져를 OS에 저장시키고 힙 내에 해당 튜플을 인서트해서 힙에 추가하고 팬딩을 비우고 상태를 커밋으로 전환
          [교정: "OS에 저장"이 아니라 sync는 **OS 캐시를 물리 디스크까지 강제로 내려쓰는 것** — append 시점에 이미 OS에는 갔고, 디스크 도달이 확정 지점 (LogManager.sync 교정과 같은 오해 2회째). + 맨 앞에 `check(state == ACTIVE)` 가드도 있다]
- `abort`:팬딩을 비우고 실제 힙과 테이블에 저장되지 않게 팬딩 자체를 비워버린다. 즉 커밋 전에 저렇게 하면 커밋 시 힙에 저장되지 않는다.
          [교정 2건: ① **AbortTx를 로그에 append하는 단계 누락** — 이 기록이 있어야 Recovery가 aborted 집합을 만들 수 있다. 버리는 것도 로그에 남긴다. ② "커밋 전에 저렇게 하면"이 아니라 abort 후엔 **commit 자체가 불가**(state가 ABORTED라 check 가드에 걸림) — 순서의 문제가 아니라 상태 전이의 문제]
- `isCommitted` / `isAborted`: 현재 해당 상태가 맞는지 확인하는 메서드

### TransactionManager

- 역할: 트랜잭션 id를 관리하여 트랜잭션 객체 생성 열갛을한다.
- `begin`: 트랜잭션을 생성할때 로그매니저와 트랜잭션 id를 이용하여 트랜잭션 객체를 생성한다.

### Recovery

- 역할: 커밋된 객체들을 다시 파일 파이트에서 읽어들여서 커밋된 객체들들과 롤백 객체를 각각 상태에 저장해놓고, 인서트 객체들은 바이트와 테이블들을 기반으로 복구한다. 즉 실 로그를 기반으로 서버의 상태를 싱크하는 역할
- `Stats`: 현재 리커버리된 상태를 저장하기 위한 데이터 객체
- `recover` — 1패스: 처음에는 우선 리플래이를 통해 레코드 객체를 각 상태값을 기준으로 분리한다.
- `recover` — 2패스: 분리 후 커밋이 아니거나 어볼트인 경우 그대로 다음으로 넘어가고 커밋이면 인서트를 통해 힙과 튜플에 저장시킨다.
          [보충: 커밋 판정 뒤 두 단계가 더 있다 — ① `heapLookup(tableName) ?: continue`로 힙을 찾고(없는 테이블이면 그 인서트만 건너뜀) ② `Tuple.decode(heap.schema, bytes)`로 바이트를 Tuple로 복원한 뒤 heap.insert. "튜플에 저장"이 아니라 **튜플을 힙에** 저장]

## 관련 파일

- impl 문서: `/home/jun/project/db-engine-lab/impl/08-01-wal-recovery.md`
- 코드: `src/main/kotlin/com/dbenginelab/wal/` (LogRecord · LogManager · Transaction · TransactionManager · Recovery)
