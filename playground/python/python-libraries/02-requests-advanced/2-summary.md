# python/python-libraries/02 — Requests 고급 — 정리 (힌트)

> 출처 — study-site 항목 `python/requests-advanced`(항목 데이터 `data/python/libraries.json`) · 정답 코드 study-practice `python/python-libraries/reference/requests-advanced.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 실행 환경 · 바깥 네트워크에 따라 달라지는 예제다.

## 한눈에 — 쉽게 말하면

**`requests` 고급 패턴은 「콜센터에 전화 거는 요령」이다.**
신호가 가는데 아무도 안 받으면 몇 초 뒤 끊는다(연결 제한 시간).
받았는데 상대가 말없이 있으면 또 몇 초 뒤 끊는다(읽기 제한 시간).
통화 중 신호면 잠깐 쉬었다가 다시 건다(재시도).
상담원이 「본인 확인」을 하면 신분을 댄다(인증).
서류는 봉투에 이름표를 붙여 함께 보낸다(파일 업로드).
통화가 왜 실패했는지를 「안 받음 · 침묵 · 거절」로 나눠 기록한다(예외 계층).
HTTP 요청도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 신호가 가는 동안 기다리는 한도 | connect timeout |
| 받은 뒤 상대의 침묵을 기다리는 한도 | read timeout |
| 통화 중이면 쉬었다 다시 걸기 | `Retry` + `HTTPAdapter` |
| 늘 쓰는 전화기에 설정해 두기 | `Session.mount()` |
| 본인 확인 | `auth=` · `Authorization` 헤더 · API 키 헤더 |
| 이름표 붙인 서류 봉투 | `files={필드명: (파일명, 파일객체, MIME)}` |
| 실패 사유별 기록 | `RequestException` 아래의 예외 클래스들 |

```text
 요청 ──► [연결 (connect timeout)] ──► [응답 기다림 (read timeout)] ──► 응답
             │ 실패                        │ 실패                    │ 4xx/5xx
             ▼                             ▼                         ▼
       ConnectionError /             ReadTimeout              raise_for_status()
       ConnectTimeout                                          → HTTPError
             └──────────────┬──────────────┴─────────────────────────┘
                            ▼
                  RequestException (모두의 부모)
```

## 이 주제가 답하려는 질문

1. 서버가 느리거나 죽었을 때 내 프로그램이 영원히 멈추지 않게 하려면 무엇을 정하나?
2. 일시적인 실패(503 · 429 등)를 어떻게 자동으로 다시 시도하고, 어떤 요청에는 다시 시도하면 안 되나?
3. 인증 정보와 파일은 요청의 어디에 실어 보내나?
4. 네트워크 실패와 HTTP 에러를 한 가지 방식(예외)으로 가려 잡으려면 어떻게 하나?

## 동작 방식

### (1) timeout — 기다림의 한도를 둘로 나눈다

**언제 쓰나** — 모든 요청에 쓴다.
원본 팁 그대로, `timeout` 을 정하지 않으면 무한히 기다릴 수 있다.

```text
requests.get(url, timeout=(3, 10))
        │
        ├─ connect: 서버와 연결을 맺는 데 3초까지 기다린다
        └─ read   : 연결 뒤 응답을 받는 데 10초까지 기다린다

requests.get(url, timeout=5)
        └─ connect · read 둘 다 5초
```

- 튜플의 첫 칸은 연결 단계의 한도다.
- 둘째 칸은 연결이 맺어진 뒤 읽기 단계의 한도다.
- 숫자 하나만 주면 두 단계에 같은 값이 쓰인다.
- 한도를 넘으면 `requests.exceptions.Timeout` 계열 예외가 난다.

> **timeout** — 요청이 응답을 얼마나 오래 기다릴지 정한 한도(초).\
> 예: `timeout=(3, 10)` 은 연결 3초, 읽기 10초.

### (2) 실패를 예외로 받는다 — `Timeout` 과 `ConnectionError`

**언제 쓰나** — 느린 서버와 아예 닿지 않는 서버를 다르게 다루고 싶을 때 쓴다.
`Timeout` 이면 재시도나 대체 처리(fallback)를, `ConnectionError` 면 연결 실패 처리를 한다.

```text
try:
    requests.get(url, timeout=1)
        │
        ├─ 한도 초과 ──────► except Timeout:          "재시도 또는 fallback"
        └─ DNS 실패·거부 ──► except ConnectionError:  "연결 실패"
