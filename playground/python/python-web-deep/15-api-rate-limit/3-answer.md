# python/python-web-deep/15 — Rate Limiting: 토큰 버킷과 슬라이딩 윈도우 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 여섯째부터 거부되고 0.5초를 기다리라 한다 — 1초 뒤에는 허용, 남은 1

**출력**

```text
  요청 1: 허용 (남은 토큰: 4)
  요청 2: 허용 (남은 토큰: 3)
  요청 3: 허용 (남은 토큰: 2)
  요청 4: 허용 (남은 토큰: 1)
  요청 5: 허용 (남은 토큰: 0)
  요청 6: 거부 (남은 토큰: 0)
         retry_after: 0.5s
  요청 7: 거부 (남은 토큰: 0)
         retry_after: 0.5s
  요청 8: 거부 (남은 토큰: 0)
         retry_after: 0.5s
  1초 후: 허용 (남은: 1)
```

**왜 그런가**
- 버킷은 5개로 가득 차서 시작하므로 처음 다섯 요청은 곧바로 허용된다.
- 요청 사이 경과 시간이 거의 0 이라 충전량도 거의 0 이다.
- 여섯째에서 토큰은 1 보다 적으므로 거부되고, `retry_after = (1 - 거의 0) / 2 ≈ 0.5` 다.
- 거부는 토큰을 빼지 않으므로 일곱째 · 여덟째도 같은 값이다.
- 1초 쉬면 `1 × 2 = 2` 개가 쌓이고, 하나를 써서 1 이 남는다.
- 근거: 2-summary 「동작 방식 (1)」, 「구현 세부사항 대 언어 보장」.

### 2. 둘 다 10.0초

**출력**

```text
  요청 1: 허용 (남은: 4)
  요청 2: 허용 (남은: 3)
  요청 3: 허용 (남은: 2)
  요청 4: 허용 (남은: 1)
  요청 5: 허용 (남은: 0)
  요청 6: 거부 (남은: 0)
         retry_after: 10.0s
  요청 7: 거부 (남은: 0)
         retry_after: 10.0s
```

**왜 그런가**
- 다섯 요청이 허용되며 목록에 시각 다섯 개가 쌓인다.
- 여섯째는 개수가 5 라 거부되고, `retry_after = oldest + 10 - now` 에서 `oldest` 와 `now` 의 차가 거의 0 이므로 약 10 이 되고 반올림해 10.0 이다.
- 거부된 요청은 목록에 적히지 않아 `oldest` 가 그대로이므로 일곱째도 10.0 이다.
- 근거: 2-summary 「동작 방식 (2)」.

### 3. 200 · 200 · 200 · 429 · 429, remaining 은 2 · 1 · 0 · 0 · 0

**출력**

```text
  요청 1: status=200, remaining=2
  요청 2: status=200, remaining=1
  요청 3: status=200, remaining=0
  요청 4: status=429, remaining=0
  요청 5: status=429, remaining=0
```

**왜 그런가**
- 허용된 세 번은 원래 함수의 결과에 `X-RateLimit-Remaining` 이 `limit - current_count - 1` 로 붙는다.
- 넷째부터는 같은 IP 키의 목록에 이미 3개가 있어 거부되고, 429 사전의 헤더가 `X-RateLimit-Remaining: '0'` 이다.
- 근거: 2-summary 「동작 방식 (3)」.

### 4. 열한째 요청이 「초당」 단계에서 거부된다

**출력**

```text
  요청 1: 허용
  요청 2: 허용
  요청 3: 허용
  요청 4: 허용
  요청 5: 허용
  요청 6: 허용
  요청 7: 허용
  요청 8: 허용
  요청 9: 허용
  요청 10: 허용
  요청 11: 거부 - 초당 제한 초과
```

**왜 그런가**
- 첫 단계는 1초 윈도우에 10번 제한이다.
- 요청이 간격 없이 이어지므로 열 번이 모두 1초 안에 들어가고, 열한째에서 첫 단계가 거부한다.
- 첫 단계에서 거부되면 분당 · 시간당 단계는 불리지 않는다.
- 이 결과는 열 번이 1초 안에 끝났다는 데 기댄다.
- 근거: 2-summary 「동작 방식 (4)」, 「구현 세부사항 대 언어 보장」.

### 5. 처음부터 토큰을 `capacity` 만큼 채워 두기 때문이다

