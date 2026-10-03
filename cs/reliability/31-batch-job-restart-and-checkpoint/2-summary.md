# reliability/31-batch-job-restart-and-checkpoint — 배치 재시작: 청크 커밋·체크포인트·멱등 재실행·실행 이력·DST — 정리 (힌트)

## 해결하는 문제

정산 배치가 1000만 행을 3시간 동안 처리한다.\
2시간째에 프로세스가 죽었다(배포 SIGTERM, OOM, 노드 교체). 다시 돌리면 무엇이 일어나나?

```text
 처음부터 다시 돌림                 체크포인트에서 이어 감
 [■■■■■■■■■■□□□□□]  2시간째 죽음     [■■■■■■■■■■□□□□□]  2시간째 죽음
 [■■■■■■■■■■■■■■■]  처음부터          체크포인트 = 마지막 커밋한 청크의 끝
  앞 2/3은 두 번 정산된다             [··········■■■■■]  거기서부터
```

- *배치(batch)*: 쌓인 데이터를 한꺼번에 처리하는 작업. 정산, 집계, 대량 변환, 파일 적재.
- *체크포인트(checkpoint)*: "여기까지 확실히 끝났다"는 표시. 다시 시작할 때 거기서부터 간다.
- *멱등 재실행*: 같은 입력으로 다시 돌려도 결과가 한 번 돌린 것과 같은 성질. 범위는 "같은 잡 인스턴스·같은 입력"으로 한정한다.

쉬운 예: 책 1000쪽 옮겨 적기다.
- 책갈피 없이 쓰다 잠들면, 깨어나서 처음부터 다시 쓴다. 앞부분이 두 번 적힌다.
- 100쪽마다 책갈피(체크포인트)를 꽂고, 공책에도 "100쪽까지 옮김"을 함께 적는다. 깨어나면 책갈피부터 쓴다.
- 쓴 줄 번호를 같이 적어 두면(멱등 키), 실수로 같은 쪽을 다시 써도 이미 쓴 줄은 건너뛸 수 있다.

똑같은 구조다.\
실무 예: 일 정산, 포인트 소멸, 월말 청구서 생성, 대량 백필, 데이터 이관.\
같은 문제의 DB 쪽 기초(청크 트랜잭션, OFFSET 함정, keyset 청크, 체크포인트 테이블)는 [database/34-large-backfill-and-batch-dml](../../database/34-large-backfill-and-batch-dml/2-summary.md) 「동작·원리」 3~4에 있다. 이 노트는 그 위에서 **잡 수준**의 재시작·이력·부분 실패·스케줄을 다룬다.

## 동작·원리

### 1. 청크 처리 — 쓰기와 체크포인트를 한 트랜잭션에

```text
 청크 크기 100 (commit interval)
 ┌─ 트랜잭션 ───────────────────────────────────────────┐
 │ read 100행 (id > last_id ORDER BY id LIMIT 100)       │
 │ process: 행마다 변환                                  │
 │ write: ledger에 100행 INSERT                          │
 │ checkpoint: UPDATE ckpt SET last_id = 이 청크의 끝     │
 └─ COMMIT ──────────────────────────────────────────────┘   → 다음 청크
 중간에 죽으면: 이 트랜잭션은 통째로 롤백 → last_id는 직전 청크 끝 그대로
```

- *청크(chunk)*: 한 번에 커밋하는 묶음. Spring Batch는 "commit interval"이라고 부른다.
- 쓰기와 체크포인트를 **같은 트랜잭션**에 넣는 것이 핵심이다.
  - 따로 커밋하면 "썼는데 체크포인트 못 남김"(재시작 때 중복)이나 "체크포인트는 남겼는데 쓰기 실패"(누락)가 생긴다.
  - 같은 DB에 있어야 이렇게 묶을 수 있다. 쓰는 곳이 다른 시스템(파일, 외부 API)이면 멱등 쓰기로 보완한다.
- 커서는 keyset(`id > last_id`)으로 둔다. OFFSET은 중간에 행이 지워지면 조용히 행을 건너뛴다([database/34](../../database/34-large-backfill-and-batch-dml/2-summary.md) 「동작·원리」 2).
- Spring Batch도 같은 구조다.
  - 스텝의 `ExecutionContext`를 커밋 지점마다 잡 저장소에 저장한다.
  - `ItemStream.update`는 "커밋 전에" 불려 현재 위치를 컨텍스트에 넣는다.
  - 재시작하면 리더가 컨텍스트의 위치에서 시작한다(Spring Batch 문서 "ItemStream", "Domain Language of Batch — ExecutionContext").

