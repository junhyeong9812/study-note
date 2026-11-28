# python/python-web-deep/07 — Django + Celery 비동기 태스크 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 「큐에 추가」 셋이 먼저, 완료 줄 셋이 뒤 — 결과는 모두 `SUCCESS`

**출력**

```text
=== 1. 비동기 태스크 ===
  [Celery] 태스크 큐에 추가: send_email (id=task-1)
  [Celery] 태스크 큐에 추가: process_image (id=task-2)
  [Celery] 태스크 큐에 추가: generate_report (id=task-3)
  [메일] user@example.com에게 '주문 확인' 전송 완료
  [이미지] #42 -> 800x600 변환 완료
  [리포트] user=1, type=monthly 생성 완료

결과 1: SUCCESS - {'sent': True, 'to': 'user@example.com'}
결과 2: SUCCESS - {'image_id': 42, 'size': '800x600'}
결과 3: SUCCESS - {'user_id': 1, 'type': 'monthly', 'url': '/reports/123.pdf'}
```

**왜 그런가**

`.delay()` 는 `run` 을 풀에 제출한 뒤 기다리지 않고 곧장 「큐에 추가」 줄을 찍고 돌아온다.
세 번의 호출이 눈 깜짝할 새 끝나므로 「큐에 추가」 세 줄이 먼저 나온다.
각 태스크는 `time.sleep(0.1)` 을 먼저 하므로 완료 줄은 그 뒤에 나온다.
메인이 0.3초 기다리는 동안 세 태스크가 동시에 돌아 끝났고, `run` 이 같은 결과 객체의 상태를 `SUCCESS` 로, 값을 반환 딕셔너리로 바꿔 두었다.
완료 줄 셋의 차례는 이번에 이렇게 나왔을 뿐 약속된 것이 아니다(5번 참고).
근거: 2-summary 「동작 방식 (2)」 · 「동작 방식 (3)」 · 「동작 방식 (4)」.

### 2. `PENDING None` 또는 `STARTED None` — 결과값은 아직 없다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

먼저 `delay` 안에서 `  [Celery] 태스크 큐에 추가: send_email (id=task-…)` 줄이 찍히고, 이어서 `PENDING None` 이나 `STARTED None` 중 하나가 찍힌다.

**왜 그런가**

결과 객체는 `PENDING` 으로 태어나고, 일꾼 스레드가 `run` 을 잡는 순간 `STARTED` 로 바뀐다.
그 순간이 `print` 보다 먼저냐 나중이냐는 스레드가 돌아가는 때에 달려 있어 둘 다 가능하다.
어느 쪽이든 함수는 `time.sleep(0.1)` 중이라 `result` 는 아직 `None` 이다.
`SUCCESS` 는 나올 수 없다.
근거: 2-summary 「동작 방식 (2)」 · 「동작 방식 (3)」 · 「어디서 틀리나 1」.

### 3. `FAILURE | 잘못된 값` — 예외는 메인으로 퍼지지 않는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

「큐에 추가」 줄 다음에 `FAILURE | 잘못된 값` 이 찍히고, 트레이스백 없이 프로그램이 이어진다.

**왜 그런가**

`run` 은 함수 호출을 `try` 로 감싸고, `except Exception as e` 에서 `str(e)` 를 결과에 넣고 상태를 `FAILURE` 로 바꾼다.
`str(ValueError('잘못된 값'))` 은 `'잘못된 값'` 이다.
예외가 그 자리에서 잡히므로 메인 스레드로 올라오지 않는다.
`boom` 에는 `sleep` 이 없으므로 0.2초 기다림이면 충분히 끝나 있을 것이다.
근거: 2-summary 「동작 방식 (3)」.

### 4. 응답에 필요한 일과 부수효과를 나누면 응답이 빨라진다

주문 생성은 응답에 주문 번호(`order.id`)가 들어가야 하므로 그 자리에서 끝내야 한다.
확인 메일은 사용자가 응답을 받는 데 필요 없는 부수효과이고, 전송에 시간이 걸린다(I/O 바운드).
메일을 큐에 넣고 넘어가면 사용자는 메일 전송을 기다리지 않고 곧바로 응답을 받는다.
원본 주석의 원칙대로 「응답 속도가 중요한 동작은 동기, 부수효과는 비동기」다.
근거: 2-summary 「동작 방식 (5)」.

### 5. 믿으면 안 된다 — 동시에 도는 태스크의 완료 차례는 약속이 아니다

