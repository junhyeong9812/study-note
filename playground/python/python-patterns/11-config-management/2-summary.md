# python/python-patterns/11 — 설정 관리 — 정리 (힌트)

> 출처 — study-site 항목 `python/config-management`(항목 데이터 `data/python/patterns.json`) · 정답 코드 study-practice `python/python-patterns/reference/config-management.py`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — 실행 환경 · 바깥 네트워크에 따라 달라지는 예제다.

## 한눈에 — 쉽게 말하면

**설정 관리는 「대본은 하나, 공연장 안내문은 공연장마다」다.**
배우가 읽는 대본은 서울 공연이든 부산 공연이든 똑같다.
조명 위치, 비상구, 출입 암호처럼 공연장마다 다른 것은 대본에 적지 않고 공연장 벽에 붙은 안내문에 적는다.
연습실에서는 손으로 쓴 메모장으로 안내문을 대신하고, 출입 암호는 금고에 넣어 둔다.
프로그램도 똑같은 구조다.
코드는 어디서나 같고, DB 주소 · 포트 · 디버그 여부 · 비밀 키처럼 실행되는 곳마다 다른 값은 코드 밖(환경변수)에서 받는다.

> **환경변수** — 운영체제가 프로세스에 넘겨주는 「이름=문자열 값」 쌍이다.\
> 예: 셸에서 `APP_PORT=8080 python app.py` 로 실행하면 프로그램 안에서 `APP_PORT` 를 읽을 수 있다.

| 비유 | 실체 |
|---|---|
| 대본 | 소스 코드 (환경과 무관하게 같다) |
| 공연장 안내문 | OS · 컨테이너 환경변수 |
| 연습실 메모장 | `.env` 파일 (개발용) |
| 안내문 견본(빈칸 양식) | `.env.example` 파일 (커밋한다) |
| 금고 | 시크릿 매니저 |
| 무대감독의 사전 점검 | 필수값 검사(fail-fast) · `pydantic-settings` 의 타입 검증 |
| 공연장 종류별 체크리스트 | `DevelopmentConfig` · `ProductionConfig` · `TestingConfig` |

```text
   [코드: 어디서나 같음]
           │ 읽는다
           ▼
   ┌───────────────────────────┐
   │ 환경변수 (전부 문자열)      │ ◀── 셸 / 컨테이너 / 시크릿 매니저
   │ APP_PORT="8080"           │ ◀── .env (개발 때만, load_dotenv)
   └───────────────────────────┘
           │ 변환 + 검사
           ▼
   설정 객체 (port=8080 : int, debug=True : bool)
```

## 이 주제가 답하려는 질문

1. 실행되는 곳마다 다른 값을 코드에 적지 않고 어떻게 넣고 읽나?
2. 문자열뿐인 환경변수를 어떻게 타입이 있는 설정 객체로 바꾸고, 빠진 값은 어떻게 잡아내나?
3. 개발 · 프로덕션 · 테스트마다 다른 설정 묶음을 어떻게 고르나?
4. `.env` 파일과 비밀 값(시크릿)은 어디에 두고 무엇을 커밋하나?

## 동작 방식

### (1) `os.environ` 으로 읽고, 변환하고, 빠지면 바로 멈춘다

**언제 쓰나** — 라이브러리 없이 환경변수 몇 개를 읽을 때 쓴다.
모든 다른 방식의 바닥이기도 하다.

```text
os.environ["APP_DEBUG"] = "true"        (시연용 · 실제로는 셸이나 .env 가 넣는다)
          │
          ▼
os.environ.get("APP_DEBUG", "false")    → "true"   (문자열)
          │ .lower() == "true"
          ▼
debug = True                            (bool)

os.environ.get("APP_PORT", "8000")      → "8080"
          │ int(...)
          ▼
port = 8080                             (int)

os.environ.get("DATABASE_URL")          → 값 또는 None
          │ if not db_url: raise ValueError("DATABASE_URL is required")
          ▼
없으면 시작하자마자 멈춘다 (fail-fast)
```

