# python/python-libraries/15 — Celery 기본 — 정리 (힌트)

> 출처 — study-site 항목 `python/celery-basics`(항목 데이터 `data/python/libraries.json`) · 정답 코드 study-practice `python/python-libraries/reference/celery-basics.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 원본 예제를 `Python 3.12.3` 에서 2회 돌렸다.

## 한눈에 — 쉽게 말하면

**Celery 는 「식당의 주문표 꽂이와 주방」이다.**
홀 직원은 주문을 받으면 주문표를 꽂이에 꽂고 곧장 다음 손님에게 간다.
요리사는 꽂이에서 주문표를 하나씩 빼서 요리하고, 다 된 요리를 배식대에 올린다.
홀 직원은 나중에 주문 번호로 배식대를 보고 요리가 나왔는지 확인한다.
아침 9시마다 해야 하는 밑준비는 벽에 붙은 시간표를 보고 알림 담당이 주문표를 대신 꽂는다.
Celery 도 똑같은 구조다.
웹앱은 할 일을 메시지로 브로커에 넣고 곧장 다음 일로 간다.
워커가 그 메시지를 꺼내 실행하고 결과를 백엔드에 적는다.

> **태스크** — Celery 가 워커 프로세스에서 대신 실행해 주는 함수다.\
> 예: `@app.task` 를 붙인 `send_email`.

> **브로커** — 태스크 메시지를 줄 세워 두는 중간 저장소다.\
> 예: `broker='redis://localhost:6379/0'`.

> **워커** — 브로커에서 메시지를 꺼내 태스크를 실제로 실행하는 프로세스다.\
> 예: `celery -A celery_app worker`.

> **결과 백엔드** — 태스크의 상태와 반환값을 적어 두는 저장소다.\
> 예: `backend='redis://localhost:6379/1'`.

| 비유 | 실체 |
|---|---|
| 홀 직원 | Producer(웹앱) — `delay()` 를 부르는 쪽 |
| 주문표 | 태스크 메시지(태스크 이름 + 인자) |
| 주문표 꽂이 | Broker(Redis / RabbitMQ) |
| 요리사 | Worker(`celery ... worker` 프로세스) |
| 배식대 | Backend(결과 저장소) |
| 주문 번호 | 태스크 ID(`result.id`) |
| 시간표를 보고 주문표를 꽂는 알림 담당 | Celery Beat |
| 주방 상황판 | Flower(모니터링 웹 화면) |

```text
 [웹앱]  --주문표-->  [브로커: 꽂이]  --꺼냄-->  [워커: 요리사]
   |                                              |
   +-- 주문 번호(ID)를 곧장 받음                   +--결과--> [백엔드: 배식대]
   +-- 나중에 번호로 배식대 확인  <----------------------------+
```

## 이 주제가 답하려는 질문

1. 오래 걸리는 일을 웹 요청 밖으로 빼려면, 무엇이 무엇을 들고 어디로 가나?
2. 평범한 함수를 태스크로 만들고 부르는 방법은 몇 가지이며, 서로 무엇이 다른가?
3. 맡긴 일의 상태와 결과는 어떻게 확인하고, 상태 이름은 무엇을 뜻하나?
4. 정해진 시각마다 일을 돌리려면 무엇을 더 설정하고 무엇을 더 띄우나?

## 동작 방식

### (1) 네 부품 — Producer · Broker · Worker · Backend

**언제 쓰나** — 이메일 발송 · 보고서 생성처럼 오래 걸리는 일을 웹 요청 안에서 기다리지 않고 뒤로 넘길 때 쓴다.
CPU 를 오래 쓰는 일(CPU-bound)이나 네트워크 · 디스크를 기다리는 일(I/O-bound)을 백그라운드로 돌리는 것이 목적이다.

> **CPU-bound** — 계산 때문에 오래 걸리는 작업이다.\
> 예: 큰 보고서의 집계 계산.

> **I/O-bound** — 바깥 응답(네트워크 · 디스크)을 기다리느라 오래 걸리는 작업이다.\
> 예: 메일 서버에 이메일 보내기.

```text
Producer (웹앱)                 Broker (Redis DB 0)            Worker (Celery)           Backend (Redis DB 1)
send_email.delay(...) --메시지--> [큐: send_email(to,...)] --꺼냄--> send_email 실행 --결과--> {ID: SUCCESS, 반환값}
   |                                                                                          ^
   +-- AsyncResult(ID) 를 곧장 받음 ---- 나중에 ID 로 상태 · 결과 조회 ------------------------+
