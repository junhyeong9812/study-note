# rust/rust-practical/11 — 설정 관리 — 정리 (힌트)

> 출처 — study-site 항목 `rust/config`(항목 데이터 `data/rust/practical.json`) · 정답 코드 study-practice `rust/rust-practical/reference/config.rs`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다).

## 한눈에 — 쉽게 말하면

**설정 관리는 「투명 필름을 겹쳐 놓는 일」이다.**
맨 아래에 기본 그림(기본값)을 깔고, 그 위에 설정 파일 필름을, 그 위에 환경변수 필름을 얹는다.
위에서 내려다보면 위 필름에 그려진 칸이 아래 칸을 가린다.
위 필름이 비워 둔 칸은 아래 그림이 그대로 비친다.
이 항목의 `ConfigBuilder` 도 똑같은 구조다.
`new()` 가 기본값을 깔고, `from_toml` · `from_env` · `with_profile` 이 차례로 필름을 얹는다.
마지막에 `build()` 가 완성된 그림을 검사한 뒤 내준다.

| 비유 | 실체 |
|---|---|
| 맨 아래 기본 그림 | `AppConfig::default()` 가 만든 기본값 |
| 위에 얹는 필름 한 장 | 설정 소스 하나(TOML 파일 · 환경변수 · 프로필) |
| 필름에 그려진 칸 | 그 소스가 실제로 값을 준 필드 |
| 필름의 빈 칸 | 그 소스에 없는 필드 — 아래 값이 유지된다 |
| 완성 그림 검사 | `build()` 의 유효성 검사 |
| 필름 목록 메모 | `sources: Vec<String>` |

```text
 위에서 본다 ↓
 ┌─────────────────────────────┐
 │ 환경변수   port=9090  level=debug │  ← 마지막에 얹음 = 가장 셈
 ├─────────────────────────────┤
 │ TOML      host  port=3000  level=info │
 ├─────────────────────────────┤
 │ 기본값     host  port=8080  level=info │  ← 맨 처음 깔림 = 가장 약함
 └─────────────────────────────┘
 결과: port=9090, level=debug, host=TOML 값
```

## 이 주제가 답하려는 질문

1. 설정 값이 여러 곳(기본값 · 파일 · 환경변수 · 커맨드라인)에 흩어져 있을 때, 어느 값이 이기는가?
2. 문자열로 들어온 설정을 어떻게 `u16` · `usize` 같은 **타입이 있는 값**으로 바꿔 담는가?
3. 잘못된 설정을 언제, 어디서 걸러 내는가?
4. 개발 · 운영 · 테스트처럼 환경마다 다른 설정을 어떻게 한 코드로 다루는가?

## 동작 방식

### (1) 타입 안전 설정 구조체

**언제 쓰나** — 설정을 문자열 맵으로 들고 다니지 않고, 컴파일러가 필드 이름과 타입을 검사하게 하고 싶을 때 쓴다.

```text
AppConfig
 ├─ server:   ServerConfig   { host: String, port: u16, workers: usize }
 ├─ database: DatabaseConfig { url: String, max_connections: u32, timeout_secs: u64 }
 └─ logging:  LogConfig      { level: String, format: String }

config.server.port  → u16   (오타면 컴파일 에러)
config.server.prot  → 컴파일 에러
```

- 설정 전체를 `AppConfig` 하나로 묶고, 안을 도메인별 구조체(서버 · DB · 로그)로 나눈다.
- 각 필드는 쓰임에 맞는 타입을 가진다 — 포트는 `u16`, 워커 수는 `usize`, 타임아웃은 `u64` 다.
- 코드는 `config.server.port` 처럼 점으로 따라 들어가 값을 꺼낸다.
- 필드 이름을 잘못 쓰면 실행 전에 컴파일러가 막는다.
- 네 구조체 모두 `#[derive(Debug, Clone)]` 을 단다 — `{:?}` 로 찍을 수 있고 복제할 수 있다.

> **타입 안전 설정** — 설정 값을 문자열이 아니라 정해진 타입의 필드로 담아, 이름과 타입 실수를 컴파일러가 잡게 하는 방식.\
> 예: `port: u16` 이면 `"abc"` 나 `70000` 은 그 필드에 들어갈 수 없다.

### (2) 기본값 — `Default` 를 섹션마다 두고 합성한다

**언제 쓰나** — 아무 설정 파일도 환경변수도 없을 때도 프로그램이 돌 수 있게, 출발점이 되는 값을 정할 때 쓴다.