- `os.environ` 은 환경변수를 사전처럼 다루는 객체다.
- `.get(키, 기본값)` 은 키가 없을 때 `KeyError` 를 내지 않고 기본값을 돌려준다.
- 환경변수 값은 늘 문자열이라 불린 · 숫자로 쓰려면 직접 바꿔야 한다.
- 불린은 소문자로 바꾼 뒤 `"true"` 와 같은지 비교해서 만든다.
- 숫자는 `int()` 로 바꾼다.
- `DATABASE_URL` 은 기본값 없이 읽고, 비어 있으면 `ValueError` 를 던져 바로 멈춘다.
- `if not db_url` 은 `None` 뿐 아니라 빈 문자열 `""` 도 「없음」으로 친다.

> **fail-fast** — 필요한 것이 빠졌으면 나중에 엉뚱한 곳에서 터지게 두지 말고 시작 시점에 즉시 실패시키는 방식이다.\
> 예: DB 주소가 없으면 첫 쿼리 때가 아니라 프로그램 시작 때 `ValueError` 로 멈춘다.

### (2) `dataclass` 설정 객체와 대안 생성자 `from_env`

**언제 쓰나** — 흩어진 변수 대신 설정을 하나의 객체로 묶고, 기본값과 타입 힌트로 「어떤 설정이 있는가」를 코드에 문서화하고 싶을 때 쓴다.

> **dataclass** — `@dataclass` 를 붙이면 필드 선언만으로 `__init__` · `__repr__` 등을 만들어 주는 표준 라이브러리 기능이다.\
> 예: `@dataclass class P: x: int = 0` 이면 `P(x=3)` 처럼 만들고 `P(x=3)` 꼴로 찍힌다.

```text
@dataclass DatabaseConfig            @dataclass AppConfig
  url = "sqlite:///app.db"             name = "MyApp"
  pool_size = 5                        debug = False
  echo = False                         port = 8000
                                       secret_key = "change-me-in-production"
                                       database = field(default_factory=DatabaseConfig)
                                                   │ 인스턴스마다 새 DatabaseConfig
AppConfig.from_env()   (classmethod)
   │ APP_NAME     → name         (없으면 "MyApp")
   │ APP_DEBUG    → debug        (.lower()=="true")
   │ APP_PORT     → port         (int, 없으면 "8000")
   │ SECRET_KEY   → secret_key   (없으면 "change-me")
   │ DATABASE_URL → database.url (없으면 "sqlite:///app.db")
   │ DB_POOL_SIZE → database.pool_size (int, 없으면 "5")
   ▼
AppConfig(name=..., debug=..., ..., database=DatabaseConfig(...))
```

- `DatabaseConfig` 는 DB 관련 설정만 묶은 작은 묶음이고, `AppConfig` 가 그것을 `database` 필드로 품는다(중첩 설정).
- `database` 의 기본값은 `field(default_factory=DatabaseConfig)` 로 준다.
- `default_factory` 는 인스턴스를 만들 때마다 그 함수를 새로 불러 기본값을 만든다.
- 기본값으로 객체 하나를 직접 두면 모든 인스턴스가 그 한 객체를 함께 쓰게 되므로, 가변 기본값은 이렇게 따로 만든다.
- `from_env` 는 `@classmethod` 라서 `cls(...)` 로 자기 클래스의 인스턴스를 만들어 돌려준다.
- 이렇게 「`__init__` 말고 다른 경로로 객체를 만드는 클래스 메서드」를 대안 생성자 패턴이라 한다.
- `from_env` 안의 변환(`int` · `.lower()=="true"`)은 (1)과 같다.
- `dataclass` 는 타입 힌트를 실행 중에 검사하지 않는다.
- `AppConfig(port="80")` 처럼 문자열을 넘겨도 그대로 문자열이 들어간다.
- 타입이 맞는 것은 `from_env` 안에서 직접 `int()` 로 바꿔 줬기 때문이다.

> **대안 생성자** — 생성자(`__init__`) 대신 다른 재료(환경변수, 파일 등)로 인스턴스를 만들어 주는 클래스 메서드다.\
> 예: `AppConfig.from_env()` · `dict.fromkeys(...)`.