```

그림 해설.
1. 웹앱이 `delay()` 를 부르면 태스크 이름과 인자가 메시지가 되어 브로커의 큐에 들어간다.
2. 웹앱은 함수 본문이 끝나기를 기다리지 않고 태스크 ID 를 담은 결과 객체를 곧장 받는다.
3. 워커는 큐에서 메시지를 꺼내 함수를 실제로 실행한다.
4. 워커는 상태와 반환값을 백엔드에 적는다.
5. 웹앱은 나중에 ID 로 백엔드를 조회해 상태와 결과를 얻는다.

원본의 아키텍처 그림이 이 흐름을 두 줄로 요약한다: `Producer (웹앱) -> Broker (Redis/RabbitMQ) -> Worker (Celery)`, 그리고 워커에서 `-> Backend (결과 저장)`.
브로커로는 Redis 가 가장 간편하다(원본 팁).
원본 예제는 같은 Redis 서버의 DB 번호만 달리해 브로커(`/0`)와 백엔드(`/1`)를 나눈다.

> **프로듀서** — 태스크 메시지를 만들어 브로커에 넣는 쪽이다.\
> 예: `delay()` 를 부르는 웹앱 코드.

> **큐** — 먼저 들어온 메시지부터 꺼내 가는 줄이다.\
> 예: `queue='high-priority'` 로 이름 붙인 큐.

### (2) 태스크 정의 — `@app.task` 와 옵션

**언제 쓰나** — 워커에게 맡길 함수를 만들 때 쓴다.
실패하면 다시 시도하게 하거나, 너무 오래 걸리면 끊게 할 때 옵션을 붙인다.

```text
def send_email(self, to, subject, body)     입력: 평범한 함수
        |
@app.task(bind=True, max_retries=3)         데코레이터가 감싼다
        |
send_email  = 태스크 객체                    .delay / .apply_async / .apply 를 갖게 됨
        |                                    bind=True → 첫 인자 self 에 태스크 인스턴스가 들어옴
        v
본문에서 예외 → raise self.retry(exc=exc, countdown=10)
        |
상태 RETRY → 10초 뒤 다시 실행 → 재시도는 최대 3번
```

그림 해설.
1. `@app.task` 데코레이터를 붙이면 함수가 Celery 태스크가 된다.
2. 태스크가 된 함수는 호출 메서드(`delay` · `apply_async` · `apply`)를 갖는다.
3. `bind=True` 를 주면 첫 인자 `self` 로 태스크 인스턴스에 접근할 수 있다.
4. `self` 가 있어야 `self.retry(...)` 로 재시도할 수 있고, 로깅 같은 기능도 쓸 수 있다(원본 팁).
5. `self.retry(exc=exc, countdown=10)` 는 「10초 뒤에 다시 하라」는 뜻이며, 원본은 이것을 `raise` 한다.
6. `max_retries=3` 은 재시도 한도다.

원본의 태스크 셋은 이렇다.

- `send_email(self, to, subject, body)` — `bind=True, max_retries=3`. 2초 잠든 뒤 `{'status': 'sent', 'to': to}` 를 돌려준다. 예외가 나면 10초 뒤 재시도한다.
- `process_data(data)` — 옵션 없는 `@app.task`. 리스트의 각 원소를 두 배로 만들어 `{'processed': 두 배 리스트, 'count': 원소 수}` 를 돌려준다.
- `generate_report(report_type, params)` — `time_limit=300`(5분 제한). 10초 잠든 뒤 `f'/reports/{report_type}_2024.pdf'` 를 돌려준다.

> **데코레이터** — 함수 정의 위에 `@이름` 으로 붙여 그 함수를 감싸 바꾸는 Python 문법이다.\
> 예: `@app.task`.

### (3) 호출 — `delay` · `apply_async` · `apply`

**언제 쓰나** — 태스크를 워커에게 맡길 때 `delay` 나 `apply_async` 를 쓴다.
테스트처럼 지금 이 자리에서 바로 돌려 보고 싶을 때 `apply` 를 쓴다.

```text
send_email.delay(a, b, c)
  └─> 인자만 담아 곧장 큐로 ─────────────> AsyncResult 반환 (기다리지 않음)