### 2. 재실행을 안전하게 — 두 가지 축

```text
                     체크포인트 없음                 체크포인트 있음
 쓰기가 멱등 아님    ✗ 앞부분 중복                     ○ 청크 경계까지는 안전
                                                     (체크포인트 밖 부수효과는 중복 가능)
 쓰기가 멱등         ○ 결과는 맞음, 처음부터 다시 읽음    ◎ 결과도 맞고 이어서 감
```

- *멱등 쓰기*: 같은 쓰기를 두 번 해도 한 번과 같게 만드는 방법. 예: 원천 행 ID에 유일 제약 + `ON CONFLICT DO NOTHING`, 결과를 덮어쓰는 `UPSERT`.
- 체크포인트는 **속도**(다시 읽지 않음)를, 멱등 쓰기는 **정확성**(다시 써도 같음)을 준다. 외부 호출처럼 트랜잭션에 묶이지 않는 부수효과가 있으면 둘 다 필요하다. 외부 호출 쪽 멱등 키는 [13-idempotency](../13-idempotency/2-summary.md) 참고.

### 3. 실행 이력 — 잡 저장소와 상태 기계

```text
 JobInstance = Job 이름 + 식별 파라미터 (예: settle, date=2026-09-30)
   └─ JobExecution #1  STARTED ──(kill -9)──> STARTED 그대로 남음  ← 재시작 불가 상태
   └─ (사람이 판정)
        ├─ FAILED 로 바꿈    → JobExecution #2  STARTED ──> COMPLETED   ← 같은 인스턴스의 두 번째 실행
        └─ ABANDONED 로 바꿈 → 이 인스턴스는 끝 (같은 파라미터로 다시 실행하면 거절)
 상태: STARTING → STARTED → COMPLETED | FAILED | STOPPING → STOPPED | ABANDONED
```

- *잡 저장소(job repository)*: 잡 실행 이력(언제, 어떤 파라미터로, 몇 행 읽고 썼나, 어디까지 갔나, 상태)을 담는 테이블. Spring Batch는 `BATCH_JOB_INSTANCE`·`BATCH_JOB_EXECUTION`·`BATCH_STEP_EXECUTION`·`..._CONTEXT` 테이블을 쓴다.
- Spring Batch 문서(Domain Language)의 규칙:
  - `JobInstance` = Job + 식별 JobParameters. 같은 날짜 파라미터로 다시 실행하면 **새 JobExecution**이지만 JobInstance는 하나다.
  - JobInstance는 실행 하나가 성공해야 완료로 본다. 완료(또는 ABANDONED)된 인스턴스를 다시 실행하면 `JobInstanceAlreadyCompleteException`이 난다(spring-batch main `TaskExecutorJobLauncher.java`).
  - 재시작할 때 이미 COMPLETED인 스텝은 건너뛴다(`allowStartIfComplete`로 바꿀 수 있다).
- **프로세스가 갑자기 죽으면 상태를 못 고친다.** Spring Batch 문서("Advanced Metadata Usage — Recovering a job"):
  - JVM이 갑자기 끝나면 실행이 `STARTED`로 남고, 그 상태는 재시작할 수 없다. `JobOperator.recover` 뒤 `restart`로 살린다.
  - kill -9 뒤 이 실행을 FAILED(재시작)로 볼지 ABANDONED(포기)로 볼지는 "비즈니스 결정이며 자동화할 방법이 없다". FAILED로 바꾸는 것은 재시작 데이터가 유효하다고 알 때만.
  - 6.0부터 `JobExecutionShutdownHook`을 JVM 종료 훅에 걸 수 있다. SIGTERM이 오면 실행에 중지 신호를 보낸다.
  - 단, 이 훅은 청크가 끝나기를 기다리지 않는다(v6.0.5 소스).
    - `run()`은 `jobOperator.stop()`을 한 번 부르고 바로 끝난다. `stop()`은 실행을 STOPPING으로 바꾸고 끝 시각을 쓴다. 저장소는 그것을 곧바로 STOPPED로 올려 저장한다(`SimpleJobOperator.stop`, `SimpleJobRepository.update`).
    - 종료 훅이 모두 끝나면 JVM은 작업 스레드를 기다리지 않고 멈춘다(`Runtime.addShutdownHook` javadoc). 그래서 진행 중 청크는 보통 커밋되지 않고 롤백된다. 다음 재시작은 마지막으로 커밋된 청크 뒤부터다.
    - 문서의 "중지는 즉시가 아니다, 제어가 프레임워크로 돌아올 때 멈춘다"는 JVM이 계속 살아 있을 때의 `stop` 이야기다. 청크 경계까지 기다리려면 실행 상태를 폴링하며 기다리는 훅을 따로 둔다(`JobOperator.stop` javadoc: 멈췄는지는 폴링으로만 안다).

