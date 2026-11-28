# python/python-web-deep/15 — Rate Limiting: 토큰 버킷과 슬라이딩 윈도우 — 정리 (힌트)

> 출처 — study-site 항목 `python/api-rate-limit`(항목 데이터 `data/python/django-flask-deep.json`) · 정답 코드 study-practice `python/python-web-deep/reference/api-rate-limit.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 원본 예제를 `Python 3.12.3` 에서 2회 돌렸다.

## 한눈에 — 쉽게 말하면

**Rate Limiting 은 「놀이기구 입구에서 손님을 세는 직원」이다.**
직원이 손님을 세는 방법은 두 가지다.
첫째, 바구니에 입장권을 담아 두고 손님마다 한 장씩 준다.
바구니는 일정한 빠르기로 다시 채워지고, 정해진 장수 이상은 담기지 않는다.
둘째, 들어간 손님의 입장 시각을 명부에 적는다.
새 손님이 오면 「최근 10초 안에 들어간 사람」만 세어 정원을 넘었는지 본다.
API 서버도 똑같은 구조다.
첫째 방법이 **토큰 버킷**, 둘째 방법이 **슬라이딩 윈도우**다.
정원을 넘은 손님에게 「몇 초 뒤에 다시 오세요」라고 알려 주는 것이 **429 응답과 `Retry-After` 헤더**다.

> **Rate Limiting(속도 제한)** — 한 사용자 · 키가 정해진 시간 안에 보낼 수 있는 요청 수를 묶어 두는 일이다.\
> 예: 「한 IP 는 10초에 5번까지」.

| 비유 | 실체 |
|---|---|
| 손님 | API 요청 |
| 입장권 바구니 | `TokenBucket` 의 `tokens` |
| 바구니를 채우는 빠르기 | `rate`(초당 충전 토큰 수) |
| 바구니 크기 | `capacity`(한꺼번에 받아 줄 수 있는 최대 요청 수) |
| 입장 시각 명부 | `SlidingWindowCounter` 의 `counters[key]`(타임스탬프 목록) |
| 「몇 초 뒤 다시 오세요」 | 429 응답 + `Retry-After` |
| 손님 이름표 | 키(IP · 사용자 ID · API 키) |

```text
 토큰 버킷                         슬라이딩 윈도우
 ┌─────────┐ ← rate 로 채움         명부: [t1, t2, t3, t4, t5]
 │ ● ● ● ● │   capacity 가 상한      지금 - 10초 보다 오래된 줄은 지운다
 └────┬────┘                        남은 줄 수 < limit → 허용 + 지금 시각 추가
      ↓ 요청마다 1개 꺼냄            남은 줄 수 = limit → 거부(429)
 모자라면 거부(429)
```

## 이 주제가 답하려는 질문

1. 요청이 몰릴 때 어떤 규칙으로 허용 · 거부를 가르나 — 토큰 버킷과 슬라이딩 윈도우는 무엇이 다른가?
2. 거부된 클라이언트에게 무엇을 알려 줘야 다시 시도할 수 있나?
3. 제한 로직을 엔드포인트마다 반복하지 않고 어떻게 붙이나?
4. 초 · 분 · 시간 단위 제한을 함께 걸고, 서버가 여러 대일 때도 같은 제한을 지키려면 어떻게 하나?

## 동작 방식

### (1) 토큰 버킷 — 일정 속도로 채우고 요청마다 꺼낸다

**언제 쓰나** — 평소에는 일정한 빠르기를 지키되, 잠깐 몰리는 요청(버스트)은 어느 정도 받아 주고 싶을 때 쓴다.

> **버스트(burst)** — 짧은 순간에 요청이 한꺼번에 몰리는 것이다.\
> 예: 페이지를 열자마자 API 를 5번 연달아 부르는 것.

```text
 TokenBucket(rate=2.0, capacity=5)    ← 시작할 때 tokens = 5 (가득)

 consume() 호출
   │
   ├─ _refill():  elapsed = 지금 - last_refill
   │              tokens = min(capacity, tokens + elapsed * rate)
   │              last_refill = 지금
   │
   ├─ tokens >= 1 ?  ── 예 ──→ tokens -= 1
   │                          (True, {remaining: int(tokens), limit, reset})
   │
   └─ 아니오 ──→ retry_after = (1 - tokens) / rate
                (False, {remaining: 0, limit, retry_after: 소수 첫째 자리 반올림})
