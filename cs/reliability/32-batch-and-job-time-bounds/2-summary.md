# reliability/32-batch-and-job-time-bounds — 배치·스케줄 작업의 시간 한도 — 정리 (힌트)

## 해결하는 문제

요청-응답에는 기다리는 사용자가 있어서 "느리다"가 바로 보인다. 배치·스케줄 작업에는 기다리는 사람이 없다.\
그래서 멈춘(hang) 잡은 아무도 모르게 몇 시간씩 머물고, 그 사이 다음 회차가 겹쳐 돌거나, 결과를 기다리는 아침 보고서가 비어 있다.

```text
 00:00 정산 잡 시작 ──────── (외부 API 응답 없음, 멈춤) ──────────────────────────>
 01:00 다음 회차 시작 ── 같은 데이터를 또 처리 ──>          이중 실행
 06:00 보고서 생성: 정산 결과 없음                           아무 경보도 없었다
 09:00 담당자 출근 후 발견                                   "끝나면 소요 시간을 검사"하는 경보는 끝나지 않으니 울리지 않았다
```

- *잡(job)·단계(step)·태스크(task)*: 잡 = 스케줄 한 회차의 전체 작업. 단계 = 그 안의 순서 있는 묶음. 태스크 = 단계 안의 작은 실행 단위(파티션 하나, 청크 하나).
- *hang*: 실패도 성공도 하지 않고 진행이 멈춘 상태. 예외가 없으니 실패 처리 경로를 타지 않는다.
- *마감 경보(deadline alert)*: 정해진 시각까지 끝나지 **않았으면** 그 시각에 울리는 경보. 끝난 뒤에 소요 시간을 보는 검사와 다르다.

쉬운 예: 빨래를 돌려 놓고 외출했다.
- 세탁기가 중간에 멈추면(hang) 집에 와서야 안다. "끝나면 알림"은 끝나지 않으니 울리지 않는다.
- "2시간이 지나도 안 끝나면 알림"이 있어야 밖에서 안다.
- 다음 빨래를 같은 세탁기에 넣으려면(다음 회차) 앞 빨래가 끝났는지(겹침 방지)부터 확인해야 한다.

똑같은 구조다.\
실무 예: 야간 정산, 파일 적재 ETL, Kubernetes CronJob, Airflow DAG, 큐 백필 작업.\
스케줄러 이중화·중복 실행 방지의 기초는 원본 [ops-patterns/10-scheduler](../../ops-patterns/10-scheduler/2-summary.md)에, 체크포인트·재시작 설계 본문은 [31-batch-job-restart-and-checkpoint](../31-batch-job-restart-and-checkpoint/2-summary.md)에 둔다. 이 노트는 **시간 한도**만 본다.

## 동작·원리

### 1. 시간 한도는 세 층이다

```text
 잡 전체 ─────────────────────────────── 잡 타임아웃 (예: K8s activeDeadlineSeconds, Airflow dagrun_timeout)
   ├ 단계 1 ──────────────               단계 타임아웃
   │   ├ 태스크 ── ── ──                 태스크 타임아웃 (예: Airflow execution_timeout)
   ├ 단계 2 ────────────────────
   └ 단계 3 ───────
 별도 축: 시작 마감(예: K8s CronJob startingDeadlineSeconds) · 마감 경보(끝나지 않아도 발화)
```

