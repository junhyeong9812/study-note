# python/python-libraries/14 — HTTPX (비동기 HTTP) — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 결과 dict 셋을 담은 「동시에 3개 요청 완료」 한 줄이 찍힌다

**출력**

```text
=== 비동기 동시 요청 데모 ===
동시에 3개 요청 완료: [{'id': 0, 'data': 'response_0'}, {'id': 1, 'data': 'response_1'}, {'id': 2, 'data': 'response_2'}]
```

**왜 그런가**
`for` 가 `i` 를 0, 1, 2 로 돌며 매번 `{"id": i, "data": f"response_{i}"}` 를 쌓는다.
`len(results)` 가 3 이고, 리스트는 Python 의 dict 표기(작은따옴표)로 찍힌다.
문구는 「동시에」지만 실제로는 `await` 를 하나씩 기다린 직렬이다 — 2-summary 「동작 방식 (3)」과 「어디서 틀리나 4」.

### 2. `https://api.example.com/users` 로 가고, 블록이 끝나면 닫힌다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
요청은 `https://api.example.com/users` 로 간다.
`with` 블록을 나오면 `client` 는 닫힌 상태가 되어 커넥션 풀도 정리된다.

**왜 그런가**
`base_url` 을 준 `Client` 의 요청은 `base_url + path` 로 간다(원본 조각의 주석 그대로).
`with` 는 블록이 끝날 때 클라이언트를 닫는다 — 2-summary 「동작 방식 (1)」.

### 3. 직렬은 대기의 합(약 0.03초 이상), `gather` 는 가장 긴 대기 정도(약 0.01초 남짓)

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`serial()` 은 0.01초 대기를 셋 차례로 겪어 대략 0.03초보다 조금 더 걸린다.
`together()` 는 셋이 겹쳐 기다려 대략 0.01초보다 조금 더 걸린다.

**왜 그런가**
`for` 안의 `await` 는 앞 대기가 끝나야 다음으로 넘어간다.
`asyncio.gather` 는 코루틴들을 함께 돌려, 기다리는 시간이 겹친다.
정확한 값은 이벤트 루프의 일정 잡기에 따라 조금씩 다르다 — 2-summary 「동작 방식 (3)」의 그림. (원본에 근거 없음 — 추론)

### 4. 함수형 API 는 부를 때마다 클라이언트를 새로 만들어 커넥션 풀을 못 쓴다

`httpx.get` 은 호출마다 클라이언트를 만들고 버린다.
그래서 같은 서버에 여러 번 부르면 연결을 재사용하지 못해 비효율이다.
`Client` 는 커넥션 풀과 `base_url` 을 공유하므로 연결을 다시 쓴다.
근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 2」.

### 5. close 누락을 막기 위해서다

`async with` 는 블록을 어떻게 빠져나가든(정상 반환이든 예외든) 나올 때 클라이언트를 닫는다.
직접 만들어 쓰면 닫는 일을 잊기 쉽다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 3」.

### 6. HTTP/2 는 `httpx[http2]` 설치, 큰 응답은 스트리밍으로

- `http2=True` 를 쓰려면 `pip install httpx[http2]` 로 extras 를 깔아야 한다(원본 주석: `h2` 패키지).
- 수 GB 파일을 일반 요청으로 받으면 본문 전체를 메모리에 올려 메모리에서 깨진다.
- `client.stream('GET', url)` 안에서 `aiter_bytes(chunk_size=…)` 로 조각씩 받아 파일에 쓰면 메모리 사용이 일정하다.

근거: 2-summary 「동작 방식 (4)」 · 「동작 방식 (5)」 · 「어디서 틀리나 6, 8」.

### 7. 기본 5초 타임아웃에 걸려 요청이 실패할 수 있다

원본 주석에 따르면 기본 timeout 은 5초다.
응답이 그보다 오래 걸리면 타임아웃으로 끝날 수 있으므로, `Timeout(read=…)` 처럼 칸별로 늘려야 한다.
근거: 2-summary 「동작 방식 (6)」 · 「어디서 틀리나 9」.
기본값 5초는 httpx 의 기본값으로 버전에 따라 다를 수 있다 — 2-summary 「구현 세부사항 대 언어 보장」.

### 8. 풀에서 빈 연결이 날 때까지 기다리는 시간의 한도다

`Limits(max_connections=…)` 는 동시에 열 수 있는 연결 수를 묶는다.
다 차면 새 요청은 풀에서 연결이 빌 때까지 기다리고, `Timeout` 의 `pool` 칸이 그 기다림의 한도다.
근거: 2-summary 「동작 방식 (6)」. (원본에 근거 없음 — 추론 — 원본은 `pool` 을 「풀 대기 타임아웃」이라고만 적었다)

