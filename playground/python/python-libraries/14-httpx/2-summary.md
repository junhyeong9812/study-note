# python/python-libraries/14 — HTTPX (비동기 HTTP) — 정리 (힌트)

> 출처 — study-site 항목 `python/httpx`(항목 데이터 `data/python/libraries.json`) · 정답 코드 study-practice `python/python-libraries/reference/httpx.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 원본 예제를 `Python 3.12.3` 에서 2회 돌렸다.

## 한눈에 — 쉽게 말하면

**httpx 는 「전화 한 대로 여러 통화를 돌리는 콜센터 상담원」이다.**
상담원 한 명이 고객 셋에게 전화를 건다.
신호가 가는 동안 손을 놓고 기다리지 않고, 다음 번호를 누른다.
받는 사람이 생기면 그 통화로 돌아간다.
httpx 의 `AsyncClient` 와 `asyncio.gather` 도 똑같은 구조다.
요청을 보내 놓고 응답을 기다리는 동안 다른 요청을 보낸다.

| 비유 | 실체 |
|---|---|
| 상담원 한 명 | 이벤트 루프(스레드 하나) |
| 회사 전화기(회선 묶음) | `httpx.Client` · `httpx.AsyncClient` 의 커넥션 풀 |
| 단축 번호 앞자리 | `base_url` |
| 셋에게 한꺼번에 걸기 | `asyncio.gather(*tasks)` |
| 긴 통화를 받아 적으며 듣기 | `client.stream(...)` + `aiter_bytes` · `aiter_lines` |
| 통화 대기 한도 | `Timeout` |
| 동시에 쓸 수 있는 회선 수 | `Limits` |

```text
  [AsyncClient: 회선 묶음]
        │
        ├── GET /users     ──── 기다리는 동안 ───┐
        ├── GET /posts     ──── 기다리는 동안 ───┤  gather 가 모두 모아
        └── GET /comments  ──── 기다리는 동안 ───┘  응답 리스트로 돌려준다
```

## 이 주제가 답하려는 질문

1. requests 처럼 쓰던 코드를 httpx 로 옮기면 무엇이 같고, 무엇이 새로 생기나?
2. 요청 여러 개를 동시에 보내려면 어떤 객체를 어떤 꼴로 열어야 하나?
3. 응답이 아주 크거나 끝없이 이어질 때 메모리를 지키며 받으려면 어떻게 하나?
4. 타임아웃 · 커넥션 수 · HTTP/2 같은 세부 설정은 어디에 거나?

## 동작 방식

### (1) 함수형 API 와 `Client`

**언제 쓰나** — 한두 번 부르는 간단한 스크립트면 함수형 API, 같은 서버에 여러 번 부르면 `Client` 다.

```text
httpx.get(url)                         with httpx.Client(base_url=B) as client:
   │                                       client.get('/users')   → B + '/users'
   ├ 클라이언트를 새로 만든다                client.post('/users', json={...})
   ├ 요청 → 응답                              │
   └ 클라이언트를 버린다                       └ 같은 커넥션 풀을 다시 쓴다
→ response.status_code, response.json()   → with 블록이 끝나면 닫힌다
```

- `httpx.get` · `httpx.post` 같은 함수형 API 는 requests 와 같은 꼴이다.
- 함수형 API 는 부를 때마다 클라이언트를 새로 만들고 버린다.
- 그래서 여러 번 부르면 비효율이고, 원본은 `Client` 를 권한다.
- `Client` 는 커넥션 풀과 `base_url` 을 공유하는 세션 객체다(requests 의 `Session` 과 비슷하다).
- `base_url` 을 주면 `client.get('/users')` 는 `base_url + path` 로 간다.
- `with` 로 열면 블록이 끝날 때 클라이언트가 닫힌다.

> **커넥션 풀** — 한 번 맺은 연결을 버리지 않고 모아 두었다가 다음 요청에 다시 쓰는 저장소다.\
> 예: 같은 서버에 GET 을 열 번 보내도 연결을 열 번 새로 맺지 않는다.

### (2) `AsyncClient` 와 `async with`

**언제 쓰나** — `async def` 안에서 요청을 보내고, 기다리는 동안 다른 일을 하게 하고 싶을 때다.

```text
async def fetch_data():
    async with httpx.AsyncClient(base_url=B) as client:   ← 들어갈 때 연다
        response = await client.get('/data')             ← 기다리는 동안 루프는 다른 일
        return response.json()
                                                         ← 나갈 때 반드시 닫는다
