# python/python-libraries/15 — Celery 기본 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 기다리지 않고 곧장 돌아오며, 상태는 대개 `PENDING` 이다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

- `delay` 줄은 2초를 기다리지 않는다.
- 태스크 메시지를 브로커에 넣고 곧장 `AsyncResult` 를 돌려준다.
- `result.id` 는 UUID 문자열이다.
- 곧장 찍은 `result.state` 는 대개 `PENDING` 이다 — 워커가 아직 받지 않았거나, 백엔드에 아직 기록이 없기 때문이다.
- 다만 타이밍에 따라 워커가 이미 잡았다면 `STARTED`(원본 설정은 `task_track_started=True`)가 보일 수도 있다.

**왜 그런가**

`delay()` 는 `apply_async()` 의 단축 형태로, 즉시 큐에 보내고 결과 객체를 돌려준다.
함수 본문은 다른 프로세스(워커)가 나중에 실행한다.
근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (3)」 · 「동작 방식 (4)」.

### 2. 그 순간에는 아무것도 찍히지 않고, 나중에는 발송 결과 사전이 나온다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

- 이어 돌리면 `result.ready()` 가 `False` 라서 `if` 블록이 건너뛰어진다 — 아무것도 찍히지 않는다.
- 70초쯤 뒤 발송이 성공했다면 `ready()` 가 `True` 가 되고 `result.get()` 은 `{'status': 'sent', 'to': 'user@example.com'}` 을 돌려준다.

**왜 그런가**

`countdown=60` 은 워커가 60초 뒤에 실행하라는 뜻이다.
`ready()` 는 기다려 주지 않고 지금 끝났는지만 알려 준다.
`send_email` 은 2초 잠든 뒤 `{'status': 'sent', 'to': to}` 를 돌려주므로, 60초 대기 + 2초 실행이 지나면 결과가 있다.
근거: 2-summary 「동작 방식 (2)」 · 「동작 방식 (3)」 · 「동작 방식 (4)」 · 「어디서 틀리나 9」.

### 3. `{'processed': [2, 4, 6], 'count': 3}`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

`{'processed': [2, 4, 6], 'count': 3}` 을 받는다.

**왜 그런가**

`process_data` 는 각 원소를 두 배로 만든 리스트를 `processed` 에, 그 길이를 `count` 에 담아 돌려준다.
`get()` 은 끝난 결과를 백엔드에서 꺼내 준다.
근거: 2-summary 「동작 방식 (2)」의 태스크 목록 · 「동작 방식 (4)」.

### 4. 열 줄, 빈 줄 둘, 띄우는 프로세스는 세 종류

**출력**

```text
=== 실행 명령어 ===
# 워커 실행
celery -A celery_app worker --loglevel=info --concurrency=4

# Beat 스케줄러 실행
celery -A celery_app beat --loglevel=info

# 모니터링 (Flower)
pip install flower
celery -A celery_app flower --port=5555
```

**왜 그런가**

- `print("")` 는 빈 줄 한 줄을 찍는다 — 그래서 워커 묶음 뒤와 Beat 묶음 뒤에 빈 줄이 하나씩, 모두 두 개다.
- 전체는 머리글 포함 열 줄이다.
- 계속 떠 있는 프로세스는 `worker` · `beat` · `flower` 세 종류다.
- `pip install flower` 는 설치 명령이지 띄우는 명령이 아니다.

근거: 2-summary 「동작 방식 (6)」.

### 5. `self.retry` 로 재시도하려면 태스크 인스턴스가 필요하다

`bind=True` 를 주면 Celery 가 첫 인자 `self` 에 태스크 인스턴스를 넣어 준다.
`send_email` 은 예외가 나면 `raise self.retry(exc=exc, countdown=10)` 로 10초 뒤 재시도하는데, 이 호출에 `self` 가 필요하다.
`max_retries=3` 과 함께 「실패하면 최대 3번 다시」를 만든다.
같은 `self` 로 로깅 같은 기능도 쓸 수 있다(원본 팁).
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 7」.

### 6. `get()` 은 결과가 나올 때까지 멈추는 블로킹 호출이다

