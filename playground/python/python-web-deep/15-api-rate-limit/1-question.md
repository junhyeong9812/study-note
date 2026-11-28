# python/python-web-deep/15 — Rate Limiting: 토큰 버킷과 슬라이딩 윈도우 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 가득 찬 버킷에 여덟 번 연달아 요청하면 (예측)

```python
# 질문용 발췌
bucket = TokenBucket(rate=2.0, capacity=5)
for i in range(8):
    allowed, info = bucket.consume()      # 요청마다 허용/거부와 remaining, 거부면 retry_after 를 찍는다
time.sleep(1)
allowed, info = bucket.consume()          # 1초 뒤 한 번 더
```

- 여덟 요청 가운데 몇 번째부터 거부되고, 거부될 때 `retry_after` 는 얼마인가?
- 1초 쉰 뒤의 요청은 허용되는가, 그때 남은 토큰은 몇인가?

### 2. 10초당 5회 제한에 일곱 번 연달아 요청하면 (예측)

```python
# 질문용 발췌
limiter = SlidingWindowCounter(limit=5, window_seconds=10)
for i in range(7):
    allowed, info = limiter.is_allowed('user:1')   # 허용/거부와 remaining, 거부면 retry_after
```

- 여섯째와 일곱째 요청의 `retry_after` 는 각각 얼마인가?

### 3. 데코레이터를 붙인 엔드포인트를 다섯 번 부르면 (예측)

```python
# 질문용 발췌
@rate_limit(limit=3, window=10)
def api_endpoint(request):
    return {'status': 200, 'data': 'Success!'}

for i in range(5):
    result = api_endpoint({'ip': '192.168.1.1'})
    status = result.get('status', 200)
    remaining = result.get('headers', {}).get('X-RateLimit-Remaining', '?')
```

- 다섯 번의 `status` 와 `remaining` 은 차례로 무엇인가?

### 4. 초당 10 · 분당 100 · 시간당 1000 다단계 제한에 열두 번 연달아 (예측)
- 같은 키로 시간 간격 없이 `check` 를 열두 번까지 부르며 거부되면 멈출 때, 몇 번째 요청이 어느 단계 때문에 거부되는가?

### 5. 토큰 버킷이 버스트를 허용하는 까닭 (왜)
- `TokenBucket` 이 생성 직후 몰려드는 요청을 곧바로 받아 줄 수 있는 것은 코드의 어느 설계 때문인가?

### 6. 타이머 없이 충전하는 까닭 (왜)
- `TokenBucket` 은 배경 타이머 없이 `consume()` 안에서 `_refill()` 을 부르는데, 이렇게 해도 토큰 수가 맞는 까닭은 무엇인가?

### 7. 슬라이딩 윈도우의 `retry_after` 가 가장 오래된 기록을 기준으로 삼는 까닭 (왜)
- 거부할 때 `retry_after` 를 `oldest + window - now` 로 셈하면 무엇을 알려 주는 것이고, 거부된 요청을 목록에 적지 않는 것이 이 계산에 왜 중요한가?

### 8. `Retry-After` 를 `int()` 로 만드는 방식의 경계 (경계)
- `retry_after` 가 0.5초일 때 원본 데코레이터의 `Retry-After` 헤더 값은 무엇이 되고, 클라이언트에게 어떤 문제가 생기는가?

### 9. 다단계 제한에서 뒤 단계가 거부할 때 (경계)
- 초당 단계는 통과하고 분당 단계에서 거부된 요청은 초당 단계의 기록에 어떤 흔적을 남기는가?

### 10. 메모리 카운터와 여러 대의 서버 (연결)
- 이 코드의 `counters` 를 그대로 둔 채 같은 API 서버를 세 대 띄우면 한 사용자의 제한이 어떻게 달라지고, 원본 팁은 이를 무엇으로 푸는가?

## 실습

### 실습 1. 토큰 버킷 · 슬라이딩 윈도우 · 429 데코레이터 · 다단계 제한 만들기

**만들 것** — 표준 라이브러리만으로 두 가지 속도 제한 알고리즘을 만들고, 그것으로 429 를 돌려주는 데코레이터와 다단계 제한기를 만든 뒤 데모를 찍는 스크립트.

**준비물** — 파이썬 표준 라이브러리만 쓴다. 5단계의 Flask(`flask-limiter`) · Django REST Framework 코드는 실행하지 않고 문자열로 출력만 하므로 설치할 것이 없다.

**요구 조건**