### (3) `python-dotenv` — `.env` 파일을 환경변수로 올린다

**언제 쓰나** — 개발 중에 매번 셸에 환경변수를 넣기 번거로울 때, 값을 `.env` 파일에 적어 두고 시작할 때 읽어 들인다.
원본 예제에서는 라이브러리 없이 돌도록 사용법을 문자열로만 보여 준다.

```text
.env 파일                         load_dotenv()
APP_NAME=MyApp        ──────────▶  os.environ 에 없는 키만 채운다
APP_DEBUG=true                    (이미 있는 환경변수는 덮어쓰지 않음)
DATABASE_URL=postgresql://...
SECRET_KEY=super-secret-key-123

.env.local            ──────────▶  load_dotenv(".env.local", override=True)
                                  이미 있는 값도 덮어쓴다
          │
          ▼
db_url = os.environ["DATABASE_URL"]   (이후에는 (1)과 같이 os.environ 으로 읽는다)
```

- `load_dotenv()` 는 기본으로 `.env` 파일을 읽어 그 안의 `키=값` 을 환경변수로 올린다.
- 기본 동작은 기존 환경변수를 덮어쓰지 않는다 — 셸이 준 값이 이긴다.
- `override=True` 를 주면 파일의 값이 기존 값을 덮어쓴다.
- 파일 이름을 넘기면(`".env.local"`) 그 파일을 읽는다.
- 읽어 들인 뒤에는 따로 객체가 생기는 것이 아니라, 그냥 `os.environ` 으로 읽는다.

> **`.env` 파일** — 한 줄에 `이름=값` 꼴로 환경변수를 적어 둔 텍스트 파일이다.\
> 예: `APP_DEBUG=true` 한 줄.

### (4) `pydantic-settings` — 자동 로드와 타입 검증

**언제 쓰나** — 실무에서 가장 권장되는 방식이다(원본 주석).
환경변수 읽기 · 타입 변환 · 검증 · 문서화를 클래스 선언 하나로 끝내고 싶을 때 쓴다.

> **`pydantic-settings`** — `BaseSettings` 를 상속한 클래스의 필드를 환경변수에서 자동으로 채우고 선언된 타입으로 검증해 주는 라이브러리다.\
> 예: `port: int = 8000` 필드는 환경변수 `PORT="8080"` 을 읽어 정수 `8080` 이 된다.

```text
class Settings(BaseSettings):
    app_name: str = "MyApp"           ◀── APP_NAME (대소문자 구분 안 함)
    debug: bool = False               ◀── DEBUG
    port: int = 8000                  ◀── PORT
    database_url: str                 ◀── DATABASE_URL  (기본값 없음 = 필수)
    secret_key: str = Field(..., min_length=16)   (필수 + 16자 이상)
    redis_url: str = "redis://localhost:6379"
    allowed_hosts: list[str] = ["localhost"]
    class Config:
        env_file = ".env"   env_file_encoding = "utf-8"
        env_prefix = ""     case_sensitive = False
          │
          ▼
settings = Settings()   → 환경변수 · .env 를 읽어 채우고 타입 검증
          │                 맞지 않거나 필수값이 없으면 여기서 오류
          ▼
settings.database_url , settings.debug  (이미 변환된 값)
```

- 필드 이름이 곧 환경변수 이름이다(`case_sensitive = False` 라 대소문자를 가리지 않는다).
- 기본값이 없는 필드(`database_url`)는 필수다.
- `Field(..., min_length=16)` 의 `...` 은 「기본값 없음 = 필수」 표시이고, `min_length=16` 은 16자 이상이어야 한다는 검증 조건이다.
- `Config` 안의 `env_file = ".env"` 로 `.env` 파일도 자동으로 읽는다 — (3)의 `load_dotenv()` 를 따로 부를 필요가 없다.
- `env_prefix` 는 환경변수 이름 앞에 붙는 접두사다.
- `DatabaseSettings` 처럼 `env_prefix = "DB_"` 를 주면 필드 `url` 은 `DB_URL`, `pool_size` 는 `DB_POOL_SIZE` 에 대응한다.
- `Settings()` 를 만드는 순간 읽기와 검증이 일어나므로, 잘못된 설정은 (1)의 fail-fast 처럼 시작 때 드러난다.
- (2)의 `dataclass` 와 달리 타입이 맞지 않는 값(예: `PORT=abc`)은 객체를 만들 때 오류가 된다.