`get()` 을 웹 요청 안에서 부르면 요청이 태스크가 끝날 때까지 멈춘다.
오래 걸리는 일을 웹 요청 밖으로 빼려고 Celery 를 썼는데, 결국 그 시간을 그대로 기다리게 된다.
웹 요청에서는 태스크 ID 만 돌려주고, 상태는 나중에 `ready()` · `state` 로 기다리지 않고 확인한다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 3」.

### 7. 믿으면 안 된다 — `PENDING` 은 「아직 기록 없음」이다

- `PENDING` 은 원본 상태 목록처럼 「큐에 전송됨」일 수도 있지만, 「결과 백엔드에 정보 없음」을 뜻할 수도 있다.
- 백엔드는 둘을 구별하지 않으므로, 잘못 적은 ID 나 `result_expires` 가 지나 지워진 결과도 `PENDING` 으로 보일 수 있다(원본에 근거 없음 — 추론, 원본 주석에서 이어짐).
- `task_track_started` 를 켜지 않으면 `STARTED` 가 기록되지 않아, 실행 중인 태스크도 `PENDING` 으로 보인다.

근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 4」 · 「어디서 틀리나 5」.

### 8. 둘이면 하루에 두 번, 없으면 한 번도 발행되지 않는다

- Beat 둘은 각자 시간표대로 평일 9시에 `daily-report` 를 발행하므로 하루에 두 번 발행된다 — 중복 발행이다.
- Beat 를 안 띄우면 `beat_schedule` 의 일은 발행되지 않는다.
- 워커는 시간표를 보지 않고, 시간표를 보고 메시지를 넣는 일은 별도 프로세스인 Beat 만 한다.

근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 6」.

### 9. 브로커는 할 일을, 백엔드는 결과를 나르고, `include` 가 빠지면 워커에서 막힌다

- Broker 는 태스크 메시지(할 일)를 Producer(웹앱)에서 Worker 로 나른다.
- Backend 는 Worker 가 적은 상태와 반환값을 담아 두었다가 Producer 의 조회에 내준다.
- 둘을 헷갈리면 결과 조회가 안 된다.
- `include=['tasks']` 를 빼면 워커가 `tasks` 모듈의 태스크를 인식하지 못한다 — 메시지는 브로커까지 가도 워커가 처리하지 못한다.

근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 1」 · 「어디서 틀리나 2」.

## 실습 정답

### 실습 1. Celery 사용법을 단계별로 찍어 보이는 시연 스크립트 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 앱 만들기 | 첫 `print("""...""")` 안의 `from celery import Celery` · `app = Celery('myproject', broker=..., backend=..., include=['tasks'])` |
| 2. 앱 설정 | 같은 문자열의 `app.conf.update(result_expires=3600, task_serializer='json', accept_content=['json'], result_serializer='json', timezone='Asia/Seoul', enable_utc=True, task_track_started=True)` |
| 3. `send_email` | 둘째 문자열의 `@app.task(bind=True, max_retries=3)` · `def send_email(self, ...)` · `try` / `except` 의 `raise self.retry(exc=exc, countdown=10)` |
| 4. `process_data` · `generate_report` | 같은 문자열의 `@app.task` + `def process_data`, `@app.task(time_limit=300)` + `def generate_report` |
| 5. `delay` · `apply_async` | 셋째 문자열의 `send_email.delay(...)` · `print(f'Task ID: ...')` · `send_email.apply_async(args=..., countdown=60, expires=3600, queue='high-priority')` |
| 6. 결과 조회 · 동기 호출 | 같은 문자열의 `if result.ready():` 블록, `send_email.apply(args=...)` · `print(result.get())` |
| 7. 상태 여섯 | `print("=== 태스크 상태 ===")` 다음 문자열의 `PENDING` ~ `REVOKED` 줄 |
| 8. Beat 시간표 | `from celery.schedules import crontab` · `app.conf.beat_schedule = {...}` 의 세 항목 |
| 9. 실행 명령어 | `print("# 워커 실행")` ~ `print("celery -A celery_app flower --port=5555")` 와 사이의 `print("")` 두 개 |
| 10. 아키텍처 | `print("\n=== 아키텍처 ===")` 와 `Producer (웹앱) -> ...` · `-> Backend (결과 저장)` 두 줄 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-libraries/reference/celery-basics.py`

```python
# [주요 라이브러리] Celery 기본
# 설명: Celery 태스크 정의, delay, 결과 조회, 주기적 태스크 개념
# 팁: Celery는 CPU-bound나 I/O-bound 작업을 백그라운드로 처리할 때 사용한다. Redis가 가장 간편한 브로커. bind=True로 self에 접근하면 재시도, 로깅 등이 가능하다. 실무에서는 Flower로 태스크 모니터링을 한다.