### 4. 부분 실패 — 스킵은 성공이 아니다

```text
 1000행 중 3행이 처리 불가 (금액 NULL)
 조용한 스킵: status = COMPLETED, 쓰기 997      ← 모니터링은 "성공"으로 본다
 보고하는 스킵: status = COMPLETED WITH SKIPS, 스킵 [137, 444, 901], 종료 코드 ≠ 0
```

- *스킵(skip)*: 처리 못 하는 항목을 건너뛰고 계속 가는 것.
- Spring Batch 문서("Configuring Skip Logic"):
  - 스킵 한도를 둔다. 한도가 10이면 **11번째** 스킵에서 스텝이 실패한다.
  - 금융 데이터처럼 정확해야 하는 데이터는 스킵하면 안 될 수 있다. 이것은 데이터를 아는 사람이 정한다.
- 스킵이 있어도 스텝 상태는 기본으로 COMPLETED다. 문서("Controlling Step Flow")는 `StepExecutionListener.afterStep`에서 `getSkipCount() > 0`이면 종료 상태를 `COMPLETED WITH SKIPS`로 바꾸는 예를 보인다. **누군가 바꾸지 않으면 바깥에서는 성공으로 보인다.**

### 실험: 550행에서 죽인 뒤 다시 돌리기

- 환경: PostgreSQL 17 컨테이너 `sn-rl-w14-pg`, Java 21 + PostgreSQL JDBC 42.7.4, 각 `--cpus=2`.
- 데이터: `src` 1000행, 금액 = `id % 7 + 1`(합 4003). `ledger`에 옮긴다.
- 죽이기: 550번째 행에서 `Runtime.halt(137)`(종료 훅 없이 끝남 — kill -9 흉내).
- 네 가지:
  1. 체크포인트 없음, 행마다 자동 커밋, 재실행은 처음부터.
  2. 같은데 `ledger(src_id)` 유일 인덱스 + `ON CONFLICT DO NOTHING`(멱등 쓰기).
  3. 청크 100 + 체크포인트를 같은 트랜잭션에. 실행 이력 테이블에 STARTED/COMPLETED.
  4. 금액 NULL 3행 — 조용한 스킵 vs 스킵 보고.

청크 모드의 핵심:

```java
c.setAutoCommit(false);
while (true) {
    r.setInt(1, from);                                   // SELECT ... WHERE id > ? ORDER BY id LIMIT 100
    ResultSet rs = r.executeQuery();
    int last = -1;
    while (rs.next()) { last = rs.getInt(1); /* INSERT INTO ledger ... */ }
    if (last < 0) break;
    ck.setInt(1, last); ck.executeUpdate();              // UPDATE ckpt SET last_id = ?
    c.commit();                                          // 청크 쓰기와 체크포인트가 함께 커밋
    from = last;
}
```

(실험, PostgreSQL 17 + JDK 21, 2026-10-01 — 결정적이라 실행마다 같다)

```text
== 1) 체크포인트 없음 — 550행에서 죽고 처음부터 재실행
  [550행에서 kill -9] ledger 행/합/중복 src_id: 549 / 2193 / 0
  [끝] ledger 행/합/중복 src_id: 1549 / 6196 / 549
== 2) 멱등 쓰기(src_id 유일 + ON CONFLICT DO NOTHING) — 같은 재실행
  [550행에서 kill -9] ledger 행/합/중복 src_id: 549 / 2193 / 0
  [끝] ledger 행/합/중복 src_id: 1000 / 4003 / 0
== 3) 청크 100 + 체크포인트(같은 트랜잭션) — 550행에서 죽고 재실행
  체크포인트에서 재개: last_id = 0
  [550행에서 kill -9] ledger 행/합/중복 src_id: 500 / 1997 / 0
  거절: 직전 실행이 STARTED로 남아 있다(죽은 실행인지 사람이 판정해야 한다)
  recover: 직전 실행 STARTED → FAILED로 표시
  체크포인트에서 재개: last_id = 500
  [끝, 이번 실행 쓰기 500] ledger 행/합/중복 src_id: 1000 / 4003 / 0
== 4) 처리 불가 행 3개 — 조용한 스킵 vs 스킵 보고
setup: src 1000 / 3988 (행 수 / 금액 합)
  상태 = COMPLETED, 쓰기 997
  [끝] ledger 행/합/중복 src_id: 997 / 3988 / 0
  (종료 코드 0)
  상태 = COMPLETED WITH SKIPS, 쓰기 997, 스킵 [137, 444, 901] → 종료 코드 3
  [끝] ledger 행/합/중복 src_id: 997 / 3988 / 0
  (종료 코드 3)
```