```text
ServerConfig::default()   → host "127.0.0.1", port 8080, workers 4
DatabaseConfig::default() → url "postgres://localhost/mydb", max_connections 10, timeout_secs 30
LogConfig::default()      → level "info", format "pretty"
        │        │        │
        └────────┼────────┘
                 ▼
AppConfig::default() = { server: ServerConfig::default(), database: …, logging: … }
```

- 섹션 구조체마다 `impl Default` 를 직접 써서 기본값을 정한다.
- 기본값은 로컬 개발 환경을 기준으로 잡혀 있다(127.0.0.1, 로컬 PostgreSQL, 사람이 읽기 좋은 `pretty` 로그).
- `AppConfig` 의 `Default` 는 새 값을 정하지 않고, 세 섹션의 `default()` 를 불러 모은다.
- 그래서 섹션 기본값을 바꾸면 전체 기본값도 저절로 따라 바뀐다.

> **`Default` 트레이트** — 「이 타입의 기본값」을 돌려주는 `default()` 함수를 약속하는 표준 트레이트.\
> 예: `AppConfig::default()` 를 부르면 기본값으로 채운 설정 하나가 나온다.

### (3) 빌더가 소스를 차례로 얹는다 — `from_toml`

**언제 쓰나** — 설정 파일 내용으로 기본값의 일부를 덮을 때 쓴다.

```text
toml_content (여러 줄 문자열)
   │ .lines() 로 한 줄씩
   ▼
 trim() ─ '#' 로 시작? 빈 줄? '[' 로 시작? ── 예 ──▶ 건너뜀
   │ 아니오
   ▼
 split_once('=') → key / value
   │ key.trim(), value.trim().trim_matches('"')
   ▼
 match key
   "host" → server.host          "url"   → database.url
   "port" → server.port (parse)  "max_connections" → database.max_connections (parse)
   "workers" → server.workers (parse)
   "level" → logging.level       "format" → logging.format
   그 밖 → 무시
```

- `ConfigBuilder::new()` 는 `AppConfig::default()` 와 `sources = ["defaults"]` 로 시작한다.
- `from_toml` 은 먼저 `sources` 에 `"toml_file"` 을 넣는다.
- 문자열을 한 줄씩 보며 앞뒤 공백을 지운다.
- 주석(`#`) · 빈 줄 · 섹션 헤더(`[server]` 같은 줄)는 건너뛴다.
- 나머지 줄은 첫 `=` 에서 둘로 나눠 키와 값을 얻는다.
- 값은 공백을 지운 뒤 양 끝의 `"` 를 벗긴다.
- 키 이름에 따라 해당 필드에 넣는다.
- 숫자 필드는 `value.parse()` 가 성공(`Ok`)할 때만 넣는다 — 실패하면 아무 일도 하지 않고 이전 값이 남는다.
- 이 파서는 **진짜 TOML 파서가 아니다**. 원본 주석 그대로 「시뮬레이션」이며, 실제로는 `toml` 크레이트로 파싱한다.
- `timeout_secs` 키는 `match` 에 없어서 TOML 에 써도 무시된다.

> **빌더 패턴** — 객체를 한 번에 만들지 않고, 메서드를 이어 불러 조금씩 채운 뒤 마지막 `build()` 로 완성하는 방식.\
> 예: `ConfigBuilder::new().from_toml(t).from_env(&e).build()`.

### (4) 환경변수를 얹는다 — `from_env`

**언제 쓰나** — 배포 환경마다 다른 값(포트, DB 주소 등)을 파일을 고치지 않고 바깥에서 바꿔 끼울 때 쓴다.

```text
env_vars: HashMap<String, String>
   │
   ├─ "APP_SERVER_HOST"  있으면 → server.host
   ├─ "APP_SERVER_PORT"  있으면 → parse 성공 시 server.port
   ├─ "APP_DATABASE_URL" 있으면 → database.url
   └─ "APP_LOG_LEVEL"    있으면 → logging.level
   없는 키 → 손대지 않음 (아래 층 값 유지)
```