- 잡 전체 타임아웃만 있으면 "늦었다"는 알아도 **어느 단계가** 느린지 모른다. 단계·태스크 한도가 원인을 좁힌다.
- 태스크 한도는 재시도 단위와 맞춘다. 태스크 하나를 다시 하면 되도록 작게 자른다.
- 제품 예(문서로 확인한 것)
  - Kubernetes Job `activeDeadlineSeconds`: 잡이 몇 번 Pod를 만들었든 잡 전체 기간에 적용된다. 도달하면 실행 중인 Pod를 모두 종료하고 잡은 `Failed`(`reason: DeadlineExceeded`)가 된다. `backoffLimit`보다 우선한다. 단 잡을 일시중지(suspend)했다 재개하면 이 타이머가 멈췄다가 재설정된다(Kubernetes Job 문서).
  - Kubernetes CronJob `startingDeadlineSeconds`: 정해진 시각을 놓쳤을 때 **시작**해도 되는 마감. 지나면 그 회차를 건너뛴다. 설정하지 않으면 마감이 없다. 10초 미만이면 컨트롤러가 10초마다 확인하므로 아예 스케줄되지 않을 수 있다(CronJob 문서).
  - Airflow `execution_timeout`: 태스크 한 번의 최대 실행 시간. 넘으면 `AirflowTaskTimeout`(Airflow 3.3 문서 Tasks "Timeouts").
  - Airflow `dagrun_timeout`: DAG 실행 한 번의 최대 시간. 넘으면 실행 중인 태스크 인스턴스는 skipped로 표시된다(Airflow `dag.py` 문서 문자열).
  - Spring Batch의 잡·스텝 단위 시간 한도 설정은 이번에 문서로 확인하지 못했다 `[?]`.

### 2. 겹침 — 멈춘 회차와 다음 회차

```text
 스케줄  ▼        ▼        ▼        ▼
 run#1   ██
 run#2            █████████████████████████  (hang)
 run#3                     ██               ← 가드가 없으면 run#2와 겹쳐 실행
```

- Kubernetes CronJob `concurrencyPolicy`: `Allow`(기본, 겹쳐 실행 허용) · `Forbid`(앞 회차가 안 끝났으면 이번 회차를 건너뜀) · `Replace`(앞 회차를 새 회차로 교체). 같은 CronJob이 만든 Job끼리만 적용된다(CronJob 문서).
- Airflow `max_active_runs`: DAG당 동시 실행 상한. 기본은 `[core] max_active_runs_per_dag` = 16(Airflow 설정 문서).
- 기본값이 "겹침 허용"인 경우가 많다. 멱등이 아닌 잡은 직접 막아야 한다.

### 3. heartbeat·lease — "살아 있음"과 "진행 중"은 다르다

```text
 리스(lease): 소유자 + 만료 시각. 소유자가 갱신(heartbeat)을 멈추면 만료 → 다른 실행이 가져간다.
   살아 있음 heartbeat: 별도 스레드가 주기적으로 갱신  → 본 작업이 멈춰도 갱신은 계속된다
   진척 heartbeat:     작업이 한 단위를 끝낼 때만 갱신 → 멈추면 갱신도 멈춘다
```

- *리스(lease)*: 기한이 있는 소유권. 갱신하지 않으면 저절로 풀린다. 조정 서비스 위의 리스·펜싱은 [distributed/12-coordination-and-fencing](../../distributed/12-coordination-and-fencing/2-summary.md).
- 별도 스레드가 보내는 heartbeat는 **프로세스가 살아 있다**는 증거일 뿐이다. 본 작업이 외부 호출에서 멈춰도 리스는 영원히 유지된다. 그러면 다음 회차는 계속 건너뛰고, 아무 작업도 진행되지 않는다.
- Airflow의 Task Instance Heartbeat Timeout은 반대 경우(워커가 OOM 등으로 죽었는데 태스크가 running으로 남은 경우)를 찾아 정리한다(Airflow 문서, 예전 이름 zombie task). 이것도 "죽음"을 찾는 장치이지 "멈춤"을 찾는 장치가 아니다.
- 리스가 만료된 뒤 옛 소유자가 깨어나 쓰는 것은 리스만으로 막지 못한다. 쓰기에 펜싱 토큰을 싣는다(distributed/12).

### 4. 마감 경보 — 끝나지 않아도 발화