```

- `AsyncClient` 는 `Client` 의 비동기판이다.
- 요청 메서드(`client.get` 등)는 코루틴을 돌려주므로 `await` 를 붙여야 응답을 얻는다.
- 원본 팁은 「`AsyncClient` 는 반드시 `async with` 로 쓴다」고 한다.
- 까닭은 close 누락을 막기 위해서다 — 블록을 어떻게 빠져나가든(정상 반환이든 예외든) 닫힌다.

> **코루틴** — `async def` 로 만든 함수를 불렀을 때 나오는, 아직 돌지 않은 「멈췄다 이어 갈 수 있는 작업」이다.\
> 예: `client.get(url)` 만 쓰면 응답이 아니라 코루틴이 나온다.

> **`async with`** — 들어갈 때와 나올 때 각각 기다릴 수 있는 정리 작업을 붙이는 문법이다.\
> 예: `async with httpx.AsyncClient() as client:` 는 나올 때 클라이언트를 닫는다.

### (3) `asyncio.gather` 로 동시 요청 — 그리고 직렬 `await` 와의 차이

**언제 쓰나** — 서로 기다릴 필요 없는 요청이 여러 개일 때다.

```text
직렬 (원본 demo_async 의 꼴)            동시 (fetch_multiple 의 꼴)
for i in range(3):                      tasks = [client.get(u) for u in urls]
    await asyncio.sleep(0.01)           responses = await asyncio.gather(*tasks)
                                         
시간 →  [0.01][0.01][0.01]              시간 →  [0.01]
                                                [0.01]   겹쳐서 기다린다
                                                [0.01]
합: 셋을 차례로 기다린다                  합: 가장 긴 하나 정도를 기다린다
```

- `[client.get(url) for url in urls]` 는 코루틴 셋을 만들 뿐, 아직 보내지 않는다.
- `asyncio.gather(*tasks)` 가 셋을 함께 돌리고, 모두 끝나면 응답을 **넣은 차례대로** 리스트로 준다.
- 원본 주석은 이것을 「여러 요청을 동시 실행 → I/O 병렬화」라고 부른다.
- 원본 팁은 「동시 요청이 많으면 `asyncio.gather` + `AsyncClient` 조합이 매우 효과적」이라고 한다.
- 반면 원본의 `demo_async` 는 `for` 안에서 `await asyncio.sleep(0.01)` 를 하나씩 기다린다 — 직렬이다.
- 원본 주석도 「직렬 await 로 흉내(실제로는 gather 로 병렬 가능)」라고 밝힌다.
- 직렬이면 걸리는 시간이 대기 시간의 합에 가깝고, `gather` 면 가장 긴 대기에 가깝다(원본에 근거 없음 — 추론).
- `demo_async` 는 결과 dict 셋을 모아 `동시에 3개 요청 완료: [...]` 를 찍고 리스트를 돌려준다.
- `asyncio.run(demo_async())` 이 이벤트 루프를 만들어 이 코루틴을 끝까지 돌린다.

> **이벤트 루프** — 기다리는 작업들을 붙들고, 준비된 것부터 이어서 돌리는 실행기다.\
> 예: `asyncio.run(main())` 이 루프를 만들고 `main()` 이 끝나면 닫는다.

### (4) 스트리밍 — 큰 응답을 조각으로 받기

**언제 쓰나** — 대용량 파일 다운로드, 서버가 줄 단위로 계속 보내는 이벤트(SSE)를 받을 때다.

```text
async with client.stream('GET', url) as response:
        │
        ├─ aiter_bytes(chunk_size=8192) → [8192바이트][8192바이트]… → f.write(chunk)
        │                                  한 조각씩만 메모리에 머문다
        └─ aiter_lines()                → 'data: hello' → line[6:] → 'hello'
                                          'data: ' 로 시작하는 줄만 골라 Event: 로 찍는다