`__init__` 에서 `self.tokens = capacity` 로 가득 채워 시작한다.
그래서 충전을 기다리지 않고 `capacity` 번까지 곧바로 허용된다.
또 `capacity` 는 충전의 상한(`min(capacity, …)`)이기도 해서, 오래 쉰 뒤에도 한꺼번에 받을 수 있는 양이 `capacity` 로 묶인다.
근거: 2-summary 「동작 방식 (1)」.

### 6. 토큰은 흐른 시간에만 비례해 늘어나므로, 쓸 때 몰아서 더해도 결과가 같다

충전량은 「흐른 시간 × `rate`」로 정해진다.
그러니 0.1초마다 조금씩 더하든, 쓰는 순간에 마지막 충전 뒤 흐른 시간만큼 한 번에 더하든 값이 같다(상한 `capacity` 로 자르는 것도 같다).
`last_refill` 을 매번 지금으로 바꾸므로 같은 시간이 두 번 더해지지도 않는다.
이것이 lazy refill 이고, 타이머 없이 객체 하나로 충분하다.
근거: 2-summary 「동작 방식 (1)」.

### 7. 「다음 자리가 나는 시각까지 남은 시간」이고, 거부를 적으면 그 시각이 밀린다

목록의 맨 앞은 가장 오래된 허용 요청이다.
그 요청이 윈도우를 벗어나는 순간(`oldest + window`)에 자리가 하나 비므로, 거기서 지금을 뺀 것이 다시 시도할 수 있는 최소 대기 시간이다.
거부된 요청까지 목록에 적으면 거부가 이어질 때마다 목록이 차서 판정이 계속 거부로 이어지고, 실제로 처리하지 않은 요청이 제한을 갉아먹는다.
근거: 2-summary 「동작 방식 (2)」.

### 8. 헤더가 `'0'` 이 되어 「곧바로 다시 보내라」로 읽힌다

데코레이터는 `str(int(info['retry_after']))` 로 헤더를 만들고, `int()` 는 소수점 아래를 버린다.
0.5 는 0 이 되므로 클라이언트가 그대로 따르면 곧장 재시도하고 또 거부된다.
올림을 쓰면 피할 수 있다(원본에 근거 없음 — 추론).
근거: 2-summary 「어디서 틀리나 2」.

### 9. 처리되지 않은 요청의 시각이 초당 단계에 남는다

`check` 는 단계를 차례로 부르고, 초당 단계의 `is_allowed` 는 허용하면서 지금 시각을 목록에 적는다.
그 뒤 분당 단계가 거부해도 초당 단계의 기록은 지워지지 않는다.
그래서 초당 단계는 실제 처리량보다 빨리 찬다.
근거: 2-summary 「동작 방식 (4)」, 「어디서 틀리나 5」.

### 10. 서버마다 따로 세어 제한이 서버 수만큼 느슨해진다 — 원본 팁은 Redis 로 푼다

`counters` 는 각 파이썬 프로세스의 메모리에 있으므로 세 서버가 저마다 따로 센다.
요청이 서버들에 나뉘어 가면 한 사용자가 최대 세 배까지 통과할 수 있다.
원본 팁은 「Redis 를 사용하면 분산 환경에서도 일관된 제한이 가능하다」고 하고, 원본 주석은 실무에서 Redis(Sorted Set)를 함께 쓴다고 적는다.
근거: 2-summary 「동작 방식 (5)」, 「어디서 틀리나 7」.

## 실습 정답

