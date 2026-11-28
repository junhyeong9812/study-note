# python/python-libraries/02 — Requests 고급 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. `HTTPError` 절이 잡아 `HTTP 에러: 404 Not Found` 를 찍는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
HTTP 에러: 404 Not Found
```

**왜 그런가**
- 가짜 `requests.get` 은 예외 없이 404 가짜 응답을 돌려준다.
- 그 응답의 `raise_for_status` 에는 `side_effect=HTTPError("404 Not Found")` 가 달려 있어 `r.raise_for_status()` 에서 `HTTPError` 가 던져진다.
- `except` 는 위에서부터 맞춰 보므로 첫 절 `HTTPError` 가 잡고, `e` 를 문자열로 찍으면 넣어 둔 메시지 `404 Not Found` 가 나온다.
- 근거: 2-summary 「동작 방식 (6)」 · 「동작 방식 (7)」.

### 2. 세 줄 모두 `{'user': 'admin'}` — 가짜 응답이 하나뿐이라서

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
Basic Auth: {'user': 'admin'}
Bearer Token: {'user': 'admin'}
API Key: {'user': 'admin'}
```

**왜 그런가**
- `mock_get.return_value` 를 한 번 정해 두면 가짜 `requests.get` 은 넘긴 `auth` · `headers` 와 상관없이 늘 그 응답을 돌려준다.
- 그 응답의 `json()` 은 `{"user": "admin"}` 을 돌려주고, f-문자열 안의 딕셔너리는 `{'user': 'admin'}` 꼴로 찍힌다.
- 값이 같은 것은 서버가 세 인증을 모두 받아 줘서가 아니다.
- 근거: 2-summary 「동작 방식 (7)」 · 「어디서 틀리나 8」.