- 관찰 1 — 체크포인트 없음: 재실행 뒤 1549행, 합 6196. 앞 549행이 **두 번** 정산됐다(중복 src_id 549). 에러는 없었다.
- 관찰 2 — 멱등 쓰기: 처음부터 다시 읽었지만 결과는 1000행·4003으로 맞다. 앞 549행을 다시 읽는 비용은 그대로다.
- 관찰 3 — 청크 + 체크포인트: 죽은 순간 501~549행을 쓰던 청크는 롤백됐다(500행·1997). 재실행은 `last_id = 500`부터 500행만 썼다.
  - 집필 코드는 보고를 찍으려고 `halt` 직전에 `rollback()`을 직접 불렀다. 점검에서 `rollback()` 없이 바로 `halt`하고 다른 프로세스에서 조회해도 ledger는 500행·1997이었다. 연결이 끊기면 PostgreSQL이 커밋 안 된 트랜잭션을 버린다(점검 실험, 같은 환경, 2026-10-01).
- 관찰 4 — 실행 이력: kill -9로 실행이 STARTED에 남자, 다음 실행은 그것을 보고 **거절**했다. 사람이 FAILED로 판정한 뒤에야 재개했다. Spring Batch의 STARTED 고착과 같은 모양이다(이 실험은 직접 만든 흉내다).
- 관찰 5 — 스킵: 두 경우 데이터는 똑같이 997행이다. 다른 것은 **상태와 종료 코드**뿐이다. 그리고 금액 합은 원천과 ledger가 **같다**(3988 = 3988). NULL은 합에서 빠지기 때문이다. 합계 대사로는 누락을 못 잡고, **행 수 대사**(1000 vs 997)로 잡힌다.

### 5. 스케줄 — 시간대와 DST

```text
 America/New_York, 2026-03-08 02:00 → 03:00 (봄, 시계가 한 시간 앞으로)
   "30 2 * * *"  → 02:30이 존재하지 않는 날
 America/New_York, 2026-11-01 02:00 → 01:00 (가을, 01시대가 두 번)
   "30 1 * * *"  → 01:30이 두 번 오는 날
```

- *DST(일광 절약 시간)*: 계절에 따라 지역 시각을 한 시간 앞당기거나 되돌리는 제도. 그날 하루는 23시간이나 25시간이다.
- 스케줄러마다 이 날을 다르게 처리한다.
  - cronie(리눅스 `cron`, man cron(8)): 3시간 미만의 시각 변경을 특별 처리한다. 앞으로 갔으면 건너뛴 시간대의 잡을 **바로** 실행한다. 뒤로 갔으면 두 번 실행하지 않는다. 특정 시각 잡과 한 시간보다 긴 주기의 잡에만 적용된다.
  - robfig/cron v3(쿠버네티스 CronJob 컨트롤러가 쓰는 Go 라이브러리 — `kubernetes/pkg/controller/cronjob/utils.go`가 import, go.mod v3.0.1): 문서에 "jobs scheduled during daylight-savings leap-ahead transitions will not be run!"이라고 적혀 있다. 되돌아가는 날은 아래 실험처럼 두 번 나온다.
- 쿠버네티스 CronJob은 `.spec.timeZone`으로 시간대를 지정한다. `schedule` 안에 `CRON_TZ=`·`TZ=`를 쓰면 검증 오류다(쿠버네티스 문서 "CronJob").

### 실험: robfig/cron v3가 뽑는 DST 전환일의 실행 시각

```go
s, _ := cron.NewParser(cron.Minute | cron.Hour | cron.Dom | cron.Month | cron.Dow).Parse("30 2 * * *")
for t = s.Next(from); t.Before(end); t = s.Next(t) { fmt.Println(t) } // from·end는 America/New_York
```

(실험, golang:1.23-alpine + github.com/robfig/cron/v3 v3.0.1, 2026-10-01 — 결정적)

```text
robfig "30 2 * * *" (America/New_York):
  2026-03-07 02:30 EST  (UTC 07:30)
  2026-03-09 02:30 EDT  (UTC 06:30)
robfig "30 1 * * *" (America/New_York):
  2026-10-31 01:30 EDT  (UTC 05:30)
  2026-11-01 01:30 EDT  (UTC 05:30)
  2026-11-01 01:30 EST  (UTC 06:30)
  2026-11-02 01:30 EST  (UTC 06:30)
```