### 실습 1. 토큰 버킷 · 슬라이딩 윈도우 · 429 데코레이터 · 다단계 제한 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 가득 채워 시작, 충전 시각 기억 | `TokenBucket.__init__` 의 `self.tokens = capacity`, `self.last_refill = time.time()` |
| 2. 흐른 시간 × rate 충전, 상한 | `_refill` 의 `elapsed * self.rate`, `min(self.capacity, …)` |
| 3. 넉넉하면 빼고 허용 정보 | `consume` 의 `self.tokens -= tokens`, `'remaining': int(self.tokens)`, `'reset'` |
| 4. 모자라면 거부와 `retry_after` | `consume` 의 `(tokens - self.tokens) / self.rate`, `round(retry_after, 1)` |
| 5. 토큰 버킷 데모 | `bucket = TokenBucket(rate=2.0, capacity=5)`, `for i in range(8)`, `time.sleep(1)` |
| 6. 키별 타임스탬프 목록 | `SlidingWindowCounter.__init__` 의 `defaultdict(list)` |
| 7. 오래된 시각 정리 | `is_allowed` 의 `ts > window_start` 리스트 내포 |
| 8. 허용이면 시각 추가 | `self.counters[key].append(now)`, `self.limit - current_count - 1` |
| 9. 거부면 가장 오래된 시각 기준 대기 | `oldest = self.counters[key][0]`, `oldest + self.window - now` |
| 10. 슬라이딩 윈도우 데모 | `limiter = SlidingWindowCounter(limit=5, window_seconds=10)`, `range(7)` |
| 11. 팩토리에서 제한기 생성 | `rate_limit` 안의 `limiter = SlidingWindowCounter(...)` |
| 12. 키 결정 | `wrapper` 의 `key_func(request)` / `request.get('ip', 'anonymous')` |
| 13. 429 응답 | `wrapper` 의 `'status': 429` 사전과 `headers` |
| 14. 허용 시 헤더 추가, `@wraps` | `isinstance(result, dict)`, `result.setdefault('headers', {})`, `@wraps(func)` |
| 15. 데코레이터 데모 | `@rate_limit(limit=3, window=10)`, `api_endpoint`, `range(5)` |
| 16. 세 단계와 이름 | `MultiTierRateLimiter.__init__` 의 `self.tiers`, `self.tier_names` |
| 17. 차례 검사, 즉시 거부 | `check` 의 `zip(self.tiers, self.tier_names)`, `return False, f"{name} 제한 초과"` |
| 18. 다단계 데모 | `multi = MultiTierRateLimiter()`, `range(12)`, `break` |
| 19. 실무 패턴 출력 | `print("""…flask_limiter…REST_FRAMEWORK…""")` |
| 20. 핵심 정리 출력 | `print("=== 핵심 정리 ===")` 아래 여섯 줄 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-web-deep/reference/api-rate-limit.py`

```python
# [웹 프레임워크 심화] Rate Limiting: 토큰 버킷과 슬라이딩 윈도우
# 설명: 토큰 버킷, 슬라이딩 윈도우 알고리즘으로 API 속도 제한, 429 응답
# 팁: Rate Limiting은 API 남용 방지의 핵심이다. 토큰 버킷은 버스트를 허용하며, 슬라이딩 윈도우는 정확한 시간 윈도우를 보장한다. 429 응답에는 반드시 Retry-After와 X-RateLimit 헤더를 포함해야 한다. Redis를 사용하면 분산 환경에서도 일관된 제한이 가능하다.

"""Rate Limiting: 토큰 버킷, 슬라이딩 윈도우, 429 응답"""
# time: 토큰 충전 시각/윈도우 경계 계산용
import time
# 타입 힌트
from typing import Dict, Tuple
# defaultdict: 키별 타임스탬프 리스트를 자동 초기화
from collections import defaultdict
# wraps: 데코레이터에서 원본 함수 메타데이터 보존
from functools import wraps

# === 1. 토큰 버킷 알고리즘 ===
print("=== 1. 토큰 버킷 ===")

# 토큰 버킷: 누수 버킷의 반대 — 버스트 허용 패턴
class TokenBucket:
    """토큰 버킷: 일정 속도로 토큰 충전, 요청 시 토큰 소비.
    버스트 트래픽 허용."""

    # 초기화: 충전 속도, 최대 용량
    def __init__(self, rate: float, capacity: int):
        """
        rate: 초당 토큰 충전 수
        capacity: 버킷 최대 용량 (최대 버스트)
        """
        self.rate = rate
        self.capacity = capacity
        # 현재 토큰: 초기에는 가득 (버스트 즉시 허용)
        self.tokens = capacity  # 시작 시 가득 참
        # 마지막 충전 시각
        self.last_refill = time.time()

    # 내부 메서드: 경과 시간만큼 토큰 충전 (lazy refill)
    def _refill(self):
        """경과 시간에 따라 토큰 충전"""
        now = time.time()
        # 마지막 충전 이후 경과 시간(초)
        elapsed = now - self.last_refill
        # 충전될 토큰 수 = 경과 시간 × rate
        new_tokens = elapsed * self.rate
        # capacity를 초과하지 않도록 min 처리
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_refill = now

    # 토큰 소비: 요청 시 호출
    def consume(self, tokens: int = 1) -> Tuple[bool, dict]:
        """토큰 소비 시도. (허용여부, 정보) 반환."""
        # 먼저 충전 후 잔량 확인
        self._refill()

        if self.tokens >= tokens:
            # 충분 → 소비하고 허용
            self.tokens -= tokens
            return True, {
                'remaining': int(self.tokens),
                'limit': self.capacity,
                # reset: 버킷이 다시 가득 찰 시각 추정
                'reset': int(self.last_refill + (self.capacity - self.tokens) / self.rate)
            }
        else:
            # 부족 → 거부, retry_after 계산 (필요한 토큰을 얻을 시간)
            retry_after = (tokens - self.tokens) / self.rate
            return False, {
                'remaining': 0,
                'limit': self.capacity,
                'retry_after': round(retry_after, 1)
            }

