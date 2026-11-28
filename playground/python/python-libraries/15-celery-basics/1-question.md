# python/python-libraries/15 — Celery 기본 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. `delay` 를 부른 직후 (예측)

```python
# 질문용 발췌
result = send_email.delay('user@example.com', '제목', '본문')
print(f'Task ID: {result.id}')
print(f'State: {result.state}')
```

- `delay` 줄은 `send_email` 본문의 `time.sleep(2)` 가 끝날 때까지 기다리나?
- 곧장 찍는 `result.state` 로 가장 흔히 보이는 값은 무엇인가?

### 2. `countdown=60` 으로 보낸 직후의 `ready()` (예측)

```python
# 질문용 발췌
result = send_email.apply_async(
    args=['user@example.com', '제목', '본문'],
    countdown=60,
)
if result.ready():
    print(result.get())
```

- 이 코드를 한 번에 이어 돌리면 `if` 블록 안에서 무언가 찍히나?
- 70초쯤 기다린 뒤(발송이 성공했다면) 같은 `if` 를 다시 돌리면 `result.get()` 은 무엇을 돌려주나?

### 3. `process_data` 에 `[1, 2, 3]` 을 맡기면 (예측)

- `process_data.delay([1, 2, 3])` 이 돌려준 객체에서 작업이 끝난 뒤 `get()` 으로 받는 값은 무엇인가?

### 4. 실행 명령어 절이 찍는 줄 (예측)

```python
# 질문용 발췌
print("=== 실행 명령어 ===")
print("# 워커 실행")
print("celery -A celery_app worker --loglevel=info --concurrency=4")
print("")
print("# Beat 스케줄러 실행")
print("celery -A celery_app beat --loglevel=info")
print("")
print("# 모니터링 (Flower)")
print("pip install flower")
print("celery -A celery_app flower --port=5555")
```

- 이 발췌는 모두 몇 줄을 찍고, 그중 빈 줄은 어디에 몇 개인가?
- 찍힌 명령 가운데 계속 떠 있는 Celery 프로세스를 띄우는 것은 몇 종류인가?

### 5. `send_email` 에 `bind=True` 를 붙인 까닭 (왜)

- `send_email` 은 왜 `bind=True` 를 주고 첫 인자로 `self` 를 받나?

### 6. `result.get()` 을 웹 요청 안에서 부르면 안 되는 까닭 (왜)

- 웹 요청 처리 중에 `result.get()` 을 부르면 왜 Celery 를 쓴 의미가 사라지나?

### 7. `PENDING` 이 말해 주는 것과 말해 주지 않는 것 (경계)

- 조회한 상태가 `PENDING` 이면 그 태스크가 브로커의 큐에 들어 있다고 믿어도 되나?
- `task_track_started` 를 켜지 않은 채 실행 중인 태스크를 조회하면 어떤 상태로 보이나?

### 8. Beat 를 몇 개 띄우나 (경계)

- Beat 프로세스를 둘 띄우면 평일 `daily-report` 는 하루에 몇 번 발행되나?
- 워커만 띄우고 Beat 를 띄우지 않으면 `beat_schedule` 의 일은 실행되나?

### 9. 브로커 · 백엔드 · `include` 의 몫 (연결)

- 아키텍처 그림에서 Broker 와 Backend 는 각각 무엇을 어느 쪽에서 어느 쪽으로 나르나?
- `include=['tasks']` 를 빼먹으면 메시지가 브로커에 잘 들어가도 어디서 일이 막히나?

## 실습

### 실습 1. Celery 사용법을 단계별로 찍어 보이는 시연 스크립트 만들기

**만들 것** — Celery 의 앱 설정 · 태스크 정의 · 호출 · 상태 · Beat · 실행 명령어 · 아키텍처를 일곱 개의 절로 나눠 화면에 찍는 Python 스크립트를 만든다.
각 절은 머리글 한 줄과, Celery 코드를 담은 여러 줄 문자열(또는 명령 줄들)로 이루어진다.

**준비물** — 이 스크립트는 Celery 를 import 하지 않고 Celery 코드를 문자열로 찍어 보이기만 한다(흉내 낸 시연이다). 문자열 안의 코드를 실제로 돌리려면 `celery` 패키지와 Redis(또는 RabbitMQ) 브로커가 필요하다.

**요구 조건**