1단계 — 토큰 버킷
1. `TokenBucket(rate, capacity)` 는 토큰을 `capacity` 로 가득 채워 시작하고, 마지막 충전 시각을 기억한다.
2. `_refill()` 은 지난 충전 뒤 흐른 시간 × `rate` 만큼 토큰을 더하되 `capacity` 를 넘지 않게 하고, 충전 시각을 지금으로 바꾼다.
3. `consume(tokens=1)` 은 먼저 충전한 뒤, 토큰이 넉넉하면 빼고 `(True, {'remaining': int(남은 토큰), 'limit', 'reset': 다시 가득 찰 시각 추정})` 을 돌려준다.
4. 모자라면 빼지 않고 `(False, {'remaining': 0, 'limit', 'retry_after': (모자란 토큰 ÷ rate) 를 소수 첫째 자리로 반올림})` 을 돌려준다.
5. 데모: `rate=2.0, capacity=5` 버킷에 8번 연달아 요청해 허용/거부와 남은 토큰(거부면 `retry_after`)을 찍고, 1초 쉰 뒤 한 번 더 요청해 결과를 찍는다.

2단계 — 슬라이딩 윈도우
6. `SlidingWindowCounter(limit, window_seconds)` 는 키별 타임스탬프 목록을 `defaultdict(list)` 로 둔다.
7. `is_allowed(key)` 는 「지금 - 윈도우」보다 오래된 시각을 지우고 남은 개수를 센다.
8. 개수가 `limit` 보다 적으면 지금 시각을 추가하고 `(True, {'remaining': limit - 개수 - 1, 'limit', 'window', 'reset'})` 을 돌려준다.
9. 아니면 시각을 추가하지 않고, 가장 오래된 시각이 윈도우를 벗어날 때까지의 초를 `retry_after` 로 하여 `(False, {'remaining': 0, 'limit', 'retry_after'})` 를 돌려준다.
10. 데모: 10초당 5회 제한에 `'user:1'` 로 7번 요청해 결과를 찍는다.

3단계 — 429 데코레이터
11. `rate_limit(limit=60, window=60, key_func=None)` 는 부를 때 `SlidingWindowCounter` 를 하나 만들고 데코레이터를 돌려준다.
12. 감싼 함수는 `key_func` 가 있으면 그것으로, 없으면 `request.get('ip', 'anonymous')` 로 키를 정한다.
13. 거부면 원래 함수를 부르지 않고 `status` 429 · `error` `'Too Many Requests'` · `retry_after` · `headers`(`X-RateLimit-Limit`, `X-RateLimit-Remaining` `'0'`, `Retry-After` 정수 문자열)를 담은 사전을 돌려준다.
14. 허용이면 원래 함수를 부르고, 결과가 `dict` 면 `headers` 에 `X-RateLimit-Limit` · `X-RateLimit-Remaining` 을 문자열로 넣는다. `@wraps` 로 원래 함수의 메타데이터를 보존한다.
15. 데모: 10초당 3회로 감싼 `api_endpoint` 를 같은 IP 로 5번 불러 `status` 와 `remaining` 을 찍는다.

4단계 — 다단계 제한
16. `MultiTierRateLimiter` 는 초당 10 · 분당 100 · 시간당 1000 의 슬라이딩 윈도우 셋과 이름 `'초당'` · `'분당'` · `'시간당'` 을 갖는다.
17. `check(key)` 는 단계를 차례로 검사해 하나라도 거부하면 곧바로 `(False, "<이름> 제한 초과")`, 모두 통과하면 `(True, "허용")` 을 돌려준다.
18. 데모: `'user:1'` 로 최대 12번 요청하며 허용을 찍고, 거부되면 이유를 찍고 멈춘다.

5단계 — 실무 패턴과 정리
19. `flask-limiter` 설정 · 라우트별 `@limiter.limit` · DRF `REST_FRAMEWORK` throttle 설정 예를 여러 줄 문자열로 출력한다.
20. 핵심 정리 여섯 줄(토큰 버킷 · 슬라이딩 윈도우 · 429 응답 · X-RateLimit · 다단계 · 키)을 출력한다.

**시작 코드**