- 관찰: 3월 8일 실행이 **없다**(누락). 11월 1일에는 01:30 EDT와 01:30 EST, **두 번**이다(UTC로 한 시간 차).
- 범위: 라이브러리의 `Next` 결과다. 쿠버네티스 컨트롤러가 이 결과에 무엇을 더 거르는지는 이 실험으로 확인하지 않았다 `[?]`.
- 해석: 일 1회 정산을 지역 시각 01:00~03:00에 두면 1년에 두 번 문제가 난다. UTC로 스케줄하거나, DST가 없는 시간대(예: Asia/Seoul)를 쓰거나, 잡 자체를 "날짜 파라미터 기준 한 번"으로 멱등하게 만든다.

### 6. 배포와 장시간 잡

```text
 잡 3시간 ──────────────────────────────────────────>
            ↑ 배포 SIGTERM (유예 30초)
            ├─ 종료 훅 없음: 즉시 종료 → 실행 이력 STARTED 고착, 분산 락은 TTL까지 남음
            ├─ 기본 JobExecutionShutdownHook: STOPPED 기록 → 훅 반환 → JVM 종료 → 진행 중 청크는 롤백
            └─ 기다리는 훅을 직접 둠: 중지 신호 → 청크 경계까지 폴링 대기 → STOPPED → 락 해제 → 다음 실행이 이어 감
```

- 우아한 종료([14-graceful-shutdown](../14-graceful-shutdown/2-summary.md))의 배치판이다. HTTP 요청처럼 몇 초 안에 끝나지 않으므로 "끝까지 기다리기"는 답이 아니다. **청크 경계에서 멈추고 이어 가기**가 답이다.
- 잡 중복 실행을 막는 락은 소유자가 죽으면 풀려야 한다. TTL·lease 기반 락과 fencing은 [distributed/12-coordination-and-fencing](../../distributed/12-coordination-and-fencing/2-summary.md).

## 쓰이는 자료구조·알고리즘

- **체크포인트 커서(keyset)** — `last_id` 하나. 다음 청크는 `WHERE id > last_id ORDER BY id LIMIT n`. 정렬 키가 유일하고 단조여야 한다.
- **실행 상태 기계** — STARTING → STARTED → COMPLETED / FAILED / STOPPED / ABANDONED. "죽은 실행"은 상태로 남지 않으므로 STARTED 고착을 사람이나 하트비트로 판정한다.
- **실행 이력 테이블** — (잡 이름, 식별 파라미터) → 실행 목록. 같은 날짜 파라미터를 두 번 COMPLETED로 돌리지 않게 하는 키다.
- **유일 제약 = 멱등 키** — `ledger(src_id)` 유일 인덱스. 두 번째 쓰기를 DB가 거절·무시한다.
- **크론 다음 시각 계산** — 분·시·일·월·요일 필드를 맞을 때까지 올리는 탐색(robfig `SpecSchedule.Next`의 주석 "increment the field until it matches"). 지역 시각에서 하므로 DST 경계에서 구멍·중복이 생긴다.

## 적용 — 풀어나가는 법

### 1. 설계 순서

```text
 1) 잡의 정체성: 이름 + 식별 파라미터(정산일) → 같은 정산일이 두 번 COMPLETED 되지 않게
 2) 커서: keyset, 청크 크기, 체크포인트를 쓰기와 같은 트랜잭션에
 3) 쓰기를 멱등하게: 유일 키 + UPSERT / 외부 호출엔 멱등 키
 4) 부분 실패 정책: 스킵 허용 여부·한도·스킵 목록 저장·종료 상태(COMPLETED WITH SKIPS)·경보
 5) 끝난 뒤 대사: 행 수·합계·키 집합 비교 (합계만 보면 NULL 누락을 놓친다)
 6) 스케줄: 시간대 명시(UTC 권장), DST 구간 피하기, 동시 실행 정책, 시작 마감
 7) 종료: SIGTERM → STOPPED 기록, 락 해제 (청크 경계까지 기다리려면 폴링하는 훅을 따로)
```

### 2. Spring Batch(6.x) 스텝 — 청크·재시작·스킵

```java
@Bean
Step settle(JobRepository repo, PlatformTransactionManager tx,
            ItemReader<Row> reader, ItemWriter<Entry> writer) {
    return new StepBuilder("settle", repo)
        .<Row, Entry>chunk(100).transactionManager(tx)   // 100행마다 커밋 + ExecutionContext 저장
        .reader(reader)                                  // 재시작 위치를 저장하는 ItemStream 리더
        .writer(writer)                                  // INSERT ... ON CONFLICT (src_id) DO NOTHING
        .faultTolerant()
        .skipPolicy(new LimitCheckingExceptionHierarchySkipPolicy(Set.of(InvalidAmountException.class), 10))
        .listener(new SkipCheckingListener())            // 스킵 > 0 이면 ExitStatus "COMPLETED WITH SKIPS"
        .build();
}
```

