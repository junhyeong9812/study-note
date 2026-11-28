# rust/rust-practical/11 — 설정 관리 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. TOML 위에 환경변수 두 개를 얹으면 (예측)

```rust
// 질문용 발췌
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
let env_vars = HashMap::from([
    ("APP_SERVER_PORT".to_string(), "9090".to_string()),
    ("APP_LOG_LEVEL".to_string(), "debug".to_string()),
]);
let config = ConfigBuilder::new().from_toml(toml_content).from_env(&env_vars).build().unwrap();
```

- 최종 `host` · `port` · `workers` · `level` · `format` 은 각각 무엇인가?
- `build` 가 찍는 설정 소스 목록에는 무엇이 어떤 차례로 들어 있는가?

### 2. 기본값 위에 `production` 프로필만 얹으면 (예측)

```rust
// 질문용 발췌
let config = ConfigBuilder::new().with_profile("production").build().unwrap();
println!("port={}, log={}, db_pool={}, workers={}",
    config.server.port, config.logging.level,
    config.database.max_connections, config.server.workers);
```

- 네 값은 각각 무엇인가?

### 3. 줄 끝 주석이 붙은 TOML 줄을 흉내 파서에 넣으면 (예측)

```rust
// 질문용 발췌
let t = "level = \"info\"  # trace, debug, info, warn, error";
let config = ConfigBuilder::new().from_toml(t).build().unwrap();
println!("[{}]", config.logging.level);
```

- 대괄호 안에 찍히는 `level` 값은 무엇인가?

### 4. 이 빌더에서 우선순위를 정하는 것 (왜)

- 이 빌더에서 「환경변수가 TOML 을 이긴다」는 결과를 만드는 것은 무엇이며, 그것이 가능한 까닭은 무엇인가?

### 5. `build` 가 패닉 대신 `Result` 를 돌려주는 까닭 (왜)

- 검사를 `build` 한 곳에 모으고 `Result` 로 실패를 알리면 무엇이 좋은가?

### 6. `parse()` 에 타입을 안 적어도 되는 까닭 (왜)

- `if let Ok(p) = value.parse() { self.config.server.port = p; }` 에서 `parse` 는 무엇으로 바꿀지 어떻게 아는가?

### 7. 포트 값이 숫자가 아니거나 너무 클 때 (경계)

- `APP_SERVER_PORT` 가 `"abc"` 나 `"70000"` 이면 최종 포트는 어떻게 되며, `build` 의 검사는 이것을 잡는가?

### 8. 섹션을 넘나드는 키 (경계)

- 흉내 TOML 에서 `[logging]` 섹션 아래에 `url = "x"` 를 쓰면 어느 필드가 바뀌는가?

### 9. 팁의 `APP_DATABASE__URL` 과 코드의 `APP_DATABASE_URL` (연결)

- 팁은 밑줄 두 개로 중첩을 표현한다고 하는데, 예제 코드는 밑줄 하나로도 동작하는 까닭은 무엇인가?

### 10. 커맨드라인 층을 더할 자리 (연결)

- 원본 팁의 우선순위를 지키며 커맨드라인 값을 반영하는 메서드를 이 빌더에 더한다면, 체인의 어디에서 불러야 하는가?

## 실습

### 실습 1. 계층 설정 빌더 만들기

**만들 것** — 기본값 · TOML(흉내) · 환경변수(흉내) · 프로필을 차례로 쌓고, 마지막에 검사해서 타입 있는 설정 구조체를 내주는 `ConfigBuilder` 를 만든다.

**준비물** — 표준 라이브러리만 쓴다. `config` · `toml` · `dotenv` 크레이트는 쓰지 않고 흉내만 낸다(TOML 은 줄 단위로 직접 읽고, 환경변수는 `HashMap` 으로 넘긴다).

**요구 조건**

1단계 — 기본값
1. `ServerConfig` · `DatabaseConfig` · `LogConfig` 마다 `Default` 를 구현한다 — 서버는 host `127.0.0.1` · port 8080 · workers 4, DB 는 url `postgres://localhost/mydb` · max_connections 10 · timeout_secs 30, 로그는 level `info` · format `pretty`.
2. `AppConfig` 의 `Default` 는 세 섹션의 `default()` 를 모아 만든다.

