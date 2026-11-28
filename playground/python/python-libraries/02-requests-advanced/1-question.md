# python/python-libraries/02 — Requests 고급 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 404 를 흉내 낸 종합 에러 처리 블록 (예측)

```python
# 질문용 발췌
with patch("requests.get") as mock_get:
    mock_get.return_value = mock_response(status=404, json_data={"error": "not found"})
    mock_get.return_value.raise_for_status = MagicMock(
        side_effect=requests.exceptions.HTTPError("404 Not Found")
    )
    try:
        r = requests.get("https://api.example.com/missing", timeout=5)
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"HTTP 에러: {e}")
    except requests.exceptions.ConnectionError:
        print("네트워크 연결 실패")
    except requests.exceptions.Timeout:
        print("요청 시간 초과")
    except requests.exceptions.RequestException as e:
        print(f"기타 요청 에러: {e}")
```

- 이 블록이 찍는 줄은 무엇인가?

### 2. 인증 방식 셋을 차례로 부르면 (예측)

```python
# 질문용 발췌
with patch("requests.get") as mock_get:
    mock_get.return_value = mock_response(json_data={"user": "admin"})
    r = requests.get("https://api.example.com/user", auth=("username", "password"))
    print(f"Basic Auth: {r.json()}")
    r = requests.get("https://api.example.com/user", headers={"Authorization": "Bearer eyJhbG..."})
    print(f"Bearer Token: {r.json()}")
    r = requests.get("https://api.example.com/user", headers={"X-API-Key": "my-secret-api-key"})
    print(f"API Key: {r.json()}")
```

- 세 줄은 각각 무엇으로 찍히는가?
- 세 줄의 값이 서로 같거나 다른 까닭은 무엇인가?

### 3. `side_effect` 에 `Timeout` 을 넣은 호출 (예측)

```python
# 질문용 발췌
with patch("requests.get") as mock_get:
    mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")
    try:
        requests.get("https://slow-api.example.com", timeout=1)
    except requests.exceptions.Timeout:
        print("Timeout 발생! 재시도 또는 fallback 처리")
    except requests.exceptions.ConnectionError:
        print("연결 실패!")
```

- 이 블록은 어느 `except` 절의 줄을 찍는가?

### 4. `timeout` 을 늘 설정하라는 까닭 (왜)
- 왜 모든 요청에 `timeout` 을 주라고 하는가?

### 5. 404 를 받아도 `raise_for_status()` 를 따로 부르는 까닭 (왜)
- 왜 `requests.get` 뒤에 `raise_for_status()` 를 부르는가?
- 시연에서 가짜 응답의 `raise_for_status` 에 `side_effect` 를 따로 달아 준 까닭은 무엇인가?

### 6. 재시도를 걸어도 되는 요청의 범위 (경계)
- 원본 예제의 `allowed_methods=["GET", "POST"]` 에서 `POST` 를 재시도하면 어떤 일이 벌어질 수 있는가?

### 7. `except` 절의 순서를 바꾸면 (경계)
- 종합 패턴에서 `RequestException` 절을 맨 앞으로 올리면 무엇이 달라지는가?

### 8. 마운트한 재시도 정책이 닿는 곳 (경계)
- `session.mount("https://", adapter)` 를 한 뒤 `requests.get("https://...")` 을 부르면 재시도 정책이 붙는가?

### 9. timeout 튜플의 두 칸과 예외 계층의 대응 (연결)
- `timeout=(3, 10)` 의 두 칸은 예외 계층의 어느 두 클래스와 짝을 이루는가?

## 실습

### 실습 1. 네트워크 없이 Requests 고급 패턴 일곱 가지를 시연하는 스크립트

**만들 것** — `patch` 와 `MagicMock` 으로 `requests.get` · `requests.post` 를 가짜로 바꿔 끼우고, timeout · 재시도 정책 · 인증 · 파일 업로드 · 에러 처리 · 예외 계층을 차례로 보이는 스크립트를 만든다.

**준비물** — `requests` 패키지(`pip install requests`, `urllib3` 가 함께 깔린다)가 필요하다. 서버 응답은 모두 `unittest.mock` 으로 흉내 낸 것이라 네트워크는 필요 없다.

