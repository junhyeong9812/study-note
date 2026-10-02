# reliability/30-scheduler-and-cron-ha — 스케줄러 이중화·중복 실행 방지·미실행 보정 — 정리 (힌트)

## 해결하는 문제

"매일 새벽 2시 정산"을 서버 한 대에서 돌리면 그 서버가 죽은 날 정산이 안 돈다.\
그래서 두 대에 띄우면, 이번에는 두 대가 **둘 다** 정산을 돌린다.\
스케줄러 이중화는 "한 대가 죽어도 돌고(가용성), 두 대가 살아도 한 번만 돌게(중복 방지)" 하는 문제다. 여기에 "죽어 있던 동안 놓친 회차를 어떻게 할까(보정)"가 붙는다.

```text
 1대:   [A] 02:00 정산 ✔        A 다운 → 02:00 정산 ✘ (놓침)
 2대:   [A] 02:00 정산 ✔
        [B] 02:00 정산 ✔        → 이중 정산 (⚠ 돈이 두 번 나간다)
 목표:  [A] 02:00 정산 ✔  [B] 건너뜀          A 다운 → [B] 02:00 정산 ✔
```

쉬운 예: 아파트 경비실 야간 순찰이다.
- 경비원 둘이 근무하는데 순찰 일지가 없으면 둘 다 순찰하거나, 서로 상대가 했겠지 하고 아무도 안 한다.
- 순찰 일지(공유 기록)에 "02시 순찰 — 김 씨"를 먼저 적은 사람만 돈다. 둘 다 졸았다면 아침에 일지의 빈칸을 보고 놓친 순찰을 처리한다.

똑같은 구조다.\
실무 예: Spring `@Scheduled` 정산·집계 잡을 여러 파드에 배포, Kubernetes `CronJob`, 리눅스 cron을 두 서버에 같은 crontab으로, 배치 서버 이중화.

- 기초(방아쇠 네 종류 — 고정 주기·고정 지연·건너뛰기·크론, 밀렸을 때의 동작, `*/7` 시 경계 문제, DST)는 원본 [ops-patterns/10-scheduler](../../ops-patterns/10-scheduler/2-summary.md)에 있다.
- 이 노트는 원본이 "한 대만 돌게 묶는다"로 넘긴 부분 — **여러 인스턴스에서 한 번만 실행**, **놓친 실행의 보정**을 실험으로 다룬다.

## 동작·원리

### 1. 세 가지 접근

```text
 ① 리더 하나만 스케줄러를 돈다    A(리더) ── 02:00 정산        B(대기) — 스케줄러 꺼짐
    선출: etcd·ZooKeeper·K8s Lease     리더가 죽으면 B가 리더가 되어 이어받음

 ② 모두 방아쇠를 당기고, 실행 직전에 락    A ─ lock("settle") ✔ 실행
    (ShedLock 방식)                         B ─ lock("settle") ✘ 건너뜀

 ③ 모두 방아쇠를 당기고, 회차(슬롯)를 기록으로 선점
    INSERT job_run(job='settle', slot='2026-10-01T02:00') ← 유일 키
    A ─ 삽입 1행 ✔ 실행      B ─ 삽입 0행 ✘ 건너뜀
```

- *회차(슬롯)*: 스케줄이 만든 예정 시각 하나. "02:00 회차"처럼 실행 단위의 이름이 된다.
- ①은 리더 선출의 문제로 옮겨 간다([distributed/10-leader-election](../../distributed/10-leader-election/2-summary.md)). 리더가 둘이 되는 순간(분할·멈춤)에는 ②·③과 같은 보호가 다시 필요하다.
- ②는 **같은 시각에 둘이 동시에 도는 것**을 막는다. **같은 회차를 두 번 도는 것**은 막지 못할 수 있다(아래 2절).
- ③은 회차 자체를 유일 키로 만들어 "이 회차는 한 번"을 기록이 보장한다. 실행 이력이 남아 보정(4절)의 재료가 된다.

### 2. 시간 기반 락의 두 함정