send_email.apply_async(args=[a, b, c], countdown=60, expires=3600, queue='high-priority')
  └─> 「60초 뒤 실행 · 1시간 지나면 만료 · high-priority 큐로」 ──> AsyncResult 반환

send_email.apply(args=[a, b, c])
  └─> 지금 이 자리에서 즉시 실행 ──────────> 결과 객체 → .get() 이 곧장 결과
```

그림 해설.
1. `delay()` 는 `apply_async()` 의 단축 형태다 — 함수 인자만 그대로 넘기고 즉시 큐에 보낸다.
2. `apply_async()` 는 인자를 `args=[...]` 로 받고, `countdown` · `eta` · `expires` · `queue` 같은 실행 옵션을 함께 받는다.
3. `countdown=60` 은 60초 뒤에 실행하라는 뜻이고, `expires=3600` 은 1시간이 지나면 만료시키라는 뜻이다.
4. `queue='high-priority'` 는 메시지를 그 이름의 큐로 보낸다.
5. 두 메서드 모두 즉시 결과 객체(`AsyncResult`)를 돌려준다 — 함수 본문의 `time.sleep(2)` 를 기다리지 않는다.
6. `apply()` 는 동기 호출이다 — 원본은 「테스트용 · 즉시 실행 후 결과 반환」이라 적는다.

> **AsyncResult** — 맡긴 태스크의 ID 를 들고 있다가 상태와 결과를 조회해 주는 객체다.\
> 예: `result = send_email.delay(...)` 의 `result`.

> **동기 호출** — 일이 끝날 때까지 기다린 뒤 다음 줄로 넘어가는 호출이다.\
> 예: `send_email.apply(...)`.

### (4) 결과와 상태 — `AsyncResult` 로 확인하기

**언제 쓰나** — 맡긴 일이 끝났는지, 성공했는지, 무엇을 돌려줬는지 알고 싶을 때 쓴다.

```text
result.id            → 태스크 ID (UUID 문자열)
result.state         → PENDING → (STARTED) → SUCCESS / FAILURE   (중간에 RETRY, 취소되면 REVOKED)
result.ready()       → 끝났나? True / False            (기다리지 않음)
result.get()         → 결과값. 끝날 때까지 멈춰 기다림   (blocking)
result.result        → 결과값. 기다리지 않고 지금 있는 것 (non-blocking)
result.successful()  → 성공했나? True / False
```

그림 해설.
1. `result.id` 는 UUID 로 된 태스크 ID 다.
2. `result.state` 는 백엔드에 적힌 현재 상태 이름이다.
3. `ready()` 는 끝났는지만 알려 주고 기다리지 않는다.
4. `get()` 은 결과가 나올 때까지 그 자리에서 멈춘다(블로킹).
5. `result.result` 는 기다리지 않고 지금 들어 있는 결과를 준다.
6. `successful()` 은 성공 여부를 준다.
7. 원본은 `if result.ready():` 안에서만 `get()` 을 불러, 끝난 경우에만 결과를 꺼낸다.

상태 여섯 가지(원본 목록).

| 상태 | 원본의 설명 |
|---|---|
| `PENDING` | 큐에 전송됨(아직 워커가 안 받음) |
| `STARTED` | 워커가 실행 중(`task_track_started=True` 필요) |
| `SUCCESS` | 성공 완료 |
| `FAILURE` | 실패 |
| `RETRY` | 재시도 대기 |
| `REVOKED` | 취소됨 |

`STARTED` 는 설정에서 `task_track_started=True` 를 켜야 기록된다.
켜지 않으면 상태는 `PENDING` 에서 바로 `SUCCESS` / `FAILURE` 로 넘어가 보인다.
`PENDING` 은 원본 주석대로 「큐에 들어갔다」가 아니라 「결과 백엔드에 정보 없음」을 뜻할 수도 있다(「어디서 틀리나 4」).

> **블로킹** — 호출한 쪽이 결과가 나올 때까지 다른 일을 못 하고 멈추는 것이다.\
> 예: `result.get()`.

> **UUID** — 겹치지 않게 만든 128비트 식별자다.\
> 예: 태스크 ID.

### (5) 주기적 태스크 — Celery Beat

**언제 쓰나** — 「30분마다 상태 점검」 · 「평일 아침 9시 보고서」처럼 시각이 정해진 일을 자동으로 맡길 때 쓴다.

```text
app.conf.beat_schedule = { 이름: {'task': ..., 'schedule': ..., 'args': ...} }
        |
