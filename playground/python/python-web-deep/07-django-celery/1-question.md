# python/python-web-deep/07 — Django + Celery 비동기 태스크 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 태스크 세 개를 `.delay()` 로 연달아 부르면 (예측)

```python
# 질문용 발췌
result1 = send_email.delay('user@example.com', '주문 확인', '주문이 접수되었습니다.')
result2 = process_image.delay(42, '800x600')
result3 = generate_report.delay(1, 'monthly')
time.sleep(0.3)
print(f"\n결과 1: {result1.status} - {result1.result}")
```

- 「큐에 추가」 줄 셋과 태스크가 찍는 완료 줄 셋은 어떤 차례로 나오는가?
- `결과 1` 줄에는 어떤 상태와 값이 찍히는가?

### 2. `.delay()` 바로 다음 줄에서 상태를 찍으면 (예측)

```python
# 질문용 발췌 — 기다리지 않고 곧바로 찍는다
r = send_email.delay('a@b.c', '제목', '본문')
print(r.status, r.result)
```

- 두 번째 줄은 무엇을 찍을 수 있는가?

### 3. 시뮬레이터의 태스크 안에서 예외가 나면 (예측)

```python
# 질문용 발췌
@app.task()
def boom():
    raise ValueError('잘못된 값')

r = boom.delay()
time.sleep(0.2)
print(r.status, '|', r.result)
```

- 마지막 줄은 무엇을 찍고, 메인 프로그램에 예외가 퍼지는가?

### 4. 뷰에서 주문 생성은 동기로, 확인 메일은 `.delay()` 로 나누는 까닭 (왜)

- 둘 다 같은 요청에서 일어나는 일인데 왜 하나는 그 자리에서 끝내고 하나는 큐에 넣는가?

### 5. 완료 줄의 차례 (경계)

- 두 번 돌려 완료 줄이 메일 → 이미지 → 리포트로 같았다면, 이 차례를 믿고 코드를 짜도 되는가?

### 6. 시뮬레이터에 `bind=True, max_retries=3` 을 넘기면 (경계)

- 시뮬레이터의 `@app.task(bind=True, max_retries=3)` 태스크가 예외를 내면 다시 실행되는가?

### 7. `acks_late=True` 가 중단된 태스크를 되살리는 까닭 (왜)

- 완료 후에 ACK 를 보내면 왜 worker 가 죽었을 때 재실행되고, 그 대가로 태스크를 어떻게 짜야 하는가?

### 8. beat 와 worker 의 몫 (연결)

- `beat_schedule` 에 적은 「매일 3시」 태스크는 누가 큐에 넣고 누가 실행하는가?

### 9. 메일 100통 보내기와 다 끝난 뒤 합치기 (연결)

- 같은 태스크를 여럿 동시에 돌리려면, 그리고 그것들이 모두 끝난 뒤 한 번 합치려면 Canvas 의 무엇을 쓰는가?

### 10. Django 모델 객체를 태스크 인자로 넘기기 (경계)

- 시뮬레이터에서는 잘 되던 「모델 객체를 `.delay()` 에 그대로 넘기기」가 예제 설정의 진짜 Celery 에서는 왜 문제가 되는가?

## 실습

### 실습 1. Celery 흉내 내는 시뮬레이터와 설정 해설 출력 프로그램 만들기

**만들 것** — 스레드 풀로 Celery 의 `@task` 와 `.delay()` 를 흉내 내 태스크 세 개를 비동기로 돌린 뒤, 진짜 Django + Celery 의 뷰 · beat · 재시도 · Canvas · 설정 코드를 절마다 찍어 보여 주는 한 파일짜리 프로그램.

**준비물** — Python 3 표준 라이브러리만 쓴다. Celery · Redis · Django 는 설치하지 않는다 — 1절은 Celery 를 흉내 낸 것이고, 2~6절의 Celery 코드는 실행하지 않고 문자열로만 찍는다.

**요구 조건**

1단계 — 결과 객체와 시뮬레이터
1. `TaskResult` 는 `task_id` 를 받고, 처음 상태를 `'PENDING'`, 결과를 `None` 으로 둔다.
2. `CelerySimulator` 는 태스크 카탈로그(`tasks`), id → 결과 매핑(`results`), 일꾼 4개짜리 `ThreadPoolExecutor`, 태스크 번호 카운터를 가진다.
3. `task(bind=False, max_retries=3, default_retry_delay=60)` 는 데코레이터를 돌려준다 — 인자는 받기만 한다.
4. 데코레이터는 `delay` 함수를 `@wraps(func)` 로 만들어 `func.delay` 와 `func.apply_async` 둘 다에 붙이고, `tasks[함수 이름]` 에 등록한 뒤 원래 함수를 돌려준다.
5. `delay` 는 카운터를 올려 `task-N` 꼴의 id 로 `TaskResult` 를 만들어 `results` 에 등록하고, 실행 함수를 풀에 제출한 뒤, `  [Celery] 태스크 큐에 추가: <이름> (id=<id>)` 줄을 찍고 결과 객체를 곧장 돌려준다.
6. 풀에서 도는 실행 함수는 상태를 `'STARTED'` 로 바꾸고 원래 함수를 부른다 — 성공하면 반환값을 넣고 `'SUCCESS'`, 예외면 예외 문자열을 넣고 `'FAILURE'` 로 바꾼다.