### 3. `Timeout` 절 — `Timeout 발생! 재시도 또는 fallback 처리`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
Timeout 발생! 재시도 또는 fallback 처리
```

**왜 그런가**
- `side_effect` 에 예외를 넣은 mock 은 불리는 순간 그 예외를 던진다.
- 던져진 것이 `Timeout` 이므로 첫 절 `except requests.exceptions.Timeout` 이 잡는다.
- 한 절이 잡으면 그 아래 `ConnectionError` 절은 실행되지 않는다.
- 근거: 2-summary 「동작 방식 (2)」 · 「동작 방식 (7)」.

### 4. 설정하지 않으면 무한히 기다릴 수 있어서

`timeout` 이 없으면 응답이 오지 않는 서버 앞에서 요청이 끝없이 기다릴 수 있다.
그동안 그 요청을 기다리는 작업 전체가 묶인다.
한도를 정해 두면 넘었을 때 `Timeout` 예외로 빠져나와 재시도나 대체 처리를 할 수 있다.
근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 1」(원본 팁).

### 5. 4xx · 5xx 를 예외로 바꿔 한 곳에서 처리하려고 — mock 은 스스로 예외를 내지 않아서

- `requests` 는 404 응답을 받아도 응답이 온 것이므로 예외를 내지 않는다.
- `raise_for_status()` 를 불러야 4xx · 5xx 가 `HTTPError` 가 되어, 네트워크 실패와 같은 `try/except` 한 덩어리로 일관되게 처리된다.
- 시연의 응답은 `MagicMock` 이라 `raise_for_status()` 를 불러도 또 다른 `MagicMock` 을 돌려줄 뿐 예외를 내지 않는다.
- 그래서 진짜 응답처럼 보이게 `side_effect=HTTPError(...)` 를 직접 달았다.
- 근거: 2-summary 「동작 방식 (6)」 · 「동작 방식 (7)」 · 「어디서 틀리나 3」.

### 6. 같은 일이 두 번 처리될 수 있다

`POST` 는 멱등하지 않은 요청일 수 있다.
서버가 요청을 처리했는데 응답만 잃었을 때 재시도하면, 주문이나 결제가 두 번 일어날 수 있다.
원본 팁은 Retry 를 멱등한 요청에만 적용하라고 하고, 정답 코드 주석도 `POST` 를 「함정 위험」으로 짚는다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 2」.

### 7. 모든 `requests` 예외가 첫 절에서 잡혀 아래 절들이 죽은 코드가 된다

`RequestException` 은 모든 `requests` 예외의 부모다.
`except` 는 위에서부터 맞춰 보므로, 맨 앞에 두면 `HTTPError` · `ConnectionError` · `Timeout` 도 모두 그 절에 걸린다.
그러면 404 시연도 `기타 요청 에러: 404 Not Found` 쪽으로 가고, 사유별 처리가 사라진다.
근거: 2-summary 「동작 방식 (6)」 · 「어디서 틀리나 5」.

### 8. 붙지 않는다 — 정책은 마운트한 그 세션으로 보낸 요청에만 붙는다

`session.mount` 는 `session` 객체에 어댑터를 연결한다.
모듈 함수 `requests.get` 은 그 `session` 을 거치지 않으므로 재시도 정책이 없다.
정책을 쓰려면 `session.get(...)` 처럼 그 세션으로 요청해야 한다.
원본 시연은 세션을 만들고 설정값만 찍을 뿐 세션으로 요청을 보내지 않는다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 7」.

### 9. 첫 칸은 `ConnectTimeout`, 둘째 칸은 `ReadTimeout`

`timeout` 튜플의 첫 칸은 연결 단계의 한도, 둘째 칸은 읽기 단계의 한도다.
예외 계층에서 `Timeout` 아래의 두 자식이 각각 연결 단계 타임아웃(`ConnectTimeout`)과 읽기 단계 타임아웃(`ReadTimeout`)이다.
그래서 둘을 한꺼번에 잡으려면 부모 `Timeout` 을 잡는다.
근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (6)」의 계층 그림.

## 실습 정답

### 실습 1. 네트워크 없이 Requests 고급 패턴 일곱 가지를 시연하는 스크립트

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 가짜 응답 헬퍼 | `mock_response` 의 `resp.status_code` · `resp.json.return_value = json_data or {}` · `resp.ok = 200 <= status < 300` · `resp.text` |
| 2. timeout 튜플로 요청 | `requests.get(..., timeout=(3, 10))` · `print(f"결과: {r.json()}")` |
| 3. Timeout 예외 따로 잡기 | `mock_get.side_effect = requests.exceptions.Timeout(...)` · `except requests.exceptions.Timeout` · `except requests.exceptions.ConnectionError` |
| 4. 재시도 정책 마운트 | `Retry(total=3, backoff_factor=1, status_forcelist=[...], allowed_methods=[...])` · `HTTPAdapter(max_retries=retry_strategy)` · `session.mount("https://", ...)` · `session.mount("http://", ...)` |
| 5. 인증 세 가지 | `auth=("username", "password")` · `headers={"Authorization": "Bearer ..."}` · `headers={"X-API-Key": ...}` |
| 6. 파일 업로드 | `patch("requests.post")` · `io.BytesIO(...)` · `files={"file": ("report.pdf", fake_file, "application/pdf")}` · `data={"description": ...}` |
| 7. 종합 에러 처리 | `mock_get.return_value.raise_for_status = MagicMock(side_effect=HTTPError(...))` · `r.raise_for_status()` · `except` 네 절 |
| 8. 예외 계층 그림 | `print("RequestException (base)")` 부터 `print("  └── ContentDecodingError")` 까지 |
| 9. 제목과 빈 줄 | 각 `print("=== … ===")` · `print()` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-libraries/reference/requests-advanced.py`

