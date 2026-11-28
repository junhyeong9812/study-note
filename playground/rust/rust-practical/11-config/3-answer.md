# rust/rust-practical/11 — 설정 관리 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. host 는 TOML, port · level 은 환경변수, 나머지는 TOML 값

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

- `host` = `0.0.0.0`(TOML), `port` = `9090`(환경변수), `workers` = `2`(TOML), `level` = `debug`(환경변수), `format` = `json`(TOML).
- 소스 목록은 `"defaults"`, `"toml_file"`, `"env_vars"` 차례다 — `build` 가 서버 · DB · 로그 줄보다 먼저 이 목록을 찍는다.

**왜 그런가**

- `new()` 가 기본값(포트 8080, level `info`, format `pretty`)을 깐다.
- `from_toml` 이 host · port(3000) · workers(2) · url · max_connections · level(`info`) · format(`json`)을 덮는다.
- `from_env` 는 맵에 있는 두 키만 덮는다 — 포트 9090, 레벨 `debug`.
- 맵에 없는 `APP_SERVER_HOST` 는 손대지 않으므로 host 는 TOML 값이 남는다.
- 근거: 2-summary 「동작 방식 (3) · (4) · (5)」.

### 2. port=8080, log=warn, db_pool=50, workers=8

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

- `port` = 8080, `log` = `warn`, `db_pool` = 50, `workers` = 8.

**왜 그런가**

- `production` 프로필은 level · format · workers · max_connections 만 바꾼다.
- 포트를 바꾸는 프로필은 없으므로 기본값 8080 이 남는다.
- 근거: 2-summary 「동작 방식 (6)」.

### 3. `info"  # trace, debug, info, warn, error` — 주석이 값에 섞인다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

- 대괄호 안에는 `info"  # trace, debug, info, warn, error` 가 찍힌다.

**왜 그런가**

- 줄이 `#` 로 시작하지 않으므로 주석으로 건너뛰지 않는다.
- `split_once('=')` 뒤 값은 `"info"  # trace, debug, info, warn, error` 이다.
- `trim_matches('"')` 는 양 끝에서만 벗긴다 — 앞 `"` 는 지워지지만 끝 글자가 `r` 이라 뒤쪽은 그대로다.
- 레벨이 빈 문자열은 아니고 검사 대상도 아니므로 `build` 는 통과한다.
- 근거: 2-summary 「어디서 틀리나 4」 · 「문법 — 형태와 규칙」.

### 4. 우선순위를 만드는 것은 「부른 순서」다

- `from_env` 를 `from_toml` 뒤에 불렀기 때문에 환경변수가 이긴다.
- 각 메서드가 `mut self` 로 빌더를 받아 필드를 덮어쓴 뒤 `self` 를 돌려주므로, 체인에서 뒤에 오는 메서드가 앞의 값을 덮는다.
- 순서를 바꿔 부르면 우선순위도 바뀐다 — 빌더도 언어도 순서를 강제하지 않는다.
- 근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 1」.

### 5. 잘못된 설정을 한 곳에서, 일찍, 호출자가 처리하게 하려고

- 설정을 다 쌓은 뒤 한 번에 검사하므로, 쓰는 곳마다 검사를 흩어 둘 필요가 없다.
- 서버가 일을 시작하기 전에 잘못된 값(포트 0, 빈 URL)을 막는다 — fail-fast 다.
- `Result` 로 돌려주면 패닉할지, 메시지를 찍고 끝낼지를 호출한 쪽이 정한다.
- 예제 `main` 은 `.unwrap()` 으로 받아 실패 시 패닉을 고른 것이다.
- 근거: 2-summary 「동작 방식 (7)」 · 「어디서 틀리나 7」.

### 6. 넣을 필드의 타입에서 추론한다

- `p` 를 `self.config.server.port` 에 넣으므로, 컴파일러는 `p` 가 `u16` 이어야 한다고 추론한다.
- 그래서 `parse` 의 목표 타입도 `u16` 이 되고, `parse::<u16>()` 을 적지 않아도 된다.
- 같은 꼴로 `workers` 는 `usize`, `max_connections` 는 `u32` 로 파싱된다.
- 이것은 언어가 보장하는 타입 추론이다.
- 근거: 2-summary 「문법 — 형태와 규칙」 · 「구현 세부사항 대 언어 보장」.

### 7. 조용히 이전 층의 포트가 남고, `build` 는 잡지 못한다

- `"abc"` 는 숫자가 아니고 `"70000"` 은 `u16` 범위(0~65535)를 넘으므로 `parse` 가 `Err` 다.
- `if let Ok` 가 실패를 버려서 포트는 아래 층 값(TOML 이 있으면 그 값, 없으면 8080)이 그대로다.
- `build` 는 포트가 0 인지만 보므로 이 경우를 통과시킨다.
- 근거: 2-summary 「어디서 틀리나 2」.