**요구 조건**
1. 1단계(가짜 응답) — `mock_response(status=200, json_data=None)` 은 `MagicMock` 에 `status_code` · `json()` 의 반환값(없으면 빈 딕셔너리) · `ok`(2xx 여부) · `text` 를 채워 돌려준다.
2. 2단계(timeout 설정) — `requests.get` 을 가짜로 바꾼 블록에서 `timeout` 을 (연결 3초, 읽기 10초) 튜플로 주고 요청한 뒤, 튜플 형태 안내 · 단일 값 안내 · `r.json()` 결과를 찍는다.
3. 3단계(timeout 예외) — 가짜 `requests.get` 이 불리면 `Timeout("Connection timed out")` 을 던지게 하고, `Timeout` 과 `ConnectionError` 를 따로 잡아 각자 다른 안내를 찍는다.
4. 4단계(재시도 정책) — 최대 3회 · 백오프 계수 1 · 상태 코드 429/500/502/503/504 · 메서드 GET/POST 인 `Retry` 를 만들어 `HTTPAdapter` 에 넣고, 새 `Session` 의 `https://` 와 `http://` 에 마운트한 뒤, `total` · `backoff_factor` · `status_forcelist`(리스트로) 와 안내 문장을 찍는다.
5. 5단계(인증) — 같은 가짜 응답(`{"user": "admin"}`)을 두고 Basic 인증(`auth=` 튜플) · Bearer 토큰(`Authorization` 헤더) · API 키(`X-API-Key` 헤더)로 한 번씩 요청하고 각 `r.json()` 을 찍는다.
6. 6단계(파일 업로드) — `requests.post` 를 가짜로 바꿔 201 응답을 돌려주게 하고, `BytesIO` 로 만든 파일을 `files={"file": (파일명, 파일객체, MIME)}` 로, 설명 필드를 `data=` 로 함께 보낸 뒤 결과와 `files` 형식 안내를 찍는다.
7. 7단계(종합 에러 처리) — 가짜 404 응답의 `raise_for_status` 가 `HTTPError("404 Not Found")` 를 던지게 하고, `timeout=5` 로 요청 → `raise_for_status()` 를 부른 뒤 `HTTPError` · `ConnectionError` · `Timeout` · `RequestException` 차례로 잡는다.
8. 8단계(예외 계층) — `RequestException` 아래 `ConnectionError` · `HTTPError` · `URLRequired` · `TooManyRedirects` · `Timeout`(그 아래 `ConnectTimeout` · `ReadTimeout`) · `ContentDecodingError` 를 나무 그림으로 찍는다.
9. 각 단계 앞에 `=== … ===` 꼴 제목을 찍고 단계 사이에 빈 줄을 찍는다.

**시작 코드**

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from unittest.mock import patch, MagicMock
import io

def mock_response(status=200, json_data=None):
    resp = MagicMock()
    # TODO: status_code, json() 반환값(없으면 {}), ok(2xx 여부), text 를 채운다
    return resp

print("=== Timeout 설정 ===")
with patch("requests.get") as mock_get:
    mock_get.return_value = mock_response(json_data={"data": "ok"})
    # TODO: 연결 3초, 읽기 10초 timeout 으로 요청한다
    print(f"timeout=(connect, read): (3, 10)")
    print(f"단일 값: timeout=5  -> connect, read 모두 5초")
    # TODO: r.json() 결과를 찍는다

print()
print("=== Timeout 예외 처리 ===")
with patch("requests.get") as mock_get:
    # TODO: 호출되면 Timeout("Connection timed out") 을 던지게 한다
    # TODO: try 로 timeout=1 요청, Timeout 과 ConnectionError 를 따로 잡는다
    pass

print()
print("=== Retry 전략 (HTTPAdapter + Retry) ===")
# TODO: Retry 정책 → HTTPAdapter → Session 의 https:// · http:// 에 마운트
# TODO: total, backoff_factor, status_forcelist(리스트) 를 찍는다
print("세션에 adapter를 마운트하면 모든 요청에 자동 적용")

print()
print("=== 인증 방식 ===")
with patch("requests.get") as mock_get:
    mock_get.return_value = mock_response(json_data={"user": "admin"})
    # TODO: Basic Auth / Bearer Token / API Key 로 한 번씩 요청하고 결과를 찍는다
    pass

print()
print("=== 파일 업로드 ===")
with patch("requests.post") as mock_post:
    mock_post.return_value = mock_response(
        status=201, json_data={"filename": "report.pdf", "size": 1024}
    )
    fake_file = io.BytesIO(b"fake pdf content")
    # TODO: files 딕셔너리와 data 딕셔너리를 만들어 함께 post 한다
    # TODO: 업로드 결과를 찍는다
    print("files 딕셔너리: {필드명: (파일명, 파일객체, MIME타입)}")

print()
print("=== 종합 에러 처리 패턴 ===")
with patch("requests.get") as mock_get:
    mock_get.return_value = mock_response(status=404, json_data={"error": "not found"})
    # TODO: raise_for_status 가 HTTPError("404 Not Found") 를 던지게 한다
    # TODO: timeout=5 요청 → raise_for_status() → 네 가지 예외를 차례로 잡는다
    pass

print()
print("=== 예외 계층 구조 ===")
# TODO: RequestException 아래 예외 클래스들을 나무 그림으로 찍는다
```

**확인 방법** — `python requests-advanced.py` 로 돌려 여덟 개의 `===` 제목 아래에 각 단계의 줄이 찍히는지, 3단계는 Timeout 쪽 안내가, 7단계는 `HTTP 에러:` 로 시작하는 줄이 찍히는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