```text
 함정 1 — 작업이 짧고 방아쇠가 어긋날 때 (lockAtLeastFor 없음)
 A: 02:00:00.000 lock ✔ ─ 작업 50ms ─ unlock(02:00:00.050)
 B: 02:00:00.150 lock ✔ (이미 풀렸다) ─ 같은 회차를 또 실행      → 회차당 2번

 함정 2 — 작업이 lease(lockAtMostFor)보다 오래 걸릴 때
 A: lock(만료 400ms) ─ 작업 ──── GC 멈춤 ──── 700ms ───────────┐
 B:                      400ms에 lock 만료 → 다음 방아쇠에 lock ✔ ─ 실행 ┘ 겹침
```

- ShedLock README(7.x)가 두 함정을 모두 적는다.
  - `lockAtLeastFor`: 노드 간 시계 차이와 아주 짧은 작업 때문에 여러 노드가 실행하는 것을 막는 최소 보유 시간.
  - `lockAtMostFor`: 노드가 죽었을 때를 위한 안전망. 정상 실행 시간보다 **훨씬** 길게 잡아야 하고, 작업이 이보다 길면 둘 이상이 락을 쥔 것처럼 동작한다.
  - ShedLock은 "같은 시각에 최대 한 번(at most once at the same time)"을 보장하고, 락을 못 잡은 쪽은 기다리지 않고 **건너뛴다**. 시계가 동기화돼 있다고 가정한다. 분산 스케줄러가 아니라 락일 뿐이라고 스스로 밝힌다.
- 아래 실험이 두 함정을 그대로 재현한다(LOCK_RELEASE_AT_END: 12회, LOCK_LEASE_EXPIRES_DURING_PAUSE: 동시 실행 2).
- 함정 2는 락 일반의 문제다. 멈췄다 깨어난 옛 주인을 막으려면 쓰기 쪽이 fencing token을 검사해야 한다([distributed/12-coordination-and-fencing](../../distributed/12-coordination-and-fencing/2-summary.md)).

### 3. Kubernetes CronJob — 플랫폼이 주는 것과 안 주는 것

| 필드 | 동작(Kubernetes 문서 "CronJob", 2026-10-01 열람) |
|---|---|
| `concurrencyPolicy: Allow`(기본) | 이전 Job이 아직 돌아도 새 Job을 만든다 |
| `Forbid` | 이전 Job이 돌고 있으면 새 회차를 건너뛴다(놓친 것으로 센다) |
| `Replace` | 이전 Job을 새 Job으로 바꾼다 |
| `startingDeadlineSeconds` | 예정 시각을 이만큼 넘기면 그 회차를 건너뛴다. 미설정이면 기한 없음. 10초 미만이면 컨트롤러가 10초마다 확인하므로 스케줄되지 않을 수 있다 |
| 놓친 회차 100개 초과 | 문서: 마지막 예정 시각부터 지금까지 놓친 회차가 100개를 넘으면 Job을 시작하지 않고 오류를 남긴다. `startingDeadlineSeconds`가 있으면 그 기간 안의 놓친 수만 센다. 단 v1.34.0 컨트롤러 소스(`pkg/controller/cronjob/utils.go` `nextScheduleTime`)는 `TooManyMissedTimes` 경고만 남기고 가장 최근 회차를 그대로 돌려준다 — 그 회차는 마감·`concurrencyPolicy` 검사를 거쳐 시작될 수 있다([31](../31-batch-job-restart-and-checkpoint/2-summary.md)) |
| `timeZone` | 스케줄을 해석할 시간대(예: `Etc/UTC`). `schedule` 안의 `CRON_TZ`·`TZ`는 지원하지 않는다 |

- 문서 원문: CronJob은 예정 시각마다 Job을 "**대략** 한 번" 만든다. 두 Job이 만들어지거나 하나도 안 만들어지는 경우가 있어 **Job은 멱등해야 한다**.
- `concurrencyPolicy`는 같은 CronJob이 만든 Job 사이에만 적용된다. 그러므로 플랫폼이 줘도 작업 쪽의 회차 선점·멱등은 여전히 필요하다.
- v1.32부터 생성된 Job에 `batch.kubernetes.io/cronjob-scheduled-timestamp` 주석으로 원래 예정 시각이 붙는다. 회차 키로 쓰기 좋다.

### 4. 놓친 실행의 보정 — 세 정책

```text
 예정:  1  2  3 │ 4  5  6  7  8  9 │ 10(재시작)
 실행:  ✔  ✔  ✔ │    전원 다운      │
 ① 몰아서 전부  : 4 5 6 7 8 9 를 지금 실행   (횟수가 계약일 때 — 일별 집계 등)
 ② 최근 하나만  : 9 만 실행                  (최신 상태만 의미 있을 때 — 캐시 갱신)
 ③ 마감 안의 것만: 8 9 실행, 4~7은 '놓침'으로 기록·알람 (늦으면 쓸모없는 일 — 백업 등)
```

