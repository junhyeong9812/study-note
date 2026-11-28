# python/python-web-deep/07 — Django + Celery 비동기 태스크 — 정리 (힌트)

> 출처 — study-site 항목 `python/django-celery`(항목 데이터 `data/python/django-flask-deep.json`) · 정답 코드 study-practice `python/python-web-deep/reference/django-celery.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 원본 예제를 `Python 3.12.3` 에서 2회 돌렸다.

## 한눈에 — 쉽게 말하면

**Celery 는 「식당의 주문표 꽂이와 주방」이다.**
홀 직원(Django 뷰)은 주문을 받으면 요리가 끝날 때까지 손님 앞에 서 있지 않는다.
주문표를 꽂이에 꽂고 손님에게 「접수됐습니다」라고 바로 말한 뒤 다음 손님을 받는다.
주방(worker)은 꽂이에서 주문표를 하나씩 빼 요리를 하고, 다 되면 완성 칸에 올려 둔다.
벽시계를 보고 「매일 3시에 냉장고 정리」 같은 정기 주문표를 꽂아 주는 매니저(beat)도 따로 있다.
Django + Celery 도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 주문표 | 태스크 메시지(함수 이름 + 인자) |
| 주문표 꽂이 | 브로커(Redis · RabbitMQ) |
| 홀 직원 | Django 뷰 — `.delay()` 를 부르는 쪽 |
| 「접수됐습니다」 영수증 | `.delay()` 가 바로 돌려주는 결과 객체(`AsyncResult`) |
| 주방 | worker 프로세스 |
| 완성 칸 | 결과 저장소(result backend) |
| 정기 주문을 꽂는 매니저 | beat 프로세스 |

```text
 [Django 뷰] --.delay()--> [브로커: 큐] --꺼냄--> [worker] --결과--> [결과 저장소]
      |                         ^
      | 즉시 응답                |
      v                     [beat: 정해진 시각마다 태스크를 넣음]
   [사용자]
```

## 이 주제가 답하려는 질문

1. 시간이 걸리는 일을 요청 처리 흐름에서 떼어 내 「나중에, 다른 곳에서」 돌리려면 무엇이 필요한가?
2. `.delay()` 를 부르는 순간과 태스크가 실제로 끝나는 순간 사이에 무슨 일이 일어나고, 결과는 어떻게 받는가?
3. 정해진 시각마다 도는 일, 실패하면 다시 해야 하는 일, 여러 태스크를 잇거나 동시에 돌리는 일은 어떻게 표현하는가?
4. 실제로 띄우려면 어떤 설정과 프로세스가 필요한가?

## 동작 방식

이 항목의 예제는 진짜 Celery 가 아니라 **Celery 의 핵심 동작을 흉내 낸 시뮬레이터**(`CelerySimulator`)로 1절을 돌리고, 2~6절은 진짜 Celery 코드를 문자열로 보여 준다.
시뮬레이터는 브로커와 별도 worker 프로세스 대신 같은 프로세스 안의 스레드 풀(`ThreadPoolExecutor(max_workers=4)`)을 쓴다.

> **ThreadPoolExecutor** — 일꾼 스레드 몇 개를 미리 두고, 제출된 함수를 빈 일꾼이 맡아 실행하게 하는 표준 라이브러리 도구.\
> 예: `executor.submit(run)` 은 `run` 을 풀에 맡기고 곧바로 돌아온다.

### (1) `@app.task()` — 함수에 `.delay` 를 붙인다

**언제 쓰나** — 어떤 함수를 「백그라운드로 돌릴 수 있는 태스크」로 등록할 때 쓴다.
진짜 Celery 에서는 `@shared_task` 를 쓴다.

```text
@app.task()                     decorator(func) 가 실행된다
def send_email(...): ...   →    1. task_name = 'send_email'
                                2. delay 함수를 새로 만든다 (@wraps 로 이름 보존)
                                3. func.delay = delay, func.apply_async = delay
                                4. app.tasks['send_email'] = func
                                5. func 를 그대로 돌려준다
                           →    send_email(...)        : 지금 여기서 바로 실행
                                send_email.delay(...)  : 큐에 넣고 바로 반환