- `sources` 에 `"env_vars"` 를 넣는다.
- 정해 둔 네 키를 `HashMap::get` 으로 하나씩 찾는다.
- 있으면 그 값으로 덮고, 없으면 그 필드는 건드리지 않는다.
- 포트만 `parse` 를 거치며, 실패하면 역시 이전 값이 남는다.
- 예제는 진짜 환경변수 대신 `HashMap` 을 넘겨 흉내 낸다 — 실제로는 `std::env::var()` 로 읽는다.
- 키 이름은 `APP_` 접두사를 붙여 다른 프로그램의 환경변수와 섞이지 않게 한다.

> **환경변수** — 운영체제가 프로세스에 넘겨주는 「이름=값」 문자열 쌍.\
> 예: `APP_SERVER_PORT=9090` 으로 실행하면 프로그램이 이 값을 읽을 수 있다.

### (5) 우선순위는 「부른 순서」가 정한다

**언제 쓰나** — 같은 필드를 여러 소스가 줄 때 누가 이기는지 정할 때다.

```text
ConfigBuilder::new()        port = 8080 (기본값)
   .from_toml(toml)         port = 3000 (덮음)
   .from_env(&env)          port = 9090 (또 덮음)
   .build()                 → port 9090
```

- 각 메서드는 `mut self` 로 빌더를 통째로 받아, 필드를 고친 뒤 `self` 를 돌려준다.
- 그래서 점(`.`)으로 이어 부를 수 있고, 뒤에 부른 메서드가 앞의 값을 덮는다.
- 즉 이 빌더에서 「나중이 우선」이다.
- 원본 팁의 우선순위는 **기본값 < 설정 파일 < 환경변수 < 커맨드라인** 이다.
- 이 순서를 지키려면 부르는 순서도 `new` → `from_toml` → `from_env` → (커맨드라인을 읽는 단계) 여야 한다.
- 순서를 바꿔 부르면 우선순위도 바뀐다 — 언어나 빌더가 순서를 강제하지 않는다.

### (6) 프로필 — `with_profile`

**언제 쓰나** — 개발 · 운영 · 테스트 환경마다 미리 정해 둔 값 묶음을 한 번에 적용할 때다.

```text
with_profile("development") → level "debug",  url ".../mydb_dev"
with_profile("production")  → level "warn",   format "json", workers 8, max_connections 50
with_profile("test")        → url ".../mydb_test", level "error"
그 밖의 이름                 → 아무것도 안 바꿈 (sources 에는 기록됨)
```

- `sources` 에 `"profile:<이름>"` 을 넣는다.
- 프로필 이름에 따라 몇몇 필드만 바꾼다 — 나머지는 아래 층 값이 그대로다.
- 예를 들어 어느 프로필도 포트를 바꾸지 않으므로, 기본값 위에 프로필만 얹으면 포트는 8080 이다.
- 운영 프로필은 로그를 `warn` 이상 · JSON 형식으로 줄이고, 워커와 DB 커넥션 풀을 늘린다.
- 모르는 프로필 이름은 `_ => {}` 로 조용히 넘어간다.

> **프로필** — 실행 환경(개발 · 운영 · 테스트) 이름 하나에 묶인 설정 값 묶음.\
> 예: `production` 이면 워커 8, 커넥션 50.

### (7) 마지막 검사 — `build`

**언제 쓰나** — 설정을 다 쌓은 뒤, 프로그램이 일을 시작하기 **전에** 말이 안 되는 값을 막을 때다.

```text
build(self)
  port == 0 ?          ── 예 ──▶ Err("포트는 0이 될 수 없습니다")
  database.url 비었나? ── 예 ──▶ Err("데이터베이스 URL이 필요합니다")
  통과 → "  설정 소스: [..]" 를 찍음 → Ok(AppConfig)
```

- 두 가지를 검사한다 — 포트가 0 이 아닌지, DB URL 이 빈 문자열이 아닌지.
- 통과하면 적용된 소스 목록을 `{:?}` 로 찍고 `Ok(self.config)` 를 돌려준다.
- 실패하면 `Err(String)` 을 돌려준다 — 패닉하지 않고 호출한 쪽이 처리를 정한다.
- 예제 `main` 은 `.unwrap()` 으로 받으므로, 검사에 걸리면 그 자리에서 패닉한다.
- 원본 주석은 이것을 **fail-fast** 원칙이라 부른다.

> **fail-fast** — 잘못된 상태를 늦게 터뜨리지 않고, 가장 이른 시점에 바로 실패시키는 원칙.\
> 예: 포트가 0 이면 서버를 띄우다 이상해지기 전에 설정 단계에서 `Err` 를 낸다.

### (8) 실제 `config` 크레이트의 모양