### 8. `database.url` 이 바뀐다

- 흉내 파서는 섹션 헤더 줄을 건너뛰기만 하고, 키 이름만 보고 필드를 고른다.
- 키 `url` 은 어느 섹션에 있든 `database.url` 로 간다.
- 근거: 2-summary 「어디서 틀리나 3」 · 「동작 방식 (3)」.

### 9. 예제는 키 이름을 하나하나 손으로 적어 두었기 때문이다

- 예제 `from_env` 는 `"APP_DATABASE_URL"` 이라는 완성된 이름을 찾으므로 밑줄 개수가 의미를 갖지 않는다.
- 팁의 `__` 는 이름을 잘라 `database.url` 같은 중첩 경로를 추론하는 방식(예: `config` 크레이트의 환경변수 소스)을 위한 것으로 읽힌다.
- 그 방식에서는 밑줄 하나가 이름의 일부인지 구분자인지 모호해지므로 구분자를 `__` 로 따로 둔다 (원본에 근거 없음 — 추론).
- 근거: 2-summary 「어디서 틀리나 5」 · 「동작 방식 (8)」.

### 10. `from_env` 뒤, `build` 바로 앞

- 원본 팁의 순서는 기본값 < 설정 파일 < 환경변수 < 커맨드라인이다.
- 이 빌더에서는 뒤에 부른 것이 이기므로, 커맨드라인을 반영하는 메서드는 `from_env` 다음, `build` 앞에 불러야 한다.
- 그래야 커맨드라인 값이 환경변수까지 덮고, 덮인 결과가 `build` 의 검사를 받는다.
- 근거: 2-summary 「동작 방식 (5)」 · 「동작 방식 (7)」.

## 실습 정답

### 실습 1. 계층 설정 빌더 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 섹션별 기본값 | `impl Default for ServerConfig` · `DatabaseConfig` · `LogConfig` |
| 2. 기본값 합성 | `impl Default for AppConfig` 안의 `ServerConfig::default()` 등 |
| 3. 기본값에서 시작 | `ConfigBuilder::new()` — `sources: vec!["defaults".to_string()]` |
| 4. 주석 · 빈 줄 · 섹션 건너뛰기 | `from_toml` 의 `line.starts_with('#') \|\| line.is_empty() \|\| line.starts_with('[')` |
| 5. 키/값 나누기 · 따옴표 벗기기 | `line.split_once('=')`, `value.trim().trim_matches('"')` |
| 6. 키를 필드에 매핑 | `from_toml` 의 `match key { "host" => … _ => {} }`, `if let Ok(p) = value.parse()` |
| 7. 환경변수로 덮기 | `from_env` 의 `if let Some(v) = env_vars.get("APP_…")` 네 개 |
| 8. 프로필 | `with_profile` 의 `match profile { "development" … "production" … "test" … _ => {} }` |
| 9. 검사 | `build` 의 `port == 0`, `url.is_empty()` 두 `return Err(…)` |
| 10. 소스 출력 · 반환 | `println!("  설정 소스: {:?}", self.sources); Ok(self.config)` |
| 11. 1절 | `AppConfig::default()` 와 `println!("  {:?}", default_config)` |
| 12. 2절 | `ConfigBuilder::new().from_toml(toml_content).from_env(&env_vars).build().unwrap()` |
| 13. 3절 | `for profile in &[…]` 안의 `ConfigBuilder::new().with_profile(profile).build().unwrap()` |
| 14. 4절 · 크레이트 안내 | `main` 끝의 `println!(r#"…"#)` 와 네 줄의 `println!` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`rust/rust-practical/reference/config.rs`