```

- 데코레이터는 원래 함수를 바꿔치기하지 않고 그대로 돌려준다.
- 대신 함수 객체에 `delay` 와 `apply_async` 라는 속성을 붙인다 — 시뮬레이터에서는 둘이 같은 함수다.
- `app.tasks` 는 등록된 태스크의 카탈로그다.
- `bind` · `max_retries` · `default_retry_delay` 인자는 진짜 Celery 의 꼴을 흉내 내려고 받기만 하고, 시뮬레이터 안에서는 쓰지 않는다.

> **데코레이터** — 함수 정의 위에 `@이름` 으로 붙여, 정의된 함수를 받아 가공한 결과를 그 이름에 묶는 문법.\
> 예: `@app.task()` 는 `send_email = app.task()(send_email)` 과 같다.

> **`@wraps`** — 감싼 함수에 원래 함수의 이름 · 문서 문자열 같은 정보를 옮겨 주는 `functools` 의 데코레이터.\
> 예: `delay.__name__` 이 `'send_email'` 이 된다.

### (2) `.delay()` — 큐에 넣고 즉시 돌아온다

**언제 쓰나** — 결과를 기다리지 않고 일을 맡기기만 할 때 쓴다.

```text
send_email.delay('user@example.com', '주문 확인', '...')
  → _task_counter += 1, task_id = 'task-1'
  → TaskResult('task-1') 생성 (status='PENDING', result=None), results 에 등록
  → run 함수를 만들어 executor.submit(run)   ← 여기서 기다리지 않는다
  → "  [Celery] 태스크 큐에 추가: send_email (id=task-1)" 을 찍는다
  → TaskResult 객체를 돌려준다
```

- 번호를 하나 올려 `task-1`, `task-2`… 꼴의 id 를 만든다.
- 상태가 `PENDING` 인 결과 객체를 먼저 만든다.
- 실제 일을 할 `run` 을 풀에 제출하고, 끝나기를 기다리지 않는다.
- 그래서 「큐에 추가」 줄이 찍히고 결과 객체가 곧장 호출자에게 돌아온다.
- 진짜 Celery 에서는 이 자리에서 함수 이름과 인자를 **직렬화해 브로커(Redis · RabbitMQ)로 보낸다**.

> **직렬화** — 메모리 속 값을 전송 · 저장할 수 있는 바이트나 문자열로 바꾸는 일.\
> 예: 딕셔너리 `{'to': 'a@b.c'}` 를 JSON 문자열로 바꾼다.

> **브로커** — 태스크 메시지를 받아 두었다가 worker 에게 넘겨 주는 중간 저장소(메시지 큐).\
> 예: `CELERY_BROKER_URL = 'redis://localhost:6379/0'`.

### (3) worker 가 꺼내 실행하고 상태를 바꾼다

**언제 쓰나** — 태스크가 어디까지 왔는지(대기 · 실행 중 · 성공 · 실패) 알아야 할 때 이 흐름을 본다.

```text
(일꾼 스레드에서)
run()
  → result.status = 'STARTED'
  → result.result = func(*args, **kwargs)      성공하면
       result.status = 'SUCCESS'
  → except Exception as e:                      예외가 나면
       result.result = str(e)
       result.status = 'FAILURE'
```

- 풀의 빈 일꾼이 `run` 을 맡으면 먼저 상태를 `STARTED` 로 바꾼다.
- 원래 함수를 실행하고, 돌려준 값을 `result.result` 에 넣고 `SUCCESS` 로 바꾼다.
- 예외가 나면 예외 메시지 문자열을 `result.result` 에 넣고 `FAILURE` 로 바꾼다 — 예외는 여기서 잡히므로 호출한 쪽으로 퍼지지 않는다.
- 재시도는 이 시뮬레이터에 없다(원본 주석: 「재시도는 별도 로직」).
- 호출자가 가진 결과 객체와 `run` 이 고치는 결과 객체는 **같은 객체**라, 호출자는 나중에 상태가 바뀐 것을 볼 수 있다.
- 세 태스크는 일꾼 넷짜리 풀에서 **동시에** 돌므로, 누가 먼저 끝날지는 스레드가 언제 돌아가느냐에 달려 있다.

> **`AsyncResult`** — 진짜 Celery 에서 `.delay()` 가 돌려주는 「아직 안 끝났을 수 있는 결과」의 손잡이 객체. 시뮬레이터의 `TaskResult` 가 이것에 대응한다.\
> 예: `result.status` 가 `'PENDING'` → `'STARTED'` → `'SUCCESS'` 로 바뀐다.

### (4) 결과를 기다리기

**언제 쓰나** — 맡긴 일의 결과값이 실제로 필요할 때 쓴다.

```text
result1 = send_email.delay(...)     ← 즉시 반환, 아직 PENDING/STARTED
time.sleep(0.3)                     ← 시뮬레이터: 넉넉히 기다린다고 「가정」
print(result1.status, result1.result)