### 9. 비동기가 필요하면 httpx, 아니면 requests 도 충분하다

원본 비교: requests 는 동기만 지원하지만 성숙하고 생태계가 넓다.
httpx 는 동기 + 비동기, HTTP/2, requests 호환 API 를 준다.
그래서 async 코드 안에서 요청하거나 HTTP/2 가 필요할 때 httpx 를 고르고, 동기 스크립트면 requests 로도 충분하다.
근거: 2-summary 「언제 쓰고 언제 안 쓰나」 · 「핵심 문장 1」.

## 실습 정답

### 실습 1. httpx 사용법 안내문 + 네트워크 없는 비동기 데모

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. `MagicMock` 으로 가짜 응답 만들기 | `mock_response` 의 `resp = MagicMock()` · `return resp` |
| 2. `status_code` · `json()` · `text` | `resp.status_code = status` · `resp.json.return_value = json_data or {}` · `resp.text = text` |
| 3. `headers` · `is_success` | `resp.headers = {...}` · `resp.is_success = True` |
| 4. 함수형 API 예 | 「httpx 동기 사용」 문자열의 `httpx.get(...)` · `response.status_code` · `response.json()` |
| 5. `Client` 예 | `with httpx.Client(base_url=...) as client:` · `client.get('/users')` · `client.post('/users', json=...)` |
| 6. `fetch_data` 예 | 「httpx 비동기 사용」 문자열의 `async with httpx.AsyncClient(...)` · `await client.get('/data')` |
| 7. `fetch_multiple` 예 | `tasks = [client.get(url) for url in urls]` · `await asyncio.gather(*tasks)` |
| 8. 세 번 sleep 하며 dict 쌓기 | `demo_async` 의 `for i in range(3):` · `await asyncio.sleep(0.01)` · `results.append(...)` |
| 9. 개수와 리스트 찍고 반환 | `print(f"동시에 {len(results)}개 요청 완료: {results}")` · `return results` |
| 10. 루프로 돌리기 | `asyncio.run(demo_async())` |
| 11. 스트리밍 예 | `client.stream('GET', url)` · `aiter_bytes(chunk_size=8192)` · `aiter_lines()` · `line.startswith('data: ')` · `line[6:]` |
| 12. HTTP/2 예 | `httpx.AsyncClient(http2=True)` · `response.http_version` |
| 13. 고급 설정 예 | `Timeout(connect=…, read=…, write=…, pool=…)` · `Limits(max_connections=…, max_keepalive_connections=…)` · `httpx.AsyncClient(timeout=…, limits=…, base_url=…, headers=…, follow_redirects=True)` |
| 14. 비교 세 줄 | 끝의 `print("requests: …")` 등 세 줄 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-libraries/reference/httpx.py`

```python
# [주요 라이브러리] HTTPX (비동기 HTTP)
# 설명: httpx 비동기/동기 클라이언트, 스트리밍, HTTP/2 지원
# 팁: httpx는 requests와 거의 동일한 API를 제공하면서 async를 지원한다. AsyncClient는 반드시 async with로 사용한다. HTTP/2를 사용하려면 httpx[http2] 설치가 필요하다. 동시 요청이 많으면 asyncio.gather + AsyncClient 조합이 매우 효과적이다.

# 비동기 실행을 위한 표준 라이브러리
import asyncio
# 외부 호출 없이 동작 시연을 위한 mock 도구
from unittest.mock import AsyncMock, MagicMock, patch

# 가짜 응답 객체를 만드는 헬퍼: 실제 네트워크 없이 시연용
def mock_response(status=200, json_data=None, text="OK"):
    # MagicMock 인스턴스를 응답처럼 사용
    resp = MagicMock()
    # status_code 속성에 HTTP 상태 코드 설정
    resp.status_code = status
    # .json() 호출 시 반환될 dict 지정
    resp.json.return_value = json_data or {}
    # text 본문 설정
    resp.text = text
    # 헤더는 JSON 응답 가정
    resp.headers = {"content-type": "application/json"}
    # is_success 플래그
    resp.is_success = True
    # 만든 mock 응답 반환
    return resp

# 섹션 헤더 출력: 동기 사용법(requests 대체)
print("=== httpx 동기 사용 ===")
# httpx.get/post 등은 함수형 API(requests와 동일)
# httpx.Client는 커넥션 풀과 base_url을 공유하는 세션 객체
# 함정: 함수형 API는 매 호출마다 클라이언트를 새로 만들어 비효율 → Client 사용 권장
print("""
import httpx

# 간단한 요청 (requests와 유사)
response = httpx.get('https://api.example.com/data')
print(response.status_code)
print(response.json())

# Client (Session과 유사 - 커넥션 풀 재사용)
with httpx.Client(base_url='https://api.example.com') as client:
    r = client.get('/users')       # base_url + path
    r = client.post('/users', json={'name': 'Alice'})
""")