- 스킵 정책 클래스는 Spring Batch 문서 "Configuring Skip Logic"의 예 그대로다. 6.x에서 패키지가 `org.springframework.batch.infrastructure.*`로 옮겨졌다(같은 문서 XML 예의 클래스 이름).
- 커서 리더는 OFFSET 대신 키 기준 페이지를 쓰는 리더를 고른다. 정렬 키를 유일 키로 둔다.

### 3. 쿠버네티스 CronJob

```yaml
apiVersion: batch/v1
kind: CronJob
spec:
  schedule: "30 17 * * *"          # UTC 17:30 = 한국 02:30
  timeZone: "Etc/UTC"              # 명시. 지역 시간대면 DST 구간을 피한다
  concurrencyPolicy: Forbid        # 기본 Allow — 앞 실행이 안 끝나도 다음 실행이 겹친다
  startingDeadlineSeconds: 3600    # 이만큼 늦으면 이번 회차는 건너뛴다(실패로 친다)
  jobTemplate:
    spec:
      backoffLimit: 2
      template:
        spec:
          terminationGracePeriodSeconds: 120   # 기다리는 종료 훅을 둘 때: 청크 하나 끝내고 STOPPED 기록할 시간
```

- 쿠버네티스 문서 "CronJob"의 규칙:
  - `concurrencyPolicy` 기본은 `Allow`다. `Forbid`는 앞 실행이 안 끝났으면 새 실행을 건너뛴다. `Replace`는 앞 실행을 새 실행으로 바꾼다.
  - `startingDeadlineSeconds`를 두지 않으면 마감이 없다. 문서는 놓친 회차가 100번을 넘으면 잡을 시작하지 않고 오류를 남긴다고 적는다("too many missed start times").
    - 단, 컨트롤러 소스(v2, v1.34.0·master `pkg/controller/cronjob/utils.go` `nextScheduleTime`)는 다르다. `TooManyMissedTimes` 경고 이벤트와 로그만 남기고 가장 최근 회차를 그대로 돌려준다. 그 회차는 마감·`concurrencyPolicy` 검사를 거쳐 시작될 수 있다. 문서와 구현이 다르므로 이벤트를 보고 판단한다.
  - 컨트롤러는 10초마다 확인하므로 `startingDeadlineSeconds`를 10초 미만으로 두면 스케줄되지 않을 수 있다.
  - 문서는 잡이 "적어도 한 번" 실행된다고 적는다(마감이 넉넉하고 `Allow`일 때). 같은 문서는 회차 하나에 잡이 둘 생기거나 하나도 안 생기는 경우가 있다며 "Jobs ... should be idempotent"라고 적는다.

### 4. 진단과 대사

```sql
-- Spring Batch: STARTED로 남은(죽은) 실행 찾기
SELECT job_execution_id, status, start_time, last_updated
FROM batch_job_execution WHERE status = 'STARTED' AND last_updated < now() - interval '1 hour';
-- 스텝별 읽기·쓰기·스킵 수
SELECT step_name, read_count, write_count, read_skip_count, process_skip_count, write_skip_count, exit_code
FROM batch_step_execution WHERE job_execution_id = :id;
-- 끝난 뒤 대사: 행 수와 키 집합 (합계만 보면 NULL 행 누락을 놓친다)
SELECT (SELECT count(*) FROM src) AS src_rows, (SELECT count(*) FROM ledger) AS ledger_rows,
       (SELECT count(*) FROM src s WHERE NOT EXISTS (SELECT 1 FROM ledger l WHERE l.src_id = s.id)) AS missing;
```

```bash
kubectl get cronjob settle -o jsonpath='{.status.lastScheduleTime} {.status.lastSuccessfulTime}'
kubectl get jobs -l <selector> --sort-by=.status.startTime   # 같은 회차 잡이 둘 있나(겹침)
```

## 장애 시나리오와 대처

### 1. 중간 실패 후 처음부터 재실행 → 앞부분 이중 정산

- 현상: 재실행 뒤 정산 금액이 원천보다 크다. 고객 일부가 두 번 지급받았다.
- 보이는 형태: 에러 로그 없음. 대사하면 같은 원천 ID가 두 번(실험 1: 중복 src_id 549, 합 6196 vs 4003).
- 원인: 체크포인트가 없고 쓰기가 멱등하지 않다. 실패 지점을 모르니 처음부터 다시 돌렸다.
- 대처: 쓰기와 체크포인트를 같은 트랜잭션에(실험 3). 원천 ID 유일 제약 + `ON CONFLICT`(실험 2). 이미 생긴 중복은 원천 ID로 찾아 역분개한다.