```

- 토큰은 생성할 때 `capacity` 만큼 가득 차 있다.
- 그래서 처음 `capacity` 번의 요청은 시간 간격 없이 곧바로 허용된다 — 이것이 「버스트 허용」이다.
- 충전은 타이머가 하지 않는다.
- `consume()` 이 불릴 때마다 `_refill()` 이 「지난 충전 뒤 흐른 시간 × `rate`」만큼 한꺼번에 더한다.
- 이런 방식을 lazy refill(게으른 충전)이라 부른다.
- 더한 결과는 `min(capacity, …)` 로 잘린다 — 오래 쉬어도 `capacity` 보다 많이 쌓이지 않는다.
- 토큰이 모자라면 아무것도 빼지 않고 거부한다.
- `retry_after` 는 「모자란 토큰 수 ÷ 초당 충전 수」, 곧 필요한 토큰이 쌓일 때까지 걸리는 시간이다.
- `rate=2.0` 이고 토큰이 거의 0 이면 1개를 모으는 데 0.5초가 걸린다.
- `tokens` 는 시간에 비례해 늘어나므로 소수다.
- `remaining` 은 그 소수를 `int()` 로 버린 값이다.
- 원본 주석은 토큰 버킷을 「누수 버킷의 반대 — 버스트 허용 패턴」이라고 소개한다.

> **lazy refill** — 정해진 시각마다 채우지 않고, 값을 쓸 때 흐른 시간만큼 몰아서 채우는 방식이다.\
> 예: 3초 만에 `consume()` 이 불리면 그때 `3 × rate` 개를 더한다.

### (2) 슬라이딩 윈도우 — 최근 N초 안의 요청 시각을 센다

**언제 쓰나** — 「어느 순간을 기준으로 잡아도 최근 N초 동안 M번 이하」를 정확히 지키고 싶을 때 쓴다.

```text
 SlidingWindowCounter(limit=5, window_seconds=10)
 counters = defaultdict(list)          ← 키마다 타임스탬프 목록

 is_allowed('user:1') 호출
   │
   ├─ window_start = 지금 - 10
   ├─ counters['user:1'] 에서 ts > window_start 인 것만 남긴다
   ├─ current_count = 남은 개수
   │
   ├─ current_count < 5 ?  ── 예 ──→ 목록에 지금 시각 추가
   │                                (True, {remaining: 5 - current_count - 1, limit, window, reset})
   │
   └─ 아니오 ──→ oldest = 목록[0]
                retry_after = oldest + 10 - 지금
                (False, {remaining: 0, limit, retry_after})