- 완료 시점에 "소요 시간 > 기준"을 검사하는 경보는 **끝나야** 돈다. hang이면 영원히 울리지 않는다.
- 마감 경보는 시작할 때 타이머를 걸고, 그 시각에 아직 안 끝났으면 울린다.
- Airflow 3.1부터 Deadline Alerts가 있다(실험적 기능). Airflow 2의 SLA 기능은 3.0에서 제거되었고 3.1에서 Deadline Alerts로 대체되었다(Airflow 3.3 문서).
  - 구성: 기준 시각(reference: DAG run이 큐에 들어간 시각, 논리 날짜, 고정 시각, 과거 평균 실행 시간 등) + 간격(interval) + 콜백. "기준 + 간격까지 끝나지 않으면" 콜백이 돈다.

### 5. 강제 종료 뒤의 부분 산출물

```text
 직접 쓰기:     report.csv ← 줄 1..7 쓰고 kill → report.csv(7줄)가 남는다 → 다음 단계가 반쪽 파일을 읽는다
 임시 + rename: report.csv.tmp-48 ← 줄 1..7 쓰고 kill → report.csv 없음 → 다음 단계는 "아직 없음"으로 본다
                (임시 파일은 남는다 → 시작 시 청소)
```

- 같은 파일 시스템 안의 원자적 rename은 "없음 → 완성본"으로만 보이게 한다. 독자는 반쪽을 볼 수 없다. 단 rename 전에 쓰기·닫기가 성공했는지 확인했을 때만 "완성본"이다(아래 실험 B 주의).
- DB라면 트랜잭션·스테이징 테이블 후 교체, 객체 저장소라면 완성 후 매니페스트(성공 표식) 기록이 같은 역할이다.

### 6. 실험 A: 멈춘 회차 — 가드 없음 vs 살아 있음 heartbeat vs 진척 heartbeat + 잡 타임아웃

- 시간을 압축했다: 스케줄 1초마다, 정상 실행 300ms, 2번째 회차만 멈춘다(인터럽트 전까지 무한 대기). 6초 동안 본다.
- 시나리오
  - A: 가드·타임아웃 없음.
  - B: 리스(TTL 1.5초) + 별도 스레드가 500ms마다 갱신하는 "살아 있음" heartbeat. 타임아웃 없음.
  - C: 리스(TTL 1.5초) + 단계를 끝낼 때만 갱신하는 진척 heartbeat + 잡 타임아웃 1.5초(인터럽트로 중단, 리스 해제).
- 경보 둘: 마감 경보(스케줄 + 1초에 안 끝났으면 발화), 완료 시 검사 경보(끝날 때 소요 > 1초면 발화).

```java
// 마감 경보: 시작할 때 걸고, 끝나면 취소
ScheduledFuture<?> deadlineAlert = sched.schedule(() -> log(me + " [마감 경보] ..."), 1000, MILLISECONDS);
// 살아 있음 heartbeat(B): 본 작업과 무관하게 갱신
sched.scheduleAtFixedRate(() -> lease.renew(me, 1500), 500, 500, MILLISECONDS);
// 진척 heartbeat(C): 단계를 끝낼 때만
for (int step = 0; step < 3; step++) { Thread.sleep(100); lease.renew(me, 1500); }
// 잡 타임아웃(C)
sched.schedule(() -> { if (!f.isDone()) f.cancel(true); }, 1500, MILLISECONDS);
```

(실험, JDK 21.0.12 Temurin, 컨테이너 `--cpus=2`, 2026-10-01)