### 2. 실패 행을 스킵하고 "COMPLETED"로 끝남 — 부분 실패 성공 위장

- 현상: 잡 대시보드는 매일 초록색인데, 며칠 뒤 일부 가맹점이 정산을 못 받았다고 연락한다.
- 보이는 형태: 상태 COMPLETED, 종료 코드 0. 스킵 수는 스텝 실행 테이블에만 있다. 금액 합계 대사는 통과한다(실험 4: NULL이 합에서 빠져 3988 = 3988).
- 원인: 스킵을 성공과 구분해 보고하지 않았다. 대사가 합계만 봤다.
- 대처: 스킵이 있으면 `COMPLETED WITH SKIPS`와 0이 아닌 종료 코드, 스킵 목록을 별도 테이블에 저장하고 경보를 건다. 금융 데이터는 스킵을 허용하지 않는 것을 기본으로 둔다. 이때는 `faultTolerant()`·스킵 정책을 아예 두지 않는다(첫 오류에 스텝 실패). 위 `LimitCheckingExceptionHierarchySkipPolicy`는 한도 0을 받지 않는다(생성자 `skipLimit > 0` 검사, v6.0.5 소스). 대사에 행 수·누락 키를 넣는다.

### 3. DST 전환일에 `30 2 * * *` 잡이 누락되거나 `30 1 * * *` 잡이 두 번 실행

- 현상: 3월 둘째 일요일(미국 기준) 정산이 없다. 11월 첫째 일요일에 01시대 잡이 두 번 돌았다.
- 보이는 형태: 실행 이력에 그날만 기록이 없거나 둘이다. 실험의 robfig 결과와 같은 모양(3/8 없음, 11/1 두 번).
- 원인: 지역 시간대로 스케줄했고, 그 시각이 그날 존재하지 않거나 두 번 존재한다. 스케줄러마다 처리 방식이 다르다(cronie는 보정, robfig는 누락·중복).
- 대처: UTC나 DST가 없는 시간대로 스케줄한다. 잡의 정체성을 "정산일 파라미터"로 두고 같은 정산일 COMPLETED가 있으면 다시 하지 않는다. 그러면 두 번 불려도 한 번만 처리된다. 누락은 "어제 정산이 없으면 경보"로 잡는다.

### 4. 배포 SIGTERM에 잡이 죽어 락·STARTED만 남음

- 현상: 배포 뒤 다음 회차 잡이 "이미 실행 중"이라며 시작하지 않는다. 또는 몇 시간 뒤 락이 풀리며 두 개가 겹친다.
- 보이는 형태: `batch_job_execution.status = 'STARTED'`인데 프로세스는 없다(실험 3의 "거절"). 분산 락 키가 TTL까지 남아 있다.
- 원인: 종료 훅이 없거나 유예 시간 안에 청크를 못 끝냈다. 상태를 고칠 기회 없이 죽었다.
- 대처: SIGTERM에 STOPPED를 기록한다(Spring Batch 6.0+ `JobExecutionShutdownHook`). 이 훅은 청크를 기다리지 않으므로 진행 중 청크는 롤백되고 재시작이 이어 간다. 청크 경계까지 기다리려면 폴링하는 훅을 따로 두고, 유예 시간을 청크 하나 처리 시간보다 길게. 죽은 실행은 하트비트(`last_updated`)로 찾아 사람이 FAILED/ABANDONED를 판정한다. 락은 lease + fencing으로.

### 5. 앞 실행이 안 끝났는데 다음 회차가 시작돼 겹친다

- 현상: 데이터가 늘어 잡이 25시간 걸린 날, 다음 날 잡이 함께 돌아 같은 행을 두 번 처리했다.
- 보이는 형태: 같은 CronJob의 잡 두 개가 동시에 Running.
- 원인: `concurrencyPolicy` 기본값 `Allow`. 애플리케이션 락도 없었다.
- 대처: `Forbid`. 그래도 컨트롤러 재시작·수동 실행으로 겹칠 수 있으니 실행 이력·락으로 한 번 더 막는다. 잡이 주기보다 길어지는 추세를 지표로 본다.

## 핵심 문장