# 데모: 초당 2개, 최대 5개 버스트
bucket = TokenBucket(rate=2.0, capacity=5)  # 초당 2개, 최대 5개 버스트

print(f"설정: rate=2/s, capacity=5")
# 8회 연속 호출 — 처음 5개는 허용, 이후는 거부될 것
for i in range(8):
    allowed, info = bucket.consume()
    status = "허용" if allowed else "거부"
    print(f"  요청 {i+1}: {status} (남은 토큰: {info['remaining']})")
    if not allowed:
        print(f"         retry_after: {info['retry_after']}s")

# 잠시 대기 후 토큰 충전
time.sleep(1)
allowed, info = bucket.consume()
print(f"  1초 후: {'허용' if allowed else '거부'} (남은: {info['remaining']})")

# === 2. 슬라이딩 윈도우 알고리즘 ===
print("\n=== 2. 슬라이딩 윈도우 ===")

# 슬라이딩 윈도우: 정확한 시간 범위 내 요청 수 카운트
class SlidingWindowCounter:
    """슬라이딩 윈도우 카운터: 고정 윈도우의 경계 문제 해결."""

    # 초기화: 제한 횟수, 윈도우 크기
    def __init__(self, limit: int, window_seconds: int):
        self.limit = limit
        self.window = window_seconds
        # 키별 타임스탬프 리스트 (실무에서는 Redis Sorted Set 사용)
        self.counters: Dict[str, list] = defaultdict(list)  # key -> [timestamps]

    # 요청 허용 여부 판정
    def is_allowed(self, key: str) -> Tuple[bool, dict]:
        """요청 허용 여부 확인"""
        now = time.time()
        # 윈도우 시작 시각: 현재 - 윈도우 크기
        window_start = now - self.window

        # 윈도우 밖의 타임스탬프 제거 (정리)
        self.counters[key] = [
            ts for ts in self.counters[key] if ts > window_start
        ]

        # 현재 윈도우 내 요청 수
        current_count = len(self.counters[key])

        if current_count < self.limit:
            # 허용: 현재 시각 추가
            self.counters[key].append(now)
            return True, {
                'remaining': self.limit - current_count - 1,
                'limit': self.limit,
                'window': self.window,
                'reset': int(window_start + self.window)
            }
        else:
            # 거부: 가장 오래된 요청이 윈도우를 벗어날 시점까지 대기
            oldest = self.counters[key][0]
            retry_after = oldest + self.window - now
            return False, {
                'remaining': 0,
                'limit': self.limit,
                'retry_after': round(retry_after, 1)
            }

# 데모: 10초당 5회 제한
limiter = SlidingWindowCounter(limit=5, window_seconds=10)

print(f"설정: 10초당 5회")
# 7회 호출 — 6번째부터 거부될 것
for i in range(7):
    allowed, info = limiter.is_allowed('user:1')
    status = "허용" if allowed else "거부"
    print(f"  요청 {i+1}: {status} (남은: {info['remaining']})")
    if not allowed:
        print(f"         retry_after: {info['retry_after']}s")

# === 3. Rate Limit 데코레이터 ===
print("\n=== 3. Rate Limit 데코레이터 ===")

# 전역 limiter 저장소 (실무에서는 Redis 단일 인스턴스 공유)
rate_limiters: Dict[str, SlidingWindowCounter] = {}