세 태스크는 일꾼 넷짜리 풀에서 동시에 돈다.
두 번 같았던 것은 그때 스레드가 그렇게 돌았다는 관찰일 뿐, 라이브러리도 언어도 그 차례를 보장하지 않는다.
진짜 Celery 라면 worker 가 여럿이라 차례는 더 흩어질 수 있다.
차례가 중요하면 `chain` 으로 이어야 한다.
근거: 2-summary 「어디서 틀리나 3」 · 「구현 세부사항 대 언어 보장」 · 「동작 방식 (8)」.

### 6. 되지 않는다 — 시뮬레이터는 그 인자를 받기만 한다

시뮬레이터의 `task()` 는 `bind` · `max_retries` · `default_retry_delay` 를 매개변수로 받지만 본문 어디서도 쓰지 않는다.
`bind=True` 여도 함수에 `self` 가 들어가지 않으므로 `self.retry()` 를 부를 수도 없다.
예외가 나면 `run` 이 `FAILURE` 로 기록하고 끝난다 — 원본 주석도 「재시도는 별도 로직」이라 적는다.
재시도는 진짜 Celery 의 `bind=True` + `self.retry()` 로 한다.
근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (3)」 · 「어디서 틀리나 4」.

### 7. ACK 가 없으면 브로커가 메시지를 지우지 않기 때문 — 두 번 돌아도 안전하게 짠다

ACK 를 받은 메시지만 큐에서 지워진다.
`acks_late=True` 면 함수가 끝난 뒤에야 ACK 를 보내므로, 그 전에 worker 가 죽으면 메시지가 남아 다시 실행된다.
대가는 「적어도 한 번」이라는 점이다 — 일은 끝냈는데 ACK 직전에 죽으면 같은 태스크가 두 번 돈다.
그래서 두 번 돌아도 결과가 같도록(예: 이미 처리했으면 건너뛰도록) 짜야 한다.
근거: 2-summary 「동작 방식 (7)」 · 「어디서 틀리나 7」.

### 8. beat 가 큐에 넣고, worker 가 실행한다

beat 는 별도 프로세스로 도는 cron 같은 스케줄러이고, `beat_schedule` 의 시각이 되면 `'myapp.tasks.cleanup_sessions'` 태스크 메시지를 브로커에 넣는다.
beat 자신은 실행하지 않는다 — 브로커에서 그 메시지를 꺼내 실행하는 것은 worker 다.
그래서 주기적 태스크가 돌려면 `celery ... beat` 와 `celery ... worker` 를 둘 다 띄워야 한다.
근거: 2-summary 「동작 방식 (6)」 · 「동작 방식 (9)」 · 「문법 — 실행 명령」.

### 9. 동시에는 `group`, 다 끝난 뒤 합치기까지는 `chord`

`group(send_email.s(email) for email in email_list)` 는 같은 태스크 여럿을 병렬로 돌린다.
`chord([process_chunk.s(chunk) ...], merge_results.s())` 는 그룹이 전부 끝난 뒤 콜백 하나를 부른다.
둘 다 `.s()` 로 만든 시그니처를 모은 뒤 `.apply_async()` 해야 큐에 들어간다.
근거: 2-summary 「동작 방식 (8)」 · 「언제 쓰고 언제 안 쓰나」.

### 10. 인자가 JSON 으로 직렬화되어 브로커를 거치기 때문

시뮬레이터는 같은 프로세스 안에서 인자를 메모리 참조 그대로 `run` 에 넘기므로 어떤 객체든 넘어간다.
진짜 Celery 는 인자를 직렬화해 브로커로 보내고 다른 프로세스(worker)가 받아 되살린다.
예제 설정은 `CELERY_TASK_SERIALIZER = 'json'` 이라 JSON 으로 바꿀 수 없는 모델 객체는 그대로 넘길 수 없다.
id 같은 단순 값을 넘기고 worker 에서 다시 조회하는 것이 안전하다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 5」 · 「문법 — 설정」.

## 실습 정답