1. 1단계 — `=== Celery 앱 설정 ===` 머리글 다음에, `celery_app.py` 의 내용을 문자열로 찍는다: `Celery` 를 import 하고, 이름 `'myproject'` · 브로커 · 백엔드 · `include=['tasks']` 를 준 앱을 만든다.
2. 1단계(이어서) — 같은 문자열 안에서 `app.conf.update(...)` 로 결과 만료 3600초, 태스크 · 결과 직렬화와 허용 형식을 JSON 으로, 시간대 `'Asia/Seoul'`, UTC 사용, `STARTED` 상태 추적을 설정한다.
3. 2단계 — `=== 태스크 정의 ===` 머리글 다음에 `tasks.py` 를 문자열로 찍는다: `send_email` 은 `bind=True` · 재시도 한도 3을 주고, 본문에서 발송 메시지를 찍고 2초 잠든 뒤 `{'status': 'sent', 'to': to}` 를 돌려주며, 예외가 나면 `self.retry` 로 10초 뒤 재시도한다.
4. 2단계(이어서) — `process_data` 는 리스트 원소를 두 배로 만들어 `processed` 와 `count` 를 담은 사전을 돌려주고, `generate_report` 는 실행 시간 제한 300초를 두고 10초 잠든 뒤 보고서 경로 문자열을 돌려준다.
5. 3단계 — `=== 태스크 호출 ===` 머리글 다음에, `delay` 로 보내고 `id` · `state` 를 찍는 코드, `apply_async` 로 `args` · 60초 지연 · 3600초 만료 · `'high-priority'` 큐를 주는 코드를 문자열로 찍는다.
6. 3단계(이어서) — 같은 문자열 안에서 `ready()` 가 참일 때만 `get()` · `result` · `successful()` 을 찍는 코드와, `apply` 로 동기 호출한 뒤 `get()` 하는 코드를 보인다.
7. 4단계 — `=== 태스크 상태 ===` 머리글 다음에 `PENDING` · `STARTED` · `SUCCESS` · `FAILURE` · `RETRY` · `REVOKED` 여섯 상태와 각각의 설명을 한 줄씩 담은 문자열을 찍는다.
8. 5단계 — `=== 주기적 태스크 (Celery Beat) ===` 머리글 다음에, `crontab` 을 import 하고 `app.conf.beat_schedule` 에 세 항목(30분 간격 `tasks.health_check`, 월~금 9시 `tasks.generate_report` 와 인자, 월요일 자정 `tasks.cleanup_old_data`)을 적은 문자열을 찍는다.
9. 6단계 — `=== 실행 명령어 ===` 머리글 다음에 워커 실행(동시성 4) · Beat 실행 · Flower 설치와 실행(포트 5555)을 주석 줄과 명령 줄로 찍고, 세 묶음 사이에 빈 줄을 하나씩 둔다.
10. 7단계 — 빈 줄 하나를 앞에 둔 `=== 아키텍처 ===` 머리글 다음에, Producer → Broker → Worker 흐름 한 줄과 Worker 아래의 Backend 갈래 한 줄을 찍는다.

**시작 코드**

```python
# [주요 라이브러리] Celery 기본 — 연습
# 문자열 안의 코드는 Celery 코드를 「보여 주기」만 한다

print("=== Celery 앱 설정 ===")
print("""
# celery_app.py
from celery import Celery

# TODO: app = Celery(...) — 이름 'myproject'
#       broker='redis://localhost:6379/0', backend='redis://localhost:6379/1', include=['tasks']

# 설정
# TODO: app.conf.update(...) — 만료 · 직렬화 3종 · timezone='Asia/Seoul' · enable_utc · STARTED 추적
""")

print("=== 태스크 정의 ===")
print("""
# tasks.py
from celery_app import app
import time

# TODO: send_email(self, to, subject, body) — 데코레이터 옵션, try 안의 발송 흉내, except 안의 재시도

# TODO: process_data(data: list) -> dict

# TODO: generate_report(report_type: str, params: dict) -> str — 5분 제한
""")

print("=== 태스크 호출 ===")
print("""
# 비동기 호출 (즉시 반환)
# TODO: send_email 을 delay 로 보내고 id, state 찍기 ('user@example.com', '제목', '본문')

# apply_async (더 세밀한 제어)
# TODO: args · countdown · expires · queue

# 결과 조회
# TODO: ready() 일 때만 get(), result, successful()

# 동기 호출 (테스트용)
# TODO: apply 후 get()
""")

print("=== 태스크 상태 ===")
print("""
# TODO: 여섯 상태를 한 줄씩
""")

print("=== 주기적 태스크 (Celery Beat) ===")
print("""
# TODO: crontab import 와 app.conf.beat_schedule 세 항목
""")

print("=== 실행 명령어 ===")
# TODO: 워커 · Beat · Flower 안내 줄과 명령 줄, 묶음 사이 빈 줄

# TODO: 빈 줄을 앞에 둔 아키텍처 머리글과 두 줄
```

**확인 방법** — `python celery-basics.py` 로 돌려 일곱 개의 `=== … ===` 머리글이 차례대로 찍히는지, 각 문자열 안의 코드가 Python 문법으로 읽히는지, 실행 명령어 절의 묶음 사이에 빈 줄이 하나씩 있는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