```

- `requests.get` 은 실패하면 값을 돌려주지 않고 예외를 던진다.
- `except` 절은 위에서부터 차례로 맞춰 본다.
- 첫 번째로 맞는 절 하나만 실행된다.

> **fallback** — 원래 길이 실패했을 때 대신 쓰는 길.\
> 예: API 가 시간 초과되면 캐시에 둔 값을 돌려준다.

### (3) 재시도 — `Retry` 를 `HTTPAdapter` 에 넣고, 어댑터를 `Session` 에 마운트한다

**언제 쓰나** — 서버가 잠깐 바쁘다고 답하는(429 · 5xx) 일이 있는 API 를 부를 때 쓴다.

```text
Retry(total=3, backoff_factor=1,
      status_forcelist=[429,500,502,503,504],
      allowed_methods=["GET","POST"])
        │  (정책)
        ▼
HTTPAdapter(max_retries=정책)
        │  (정책을 품은 전송기)
        ▼
session.mount("https://", adapter)
session.mount("http://",  adapter)
        │
        ▼
session.get(...) / session.post(...)  ── 이 세션을 거치는 요청에 정책이 붙는다
```

- `Retry` 는 urllib3 의 클래스로, 「몇 번 · 얼마나 쉬고 · 어떤 상태 코드일 때 · 어떤 메서드만」 다시 할지를 담는다.
- `total=3` 은 최대 재시도 횟수다.
- `backoff_factor=1` 은 재시도 사이에 기다리는 시간을 점점 늘리는(지수 백오프) 계수다.
- 원본 주석은 그 대기를 「1초, 2초, 4초…」로 적는다(이 주장의 의심점은 「어디서 틀리나 4」).
- `status_forcelist` 에 든 상태 코드가 오면 재시도한다.
- `allowed_methods` 에 든 HTTP 메서드만 재시도한다.
- `HTTPAdapter(max_retries=...)` 가 정책을 품는다.
- `session.mount(접두사, adapter)` 는 그 접두사로 시작하는 URL 에 이 어댑터를 쓰라는 뜻이다.
- 원본 문장 「세션에 adapter를 마운트하면 모든 요청에 자동 적용」의 「모든 요청」은 **그 세션을 거치는 요청**이다.
- 원본 시연은 세션을 만들고 설정값만 찍을 뿐, 세션으로 요청을 보내지는 않는다.

> **멱등(idempotent)** — 같은 요청을 여러 번 보내도 한 번 보낸 것과 결과가 같은 성질.\
> 예: `GET /users/1` 은 몇 번 보내도 서버 상태가 그대로지만, 주문을 만드는 `POST` 는 두 번 가면 주문이 둘 생길 수 있다.

> **지수 백오프** — 재시도할 때마다 기다리는 시간을 곱절로 늘리는 방식.\
> 예: 1초 → 2초 → 4초.

### (4) 인증 — 세 가지 실어 나르는 법

**언제 쓰나** — API 가 「누구냐」를 확인할 때 쓴다.
API 문서가 정한 방식을 따른다.

```text
auth=("username", "password")            → HTTPBasicAuth 로 바뀌어 Basic 인증
headers={"Authorization": "Bearer ..."}  → OAuth2 Bearer 토큰
headers={"X-API-Key": "..."}             → API 키 (헤더 이름은 서비스마다 다르다)
```

- `auth=` 에 (아이디, 비밀번호) 튜플을 주면 `HTTPBasicAuth` 로 자동 변환된다.
- Bearer 토큰은 `Authorization` 헤더 값 앞에 `Bearer ` 를 붙여 보낸다.
- API 키 헤더 이름은 `X-API-Key` · `Api-Key` · `X-Auth-Token` 처럼 서비스마다 다르다.

> **Bearer 토큰** — 「이 토큰을 가진 사람(bearer)에게 권한을 준다」는 방식의 접근 토큰.\
> 예: `Authorization: Bearer eyJhbG...`.

### (5) 파일 업로드 — `files` 와 `data` 를 함께

**언제 쓰나** — 파일과 설명 같은 폼 필드를 한 요청에 올릴 때 쓴다.

```text
files = {"file": ("report.pdf", 파일객체, "application/pdf")}
data  = {"description": "월간 보고서"}
requests.post(url, files=files, data=data)
        │
        ▼