### (5) 환경별 설정 클래스와 `get_config`

**언제 쓰나** — 개발 · 프로덕션 · 테스트처럼 정해진 몇 가지 환경마다 설정 묶음이 통째로 다를 때 쓴다.

```text
BaseConfig            APP_NAME="MyApp", LOG_LEVEL="INFO"
  ├─ DevelopmentConfig  DEBUG=True,  DATABASE_URL="sqlite:///dev.db", LOG_LEVEL="DEBUG"
  ├─ ProductionConfig   DEBUG=False, DATABASE_URL=os.environ.get("DATABASE_URL",""), LOG_LEVEL="WARNING"
  └─ TestingConfig      TESTING=True, DATABASE_URL="sqlite:///:memory:"   (DEBUG 없음, LOG_LEVEL 물려받음)

get_config():
   env = os.environ.get("APP_ENV", "development")
   configs = {"development": Dev.., "production": Prod.., "testing": Test..}
   return configs.get(env, DevelopmentConfig)()    ← 클래스를 골라 () 로 인스턴스화

출력 줄 만들기: getattr(cfg, "DEBUG", False)   ← DEBUG 가 없으면 False
```

- 공통 값은 `BaseConfig` 에 두고, 환경마다 다른 값만 하위 클래스에서 덮어쓴다(상속).
- 하위 클래스가 덮어쓰지 않은 속성(`TestingConfig` 의 `LOG_LEVEL`)은 부모 값을 그대로 쓴다.
- 테스트는 `sqlite:///:memory:` 인메모리 DB 로 다른 데이터와 격리한다.
- `get_config` 는 `APP_ENV` 값을 키로 사전에서 클래스를 찾고, 없는 키면 `DevelopmentConfig` 를 쓴다.
- 값에 따라 쓸 구현을 사전에서 고르는 이 꼴을 원본은 「전략 패턴 + 매핑」이라 부른다.
- `TestingConfig` 에는 `DEBUG` 가 없어서 `cfg.DEBUG` 로 읽으면 `AttributeError` 가 난다 — 그래서 `getattr(cfg, 'DEBUG', False)` 로 기본값을 준다.
- 클래스 본문의 대입문은 클래스를 정의할 때 **한 번** 실행된다.
- 그래서 `ProductionConfig.DATABASE_URL` 은 `get_config()` 를 부를 때가 아니라 모듈이 `class ProductionConfig` 줄을 지날 때의 환경변수 값으로 굳는다.

> **`getattr(객체, 이름, 기본값)`** — 객체의 속성을 이름(문자열)으로 읽되, 없으면 기본값을 돌려주는 내장 함수다.\
> 예: `getattr(cfg, "DEBUG", False)`.

### (6) 12-Factor 원칙과 파일 관리

**언제 쓰나** — 위 방식들을 어떤 규칙으로 묶어 쓸지 정할 때의 기준이다.

> **12-Factor App** — 배포하기 쉬운 서비스를 위한 원칙 모음이고, 그중 하나가 「설정은 환경에 둔다」이다.\
> 예: 같은 이미지(코드)를 개발 · 운영에 그대로 올리고 환경변수만 바꾼다.

```text
저장소(git)에 들어가는 것           들어가지 않는 것
 ├─ 코드                           ├─ .env         (.gitignore 에 추가)
 └─ .env.example                   └─ 시크릿(비밀 키, DB 비밀번호)
    (필요한 이름 목록, 값은 비움/예시)

개발:      .env  → load_dotenv / pydantic env_file
프로덕션:  OS · 컨테이너 환경변수, 시크릿 매니저
```