### 실습 1. Celery 흉내 내는 시뮬레이터와 설정 해설 출력 프로그램 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 처음 상태 `PENDING`, 결과 `None` | `TaskResult.__init__` 의 `self.status = 'PENDING'` · `self.result = None` |
| 2. 카탈로그 · 매핑 · 풀 · 카운터 | `CelerySimulator.__init__` 의 `self.tasks` · `self.results` · `ThreadPoolExecutor(max_workers=4)` · `self._task_counter` |
| 3. 인자를 받기만 하는 `task()` | `def task(self, bind=False, max_retries=3, default_retry_delay=60)` → `return decorator` |
| 4. `delay` · `apply_async` 붙이고 등록 | `@wraps(func) def delay` · `func.delay = delay` · `func.apply_async = delay` · `self.tasks[task_name] = func` · `return func` |
| 5. id 발급 · 제출 · 큐 추가 줄 · 즉시 반환 | `delay` 안의 `self._task_counter += 1` · `TaskResult(task_id)` · `self.executor.submit(run)` · `print(f"  [Celery] 태스크 큐에 추가: ...")` · `return result` |
| 6. STARTED → SUCCESS / FAILURE | `run()` 의 `result.status = 'STARTED'` · `try` / `except Exception as e` |
| 7. 전역 앱과 1절 제목 | `app = CelerySimulator()` · `print("=== 1. 비동기 태스크 ===")` |
| 8. 세 태스크 등록 | `@app.task()` 가 붙은 `send_email` · `process_image` · `generate_report` |
| 9. 세 번의 `.delay()` | `result1 = send_email.delay(...)` · `result2 = process_image.delay(42, '800x600')` · `result3 = generate_report.delay(1, 'monthly')` |
| 10. 대기 후 결과 세 줄 | `time.sleep(0.3)` · `print(f"\n결과 1: ...")` 등 |
| 11. 뷰 패턴 | `=== 2. Django 뷰에서 Celery 사용 ===` 아래 `place_order` 문자열 |
| 12. beat 시간표 | `=== 3. 주기적 태스크 ===` 아래 `app.conf.beat_schedule` 문자열 |
| 13. 재시도와 `acks_late` | `=== 4. 재시도와 에러 처리 ===` 아래 `send_webhook` · `critical_task` 문자열 |
| 14. Canvas | `=== 5. 태스크 체이닝 ===` 아래 `chain` · `group` · `chord` 문자열 |
| 15. 설정과 실행 명령 | `=== 6. Celery 설정 ===` 아래 `CELERY_...` · `celery -A myproject ...` 문자열 |
| 16. 핵심 정리 | `=== 핵심 정리 ===` 와 `print("1. ...")` ~ `print("6. ...")` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-web-deep/reference/django-celery.py`

```python
# [웹 프레임워크 심화] Django + Celery 비동기 태스크
# 설명: Celery 연동, 비동기 태스크 정의/실행, 주기적 태스크
# 팁: Celery는 .delay()로 태스크를 비동기 큐에 넣고, worker가 처리한다. 이메일 전송, 이미지 처리, 리포트 생성 등 시간이 걸리는 작업에 적합하다. beat로 주기적 태스크를 스케줄링하고, bind=True로 재시도 로직을 구현한다. Redis가 가장 흔한 브로커다.

"""Django + Celery: 비동기 태스크, 주기적 태스크"""
# time: 작업 지연 시뮬레이션
import time
# 타입 힌트
from typing import Any
# 일정 표현용
from datetime import datetime, timedelta
# 비동기 실행 시뮬레이션 (실제 Celery는 별도 worker 프로세스)
from concurrent.futures import ThreadPoolExecutor
# 데코레이터 보조
from functools import wraps
# 스레드 안전성 (시뮬레이션 단순화)
import threading

# === Celery 시뮬레이션 ===
# 태스크 실행 결과 객체 (Celery의 AsyncResult에 대응)
class TaskResult:
    def __init__(self, task_id: str):
        self.task_id = task_id
        # 상태: PENDING → STARTED → SUCCESS/FAILURE
        self.status = 'PENDING'
        self.result = None