multipart/form-data 본문
  ├─ 부분 1: 필드 "file"        = report.pdf 의 바이트 (application/pdf)
  └─ 부분 2: 필드 "description" = 월간 보고서
```

- `files` 딕셔너리의 키는 서버가 기대하는 필드 이름이다.
- 값은 `(파일명, 파일객체, MIME타입)` 튜플이다.
- 같은 multipart 본문에 일반 폼 필드를 더하려면 `data` 를 함께 넘긴다.
- 시연은 `io.BytesIO(b"...")` 로 메모리 파일을 만들었고, 실제로는 `open(path, "rb")` 로 연다.
- 시연의 가짜 응답 상태 코드는 201(생성됨)이다.

> **multipart/form-data** — 본문을 여러 부분으로 나눠 파일과 폼 필드를 함께 싣는 요청 형식.\
> 예: 웹 폼에서 첨부 파일과 제목을 같이 보낼 때.

> **MIME 타입** — 데이터의 종류를 나타내는 이름표.\
> 예: `application/pdf` · `image/png`.

### (6) `raise_for_status()` 와 예외 계층 — 한 줄기로 잡는다

**언제 쓰나** — 응답이 왔지만 4xx · 5xx 일 때도 네트워크 실패처럼 예외로 다루고 싶을 때 쓴다.

```text
r = requests.get(url, timeout=5)   ← 404 도 "응답이 온 것"이라 예외가 안 난다
r.raise_for_status()               ← 4xx/5xx 면 여기서 HTTPError 를 던진다
        │
        ▼
except HTTPError        → "HTTP 에러: ..."
except ConnectionError  → "네트워크 연결 실패"
except Timeout          → "요청 시간 초과"
except RequestException → "기타 요청 에러"  (맨 마지막: 모두의 부모)
```

- `requests` 는 404 응답을 받아도 그 자체로는 예외를 내지 않는다.
- `raise_for_status()` 를 불러야 4xx · 5xx 가 `HTTPError` 로 바뀐다.
- 원본 팁대로, 이렇게 하면 HTTP 에러와 네트워크 에러를 같은 `try/except` 한 덩어리에서 일관되게 처리한다.
- `RequestException` 은 모든 `requests` 예외의 부모라 맨 마지막에 둔다.
- 앞에 두면 자식 예외를 전부 먼저 삼켜 아래 절들이 쓸모없어진다.

원본이 보인 계층:

```text
RequestException (base)
  ├── ConnectionError        네트워크 연결 실패
  ├── HTTPError              HTTP 상태 에러 (raise_for_status)
  ├── URLRequired            URL 누락
  ├── TooManyRedirects       리다이렉트 과다
  ├── Timeout                타임아웃 베이스
  │   ├── ConnectTimeout     연결 단계 타임아웃
  │   └── ReadTimeout        읽기 단계 타임아웃
  └── ContentDecodingError   본문 디코드 실패
```

### (7) 시연 장치 — `patch` 와 `MagicMock` 으로 네트워크 없이 돌린다

**언제 쓰나** — 실제 서버 없이 요청 코드의 흐름을 보이거나 테스트할 때 쓴다.

```text
with patch("requests.get") as mock_get:
    mock_get.return_value = mock_response(...)   → requests.get(...) 이 이 가짜 응답을 돌려준다
    mock_get.side_effect  = Timeout("...")       → requests.get(...) 이 이 예외를 던진다