(진짜 Celery)
result1.get()        ← 끝날 때까지 기다려 값을 받는다
또는 상태를 주기적으로 물어본다(폴링)
```

- 각 태스크는 `time.sleep(0.1)` 만큼 걸리고, 메인은 `time.sleep(0.3)` 동안 기다린 뒤 결과를 찍는다.
- 이 대기는 시뮬레이션을 위한 것이다 — 0.3초 안에 끝난다는 보장은 없다.
- 원본 주석은 진짜 환경에서는 `.get()` 으로 기다리거나 폴링한다고 적는다.
- 진짜 Celery 에서 결과는 결과 저장소(`CELERY_RESULT_BACKEND`)에 쌓이고, `AsyncResult` 는 그곳을 들여다본다.

### (5) Django 뷰에 끼우기 — 동기와 비동기를 나눈다

**언제 쓰나** — 응답을 빨리 돌려줘야 하는 요청 안에 느린 부수 작업이 섞여 있을 때 쓴다.

```text
place_order(request)
  → Order.objects.create(...)       동기: 응답에 꼭 필요한 일 (주문 번호)
  → send_email.delay(...)           비동기: 부수효과 — 큐에만 넣는다
  → JsonResponse({'order_id': ..., 'status': 'created'})   곧장 응답
```

- 주문 생성은 응답에 주문 번호가 들어가야 하므로 그 자리에서 끝낸다.
- 확인 메일은 사용자가 응답을 받는 데 필요 없으므로 큐에 넣고 넘어간다.
- 원본 주석의 원칙: **응답 속도가 중요한 동작은 동기, 부수효과는 비동기로 분리한다.**
- 원본 팁이 꼽는 비동기 후보: 이메일 전송(I/O 바운드의 전형), 이미지 처리(원본 주석은 CPU 바운드로 분류), 리포트 생성(오래 걸리는 집계).

### (6) beat — 주기적 태스크

**언제 쓰나** — 「매일 3시」「5분마다」처럼 시간표대로 돌아야 하는 일에 쓴다.

```text
[beat 프로세스]  시계를 보다가 시각이 되면
     → 'myapp.tasks.cleanup_sessions' 태스크를 브로커에 넣는다
     → [worker] 가 꺼내 실행한다
```

- beat 는 cron 같은 스케줄러이고 **별도 프로세스로** 돈다.
- beat 자신은 태스크를 실행하지 않고, 정해진 때에 태스크 메시지를 큐에 넣을 뿐이다 — 실행은 worker 몫이다.
- 시간표는 `app.conf.beat_schedule` 딕셔너리에 적는다(문법 절 참고).

### (7) 재시도와 `acks_late`

**언제 쓰나** — 외부 서비스 호출처럼 일시적으로 실패할 수 있는 일, 또는 worker 가 죽어도 잃으면 안 되는 일에 쓴다.

```text
@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_webhook(self, url, data):
    요청 실패 (RequestException)
      → self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
           retries=0 → 60초 뒤, 1 → 120초 뒤, 2 → 180초 뒤 다시 실행
      → 최대 횟수를 넘으면 MaxRetriesExceededError 를 잡아 실패를 기록

@shared_task(bind=True, acks_late=True)
  → 작업이 「끝난 뒤에」 ACK
  → worker 가 중간에 죽으면 ACK 가 없으므로 다시 실행된다