```python
# [주요 라이브러리] Requests 고급
# 설명: timeout, retry, auth, 파일 업로드, 에러 처리 등 실무 패턴
# 팁: timeout은 항상 설정해야 한다. 미설정 시 무한 대기 가능. Retry는 멱등한(idempotent) 요청에만 적용하는 것이 안전하다. raise_for_status()로 HTTP 에러를 예외로 변환하면 일관된 에러 처리가 가능하다.

# requests 라이브러리: 가장 널리 쓰이는 동기 HTTP 클라이언트
import requests
# Session에 마운트할 어댑터 클래스
from requests.adapters import HTTPAdapter
# 재시도 정책을 정의하는 urllib3의 Retry
from urllib3.util.retry import Retry
# 외부 호출 없이 시연하기 위한 mock 도구
from unittest.mock import patch, MagicMock, mock_open
# 메모리 상의 파일 객체(BytesIO) 사용
import io

# 가짜 응답을 만드는 헬퍼(테스트/시연용)
def mock_response(status=200, json_data=None):
    # MagicMock으로 응답 객체 흉내
    resp = MagicMock()
    # 상태 코드 설정
    resp.status_code = status
    # .json() 호출 결과 지정
    resp.json.return_value = json_data or {}
    # ok 속성: 2xx 여부
    resp.ok = 200 <= status < 300
    # text 본문(문자열화)
    resp.text = str(json_data)
    # 만든 mock 응답 반환
    return resp

# 섹션 헤더 출력: timeout 설정 패턴
print("=== Timeout 설정 ===")
# patch로 requests.get을 mock으로 교체(실제 네트워크 호출 안 함)
with patch("requests.get") as mock_get:
    # mock 응답 지정
    mock_get.return_value = mock_response(json_data={"data": "ok"})
    # connect timeout 3초, read timeout 10초
    # 함정: timeout 미설정 시 무한 대기 가능 → 실무에서 반드시 설정
    r = requests.get(
        "https://api.example.com/data",
        timeout=(3, 10)
    )
    # (connect, read) 튜플 형태 안내
    print(f"timeout=(connect, read): (3, 10)")
    # 단일 값 형태 안내
    print(f"단일 값: timeout=5  -> connect, read 모두 5초")
    # mock 응답 결과 출력
    print(f"결과: {r.json()}")

# 빈 줄 출력으로 섹션 분리
print()
# 섹션 헤더 출력: Timeout 발생 시 예외 처리
print("=== Timeout 예외 처리 ===")
# requests.get을 patch하고 side_effect로 예외를 발생시킴
with patch("requests.get") as mock_get:
    # 호출 시 Timeout 예외를 발생시키도록 설정
    mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")
    try:
        # 시뮬레이션 호출
        requests.get("https://slow-api.example.com", timeout=1)
    except requests.exceptions.Timeout:
        # Timeout만 별도로 처리(재시도/대체 로직 적용 가능)
        print("Timeout 발생! 재시도 또는 fallback 처리")
    except requests.exceptions.ConnectionError:
        # DNS 실패/연결 거부 등
        print("연결 실패!")

# 빈 줄 출력으로 섹션 분리
print()
# 섹션 헤더 출력: HTTPAdapter + Retry로 재시도 정책 구성
print("=== Retry 전략 (HTTPAdapter + Retry) ===")
# 실제 retry 설정 방법 시연
# total: 총 재시도 횟수. backoff_factor로 지수 백오프(1, 2, 4, 8...)
# status_forcelist: 어떤 상태 코드일 때 재시도할지 지정
# allowed_methods: 멱등 메서드만 허용하는 게 안전(POST는 함정 위험)
retry_strategy = Retry(
    total=3,                    # 최대 재시도 횟수
    backoff_factor=1,           # 대기: 1초, 2초, 4초...
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET", "POST"],
)
# Retry를 어댑터에 주입
adapter = HTTPAdapter(max_retries=retry_strategy)

# Session에 어댑터를 마운트하면 모든 요청에 정책이 적용됨
session = requests.Session()
# https 스킴에 어댑터 마운트
session.mount("https://", adapter)
# http 스킴에도 동일 적용
session.mount("http://", adapter)
# 설정값 확인 출력
print(f"Retry total: {retry_strategy.total}")
# backoff 인수 출력
print(f"Backoff factor: {retry_strategy.backoff_factor}")
# 재시도 트리거 상태코드 출력
print(f"Status forcelist: {list(retry_strategy.status_forcelist)}")
# 안내 메시지
print("세션에 adapter를 마운트하면 모든 요청에 자동 적용")

# 빈 줄 출력으로 섹션 분리
print()
# 섹션 헤더 출력: 다양한 인증 방식
print("=== 인증 방식 ===")
# requests.get을 mock으로 교체하여 시연
with patch("requests.get") as mock_get:
    # 인증된 사용자 응답을 흉내
    mock_get.return_value = mock_response(json_data={"user": "admin"})

    # 1. Basic Auth
    # auth=(user, pass) 튜플은 HTTPBasicAuth로 자동 변환
    r = requests.get(
        "https://api.example.com/user",
        auth=("username", "password")  # HTTPBasicAuth
    )
    # 결과 출력
    print(f"Basic Auth: {r.json()}")

    # 2. Bearer Token
    # Authorization 헤더로 OAuth2 Bearer 토큰 전달
    r = requests.get(
        "https://api.example.com/user",
        headers={"Authorization": "Bearer eyJhbG..."}
    )
    # 결과 출력
    print(f"Bearer Token: {r.json()}")

    # 3. API Key
    # 서비스마다 헤더명이 다름(X-API-Key, Api-Key, X-Auth-Token 등)
    r = requests.get(
        "https://api.example.com/user",
        headers={"X-API-Key": "my-secret-api-key"}
    )
    # 결과 출력
    print(f"API Key: {r.json()}")

# 빈 줄 출력으로 섹션 분리
print()
# 섹션 헤더 출력: multipart 파일 업로드
print("=== 파일 업로드 ===")
# requests.post를 mock으로 패치
with patch("requests.post") as mock_post:
    # 생성 응답(201) 흉내
    mock_post.return_value = mock_response(
        status=201, json_data={"filename": "report.pdf", "size": 1024}
    )
    # 파일 업로드 (multipart/form-data)
    # BytesIO로 가짜 파일 객체 생성(실제로는 open(path, "rb") 사용)
    fake_file = io.BytesIO(b"fake pdf content")
    # files 딕셔너리 형식: 필드명 → (파일명, 파일객체, MIME)
    files = {
        "file": ("report.pdf", fake_file, "application/pdf")
    }
    # 같은 multipart에 추가 폼 필드를 보낼 때는 data 파라미터 사용
    data = {"description": "월간 보고서"}
    r = requests.post(
        "https://api.example.com/upload",
        files=files,
        data=data  # 추가 필드
    )
    # 응답 출력
    print(f"업로드 결과: {r.json()}")
    # files 형식 안내
    print("files 딕셔너리: {필드명: (파일명, 파일객체, MIME타입)}")

# 빈 줄 출력으로 섹션 분리
print()
# 섹션 헤더 출력: 종합적인 예외 처리 패턴
print("=== 종합 에러 처리 패턴 ===")
# 404 응답을 흉내내고 raise_for_status도 강제로 예외를 발생시키도록 설정
with patch("requests.get") as mock_get:
    # 404 응답 mock
    mock_get.return_value = mock_response(status=404, json_data={"error": "not found"})
    # raise_for_status 호출 시 HTTPError를 던지도록 강제
    mock_get.return_value.raise_for_status = MagicMock(
        side_effect=requests.exceptions.HTTPError("404 Not Found")
    )
    try:
        # timeout 명시는 모범 사례
        r = requests.get("https://api.example.com/missing", timeout=5)
        # 4xx/5xx면 HTTPError 발생 → 일관된 에러 처리 가능
        r.raise_for_status()  # 4xx, 5xx이면 예외 발생
    except requests.exceptions.HTTPError as e:
        # HTTP 에러(4xx/5xx)
        print(f"HTTP 에러: {e}")
    except requests.exceptions.ConnectionError:
        # 네트워크 도달 불가
        print("네트워크 연결 실패")
    except requests.exceptions.Timeout:
        # 연결/읽기 타임아웃
        print("요청 시간 초과")
    except requests.exceptions.RequestException as e:
        # 기타 모든 requests 예외(부모 클래스)
        print(f"기타 요청 에러: {e}")  # 모든 requests 예외의 부모

# 빈 줄 출력으로 섹션 분리
print()
# 섹션 헤더 출력: 예외 클래스 계층 구조
print("=== 예외 계층 구조 ===")
# 모든 예외의 베이스
print("RequestException (base)")
# 네트워크 연결 실패
print("  ├── ConnectionError")
# HTTP 상태 에러(raise_for_status)
print("  ├── HTTPError")
# URL 누락
print("  ├── URLRequired")
# 리다이렉트 과다
print("  ├── TooManyRedirects")
# 타임아웃 베이스
print("  ├── Timeout")
# 연결 단계 타임아웃
print("  │   ├── ConnectTimeout")
# 읽기 단계 타임아웃
print("  │   └── ReadTimeout")
# 본문 디코드 실패
print("  └── ContentDecodingError")
```

**실행 결과** — 실행하지 않음 — 실행 환경 · 바깥 네트워크에 따라 달라지는 예제다.

**풀이 요점**
- `patch("requests.get")` 블록 안에서는 `requests.get` 이 가짜라, `return_value` 로 응답을, `side_effect` 로 예외를 마음대로 정한다.
- 재시도 정책은 `Retry` → `HTTPAdapter(max_retries=...)` → `session.mount(...)` 의 사슬로 세션에 붙고, 그 세션으로 보낸 요청에만 적용된다.
- `POST` 를 `allowed_methods` 에 넣은 것은 원본 그대로지만, 멱등하지 않은 요청을 재시도하는 위험이 있다.
- `files` 튜플은 `(파일명, 파일객체, MIME)` 순서이고, 함께 보낼 폼 필드는 `data=` 로 넘긴다.
- `MagicMock` 응답은 스스로 `HTTPError` 를 내지 않으니 `raise_for_status` 에 `side_effect` 를 달아야 진짜 404 처럼 동작한다.
- `except` 는 자식 예외부터 쓰고, 모두의 부모 `RequestException` 은 맨 끝에 둔다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 실행 환경 · 바깥 네트워크에 따라 달라지는 예제다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
