# python/python-patterns/11 — 설정 관리 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. `"true"` 계열만 `True`, `"1"` · `"yes"` 는 `False`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
true True
TRUE True
1 False
yes False
```

**왜 그런가**
`.lower()` 가 `"TRUE"` 를 `"true"` 로 바꾸므로 앞의 둘은 `"true"` 와 같아 `True` 다.
`"1"` 과 `"yes"` 는 소문자로 바꿔도 `"true"` 가 아니므로 `False` 다.
이 변환은 `"true"` 하나만 참으로 본다.
근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 1」.

### 2. 환경변수는 늘 문자열이라서

환경변수 값은 늘 문자열이므로, 포트를 숫자로 쓰려면 `int()` 로, 디버그를 불린으로 쓰려면 비교로 바꿔야 한다.
`bool("false")` 는 비어 있지 않은 문자열이라 `True` 가 되므로, `bool()` 로 감싸면 `APP_DEBUG=false` 도 디버그가 켜진다.
그래서 소문자로 바꾼 뒤 `"true"` 와 같은지를 본다.
근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 1」.

### 3. testing 줄은 `debug=False, log=INFO`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
  development: debug=True, log=DEBUG
  production: debug=False, log=WARNING
  testing: debug=False, log=INFO
```

**왜 그런가**
`get_config` 가 `APP_ENV` 값으로 사전에서 클래스를 골라 인스턴스를 만든다.
development · production 은 각자 `DEBUG` 와 `LOG_LEVEL` 을 덮어쓴다.
`TestingConfig` 에는 `DEBUG` 가 없어 `getattr` 의 기본값 `False` 가 쓰이고, `LOG_LEVEL` 은 덮어쓰지 않았으므로 `BaseConfig` 의 `"INFO"` 를 물려받는다.
근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 7」.