# Celery 구조와 사용법 시연
# 실행하려면 Redis/RabbitMQ 브로커 필요

# 섹션 헤더 출력: Celery 앱 설정 부분 시작을 알린다
print("=== Celery 앱 설정 ===")
# Celery 앱 인스턴스 생성 예시 코드(문자열로 시연)
# 함정: broker URL과 backend URL을 혼동하면 결과 조회가 안 된다
# include에 누락된 모듈은 워커가 태스크를 인식하지 못한다
print("""
# celery_app.py
from celery import Celery

app = Celery(
    'myproject',
    broker='redis://localhost:6379/0',      # 메시지 브로커
    backend='redis://localhost:6379/1',     # 결과 저장소
    include=['tasks']                        # 태스크 모듈
)

# 설정
app.conf.update(
    result_expires=3600,           # 결과 만료 시간 (초)
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Seoul',
    enable_utc=True,
    task_track_started=True,       # STARTED 상태 추적
)
""")

# 섹션 헤더 출력: 태스크 정의 예시
print("=== 태스크 정의 ===")
# @app.task 데코레이터로 함수가 Celery 태스크가 된다
# bind=True 시 첫 인자 self로 태스크 인스턴스 접근(재시도 등)
# max_retries로 재시도 한도 설정. self.retry(exc=..., countdown=...)로 재시도
print("""
# tasks.py
from celery_app import app
import time

@app.task(bind=True, max_retries=3)
def send_email(self, to: str, subject: str, body: str):
    \"\"\"이메일 발송 태스크\"\"\"
    try:
        # 실제 이메일 발송 로직
        print(f'Sending email to {to}: {subject}')
        time.sleep(2)  # 발송 시간 시뮬레이션
        return {'status': 'sent', 'to': to}
    except Exception as exc:
        # 실패 시 재시도 (10초 후)
        raise self.retry(exc=exc, countdown=10)

@app.task
def process_data(data: list) -> dict:
    \"\"\"데이터 처리 태스크\"\"\"
    result = [item * 2 for item in data]
    return {'processed': result, 'count': len(result)}

@app.task(time_limit=300)  # 5분 제한
def generate_report(report_type: str, params: dict) -> str:
    \"\"\"보고서 생성 (시간이 오래 걸리는 작업)\"\"\"
    time.sleep(10)
    return f'/reports/{report_type}_2024.pdf'
""")

# 섹션 헤더 출력: 태스크 호출(produce) 방법
print("=== 태스크 호출 ===")
# delay()는 apply_async()의 단축 형태(즉시 큐에 전송, AsyncResult 반환)
# apply_async는 countdown, eta, queue 등 세밀한 제어 가능
# 함정: result.get()은 블로킹 호출이므로 웹 요청 안에서 사용하면 안 된다
print("""
# 비동기 호출 (즉시 반환)
result = send_email.delay('user@example.com', '제목', '본문')
print(f'Task ID: {result.id}')     # UUID
print(f'State: {result.state}')    # PENDING -> STARTED -> SUCCESS/FAILURE

# apply_async (더 세밀한 제어)
result = send_email.apply_async(
    args=['user@example.com', '제목', '본문'],
    countdown=60,           # 60초 후 실행
    expires=3600,           # 1시간 후 만료
    queue='high-priority',  # 특정 큐로 전송
)

# 결과 조회
if result.ready():         # 완료 여부
    print(result.get())     # 결과 가져오기 (blocking)
    print(result.result)    # 결과 (non-blocking)
    print(result.successful())  # 성공 여부

# 동기 호출 (테스트용)
result = send_email.apply(
    args=['user@example.com', '제목', '본문']
)
print(result.get())  # 즉시 실행 후 결과 반환
""")

