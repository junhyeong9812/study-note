# python/python-libraries/14 — HTTPX (비동기 HTTP) — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 원본 `demo_async` 를 `asyncio.run` 으로 돌리면 (예측)

```python
# 질문용 발췌
async def demo_async():
    print("\n=== 비동기 동시 요청 데모 ===")
    results = []
    for i in range(3):
        await asyncio.sleep(0.01)
        results.append({"id": i, "data": f"response_{i}"})
    print(f"동시에 {len(results)}개 요청 완료: {results}")
    return results

asyncio.run(demo_async())
```

- 제목 줄 다음에 찍히는 한 줄은 무엇인가?

### 2. `base_url` 을 준 `Client` 의 상대 경로 요청 (예측)

```python
# 질문용 발췌
with httpx.Client(base_url='https://api.example.com') as client:
    r = client.get('/users')
```

- 이 GET 요청이 실제로 가는 주소는 무엇인가?
- `with` 블록이 끝나면 `client` 는 어떤 상태가 되나?

### 3. 직렬 `await` 셋과 `gather` 셋의 걸리는 시간 (예측)

```python
# 질문용 발췌
async def serial():
    for _ in range(3):
        await asyncio.sleep(0.01)

async def together():
    await asyncio.gather(*[asyncio.sleep(0.01) for _ in range(3)])
```

- `serial()` 과 `together()` 는 각각 대략 얼마쯤 걸리나?

### 4. 반복문에서는 함수형 API 대신 `Client` 를 권하는 까닭 (왜)

- 같은 서버에 `httpx.get` 을 여러 번 부르는 것이 왜 비효율인가?

### 5. `AsyncClient` 를 `async with` 로 여는 까닭 (왜)

- 원본 팁이 `AsyncClient` 를 「반드시」 `async with` 로 쓰라고 하는 이유는 무엇인가?

### 6. `http2=True` 와 큰 응답 받기의 한계 (경계)

- 기본 설치만 한 httpx 에서 `http2=True` 를 쓰려면 무엇이 더 있어야 하나?
- 수 GB 파일을 일반 요청으로 받으면 어디서 깨지고, 무엇으로 바꿔야 하나?

### 7. 느린 API 와 기본 타임아웃 (경계)

- 응답에 수십 초 걸리는 API 를 기본 설정 그대로 부르면 어떤 일이 생길 수 있나?

### 8. `Timeout` 의 `pool` 칸과 `Limits` 의 관계 (연결)

- `max_connections` 가 다 찬 상태에서 새 요청이 오면, `pool` 타임아웃은 무엇을 재나?

### 9. requests 와 httpx 사이에서 고르기 (연결)

- 원본의 비교에 따르면 어떤 조건일 때 httpx 를 고르고, 언제 requests 로도 충분한가?

## 실습

### 실습 1. httpx 사용법 안내문 + 네트워크 없는 비동기 데모

**만들 것** — httpx 의 동기 · 비동기 · 스트리밍 · HTTP/2 · 고급 설정 사용법을 코드 문자열로 차례로 찍고, 중간에 실제로 도는 비동기 데모 하나를 돌리는 스크립트다.

**준비물** — Python 3 표준 라이브러리(`asyncio` · `unittest.mock`)만 있으면 된다. httpx 는 설치하지 않는다 — httpx 코드는 문자열로 찍기만 하고, 네트워크 요청은 `asyncio.sleep` 과 `MagicMock` 으로 흉내 낸 것이다.

**요구 조건**

1단계 — 가짜 응답 헬퍼
1. `mock_response(status=200, json_data=None, text="OK")` 는 `MagicMock` 하나를 만들어 응답처럼 꾸며 돌려준다.
2. 그 객체의 `status_code` 는 `status`, `json()` 의 반환값은 `json_data`(없으면 빈 dict), `text` 는 `text` 다.
3. `headers` 는 JSON 응답을 가정한 dict, `is_success` 는 참이다.

2단계 — 동기 사용 안내
4. `=== httpx 동기 사용 ===` 를 찍은 뒤, 함수형 API(`httpx.get`)로 GET 하고 상태 코드와 JSON 본문을 찍는 예를 문자열로 찍는다.
5. 같은 문자열에 `base_url` 을 준 `httpx.Client` 를 `with` 로 열어 `/users` 에 GET 과 POST(`json=` 본문)를 보내는 예를 담는다.

3단계 — 비동기 사용 안내
6. `=== httpx 비동기 사용 ===` 를 찍은 뒤, `AsyncClient` 를 `async with` 로 열어 `/data` 를 `await` 하고 JSON 을 돌려주는 `fetch_data` 예를 찍는다.
7. 같은 문자열에 URL 셋으로 `client.get` 코루틴 목록을 만들고 `asyncio.gather(*tasks)` 로 모아 JSON 리스트를 돌려주는 `fetch_multiple` 예를 담는다.