```text
== A: 가드 없음 · 타임아웃 없음
  t= 1015ms run#2 시작 — 멈춘다(hang)
  t= 2014ms run#2 [마감 경보] 스케줄+1000ms가 지났는데 아직 안 끝남
  결과: 회차 7 · 완료 6 · 건너뜀 0 · 동시 실행 최대 2 · 지금도 도는 실행 1
  t= 6517ms run#2 인터럽트로 중단 → 부분 산출물 정리·리스 해제
== B: 리스 + 살아 있음 heartbeat(별도 스레드) · 타임아웃 없음
  t= 1001ms run#2 시작 — 멈춘다(hang)
  t= 2001ms run#2 [마감 경보] 스케줄+1000ms가 지났는데 아직 안 끝남
  t= 2001ms run#3 리스 획득 실패 → 이번 회차 건너뜀
  t= 3001ms run#4 리스 획득 실패 → 이번 회차 건너뜀
  t= 4000ms run#5 리스 획득 실패 → 이번 회차 건너뜀
  t= 5000ms run#6 리스 획득 실패 → 이번 회차 건너뜀
  t= 6000ms run#7 리스 획득 실패 → 이번 회차 건너뜀
  결과: 회차 7 · 완료 1 · 건너뜀 5 · 동시 실행 최대 1 · 지금도 도는 실행 1
  t= 6502ms run#2 인터럽트로 중단 → 부분 산출물 정리·리스 해제
== C: 리스 + 진척 heartbeat + 잡 타임아웃 1.5s
  t= 1001ms run#2 시작 — 멈춘다(hang)
  t= 2001ms run#3 리스 획득 실패 → 이번 회차 건너뜀
  t= 2001ms run#2 [마감 경보] 스케줄+1000ms가 지났는데 아직 안 끝남
  t= 2501ms run#2 잡 타임아웃 1500ms → cancel(true)
  t= 2502ms run#2 인터럽트로 중단 → 부분 산출물 정리·리스 해제
  결과: 회차 7 · 완료 5 · 건너뜀 1 · 동시 실행 최대 1 · 지금도 도는 실행 0
```

- 관찰 1 — A: 멈춘 run#2 옆에서 다음 회차들이 계속 돌아 동시 실행이 2가 됐다. 멱등이 아닌 잡이면 이중 처리다.
- 관찰 2 — B: 겹침은 막았다(최대 1). 그러나 별도 스레드 heartbeat가 멈춘 run#2의 리스를 계속 갱신해 run#3~7이 **전부** 건너뛰었다. 완료 1(run#1)뿐이다.
- 관찰 3 — C: 진척이 멈추자 리스 갱신도 멈췄고, 1.5초 잡 타임아웃이 run#2를 인터럽트해 정리했다. 건너뛴 회차는 run#3 하나, 완료 5.
- 관찰 4 — 세 시나리오 모두 **마감 경보는 2.0초에 울렸다**. 완료 시 검사 경보는 한 번도 울리지 않았다. run#2는 끝나지 않았기 때문이다.
- A·B의 6.5초 "인터럽트로 중단" 줄은 실험을 끝내며 정리한 것이다. 실제로는 그대로 남는다(결과 줄의 "지금도 도는 실행 1").

### 7. 실험 B: 강제 종료 뒤 부분 산출물 — 직접 쓰기 vs 임시 파일 + 원자적 rename

```java
Path target = atomic ? out.resolveSibling(out.getFileName() + ".tmp-" + pid) : out;
try (PrintWriter w = new PrintWriter(Files.newBufferedWriter(target))) {
    for (int i = 1; i <= 10; i++) { w.println("row," + i); w.flush(); Thread.sleep(200); }
}
if (atomic) Files.move(target, out, StandardCopyOption.ATOMIC_MOVE);
```

- 주의: 이 실험 코드는 강제 종료만 보려고 단순화했다. `PrintWriter`는 I/O 오류를 예외로 던지지 않는다(JDK 21 `PrintWriter` 문서 — `checkError()`로 물어야 한다). 실무 코드라면 `BufferedWriter`를 직접 써서 쓰기·닫기 예외를 받거나 `checkError()`를 확인한 뒤에만 `Files.move`한다. 그렇지 않으면 디스크 가득 참 같은 오류에도 반쪽 파일이 최종 이름으로 올라간다.

(실험, JDK 21.0.12, 컨테이너 안에서 `timeout -s KILL 1.5`(uutils coreutils 0.8.0)로 강제 종료, 2026-10-01 — 임시 파일 이름의 pid(48)는 실행마다 다르다)