```

- `client.stream(method, url)` 은 비동기 컨텍스트로 쓰는 응답이다 — 본문을 한꺼번에 읽지 않는다.
- `response.aiter_bytes(chunk_size)` 는 본문을 그 크기의 조각으로 넘겨준다.
- 원본 주석은 이것이 「메모리 사용을 일정하게 유지」한다고 한다.
- 다운로드 예는 파일을 `'wb'`(바이너리 쓰기)로 열고 조각마다 `f.write(chunk)` 한다.
- `response.aiter_lines()` 는 본문을 줄 단위로 넘겨준다 — SSE 처리에 쓴다.
- SSE 예는 `line.startswith('data: ')` 인 줄만 골라, 앞 6글자(`'data: '`)를 잘라 낸 나머지를 찍는다.
- `async for` 로 돌리는 까닭은 다음 조각이 올 때까지 기다려야 하기 때문이다.

> **SSE(Server-Sent Events)** — 서버가 연결을 열어 둔 채 `data: …` 꼴의 줄을 계속 밀어 보내는 방식이다.\
> 예: 알림 피드가 `data: 새 메시지` 줄을 이어서 보낸다.

> **청크** — 큰 데이터를 나눈 한 조각이다.\
> 예: `chunk_size=8192` 면 한 번에 8192바이트씩 받는다.

### (5) HTTP/2

**언제 쓰나** — HTTP/2 를 지원하는 서버와 통신할 때다.

```text
pip install httpx[http2]   → h2 패키지가 함께 깔린다
        │
AsyncClient(http2=True)    → HTTP/2 를 쓰겠다고 켠다
        │
response.http_version      → 실제로 쓴 버전 문자열 (원본 주석: 'HTTP/2')
```

- `http2=True` 옵션을 쓰려면 `httpx[http2]` 를 설치해야 한다.
- 원본 주석에 따르면 이 extras 가 `h2` 패키지를 깐다.
- 원본은 `response.http_version` 이 `'HTTP/2'` 라고 주석을 달았다 — 이 주장의 한계는 「어디서 틀리나」에 적었다.

> **extras** — 패키지 이름 뒤 `[...]` 로 고르는 선택 의존성 묶음이다.\
> 예: `pip install httpx[http2]` 는 httpx 에 HTTP/2 용 의존성을 더한다.

### (6) `Timeout` · `Limits` · 그 밖의 클라이언트 옵션

**언제 쓰나** — 느린 API, 많은 동시 요청, 공통 헤더 · 리다이렉트 처리가 필요할 때다.

```text
Timeout(connect=5.0, read=10.0, write=5.0, pool=10.0)
   연결 맺기   응답 읽기   요청 쓰기   풀에서 빈 연결 기다리기

Limits(max_connections=100, max_keepalive_connections=20)
   동시에 열 수 있는 연결 최대    쉬는 동안에도 살려 둘 연결 수

AsyncClient(timeout=…, limits=…, base_url=…, headers={…}, follow_redirects=True)
```

- `Timeout` 은 connect · read · write · pool 네 칸으로 따로 정할 수 있다(단위는 초).
- `Limits` 는 동시 커넥션 수(`max_connections`)와 keepalive 커넥션 수(`max_keepalive_connections`)를 제어한다.
- 연결이 `max_connections` 까지 다 쓰이면 새 요청은 풀에서 자리가 나길 기다리고, 그 기다림의 한도가 `pool` 타임아웃이다(원본에 근거 없음 — 추론).
- `headers` 에 준 값(예: `Authorization`)은 그 클라이언트의 모든 요청에 붙는다.
- `follow_redirects=True` 면 리다이렉트 응답을 따라간다.
- 원본 주석은 「기본 timeout 은 5초이므로 느린 API 는 명시적 조정이 필요하다」고 경고한다.

> **keepalive** — 응답을 받은 뒤에도 연결을 끊지 않고 다음 요청을 위해 살려 두는 것이다.\
> 예: `max_keepalive_connections=20` 이면 쉬는 연결을 20개까지 보관한다.

### (7) mock 으로 시연하기

**언제 쓰나** — 네트워크 없이 응답 객체의 꼴을 흉내 내고 싶을 때다.

```text
mock_response(status=200, json_data=None, text="OK")
   resp = MagicMock()
   resp.status_code = 200
   resp.json.return_value = json_data or {}   → resp.json() 이 {} 를 돌려준다
   resp.text, resp.headers, resp.is_success 를 채운다
   → 응답처럼 보이는 가짜 객체