2단계 — 태스크 세 개 돌리기
7. 전역 `app` 을 만들고 `=== 1. 비동기 태스크 ===` 를 찍는다.
8. `send_email` · `process_image` · `generate_report` 를 `@app.task()` 로 등록한다(본문은 시작 코드에 있다).
9. 세 태스크를 `.delay()` 로 부른다 — 인자는 각각 (`'user@example.com'`, `'주문 확인'`, `'주문이 접수되었습니다.'`), (`42`, `'800x600'`), (`1`, `'monthly'`).
10. 0.3초 기다린 뒤 `결과 N: <상태> - <결과>` 세 줄을 찍는다(첫 줄 앞에 빈 줄).

3단계 — 진짜 Celery 코드 해설 찍기
11. `=== 2. Django 뷰에서 Celery 사용 ===` 아래에, 주문은 동기로 만들고 `send_email.delay(...)` 로 메일을 맡긴 뒤 `JsonResponse` 를 돌려주는 `place_order` 뷰 코드를 여러 줄 문자열로 찍는다.
12. `=== 3. 주기적 태스크 ===` 아래에, `Celery('myproject')` 앱 설정과 네 항목(매일 3시 세션 정리, 평일 9시 리포트, 300초마다 환율, 일요일 2시 백업)짜리 `beat_schedule` 을 찍는다.
13. `=== 4. 재시도와 에러 처리 ===` 아래에, `bind=True` + `self.retry()` 를 쓰는 `send_webhook` 과 `acks_late=True` 인 `critical_task` 를 찍는다.
14. `=== 5. 태스크 체이닝 ===` 아래에, `chain` · `group` · `chord` 를 하나씩 쓰는 코드를 찍는다.
15. `=== 6. Celery 설정 ===` 아래에, `CELERY_` 설정 여덟 줄과 worker · beat · flower 실행 명령을 찍는다.
16. `=== 핵심 정리 ===` 와 핵심 여섯 줄(`.delay()` · beat · 재시도 · Canvas · 브로커 · flower)을 찍는다.

**시작 코드**

```python
"""Django + Celery: 비동기 태스크, 주기적 태스크"""
import time
from concurrent.futures import ThreadPoolExecutor
from functools import wraps


class TaskResult:
    def __init__(self, task_id: str):
        self.task_id = task_id
        # TODO: 처음 상태와 결과 값


class CelerySimulator:
    """Celery의 핵심 동작을 시뮬레이션"""
    def __init__(self):
        self.tasks = {}
        self.results = {}
        # TODO: 일꾼 4개짜리 스레드 풀
        self._task_counter = 0

    def task(self, bind=False, max_retries=3, default_retry_delay=60):
        """@shared_task 데코레이터 시뮬레이션"""
        def decorator(func):
            task_name = func.__name__

            @wraps(func)
            def delay(*args, **kwargs):
                # TODO: 번호를 올리고 task-N id 로 TaskResult 를 만들어 results 에 등록

                def run():
                    # TODO: STARTED → 함수 실행 → SUCCESS, 예외면 FAILURE
                    pass

                # TODO: run 을 풀에 제출
                # 찍을 꼴: f"  [Celery] 태스크 큐에 추가: {task_name} (id={task_id})"
                # TODO: 결과 객체를 돌려준다

            # TODO: func 에 delay · apply_async 를 붙이고 tasks 에 등록
            return func
        return decorator


app = CelerySimulator()

print("=== 1. 비동기 태스크 ===")


# TODO: 태스크로 등록
def send_email(to: str, subject: str, body: str):
    """이메일 전송 (시간이 걸리는 작업)"""
    time.sleep(0.1)
    print(f"  [메일] {to}에게 '{subject}' 전송 완료")
    return {'sent': True, 'to': to}


# TODO: 태스크로 등록
def process_image(image_id: int, size: str):
    """이미지 리사이징 (CPU 집약적)"""
    time.sleep(0.1)
    print(f"  [이미지] #{image_id} -> {size} 변환 완료")
    return {'image_id': image_id, 'size': size}


# TODO: 태스크로 등록
def generate_report(user_id: int, report_type: str):
    """리포트 생성 (시간이 걸리는 집계)"""
    time.sleep(0.1)
    print(f"  [리포트] user={user_id}, type={report_type} 생성 완료")
    return {'user_id': user_id, 'type': report_type, 'url': '/reports/123.pdf'}


# TODO: 세 태스크를 비동기로 실행 → result1, result2, result3
# TODO: 0.3초 대기 후 결과 세 줄

print("\n=== 2. Django 뷰에서 Celery 사용 ===")
# TODO: place_order 뷰 코드를 여러 줄 문자열로

print("=== 3. 주기적 태스크 ===")
# TODO: celery.py 앱 설정 + beat_schedule 네 항목

print("=== 4. 재시도와 에러 처리 ===")
# TODO: send_webhook(bind=True, max_retries=3, default_retry_delay=60) + critical_task(acks_late=True)

print("=== 5. 태스크 체이닝 ===")
# TODO: chain / group / chord

print("=== 6. Celery 설정 ===")
# TODO: settings.py 의 CELERY_ 설정 여덟 줄 + 실행 명령 세 줄

print("=== 핵심 정리 ===")
# TODO: 핵심 여섯 줄
```

**확인 방법** — `python django-celery.py` 로 돌려, 「큐에 추가」 세 줄이 완료 줄들보다 먼저 나오는지, `결과 1~3` 이 모두 `SUCCESS` 와 반환 딕셔너리를 찍는지, 이어서 2~6절과 핵심 정리가 차례로 찍히는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