```

- 키(예: `'user:1'`)마다 허용된 요청의 시각을 목록으로 둔다.
- 요청이 올 때마다 「지금 - 윈도우」보다 오래된 시각을 지운다.
- 그래서 세는 범위가 시간을 따라 미끄러진다(sliding).
- 남은 개수가 `limit` 보다 적으면 지금 시각을 적고 허용한다.
- `remaining` 은 「방금 이 요청까지 센 뒤 남은 자리」라서 `limit - current_count - 1` 이다.
- 거부할 때는 지금 시각을 **적지 않는다**.
- 그래서 거부가 여러 번 이어져도 목록의 맨 앞(`oldest`)은 그대로다.
- 목록은 시각 순서대로 쌓이므로 맨 앞이 가장 오래된 요청이다.
- 그 요청이 윈도우 밖으로 나가는 순간 자리가 하나 빈다 — `retry_after = oldest + window - now` 는 그때까지 남은 시간이다.
- 원본 독스트링은 이 방식을 「고정 윈도우의 경계 문제 해결」이라고 소개한다.
- 원본 주석은 실무에서는 이 목록 대신 Redis Sorted Set 을 쓴다고 적는다.

> **슬라이딩 윈도우** — 「지금부터 거슬러 N초」라는 움직이는 구간 안의 요청 수로 판정하는 방식이다.\
> 예: 10초당 5회 제한이면 언제 재도 최근 10초 안의 허용 요청이 5개를 넘지 않는다.

> **`defaultdict(list)`** — 없는 키를 꺼내면 빈 목록을 만들어 넣어 주는 사전이다.\
> 예: 처음 보는 `'user:2'` 도 `counters['user:2']` 가 곧바로 `[]` 다.

### (3) 데코레이터 — 엔드포인트 앞에서 막고 429 를 돌려준다

**언제 쓰나** — 여러 엔드포인트에 저마다 다른 제한을 함수 위 한 줄로 붙이고 싶을 때 쓴다.

```text
 @rate_limit(limit=3, window=10)          ← 바깥 함수: limiter 를 하나 만든다
 def api_endpoint(request): ...

 api_endpoint({'ip': '192.168.1.1'}) 호출
   │
   ├─ key = key_func(request)  또는  request.get('ip', 'anonymous')
   ├─ allowed, info = limiter.is_allowed(key)
   │
   ├─ 거부 → {status: 429, error: 'Too Many Requests', retry_after,
   │          headers: {X-RateLimit-Limit, X-RateLimit-Remaining: '0',
   │                    Retry-After: str(int(retry_after))}}
   │          (원래 함수는 부르지 않는다)
   │
   └─ 허용 → result = 원래 함수(request)
             result 가 dict 면 headers 에 X-RateLimit-Limit, X-RateLimit-Remaining 추가
```

- `rate_limit(...)` 은 데코레이터를 돌려주는 함수(데코레이터 팩토리)다.
- `rate_limit(...)` 이 불릴 때 `SlidingWindowCounter` 를 하나 만든다.
- 그 객체는 `wrapper` 가 닫아 쥐고(클로저) 호출이 끝나도 살아 있다.
- 원본 주석대로 「데코레이터마다 별도 limiter 인스턴스」가 생긴다 — 엔드포인트마다 제한이 따로 센다.
- 키는 `key_func` 를 주면 그 함수가 요청에서 뽑는다.
- `key_func` 를 주지 않으면 `request` 의 `'ip'` 를 쓰고, 없으면 `'anonymous'` 다.
- 거부되면 원래 함수를 부르지 않고 429 사전을 곧바로 돌려준다.
- 허용되면 원래 함수의 결과에 남은 횟수 헤더를 붙여 클라이언트에게 잔량을 알린다.
- `@wraps(func)` 는 `wrapper` 가 원래 함수의 이름 · 독스트링 같은 메타데이터를 이어받게 한다.

> **429 Too Many Requests** — 「요청이 너무 많다」를 뜻하는 HTTP 상태 코드다.\
> 예: 10초에 3번 제한에서 4번째 요청이 받는 응답.

> **`Retry-After`** — 몇 초 뒤에 다시 시도하면 되는지 알려 주는 응답 헤더다.\
> 예: `Retry-After: 10`.

> **`X-RateLimit-*` 헤더** — 제한값(`Limit`) · 남은 횟수(`Remaining`) · 초기화 시각(`Reset`)을 알려 주는 응답 헤더 묶음이다.\
> 예: `X-RateLimit-Remaining: 0`.

> **데코레이터 팩토리** — 인자를 받아 데코레이터를 만들어 돌려주는 함수다.\
> 예: `rate_limit(limit=3, window=10)` 이 돌려준 `decorator` 가 `api_endpoint` 를 감싼다.

### (4) 다단계 제한 — 짧은 윈도우와 긴 윈도우를 겹쳐 건다

**언제 쓰나** — 「순간 폭주」와 「긴 시간 동안의 과다 사용」을 함께 막고 싶을 때 쓴다.

```text
 MultiTierRateLimiter.check('user:1')
   │
   ├─ 초당 10   (window 1)     is_allowed → 거부면 즉시 return (False, "초당 제한 초과")
   ├─ 분당 100  (window 60)    is_allowed → 거부면 즉시 return (False, "분당 제한 초과")
   ├─ 시간당 1000 (window 3600) is_allowed → 거부면 즉시 return (False, "시간당 제한 초과")
   └─ 모두 통과 → (True, "허용")