```text
direct: 1.5초에 SIGKILL (timeout 종료 코드 124)
atomic: 1.5초에 SIGKILL (timeout 종료 코드 124)
--- 강제 종료 직후 out/
out/report-atomic.csv.tmp-48: 7줄
out/report-direct.csv: 7줄
```

- 관찰: 직접 쓰기는 최종 이름(`report-direct.csv`)에 7줄짜리 반쪽 파일을 남겼다. 다음 단계는 이것을 완성본으로 읽는다.
- 임시 + rename은 최종 이름이 아예 없다. 반쪽은 `.tmp-48`로만 남았다. 다음 실행이 시작할 때 임시 파일을 청소하면 된다.
- `timeout`의 종료 코드 124는 "시간 초과로 끝냈다"는 뜻이다. 단 이 값은 구현에 따라 다르다. 이 컨테이너의 `timeout`은 uutils coreutils 0.8.0이었고 124를 돌려줬다(사실 점검 재실행에서 확인). GNU coreutils `timeout`은 KILL 신호면 137(128+9)로 끝나고, 이 137은 명령이 KILL을 받았든 `timeout` 자신이 받았든 같아 구별할 수 없다(GNU coreutils 매뉴얼 "timeout invocation"). 명령이 스스로 124를 돌려줄 수도 있다. 그래서 종료 코드는 단서일 뿐이다. 시간 초과 판별은 래퍼가 "타이머가 발화했다"를 따로 로그·지표로 남겨 함께 본다.

## 쓰이는 자료구조·알고리즘

- **리스 = (소유자, 만료 시각)** — 획득은 "비었거나 만료됐을 때만", 갱신은 "내 것일 때만". 실험의 `Lease` 클래스가 그 최소형이다. 분산 버전은 etcd lease·ZooKeeper 세션([distributed/12](../../distributed/12-coordination-and-fencing/2-summary.md)).
- **펜싱 토큰** — 리스를 잃은 옛 소유자의 늦은 쓰기를 자원이 거절하게 하는 단조 증가 번호.
- **지연 큐·타이머** — 마감 경보와 잡 타임아웃은 "이 시각에 이것을 확인하라"는 예약이다. 많은 예약은 시각 순 우선순위 큐(힙)로 관리한다([data-structure/07-heap](../../data-structure/07-heap/2-summary.md)).
- **체크포인트** — 처리한 위치(오프셋·키·청크 번호)를 원자적으로 기록해, 재시작 때 거기서부터 한다. 설계 본문은 [31](../31-batch-job-restart-and-checkpoint/2-summary.md).
- **원자적 rename** — 같은 파일 시스템 안의 `rename`은 다른 독자에게 원자적으로 보인다. "임시에 쓰고 바꿔 단다"는 커밋 패턴이다.

## 적용 — 풀어나가는 법

### 1. 순서

1. 잡을 단계·태스크로 나누고 각 단위의 정상 소요 분포를 잰다(p50·p99).
2. 태스크 한도 = 태스크 p99.x + 여유. 단계·잡 한도는 그 위에.
3. 겹침 정책을 정한다: 멱등이면 허용 가능, 아니면 금지 + 리스.
4. 리스 갱신은 **진척**에 묶는다. 별도 스레드로 갱신한다면 "마지막 진척 시각"이 너무 오래됐을 때 갱신을 멈추게 한다.
5. 타임아웃이 나면 실제로 멈추게 한다(인터럽트 확인·프로세스 종료 — [09](../09-cancellation-propagation/2-summary.md)).
6. 산출물은 임시에 쓰고 완성 후 원자적으로 바꿔 단다. 시작 시 남은 임시를 청소한다.
7. 체크포인트를 남겨, 타임아웃 뒤 재실행이 처음부터가 아니라 이어서 하게 한다.
8. 마감 경보: "다음 소비자가 이 결과를 필요로 하는 시각"에서 역산해 건다.