# Celery 앱 시뮬레이션: @task 데코레이터와 .delay() 메커니즘
class CelerySimulator:
    """Celery의 핵심 동작을 시뮬레이션"""
    def __init__(self):
        # 등록된 태스크 카탈로그
        self.tasks = {}
        # 태스크 ID → 결과 매핑
        self.results = {}
        # 워커 풀: 실제 Celery는 별도 OS 프로세스(Redis/RabbitMQ를 통해 통신)
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._task_counter = 0

    # @app.task() 데코레이터: 함수를 비동기 가능하게 변환
    def task(self, bind=False, max_retries=3, default_retry_delay=60):
        """@shared_task 데코레이터 시뮬레이션"""
        def decorator(func):
            task_name = func.__name__

            # delay(): 태스크를 큐에 넣고 즉시 반환
            @wraps(func)
            def delay(*args, **kwargs):
                self._task_counter += 1
                task_id = f"task-{self._task_counter}"
                result = TaskResult(task_id)
                self.results[task_id] = result

                # 워커 측에서 실행될 함수 (실제 Celery는 broker에서 메시지 pull)
                def run():
                    result.status = 'STARTED'
                    try:
                        # 실제 함수 실행
                        result.result = func(*args, **kwargs)
                        result.status = 'SUCCESS'
                    except Exception as e:
                        # 에러 시 FAILURE (재시도는 별도 로직)
                        result.result = str(e)
                        result.status = 'FAILURE'

                # 비동기 실행 제출 (실제로는 Redis/RabbitMQ에 직렬화하여 전송)
                self.executor.submit(run)
                print(f"  [Celery] 태스크 큐에 추가: {task_name} (id={task_id})")
                return result

            # 함수에 .delay와 .apply_async 어태치
            func.delay = delay
            func.apply_async = delay
            self.tasks[task_name] = func
            return func
        return decorator

# 전역 Celery 앱
app = CelerySimulator()

# === 1. 기본 비동기 태스크 ===
print("=== 1. 비동기 태스크 ===")

# 이메일 전송: I/O 바운드 작업의 전형
@app.task()
def send_email(to: str, subject: str, body: str):
    """이메일 전송 (시간이 걸리는 작업)"""
    time.sleep(0.1)  # 전송 시뮬레이션
    print(f"  [메일] {to}에게 '{subject}' 전송 완료")
    return {'sent': True, 'to': to}

# 이미지 처리: CPU 바운드 작업 예시
@app.task()
def process_image(image_id: int, size: str):
    """이미지 리사이징 (CPU 집약적)"""
    time.sleep(0.1)
    print(f"  [이미지] #{image_id} -> {size} 변환 완료")
    return {'image_id': image_id, 'size': size}

# 리포트 생성: 시간이 오래 걸리는 집계
@app.task()
def generate_report(user_id: int, report_type: str):
    """리포트 생성 (시간이 걸리는 집계)"""
    time.sleep(0.1)
    print(f"  [리포트] user={user_id}, type={report_type} 생성 완료")
    return {'user_id': user_id, 'type': report_type, 'url': '/reports/123.pdf'}

# 비동기 실행: 호출 즉시 AsyncResult 반환, 실제 작업은 백그라운드
result1 = send_email.delay('user@example.com', '주문 확인', '주문이 접수되었습니다.')
result2 = process_image.delay(42, '800x600')
result3 = generate_report.delay(1, 'monthly')

# 시뮬레이션이라 sleep으로 완료 대기 (실제로는 .get()으로 기다리거나 폴링)
time.sleep(0.3)  # 태스크 완료 대기

print(f"\n결과 1: {result1.status} - {result1.result}")
print(f"결과 2: {result2.status} - {result2.result}")
print(f"결과 3: {result3.status} - {result3.result}")

# === 2. Django 뷰에서 사용 ===
print("\n=== 2. Django 뷰에서 Celery 사용 ===")
# 패턴: 응답 속도가 중요한 동작은 동기, 부수효과는 비동기로 분리
print("""
# views.py
from .tasks import send_email, generate_report

def place_order(request):
    order = Order.objects.create(...)  # 동기: 주문 생성

    # 비동기: 이메일/리포트는 백그라운드에서
    send_email.delay(
        to=request.user.email,
        subject='주문 확인',
        body=f'주문 #{order.id}가 접수되었습니다.'
    )

    return JsonResponse({'order_id': order.id, 'status': 'created'})
""")

# === 3. 주기적 태스크 (Celery Beat) ===
print("=== 3. 주기적 태스크 ===")
# Celery Beat: cron-like 스케줄러 (별도 프로세스로 실행)
print("""
# celery.py
from celery import Celery
from celery.schedules import crontab

app = Celery('myproject')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# 주기적 태스크 스케줄
app.conf.beat_schedule = {
    'cleanup-expired-sessions': {
        'task': 'myapp.tasks.cleanup_sessions',
        'schedule': crontab(hour=3, minute=0),  # 매일 3시
    },
    'send-daily-report': {
        'task': 'myapp.tasks.send_daily_report',
        'schedule': crontab(hour=9, minute=0, day_of_week='mon-fri'),
    },
    'update-exchange-rates': {
        'task': 'myapp.tasks.update_rates',
        'schedule': 300.0,  # 5분마다
    },
    'weekly-backup': {
        'task': 'myapp.tasks.backup_database',
        'schedule': crontab(hour=2, minute=0, day_of_week='sunday'),
    },
}
""")