# 섹션 헤더 출력: 태스크 상태 머신 설명
print("=== 태스크 상태 ===")
# PENDING은 "큐에 들어갔다"가 아니라 "결과 백엔드에 정보 없음"을 의미할 수도 있다(함정)
print("""
PENDING  -> 큐에 전송됨 (아직 워커가 안 받음)
STARTED  -> 워커가 실행 중 (track_started=True 필요)
SUCCESS  -> 성공 완료
FAILURE  -> 실패
RETRY   -> 재시도 대기
REVOKED  -> 취소됨
""")

# 섹션 헤더 출력: Celery Beat(스케줄러) 사용법
print("=== 주기적 태스크 (Celery Beat) ===")
# crontab으로 분/시/요일 단위 스케줄 설정
# 주의: Beat는 별도 프로세스. 두 개의 Beat가 동시에 실행되면 태스크가 중복 발행됨
print("""
from celery.schedules import crontab

app.conf.beat_schedule = {
    # 매 30분마다 실행
    'check-health-every-30-min': {
        'task': 'tasks.health_check',
        'schedule': 30.0 * 60,  # 초 단위
    },
    # 매일 오전 9시 (월~금)
    'daily-report': {
        'task': 'tasks.generate_report',
        'schedule': crontab(hour=9, minute=0, day_of_week='1-5'),
        'args': ('daily', {'date': 'today'}),
    },
    # 매주 월요일 자정
    'weekly-cleanup': {
        'task': 'tasks.cleanup_old_data',
        'schedule': crontab(hour=0, minute=0, day_of_week='monday'),
    },
}
""")

# 섹션 헤더 출력: 실제 실행 명령어
print("=== 실행 명령어 ===")
# 워커 시작 명령. -A는 앱 모듈, --concurrency는 프리포크 워커 수
print("# 워커 실행")
# 콘솔에 워커 실행 명령어 출력
print("celery -A celery_app worker --loglevel=info --concurrency=4")
# 빈 줄 출력으로 가독성 확보
print("")
# Beat 스케줄러 실행 명령어 안내
print("# Beat 스케줄러 실행")
# Beat 명령어 출력
print("celery -A celery_app beat --loglevel=info")
# 빈 줄 출력
print("")
# 모니터링 도구 Flower 안내
print("# 모니터링 (Flower)")
# Flower 설치 명령
print("pip install flower")
# Flower 실행 명령(웹 UI를 5555 포트에서 제공)
print("celery -A celery_app flower --port=5555")