```

- `MagicMock` 은 어떤 속성이든 받아 주는 가짜 객체다.
- `resp.json.return_value` 를 정하면 `resp.json()` 을 부를 때 그 값이 나온다.
- `json_data or {}` 라서 `json_data` 를 안 주면 빈 dict 가 나온다.
- 원본 예제의 httpx 코드는 실제로 돌지 않고 문자열로 찍히기만 한다 — 실제로 도는 것은 `demo_async` 하나다.

> **mock** — 진짜 객체 대신 쓰는, 정해 둔 대로만 반응하는 가짜 객체다.\
> 예: `MagicMock().status_code = 200` 으로 응답 흉내를 낸다.

## 문법 — 형태와 규칙

```python
import asyncio
import httpx

async def main():
    async with httpx.AsyncClient(base_url="https://api.example.com",
                                 timeout=httpx.Timeout(connect=5.0, read=10.0, write=5.0, pool=10.0)) as client:
        tasks = [client.get(p) for p in ("/users", "/posts")]
        responses = await asyncio.gather(*tasks)
        return [r.status_code for r in responses]

asyncio.run(main())
```

- 동기: `httpx.get(url)` 또는 `with httpx.Client(...) as client: client.get(path)`.
- 비동기: `async with httpx.AsyncClient(...) as client:` 안에서 `await client.get(path)`.
- 동시 실행: 코루틴 리스트를 만든 뒤 `await asyncio.gather(*tasks)` — 결과는 넣은 차례대로다.
- 응답: `status_code` · `json()` · `text` · `headers` · `is_success` · `http_version`.
- 스트리밍: `async with client.stream('GET', url) as response:` 안에서 `async for chunk in response.aiter_bytes(chunk_size=…)` 또는 `async for line in response.aiter_lines()`.
- POST 본문을 JSON 으로: `client.post('/users', json={'name': 'Alice'})`.
- HTTP/2: `pip install httpx[http2]` 후 `AsyncClient(http2=True)`.
- 설정: `timeout=Timeout(...)` · `limits=Limits(...)` · `base_url=` · `headers=` · `follow_redirects=`.
- 최상위 진입점: `asyncio.run(코루틴)`.

## 어디서 틀리나

### 1. requests 와 「거의」 같다는 말을 「똑같다」로 읽기
원본 팁은 httpx 가 requests 와 거의 동일한 API 를 주면서 async 를 지원한다고 한다.
API 꼴이 비슷해 옮기기 쉽지만, 비동기 쪽은 `AsyncClient` · `await` · `async with` 가 새로 붙는다.

### 2. 반복문에서 함수형 API 부르기
`httpx.get` 은 부를 때마다 클라이언트를 새로 만든다.
같은 서버에 여러 번 부르면 커넥션 풀을 못 쓰고 비효율이 된다 — `Client` 를 쓴다.

### 3. `AsyncClient` 를 `async with` 없이 쓰기
원본 팁은 「반드시 `async with` 로」라고 한다.
그냥 만들어 쓰면 닫는 것을 잊기 쉽다.
원본의 「HTTP/2」·「고급 설정」 조각은 `client = httpx.AsyncClient(...)` 로 만들고 닫지 않는다 — 설정을 보이려는 조각일 뿐 팁대로 쓴 꼴이 아니다.

### 4. `await` 를 하나씩 걸고 「동시」라고 부르기
`demo_async` 는 `for` 안에서 `await` 를 차례로 건다 — 직렬이다.
그런데 찍는 문구는 「동시에 3개 요청 완료」다.
원본의 주장(「동시」) → 의심스러운 까닭: 코드 주석 스스로 「직렬 await 로 흉내」라고 적었고, 동시로 돌리려면 `gather` 가 필요하다.

### 5. `gather` 에 코루틴이 아닌 응답을 넣으려 하기
`tasks = [client.get(url) for url in urls]` 는 아직 `await` 하지 않은 코루틴 리스트여야 한다.
`*tasks` 로 풀어서 넘긴다 — 리스트를 그대로 넘기지 않는다.

### 6. HTTP/2 를 켰는데 패키지를 안 깔기
`http2=True` 는 `httpx[http2]` 설치(원본 주석: `h2` 패키지)가 있어야 쓸 수 있다.

### 7. `http_version` 이 늘 `'HTTP/2'` 라고 믿기
원본 조각의 주석은 `# 'HTTP/2'` 다.
원본의 주장 → 의심스러운 까닭: 버전은 클라이언트만 정하는 것이 아니라 상대 서버도 HTTP/2 를 지원해야 한다(원본에 근거 없음 — 추론).