# with 블록을 나오면 원래 requests.get 으로 돌아온다
```

- `patch("requests.get")` 은 블록 안에서 `requests` 모듈의 `get` 을 가짜로 갈아 끼운다.
- `return_value` 는 호출했을 때 돌려줄 값이다.
- `side_effect` 에 예외를 넣으면 호출했을 때 그 예외가 던져진다.
- 헬퍼 `mock_response` 는 `MagicMock` 에 `status_code` · `json()` 의 반환값 · `ok`(2xx 여부) · `text` 를 채운 가짜 응답이다.
- `json_data` 가 없으면 `json()` 은 `{}` 를 돌려준다.
- 가짜 함수는 넘긴 URL · `auth` · `headers` · `timeout` 을 검사하지 않고 정해 둔 값만 돌려준다.
- `MagicMock` 의 메서드는 부르면 그냥 또 다른 `MagicMock` 을 돌려줄 뿐 예외를 내지 않는다.
- 그래서 404 시연에서는 `raise_for_status` 에 `side_effect=HTTPError("404 Not Found")` 를 따로 달아 진짜 응답처럼 예외가 나게 했다.

> **mock** — 진짜 객체 대신 쓰는, 동작을 미리 정해 둔 가짜 객체.\
> 예: `MagicMock()` 의 `.json.return_value = {"data": "ok"}`.

## 문법 — 형태와 규칙

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()
retry = Retry(total=2, backoff_factor=0.5, status_forcelist=[503], allowed_methods=["GET"])
session.mount("https://", HTTPAdapter(max_retries=retry))

try:
    r = session.get("https://api.example.com/items", timeout=(3, 10),
                    headers={"Authorization": "Bearer TOKEN"})
    r.raise_for_status()
    print(r.json())
except requests.exceptions.HTTPError as e:
    print("HTTP 에러:", e)
except requests.exceptions.RequestException as e:
    print("요청 실패:", e)
```

- `timeout=숫자` 또는 `timeout=(connect, read)`.
- `Retry(total=, backoff_factor=, status_forcelist=, allowed_methods=)` → `HTTPAdapter(max_retries=Retry객체)` → `session.mount("https://", adapter)`.
- 재시도 정책은 마운트한 **세션**으로 보낸 요청에 붙는다.
- `auth=(user, pass)` 는 Basic 인증이다.
- 토큰 · 키는 `headers=` 딕셔너리로 보낸다.
- `files={필드명: (파일명, 파일객체, MIME)}` 에 `data={...}` 를 더하면 multipart/form-data 하나로 간다.
- `r.raise_for_status()` 는 4xx · 5xx 에서 `HTTPError` 를 던진다.
- `except` 는 자식 예외부터 쓰고 `RequestException` 을 맨 끝에 둔다.

## 어디서 틀리나

### 1. `timeout` 을 빼먹는다
원본 팁: timeout 은 항상 설정해야 한다.
설정하지 않으면 응답이 안 오는 서버 앞에서 무한히 기다릴 수 있다.
그 요청을 기다리는 스레드나 작업자가 통째로 묶인다.

### 2. 재시도를 멱등하지 않은 요청에 건다
원본 팁: Retry 는 멱등한 요청에만 적용하는 것이 안전하다.
그런데 원본 예제는 `allowed_methods=["GET", "POST"]` 로 `POST` 도 재시도하게 해 두었다.
정답 코드 주석도 「POST는 함정 위험」이라고 짚는다.
서버가 요청을 처리한 뒤 응답만 잃어버린 경우, `POST` 를 다시 보내면 같은 일이 두 번 일어난다(주문 두 번, 결제 두 번).

### 3. `raise_for_status()` 를 부르지 않는다
원본 팁: `raise_for_status()` 로 HTTP 에러를 예외로 바꾸면 일관된 에러 처리가 된다.
부르지 않으면 404 · 500 응답도 그대로 `r` 에 담겨 다음 줄로 넘어간다.
그러면 에러 본문을 정상 데이터로 착각하기 쉽다.

### 4. 백오프 대기 시간을 주석대로 믿는다
원본의 주장: `backoff_factor=1` 이면 대기가 「1초, 2초, 4초…」.
왜 의심스러운가: urllib3 의 백오프 계산은 버전에 따라 다르고, 첫 재시도에는 기다리지 않는 버전이 있는 것으로 안다 (확인 필요).
정확한 대기 시간은 쓰는 urllib3 버전의 문서로 확인해야 한다.

### 5. `except` 순서를 거꾸로 쓴다
`RequestException` 을 맨 앞에 쓰면 모든 `requests` 예외가 거기서 잡힌다.
뒤의 `HTTPError` · `Timeout` 절은 영영 실행되지 않는다.

### 6. 예외 계층 그림을 완전한 것으로 믿는다
원본의 주장: `ConnectTimeout` 은 `Timeout` 아래에만 있다.
왜 의심스러운가: `requests` 에서 `ConnectTimeout` 은 `ConnectionError` 와 `Timeout` 을 둘 다 부모로 둔다고 알려져 있다 (확인 필요).
그렇다면 종합 패턴처럼 `ConnectionError` 절이 `Timeout` 절보다 위에 있을 때 연결 타임아웃은 「네트워크 연결 실패」 쪽으로 잡힌다.
원본 그림에 없는 예외 클래스도 더 있을 수 있다 (확인 필요).