# 아키텍처 다이어그램 출력 섹션 시작
print("\n=== 아키텍처 ===")
# Producer/Broker/Worker/Backend 4컴포넌트 구조 설명
print("Producer (웹앱) -> Broker (Redis/RabbitMQ) -> Worker (Celery)")
# 결과 저장 흐름 표현
print("                                            -> Backend (결과 저장)")
```

**실행 결과** — 원본 예제(`component`)를 실제로 돌린 출력이다. 환경 `Python 3.12.3` · 2026-11-28 · exit 0 · 두 번 돌려 출력이 같았다.

````text
$ python3 -I example.py
=== Celery 앱 설정 ===

# celery_app.py
from celery import Celery

app = Celery(
    'myproject',
    broker='redis://localhost:6379/0',      # 메시지 브로커
    backend='redis://localhost:6379/1',     # 결과 저장소
    include=['tasks']                        # 태스크 모듈
)

# 설정
app.conf.update(
    result_expires=3600,           # 결과 만료 시간 (초)
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Seoul',
    enable_utc=True,
    task_track_started=True,       # STARTED 상태 추적
)

=== 태스크 정의 ===

# tasks.py
from celery_app import app
import time

@app.task(bind=True, max_retries=3)
def send_email(self, to: str, subject: str, body: str):
    """이메일 발송 태스크"""  
    try:
        # 실제 이메일 발송 로직
        print(f'Sending email to {to}: {subject}')
        time.sleep(2)  # 발송 시간 시뮬레이션
        return {'status': 'sent', 'to': to}
    except Exception as exc:
        # 실패 시 재시도 (10초 후)
        raise self.retry(exc=exc, countdown=10)

@app.task
def process_data(data: list) -> dict:
    """데이터 처리 태스크"""  
    result = [item * 2 for item in data]
    return {'processed': result, 'count': len(result)}

@app.task(time_limit=300)  # 5분 제한
def generate_report(report_type: str, params: dict) -> str:
    """보고서 생성 (시간이 오래 걸리는 작업)"""  
    time.sleep(10)
    return f'/reports/{report_type}_2024.pdf'

=== 태스크 호출 ===

# 비동기 호출 (즉시 반환)
result = send_email.delay('user@example.com', '제목', '본문')
print(f'Task ID: {result.id}')     # UUID
print(f'State: {result.state}')    # PENDING -> STARTED -> SUCCESS/FAILURE

# apply_async (더 세밀한 제어)
result = send_email.apply_async(
    args=['user@example.com', '제목', '본문'],
    countdown=60,           # 60초 후 실행
    expires=3600,           # 1시간 후 만료
    queue='high-priority',  # 특정 큐로 전송
)

# 결과 조회
if result.ready():         # 완료 여부
    print(result.get())     # 결과 가져오기 (blocking)
    print(result.result)    # 결과 (non-blocking)
    print(result.successful())  # 성공 여부

# 동기 호출 (테스트용)
result = send_email.apply(
    args=['user@example.com', '제목', '본문']
)
print(result.get())  # 즉시 실행 후 결과 반환

=== 태스크 상태 ===

PENDING  -> 큐에 전송됨 (아직 워커가 안 받음)
STARTED  -> 워커가 실행 중 (track_started=True 필요)
SUCCESS  -> 성공 완료
FAILURE  -> 실패
RETRY   -> 재시도 대기
REVOKED  -> 취소됨

=== 주기적 태스크 (Celery Beat) ===

from celery.schedules import crontab

app.conf.beat_schedule = {
    # 매 30분마다 실행
    'check-health-every-30-min': {
        'task': 'tasks.health_check',
        'schedule': 30.0 * 60,  # 초 단위
    },
    # 매일 오전 9시 (월~금)
    'daily-report': {
        'task': 'tasks.generate_report',
        'schedule': crontab(hour=9, minute=0, day_of_week='1-5'),
        'args': ('daily', {'date': 'today'}),
    },
    # 매주 월요일 자정
    'weekly-cleanup': {
        'task': 'tasks.cleanup_old_data',
        'schedule': crontab(hour=0, minute=0, day_of_week='monday'),
    },
}

=== 실행 명령어 ===
# 워커 실행
celery -A celery_app worker --loglevel=info --concurrency=4

# Beat 스케줄러 실행
celery -A celery_app beat --loglevel=info

# 모니터링 (Flower)
pip install flower
celery -A celery_app flower --port=5555

=== 아키텍처 ===
Producer (웹앱) -> Broker (Redis/RabbitMQ) -> Worker (Celery)
                                            -> Backend (결과 저장)
````

**풀이 요점**

- 스크립트는 Celery 를 실제로 부르지 않고, 각 절의 코드를 `print("""...""")` 여러 줄 문자열로 찍어 보인다.
- 문자열 안의 독스트링은 `\"\"\"` 로 이스케이프해야 바깥 `"""` 문자열이 중간에 끝나지 않는다.
- 핵심 문법은 `@app.task(옵션)` · `delay` / `apply_async` / `apply` · `ready` / `get` · `beat_schedule` + `crontab` 네 덩어리다.
- 실행 명령어 절의 빈 줄은 `print("")` 로, 아키텍처 머리글 앞의 빈 줄은 문자열 앞의 `\n` 으로 만든다.
- `beat_schedule` 이 부르는 `tasks.health_check` · `tasks.cleanup_old_data` 는 `tasks.py` 에 정의되어 있지 않다 — 실제로 돌리려면 두 태스크를 더 정의해야 한다(2-summary 「어디서 틀리나 8」).

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 원본 예제를 `Python 3.12.3` 에서 2회 돌렸다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