### 8. 큰 응답을 통째로 읽기
대용량 파일이나 끝없는 이벤트 흐름을 일반 요청으로 받으면 본문 전체를 메모리에 올린다.
`client.stream` + `aiter_bytes` · `aiter_lines` 로 조각 단위로 받는다.

### 9. 기본 타임아웃을 잊기
원본 주석에 따르면 기본 timeout 은 5초다.
느린 API 는 `Timeout` 으로 칸별로 늘려야 한다.

### 10. 모듈 최상위에서 `await` 쓰기
「HTTP/2 지원」 조각의 `response = await client.get(...)` 은 함수 밖에 있다.
보통 `.py` 파일에서는 `await` 가 `async def` 안에서만 쓰일 수 있다 — 조각은 설명용 꼴이다.

### 11. 안 쓰는 import · 헬퍼
원본은 `AsyncMock` · `patch` 를 import 하고 `mock_response` 를 정의하지만 어디서도 부르지 않는다.
시연 틀만 놓아 둔 것이다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `await` 는 `async def` 안에서만 쓴다 · `async with` · `async for` 문법 | Python 언어 |
| `asyncio.gather` 가 결과를 넣은 차례대로 돌려준다 | 표준 라이브러리 `asyncio` |
| `asyncio.run` 이 루프를 만들어 코루틴을 끝까지 돌린다 | 표준 라이브러리 `asyncio` |
| `MagicMock` · `return_value` 의 동작 | 표준 라이브러리 `unittest.mock` |
| 함수형 API 가 호출마다 클라이언트를 새로 만든다 | httpx 라이브러리의 구현 (버전에 따라 다를 수 있음 — 확인 필요) |
| 기본 timeout 이 5초다 | httpx 라이브러리의 기본값 (원본 주석의 주장 · 버전에 따라 다를 수 있음 — 확인 필요) |
| `http2=True` 에 `httpx[http2]`(`h2`)가 필요하다 | httpx 의 패키징 |
| `http_version` 이 `'HTTP/2'` 가 된다 | 클라이언트와 서버의 협상 결과 (원본에 근거 없음 — 추론) |
| `gather` 로 묶으면 빨라진다 | 보장 아님 — 기다림이 I/O 일 때 겹칠 수 있다는 것뿐, 실제 속도는 서버 · 네트워크에 달림 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 동기 스크립트에서 요청 한두 번 | `httpx.get` 또는 requests | 굳이 `AsyncClient` |
| 같은 서버에 요청 여러 번 | `httpx.Client` + `base_url` | 반복문 속 `httpx.get` |
| async 코드 안에서 요청 | `async with httpx.AsyncClient()` | 동기 requests(루프를 막는다 — 원본에 근거 없음 — 추론) |
| 서로 독립인 요청 여러 개 | `asyncio.gather(*tasks)` | `for` 안의 직렬 `await` |
| 대용량 다운로드 · SSE | `client.stream` + `aiter_bytes` · `aiter_lines` | 본문을 통째로 읽기 |
| HTTP/2 서버 | `httpx[http2]` + `http2=True` | 패키지 없이 `http2=True` |
| 느린 API · 동시 연결 제한 | `Timeout` · `Limits` | 기본값에 맡기기 |
| 비동기가 필요 없음 | requests 도 충분(원본의 비교) | — |

## 핵심 문장