- 보정에는 **실행 이력**이 필요하다. "마지막으로 성공한 회차"를 기록에서 읽어야 빈칸을 안다. 1절의 ③(회차 선점 테이블)에 상태(RUNNING·SUCCEEDED·FAILED)를 같이 기록하면 이력이 된다(적용 2절 코드).
  - 선점 행만으로는 성공을 알 수 없다. 선점 직후 죽으면 RUNNING 행이 남고, 유일 키 때문에 재선점도 막힌다. 그래서 오래된 RUNNING을 실패로 보고 다시 돌리는 복구 규칙을 따로 둔다(Spring Batch도 JVM이 갑자기 죽은 실행은 사람이 FAILED·ABANDONED로 바꿔 줘야 재시작할 수 있다고 적는다 — [31](../31-batch-job-restart-and-checkpoint/2-summary.md)). 아래 예시 `claim`은 `DO NOTHING`이라 FAILED 회차도 다시 선점하지 못한다. 재실행은 FAILED 행을 `UPDATE … SET status='RUNNING' WHERE status='FAILED'`로 가져가는 경로를 따로 둔다.
- 회복 직후는 가장 약한 순간이다. ①은 밀린 것을 한꺼번에 돌려 부하를 키운다(원본 10의 고정 주기 "몰아서"). 보정 실행에도 동시 실행 상한을 둔다.
- 보정한 회차는 **그 회차의 시각으로** 계산해야 한다. 4번 회차를 지금 시각 기준 데이터로 돌리면 결과가 틀린다(입력 범위를 회차 키에서 계산한다).

### 실험: 두 인스턴스, 다섯 가지 조정 방식

- 인스턴스 A·B가 같은 "500ms마다" 작업(50ms)을 가진다. B의 방아쇠는 150ms 늦게 당겨진다(시계 차이·지연 흉내).
- 조정 저장소: PostgreSQL 17.11(전용 컨테이너). 락은 ShedLock JDBC 방식을 흉내 낸 행 하나(`name` PK, `lock_until`), 획득은 `UPDATE … WHERE lock_until <= now()`. 시각은 DB 시계(`now()`).
- 방식: 조정 없음 / 락(끝나면 즉시 해제) / 락 + `lockAtLeastFor` 400ms / 회차 선점(`INSERT … ON CONFLICT DO NOTHING`) / 락(`lockAtMostFor` 400ms) + A가 2번 회차에서 700ms 멈춤.

핵심 코드(전체: 실험 목록의 `SchedHA.java`):

```java
// ShedLock 흉내: 만료된 락만 가져간다
"UPDATE shedlock SET lock_until = now() + make_interval(secs => ?), locked_at_start = now(), locked_by=? " +
"WHERE name='settle' AND lock_until <= now()"
// 해제: lockAtLeastFor만큼은 쥐고 있는다
"UPDATE shedlock SET lock_until = greatest(now(), locked_at_start + make_interval(secs => ?)) WHERE name='settle' AND locked_by=?"
// 회차 선점: 회차가 유일 키
"INSERT INTO job_run(job, slot, owner) VALUES ('settle', ?, ?) ON CONFLICT DO NOTHING"
```

(실험, PostgreSQL 17.11 + JDK 21.0.12, `--cpus=2`, 2026-10-01 — 집필 2회·점검 2회 실행해 출력이 같았다)