### 2. Kubernetes CronJob 예

```yaml
apiVersion: batch/v1
kind: CronJob
metadata: { name: nightly-settlement }
spec:
  schedule: "0 0 * * *"
  concurrencyPolicy: Forbid          # 앞 회차가 안 끝났으면 이번 회차를 건너뛴다(기본 Allow)
  startingDeadlineSeconds: 1800      # 30분 넘게 늦으면 이번 회차는 시작하지 않는다
  jobTemplate:
    spec:
      activeDeadlineSeconds: 7200    # 잡 전체 2시간. 넘으면 Pod 종료, Failed/DeadlineExceeded
      backoffLimit: 2
      template:
        spec:
          restartPolicy: Never
          containers:
          - name: settle
            image: example/settle:1.0   # (예시)
```

- `Forbid`는 앞 회차가 멈춰 있으면 다음 회차를 계속 건너뛴다(실험 A의 시나리오 B 모양). 그래서 `activeDeadlineSeconds`와 함께 둔다.
- 값은 예시다.

### 3. Airflow 예

```python
with DAG(
    dag_id="nightly_settlement",
    schedule="0 0 * * *",                         # 매일 0시. Airflow 3.x는 기본이 None(자동 실행 안 함)
    dagrun_timeout=timedelta(hours=2),            # DAG 실행 전체
    max_active_runs=1,                             # 겹침 금지(기본 16)
    deadline=DeadlineAlert(                        # 3.1+ (실험적)
        reference=DeadlineReference.DAGRUN_QUEUED_AT,
        interval=timedelta(hours=1, minutes=30),
        callback=AsyncCallback(SlackWebhookNotifier, kwargs={"text": "정산이 마감까지 안 끝남"}),
    ),
):
    load = PythonOperator(task_id="load", python_callable=load_fn,
                          execution_timeout=timedelta(minutes=20))   # 태스크 한 번
```

- `DeadlineAlert`·`AsyncCallback`의 import 경로는 버전마다 바뀌었다(문서: 3.2에서 `AsyncCallback` 경로 변경). 쓰는 버전 문서로 확인한다.

### 4. Java — 진척 기반 heartbeat

```java
volatile long lastProgressNanos = System.nanoTime();
// 작업: 청크 하나 끝낼 때마다
lastProgressNanos = System.nanoTime(); checkpoint.save(offset);
// 갱신 스레드: 진척이 끊기면 갱신하지 않는다 → 리스가 만료되어 다른 실행이 넘겨받는다
scheduler.scheduleAtFixedRate(() -> {
    if (System.nanoTime() - lastProgressNanos < STALL_LIMIT_NANOS) lease.renew(me, ttl);
    else log.warn("진척 없음 {}s — 리스 갱신 중단", STALL_LIMIT_NANOS / 1e9);
}, 0, ttl / 3, MILLISECONDS);
```

### 5. 진단

```bash
# K8s: 겹쳐 도는 Job, 마감 초과로 실패한 Job
kubectl get jobs -l app=nightly-settlement --sort-by=.status.startTime
kubectl get job <name> -o jsonpath='{.status.conditions[?(@.type=="Failed")].reason}'   # DeadlineExceeded
# 멈춘 잡이 어디서 멈췄나(자바)
jcmd <pid> Thread.print | grep -B2 -A8 'SettlementJob'
# 남은 임시 산출물
find /data/out -name '*.tmp-*' -mmin +60
```

## 장애 시나리오와 대처

### 1. 잡이 멈춘다 → 다음 스케줄과 겹쳐 이중 실행 (⚠ 커리큘럼)

