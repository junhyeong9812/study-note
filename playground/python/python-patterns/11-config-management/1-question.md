# python/python-patterns/11 — 설정 관리 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 네 가지 `APP_DEBUG` 값의 불린 변환 (예측)

```python
# 질문용 발췌
import os
for raw in ["true", "TRUE", "1", "yes"]:
    os.environ["APP_DEBUG"] = raw
    debug = os.environ.get("APP_DEBUG", "false").lower() == "true"
    print(raw, debug)
```

- 네 줄은 각각 어떻게 찍히나?

### 2. 환경변수를 읽은 뒤 거치는 변환 (왜)

- `from_env` 가 포트를 `int(...)` 로, 디버그를 `.lower() == "true"` 로 감싸는 까닭은 무엇인가?
- 디버그를 `bool(...)` 로 감싸면 안 되는 까닭은 무엇인가?

### 3. 세 환경을 차례로 고르는 반복문 (예측)

```python
# 질문용 발췌
class BaseConfig:
    APP_NAME = "MyApp"; LOG_LEVEL = "INFO"
class DevelopmentConfig(BaseConfig):
    DEBUG = True; LOG_LEVEL = "DEBUG"
class ProductionConfig(BaseConfig):
    DEBUG = False; LOG_LEVEL = "WARNING"
class TestingConfig(BaseConfig):
    TESTING = True

for env in ["development", "production", "testing"]:
    os.environ["APP_ENV"] = env
    cfg = get_config()   # 원본과 같은 매핑 함수
    print(f"  {env}: debug={getattr(cfg, 'DEBUG', False)}, log={cfg.LOG_LEVEL}")
```

- 세 줄은 각각 무엇인가?

### 4. 클래스 정의 뒤에 바꾼 환경변수 (예측)

```python
# 질문용 발췌
import os
os.environ["DATABASE_URL"] = "postgresql://old"

class ProductionConfig:
    DATABASE_URL = os.environ.get("DATABASE_URL", "")

os.environ["DATABASE_URL"] = "postgresql://new"
print(ProductionConfig().DATABASE_URL)
```

- 무엇이 찍히나?

### 5. 중첩 설정 필드에 `default_factory` 를 쓰는 까닭 (왜)

- `database` 필드의 기본값을 `DatabaseConfig()` 가 아니라 `field(default_factory=DatabaseConfig)` 로 주는 까닭은 무엇인가?

### 6. 비어 있거나 빠진 `DATABASE_URL` (경계)

- `DATABASE_URL` 이 빈 문자열 `""` 로 설정돼 있으면 섹션 1의 필수값 검사를 통과하나?
- `DATABASE_URL` 이 아예 없을 때 `AppConfig.from_env()` 의 `database.url` 은 어떻게 되나?

### 7. `load_dotenv` 와 이미 있는 환경변수 (경계)

- 셸에 `DATABASE_URL` 이 이미 있을 때 `load_dotenv()` 는 `.env` 의 값으로 바꾸나?
- `load_dotenv(".env.local", override=True)` 면 어떻게 다른가?

### 8. `dataclass` 설정과 `pydantic-settings` 의 타입 (연결)

- `AppConfig(port="80")` 으로 직접 만들면 `port` 에는 무엇이 들어가나?
- `pydantic-settings` 의 `Settings` 에서 포트 값이 `"abc"` 면 언제 무엇이 일어나나?

### 9. `get_config` 의 매핑과 전략 패턴 (연결)

- `staging` 환경을 더하려면 어디를 고치면 되나?
- `APP_ENV` 에 오타가 난 값이 들어오면 어떤 설정이 고르나?

### 10. 12-Factor 원칙과 저장소에 넣을 파일 (연결)

- `.env` 와 `.env.example` 중 어느 것을 커밋하고, 각각에는 무엇이 들어가나?
- 프로덕션의 비밀 키는 어디서 받아야 하나?

## 실습

### 실습 1. 다섯 가지 설정 관리 방식을 한 파일에 늘어놓기