```

- `bind=True` 면 태스크 함수의 첫 인자로 `self`(태스크 인스턴스)가 들어온다.
- 그래서 `self.retry()` 를 부를 수 있고, `self.request.retries` 로 지금까지 재시도한 횟수를 읽을 수 있다.
- 예제의 `countdown` 식은 재시도할수록 기다리는 시간을 늘린다.
- `acks_late=True` 는 작업 완료 후에야 ACK 를 보낸다 — 원본 주석은 이를 at-least-once(적어도 한 번) 보장이라 부른다.
- 「적어도 한 번」이므로 같은 태스크가 두 번 돌 수도 있다 — 두 번 돌아도 결과가 같도록 짜야 안전하다.

> **ACK** — 「이 메시지 처리했다」고 브로커에 알리는 확인 신호. ACK 를 받은 메시지는 큐에서 지워진다.\
> 예: `acks_late=True` 면 함수가 끝난 뒤에 ACK 를 보낸다.

### (8) Canvas — 태스크 조합

**언제 쓰나** — 여러 태스크를 순서대로 잇거나, 한꺼번에 돌리거나, 한꺼번에 돌린 뒤 합칠 때 쓴다.

```text
chain(A.s(url), B.s(), C.s())     A → B → C   순차
group(send_email.s(e) for e ...)  A | A | A   병렬
chord([P.s(c) for c ...], M.s())  (P | P | P) → M   병렬 후 콜백
```

- `.s()` 는 「이 태스크를 이 인자로 부를 것」이라는 서명(시그니처)을 만든다 — 바로 실행하지 않는다.
- `chain` 은 순차 실행, `group` 은 병렬 실행, `chord` 는 그룹이 전부 끝난 뒤 콜백을 부른다.
- 조합한 결과에 `.apply_async()` 를 불러야 큐에 들어간다.

> **시그니처(`.s()`)** — 태스크와 인자를 묶어 둔, 아직 실행하지 않은 호출 설명서.\
> 예: `send_email.s(email)`.

### (9) 실제 구성 — 설정과 세 프로세스

**언제 쓰나** — 시뮬레이터가 아니라 진짜 Celery 를 Django 와 함께 띄울 때 쓴다.

```text
Django 프로세스 ──메시지──> Redis db0 (브로커) ──> celery worker
                                                     │결과
celery beat ──정기 메시지──> Redis db0              Redis db1 (결과 저장소)
celery flower ── 상태를 보여 주는 웹 화면
```

- `celery.py` 에서 `Celery('myproject')` 앱을 만들고 `config_from_object('django.conf:settings', namespace='CELERY')` 로 Django 설정을 읽는다.
- `namespace='CELERY'` 때문에 설정 이름이 `CELERY_` 로 시작한다.
- `autodiscover_tasks()` 는 각 앱의 태스크를 찾아 등록한다.
- 원본 주석: Redis 는 가볍고 가장 흔한(권장) 브로커, RabbitMQ 는 견고한 메시지 큐다.
- worker · beat · flower 는 각각 따로 띄우는 명령이다.

## 문법 — 형태와 규칙

```python
# tasks.py
from celery import shared_task

@shared_task
def send_email(to, subject, body):
    ...                                  # 느린 일
    return {'sent': True, 'to': to}

# views.py
def place_order(request):
    order = Order.objects.create(...)            # 동기
    send_email.delay(request.user.email, '주문 확인', '...')  # 비동기
    return JsonResponse({'order_id': order.id})