- 배치 재시작의 핵심은 쓰기와 체크포인트를 같은 트랜잭션에 커밋하는 것이다. 그러면 죽은 청크는 통째로 롤백되고 재시작은 정확히 그 경계부터 간다(실험 3: 500행 + 500행).
- 체크포인트는 다시 읽지 않게 해 주고, 멱등 쓰기는 다시 써도 같게 해 준다. 처음부터 다시 돌린 비멱등 잡은 앞 549행을 두 번 정산했다(실험 1).
- 갑자기 죽은 실행은 STARTED로 남는다. 그것이 정말 죽었는지는 사람이 판정한다(Spring Batch 문서: 자동화할 방법이 없다).
- 스킵은 성공이 아니다. 상태·종료 코드·스킵 목록으로 드러내고, 대사는 합계뿐 아니라 행 수로 한다(실험 4: 합계는 같았다).
- 지역 시간대 크론은 DST 날 실행이 사라지거나 두 번 온다(robfig v3 실험). UTC로 스케줄하고 잡을 정산일 기준으로 멱등하게 만든다.

## 관련 주제·근거

- 선행
  - [30-scheduler-and-cron-ha](../30-scheduler-and-cron-ha/2-summary.md) — 원본 [ops-patterns/10-scheduler](../../ops-patterns/10-scheduler/2-summary.md)(고정 주기·크론·건너뛰기)
  - [13-idempotency](../13-idempotency/2-summary.md) — 원본 [ops-patterns/06-idempotency-store](../../ops-patterns/06-idempotency-store/2-summary.md)
  - [database/34-large-backfill-and-batch-dml](../../database/34-large-backfill-and-batch-dml/2-summary.md) — 청크 트랜잭션, OFFSET 함정, keyset, 체크포인트 테이블
- 후속·연결
  - [32-batch-and-job-time-bounds](../32-batch-and-job-time-bounds/2-summary.md) — 잡·단계 타임아웃, heartbeat
  - [14-graceful-shutdown](../14-graceful-shutdown/2-summary.md) — SIGTERM과 유예 시간
  - [distributed/12-coordination-and-fencing](../../distributed/12-coordination-and-fencing/2-summary.md) — 잡 단일 실행 락, lease, fencing
  - api-design 25 case-settlement-report — 노트 [api-design/04-settlement-report](../../api-design/25-case-settlement-report/)
  - [database/27-temporal-types-and-session-timezone](../../database/27-temporal-types-and-session-timezone/2-summary.md) — 시간대
- 문서·소스
  - Spring Batch 6.0 문서: "Configuring a Step for Restart"(startLimit·allowStartIfComplete), "Configuring Skip Logic"(11번째 스킵에서 실패), "Controlling Step Flow"(COMPLETED WITH SKIPS 리스너), "ItemStream"(update는 커밋 전), "The Domain Language of Batch"(JobInstance = Job + 식별 파라미터, ExecutionContext는 커밋마다 저장), "Advanced Metadata Usage"(STARTED 고착·recover·ABANDONED·JobExecutionShutdownHook 6.0+) <https://docs.spring.io/spring-batch/reference/>
  - spring-batch 소스 v6.0.5 태그: `JobExecutionShutdownHook.java`(stop 한 번 부르고 반환), `JobOperator.java`(stop javadoc: 폴링으로만 확인), `SimpleJobOperator.java`(STOPPING + endTime), `SimpleJobRepository.java`(STOPPING → STOPPED 승격), `TaskExecutorJobLauncher.java`(COMPLETED·ABANDONED 거절), `LimitCheckingExceptionHierarchySkipPolicy.java`(`skipLimit > 0`)
  - Kubernetes 문서 "CronJob"(concurrencyPolicy·startingDeadlineSeconds·100회 누락·timeZone). 100회 누락은 소스 `utils.go` `nextScheduleTime`(v1.34.0·master)과 다르다 — 경고 이벤트만 <https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/>
  - kubernetes `pkg/controller/cronjob/utils.go`(robfig/cron/v3 import), `go.mod`(v3.0.1)
  - robfig/cron `doc.go`("leap-ahead transitions will not be run"), `spec.go`(`Next`) <https://github.com/robfig/cron>
  - cron(8) man page(cronie — DST 3시간 미만 처리) <https://man7.org/linux/man-pages/man8/cron.8.html>
- 실험 목록
  - E31a 550행 kill -9 후 재실행 4종(비멱등·멱등·청크+체크포인트+실행 이력·스킵 보고) — PostgreSQL 17 + JDK 21 + JDBC 42.7.4, 코드 `Batch.java`·`run.sh`
  - E31b robfig/cron v3.0.1 `Next`로 America/New_York 2026 DST 전환일 실행 시각 — golang:1.23-alpine, 코드 `dst/main.go`