```python
"""Rate Limiting: 토큰 버킷, 슬라이딩 윈도우, 429 응답"""
import time
from typing import Dict, Tuple
from collections import defaultdict
from functools import wraps

# === 1. 토큰 버킷 ===
print("=== 1. 토큰 버킷 ===")

class TokenBucket:
    def __init__(self, rate: float, capacity: int):
        self.rate = rate
        self.capacity = capacity
        # TODO: 현재 토큰(처음엔 가득)과 마지막 충전 시각

    def _refill(self):
        # TODO: 흐른 시간 × rate 만큼 채우되 capacity 를 넘지 않게, 충전 시각 갱신
        pass

    def consume(self, tokens: int = 1) -> Tuple[bool, dict]:
        # TODO: 충전 → 넉넉하면 빼고 허용 정보 / 모자라면 거부 정보(retry_after)
        pass

bucket = TokenBucket(rate=2.0, capacity=5)
print(f"설정: rate=2/s, capacity=5")
for i in range(8):
    allowed, info = None, {}  # TODO: 버킷에 토큰 하나를 청한다
    status = "허용" if allowed else "거부"
    print(f"  요청 {i+1}: {status} (남은 토큰: {info['remaining']})")
    if not allowed:
        print(f"         retry_after: {info['retry_after']}s")

# TODO: 1초 쉬고 한 번 더 청한다
allowed, info = None, {}
print(f"  1초 후: {'허용' if allowed else '거부'} (남은: {info['remaining']})")

# === 2. 슬라이딩 윈도우 ===
print("\n=== 2. 슬라이딩 윈도우 ===")

class SlidingWindowCounter:
    def __init__(self, limit: int, window_seconds: int):
        self.limit = limit
        self.window = window_seconds
        # TODO: 키 → 타임스탬프 목록

    def is_allowed(self, key: str) -> Tuple[bool, dict]:
        # TODO: 오래된 시각 정리 → 개수 판정 → 허용(시각 추가) / 거부(retry_after)
        pass

limiter = SlidingWindowCounter(limit=5, window_seconds=10)
print(f"설정: 10초당 5회")
for i in range(7):
    allowed, info = None, {}  # TODO: 'user:1' 로 판정
    status = "허용" if allowed else "거부"
    print(f"  요청 {i+1}: {status} (남은: {info['remaining']})")
    if not allowed:
        print(f"         retry_after: {info['retry_after']}s")

# === 3. Rate Limit 데코레이터 ===
print("\n=== 3. Rate Limit 데코레이터 ===")

rate_limiters: Dict[str, SlidingWindowCounter] = {}

def rate_limit(limit: int = 60, window: int = 60, key_func=None):
    # TODO: 제한기 하나를 만들고, 키 결정 → 판정 → 429 또는 원래 함수 + 헤더
    pass

# TODO: 10초당 3회로 감싼다
def api_endpoint(request):
    return {'status': 200, 'data': 'Success!'}

print("데코레이터 테스트 (3회/10초):")
for i in range(5):
    result = api_endpoint({'ip': '192.168.1.1'})
    status = result.get('status', 200)
    remaining = result.get('headers', {}).get('X-RateLimit-Remaining', '?')
    print(f"  요청 {i+1}: status={status}, remaining={remaining}")

# === 4. 다단계 Rate Limiting ===
print("\n=== 4. 다단계 Rate Limiting ===")

class MultiTierRateLimiter:
    def __init__(self):
        # TODO: 초당 10 · 분당 100 · 시간당 1000 단계와 이름
        pass

    def check(self, key: str) -> Tuple[bool, str]:
        # TODO: 단계를 차례로 검사, 하나라도 거부면 즉시 이유와 함께 거부
        pass

multi = MultiTierRateLimiter()
for i in range(12):
    allowed, msg = multi.check('user:1')
    if not allowed:
        print(f"  요청 {i+1}: 거부 - {msg}")
        break
    else:
        print(f"  요청 {i+1}: 허용")

# === 5. 실무 패턴 ===
print("\n=== 5. 실무 구현 패턴 ===")
# TODO: flask-limiter 설정 · 라우트별 제한 · DRF throttle 설정 예를 여러 줄 문자열로 출력

print("=== 핵심 정리 ===")
print("토큰 버킷:   버스트 허용, 일정 속도 충전")
print("슬라이딩 윈도우: 정확한 윈도우, 경계 문제 없음")
print("429 응답:    Too Many Requests + Retry-After 헤더")
print("X-RateLimit: Limit, Remaining, Reset 헤더")
print("다단계:      초/분/시간 단위 중첩 적용")
print("키:          IP, 사용자 ID, API 키 등으로 식별")
```

**확인 방법** — `python api-rate-limit.py` 로 돌려, 토큰 버킷은 다섯 번 허용 뒤 거부, 슬라이딩 윈도우는 여섯째부터 거부, 데코레이터는 넷째부터 `status=429`, 다단계는 열한째에서 「초당 제한 초과」로 멈추는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