4단계 — 실제로 도는 데모
8. `demo_async` 코루틴은 제목을 찍고, 세 번 돌며 매번 `asyncio.sleep(0.01)` 을 기다린 뒤 `{"id": i, "data": "response_i"}` 꼴의 dict 를 리스트에 쌓는다.
9. 다 쌓으면 개수와 리스트를 `동시에 N개 요청 완료: …` 꼴로 찍고 리스트를 돌려준다.
10. `asyncio.run` 으로 `demo_async` 를 돌린다.

5단계 — 스트리밍 · HTTP/2 · 고급 설정 · 비교
11. 스트리밍 안내: `client.stream('GET', url)` 안에서 `aiter_bytes(chunk_size=8192)` 로 받아 파일에 쓰는 `download_large_file`, `aiter_lines()` 로 `data: ` 로 시작하는 줄만 골라 `Event: …` 로 찍는 `stream_events` 예를 찍는다.
12. HTTP/2 안내: 설치 안내 주석, `http2=True` 인 `AsyncClient`, `response.http_version` 을 찍는 예를 찍는다.
13. 고급 설정 안내: connect · read · write · pool 네 칸의 `Timeout`, 두 칸의 `Limits`, 그리고 이 둘과 `base_url` · `headers` · `follow_redirects` 를 넘긴 `AsyncClient` 예를 찍는다.
14. 끝으로 requests 와 httpx 의 비교 세 줄을 찍는다.

**시작 코드**

```python
# 실습: httpx 사용법 안내 + 네트워크 없는 비동기 데모
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

def mock_response(status=200, json_data=None, text="OK"):
    resp = MagicMock()
    # TODO: status_code · json() 의 반환값(없으면 빈 dict) · text 를 채운다
    resp.headers = {"content-type": "application/json"}
    resp.is_success = True
    return resp

print("=== httpx 동기 사용 ===")
print("""
import httpx

# 간단한 요청 (requests와 유사)
# TODO: 함수형 API 로 GET 하고 상태 코드와 JSON 본문을 찍는 세 줄

# Client (Session과 유사 - 커넥션 풀 재사용)
# TODO: base_url 을 준 Client 를 with 로 열고 '/users' 에 GET, POST(json=)
""")

print("=== httpx 비동기 사용 ===")
print("""
import httpx
import asyncio

# TODO: fetch_data — AsyncClient 를 async with 로 열고 '/data' 를 await, JSON 반환

# 동시 요청
# TODO: fetch_multiple — URL 셋 → client.get 코루틴 목록 → asyncio.gather(*tasks) → JSON 리스트
""")

async def demo_async():
    print("\n=== 비동기 동시 요청 데모 ===")
    results = []
    # TODO: 세 번 돌며 asyncio.sleep(0.01) 을 기다리고 {"id": i, "data": f"response_{i}"} 를 쌓는다
    # TODO: "동시에 N개 요청 완료: [...]" 를 찍고 results 를 돌려준다

# TODO: 이벤트 루프로 demo_async 를 돌린다

print("\n=== 스트리밍 ===")
print("""
# 대용량 다운로드 스트리밍
# TODO: download_large_file(url, path) — client.stream('GET', url) + aiter_bytes(chunk_size=8192) → 파일에 쓰기

# 서버 이벤트 스트리밍 (SSE)
# TODO: stream_events() — aiter_lines() 에서 'data: ' 줄만 골라 Event: 뒤에 찍기
""")

print("=== HTTP/2 지원 ===")
print("""
# HTTP/2 활성화 (pip install httpx[http2])
# TODO: http2=True 인 AsyncClient 로 GET 하고 http_version 을 찍는 세 줄
""")

print("=== 고급 설정 ===")
print("""
import httpx
from httpx import Timeout, Limits

# 세밀한 타임아웃
# TODO: connect · read · write · pool 네 칸의 Timeout

# 커넥션 풀 제한
# TODO: max_connections · max_keepalive_connections 의 Limits

# TODO: timeout · limits · base_url · headers · follow_redirects 를 넘긴 AsyncClient
""")

print("=== requests vs httpx 비교 ===")
print("requests: 동기만, 성숙, 넓은 생태계")
print("httpx:    동기+비동기, HTTP/2, requests 호환 API")
print("         비동기가 필요하면 httpx, 아니면 requests도 충분")
```

**확인 방법** — `python httpx_practice.py` 로 돌려, 섹션 제목 여섯 개가 차례로 찍히고 「비동기 동시 요청 데모」 아래에 `동시에 3개 요청 완료:` 와 dict 세 개가 든 리스트가 찍히는지 본다. 3-answer.md 의 실행 결과와 줄 단위로 맞춰 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