**언제 쓰나** — 위의 손수 만든 빌더 대신, 실제 프로젝트에서 크레이트에 계층 관리를 맡길 때다.

```text
Config::builder()
  .add_source(File::with_name("config"))       → TOML/YAML/JSON 파일
  .add_source(Environment::with_prefix("APP")) → APP_ 로 시작하는 환경변수
  .build()?                                    → 병합된 설정
  .try_deserialize::<AppConfig>()?             → 타입 있는 구조체로
```

- 원본이 소개하는 네 단계다.
- `Config::builder()` 로 시작해 소스를 `add_source` 로 쌓는다.
- 파일 소스는 TOML · YAML · JSON 을 받는다.
- 환경변수 소스는 접두사 `APP` 으로 거른다.
- 마지막에 `try_deserialize` 로 구조체에 담아 타입 안전을 얻는다.
- 원본 팁은 「config 크레이트는 이 계층을 자동으로 관리한다」고 말한다.
- 원본 팁은 환경변수에 `APP_` 접두사를 붙이고 `__`(밑줄 두 개)로 중첩을 표현한다고 한다 — 예: `APP_DATABASE__URL` 은 `database.url` 을 뜻한다.
- 원본 팁은 `dotenv` 로 개발 환경의 `.env` 파일을 읽어 환경변수로 올릴 수 있다고 한다.
- 원본 주석의 의존성 예: `config = "0.14"`, `serde`(`derive` 기능), `toml = "0.8"`, `dotenv = "0.15"`.

## 문법 — 형태와 규칙

```rust
#[derive(Debug, Default)]
struct Cfg { port: u16 }

struct Builder { cfg: Cfg }

impl Builder {
    fn new() -> Self { Builder { cfg: Cfg::default() } }
    fn port(mut self, v: &str) -> Self {
        if let Ok(p) = v.parse() { self.cfg.port = p; }
        self
    }
    fn build(self) -> Result<Cfg, String> {
        if self.cfg.port == 0 { return Err("port 0".to_string()); }
        Ok(self.cfg)
    }
}
```

- 빌더 메서드는 `fn 이름(mut self, …) -> Self` 꼴이다 — 소유권을 받아 고치고 다시 넘긴다.
- 끝 메서드 `build(self)` 는 `Self` 대신 완성품을 `Result` 로 돌려준다.
- `v.parse()` 의 목표 타입은 결과를 넣는 필드(`self.cfg.port: u16`)에서 추론된다 — 직접 `parse::<u16>()` 이라 쓰지 않아도 된다.
- `if let Ok(p) = …` 는 성공일 때만 값을 넣고, 실패는 버린다.
- `if let Some(v) = map.get("KEY")` 는 키가 있을 때만 덮는다.
- `line.split_once('=')` 는 첫 `=` 에서 나눠 `Option<(&str, &str)>` 을 준다.
- `trim_matches('"')` 는 문자열 **양 끝**에서 `"` 가 아닌 글자를 만날 때까지만 벗긴다 — 가운데 `"` 는 건드리지 않는다.
- `#[derive(Default)]` 로 만든 숫자 필드의 기본값은 0 이다 — 위 예에서 `port` 를 안 주면 `build` 가 `Err` 를 낸다.
- `HashMap::from([(k, v), …])` 로 맵을 한 번에 만든다.
- `r#"…"#` 는 원시 문자열이다 — 안의 `"` 를 이스케이프하지 않아도 된다.

## 어디서 틀리나

### 1. 우선순위를 「소스의 종류」가 정한다고 믿는다

원본 팁의 순서 「기본값 < 설정 파일 < 환경변수 < 커맨드라인」은 이 빌더에서는 **부른 순서**로만 지켜진다.
`.from_env(&env).from_toml(t)` 처럼 바꿔 부르면 TOML 이 환경변수를 덮는다.
`with_profile` 도 마찬가지다 — 환경변수 뒤에 부르면 프로필이 환경변수 값을 덮는다.

### 2. 숫자 파싱 실패가 조용히 묻힌다

`port = abc` 나 `APP_SERVER_PORT=70000` 은 `parse` 가 `Err` 를 낸다(`u16` 의 범위는 0~65535).
이 코드는 `if let Ok` 로 실패를 버리므로 에러도 경고도 없이 이전 층의 값이 남는다.
`build` 의 fail-fast 검사는 포트가 0 인지만 보므로 이 경우를 잡지 못한다.
사용자는 9090 을 줬다고 믿지만 실제로는 다른 포트로 뜰 수 있다.