- 현상: 같은 날짜의 정산이 두 번 반영됐다.
- 보이는 형태: 같은 잡의 실행 둘이 시간대가 겹친다(실험 A: 동시 실행 최대 2). 멈춘 실행의 로그가 어느 외부 호출 뒤로 끊겨 있다.
- 원인: 겹침 허용이 기본(K8s `concurrencyPolicy: Allow`)이고, 잡 타임아웃이 없다.
- 대처: 겹침 금지 + 리스, 잡 타임아웃, 잡 자체를 멱등하게(같은 날짜 재처리가 결과를 바꾸지 않게).

### 2. 잡 전체 타임아웃만 있다 → 어느 단계가 느린지 모른다 (⚠ 커리큘럼)

- 현상: 잡이 `DeadlineExceeded`로 실패했는데 원인 단계를 모른다. 다음 날도 같다.
- 보이는 형태: 잡 단위 지표·로그만 있다. 단계별 시작·끝 시각이 없다.
- 원인: 한도·관측이 잡 단위뿐이다.
- 대처: 단계·태스크 한도와 단계별 소요 지표. 태스크 한도는 재시도 단위와 맞춘다.

### 3. 타임아웃으로 kill한 뒤 부분 산출물이 남는다 (⚠ 커리큘럼)

- 현상: 다음 단계가 반쯤 된 파일·테이블을 읽어 보고서 숫자가 작다. 에러는 없다.
- 보이는 형태: 산출물의 행 수가 평소보다 적다(실험 B: 10줄 중 7줄). 산출물 수정 시각이 kill 시각과 같다.
- 원인: 최종 위치에 직접 썼다.
- 대처: 임시 + 원자적 rename, 스테이징 테이블 교체, 완료 표식(매니페스트). 시작 시 임시 청소. 다음 단계는 완료 표식이 있을 때만 읽는다.

### 4. 체크포인트가 없다 → 매번 처음부터 다시 해서 영원히 못 끝낸다 (⚠ 커리큘럼)

- 현상: 데이터가 늘어 잡이 한도를 조금 넘기기 시작했고, 그 뒤로 한 번도 성공하지 못한다.
- 보이는 형태: 매 실행이 같은 진행률 근처에서 타임아웃. 재시도마다 처음부터 같은 로그.
- 원인: 타임아웃 뒤 재실행이 0부터 시작한다. 한도보다 긴 일은 재시도로 절대 끝나지 않는다.
- 대처: 체크포인트에서 이어 하기([31](../31-batch-job-restart-and-checkpoint/2-summary.md)), 잡 분할(날짜·파티션), 병렬화. SRE 22장도 체크포인트를 남기며 진행하는 작업은 데드라인 뒤에도 계속할 가치가 있을 수 있다고 적는다.

### 5. SLA 경보가 작업이 끝난 뒤에야 발화한다 (⚠ 커리큘럼)

- 현상: 잡이 멈춘 날 아침까지 아무 경보가 없었다. 담당자가 수동으로 발견했다.
- 보이는 형태: 경보 규칙이 "완료 이벤트의 소요 시간 > 기준"이다. 실험 A에서 이 경보는 세 시나리오 모두 한 번도 울리지 않았다.
- 원인: 끝나야 검사하는 경보는 hang을 못 잡는다.
- 대처: 마감 경보(시작 때 타이머, 마감에 미완료면 발화 — 실험에서 2.0초에 울림). Airflow 3.1+ Deadline Alerts, 또는 "마지막 성공 시각"이 기준보다 오래되면 울리는 경보.

### 6. 살아 있음 heartbeat가 멈춘 잡을 계속 살려 둔다

- 현상: 겹침 방지를 넣었더니 이번엔 잡이 며칠째 한 번도 안 돈다.
- 보이는 형태: 리스 소유자가 며칠 전 시작한 실행이다. 그 실행의 진척 로그가 없다. 실험 A의 B: 5회차 연속 건너뜀.
- 원인: 별도 스레드 heartbeat는 프로세스 생존만 증명한다.
- 대처: 리스 갱신을 진척에 묶는다(적용 4). 잡 타임아웃을 함께 둔다.

## 핵심 문장