```text
슬롯 500ms · B 방아쇠 +150ms · 작업 50ms
NONE                             실행 12회 / 슬롯 6 · 동시 실행 최대 1 · 1:[A, B] 2:[A, B] 3:[A, B] 4:[A, B] 5:[A, B] 6:[A, B]
LOCK_RELEASE_AT_END              실행 12회 / 슬롯 6 · 동시 실행 최대 1 · 1:[A, B] 2:[A, B] 3:[A, B] 4:[A, B] 5:[A, B] 6:[A, B]
LOCK_AT_LEAST_FOR                실행  6회 / 슬롯 6 · 동시 실행 최대 1 · 1:[A] 2:[A] 3:[A] 4:[A] 5:[A] 6:[A]
SLOT_CLAIM                       실행  6회 / 슬롯 6 · 동시 실행 최대 1 · 1:[A] 2:[A] 3:[A] 4:[A] 5:[A] 6:[A]
LOCK_LEASE_EXPIRES_DURING_PAUSE  실행  6회 / 슬롯 6 · 동시 실행 최대 2 · 1:[A] 2:[A] 3:[B] 4:[B] 5:[B] 6:[B]
재시작 시점 슬롯 10, 마지막 성공 3 → 놓친 슬롯 [4, 5, 6, 7, 8, 9]
  몰아서 전부(catch-up all) : [4, 5, 6, 7, 8, 9]
  가장 최근 하나만          : [9]
  마감 2슬롯 안의 것만      : [8, 9]  (나머지 4개는 '놓침'으로 기록·알람)
```

- 관찰 1 — 조정 없음: 회차마다 A·B가 모두 돌았다(12회). 이중 정산의 모양이다.
- 관찰 2 — 락만 걸고 끝나면 바로 풀면 **역시 12회**다. 동시에 돈 적은 없다(동시 최대 1). A가 50ms 만에 풀고, 150ms 늦게 온 B가 같은 회차를 다시 잡았다. "락이 있으니 한 번"은 틀렸다. 락은 **같은 시각**의 중복만 막는다.
- 관찰 3 — `lockAtLeastFor` 400ms 또는 회차 선점이면 회차당 1회다. 회차 선점은 시계 차이 크기와 무관하게 성립한다. 락 + 최소 보유는 "최소 보유 시간 > 방아쇠 어긋남"일 때만 성립한다.
- 관찰 4 — lease가 작업보다 짧으면: A가 2번 회차에서 700ms 걸리는 동안 400ms에 락이 만료됐다. B가 3번 회차에서 락을 잡아 **A와 겹쳐** 돌았다(동시 최대 2). 해제는 `locked_by`를 확인하므로 A의 늦은 해제가 B의 락을 지우지는 않았다. 그 뒤로는 B가 계속 먼저 잡았다(누가 잡을지는 타이밍이 정한다).
- 관찰 5 — 보정: 실행 이력 테이블에서 마지막 성공(3)을 읽어 빈칸(4~9)을 계산했다. 정책에 따라 6개 / 1개 / 2개를 돌린다. 이 부분은 이력 조회와 정책 계산을 보인 것이고, 보정 실행 자체의 부하는 재지 않았다.

## 쓰이는 자료구조·알고리즘

- **우선순위 큐(최소 힙)** — "다음 실행 시각이 가장 이른 작업"을 꺼낸다. JDK `ScheduledThreadPoolExecutor`의 지연 큐가 이 방식이다. [data-structure/07-heap](../../data-structure/07-heap/2-summary.md).
- **타이머 휠(timing wheel)** — 원형 버킷 배열. 슬롯 = (만료 시각 / 틱) mod 휠 크기. 등록·취소가 O(1)이라 타이머가 아주 많을 때(I/O 타임아웃 수십만 개) 힙 대신 쓴다. Netty `HashedWheelTimer`(4.1)는 Varghese·Lauck(1987) "Hashed and Hierarchical Timing Wheels"를 따르고, 기본 틱 100ms·휠 크기 512다. 대신 정확한 시각이 아니라 틱 단위로 근사 실행한다. 크론처럼 드문 작업에는 힙이면 충분하다.

```text
 휠 크기 8, 틱 100ms           지금 바늘 → [3]
   [0] [1] [2] [3] [4] [5] [6] [7]
                ↑ 바늘이 칸을 지날 때 그 칸의 타이머 중 '바퀴 수 0'인 것을 실행
   1200ms 뒤 타이머 → 12틱 → 칸 (3+12) mod 8 = 7, 남은 바퀴 12 div 8 = 1
```

- **lease(기한 있는 소유)** — `lock_until`. 주인이 죽으면 시간이 지나 저절로 풀린다. 대신 늦게 깨어난 옛 주인을 시간만으로는 막지 못한다.
- **유일 키 선점** — `(job, slot)` 기본 키. 회차 단위의 멱등. [13-idempotency](../13-idempotency/2-summary.md)의 키 선점과 같은 재료다.
- **실행 이력(작업 저장소)** — 회차별 상태(시작·성공·실패). 보정·감시·재실행의 근거. Spring Batch의 JobRepository가 이 역할이다([31](../31-batch-job-restart-and-checkpoint/2-summary.md)).