**만들 것** — 환경변수 직접 읽기, `dataclass` 설정 객체, `python-dotenv` 사용 예, `pydantic-settings` 사용 예, 환경별 설정 클래스, 12-Factor 원칙을 차례로 보여 주는 스크립트 하나.

**준비물** — Python 3 만 있으면 된다. `python-dotenv` · `pydantic-settings` 는 설치하지 않고, 사용법을 문자열로 출력해서 보여 주기만 한다.

**요구 조건**

1단계 — `os.environ`
1. `=== os.environ ===` 제목을 찍은 뒤, 시연용으로 `APP_NAME="MyApp"` · `APP_DEBUG="true"` · `APP_PORT="8080"` · `DATABASE_URL="postgresql://user:pass@localhost/db"` 를 환경변수에 넣는다.
2. `APP_NAME` 은 `.get` 으로 읽되 없으면 `"DefaultApp"` 을 쓴다.
3. `APP_DEBUG` 는 없으면 `"false"` 로 읽고, 소문자로 바꿔 `"true"` 와 같은지로 불린을 만든다.
4. `APP_PORT` 는 없으면 `"8000"` 으로 읽고 정수로 바꾼다.
5. `DATABASE_URL` 은 기본값 없이 읽고, 비어 있으면 `ValueError("DATABASE_URL is required")` 를 던진다.
6. 네 값을 `APP_NAME: …` · `DEBUG: …` · `PORT: …` · `DB: …` 네 줄로 찍는다.

2단계 — `dataclass` 설정
7. `=== dataclass 설정 ===` 제목을 찍는다.
8. `DatabaseConfig`(`url`, `pool_size`, `echo`)와 `AppConfig`(`name`, `debug`, `port`, `secret_key`, `database`)를 `dataclass` 로 만든다 — 기본값은 시작 코드에 있다.
9. `AppConfig.database` 는 인스턴스마다 새 `DatabaseConfig` 가 생기게 한다.
10. 클래스 메서드 `from_env` 가 `APP_NAME`(기본 `"MyApp"`) · `APP_DEBUG`(불린) · `APP_PORT`(정수, 기본 `"8000"`) · `SECRET_KEY`(기본 `"change-me"`) · `DATABASE_URL`(기본 `"sqlite:///app.db"`) · `DB_POOL_SIZE`(정수, 기본 `"5"`)로 `AppConfig` 를 만들어 돌려준다.
11. `from_env()` 로 만든 객체를 `Config: …` 로 찍는다.

3단계 — `python-dotenv` 사용 예
12. `=== python-dotenv ===` 제목을 찍고, `.env` 파일 예(`APP_NAME` · `APP_DEBUG` · `DATABASE_URL` · `SECRET_KEY`)와 `load_dotenv()`(덮어쓰지 않음) · `load_dotenv(".env.local", override=True)`(덮어씀) · 이후 `os.environ["DATABASE_URL"]` 로 읽는 코드를 여러 줄 문자열로 찍는다.

4단계 — `pydantic-settings` 사용 예
13. `=== pydantic-settings ===` 제목을 찍고, `BaseSettings` 를 상속한 `Settings`(기본값 있는 필드, 필수 `database_url`, `Field(..., min_length=16)` 인 `secret_key`, `redis_url`, `allowed_hosts`, `Config` 의 `env_file` · `env_file_encoding` · `env_prefix` · `case_sensitive`)와 사용 예, `env_prefix = "DB_"` 인 `DatabaseSettings` 를 여러 줄 문자열로 찍는다.