- 원칙 1: 설정은 환경변수로 관리하고 코드에 하드코딩하지 않는다.
- 원칙 2: `.env` 파일은 개발용이고, 프로덕션은 OS · 컨테이너 환경변수를 쓴다.
- 원칙 3: 시크릿은 절대 코드나 깃에 넣지 않는다.
- 원칙 4: 환경(dev / staging / prod)마다 설정이 다르다.
- 원칙 5: `.env.example` 파일로 필요한 환경변수를 문서화한다.
- 팁: `.env` 는 `.gitignore` 에 추가하고 `.env.example` 을 커밋한다.
- 팁: 프로덕션에서는 OS 환경변수나 시크릿 매니저를 쓴다.

> **시크릿 매니저** — 비밀 값을 암호화해 보관하고 권한 있는 프로그램에만 넘겨주는 별도 서비스다.\
> 예: 배포 때 DB 비밀번호를 시크릿 매니저에서 받아 환경변수로 넣는다.

## 문법 — 형태와 규칙

```python
import os
from dataclasses import dataclass, field

@dataclass
class Db:
    url: str = "sqlite:///app.db"

@dataclass
class Cfg:
    debug: bool = False
    db: Db = field(default_factory=Db)

    @classmethod
    def from_env(cls) -> "Cfg":
        return cls(debug=os.environ.get("DEBUG", "false").lower() == "true",
                   db=Db(url=os.environ.get("DB_URL", "sqlite:///app.db")))
```

- `os.environ.get("K", "기본")` — 없으면 기본값, `os.environ["K"]` — 없으면 `KeyError`.
- 값은 늘 `str` 이다 → 불린은 `.lower() == "true"`, 정수는 `int(...)`.
- 필수값은 기본값 없이 읽고 `if not 값: raise ValueError(...)` 로 막는다.
- `dataclass` 의 가변 · 중첩 기본값은 `field(default_factory=클래스)` 로 준다.
- 대안 생성자는 `@classmethod` + `return cls(...)`.
- `load_dotenv()` — `.env` 를 읽되 덮어쓰지 않음, `load_dotenv(경로, override=True)` — 덮어씀.
- `BaseSettings` 필드: 기본값 있으면 선택, 없으면 필수, `Field(..., 조건)` 은 필수 + 검증 조건.
- `Config` 의 네 옵션:

| 옵션 | 원본 값 | 뜻 |
|---|---|---|
| `env_file` | `".env"` | 이 파일도 자동으로 읽는다 |
| `env_file_encoding` | `"utf-8"` | 그 파일의 인코딩 |
| `env_prefix` | `""` / `"DB_"` | 환경변수 이름 앞 접두사 (`"DB_"` 면 `url` ↔ `DB_URL`) |
| `case_sensitive` | `False` | 환경변수 이름의 대소문자를 가리지 않는다 |

- 환경 고르기: `사전.get(키, 기본클래스)()` — 끝의 `()` 가 인스턴스를 만든다.

## 어디서 틀리나

### 1. 환경변수는 늘 문자열이다

`"false"` 도 빈 문자열이 아니므로 `bool("false")` 는 `True` 다.
그래서 원본은 `bool()` 대신 `.lower() == "true"` 로 비교한다.
대신 이 비교는 `"true"` (대소문자 무시) 하나만 참으로 본다 — `"1"` · `"yes"` · `"on"` 은 전부 `False` 가 된다.
팀이 `APP_DEBUG=1` 로 적는 관례라면 조용히 디버그가 꺼진다.

### 2. `os.environ[...]` 과 `.get()` 은 없을 때가 다르다

`.get(키, 기본값)` 은 키가 없어도 `KeyError` 가 나지 않는다.
`os.environ["DATABASE_URL"]` 은 키가 없으면 `KeyError` 다.
기본값을 주는 것이 늘 좋은 것은 아니다 — 프로덕션에 꼭 있어야 하는 값에 기본값을 주면 빠져도 조용히 뜬다.

### 3. 필수값 검사와 기본값이 섞이면 결과가 갈린다