### 4. 정의할 때의 값 `postgresql://old`

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
postgresql://old
```

**왜 그런가**
클래스 본문의 대입문은 `class ProductionConfig:` 를 지나는 그 순간 한 번 실행된다.
그때 환경변수는 `"postgresql://old"` 였으므로 그 문자열이 클래스 속성으로 굳는다.
뒤에서 환경변수를 바꿔도, 인스턴스를 새로 만들어도 클래스 속성은 다시 계산되지 않는다.
근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 6」.

### 5. 모든 인스턴스가 한 객체를 함께 쓰지 않게

`DatabaseConfig()` 를 기본값으로 직접 두면 그 객체 하나가 기본값으로 쓰여, 기본값을 쓰는 모든 `AppConfig` 가 같은 `DatabaseConfig` 를 함께 가진다.
한 인스턴스에서 `database.pool_size` 를 고치면 다른 인스턴스도 바뀐 것처럼 보인다.
`default_factory` 는 인스턴스를 만들 때마다 `DatabaseConfig` 를 새로 불러 각자 자기 것을 갖게 한다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 5」.

### 6. 빈 문자열은 걸리고, `from_env` 는 조용히 sqlite 로 뜬다

빈 문자열은 통과하지 못한다 — `if not db_url` 은 `""` 도 참으로 보므로 `ValueError("DATABASE_URL is required")` 가 난다.
`from_env` 는 `os.environ.get("DATABASE_URL", "sqlite:///app.db")` 로 읽으므로 키가 없으면 오류 없이 `"sqlite:///app.db"` 가 된다.
같은 값을 섹션 1은 필수로, `from_env` 는 선택으로 다룬다.
근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 3」.

### 7. 기본은 그대로 두고, `override=True` 면 덮어쓴다

`load_dotenv()` 는 기본으로 이미 있는 환경변수를 덮어쓰지 않는다 — 셸의 `DATABASE_URL` 이 남는다.
`load_dotenv(".env.local", override=True)` 는 `.env.local` 을 읽고, 이미 있는 값도 파일의 값으로 덮어쓴다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 8」.

### 8. `dataclass` 는 문자열을 그대로 담고, pydantic 은 만들 때 막는다

`dataclass` 는 타입 힌트를 실행 중에 검사하지 않으므로 `port` 에는 문자열 `"80"` 이 그대로 들어간다.
`pydantic-settings` 는 `Settings()` 를 만드는 순간 환경변수를 읽어 선언된 타입으로 검증하므로, `port: int` 에 `"abc"` 가 오면 객체를 만들 때 오류가 난다.
그래서 잘못된 설정이 시작 시점에 드러난다 — (1)의 fail-fast 와 같은 효과다.
근거: 2-summary 「동작 방식 (2)」 · 「동작 방식 (4)」 · 「어디서 틀리나 12」.

### 9. 클래스 하나와 사전 한 줄, 오타면 개발 설정

`BaseConfig` 를 상속한 `StagingConfig` 를 만들고, `get_config` 의 `configs` 사전에 `"staging": StagingConfig` 한 줄을 더하면 된다 — 고르는 코드 자체는 그대로다.
매핑에 없는 값이면 `configs.get(env, DevelopmentConfig)` 의 기본값 때문에 `DevelopmentConfig` 가 오류 없이 골라진다.
값에 따라 쓸 구현을 사전에서 바꿔 끼우는 것이 원본이 말한 「전략 패턴 + 매핑」이다.
근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 7」.

### 10. `.env.example` 을 커밋하고, 비밀 키는 환경변수 · 시크릿 매니저로

`.env` 는 실제 값(비밀 포함)이 들어가므로 `.gitignore` 에 넣고 커밋하지 않는다.
`.env.example` 에는 필요한 환경변수 이름을 적어 커밋해, 무엇을 채워야 하는지 문서로 남긴다.
프로덕션 비밀 키는 `.env` 나 코드 속 기본값이 아니라 OS · 컨테이너 환경변수나 시크릿 매니저에서 받는다.
근거: 2-summary 「동작 방식 (6)」 · 「어디서 틀리나 9」.

## 실습 정답

### 실습 1. 다섯 가지 설정 관리 방식을 한 파일에 늘어놓기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 제목과 시연용 환경변수 넷 | `print("=== os.environ ===")` · `os.environ["APP_NAME"] = "MyApp"` 등 네 줄 |
| 2. `APP_NAME` 기본값 | `os.environ.get("APP_NAME", "DefaultApp")` |
| 3. 디버그 불린 | `os.environ.get("APP_DEBUG", "false").lower() == "true"` |
| 4. 포트 정수 | `int(os.environ.get("APP_PORT", "8000"))` |
| 5. 필수값 fail-fast | `db_url = os.environ.get("DATABASE_URL")` · `if not db_url: raise ValueError(...)` |
| 6. 네 줄 찍기 | `print(f"APP_NAME: {app_name}")` 등 네 줄 |
| 7. 제목 | `print("\n=== dataclass 설정 ===")` |
| 8. 두 설정 dataclass | `@dataclass class DatabaseConfig` · `@dataclass class AppConfig` |
| 9. 인스턴스마다 새 DB 설정 | `database: DatabaseConfig = field(default_factory=DatabaseConfig)` |
| 10. 대안 생성자 | `@classmethod def from_env(cls)` 의 `return cls(...)` |
| 11. 설정 객체 찍기 | `config = AppConfig.from_env()` · `print(f"Config: {config}")` |
| 12. dotenv 사용 예 | `print("\n=== python-dotenv ===")` 와 `load_dotenv()` 가 든 여러 줄 문자열 |
| 13. pydantic-settings 사용 예 | `print("=== pydantic-settings ===")` 와 `class Settings(BaseSettings)` · `class DatabaseSettings` 가 든 여러 줄 문자열 |
| 14. 제목 | `print("\n=== 환경별 설정 ===")` |
| 15. 환경별 클래스 셋 | `DevelopmentConfig` · `ProductionConfig` · `TestingConfig` (모두 `BaseConfig` 상속) |
| 16. 환경 고르기 | `get_config()` 의 `configs` 사전과 `configs.get(env, DevelopmentConfig)()` |
| 17. 세 환경 미리보기 | `for env in [...]` 반복문의 `getattr(cfg, 'DEBUG', False)` |
| 18. 12-Factor 다섯 원칙 | `print("\n=== 12-Factor App 설정 원칙 ===")` 아래 `print("1. …")` ~ `print("5. …")` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-patterns/reference/config-management.py`