# Rate Limit 데코레이터 팩토리
def rate_limit(limit: int = 60, window: int = 60, key_func=None):
    """Rate Limit 데코레이터
    limit: 윈도우 당 최대 요청 수
    window: 윈도우 크기 (초)
    key_func: 요청에서 키 추출 함수
    """
    # 데코레이터마다 별도 limiter 인스턴스 생성
    limiter = SlidingWindowCounter(limit=limit, window_seconds=window)

    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            # 키 결정 (IP, 사용자 ID 등) — 분산 환경에서는 Redis 키로 사용
            if key_func:
                key = key_func(request)
            else:
                key = request.get('ip', 'anonymous')

            # 허용 여부 판정
            allowed, info = limiter.is_allowed(key)

            if not allowed:
                # 429 Too Many Requests 응답 (표준 헤더 포함)
                return {
                    'status': 429,
                    'error': 'Too Many Requests',
                    'retry_after': info['retry_after'],
                    'headers': {
                        'X-RateLimit-Limit': str(info['limit']),
                        'X-RateLimit-Remaining': '0',
                        'Retry-After': str(int(info['retry_after'])),
                    }
                }

            # 정상 처리
            result = func(request, *args, **kwargs)
            # 응답에 Rate Limit 헤더 추가 (클라이언트에 잔량 통지)
            if isinstance(result, dict):
                result.setdefault('headers', {})
                result['headers']['X-RateLimit-Limit'] = str(info['limit'])
                result['headers']['X-RateLimit-Remaining'] = str(info['remaining'])
            return result

        return wrapper
    return decorator

# 데코레이터 적용 예시: 10초당 3회
@rate_limit(limit=3, window=10)
def api_endpoint(request):
    return {'status': 200, 'data': 'Success!'}

print("데코레이터 테스트 (3회/10초):")
# 5번 요청 — 4, 5번째는 429
for i in range(5):
    result = api_endpoint({'ip': '192.168.1.1'})
    status = result.get('status', 200)
    remaining = result.get('headers', {}).get('X-RateLimit-Remaining', '?')
    print(f"  요청 {i+1}: status={status}, remaining={remaining}")

# === 4. 다단계 Rate Limiting ===
print("\n=== 4. 다단계 Rate Limiting ===")

# 다단계 제한: 짧은/긴 윈도우를 동시에 적용 (실무에서 흔한 패턴)
class MultiTierRateLimiter:
    """여러 레벨의 Rate Limit 적용"""
    def __init__(self):
        # 초/분/시간 3단계 제한
        self.tiers = [
            SlidingWindowCounter(limit=10, window_seconds=1),    # 초당 10
            SlidingWindowCounter(limit=100, window_seconds=60),  # 분당 100
            SlidingWindowCounter(limit=1000, window_seconds=3600), # 시간당 1000
        ]
        self.tier_names = ['초당', '분당', '시간당']

    # 모든 티어 통과해야 허용
    def check(self, key: str) -> Tuple[bool, str]:
        for tier, name in zip(self.tiers, self.tier_names):
            allowed, info = tier.is_allowed(key)
            if not allowed:
                # 한 티어라도 초과하면 즉시 거부
                return False, f"{name} 제한 초과"
        return True, "허용"

# 다단계 데모
multi = MultiTierRateLimiter()
for i in range(12):
    allowed, msg = multi.check('user:1')
    if not allowed:
        # 11회째쯤 초당 제한 초과 예상
        print(f"  요청 {i+1}: 거부 - {msg}")
        break
    else:
        print(f"  요청 {i+1}: 허용")

# === 5. 실무 패턴 ===
print("\n=== 5. 실무 구현 패턴 ===")
# Flask/Django 실무 예제 (분산 환경에서는 Redis 백엔드 사용)
print("""
# Flask + flask-limiter
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=['200 per day', '50 per hour']
)

@app.route('/api/search')
@limiter.limit('10 per minute')  # 추가 제한
def search():
    return jsonify(results=[])

@app.route('/api/upload')
@limiter.limit('5 per minute', key_func=lambda: current_user.id)
def upload():
    return jsonify(status='ok')

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day',
    }
}
""")