### 7. 세션에 마운트하고 `requests.get` 을 부른다
`session.mount` 로 붙인 재시도 정책은 그 `session` 으로 보낸 요청에만 붙는다.
모듈 함수 `requests.get(...)` 은 그 세션을 거치지 않는다.

### 8. mock 이 「잘 됐다」고 해서 진짜로 된 줄 안다
시연의 `requests.get` 은 가짜라 인증 정보가 맞든 틀리든 같은 응답을 돌려준다.
세 인증 방식이 모두 `{'user': 'admin'}` 을 받는 것은 서버가 확인해 줘서가 아니라 가짜 응답을 그렇게 정했기 때문이다.
`MagicMock` 응답의 `raise_for_status()` 는 따로 정하지 않으면 404 여도 예외를 내지 않는다.
원본 코드는 `mock_open` 을 import 하지만 쓰지 않는다.

### 9. `requests` 의 `ConnectionError` 를 파이썬 내장 `ConnectionError` 와 헷갈린다
원본 코드는 언제나 `requests.exceptions.ConnectionError` 로 적는다.
그냥 `ConnectionError` 라고 쓰면 파이썬 내장 예외를 가리키니 `requests` 의 예외를 놓칠 수 있다 (확인 필요).

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `timeout=(3, 10)` 이 연결 3초 · 읽기 10초, 숫자 하나면 둘 다 그 값 | `requests` 라이브러리의 동작 (원본 근거) |
| `timeout` 을 안 주면 무한 대기할 수 있다 | `requests` 라이브러리의 동작 (원본 팁) |
| `Retry` 의 `total` · `backoff_factor` · `status_forcelist` · `allowed_methods` | urllib3 라이브러리 — 매개변수 이름과 백오프 계산은 버전마다 다를 수 있다 (확인 필요) |
| `auth=` 튜플이 `HTTPBasicAuth` 로 바뀐다 | `requests` 라이브러리의 동작 (원본 근거) |
| 4xx · 5xx 에서 `raise_for_status()` 가 `HTTPError` 를 던진다 | `requests` 라이브러리의 동작 (원본 근거) |
| 예외 계층 구조 | `requests` 라이브러리 — 원본 그림은 일부만 보인다 (확인 필요) |
| `patch` · `MagicMock` · `return_value` · `side_effect` | 파이썬 표준 라이브러리 `unittest.mock` |
| `except` 절을 위에서부터 맞춰 보고 첫 번째 맞는 절만 실행 | 파이썬 언어 |
| f-문자열 안의 딕셔너리가 `{'user': 'admin'}` 꼴로 찍힌다 | 파이썬 언어(딕셔너리의 `repr`) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 어떤 요청이든 | `timeout=` | `timeout` 없는 호출 |
| 같은 API 를 여러 번 부른다 | `Session` + 마운트한 `HTTPAdapter` | 매번 새로 부르는 `requests.get` 에 정책을 기대하기 |
| 일시적 실패(429 · 5xx) 재시도 | `Retry` 를 `GET` 같은 멱등 메서드에 | 주문 · 결제 같은 `POST` 재시도 |
| 아이디 · 비밀번호 인증 | `auth=(user, pass)` | URL 에 비밀번호 넣기 |
| 토큰 · API 키 | `headers=` | 문서와 다른 헤더 이름 |
| 파일과 폼 필드를 함께 | `files=` + `data=` | 파일 내용을 문자열로 `data` 에 억지로 넣기 |
| 4xx · 5xx 를 에러로 다루기 | `raise_for_status()` + `except HTTPError` | `status_code` 를 곳곳에서 손으로 검사 |
| 서버 없이 흐름 시연 · 테스트 | `patch` · `MagicMock` | 실제 외부 API 를 테스트마다 호출 |

## 핵심 문장