```

- `.delay(*args, **kwargs)` — 태스크를 큐에 넣고 `AsyncResult` 를 즉시 돌려준다.
- 태스크 함수를 그냥 부르면(`send_email(...)`) 큐를 거치지 않고 그 자리에서 실행된다(시뮬레이터 기준. 진짜 Celery 도 같다고 알려져 있다 — 확인 필요).
- `bind=True` 면 첫 매개변수가 `self` 다.

**beat 시간표 (`app.conf.beat_schedule`)**

| 항목 이름 | `task` | `schedule` | 뜻 |
|---|---|---|---|
| `cleanup-expired-sessions` | `myapp.tasks.cleanup_sessions` | `crontab(hour=3, minute=0)` | 매일 3시 0분 |
| `send-daily-report` | `myapp.tasks.send_daily_report` | `crontab(hour=9, minute=0, day_of_week='mon-fri')` | 평일 9시 0분 |
| `update-exchange-rates` | `myapp.tasks.update_rates` | `300.0` | 300초(5분)마다 |
| `weekly-backup` | `myapp.tasks.backup_database` | `crontab(hour=2, minute=0, day_of_week='sunday')` | 일요일 2시 0분 |

- `task` 에는 함수 객체가 아니라 **점으로 이은 이름 문자열**을 적는다.
- `schedule` 에는 `crontab(...)`(달력 기준) 또는 숫자(초 간격)를 적는다.

**설정 (`settings.py`)**

| 설정 | 예제 값 | 뜻 |
|---|---|---|
| `CELERY_BROKER_URL` | `redis://localhost:6379/0` | 메시지 브로커 |
| `CELERY_RESULT_BACKEND` | `redis://localhost:6379/1` | 결과 저장소 |
| `CELERY_ACCEPT_CONTENT` | `['json']` | 받아들일 메시지 형식 |
| `CELERY_TASK_SERIALIZER` | `'json'` | 태스크 인자를 직렬화할 형식 |
| `CELERY_RESULT_SERIALIZER` | `'json'` | 결과를 직렬화할 형식 |
| `CELERY_TIMEZONE` | `'Asia/Seoul'` | 시간대 |
| `CELERY_TASK_TRACK_STARTED` | `True` | 시작(`STARTED`) 상태도 기록 (확인 필요) |
| `CELERY_TASK_TIME_LIMIT` | `300` | 태스크 실행 시간 제한(5분) |

**실행 명령**

```bash
celery -A myproject worker -l info   # 태스크를 실행하는 worker
celery -A myproject beat -l info     # 주기적 태스크를 넣는 스케줄러
celery -A myproject flower           # 웹 기반 모니터링 UI
```

## 어디서 틀리나

### 1. `.delay()` 직후에 결과가 있다고 믿는다

`.delay()` 는 큐에 넣고 곧장 돌아온다.
돌아온 직후의 상태는 `PENDING` 이거나, 일꾼이 막 잡았다면 `STARTED` 이고, `result` 는 아직 `None` 이다.
결과값이 필요하면 기다려야 한다.

### 2. `time.sleep(0.3)` 을 기다리는 방법으로 베낀다

예제의 `sleep` 은 시뮬레이션을 위한 「아마 이쯤이면 끝났겠지」다.
태스크가 더 오래 걸리면 `PENDING`/`STARTED` 인 채로 찍힌다.
진짜로는 `.get()` 으로 기다리거나 폴링한다 — 원본 주석이 그렇게 적는다.

### 3. 완료 순서를 믿는다

세 태스크는 풀 안에서 동시에 돈다.
실행 결과에서 메일 → 이미지 → 리포트 순서로 끝났어도, 그것은 그때 스레드가 그렇게 돌았을 뿐 약속된 순서가 아니다.
순서가 중요하면 `chain` 으로 이어야 한다.

### 4. 시뮬레이터가 재시도까지 해 준다고 생각한다

시뮬레이터의 `task()` 는 `bind` · `max_retries` · `default_retry_delay` 를 받기만 한다.
`bind=True` 를 줘도 함수에 `self` 가 들어가지 않고, 예외가 나면 `FAILURE` 로 끝날 뿐 다시 돌지 않는다.
`apply_async` 도 `delay` 와 같은 함수를 붙여 둔 것일 뿐이다.

### 5. 아무 값이나 인자로 넘긴다

시뮬레이터는 같은 프로세스 안에서 인자를 메모리 참조 그대로 넘기므로 무엇이든 넘어간다.
진짜 Celery 는 인자를 직렬화해 브로커로 보내고, 예제 설정은 `json` 을 쓴다.
JSON 으로 바꿀 수 없는 값(예: Django 모델 객체)은 그대로 못 넘긴다 — 대신 id 같은 단순 값을 넘기고 worker 에서 다시 조회한다.

### 6. 재시도 예제를 그대로 믿는다

- 원본의 주장: `self.retry(...)` 를 `try` 로 감싸고 `except MaxRetriesExceededError` 로 최대 재시도 초과를 잡는다.
- 왜 의심스러운가: `retry` 에 `exc=` 를 넘기면, 최대 횟수를 넘었을 때 `MaxRetriesExceededError` 대신 넘긴 원래 예외를 다시 던진다고 알려져 있다 — 그러면 그 `except` 절이 잡지 못한다 (확인 필요).
- 또 `retry` 는 호출 자체가 예외를 던져 흐름을 끊는 방식이라, 관례로 `raise self.retry(...)` 라고 쓴다 (확인 필요).
- 예제의 `countdown` 은 `default_retry_delay=60` 보다 우선하므로, 실제 대기 시간은 60 · 120 · 180초가 된다.