# === 4. 재시도와 에러 처리 ===
print("=== 4. 재시도와 에러 처리 ===")
# bind=True: 첫 인자 self로 태스크 인스턴스 접근 → self.retry() 호출 가능
# acks_late: 작업 완료 후에야 ACK (워커 죽으면 재실행) — at-least-once 보장
print("""
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_webhook(self, url, data):
    try:
        response = requests.post(url, json=data, timeout=10)
        response.raise_for_status()
        return {'status': 'sent', 'code': response.status_code}
    except requests.RequestException as exc:
        try:
            self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
        except MaxRetriesExceededError:
            logger.error(f'Webhook 전송 실패 (최대 재시도): {url}')
            return {'status': 'failed', 'error': str(exc)}

@shared_task(bind=True, acks_late=True)  # 완료 후 ACK
def critical_task(self, data):
    '''중요한 태스크: worker 중단 시 재실행'''
    process_critical_data(data)
""")

# === 5. 체이닝과 그룹 ===
print("=== 5. 태스크 체이닝 ===")
# Canvas: chain(순차), group(병렬), chord(병렬+콜백) — 워크플로 조합
print("""
from celery import chain, group, chord

# 체이닝: A -> B -> C 순차 실행
result = chain(
    fetch_data.s(url),
    process_data.s(),
    save_results.s()
).apply_async()

# 그룹: 병렬 실행
result = group(
    send_email.s(email) for email in email_list
).apply_async()

# chord: 그룹 완료 후 콜백
result = chord(
    [process_chunk.s(chunk) for chunk in data_chunks],
    merge_results.s()
).apply_async()
""")

# === 6. 설정 ===
print("=== 6. Celery 설정 ===")
# 브로커: Redis(권장, 가벼움) 또는 RabbitMQ(견고한 메시지 큐)
# Result Backend: 작업 결과 저장소 (Redis/DB)
print("""
# settings.py
CELERY_BROKER_URL = 'redis://localhost:6379/0'  # 메시지 브로커
CELERY_RESULT_BACKEND = 'redis://localhost:6379/1'  # 결과 저장
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Seoul'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 300  # 5분 제한

# 실행 명령
# celery -A myproject worker -l info
# celery -A myproject beat -l info
# celery -A myproject flower  # 모니터링 UI
""")