## 적용 — 풀어나가는 법

### 1. 순서

1. **작업의 성질** — 횟수가 계약인가(집계·정산), 최신만 의미 있나(캐시 갱신), 늦으면 쓸모없나(백업). 보정 정책이 여기서 정해진다.
2. **회차 키를 정한다** — `job + 예정 시각(UTC)`. 실행 시각이 아니라 **예정** 시각이다.
3. **회차 선점** — 유일 키 `INSERT`. 이긴 쪽만 실행한다. 이력이 같이 남는다.
4. **작업 자체를 멱등하게** — 같은 회차를 두 번 돌려도 결과가 같게(덮어쓰기·업서트). 플랫폼(CronJob)도 "대략 한 번"이다.
5. **오래 걸리는 작업** — lease를 쓰면 실행 시간보다 훨씬 길게, 또는 실행 중 갱신(heartbeat)한다. 결과 쓰기에 fencing token을 싣는다.
6. **보정 정책** — 재시작 시 이력에서 빈칸을 계산하고 정책대로 처리한다. 놓친 회차는 지표·알람으로 남긴다.
7. **감시** — "마지막 **성공** 회차가 얼마나 오래됐나"로 알람(안 도는 것을 감시).

### 2. 회차 선점 + 멱등 실행 (Java, Spring 개념 예)

```java
@Scheduled(cron = "0 0 2 * * *", zone = "UTC")           // 시간대를 명시한다
void settleDaily() {
    Instant slot = Instant.now().truncatedTo(ChronoUnit.DAYS).plus(2, ChronoUnit.HOURS); // 예정 시각
    if (!claim("settle", slot)) return;                   // 다른 인스턴스가 이미 가져감
    try {
        settlement.run(slot.minus(1, ChronoUnit.DAYS), slot); // 입력 범위는 회차 키에서 계산
        finish("settle", slot, "SUCCEEDED");
    } catch (RuntimeException e) {
        finish("settle", slot, "FAILED");                   // 실패도 기록 → 재실행·알람 대상
        throw e;
    }
}

boolean claim(String job, Instant slot) {
    return jdbc.update("""
        INSERT INTO job_run(job, slot, owner, status, started_at)
        VALUES (?, ?, ?, 'RUNNING', now()) ON CONFLICT (job, slot) DO NOTHING
        """, job, Timestamp.from(slot), hostName) == 1;
}
```

- 정산 결과 쓰기는 `INSERT … ON CONFLICT (settle_date, merchant_id) DO UPDATE`처럼 회차 단위로 덮어쓰게 만든다. 그러면 회차 선점이 실패한 드문 경우(수동 재실행 등)에도 결과 표에 이중 기록이 생기지 않는다.
- 업서트는 **DB 행**의 중복만 막는다. 실제 송금처럼 외부 호출이 있으면 지급 요청에도 (회차, 가맹점) 단위 멱등 키를 실어야 돈이 두 번 나가지 않는다([13-idempotency](../13-idempotency/2-summary.md)).

### 3. 재시작 보정

```sql
-- 최근 7일 중 성공 기록이 없는 회차(1일 주기, 02:00 UTC)
-- date_trunc의 세 번째 인자 'UTC'로 세션 TimeZone과 무관하게 UTC 기준 자정을 잡는다
SELECT g AS missed_slot
  FROM generate_series(date_trunc('day', now(), 'UTC') - interval '7 days' + interval '2 hours',
                       now(), interval '1 day') g
 WHERE NOT EXISTS (SELECT 1 FROM job_run r WHERE r.job = 'settle' AND r.slot = g AND r.status = 'SUCCEEDED');
```

- 이 쿼리는 마지막 성공 **이전**의 빈칸도 돌려준다. "마지막 성공 이후만" 보정하려면 하한을 `(SELECT max(slot) FROM job_run WHERE job='settle' AND status='SUCCEEDED')`로 둔다.
- 세 번째 인자 없이 `date_trunc('day', now())`를 쓰면 DB 세션 시간대의 자정이 된다. 세션이 `Asia/Seoul`이면 02:00 KST(= 17:00 UTC 전날)를 만들어 코드의 02:00 UTC 회차 키와 어긋나, 성공한 회차도 빈칸으로 나온다(PostgreSQL 17 컨테이너에서 확인: 세션 `Asia/Seoul`에서 2인자판은 `02:00+09`, `'UTC'` 3인자판은 `11:00+09` = 02:00 UTC).