### 7. `acks_late` 태스크가 정확히 한 번 돈다고 생각한다

완료 후 ACK 이므로, 일은 끝냈는데 ACK 직전에 worker 가 죽으면 같은 태스크가 다시 돈다.
「적어도 한 번」이지 「정확히 한 번」이 아니다.
두 번 돌아도 해가 없게(예: 이미 처리했으면 건너뛰게) 짠다.

### 8. 시뮬레이터 코드의 군더더기

- `Any` · `datetime` · `timedelta` · `threading` 은 가져오기만 하고 쓰지 않는다.
- `threading` 옆 주석은 「스레드 안전성」이지만 잠금(`Lock`)은 없다.
- `_task_counter += 1` 은 메인 스레드 하나에서만 `delay` 를 부르니 문제없지만, 여러 스레드가 동시에 부르면 번호가 겹칠 수 있다.
- `process_image` 주석은 「CPU 집약적」이지만 본문은 `time.sleep` 이라 실제로 CPU 를 쓰지 않는다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `.delay()` 가 기다리지 않고 바로 돌아온다 | Celery 라이브러리의 동작. 시뮬레이터에서는 `ThreadPoolExecutor.submit` 이 바로 돌아오기 때문 |
| `@wraps` 가 원래 함수 이름을 옮긴다 | Python 표준 라이브러리 `functools` 가 보장 |
| 세 태스크가 메일 → 이미지 → 리포트 순으로 끝난다 | 아무도 보장하지 않음 — 그때의 스레드 스케줄링 결과 |
| `sleep(0.3)` 이면 모두 끝나 있다 | 아무도 보장하지 않음 — 시뮬레이션의 가정 |
| `acks_late=True` 면 worker 중단 시 재실행된다 | Celery 설정과 브로커의 메시지 재전달 동작(브로커 · 설정에 따라 다를 수 있음 — 확인 필요) |
| 인자는 JSON 으로 바꿀 수 있어야 한다 | 이 예제의 설정(`CELERY_TASK_SERIALIZER='json'`)이 정한 것 |
| Redis 가 가장 흔한 브로커다 | 관행 · 원본의 판단. 라이브러리 보장 아님 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 주문 후 확인 메일 | 뷰에서 `send_email.delay(...)` | 뷰 안에서 메일 전송을 끝까지 기다리기 |
| 업로드 이미지 리사이징 · 월간 리포트 | 태스크 + `.delay()` | 요청 처리 중 동기 실행 |
| 매일 정해진 시각의 정리 · 백업 | beat + `crontab` | 서버 안에서 직접 짠 반복문 타이머 |
| 일시적으로 실패하는 외부 호출(웹훅) | `bind=True` + `self.retry()` | 실패 한 번에 포기 |
| 잃으면 안 되는 작업 | `acks_late=True` + 두 번 돌아도 안전한 코드 | 두 번 돌면 망가지는 코드에 `acks_late` |
| A 다음 B 다음 C | `chain` | `.delay()` 셋을 연달아 부르고 순서를 기대하기 |
| 같은 일 여러 개를 한꺼번에 · 다 끝나면 합치기 | `group` · `chord` | 하나씩 `.get()` 으로 기다리기 |
| 응답에 바로 필요한 값(주문 번호) | 동기로 처리 | 비동기로 미루기 |

## 핵심 문장

1. **`.delay()` 는 「맡기기」다** — 태스크를 큐에 넣고 결과 손잡이(`AsyncResult`)를 즉시 돌려줄 뿐, 일이 끝났다는 뜻이 아니다.
2. **실행은 worker, 시간표는 beat** — 둘 다 Django 와 별도 프로세스이고, 그 사이를 브로커(Redis 가 흔함)가 잇는다.
3. **응답에 필요한 일은 동기, 부수효과는 비동기** — 뷰는 주문을 만들고 메일은 큐에 넣는다.
4. **실패와 중단에 대비한다** — `bind=True` + `self.retry()` 로 재시도, `acks_late` 로 중단 시 재실행(그래서 두 번 돌아도 안전하게).
5. **여러 태스크는 Canvas 로 조합한다** — `chain` 순차, `group` 병렬, `chord` 병렬 후 콜백.