1. **httpx 는 requests 와 거의 같은 API 에 비동기 · HTTP/2 를 더한 HTTP 클라이언트다.**
2. **여러 번 부를 때는 커넥션 풀을 공유하는 `Client` · `AsyncClient` 를 쓰고, `AsyncClient` 는 `async with` 로 연다.**
3. **동시 요청은 `asyncio.gather` 로 묶어야 동시다 — `for` 안에서 하나씩 `await` 하면 직렬이다.**
4. **큰 응답은 `client.stream` 과 `aiter_bytes` · `aiter_lines` 로 조각 단위로 받는다.**
5. **세부 동작은 `Timeout`(connect · read · write · pool)과 `Limits` 로 클라이언트에 건다.**

## 관련 자료

- `requests-basics` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `concurrency-patterns` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/python/libraries.json` 의 `httpx`

## 용어 풀이

- **httpx** — 동기 · 비동기를 모두 지원하는 Python HTTP 클라이언트 라이브러리.
- **requests** — 동기 전용의 성숙한 Python HTTP 클라이언트 라이브러리.
- **함수형 API** — `httpx.get(url)` 처럼 클라이언트 없이 바로 부르는 함수.
- **`Client`** — 커넥션 풀과 `base_url` 을 공유하는 동기 세션 객체.
- **`AsyncClient`** — `Client` 의 비동기판.
- **커넥션 풀** — 맺은 연결을 모아 다시 쓰는 저장소.
- **`base_url`** — 클라이언트의 요청 경로 앞에 붙는 공통 주소.
- **코루틴** — `async def` 함수를 불러 나온, 멈췄다 이어 갈 수 있는 작업.
- **`await`** — 코루틴이 끝날 때까지 기다리며 그동안 루프에 제어를 넘기는 키워드.
- **이벤트 루프** — 기다리는 작업 중 준비된 것부터 이어 돌리는 실행기.
- **`asyncio.gather`** — 여러 코루틴을 함께 돌려 결과를 차례대로 모으는 함수.
- **`asyncio.run`** — 루프를 만들어 코루틴 하나를 끝까지 돌리는 진입점.
- **`async with`** — 들어갈 때 · 나올 때 비동기 정리 작업을 붙이는 문법.
- **`async for`** — 다음 값을 기다려 가며 도는 반복.
- **스트리밍** — 응답 본문을 한꺼번에가 아니라 조각으로 받는 것.
- **청크** — 나눠 받은 한 조각.
- **SSE** — 서버가 `data: …` 줄을 계속 밀어 보내는 방식.
- **HTTP/2** — HTTP 의 2판 프로토콜.
- **extras** — `패키지[이름]` 꼴로 고르는 선택 의존성.
- **`Timeout`** — connect · read · write · pool 별 제한 시간.
- **`Limits`** — 동시 커넥션 · keepalive 커넥션 수 제한.
- **keepalive** — 응답 뒤에도 연결을 살려 두는 것.
- **`follow_redirects`** — 리다이렉트 응답을 따라갈지 정하는 옵션.
- **mock** — 정해 둔 대로만 반응하는 가짜 객체.
- **`MagicMock`** — 어떤 속성 · 호출이든 받아 주는 mock.

## 더 들어가면

- HTTP/2 는 한 연결 위에 여러 요청을 겹쳐 보내는 다중화를 지원한다 — 동시 요청이 많을 때 연결 수를 줄일 수 있다(확인 필요).
- 서버가 HTTP/2 를 지원하지 않으면 httpx 는 HTTP/1.1 로 통신하고 `http_version` 도 그에 맞게 나온다(확인 필요).
- `Timeout(10.0)` 처럼 숫자 하나만 주면 네 칸 모두에 같은 값이 걸린다(확인 필요).
- 동시 요청이 수백 개면 `asyncio.Semaphore` 로 한 번에 도는 수를 묶는 경우가 많다(확인 필요).
- 응답이 실패 상태 코드일 때 예외로 바꾸려면 `response.raise_for_status()` 를 쓴다(확인 필요).
- 텍스트 조각이 필요하면 `aiter_text()` 도 있다(확인 필요).
- 동기 `Client` 의 스트리밍은 `with client.stream(...)` 과 `iter_bytes()` · `iter_lines()` 꼴이다(확인 필요).