```

- 세 개의 `SlidingWindowCounter` 를 차례대로 검사한다.
- 하나라도 거부하면 그 자리에서 멈추고 어느 단계에서 막혔는지 알려 준다.
- 모든 단계를 통과해야 허용이다.
- 단계마다 `is_allowed` 는 「허용이면 지금 시각을 적는다」.
- 그래서 앞 단계는 통과하며 시각을 적었는데 뒤 단계가 거부하면, 앞 단계에는 실제로 처리되지 않은 요청이 기록으로 남는다.
- 반대로 앞 단계에서 거부되면 뒤 단계는 아예 불리지 않아 기록이 없다.
- 요청을 시간 간격 없이 연달아 보내면 1초 안에 10번을 넘기는 순간, 곧 11번째에서 「초당」 단계가 먼저 막는다.

### (5) 키와 분산 환경 — 누구를 세나, 어디에 세나

**언제 쓰나** — 제한 단위를 정하고, 서버가 여러 대로 늘어날 때 쓴다.

```text
 요청 ──→ key_func ──→ 'IP' | '사용자 ID' | 'API 키'
                          │
         서버 A 메모리 counters   ← 이 코드의 방식: 서버마다 따로 센다
         서버 B 메모리 counters
                          │
         Redis (한 곳)            ← 팁의 방식: 모든 서버가 같은 숫자를 본다
```

- 원본 핵심 정리대로 키는 IP · 사용자 ID · API 키 등으로 정한다.
- 이 코드의 `counters` 와 `tokens` 는 파이썬 프로세스의 메모리에 있다.
- 서버(또는 프로세스)가 여러 개면 저마다 따로 센다 — 한 사용자가 서버를 옮겨 가며 보내면 제한이 서버 수만큼 느슨해진다.
- 원본 팁은 「Redis 를 사용하면 분산 환경에서도 일관된 제한이 가능하다」고 한다.
- 원본 주석도 「실무에서는 Redis 단일 인스턴스 공유」 · 「분산 환경에서는 Redis 키로 사용」이라고 적는다.
- 실무에서는 Flask 의 `flask-limiter`, Django REST Framework 의 throttle 설정처럼 프레임워크용 도구를 쓴다(원본 5절).

> **Redis** — 여러 서버가 함께 쓰는 메모리 기반 키-값 저장소다.\
> 예: 모든 API 서버가 `ratelimit:user:1` 키 하나를 읽고 쓴다.

> **throttle** — 요청 빈도를 조여 제한하는 일이다. Django REST Framework 는 속도 제한을 이 이름으로 부른다.\
> 예: `AnonRateThrottle`.

## 문법 — 형태와 규칙

```python
# 사용자 ID 로 세는 엔드포인트 — 5초에 2번
@rate_limit(limit=2, window=5, key_func=lambda req: req['user_id'])
def get_profile(request):
    return {'status': 200, 'data': 'profile'}

r = get_profile({'user_id': 'u1'})
print(r['headers']['X-RateLimit-Remaining'])   # 허용이면 남은 횟수 문자열