celery -A celery_app beat   (별도 프로세스)
        |  시간표를 보며 때가 되면
        v
브로커에 태스크 메시지 발행 ──> 워커가 꺼내 실행 (평소 delay 와 같은 길)
```

그림 해설.
1. `app.conf.beat_schedule` 사전에 「항목 이름 → 태스크 이름 · 일정 · 인자」를 적는다.
2. Beat 는 워커와 다른 별도 프로세스이며, 시간표만 보고 있다가 때가 되면 메시지를 브로커에 넣는다.
3. 실행은 결국 워커가 한다 — Beat 는 발행만 한다.

원본의 시간표 셋.

| 항목 이름 | 태스크 | 일정 |
|---|---|---|
| `check-health-every-30-min` | `tasks.health_check` | `30.0 * 60` 초(30분)마다 |
| `daily-report` | `tasks.generate_report`, `args=('daily', {'date': 'today'})` | `crontab(hour=9, minute=0, day_of_week='1-5')` — 월~금 오전 9시 |
| `weekly-cleanup` | `tasks.cleanup_old_data` | `crontab(hour=0, minute=0, day_of_week='monday')` — 매주 월요일 자정 |

`'schedule'` 에 숫자를 주면 초 단위 간격이고, `crontab(...)` 을 주면 분 · 시 · 요일로 시각을 정한다.

> **crontab** — 분 · 시 · 요일 같은 칸으로 「언제」를 적는 일정 표기다.\
> 예: `crontab(hour=9, minute=0, day_of_week='1-5')`.

> **Celery Beat** — 시간표를 보고 때가 되면 태스크 메시지를 발행하는 스케줄러 프로세스다.\
> 예: `celery -A celery_app beat`.

### (6) 띄우는 프로세스 — worker · beat · flower

**언제 쓰나** — 코드를 다 쓴 뒤 실제로 돌릴 때, 역할마다 프로세스를 따로 띄운다.

```text
celery -A celery_app worker --loglevel=info --concurrency=4   → 태스크 실행 담당 (일꾼 4개)
celery -A celery_app beat   --loglevel=info                   → 시간표 발행 담당
pip install flower                                             → (설치 명령 — 한 번만)
celery -A celery_app flower --port=5555                       → 모니터링 웹 화면 (5555 포트)
```

그림 해설.
1. `-A celery_app` 은 Celery 앱이 들어 있는 모듈을 가리킨다.
2. `worker` 는 태스크를 실행하며, `--concurrency=4` 는 원본 주석대로 프리포크 워커 수다.
3. `beat` 는 주기적 태스크를 발행한다.
4. `flower` 는 태스크를 지켜보는 웹 UI 를 `--port` 로 준 포트에서 연다 — 실무에서는 Flower 로 모니터링한다(원본 팁).
5. `pip install flower` 는 띄우는 명령이 아니라 설치 명령이다.

> **프리포크** — 워커가 자식 프로세스를 미리 여러 개 만들어 두고 태스크를 나눠 맡기는 방식이다.\
> 예: `--concurrency=4` 면 자식 4개.

> **Flower** — Celery 태스크의 상태를 웹 화면으로 보여 주는 모니터링 도구다.\
> 예: `celery -A celery_app flower --port=5555`.

## 문법 — 형태와 규칙

최소 예제(직접 쓴 것).

```python
from celery import Celery

app = Celery('demo',
             broker='redis://localhost:6379/0',   # 메시지가 가는 곳
             backend='redis://localhost:6379/1')  # 결과가 적히는 곳

@app.task
def add(x, y):
    return x + y

r1 = add.delay(2, 3)                              # 인자만, 곧장 큐로
r2 = add.apply_async(args=[2, 3], countdown=5)    # 옵션과 함께
if r1.ready():
    print(r1.get())