섹션 1은 `DATABASE_URL` 이 없으면 `ValueError` 로 멈춘다.
하지만 같은 파일의 `from_env` 는 `DATABASE_URL` 이 없으면 `"sqlite:///app.db"` 로 조용히 뜬다.
`ProductionConfig` 는 없으면 빈 문자열 `""` 이 된다.
같은 값을 세 군데서 세 방식으로 다루면 어느 경로로 실행했느냐에 따라 결과가 달라진다.

### 4. 기본값이 두 곳에서 어긋난다

`AppConfig` 의 필드 기본값은 `secret_key = "change-me-in-production"` 이다.
`from_env` 의 기본값은 `"change-me"` 다.
`SECRET_KEY` 가 없으면 `from_env` 로 만든 객체는 `"change-me"` 를 갖는다.
게다가 비밀 키에 기본값이 있으면 프로덕션에서 약한 키로 조용히 뜰 수 있다 — `pydantic-settings` 예제처럼 `Field(..., min_length=16)` 로 필수 · 길이 검사를 거는 편이 안전하다.

### 5. 중첩 기본값을 `default_factory` 없이 주기

`database: DatabaseConfig = DatabaseConfig()` 처럼 객체 하나를 기본값으로 두면, 기본값을 쓰는 모든 `AppConfig` 가 그 한 객체를 같이 쓴다.
하나를 고치면 다른 인스턴스에서도 바뀐 것처럼 보인다.
원본 주석대로 가변 기본값은 `default_factory` 로 인스턴스마다 새로 만든다.

### 6. 클래스 속성은 정의할 때 한 번만 읽힌다

`ProductionConfig.DATABASE_URL = os.environ.get(...)` 은 클래스 본문이 실행될 때, 즉 모듈을 처음 읽을 때 평가된다.
그 뒤에 환경변수를 바꾸거나 `load_dotenv()` 를 늦게 불러도 이 값은 바뀌지 않는다.
환경변수를 읽는 클래스 속성이 있다면 그 전에 환경이 다 채워져 있어야 한다.

### 7. 하위 클래스마다 속성이 다르다

`TestingConfig` 에는 `DEBUG` 가 없고 `TESTING` 만 있다.
`cfg.DEBUG` 로 바로 읽으면 testing 에서 `AttributeError` 가 난다.
원본은 `getattr(cfg, 'DEBUG', False)` 로 피한다.
`get_config` 는 모르는 `APP_ENV` 값(오타 포함)을 만나면 오류 없이 `DevelopmentConfig` 로 떨어진다 — 프로덕션에서 오타가 나면 개발 설정으로 뜬다.

### 8. `load_dotenv()` 는 기본으로 덮어쓰지 않는다

셸에 이미 `DATABASE_URL` 이 있으면 `.env` 의 값은 무시된다.
`.env` 를 고쳤는데 안 바뀐다면 이 때문이다.
덮어쓰려면 `override=True` 를 준다.

### 9. `.env` 를 커밋하기

`.env` 에는 실제 비밀 값이 들어가므로 `.gitignore` 에 추가한다.
대신 이름만 적은 `.env.example` 을 커밋해 어떤 환경변수가 필요한지 알린다.
프로덕션은 `.env` 대신 OS · 컨테이너 환경변수나 시크릿 매니저를 쓴다.

### 10. 시연용 `os.environ[...] = ...` 를 실제 코드에 남기기

원본 섹션 1의 대입은 시연용이다(주석: 실제로는 셸이나 `.env` 에서 주입).
실제 코드에 남기면 셸이 넘긴 진짜 값을 코드가 덮어써서 「설정은 코드 밖」 원칙이 깨진다.

### 11. 원본 `pydantic-settings` 예제의 꼴

원본의 주장: `class Settings(BaseSettings)` 안에 `class Config:` 를 두고 `env_file` · `env_prefix` 등을 적는다.
왜 의심스러운가: 이 꼴은 pydantic 의 예전 방식이고, 최근 `pydantic-settings` 는 `model_config = SettingsConfigDict(...)` 꼴을 쓴다고 알려져 있다 (확인 필요).
또 원본은 `DatabaseSettings` 를 「중첩 설정」이라 부르지만, 예제 안에서 `Settings` 의 필드로 들어가 있지 않다 — 접두사를 따로 쓰는 별도 설정 클래스다.