# 섹션 헤더 출력: AsyncClient를 사용한 비동기 패턴
print("=== httpx 비동기 사용 ===")
# AsyncClient는 반드시 async with로 컨텍스트 관리(close 누락 방지)
# asyncio.gather로 여러 요청을 동시 실행 → I/O 병렬화
print("""
import httpx
import asyncio

async def fetch_data():
    async with httpx.AsyncClient(base_url='https://api.example.com') as client:
        response = await client.get('/data')
        return response.json()

# 동시 요청
async def fetch_multiple():
    async with httpx.AsyncClient() as client:
        urls = [
            'https://api.example.com/users',
            'https://api.example.com/posts',
            'https://api.example.com/comments'
        ]
        tasks = [client.get(url) for url in urls]
        responses = await asyncio.gather(*tasks)
        return [r.json() for r in responses]
""")

# 실제 실행 가능한 비동기 데모
# async 함수: 병렬 요청을 흉내 내는 데모
async def demo_async():
    # 데모 시작 헤더 출력
    print("\n=== 비동기 동시 요청 데모 ===")
    # 결과를 누적할 리스트
    results = []
    # 3개의 가짜 요청을 직렬 await로 흉내(실제로는 gather로 병렬 가능)
    for i in range(3):
        # 비동기 sleep으로 네트워크 지연 시뮬레이션
        await asyncio.sleep(0.01)  # 네트워크 요청 시뮬레이션
        # 가짜 응답을 결과 리스트에 추가
        results.append({"id": i, "data": f"response_{i}"})
    # 누적된 결과 출력
    print(f"동시에 {len(results)}개 요청 완료: {results}")
    # 결과 반환
    return results

# 이벤트 루프를 만들어 데모 코루틴 실행
asyncio.run(demo_async())

# 섹션 헤더 출력: 스트리밍 다운로드/SSE 패턴
print("\n=== 스트리밍 ===")
# client.stream(method, url)은 비동기 컨텍스트로 큰 응답을 청크 단위 처리
# aiter_bytes(chunk_size)로 메모리 사용을 일정하게 유지
# aiter_lines로 SSE(Server-Sent Events) 라인 단위 처리
print("""
# 대용량 다운로드 스트리밍
async def download_large_file(url: str, path: str):
    async with httpx.AsyncClient() as client:
        async with client.stream('GET', url) as response:
            with open(path, 'wb') as f:
                async for chunk in response.aiter_bytes(chunk_size=8192):
                    f.write(chunk)

# 서버 이벤트 스트리밍 (SSE)
async def stream_events():
    async with httpx.AsyncClient() as client:
        async with client.stream('GET', 'https://api.example.com/events') as response:
            async for line in response.aiter_lines():
                if line.startswith('data: '):
                    print(f'Event: {line[6:]}')
""")

# 섹션 헤더 출력: HTTP/2 활성화
print("=== HTTP/2 지원 ===")
# http2=True 옵션 사용 시 httpx[http2] extras로 h2 패키지 설치 필요
print("""
# HTTP/2 활성화 (pip install httpx[http2])
client = httpx.AsyncClient(http2=True)
response = await client.get('https://http2.example.com')
print(response.http_version)  # 'HTTP/2'
""")

# 섹션 헤더 출력: 타임아웃과 커넥션 풀 세부 설정
print("=== 고급 설정 ===")
# Timeout은 connect/read/write/pool로 구분 설정 가능
# Limits로 동시 커넥션과 keepalive 커넥션 수 제어
# 함정: 기본 timeout=5초이므로 느린 API는 명시적 조정 필요
print("""
import httpx
from httpx import Timeout, Limits

# 세밀한 타임아웃
timeout = Timeout(
    connect=5.0,    # 연결 타임아웃
    read=10.0,      # 읽기 타임아웃
    write=5.0,      # 쓰기 타임아웃
    pool=10.0       # 풀 대기 타임아웃
)

# 커넥션 풀 제한
limits = Limits(
    max_connections=100,        # 최대 커넥션
    max_keepalive_connections=20  # keepalive 커넥션
)

client = httpx.AsyncClient(
    timeout=timeout,
    limits=limits,
    base_url='https://api.example.com',
    headers={'Authorization': 'Bearer token'},
    follow_redirects=True
)
""")