### 3. 흉내 낸 TOML 파서는 섹션을 보지 않는다

`[server]` · `[database]` 같은 헤더 줄은 건너뛰기만 한다.
키 이름만 보고 필드를 정하므로, `[logging]` 아래에 `url = …` 을 써도 `database.url` 이 바뀐다.
같은 키가 두 번 나오면 뒤의 줄이 이긴다.
`timeout_secs` 처럼 `match` 에 없는 키, 오타 난 키는 조용히 무시된다.

### 4. 줄 끝 주석이 값에 섞인다

원본 4절이 보여 주는 실전 TOML 에는 `level = "info"  # trace, debug, info, warn, error` 처럼 줄 끝 주석이 있다.
흉내 파서는 줄이 `#` 로 **시작**할 때만 주석으로 본다.
그래서 이 줄은 값 쪽에 주석까지 딸려 오고, `trim_matches('"')` 는 앞의 `"` 만 벗긴다(끝 글자가 `"` 가 아니라서).
원본 `main` 은 이 TOML 을 찍기만 하고 파싱하지는 않는다 — 넣으면 깨진다는 뜻이다.

### 5. 팁의 `__` 와 코드의 `_` 가 다르다

원본의 주장 → 「환경변수는 `__` 로 중첩을 표현한다(`APP_DATABASE__URL`)」.
왜 헷갈리나 → 예제의 `from_env` 는 `APP_DATABASE_URL`(밑줄 하나)을 찾는다.
예제는 키를 하나하나 손으로 적어 두어서 밑줄 하나로도 동작한다.
`config` 크레이트처럼 이름을 잘라 중첩을 추론하는 방식에서는 `DATABASE_URL` 의 밑줄이 「구분자」인지 「이름의 일부」인지 모호해진다 — 그래서 구분자를 `__` 로 따로 둔다는 것이 팁의 뜻으로 읽힌다(원본에 근거 없음 — 추론).

### 6. 모르는 프로필 이름도 성공처럼 보인다

`with_profile("prod")` 처럼 철자를 틀려도 `_ => {}` 라서 에러가 없다.
`sources` 에는 `"profile:prod"` 가 찍히니 적용된 것처럼 보이지만 아무 값도 바뀌지 않는다.

### 7. `build` 의 `unwrap` 은 실패를 패닉으로 바꾼다

`build` 는 `Result` 로 정중히 실패를 알리지만, 예제 `main` 은 `.unwrap()` 으로 받는다.
실제 프로그램에서는 `?` 로 넘기거나 에러 메시지를 찍고 종료하는 편이 읽기 좋다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| 뒤에 부른 소스가 앞의 값을 덮는다 | 이 예제 빌더의 코드(호출 순서) — Rust 언어의 규칙이 아니다 |
| 기본값 < 파일 < 환경변수 < 커맨드라인 | 원본 팁이 말하는 관례 — 언어가 강제하지 않는다 |
| `config` 크레이트가 계층을 자동 관리한다 | `config` 크레이트의 동작(원본 팁의 주장 · 확인 필요) |
| 환경변수에 `APP_` 접두사 · `__` 중첩 | 관례 + 크레이트 설정(확인 필요) — 언어와 무관 |
| `u16` 필드에 70000 이 들어갈 수 없다 | 언어 보장(정수 타입의 범위) |
| `parse()` 의 목표 타입이 필드 타입에서 정해진다 | 언어 보장(타입 추론) |
| 흉내 파서가 섹션을 무시한다 | 이 예제의 구현 — 진짜 TOML 파서의 동작이 아니다 |
| `{:?}` 로 찍은 구조체 모양 | `derive(Debug)` 가 만드는 모양 — 정확한 꼴은 안정 보장이 아니다(확인 필요) |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 설정 필드가 여럿이고 타입이 다르다 | 도메인별 구조체 + `Default` | 문자열 `HashMap` 을 들고 다니기 |
| 배포 환경마다 포트 · DB 주소만 다르다 | 환경변수 층으로 덮기 | 환경마다 소스 코드 고치기 |
| 개발/운영/테스트 묶음 값 | 프로필 | 같은 값을 여러 곳에 흩어 적기 |
| 실제 프로젝트의 TOML 파일 | `toml`/`config` 크레이트 | 예제의 줄 단위 흉내 파서 |
| 잘못된 값 거르기 | `build` 에서 `Result` 로 검사 | 쓰는 곳마다 그때그때 검사하기 |
| 숫자 설정이 틀렸을 때 | 파싱 실패를 `Err` 로 올리기 | `if let Ok` 로 조용히 버리기 |