### 4. 진단

```bash
# Kubernetes: CronJob의 마지막 예정·성공 시각과 이벤트
kubectl get cronjob settle -o jsonpath='{.status.lastScheduleTime} {.status.lastSuccessfulTime}'
kubectl describe cronjob settle | sed -n '/Events/,$p'     # "too many missed start times" 등
kubectl get jobs -l app=settle --sort-by=.metadata.creationTimestamp
```

- PromQL 개념 예: `time() - job_last_success_timestamp_seconds{job="settle"} > 26*3600` — 하루 주기 작업이 26시간 넘게 성공하지 못했다.

## 장애 시나리오와 대처

### 1. 두 인스턴스가 같은 배치를 실행 → 이중 정산 (⚠)

- 현상: 파드를 2개로 늘린 날부터 가맹점 정산금이 두 번 지급됐다.
- 보이는 형태: 같은 예정 시각의 실행 로그가 두 호스트에. 정산 결과 표에 같은 (날짜, 가맹점) 행이 둘(유일 제약이 없을 때).
- 원인: 스케줄러 상태가 프로세스 안에만 있다. 두 대는 서로를 모른다(실험 NONE: 12회).
- 대처: 회차 선점 테이블(실험 SLOT_CLAIM: 6회), 정산 결과에 (날짜, 가맹점) 유일 제약과 업서트, 외부 송금 요청에는 같은 단위의 멱등 키. 리더만 스케줄러를 돌리는 방식도 쓸 수 있다.

### 2. 락을 걸었는데도 같은 회차가 두 번 돈다

- 현상: ShedLock을 붙였는데 짧은 작업이 가끔 두 번 실행된다. 동시에 돈 기록은 없다.
- 보이는 형태: 같은 회차 실행 로그가 수십~수백 ms 간격으로 두 호스트에. 두 서버의 시계 차이 또는 GC로 방아쇠가 어긋났다.
- 원인: 작업이 끝나자마자 락이 풀려, 늦게 방아쇠를 당긴 쪽이 다시 잡았다(실험 LOCK_RELEASE_AT_END: 12회).
- 대처: `lockAtLeastFor`를 시계 차이·방아쇠 지연보다 길게(실험: 6회). 더 견고하게는 회차 자체를 유일 키로 선점한다.

### 3. 작업이 lease보다 길어 두 개가 겹친다

- 현상: 평소 5분 걸리던 작업이 데이터 증가로 15분이 되자, 다른 인스턴스가 같은 작업을 시작해 결과가 섞였다.
- 보이는 형태: 두 실행의 시간 구간이 겹친다. 락 테이블의 `locked_by`가 실행 도중 바뀌었다.
- 원인: `lockAtMostFor`(lease)가 실행 시간보다 짧았다. 만료로 락이 넘어갔는데 옛 주인은 모른다(실험 LEASE: 동시 최대 2).
- 대처: lease를 실행 시간 최대치보다 훨씬 길게, 또는 실행 중 갱신(heartbeat). 결과 쓰기에 fencing token을 싣고 저장소가 검사한다. 실행 시간 추세를 지표로 본다.

### 4. 장애 중 놓친 실행 (⚠)

- 현상: 배포 사고로 3시간 동안 스케줄러가 없었다. 그 사이 시간별 집계 세 칸이 비었는데 아무도 몰랐다.
- 보이는 형태: 에러 로그 없음. 집계 표의 빈 시간대. Kubernetes라면 오래 멈춘 뒤 `too many missed start times` 이벤트가 난다(놓친 회차 100개 초과 — 예: 1분 주기 CronJob이 100분 넘게 멈춤). 이때도 빠진 회차들은 채워지지 않는다. 문서는 Job을 시작하지 않는다고 적지만, v1.34.0 소스는 가장 최근 회차 하나는 시작할 수 있다.
- 원인: 스케줄러는 지나간 회차를 기본적으로 다시 돌리지 않거나(크론의 구조적 건너뛰기), 정책 없이 하나만 돈다.
- 대처: 실행 이력에서 빈칸을 계산해 작업 성질에 맞는 정책(전부·최근 하나·마감 안)으로 보정한다. 놓친 회차 수를 지표로 내고, "마지막 성공이 오래됨" 알람을 둔다. CronJob이면 `startingDeadlineSeconds`로 보정 범위를 명시한다.