2단계 — 빌더와 소스
3. `ConfigBuilder::new()` 는 기본값 설정과 `sources = ["defaults"]` 로 시작한다.
4. `from_toml(mut self, &str) -> Self` 는 `sources` 에 `"toml_file"` 을 넣고, 한 줄씩 공백을 지운 뒤 `#` 주석 · 빈 줄 · `[` 섹션 헤더를 건너뛴다.
5. 나머지 줄은 첫 `=` 로 키와 값을 나누고, 값의 공백과 양 끝 `"` 를 벗긴다.
6. 키 `host` · `port` · `workers` · `url` · `max_connections` · `level` · `format` 을 해당 필드에 넣는다 — 숫자 키는 `parse` 가 성공할 때만 넣고, 모르는 키는 무시한다.
7. `from_env(mut self, &HashMap<String, String>) -> Self` 는 `sources` 에 `"env_vars"` 를 넣고, `APP_SERVER_HOST` · `APP_SERVER_PORT` · `APP_DATABASE_URL` · `APP_LOG_LEVEL` 이 있을 때만 덮는다(포트는 `parse` 성공 시에만).
8. `with_profile(mut self, &str) -> Self` 는 `sources` 에 `"profile:<이름>"` 을 넣고 — `development` 는 level `debug` · url `postgres://localhost/mydb_dev`, `production` 은 level `warn` · format `json` · workers 8 · max_connections 50, `test` 는 url `postgres://localhost/mydb_test` · level `error` 로 바꾸며, 그 밖의 이름은 아무것도 바꾸지 않는다.

3단계 — 검사
9. `build(self) -> Result<AppConfig, String>` 는 포트가 0 이면 `"포트는 0이 될 수 없습니다"`, DB URL 이 비었으면 `"데이터베이스 URL이 필요합니다"` 를 `Err` 로 돌려준다.
10. 통과하면 `"  설정 소스: {:?}"` 꼴로 소스 목록을 찍고 `Ok` 로 설정을 돌려준다.

4단계 — `main`
11. 1절: 기본 설정을 `{:?}` 로 찍는다.
12. 2절: 기본값 → TOML → 환경변수(포트 9090, 로그 레벨 debug) 순으로 쌓아 서버 · DB · 로그 값을 찍는다.
13. 3절: `development` · `production` · `test` 마다 기본값 위에 프로필만 얹어 포트 · 로그 레벨 · 커넥션 수를 찍는다.
14. 4절과 마지막 절은 실전 TOML 형식과 `config` 크레이트 사용 단계를 글로 찍는다(시작 코드에 채워져 있다).

**시작 코드**

```rust
use std::collections::HashMap;

#[derive(Debug, Clone)]
struct AppConfig {
    server: ServerConfig,
    database: DatabaseConfig,
    logging: LogConfig,
}

#[derive(Debug, Clone)]
struct ServerConfig {
    host: String,
    port: u16,
    workers: usize,
}

#[derive(Debug, Clone)]
struct DatabaseConfig {
    url: String,
    max_connections: u32,
    timeout_secs: u64,
}

#[derive(Debug, Clone)]
struct LogConfig {
    level: String,
    format: String,
}

// TODO: ServerConfig / DatabaseConfig / LogConfig 의 Default 구현
// TODO: AppConfig 의 Default — 세 섹션의 default() 를 모은다

struct ConfigBuilder {
    config: AppConfig,
    sources: Vec<String>,
}

impl ConfigBuilder {
    fn new() -> Self {
        // TODO: 기본값 + sources = ["defaults"]
        todo!()
    }

    fn from_toml(mut self, toml_content: &str) -> Self {
        // TODO: "toml_file" 기록, 줄 단위로 key = value 를 읽어 필드에 넣기
        self
    }

    fn from_env(mut self, env_vars: &HashMap<String, String>) -> Self {
        // TODO: "env_vars" 기록, APP_ 키가 있을 때만 덮기
        self
    }

    fn with_profile(mut self, profile: &str) -> Self {
        // TODO: "profile:<이름>" 기록, 프로필별 값 바꾸기
        self
    }

    fn build(self) -> Result<AppConfig, String> {
        // TODO: 포트 0 · 빈 URL 검사, 소스 목록 출력, Ok 반환
        todo!()
    }
}

fn main() {
    println!("=== 1. 기본 설정 ===");
    // TODO: 기본 설정을 {:?} 로 찍기

    println!("\n=== 2. TOML + 환경변수 계층 설정 ===");
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
    let env_vars = HashMap::from([
        ("APP_SERVER_PORT".to_string(), "9090".to_string()),
        ("APP_LOG_LEVEL".to_string(), "debug".to_string()),
    ]);

    // TODO: 기본값 < TOML < 환경변수 순서로 쌓아 config 만들기
    // TODO: 서버 · DB · 로그 값 찍기

    println!("\n=== 3. 프로필별 설정 ===");
    for profile in &["development", "production", "test"] {
        // TODO: 프로필만 얹어 build 하고 port / log / db_pool 찍기
    }

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

    println!("=== config 크레이트 사용 시 ===");
    println!("1. Config::builder()로 계층 소스 추가");
    println!("2. .add_source(File::with_name(\"config\")) -> TOML/YAML/JSON");
    println!("3. .add_source(Environment::with_prefix(\"APP\")) -> 환경변수");
    println!("4. .build()?.try_deserialize::<AppConfig>()? -> 타입 안전");
}
```

**확인 방법** — `rustc config.rs && ./config` 로 돌려, 2절에서 포트가 TOML 의 3000 이 아니라 환경변수의 9090 인지, 로그 레벨이 `debug` 인지, 3절에서 프로필마다 로그 레벨과 커넥션 수가 달라지는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