### 12. `dataclass` 는 타입을 지켜 주지 않는다

`port: int` 라고 적어도 `AppConfig(port="80")` 은 그대로 문자열을 담는다.
`from_env` 를 거치지 않고 직접 만들면 타입이 틀린 설정이 조용히 생긴다.
타입 검증이 필요하면 `pydantic-settings` 를 쓴다(팁: 자동 로드 + 타입 검증).

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `os.environ` 의 값은 문자열이고 `.get()` 은 없을 때 기본값을 돌려준다 | Python 표준 라이브러리 `os` 의 동작 |
| 클래스 본문의 대입은 클래스 정의 때 한 번 실행된다 | Python 언어 규칙 |
| `dataclass` 는 타입 힌트를 실행 중에 검사하지 않는다 · `default_factory` 는 인스턴스마다 불린다 | 표준 라이브러리 `dataclasses` 의 동작 |
| `load_dotenv()` 기본은 덮어쓰지 않고 `override=True` 면 덮어쓴다 | 서드파티 `python-dotenv` 의 동작 (버전별 차이는 확인 필요) |
| `BaseSettings` 의 자동 로드 · 타입 검증 · `Config` 옵션 이름 | 서드파티 `pydantic-settings` 의 동작 — 설정 꼴은 버전에 따라 다르다 (확인 필요) |
| `"true"` 만 참으로 보는 불린 변환 · 모르는 `APP_ENV` 면 개발 설정 | 이 예제 코드의 설계 선택 |
| 12-Factor 원칙 · `.env` 는 개발용 · `.env.example` 커밋 | 언어 보장이 아니라 업계 관례 · 방법론 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 스크립트에서 값 두세 개 | `os.environ.get` + 직접 변환 + 필수값 fail-fast | 설정 클래스 계층 |
| 라이브러리 없이 설정을 한 객체로 | `dataclass` + `from_env` 대안 생성자 | 모듈 곳곳의 흩어진 `os.environ` 호출 |
| 실무 서비스, 타입 · 필수값 검증 필요 | `pydantic-settings` `BaseSettings` | 검증 없는 `dataclass` 에 문자열 그대로 |
| 개발 때 값을 파일에 적어 두기 | `.env` + `load_dotenv()` 또는 `env_file` | 코드에 하드코딩 · `.env` 커밋 |
| 프로덕션 비밀 값 | OS · 컨테이너 환경변수, 시크릿 매니저 | `.env` 파일 · 코드 속 기본값 |
| 정해진 환경 몇 개마다 묶음이 다름 | 환경별 설정 클래스 + `APP_ENV` 매핑 | 코드 곳곳의 `if env == "prod"` |

## 핵심 문장

1. **설정은 코드 밖(환경변수)에 두고, 코드는 어디서나 같게 둔다.**
2. **환경변수는 늘 문자열이다** — 불린 · 숫자로 바꾸는 일과 빠진 값을 시작 때 막는 일(fail-fast)은 누군가 해야 한다.
3. **`dataclass` 는 설정을 묶고 문서화하지만 타입은 검사하지 않고, `pydantic-settings` 는 읽기 · 변환 · 검증을 한 번에 한다.**
4. **환경별 차이는 공통 베이스를 상속한 설정 클래스와 `APP_ENV` 매핑으로 고른다.**
5. **`.env` 는 개발용으로 `.gitignore` 에, `.env.example` 은 커밋, 시크릿은 환경변수나 시크릿 매니저로.**

## 관련 자료