### 5. 보정 실행이 회복 직후를 다시 무너뜨린다

- 현상: 장애 복구 직후 밀린 회차 수십 개가 한꺼번에 돌아 DB가 다시 느려졌다.
- 보이는 형태: 재시작 직후 같은 작업의 동시 실행이 회차 수만큼. 원본 10의 고정 주기 "몰아서"와 같은 모양.
- 원인: 보정 정책이 "전부, 즉시, 동시"였다.
- 대처: 보정은 순서대로 하나씩(동시 실행 상한 1~2), 오래된 회차는 업무 판단으로 건너뛰거나 수동 처리. CronJob이면 `concurrencyPolicy: Forbid`.

## 핵심 문장

- 스케줄러 이중화는 "한 대가 죽어도 돌고, 두 대가 살아도 한 번만"이다. 둘 다 공유 기록 없이는 안 된다.
- 락은 같은 시각의 중복만 막는다. 실험에서 끝나자마자 푼 락은 150ms 늦은 인스턴스가 같은 회차를 다시 돌게 했다(12회).
- 회차(예정 시각)를 유일 키로 선점하면 시계 차이와 무관하게 회차당 한 번이 되고, 그 기록이 보정의 재료가 된다.
- lease가 작업보다 짧으면 두 실행이 겹친다. lease는 넉넉하게 잡거나 갱신하고, 결과 쓰기는 fencing으로 막는다.
- 놓친 실행의 보정은 작업 성질이 정한다 — 전부, 최근 하나, 마감 안의 것. 어느 쪽이든 놓친 수를 지표로 남긴다.
- 플랫폼 스케줄러(Kubernetes CronJob)도 "대략 한 번"이다. 작업은 멱등해야 한다.

## 관련 주제·근거

- 선행
  - [distributed/12-coordination-and-fencing](../../distributed/12-coordination-and-fencing/2-summary.md) — 분산 락·lease·fencing token
  - 원본 [ops-patterns/10-scheduler](../../ops-patterns/10-scheduler/2-summary.md) — 방아쇠 네 종류, 크론 `*/n`, DST
- 후속·연결
  - [distributed/10-leader-election](../../distributed/10-leader-election/2-summary.md) — 리더만 스케줄러를 도는 방식
  - [13-idempotency](../13-idempotency/2-summary.md) — 유일 키 선점과 멱등
  - [31-batch-job-restart-and-checkpoint](../31-batch-job-restart-and-checkpoint/2-summary.md) — 체크포인트·실행 이력 · [32-batch-and-job-time-bounds](../32-batch-and-job-time-bounds/2-summary.md)
  - [29-cache-stampede](../29-cache-stampede/2-summary.md) — 중앙 스케줄러로 캐시 미리 채우기
- 근거
  - Kubernetes 문서 "CronJob"(concurrencyPolicy·startingDeadlineSeconds·100개 초과·timeZone·"approximately once"·멱등 권고·v1.32 scheduled-timestamp 주석) <https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/>
  - ShedLock README(7.10.1 기준 — at most once at the same time, 건너뛰기, lockAtMostFor·lockAtLeastFor, 시계 동기 가정, "not a distributed scheduler") <https://github.com/lukas-krecan/ShedLock>
  - PostgreSQL 17 문서 "Date/Time Functions" — `date_trunc(field, timestamptz, zone)`, 2인자판은 세션 `TimeZone` 기준 <https://www.postgresql.org/docs/17/functions-datetime.html>
  - Spring Batch 문서 "Advanced Meta-Data Usage" — 비정상 종료 실행의 상태 복구 <https://docs.spring.io/spring-batch/reference/job/advanced-meta-data.html>
  - Netty 4.1 `HashedWheelTimer` Javadoc(기본 틱 100ms·휠 512, 근사 실행) · Varghese & Lauck, "Hashed and Hierarchical Timing Wheels", SOSP 1987
- 실험 목록
  - 두 인스턴스 × 조정 방식 5가지 + 보정 정책 계산 — `SchedHA.java`, PostgreSQL 17.11 전용 컨테이너, JDK 21 + JDBC 42.7.4, `--cpus=2`, 집필 2회·점검 2회 실행(같은 출력)