bucket = TokenBucket(rate=1.0, capacity=3)     # 초당 1개, 한꺼번에 3개까지
ok, info = bucket.consume()                    # (허용 여부, 정보 사전)
```

- `TokenBucket(rate, capacity)` — `rate` 는 초당 충전 토큰 수, `capacity` 는 최대 버스트다.
- `consume(tokens=1)` — 한 요청이 토큰을 여러 개 쓰게 할 수도 있다. 돌려주는 값은 `(bool, dict)` 다.
- `SlidingWindowCounter(limit, window_seconds)` — 윈도우당 최대 요청 수와 윈도우 크기(초)다.
- `is_allowed(key)` — 키별로 판정하고 `(bool, dict)` 를 돌려준다.
- `rate_limit(limit=60, window=60, key_func=None)` — 기본값은 60초에 60번이다.
- 감싸이는 함수의 첫 인자는 `request` 여야 한다(`wrapper(request, *args, **kwargs)`).
- 감싸인 함수가 `dict` 를 돌려줄 때만 헤더가 붙는다(`isinstance(result, dict)`).

정보 사전의 필드는 이렇다.

| 필드 | 허용일 때 | 거부일 때 |
|---|---|---|
| `remaining` | 남은 횟수(토큰 버킷은 `int(tokens)`) | `0` |
| `limit` | `capacity` 또는 `limit` | 같다 |
| `reset` | 정수 시각(유닉스 초) | 없음 |
| `retry_after` | 없음 | 다시 시도까지 초(소수 첫째 자리 반올림) |
| `window` | 슬라이딩 윈도우만 | 없음 |

429 응답의 헤더는 이렇다.

| 헤더 | 값 |
|---|---|
| `X-RateLimit-Limit` | 제한값 문자열 |
| `X-RateLimit-Remaining` | `'0'` |
| `Retry-After` | `str(int(retry_after))` — 정수로 자른 초 |

프레임워크 설정의 꼴(원본 5절)은 이렇다.

- `flask-limiter`: `Limiter(app=app, key_func=get_remote_address, default_limits=['200 per day', '50 per hour'])` 로 기본 제한을 걸고, 라우트마다 `@limiter.limit('10 per minute')` 를 덧붙인다.
- `@limiter.limit('5 per minute', key_func=lambda: current_user.id)` 처럼 라우트별로 키를 바꿀 수 있다.
- Django REST Framework: `REST_FRAMEWORK` 설정의 `DEFAULT_THROTTLE_CLASSES` 에 `AnonRateThrottle` · `UserRateThrottle` 을, `DEFAULT_THROTTLE_RATES` 에 `'anon': '100/day'` · `'user': '1000/day'` 를 둔다.

## 어디서 틀리나

### 1. 429 에 헤더를 빠뜨린다
원본 팁: 429 응답에는 반드시 `Retry-After` 와 `X-RateLimit` 헤더를 넣어야 한다.
헤더가 없으면 클라이언트는 언제 다시 보낼지 몰라 곧바로 재시도를 거듭한다.
원본 핵심 정리는 `X-RateLimit` 을 「Limit, Remaining, Reset」 셋으로 꼽는다.
그런데 원본 데코레이터는 `Reset` 헤더를 넣지 않는다 — 정리와 코드가 어긋난다.

### 2. `Retry-After` 를 `int()` 로 자르면 0 이 될 수 있다
데코레이터는 `str(int(info['retry_after']))` 로 헤더를 만든다.
`int()` 는 소수점 아래를 버린다.
`retry_after` 가 `0.5` 면 헤더는 `'0'` — 「지금 바로 다시 보내라」는 뜻이 된다.
클라이언트가 그대로 따르면 또 거부된다.
올림(`math.ceil`)을 쓰면 이런 일이 없다(원본에 근거 없음 — 추론).

### 3. 슬라이딩 윈도우의 `reset` 은 「지금」이다
원본의 주장 → `'reset': int(window_start + self.window)` 를 초기화 시각으로 돌려준다.
왜 의심스러운가 → `window_start = now - self.window` 이므로 `window_start + self.window` 는 `now` 다.
곧 `reset` 은 언제나 현재 시각(정수로 자른 것)이라 「언제 다시 자리가 나나」를 알려 주지 못한다.
토큰 버킷의 `reset`(`last_refill + (capacity - tokens) / rate`)은 「다시 가득 찰 시각 추정」이라 뜻이 있다.

### 4. 토큰 버킷의 `remaining` 은 소수를 버린 값이다
`tokens` 는 흐른 시간에 비례해 소수로 늘어난다.
`remaining: int(self.tokens)` 는 0.9 개를 0 으로 보여 준다.
`remaining` 이 0 이어도 다음 요청이 곧 허용될 수 있다.

### 5. 다단계 제한은 앞 단계에 「처리 안 된 요청」을 적는다
`check` 는 단계를 차례로 부르고, 각 `is_allowed` 는 허용이면 시각을 적는다.
초당 단계는 허용(기록)했는데 분당 단계가 거부하면, 거부된 요청이 초당 단계 목록에 남는다.
그만큼 앞 단계가 실제보다 빨리 찬다.

### 6. 키가 없으면 모두 한 칸에 몰린다
기본 키는 `request.get('ip', 'anonymous')` 다.
IP 를 얻지 못한 요청은 전부 `'anonymous'` 하나를 함께 쓴다 — 한 명이 넘치면 모두가 막힌다.

### 7. 메모리에 세면 서버마다 따로 센다
원본 팁대로 분산 환경에서는 Redis 처럼 함께 보는 저장소가 필요하다.
또 `counters` 는 키를 지우지 않는다 — 목록은 비워져도 키는 사전에 남아 키 수만큼 자란다.

### 8. 선언만 하고 쓰지 않는 전역 저장소
원본은 `rate_limiters: Dict[str, SlidingWindowCounter] = {}` 를 「전역 limiter 저장소」로 선언한다.
실제로는 아무 데서도 쓰지 않고, limiter 는 데코레이터마다 클로저에 따로 산다.

### 9. `TokenBucket` 은 키를 모른다
`TokenBucket` 은 버킷 하나뿐이다.
사용자마다 따로 제한하려면 키별로 버킷을 만들어 사전에 담아야 한다(원본에 근거 없음 — 추론).

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `time.time()` 이 유닉스 시각(초)을 `float` 로 돌려준다 | 파이썬 표준 라이브러리. 시계의 정밀도는 운영체제에 따라 다르다 |
| 실행 결과의 `retry_after: 0.5s` · `10.0s` | 아무도 보장하지 않는다 — 데모가 연달아 빠르게 돌아 경과 시간이 거의 0 이었기 때문에 나온 값이다 |
| `time.sleep(1)` 뒤 남은 토큰이 1 | 실제로 1초 가까이 쉬었다는 데 기댄다. 쉬는 시간이 정확히 1초라는 보장은 운영체제 스케줄링에 달렸다 (확인 필요) |
| 다단계 데모에서 11번째가 막힌다 | 10번의 요청이 1초 안에 끝났다는 데 기댄다. 원본 주석도 「11회째쯤」이라고 적는다 |
| `defaultdict(list)` 가 없는 키에 빈 목록을 만든다 | 파이썬 표준 라이브러리 `collections` |
| `@wraps` 가 원래 함수의 이름 · 독스트링을 옮긴다 | 파이썬 표준 라이브러리 `functools` |
| 429 의 뜻과 `Retry-After` 헤더 | HTTP 명세 |
| `X-RateLimit-Limit` · `Remaining` · `Reset` 헤더 | 명세가 아니라 업계 관례다 (확인 필요) |
| `flask-limiter` · DRF throttle 설정 문법 | 각 라이브러리. 버전에 따라 다를 수 있다 (확인 필요) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 짧은 몰림은 받아 주고 평균 속도만 지키고 싶다 | 토큰 버킷 | 엄격한 슬라이딩 윈도우 |
| 「최근 N초에 M번」을 정확히 지켜야 한다 | 슬라이딩 윈도우 | 버스트를 크게 잡은 토큰 버킷 |
| 엔드포인트마다 다른 제한을 붙인다 | 데코레이터(`@rate_limit`, `@limiter.limit`) | 함수마다 복사한 판정 코드 |
| 순간 폭주와 장시간 남용을 함께 막는다 | 다단계(초 · 분 · 시간) | 한 단계 제한만 |
| 서버가 여러 대다 | Redis 같은 공유 저장소 | 프로세스 메모리의 `dict` |
| 로그인 사용자별로 공정하게 나눈다 | 사용자 ID · API 키를 키로 | 기본값 `'anonymous'` 에 몰기 |

## 핵심 문장

1. **토큰 버킷은 가득 찬 채로 시작해 일정 속도로 채운다** — 그래서 `capacity` 만큼의 버스트를 허용한다.
2. **슬라이딩 윈도우는 최근 N초 안의 허용 시각만 센다** — 거부된 요청은 적지 않으므로 `retry_after` 는 가장 오래된 기록이 빠질 때까지다.
3. **거부할 때는 429 와 `Retry-After` · `X-RateLimit` 헤더를 함께 준다** — 클라이언트가 언제 다시 보낼지 알게 한다.
4. **데코레이터 팩토리는 엔드포인트마다 제한기를 하나씩 클로저에 쥔다.**
5. **다단계 제한은 모든 단계를 통과해야 허용이고, 여러 서버에서는 Redis 같은 공유 저장소로 센다.**

## 관련 자료

- `api-versioning` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `api-pagination` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `django-middleware` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/python/django-flask-deep.json` 의 `api-rate-limit`