```

규칙.

- 앱은 `Celery('이름', broker=..., backend=..., include=[모듈 이름들])` 으로 만든다.
- `include` 에는 워커가 불러올 태스크 모듈을 적는다 — 원본은 `include=['tasks']`.
- 설정은 `app.conf.update(...)` 로 한꺼번에 넣는다.
- 태스크는 `@app.task` 또는 `@app.task(옵션=...)` 로 만든다.
- `delay(*인자)` 는 인자만, `apply_async(args=[...], 옵션...)` 은 인자와 실행 옵션을 받는다.
- 주기적 태스크는 `app.conf.beat_schedule` 사전에 적고 `from celery.schedules import crontab` 으로 `crontab` 을 가져온다.

원본의 `app.conf.update` 설정값.

| 설정 | 원본 값 | 뜻 |
|---|---|---|
| `result_expires` | `3600` | 결과 만료 시간(초) — 1시간 뒤 결과가 지워진다 |
| `task_serializer` | `'json'` | 태스크 메시지를 JSON 으로 직렬화 |
| `accept_content` | `['json']` | JSON 메시지만 받는다 |
| `result_serializer` | `'json'` | 결과도 JSON 으로 저장 |
| `timezone` | `'Asia/Seoul'` | 시간대 |
| `enable_utc` | `True` | UTC 사용 |
| `task_track_started` | `True` | `STARTED` 상태 기록 |

> **직렬화** — 파이썬 값을 메시지로 보낼 수 있는 바이트 · 문자열로 바꾸는 것이다.\
> 예: `{'to': 'a@b.c'}` → JSON 문자열.

태스크 옵션과 호출 옵션.

| 어디에 | 옵션 | 원본 값 | 뜻 |
|---|---|---|---|
| `@app.task(...)` | `bind` | `True` | 첫 인자 `self` 로 태스크 인스턴스 접근 |
| `@app.task(...)` | `max_retries` | `3` | 재시도 한도 |
| `@app.task(...)` | `time_limit` | `300` | 실행 시간 제한(초, 5분) |
| `self.retry(...)` | `countdown` | `10` | 10초 뒤 재시도 |
| `apply_async(...)` | `countdown` | `60` | 60초 뒤 실행 |
| `apply_async(...)` | `expires` | `3600` | 1시간 뒤 만료 |
| `apply_async(...)` | `queue` | `'high-priority'` | 보낼 큐 이름 |

## 어디서 틀리나

### 1. 브로커 URL 과 백엔드 URL 을 헷갈린다

브로커는 「할 일」이 가는 길이고 백엔드는 「결과」가 적히는 곳이다.
둘을 혼동하면 결과 조회가 안 된다(원본 주석).
원본은 같은 Redis 의 `/0` 과 `/1` 로 나눠 두었다.

### 2. `include` 에 모듈을 빠뜨린다

`include` 에 없는 모듈의 태스크는 워커가 인식하지 못한다(원본 주석).
웹앱은 메시지를 잘 보내도, 그 메시지를 받은 워커가 「모르는 태스크」로 처리하지 못한다.

### 3. 웹 요청 안에서 `result.get()` 을 부른다

`get()` 은 블로킹 호출이라 웹 요청 안에서 쓰면 안 된다(원본 주석).
결과가 나올 때까지 요청이 멈춰, 백그라운드로 뺀 의미가 사라진다.
웹 요청에서는 ID 만 돌려주고, 상태는 `ready()` · `state` 로 나중에 확인한다.

### 4. `PENDING` 을 「큐에 들어갔다」로만 읽는다

원본 상태 목록은 `PENDING -> 큐에 전송됨 (아직 워커가 안 받음)` 이라 적는다.
그러나 정답 코드의 주석은 `PENDING` 이 「결과 백엔드에 정보 없음」을 뜻할 수도 있다고 경고한다.
원본의 주장 → 왜 의심스러운가: 백엔드는 정보가 없는 ID 를 따로 구별하지 않으므로, 큐에 있든 없든 「아직 기록 없음」이면 모두 `PENDING` 으로 보인다.
그래서 잘못 적은 ID 나 `result_expires`(3600초)가 지나 지워진 결과도 `PENDING` 으로 보일 수 있다(원본 주석에서 이어지는 추론).

### 5. `STARTED` 가 안 보인다

`STARTED` 는 `task_track_started=True` 일 때만 기록된다.
끄면 실행 중이어도 `PENDING` 으로 보인다.

### 6. Beat 를 둘 띄운다

Beat 는 별도 프로세스다.
두 개의 Beat 가 동시에 돌면 각자 시간표대로 발행하므로 태스크가 중복 발행된다(원본 주석).
Beat 는 하나만 띄운다.
반대로 Beat 를 안 띄우면 `beat_schedule` 에 적은 일은 하나도 발행되지 않는다 — 워커는 시간표를 보지 않는다.

### 7. `bind=True` 없이 `self.retry` 를 쓰려 한다

`self` 는 `bind=True` 일 때 첫 인자로 들어온다.
`bind` 가 없으면 함수 안에서 태스크 인스턴스에 닿을 길이 없어 재시도 · 로깅을 못 한다.

### 8. 시간표의 태스크 이름이 정의와 어긋난다

원본 `beat_schedule` 은 `tasks.health_check` 와 `tasks.cleanup_old_data` 를 부르지만, 원본 `tasks.py` 에는 이 둘이 정의되어 있지 않다.
원본의 주장 → 왜 의심스러운가: 시간표만 보면 세 일이 다 돌 것 같지만, 워커가 모르는 이름이면 실행되지 않는다(「어디서 틀리나 2」와 같은 원리).
`'task'` 값은 「모듈 이름.함수 이름」꼴이라 모듈 이름(`tasks`)이 바뀌어도 어긋난다.

### 9. `apply_async` 직후 바로 `ready()` 를 믿는다

원본은 `countdown=60` 으로 보낸 직후 `if result.ready():` 를 둔다.
워커는 60초 뒤에야 실행하므로 그 순간에는 끝났을 리 없다 — 그 `if` 블록은 그 시점에 건너뛰어진다.
`ready()` 는 기다려 주지 않는다는 점을 기억한다.

### 10. `apply()` 를 운영 코드에 쓴다

`apply()` 는 「테스트용 · 즉시 실행 후 결과 반환」이다(원본 주석).
지금 프로세스에서 끝날 때까지 실행하므로, 웹 요청에서 쓰면 오래 걸리는 일을 그대로 기다리게 된다.

## 구현 세부사항 대 언어 보장

이 주제는 Python 언어가 아니라 Celery 라이브러리의 동작이다.
「언어 보장」에 해당하는 것은 데코레이터 문법 정도다.

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `@app.task` 가 함수 위에서 그 함수를 감싼다 | Python 언어(데코레이터 문법) |
| `delay()` 는 `apply_async()` 의 단축 형태다 | Celery 라이브러리의 API |
| `bind=True` 면 첫 인자로 태스크 인스턴스가 들어온다 | Celery 라이브러리 |
| `get()` 은 블로킹, `result.result` 는 논블로킹 | Celery 라이브러리 |
| `PENDING` 이 「백엔드에 정보 없음」과 구별되지 않는다 | Celery 결과 백엔드의 동작(원본 주석) |
| `STARTED` 는 `task_track_started=True` 일 때만 기록 | Celery 설정 |
| `time_limit` 을 넘으면 태스크가 끊긴다 | Celery 워커 — 풀 종류에 따라 다를 수 있다(확인 필요) |
| `--concurrency` 는 프리포크 워커 수 | Celery 워커의 프리포크 풀(원본 주석 — 다른 풀이면 뜻이 다를 수 있다, 확인 필요) |
| Beat 를 둘 띄우면 중복 발행된다 | Celery 가 기본으로 막지 않는다는 원본 주석 |
| Redis 가 가장 간편한 브로커다 | 원본 팁의 판단 — 보장이 아니다 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 웹 요청 안에서 이메일 발송을 맡긴다 | `send_email.delay(...)` 후 ID 만 응답 | 요청 안에서 `result.get()` |
| 1분 뒤 · 특정 큐로 보내고 싶다 | `apply_async(countdown=..., queue=...)` | `delay` (옵션을 못 받는다) |
| 테스트에서 결과를 곧장 확인한다 | `apply(args=[...]).get()` | 운영 코드에서 `apply` |
| 일시적 실패가 날 수 있다 | `bind=True` + `self.retry(exc=..., countdown=...)` + `max_retries` | 무한히 다시 부르는 수동 반복 |
| 너무 오래 걸리면 끊고 싶다 | `@app.task(time_limit=...)` | 제한 없이 방치 |
| 평일 9시마다 보고서 | `beat_schedule` + `crontab` + Beat 하나 | Beat 여러 개 |
| 끝났는지 기다리지 않고 확인 | `ready()` · `state` | 루프 안의 `get()` |
| 태스크 흐름을 눈으로 보고 싶다 | Flower | 로그만 뒤지기 |
| 수 밀리초면 끝나는 일 | 그냥 함수 호출 | Celery 태스크(브로커 왕복이 오히려 짐이다 — 원본에 근거 없음, 추론) |

## 핵심 문장

1. **Celery 는 Producer → Broker → Worker → Backend 의 네 부품이다** — 할 일은 브로커로, 결과는 백엔드로 간다.
2. **`delay` · `apply_async` 는 기다리지 않고 `AsyncResult` 를 곧장 돌려준다** — 옵션이 필요하면 `apply_async`, 테스트에서 즉시 실행은 `apply`.
3. **`get()` 은 멈춰 기다린다** — 웹 요청 안에서는 쓰지 않는다.
4. **`PENDING` 은 「아직 기록 없음」이다** — 큐에 있다는 보장이 아니다.
5. **주기적 태스크는 `beat_schedule` + 별도의 Beat 프로세스 하나** — 실행은 여전히 워커가 한다.

## 관련 자료

- `concurrency-patterns` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- [fastapi-advanced](../04-fastapi-advanced/2-summary.md)
- 원본: study-site 항목 데이터 `data/python/libraries.json` 의 `celery-basics`

## 용어 풀이

- **태스크** — Celery 가 워커에서 대신 실행하는 함수.
- **프로듀서(Producer)** — 태스크 메시지를 만들어 브로커에 넣는 쪽(웹앱).
- **브로커(Broker)** — 태스크 메시지를 줄 세워 두는 저장소(Redis · RabbitMQ).
- **큐** — 먼저 들어온 메시지부터 꺼내 가는 줄.
- **워커(Worker)** — 브로커에서 메시지를 꺼내 태스크를 실행하는 프로세스.
- **결과 백엔드(Backend)** — 태스크의 상태와 반환값을 적어 두는 저장소.
- **데코레이터** — `@이름` 으로 함수를 감싸 바꾸는 Python 문법.
- **`bind=True`** — 태스크 함수의 첫 인자 `self` 로 태스크 인스턴스를 받게 하는 옵션.
- **재시도(`self.retry`)** — 실패한 태스크를 일정 시간 뒤 다시 실행하게 하는 호출.
- **`AsyncResult`** — 태스크 ID 로 상태와 결과를 조회하는 객체.
- **UUID** — 겹치지 않게 만든 128비트 식별자.
- **블로킹** — 결과가 나올 때까지 호출한 쪽이 멈추는 것.
- **동기 호출** — 끝날 때까지 기다린 뒤 다음 줄로 넘어가는 호출.
- **직렬화** — 파이썬 값을 보낼 수 있는 문자열 · 바이트로 바꾸는 것.
- **crontab** — 분 · 시 · 요일 칸으로 시각을 적는 일정 표기.
- **Celery Beat** — 시간표대로 태스크 메시지를 발행하는 스케줄러 프로세스.
- **프리포크** — 자식 프로세스를 미리 만들어 태스크를 나눠 맡기는 워커 방식.
- **Flower** — Celery 태스크를 웹 화면으로 보여 주는 모니터링 도구.
- **CPU-bound** — 계산 때문에 오래 걸리는 작업.
- **I/O-bound** — 바깥 응답을 기다리느라 오래 걸리는 작업.

## 더 들어가면

- JSON 직렬화를 거치면 튜플이 리스트로 바뀌어 돌아오는 등, 파이썬 타입이 그대로 보존되지 않을 수 있다(확인 필요).
- 같은 태스크가 두 번 실행되어도 결과가 같도록(멱등하게) 짜 두면 재시도 · 중복 발행에 안전하다(확인 필요).
- `acks_late` 설정은 워커가 태스크를 끝낸 뒤에 메시지 수신을 확인하게 해, 워커가 죽었을 때 메시지를 잃지 않게 돕는다고 알려져 있다(확인 필요).
- `max_retries` 를 다 쓰면 `self.retry` 가 더 미루지 않고 예외를 올려 태스크가 `FAILURE` 가 된다고 알려져 있다(확인 필요).
- 테스트에서는 `task_always_eager` 같은 설정으로 `delay` 도 즉시 실행되게 할 수 있다(확인 필요).
- 여러 태스크를 잇거나 묶는 `chain` · `group` · `chord` 같은 도구가 있다(확인 필요).
- 취소는 `AsyncResult` 의 `revoke()` 로 하며, 그때 상태가 `REVOKED` 가 된다(확인 필요).
- Windows 에서는 프리포크 풀이 잘 맞지 않아 다른 풀을 고른다는 말이 있다(확인 필요).