## 핵심 문장

1. **설정은 층으로 쌓는다** — 기본값 위에 파일, 그 위에 환경변수, 그 위에 커맨드라인을 얹고 위가 이긴다.
2. **이 빌더에서 우선순위는 부른 순서다** — `mut self` 를 받아 `self` 를 돌려주는 메서드를 이어 부르면 뒤가 앞을 덮는다.
3. **설정은 타입 있는 구조체에 담는다** — 필드 타입이 `parse` 의 목표를 정하고, 이름 실수는 컴파일러가 잡는다.
4. **검사는 `build` 에서 한 번에, 일찍 한다** — `Result` 로 실패를 돌려주는 fail-fast.
5. **흉내 파서는 섹션 · 줄 끝 주석 · 파싱 실패를 다루지 못한다** — 실전은 크레이트에 맡긴다.

## 관련 자료

- `serde-json` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- `file-io` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- [logging](../10-logging/2-summary.md)
- 원본: study-site 항목 데이터 `data/rust/practical.json` 의 `config`

## 용어 풀이

- **설정 관리** — 프로그램이 쓰는 바깥 값(주소 · 포트 · 레벨 등)을 모으고 합치고 검사하는 일.
- **계층 설정** — 여러 소스의 설정을 우선순위대로 겹쳐 최종 값을 정하는 방식.
- **설정 소스** — 설정 값이 오는 곳 하나(기본값 · 파일 · 환경변수 · 프로필 · 커맨드라인).
- **타입 안전 설정** — 설정을 타입이 정해진 구조체 필드로 담는 방식.
- **`Default` 트레이트** — 타입의 기본값을 돌려주는 `default()` 를 약속하는 표준 트레이트.
- **빌더 패턴** — 메서드를 이어 불러 값을 채우고 `build()` 로 완성하는 방식.
- **환경변수** — 운영체제가 프로세스에 넘기는 「이름=값」 문자열 쌍.
- **접두사(prefix)** — 내 프로그램의 환경변수를 가려내려고 이름 앞에 붙이는 글자(`APP_`).
- **프로필** — 실행 환경 이름 하나에 묶인 설정 값 묶음.
- **TOML** — `[섹션]` 과 `키 = 값` 줄로 쓰는 설정 파일 형식.
- **섹션 헤더** — TOML 에서 `[server]` 처럼 대괄호로 묶은 줄. 아래 키들의 묶음 이름이다.
- **fail-fast** — 잘못된 상태를 가장 이른 시점에 바로 실패시키는 원칙.
- **`dotenv`** — `.env` 파일의 내용을 환경변수로 읽어 들이는 크레이트(원본 팁).
- **`config` 크레이트** — 여러 소스를 쌓아 병합하고 구조체로 풀어 주는 설정 크레이트.
- **원시 문자열** — `r#"…"#` 꼴. 안의 `"` 와 `\` 를 그대로 둔다.

## 더 들어가면

- `try_deserialize::<AppConfig>()` 를 쓰려면 구조체에 `serde` 의 `#[derive(Deserialize)]` 가 붙어야 한다 — 예제 구조체에는 `Debug, Clone` 만 있다(확인 필요).
- `config` 크레이트에서 `__` 를 중첩 구분자로 쓰려면 `Environment::with_prefix("APP").separator("__")` 처럼 구분자를 따로 지정해야 하는 것으로 알려져 있다(확인 필요).
- `config` 크레이트에서도 우선순위는 `add_source` 를 부른 순서로 정해지며, 뒤에 더한 소스가 이기는 것으로 알려져 있다(확인 필요).
- `dotenv` 크레이트는 관리가 멈춰, 포크인 `dotenvy` 를 쓰는 경우가 많다고 알려져 있다(확인 필요).
- 커맨드라인 층은 흔히 `clap` 크레이트로 읽어 마지막에 덮는다(확인 필요).
- 비밀번호가 든 DB URL 을 `{:?}` 로 통째로 찍으면 로그에 비밀이 샌다 — 민감 필드는 `Debug` 를 직접 구현해 가리는 방식이 쓰인다(확인 필요).