print("=== 핵심 정리 ===")
print("토큰 버킷:   버스트 허용, 일정 속도 충전")
print("슬라이딩 윈도우: 정확한 윈도우, 경계 문제 없음")
print("429 응답:    Too Many Requests + Retry-After 헤더")
print("X-RateLimit: Limit, Remaining, Reset 헤더")
print("다단계:      초/분/시간 단위 중첩 적용")
print("키:          IP, 사용자 ID, API 키 등으로 식별")
```

**실행 결과** — 원본 예제(`component`)를 실제로 돌린 출력이다. 환경 `Python 3.12.3` · 2026-11-28 · exit 0 · 두 번 돌려 출력이 같았다.

````text
$ python3 -I example.py
=== 1. 토큰 버킷 ===
설정: rate=2/s, capacity=5
  요청 1: 허용 (남은 토큰: 4)
  요청 2: 허용 (남은 토큰: 3)
  요청 3: 허용 (남은 토큰: 2)
  요청 4: 허용 (남은 토큰: 1)
  요청 5: 허용 (남은 토큰: 0)
  요청 6: 거부 (남은 토큰: 0)
         retry_after: 0.5s
  요청 7: 거부 (남은 토큰: 0)
         retry_after: 0.5s
  요청 8: 거부 (남은 토큰: 0)
         retry_after: 0.5s
  1초 후: 허용 (남은: 1)

=== 2. 슬라이딩 윈도우 ===
설정: 10초당 5회
  요청 1: 허용 (남은: 4)
  요청 2: 허용 (남은: 3)
  요청 3: 허용 (남은: 2)
  요청 4: 허용 (남은: 1)
  요청 5: 허용 (남은: 0)
  요청 6: 거부 (남은: 0)
         retry_after: 10.0s
  요청 7: 거부 (남은: 0)
         retry_after: 10.0s

=== 3. Rate Limit 데코레이터 ===
데코레이터 테스트 (3회/10초):
  요청 1: status=200, remaining=2
  요청 2: status=200, remaining=1
  요청 3: status=200, remaining=0
  요청 4: status=429, remaining=0
  요청 5: status=429, remaining=0

=== 4. 다단계 Rate Limiting ===
  요청 1: 허용
  요청 2: 허용
  요청 3: 허용
  요청 4: 허용
  요청 5: 허용
  요청 6: 허용
  요청 7: 허용
  요청 8: 허용
  요청 9: 허용
  요청 10: 허용
  요청 11: 거부 - 초당 제한 초과

=== 5. 실무 구현 패턴 ===

# Flask + flask-limiter
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=['200 per day', '50 per hour']
)

@app.route('/api/search')
@limiter.limit('10 per minute')  # 추가 제한
def search():
    return jsonify(results=[])

@app.route('/api/upload')
@limiter.limit('5 per minute', key_func=lambda: current_user.id)
def upload():
    return jsonify(status='ok')

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day',
    }
}

=== 핵심 정리 ===
토큰 버킷:   버스트 허용, 일정 속도 충전
슬라이딩 윈도우: 정확한 윈도우, 경계 문제 없음
429 응답:    Too Many Requests + Retry-After 헤더
X-RateLimit: Limit, Remaining, Reset 헤더
다단계:      초/분/시간 단위 중첩 적용
키:          IP, 사용자 ID, API 키 등으로 식별
````

**풀이 요점**
- 토큰 버킷은 가득 찬 채로 시작하고 `consume` 때마다 흐른 시간만큼 몰아서 채운다 — 이것이 버스트 허용과 lazy refill 이다.
- 슬라이딩 윈도우는 허용된 요청의 시각만 적고, 거부는 적지 않으므로 `retry_after` 가 가장 오래된 기록 기준으로 정확히 나온다.
- 데코레이터 팩토리는 부를 때 제한기를 하나 만들어 클로저에 쥐므로, 감싼 엔드포인트마다 제한이 따로 센다.
- 거부 경로는 원래 함수를 부르지 않고 429 사전을 돌려주며, 허용 경로는 결과에 `X-RateLimit-*` 헤더를 붙인다.
- 다단계 제한은 앞 단계부터 검사해 첫 거부에서 멈춘다 — 앞 단계가 허용하며 남긴 기록은 뒤 단계가 거부해도 지워지지 않는다.
- 데모의 출력 수치(0.5s · 10.0s · 11번째)는 요청이 간격 없이 빠르게 이어졌다는 데 기댄 값이다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 원본 예제를 `Python 3.12.3` 에서 2회 돌렸다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