## 용어 풀이

- **Rate Limiting(속도 제한)** — 정해진 시간 안에 받을 요청 수를 묶는 일.
- **throttle** — 요청 빈도를 조이는 일. DRF 에서 속도 제한을 부르는 이름.
- **토큰 버킷** — 일정 속도로 토큰을 채우고 요청마다 꺼내 쓰는 제한 방식.
- **누수 버킷** — 원본 주석이 토큰 버킷의 「반대」로 꼽는 방식.
- **버스트** — 짧은 순간에 요청이 몰리는 것.
- **lazy refill** — 쓸 때 흐른 시간만큼 몰아서 채우는 충전 방식.
- **슬라이딩 윈도우** — 「지금부터 거슬러 N초」라는 움직이는 구간으로 세는 방식.
- **타임스탬프** — 요청이 허용된 시각(`time.time()` 값).
- **키** — 제한을 따로 세는 단위(IP · 사용자 ID · API 키).
- **429 Too Many Requests** — 요청 과다를 알리는 HTTP 상태 코드.
- **`Retry-After`** — 다시 시도까지 기다릴 초를 알리는 헤더.
- **`X-RateLimit-*`** — 제한값 · 남은 횟수 · 초기화 시각을 알리는 헤더 묶음.
- **데코레이터 팩토리** — 인자를 받아 데코레이터를 만드는 함수.
- **클로저** — 바깥 함수의 변수를 쥐고 살아 있는 안쪽 함수.
- **`@wraps`** — 감싼 함수에 원래 함수의 메타데이터를 옮기는 데코레이터.
- **`defaultdict`** — 없는 키에 기본값을 만들어 주는 사전.
- **다단계 제한** — 길이가 다른 윈도우 여러 개를 함께 거는 것.
- **Redis** — 여러 서버가 함께 쓰는 메모리 기반 키-값 저장소.
- **Sorted Set** — Redis 의 점수 순 정렬 집합. 원본 주석이 타임스탬프 목록의 실무 대안으로 꼽는다.