# 섹션 헤더 출력: requests와 httpx 차이 요약
print("=== requests vs httpx 비교 ===")
# requests: 동기 전용
print("requests: 동기만, 성숙, 넓은 생태계")
# httpx: 동기+비동기 모두 지원, HTTP/2 지원
print("httpx:    동기+비동기, HTTP/2, requests 호환 API")
# 선택 가이드: 비동기가 필요할 때 httpx
print("         비동기가 필요하면 httpx, 아니면 requests도 충분")
```

**실행 결과** — 원본 예제(`component`)를 실제로 돌린 출력이다. 환경 `Python 3.12.3` · 2026-11-28 · exit 0 · 두 번 돌려 출력이 같았다.

````text
$ python3 -I example.py
=== httpx 동기 사용 ===

import httpx

# 간단한 요청 (requests와 유사)
response = httpx.get('https://api.example.com/data')
print(response.status_code)
print(response.json())

# Client (Session과 유사 - 커넥션 풀 재사용)
with httpx.Client(base_url='https://api.example.com') as client:
    r = client.get('/users')       # base_url + path
    r = client.post('/users', json={'name': 'Alice'})

=== httpx 비동기 사용 ===

import httpx
import asyncio

async def fetch_data():
    async with httpx.AsyncClient(base_url='https://api.example.com') as client:
        response = await client.get('/data')
        return response.json()

# 동시 요청
async def fetch_multiple():
    async with httpx.AsyncClient() as client:
        urls = [
            'https://api.example.com/users',
            'https://api.example.com/posts',
            'https://api.example.com/comments'
        ]
        tasks = [client.get(url) for url in urls]
        responses = await asyncio.gather(*tasks)
        return [r.json() for r in responses]


=== 비동기 동시 요청 데모 ===
동시에 3개 요청 완료: [{'id': 0, 'data': 'response_0'}, {'id': 1, 'data': 'response_1'}, {'id': 2, 'data': 'response_2'}]

=== 스트리밍 ===

# 대용량 다운로드 스트리밍
async def download_large_file(url: str, path: str):
    async with httpx.AsyncClient() as client:
        async with client.stream('GET', url) as response:
            with open(path, 'wb') as f:
                async for chunk in response.aiter_bytes(chunk_size=8192):
                    f.write(chunk)

# 서버 이벤트 스트리밍 (SSE)
async def stream_events():
    async with httpx.AsyncClient() as client:
        async with client.stream('GET', 'https://api.example.com/events') as response:
            async for line in response.aiter_lines():
                if line.startswith('data: '):
                    print(f'Event: {line[6:]}')

=== HTTP/2 지원 ===

# HTTP/2 활성화 (pip install httpx[http2])
client = httpx.AsyncClient(http2=True)
response = await client.get('https://http2.example.com')
print(response.http_version)  # 'HTTP/2'

=== 고급 설정 ===

import httpx
from httpx import Timeout, Limits

# 세밀한 타임아웃
timeout = Timeout(
    connect=5.0,    # 연결 타임아웃
    read=10.0,      # 읽기 타임아웃
    write=5.0,      # 쓰기 타임아웃
    pool=10.0       # 풀 대기 타임아웃
)

# 커넥션 풀 제한
limits = Limits(
    max_connections=100,        # 최대 커넥션
    max_keepalive_connections=20  # keepalive 커넥션
)

client = httpx.AsyncClient(
    timeout=timeout,
    limits=limits,
    base_url='https://api.example.com',
    headers={'Authorization': 'Bearer token'},
    follow_redirects=True
)

=== requests vs httpx 비교 ===
requests: 동기만, 성숙, 넓은 생태계
httpx:    동기+비동기, HTTP/2, requests 호환 API
         비동기가 필요하면 httpx, 아니면 requests도 충분
````

**풀이 요점**
- 실제로 도는 것은 `demo_async` 하나뿐이고, httpx 코드는 모두 `print("""…""")` 로 찍히는 안내문이다 — 그래서 httpx 를 깔지 않아도 돈다.
- `demo_async` 는 `for` 안에서 `await` 를 하나씩 거는 직렬이다 — 진짜 동시로 하려면 안내문의 `fetch_multiple` 처럼 `asyncio.gather(*tasks)` 를 쓴다.
- `json_data or {}` 덕분에 `json_data` 를 안 주면 `resp.json()` 이 빈 dict 를 돌려준다.
- `mock_response` · `AsyncMock` · `patch` 는 시연 틀로 놓였을 뿐 쓰이지 않는다.
- 안내문의 「HTTP/2」·「고급 설정」 조각은 `AsyncClient` 를 `async with` 없이 만든다 — 설정 꼴을 보이려는 조각이고, 실제 코드에서는 `async with` 로 연다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 원본 예제를 `Python 3.12.3` 에서 2회 돌렸다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