- [data-validation](../20-data-validation/2-summary.md)
- `clean-code` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/python/patterns.json` 의 `config-management`

## 용어 풀이

- **환경변수** — 운영체제가 프로세스에 넘기는 「이름=문자열」 쌍이다.
- **`os.environ`** — 환경변수를 사전처럼 읽고 쓰는 `os` 모듈의 객체다.
- **fail-fast** — 필요한 것이 빠졌으면 시작 시점에 즉시 실패시키는 방식이다.
- **dataclass** — 필드 선언만으로 생성자 · `repr` 등을 만들어 주는 표준 기능이다.
- **`default_factory`** — 인스턴스를 만들 때마다 불러서 기본값을 새로 만드는 함수다.
- **가변 기본값** — 리스트 · 사전 · 객체처럼 나중에 내용이 바뀔 수 있는 기본값이다.
- **`@classmethod`** — 인스턴스가 아니라 클래스(`cls`)를 첫 인자로 받는 메서드다.
- **대안 생성자** — `__init__` 말고 다른 재료로 인스턴스를 만들어 주는 클래스 메서드다.
- **`python-dotenv`** — `.env` 파일을 읽어 환경변수로 올리는 라이브러리다.
- **`.env` 파일** — `이름=값` 을 줄마다 적은 개발용 설정 파일이다.
- **`.env.example`** — 필요한 환경변수 이름을 적어 커밋하는 견본 파일이다.
- **`override`** — `load_dotenv` 가 기존 환경변수를 덮어쓸지 정하는 인자다.
- **`pydantic-settings`** — 환경변수를 자동으로 읽어 타입을 검증하는 설정 라이브러리다.
- **`BaseSettings`** — `pydantic-settings` 에서 설정 클래스가 상속하는 바탕 클래스다.
- **`Field(...)`** — 필드에 필수 여부 · 검증 조건을 붙이는 pydantic 함수다(`...` 은 필수).
- **`env_prefix`** — 필드 이름 앞에 붙여 환경변수 이름을 만드는 접두사다.
- **`case_sensitive`** — 환경변수 이름의 대소문자를 가릴지 정하는 옵션이다.
- **`getattr`** — 속성을 이름으로 읽고 없으면 기본값을 주는 내장 함수다.
- **전략 패턴** — 상황에 따라 쓸 구현(여기서는 설정 클래스)을 바꿔 끼우는 설계다.
- **인메모리 DB** — 파일 없이 메모리에만 있다가 끝나면 사라지는 DB 다(`sqlite:///:memory:`).
- **12-Factor App** — 설정을 환경에 두는 것을 포함한 서비스 설계 원칙 모음이다.
- **시크릿 매니저** — 비밀 값을 보관하고 권한 있는 곳에만 넘겨주는 서비스다.

## 더 들어가면

- 최근 `pydantic-settings` 는 `class Config` 대신 `model_config = SettingsConfigDict(env_file=".env", env_prefix="DB_")` 꼴을 쓴다고 알려져 있다 (확인 필요).
- `pydantic-settings` 의 불린 변환은 `"1"` · `"yes"` · `"on"` 같은 값도 참으로 받는다고 알려져 있다 — 손으로 쓴 `.lower() == "true"` 보다 넓다 (확인 필요).
- `list[str]` 같은 복합 타입 필드는 환경변수 값을 JSON 으로 해석한다고 알려져 있다(`ALLOWED_HOSTS='["a","b"]'`) (확인 필요).
- 진짜 중첩(설정 안의 설정)을 환경변수로 채울 때는 `env_nested_delimiter="__"` 같은 옵션을 쓴다고 알려져 있다 (확인 필요).
- 비밀 값 필드를 `SecretStr` 로 선언하면 `repr` 에 값이 가려진다고 알려져 있다 — `dataclass` 의 `repr` 은 `secret_key` 를 그대로 찍는다 (확인 필요).
- 검증 실패 때 나는 예외는 pydantic 의 `ValidationError` 다 (확인 필요).
- `dataclass` 는 Python 3.11 이후 해시할 수 없는 기본값(기본 설정의 dataclass 인스턴스 포함)을 정의 시점에 `ValueError` 로 막는다고 알려져 있다 — 이전 버전은 `list` · `dict` · `set` 만 막았다 (확인 필요).
- `os.environ` 을 고치면 현재 프로세스와 그 뒤에 만든 자식 프로세스에만 보이고, 부모 셸에는 영향이 없다 (확인 필요).