## 더 들어가면

- **고정 윈도우의 경계 문제** — 「매 분 0초에 카운터를 0으로」 하는 고정 윈도우는 59초에 M번, 다음 분 0초에 M번을 보내면 2초 사이에 2M번이 통과한다. 슬라이딩 윈도우는 어느 순간을 기준으로 재도 M번을 넘지 않아 이 문제가 없다 (확인 필요).
- **이름의 갈래** — 이 코드처럼 타임스탬프를 전부 적는 방식을 흔히 「sliding window log」, 이전 윈도우와 현재 윈도우의 카운트를 가중 평균하는 방식을 「sliding window counter」라 따로 부른다. 원본 클래스 이름은 「Counter」지만 동작은 log 쪽이다 (확인 필요).
- **메모리 비용** — log 방식은 키마다 최대 `limit` 개의 시각을 쥔다. 시간당 1000번 같은 큰 제한에서는 키 수 × 1000 개가 쌓인다 (확인 필요).
- **벽시계 대 단조 시계** — `time.time()` 은 시스템 시계를 맞추면 뒤로 가거나 앞으로 뛸 수 있다. 경과 시간만 재려면 `time.monotonic()` 이 안전하다. 다만 Redis 처럼 여러 서버가 시각을 공유할 때는 단조 시계를 쓸 수 없다 (확인 필요).
- **동시성** — 여러 스레드가 같은 `TokenBucket` 이나 `counters` 를 동시에 건드리면 「읽고-판정하고-쓰기」 사이에 끼어들 수 있다. 락으로 감싸거나, Redis 에서는 Lua 스크립트나 트랜잭션으로 한 번에 처리하는 방법이 쓰인다 (확인 필요).
- **누수 버킷** — 요청을 큐에 담고 일정 속도로만 흘려보내 출력 속도를 평탄하게 만드는 방식으로 알려져 있다 (확인 필요).