5단계 — 환경별 설정
14. `=== 환경별 설정 ===` 제목을 찍는다.
15. `BaseConfig` 를 상속한 `DevelopmentConfig`(`DEBUG=True`, `DATABASE_URL="sqlite:///dev.db"`, `LOG_LEVEL="DEBUG"`) · `ProductionConfig`(`DEBUG=False`, `DATABASE_URL` 은 환경변수에서 · 없으면 `""`, `LOG_LEVEL="WARNING"`) · `TestingConfig`(`TESTING=True`, `DATABASE_URL="sqlite:///:memory:"`)를 만든다.
16. `get_config()` 는 `APP_ENV`(기본 `"development"`)로 세 클래스를 담은 사전에서 클래스를 골라(없으면 `DevelopmentConfig`) 인스턴스를 돌려준다.
17. 세 환경 이름을 돌며 `APP_ENV` 를 바꾸고, `DEBUG` 가 없는 클래스도 깨지지 않게 `  {env}: debug=…, log=…` 줄을 찍는다.

6단계 — 12-Factor 원칙
18. `=== 12-Factor App 설정 원칙 ===` 제목 아래 다섯 원칙(설정은 환경변수로 · `.env` 는 개발용 · 시크릿은 코드/깃에 넣지 않음 · 환경마다 설정이 다름 · `.env.example` 로 문서화)을 번호 붙여 찍는다.

**시작 코드**

```python
import os
from dataclasses import dataclass, field

# === 1. os.environ 기본 ===
print("=== os.environ ===")
os.environ["APP_NAME"] = "MyApp"
os.environ["APP_DEBUG"] = "true"
os.environ["APP_PORT"] = "8080"
os.environ["DATABASE_URL"] = "postgresql://user:pass@localhost/db"

app_name = None  # TODO: APP_NAME (없으면 "DefaultApp")
debug = None     # TODO: APP_DEBUG 를 불린으로 (없으면 "false")
port = None      # TODO: APP_PORT 를 정수로 (없으면 "8000")
db_url = None    # TODO: DATABASE_URL (기본값 없음)
# TODO: db_url 이 비어 있으면 즉시 실패

print(f"APP_NAME: {app_name}")
print(f"DEBUG: {debug}")
print(f"PORT: {port}")
print(f"DB: {db_url}")

# === 2. dataclass 기반 설정 ===
print("\n=== dataclass 설정 ===")

@dataclass
class DatabaseConfig:
    url: str = "sqlite:///app.db"
    pool_size: int = 5
    echo: bool = False

@dataclass
class AppConfig:
    name: str = "MyApp"
    debug: bool = False
    port: int = 8000
    secret_key: str = "change-me-in-production"
    database: DatabaseConfig = None  # TODO: 인스턴스마다 새 DatabaseConfig

    # TODO: 환경변수에서 AppConfig 를 만드는 대안 생성자 from_env

config = None  # TODO: from_env 로 만든다
print(f"Config: {config}")

# === 3. python-dotenv ===
print("\n=== python-dotenv ===")
print("""
# TODO: .env 파일 예와 load_dotenv 사용 예
""")

# === 4. pydantic-settings ===
print("=== pydantic-settings ===")
print("""
# TODO: Settings(BaseSettings) 예와 DatabaseSettings(env_prefix="DB_") 예
""")

# === 5. 환경별 설정 ===
print("\n=== 환경별 설정 ===")

class BaseConfig:
    APP_NAME = "MyApp"
    LOG_LEVEL = "INFO"

# TODO: DevelopmentConfig / ProductionConfig / TestingConfig

def get_config():
    # TODO: APP_ENV 로 매핑에서 클래스를 골라 인스턴스를 돌려준다
    pass

for env in ["development", "production", "testing"]:
    os.environ["APP_ENV"] = env
    cfg = get_config()
    # TODO: DEBUG 가 없어도 깨지지 않게 debug 와 LOG_LEVEL 을 한 줄로 찍는다

print("\n=== 12-Factor App 설정 원칙 ===")
# TODO: 원칙 다섯 줄
```

**확인 방법** — `python config-management.py` 로 돌려서 여섯 제목이 차례로 나오는지, `PORT` 가 따옴표 없는 정수로, `Config:` 줄에 `database=DatabaseConfig(...)` 가 들어 있는지, 환경별 세 줄 중 testing 줄이 오류 없이 찍히는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