- 배치에는 기다리는 사용자가 없어서 멈춤이 보이지 않는다. 잡·단계·태스크 세 층의 한도와 시작 마감이 필요하다.
- 겹침 허용이 기본인 스케줄러가 많다(K8s CronJob `Allow`, Airflow `max_active_runs` 16). 멈춘 회차와 다음 회차가 겹치면 이중 실행이다.
- 별도 스레드 heartbeat는 "살아 있음"만 증명한다. 실험에서 그런 리스는 멈춘 회차를 붙잡아 다음 5회차를 모두 건너뛰게 했다. 리스 갱신은 진척에 묶는다.
- 끝날 때 소요 시간을 검사하는 경보는 hang에 울리지 않는다. 마감 시각에 미완료면 울리는 경보가 필요하다.
- 강제 종료는 부분 산출물을 남긴다. 임시에 쓰고 원자적으로 바꿔 달면 독자는 "없음" 또는 "완성본"만 본다.

## 관련 주제·근거

- 선행
  - [08-time-budget-allocation](../08-time-budget-allocation/2-summary.md) — 한도를 분포에서 정하기
  - [30-scheduler-and-cron-ha](../30-scheduler-and-cron-ha/2-summary.md) · 원본 [ops-patterns/10-scheduler](../../ops-patterns/10-scheduler/2-summary.md)
  - [31-batch-job-restart-and-checkpoint](../31-batch-job-restart-and-checkpoint/2-summary.md) — 체크포인트·재시작 설계 본문
  - [data-engineering/08-idempotent-pipelines-and-backfill](../../data-engineering/08-idempotent-pipelines-and-backfill/2-summary.md)
- 연결
  - [distributed/12-coordination-and-fencing](../../distributed/12-coordination-and-fencing/2-summary.md) — lease·fencing token
  - [09-cancellation-propagation](../09-cancellation-propagation/2-summary.md) — 타임아웃 뒤 실제로 멈추기
  - [05-timeouts-and-deadline-propagation](../05-timeouts-and-deadline-propagation/2-summary.md) — SRE의 "체크포인트 작업은 데드라인 뒤에도" 예외
- 문서
  - Kubernetes Job 문서 — `activeDeadlineSeconds`(잡 전체, `DeadlineExceeded`, `backoffLimit`보다 우선) <https://kubernetes.io/docs/concepts/workloads/controllers/job/>
  - Kubernetes CronJob 문서 — `startingDeadlineSeconds`(미설정 = 마감 없음, 10초 미만 주의), `concurrencyPolicy` Allow(기본)·Forbid·Replace <https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/>
  - Airflow 3.3 문서 Tasks "Timeouts"(`execution_timeout`, `AirflowTaskTimeout`), "SLAs"(3.0 제거, 3.1 Deadline Alerts로 대체), "Task Instance Heartbeat Timeout" <https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/tasks.html>
  - Airflow 3.3 문서 "Deadline Alerts"(실험적, reference·interval·callback, DAGRUN_QUEUED_AT 등) <https://airflow.apache.org/docs/apache-airflow/stable/howto/deadline-alerts.html>
  - Airflow `task-sdk/src/airflow/sdk/definitions/dag.py`(main) — `dagrun_timeout`, `max_active_runs`; `config.yml` — `max_active_runs_per_dag` 기본 16
  - Google SRE 책 22장 — 체크포인트하는 따라잡기 작업의 예외
- 실험 목록
  - A `Jobs.java` — 1초 스케줄, run#2 hang, 가드 없음 / 살아 있음 heartbeat 리스 / 진척 heartbeat 리스 + 잡 타임아웃, 마감 경보 vs 완료 시 검사 경보. JDK 21.0.12 컨테이너 `--cpus=2`
  - B `Writer.java` — 10줄 산출물을 200ms마다 쓰다가 1.5초에 SIGKILL, 직접 쓰기 vs 임시 + `ATOMIC_MOVE`. 같은 컨테이너