```rust
// [실전 Rust] 설정 관리
// 설명: config 크레이트 패턴, 환경변수, TOML 파일, 계층 설정, 타입 안전 설정
// 팁: 설정 우선순위: 기본값 < 설정 파일 < 환경변수 < 커맨드라인. config 크레이트는 이 계층을 자동으로 관리한다. 환경변수는 APP_ 접두사를 붙이고 __ 로 중첩을 표현한다(APP_DATABASE__URL). dotenv로 개발 환경의 .env 파일을 로드할 수 있다.

// === 설정 관리 패턴 ===
// Cargo.toml:
//   config = "0.14"
//   serde = { version = "1", features = ["derive"] }
//   toml = "0.8"
//   dotenv = "0.15"

// 환경변수 시뮬레이션용
use std::collections::HashMap;

// ===== 1. 타입 안전 설정 구조체 =====

// 애플리케이션 전체 설정 - 도메인별 그룹으로 분리
#[derive(Debug, Clone)]
struct AppConfig {
    server: ServerConfig,
    database: DatabaseConfig,
    logging: LogConfig,
}

// 서버 설정 - host/port/worker 수
#[derive(Debug, Clone)]
struct ServerConfig {
    host: String,
    port: u16,
    workers: usize,
}

// DB 연결 설정 - URL, 풀 크기, 타임아웃
#[derive(Debug, Clone)]
struct DatabaseConfig {
    url: String,
    max_connections: u32,
    timeout_secs: u64,
}

// 로깅 설정 - 레벨과 포맷
#[derive(Debug, Clone)]
struct LogConfig {
    level: String,
    format: String,
}

// ===== 2. 기본값 =====

// 서버 기본값 - 로컬 개발 환경 기준
impl Default for ServerConfig {
    fn default() -> Self {
        ServerConfig {
            host: "127.0.0.1".to_string(),
            port: 8080,
            workers: 4,
        }
    }
}

// DB 기본값 - 로컬 PostgreSQL 가정
impl Default for DatabaseConfig {
    fn default() -> Self {
        DatabaseConfig {
            url: "postgres://localhost/mydb".to_string(),
            max_connections: 10,
            timeout_secs: 30,
        }
    }
}

// 로그 기본값 - info + pretty 형식
impl Default for LogConfig {
    fn default() -> Self {
        LogConfig {
            level: "info".to_string(),
            format: "pretty".to_string(),
        }
    }
}

// AppConfig는 각 섹션의 Default를 합성
impl Default for AppConfig {
    fn default() -> Self {
        AppConfig {
            server: ServerConfig::default(),
            database: DatabaseConfig::default(),
            logging: LogConfig::default(),
        }
    }
}

// ===== 3. 계층 설정 빌더 =====

// 계층적 설정 빌더 - 여러 소스를 순차 병합
struct ConfigBuilder {
    config: AppConfig,
    // 디버그용 - 어떤 소스가 적용되었는지 추적
    sources: Vec<String>,
}

impl ConfigBuilder {
    // 기본값에서 시작
    fn new() -> Self {
        ConfigBuilder {
            config: AppConfig::default(),
            sources: vec!["defaults".to_string()],
        }
    }

    // TOML 파일에서 로드 (시뮬레이션) - 실제는 toml 크레이트로 파싱
    fn from_toml(mut self, toml_content: &str) -> Self {
        self.sources.push("toml_file".to_string());

        // 간단한 TOML 파서 시뮬레이션 - line 단위 key=value 처리
        for line in toml_content.lines() {
            let line = line.trim();
            // 주석/빈줄/섹션 헤더는 스킵
            if line.starts_with('#') || line.is_empty() || line.starts_with('[') {
                continue;
            }
            // key = value 분리
            if let Some((key, value)) = line.split_once('=') {
                let key = key.trim();
                // 양 끝 따옴표 제거
                let value = value.trim().trim_matches('"');
                // 키 이름으로 적절한 필드에 매핑
                match key {
                    "host" => self.config.server.host = value.to_string(),
                    "port" => if let Ok(p) = value.parse() { self.config.server.port = p; },
                    "workers" => if let Ok(w) = value.parse() { self.config.server.workers = w; },
                    "url" => self.config.database.url = value.to_string(),
                    "max_connections" => if let Ok(m) = value.parse() { self.config.database.max_connections = m; },
                    "level" => self.config.logging.level = value.to_string(),
                    "format" => self.config.logging.format = value.to_string(),
                    _ => {}
                }
            }
        }
        self
    }

    // 환경변수에서 로드 - APP_ 접두사 패턴 (실제로는 std::env::var 사용)
    fn from_env(mut self, env_vars: &HashMap<String, String>) -> Self {
        self.sources.push("env_vars".to_string());

        // 각 환경변수가 있을 때만 덮어쓰기 (없으면 이전 값 유지)
        if let Some(v) = env_vars.get("APP_SERVER_HOST") {
            self.config.server.host = v.clone();
        }
        if let Some(v) = env_vars.get("APP_SERVER_PORT") {
            if let Ok(p) = v.parse() { self.config.server.port = p; }
        }
        if let Some(v) = env_vars.get("APP_DATABASE_URL") {
            self.config.database.url = v.clone();
        }
        if let Some(v) = env_vars.get("APP_LOG_LEVEL") {
            self.config.logging.level = v.clone();
        }
        self
    }

    // 프로필별 설정 (development/production/test) - 환경별 디폴트 적용
    fn with_profile(mut self, profile: &str) -> Self {
        self.sources.push(format!("profile:{}", profile));

        match profile {
            // 개발: 디버그 레벨, 별도 DB
            "development" => {
                self.config.logging.level = "debug".to_string();
                self.config.database.url = "postgres://localhost/mydb_dev".to_string();
            }
            // 운영: warn 이상, JSON 로그, 워커 증가, 풀 확장
            "production" => {
                self.config.logging.level = "warn".to_string();
                self.config.logging.format = "json".to_string();
                self.config.server.workers = 8;
                self.config.database.max_connections = 50;
            }
            // 테스트: error 레벨, 별도 DB
            "test" => {
                self.config.database.url = "postgres://localhost/mydb_test".to_string();
                self.config.logging.level = "error".to_string();
            }
            _ => {}
        }
        self
    }

    // 최종 설정 유효성 검사 및 빌드 - fail-fast 원칙
    fn build(self) -> Result<AppConfig, String> {
        // 포트 검증
        if self.config.server.port == 0 {
            return Err("포트는 0이 될 수 없습니다".to_string());
        }
        // DB URL 필수
        if self.config.database.url.is_empty() {
            return Err("데이터베이스 URL이 필요합니다".to_string());
        }

        // 적용된 소스 디버그 출력
        println!("  설정 소스: {:?}", self.sources);
        Ok(self.config)
    }
}

fn main() {
    println!("=== 1. 기본 설정 ===");
    // Default::default() 호출
    let default_config = AppConfig::default();
    println!("  {:?}", default_config);

    println!("\n=== 2. TOML + 환경변수 계층 설정 ===");
    // TOML 원본 (실제로는 config.toml 파일에서 읽음)
    let toml_content = r#"
[server]
host = "0.0.0.0"
port = 3000
workers = 2

[database]
url = "postgres://db.example.com/prod"
max_connections = 20

[logging]
level = "info"
format = "json"
"#;

    // 환경변수 (실제로는 std::env::var()로 읽음)
    let env_vars = HashMap::from([
        ("APP_SERVER_PORT".to_string(), "9090".to_string()),
        ("APP_LOG_LEVEL".to_string(), "debug".to_string()),
    ]);

    // 계층: 기본값 < TOML < 환경변수 (나중이 우선)
    let config = ConfigBuilder::new()
        .from_toml(toml_content)
        .from_env(&env_vars)
        .build()
        .unwrap();

    // 환경변수가 TOML을 덮어쓴 결과 확인
    println!("  서버: {}:{} (workers: {})", config.server.host, config.server.port, config.server.workers);
    println!("  DB: {}", config.database.url);
    println!("  로그: {} ({})", config.logging.level, config.logging.format);
    println!("  -> port=9090 (환경변수가 TOML의 3000을 덮어씀)");
    println!("  -> level=debug (환경변수가 TOML의 info를 덮어씀)");

    println!("\n=== 3. 프로필별 설정 ===");
    // 프로필별 비교
    for profile in &["development", "production", "test"] {
        let config = ConfigBuilder::new()
            .with_profile(profile)
            .build()
            .unwrap();
        println!("  [{}] port={}, log={}, db_pool={}",
            profile, config.server.port, config.logging.level, config.database.max_connections);
    }

    // 실전 TOML 형식 가이드
    println!("\n=== 4. 실전 TOML 형식 ===");
    println!(r#"
# config.toml
[server]
host = "0.0.0.0"
port = 8080
workers = 4

[database]
url = "postgres://user:pass@host/db"
max_connections = 20
timeout_secs = 30

[logging]
level = "info"  # trace, debug, info, warn, error
format = "json"  # json, pretty
"#);

    // config 크레이트 실제 사용 패턴
    println!("=== config 크레이트 사용 시 ===");
    println!("1. Config::builder()로 계층 소스 추가");
    println!("2. .add_source(File::with_name(\"config\")) -> TOML/YAML/JSON");
    println!("3. .add_source(Environment::with_prefix(\"APP\")) -> 환경변수");
    println!("4. .build()?.try_deserialize::<AppConfig>()? -> 타입 안전");
}
```

**실행 결과** — 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다).

**풀이 요점**

- 빌더 메서드는 모두 `mut self` 를 받아 `self` 를 돌려준다 — 그래서 체인이 되고, 뒤가 앞을 덮는다.
- 「없으면 건드리지 않는다」가 계층 설정의 핵심이다 — `if let Some` 과 `if let Ok` 가 그 일을 한다.
- 숫자 필드의 `parse` 목표 타입은 넣을 필드에서 추론된다.
- 검사는 `build` 한 곳에 모으고 `Result` 로 돌려준다.
- 흉내 TOML 파서는 섹션 · 줄 끝 주석 · 파싱 실패를 다루지 못한다 — 실전에서는 `toml`/`config` 크레이트를 쓴다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다) |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