```python
# [디자인 패턴 & 실무] 설정 관리
# 설명: 환경변수, dotenv, pydantic-settings, 12-factor 원칙의 설정 관리
# 팁: pydantic-settings는 환경변수를 자동으로 로드하고 타입 검증까지 해준다. .env 파일은 .gitignore에 추가하고, .env.example을 커밋한다. 프로덕션에서는 OS 환경변수나 시크릿 매니저를 사용한다.

# 환경변수 접근용 표준 모듈
import os
# 설정 객체를 dataclass로 표현
from dataclasses import dataclass, field
from typing import Optional

# === 1. os.environ 기본 ===
print("=== os.environ ===")
# 환경변수 설정 (시연용 - 실제로는 셸이나 .env에서 주입)
os.environ["APP_NAME"] = "MyApp"
os.environ["APP_DEBUG"] = "true"
os.environ["APP_PORT"] = "8080"
os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost/db"

# .get(키, 기본값): 키가 없어도 KeyError 안 남
app_name = os.environ.get("APP_NAME", "DefaultApp")
# 환경변수는 항상 문자열 -> 불린/숫자로 변환 필요
debug = os.environ.get("APP_DEBUG", "false").lower() == "true"
port = int(os.environ.get("APP_PORT", "8000"))
db_url = os.environ.get("DATABASE_URL")
# 필수 환경변수가 누락된 경우 즉시 실패시키는 것이 안전 (fail-fast)
if not db_url:
    raise ValueError("DATABASE_URL is required")

print(f"APP_NAME: {app_name}")
print(f"DEBUG: {debug}")
print(f"PORT: {port}")
print(f"DB: {db_url}")

# === 2. dataclass 기반 설정 ===
print("\n=== dataclass 설정 ===")

# 중첩된 설정: 데이터베이스 관련 설정 그룹
@dataclass
class DatabaseConfig:
    url: str = "sqlite:///app.db"
    pool_size: int = 5
    echo: bool = False

# 최상위 앱 설정
@dataclass
class AppConfig:
    name: str = "MyApp"
    debug: bool = False
    port: int = 8000
    secret_key: str = "change-me-in-production"
    # 가변 기본값(중첩 dataclass)은 default_factory로 - 인스턴스마다 새로 생성
    database: DatabaseConfig = field(default_factory=DatabaseConfig)

    # 환경변수에서 설정을 로드하는 팩토리 메서드 (대안 생성자 패턴)
    @classmethod
    def from_env(cls) -> 'AppConfig':
        return cls(
            name=os.environ.get("APP_NAME", "MyApp"),
            debug=os.environ.get("APP_DEBUG", "false").lower() == "true",
            port=int(os.environ.get("APP_PORT", "8000")),
            secret_key=os.environ.get("SECRET_KEY", "change-me"),
            database=DatabaseConfig(
                url=os.environ.get("DATABASE_URL", "sqlite:///app.db"),
                pool_size=int(os.environ.get("DB_POOL_SIZE", "5")),
            )
        )

config = AppConfig.from_env()
print(f"Config: {config}")

# === 3. python-dotenv ===
print("\n=== python-dotenv ===")
# 코드 예시 출력 (실제 import는 라이브러리 필요)
print("""
# .env 파일:
# APP_NAME=MyApp
# APP_DEBUG=true
# DATABASE_URL=postgresql://user:pass@localhost/db
# SECRET_KEY=super-secret-key-123

from dotenv import load_dotenv

# .env 파일 로드 (기존 환경변수는 덮어쓰지 않음)
load_dotenv()  # 기본: .env
load_dotenv(".env.local", override=True)  # override: 기존 값 덮어쓰기

# 이후 os.environ으로 접근
db_url = os.environ["DATABASE_URL"]
""")

# === 4. pydantic-settings ===
print("=== pydantic-settings ===")
# 실무에서 가장 권장: 타입 검증 + 자동 로드 + 문서화
print("""
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    app_name: str = "MyApp"
    debug: bool = False
    port: int = 8000
    database_url: str
    secret_key: str = Field(..., min_length=16)
    redis_url: str = "redis://localhost:6379"
    allowed_hosts: list[str] = ["localhost"]

    class Config:
        env_file = ".env"               # .env 파일 자동 로드
        env_file_encoding = "utf-8"
        env_prefix = ""                  # 환경변수 접두사
        case_sensitive = False           # 대소문자 구분 안 함

# 사용
settings = Settings()  # 환경변수에서 자동 로드 + 타입 검증
print(f"DB: {settings.database_url}")
print(f"Debug: {settings.debug}")

# 중첩 설정
class DatabaseSettings(BaseSettings):
    url: str = "sqlite:///app.db"
    pool_size: int = 5
    pool_recycle: int = 3600

    class Config:
        env_prefix = "DB_"  # DB_URL, DB_POOL_SIZE로 매핑
""")

# === 5. 환경별 설정 ===
print("\n=== 환경별 설정 ===")

# 모든 환경 공통의 베이스
class BaseConfig:
    APP_NAME = "MyApp"
    LOG_LEVEL = "INFO"

# 개발 환경: DEBUG ON, 로컬 SQLite
class DevelopmentConfig(BaseConfig):
    DEBUG = True
    DATABASE_URL = "sqlite:///dev.db"
    LOG_LEVEL = "DEBUG"

# 프로덕션: DEBUG OFF, 환경변수에서 DB URL 받음
class ProductionConfig(BaseConfig):
    DEBUG = False
    DATABASE_URL = os.environ.get("DATABASE_URL", "")
    LOG_LEVEL = "WARNING"

# 테스트: 인메모리 DB로 격리
class TestingConfig(BaseConfig):
    TESTING = True
    DATABASE_URL = "sqlite:///:memory:"

# APP_ENV 환경변수에 따라 설정 클래스 선택 (전략 패턴 + 매핑)
def get_config():
    env = os.environ.get("APP_ENV", "development")
    configs = {
        "development": DevelopmentConfig,
        "production": ProductionConfig,
        "testing": TestingConfig,
    }
    # 매핑에서 클래스를 찾아 인스턴스화
    return configs.get(env, DevelopmentConfig)()

# 각 환경별 설정 미리보기
for env in ["development", "production", "testing"]:
    os.environ["APP_ENV"] = env
    cfg = get_config()
    # getattr로 속성이 없을 때 기본값 사용 (TestingConfig는 DEBUG가 없음)
    print(f"  {env}: debug={getattr(cfg, 'DEBUG', False)}, log={cfg.LOG_LEVEL}")

print("\n=== 12-Factor App 설정 원칙 ===")
print("1. 설정은 환경변수로 관리 (코드에 하드코딩 X)")
print("2. .env 파일은 개발용. 프로덕션은 OS/컨테이너 환경변수")
print("3. 시크릿은 절대 코드/깃에 포함하지 않음")
print("4. 환경(dev/staging/prod)마다 설정이 다름")
print("5. .env.example 파일로 필요한 환경변수를 문서화")
```

**실행 결과** — 실행하지 않음 — 실행 환경 · 바깥 네트워크에 따라 달라지는 예제다.

**풀이 요점**

- 환경변수는 늘 문자열이라 `int()` 와 `.lower() == "true"` 로 바꾸고, 필수값은 `if not` 으로 시작 때 막는다.
- 중첩 설정 필드는 `field(default_factory=DatabaseConfig)` 로 인스턴스마다 새로 만든다.
- `from_env` 는 `@classmethod` 대안 생성자라서 `cls(...)` 로 자기 클래스를 만든다.
- dotenv · pydantic-settings 는 라이브러리 없이 돌도록 사용법을 여러 줄 문자열로 찍기만 한다.
- `get_config` 는 사전 매핑으로 클래스를 고르고 끝의 `()` 로 인스턴스를 만든다.
- `TestingConfig` 에 `DEBUG` 가 없으므로 `getattr` 의 기본값이 있어야 반복문이 끝까지 돈다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 실행 환경 · 바깥 네트워크에 따라 달라지는 예제다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