print("=== 핵심 정리 ===")
print("1. @shared_task + .delay(): 비동기 태스크 실행")
print("2. beat_schedule + crontab: 주기적 태스크")
print("3. bind=True + self.retry(): 재시도 처리")
print("4. chain/group/chord: 태스크 조합")
print("5. 브로커: Redis(권장) 또는 RabbitMQ")
print("6. flower: 웹 기반 모니터링")
```

**실행 결과** — 원본 예제(`component`)를 실제로 돌린 출력이다. 환경 `Python 3.12.3` · 2026-11-28 · exit 0 · 두 번 돌려 출력이 같았다.

````text
$ python3 -I example.py
=== 1. 비동기 태스크 ===
  [Celery] 태스크 큐에 추가: send_email (id=task-1)
  [Celery] 태스크 큐에 추가: process_image (id=task-2)
  [Celery] 태스크 큐에 추가: generate_report (id=task-3)
  [메일] user@example.com에게 '주문 확인' 전송 완료
  [이미지] #42 -> 800x600 변환 완료
  [리포트] user=1, type=monthly 생성 완료

결과 1: SUCCESS - {'sent': True, 'to': 'user@example.com'}
결과 2: SUCCESS - {'image_id': 42, 'size': '800x600'}
결과 3: SUCCESS - {'user_id': 1, 'type': 'monthly', 'url': '/reports/123.pdf'}

=== 2. Django 뷰에서 Celery 사용 ===

# views.py
from .tasks import send_email, generate_report

def place_order(request):
    order = Order.objects.create(...)  # 동기: 주문 생성

    # 비동기: 이메일/리포트는 백그라운드에서
    send_email.delay(
        to=request.user.email,
        subject='주문 확인',
        body=f'주문 #{order.id}가 접수되었습니다.'
    )

    return JsonResponse({'order_id': order.id, 'status': 'created'})

=== 3. 주기적 태스크 ===

# celery.py
from celery import Celery
from celery.schedules import crontab

app = Celery('myproject')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# 주기적 태스크 스케줄
app.conf.beat_schedule = {
    'cleanup-expired-sessions': {
        'task': 'myapp.tasks.cleanup_sessions',
        'schedule': crontab(hour=3, minute=0),  # 매일 3시
    },
    'send-daily-report': {
        'task': 'myapp.tasks.send_daily_report',
        'schedule': crontab(hour=9, minute=0, day_of_week='mon-fri'),
    },
    'update-exchange-rates': {
        'task': 'myapp.tasks.update_rates',
        'schedule': 300.0,  # 5분마다
    },
    'weekly-backup': {
        'task': 'myapp.tasks.backup_database',
        'schedule': crontab(hour=2, minute=0, day_of_week='sunday'),
    },
}

=== 4. 재시도와 에러 처리 ===

from celery import shared_task
from celery.exceptions import MaxRetriesExceededError

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_webhook(self, url, data):
    try:
        response = requests.post(url, json=data, timeout=10)
        response.raise_for_status()
        return {'status': 'sent', 'code': response.status_code}
    except requests.RequestException as exc:
        try:
            self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
        except MaxRetriesExceededError:
            logger.error(f'Webhook 전송 실패 (최대 재시도): {url}')
            return {'status': 'failed', 'error': str(exc)}

@shared_task(bind=True, acks_late=True)  # 완료 후 ACK
def critical_task(self, data):
    '''중요한 태스크: worker 중단 시 재실행'''
    process_critical_data(data)

=== 5. 태스크 체이닝 ===

from celery import chain, group, chord

# 체이닝: A -> B -> C 순차 실행
result = chain(
    fetch_data.s(url),
    process_data.s(),
    save_results.s()
).apply_async()

# 그룹: 병렬 실행
result = group(
    send_email.s(email) for email in email_list
).apply_async()

# chord: 그룹 완료 후 콜백
result = chord(
    [process_chunk.s(chunk) for chunk in data_chunks],
    merge_results.s()
).apply_async()

=== 6. Celery 설정 ===

# settings.py
CELERY_BROKER_URL = 'redis://localhost:6379/0'  # 메시지 브로커
CELERY_RESULT_BACKEND = 'redis://localhost:6379/1'  # 결과 저장
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Seoul'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 300  # 5분 제한

# 실행 명령
# celery -A myproject worker -l info
# celery -A myproject beat -l info
# celery -A myproject flower  # 모니터링 UI

=== 핵심 정리 ===
1. @shared_task + .delay(): 비동기 태스크 실행
2. beat_schedule + crontab: 주기적 태스크
3. bind=True + self.retry(): 재시도 처리
4. chain/group/chord: 태스크 조합
5. 브로커: Redis(권장) 또는 RabbitMQ
6. flower: 웹 기반 모니터링
````

**풀이 요점**
- `delay` 의 핵심은 「제출하고 기다리지 않는다」다 — `executor.submit(run)` 뒤에 곧장 줄을 찍고 결과 객체를 돌려주므로 「큐에 추가」 줄이 완료 줄보다 먼저 나온다.
- 호출자가 받은 결과 객체와 `run` 이 고치는 결과 객체가 같은 객체라서, 기다린 뒤에 바뀐 상태를 읽을 수 있다.
- 데코레이터는 원래 함수를 그대로 돌려주고 속성(`delay` · `apply_async`)만 붙이므로, 함수를 그냥 부르면 동기로 돈다.
- `bind` · `max_retries` · `default_retry_delay` 는 진짜 Celery 의 꼴을 흉내 낼 뿐 시뮬레이터에서는 쓰이지 않는다 — 재시도는 4절의 진짜 Celery 코드가 보여 준다.
- `time.sleep(0.3)` 은 시뮬레이션의 가정이고, 진짜 환경에서는 `.get()` 이나 폴링으로 기다린다.
- 2~6절은 실행되지 않는 해설 문자열이다 — 뷰 분리 · beat · 재시도 · Canvas · 설정이라는 진짜 Celery 의 지도를 한 화면에 모아 보이는 몫이다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 원본 예제를 `Python 3.12.3` 에서 2회 돌렸다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