## 관련 자료

- [django-signals](../02-django-signals/2-summary.md)
- `django-cache` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `django-websocket` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/python/django-flask-deep.json` 의 `django-celery`

## 용어 풀이

- **Celery** — Python 의 분산 태스크 큐 라이브러리. 함수를 메시지로 보내 다른 프로세스에서 실행하게 한다.
- **태스크** — Celery 에 등록되어 큐를 거쳐 실행될 수 있는 함수.
- **큐** — 먼저 들어온 메시지부터 꺼내 처리하는 대기열.
- **브로커** — 태스크 메시지를 맡아 두고 worker 에게 넘기는 중간 저장소(Redis · RabbitMQ).
- **worker** — 브로커에서 태스크를 꺼내 실제로 실행하는 프로세스.
- **beat** — 정해진 시간표대로 태스크를 큐에 넣는 스케줄러 프로세스.
- **결과 저장소(result backend)** — 태스크의 상태와 반환값을 보관하는 곳.
- **`AsyncResult`** — `.delay()` 가 돌려주는, 나중에 결과를 확인하는 손잡이 객체.
- **`crontab`** — 분 · 시 · 요일 등으로 반복 시각을 적는 스케줄 표현.
- **ACK** — 메시지 처리를 마쳤다고 브로커에 알리는 확인 신호.
- **at-least-once** — 메시지가 적어도 한 번은 처리되지만 두 번 이상 처리될 수도 있는 전달 방식.
- **직렬화** — 값을 전송 · 저장 가능한 문자열이나 바이트로 바꾸는 일.
- **시그니처(`.s()`)** — 태스크와 인자를 묶어 둔, 아직 실행하지 않은 호출.
- **`chain` / `group` / `chord`** — 순차 / 병렬 / 병렬 후 콜백으로 태스크를 조합하는 Canvas 도구.
- **Flower** — Celery 의 웹 기반 모니터링 UI.
- **`ThreadPoolExecutor`** — 정해진 수의 스레드로 제출된 함수를 실행하는 표준 라이브러리 도구.
- **데코레이터** — 함수 정의를 받아 가공하는 `@` 문법.
- **I/O 바운드 / CPU 바운드** — 기다림(네트워크 · 디스크)이 대부분인 일 / 계산이 대부분인 일.

## 더 들어가면

- `chain` 에서 앞 태스크의 반환값은 다음 시그니처의 첫 인자로 넘어간다고 알려져 있다 — 그래서 `process_data.s()` 가 인자 없이 쓰인다 (확인 필요).
- `apply_async` 는 `delay` 와 달리 `countdown` · `eta` · `queue` 같은 실행 옵션을 받을 수 있다 (확인 필요).
- `CELERY_TASK_TRACK_STARTED` 를 켜지 않으면 진짜 Celery 는 `STARTED` 상태를 기록하지 않고 `PENDING` 에서 곧바로 `SUCCESS` 로 보인다고 알려져 있다 (확인 필요).
- 결과 저장소에 없는 아무 id 의 상태를 물어도 `PENDING` 이 나온다고 알려져 있다 — 「모름」과 「대기 중」이 구별되지 않는다 (확인 필요).
- beat 를 두 개 이상 띄우면 같은 주기 태스크가 중복으로 들어갈 수 있으므로 보통 하나만 띄운다 (확인 필요).
- Redis 브로커와 `acks_late` 를 함께 쓸 때는 ACK 되지 않은 메시지를 다시 내주기까지의 시간 제한(visibility timeout)이 오래 걸리는 태스크보다 짧으면 중복 실행이 생길 수 있다 (확인 필요).
- 시뮬레이터처럼 스레드로 CPU 바운드 일을 돌리면 CPython 의 GIL 때문에 병렬로 빨라지지 않는다 — 진짜 Celery worker 는 기본적으로 여러 프로세스를 쓴다 (확인 필요).
- `CELERY_TIMEZONE` 이 `'Asia/Seoul'` 이면 `crontab(hour=3)` 의 3시는 서울 시각으로 해석된다 (확인 필요).