1. **`timeout` 은 언제나 준다** — `(connect, read)` 두 칸으로 나눠 정할 수 있다.
2. **재시도는 `Retry` → `HTTPAdapter` → `session.mount` 의 사슬로 세션에 붙고**, 멱등한 요청에만 거는 것이 안전하다.
3. **인증은 `auth=` 튜플이나 헤더로, 파일은 `files=` 튜플(+ `data=`)로 싣는다.**
4. **`raise_for_status()` 가 HTTP 에러를 예외로 바꿔**, 네트워크 실패와 함께 `RequestException` 계층 하나로 처리하게 해 준다 — `except` 는 자식부터, 부모는 맨 끝.
5. **`patch` · `MagicMock` 은 정해 둔 값만 돌려준다** — 시연이 성공해도 실제 서버가 받아 준다는 뜻은 아니다.

## 관련 자료

- `requests-basics` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- [httpx](../14-httpx/2-summary.md)
- `error-handling` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/python/libraries.json` 의 `requests-advanced`

## 용어 풀이

- **timeout** — 요청이 기다릴 최대 시간(초).
- **connect timeout** — 서버와 연결을 맺기까지 기다리는 한도.
- **read timeout** — 연결 뒤 응답 데이터를 기다리는 한도.
- **fallback** — 원래 길이 실패했을 때 대신 쓰는 길.
- **재시도(retry)** — 실패한 요청을 다시 보내는 것.
- **지수 백오프** — 재시도 사이의 대기를 곱절로 늘리는 방식.
- **멱등(idempotent)** — 여러 번 해도 한 번 한 것과 결과가 같은 성질.
- **`HTTPAdapter`** — 세션이 실제 전송에 쓰는 부품. 재시도 정책을 품는다.
- **마운트(`mount`)** — URL 접두사에 어댑터를 연결하는 것.
- **`Session`** — 설정(어댑터 · 헤더 등)을 유지한 채 여러 요청을 보내는 객체.
- **Basic 인증** — 아이디와 비밀번호를 요청에 실어 보내는 인증 방식.
- **Bearer 토큰** — `Authorization: Bearer <토큰>` 으로 보내는 접근 토큰.
- **API 키** — 서비스가 발급한 비밀 문자열. 서비스가 정한 헤더로 보낸다.
- **multipart/form-data** — 파일과 폼 필드를 여러 부분으로 나눠 싣는 본문 형식.
- **MIME 타입** — 데이터 종류의 이름표.
- **`raise_for_status()`** — 4xx · 5xx 응답이면 `HTTPError` 를 던지는 메서드.
- **`RequestException`** — 모든 `requests` 예외의 부모 클래스.
- **mock** — 동작을 미리 정해 둔 가짜 객체.
- **`patch`** — 정해진 범위 안에서 이름(예: `requests.get`)을 가짜로 바꿔 끼우는 도구.
- **`return_value`** — mock 을 불렀을 때 돌려줄 값.
- **`side_effect`** — mock 을 불렀을 때 일으킬 일. 예외를 넣으면 그 예외를 던진다.
- **`BytesIO`** — 메모리 위의 바이트를 파일처럼 다루는 객체.

## 더 들어가면

- read timeout 은 「요청 전체의 제한 시간」이 아니라 서버에서 바이트가 오는 사이사이의 침묵 한도로 알려져 있다. 서버가 조금씩 계속 보내면 전체 시간은 훨씬 길어질 수 있다 (확인 필요).
- urllib3 의 예전 버전에서는 `allowed_methods` 대신 `method_whitelist` 라는 이름을 썼다 (확인 필요).
- urllib3 의 `Retry` 는 기본적으로 멱등한 메서드들만 재시도 대상으로 둔다고 알려져 있다. `POST` 를 넣는 것은 일부러 그 기본을 넓히는 셈이다 (확인 필요).
- 429 응답에 `Retry-After` 헤더가 있으면 `Retry` 가 그 값을 존중해 기다릴 수 있다 (확인 필요).
- 재시도를 다 써도 상태 코드가 그대로면 기본 설정에서는 예외가 난다. `raise_on_status=False` 로 마지막 응답을 그대로 받을 수 있다 (확인 필요).
- `POST` 를 안전하게 재시도해야 한다면 서버가 지원하는 「멱등 키」 헤더로 중복 처리를 막는 방법이 있다 (확인 필요).
- 실제 파일은 `with open(path, "rb") as f:` 안에서 `files=` 에 넘겨, 업로드 뒤 파일이 닫히게 한다.
