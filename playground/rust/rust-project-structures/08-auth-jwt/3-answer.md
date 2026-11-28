# rust/rust-project-structures/08 — JWT 인증 구조 — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 거부: 권한 부족 · 인증 실패: 토큰 없음 · 인증 실패: 잘못된 서명

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
  거부: 권한 부족 (user=user_2, role=user)
  인증 실패: 토큰 없음
  인증 실패: 잘못된 서명
```

**왜 그런가**
- 2번: 토큰은 같은 비밀키로 발급된 진짜라 인증은 통과한다.
  역할 `user` 는 `admin` 도 아니고 요구 역할 `admin` 과도 다르므로 `InsufficientPermission` 이다.
  인증을 통과했으니 거부 줄에 `user` · `role` 이 찍힌다.
- 4번: 헤더가 `None` 이라 `ok_or(MissingToken)?` 에서 바로 끝난다.
- 5번: `"Bearer "` 를 떼면 `invalid.token.here` 다.
  `rsplitn(2, '.')` 이 서명 자리 `"here"` 와 페이로드 `"invalid.token"` 으로 나눈다.
  `sign` 은 늘 16글자라 4글자 `"here"` 와 같을 수 없다 → 서명 검사가 파싱보다 먼저라 `InvalidSignature` 가 먼저 나온다.
- 근거: 2-summary 「동작 방식 (3)」 · 「동작 방식 (5)」.

### 2. 두 번째 검사(서명)에서 멈춘다 — 「에러: 잘못된 서명」

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
에러: 잘못된 서명
```

**왜 그런가**
- 토큰에는 `.` 이 있어 첫 검사(둘로 나누기)는 통과한다.
- `verifier` 는 `"another-secret"` 바이트로 XOR 하므로 다시 계산한 서명이 발급 때 서명과 다르다 → `InvalidSignature`.
- 이론상 두 해시가 우연히 같을 수는 있지만 사실상 일어나지 않는다고 본다(원본에 근거 없음 — 추론).
- 근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 6」.

### 3. 중괄호가 하나씩 찍힌다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
use jsonwebtoken::{encode, decode};
```

**왜 그런가**
- `r#"…"#` 는 따옴표 · 역슬래시를 그대로 두는 원시 문자열일 뿐이다.
- `println!` 의 첫 인자는 포맷 문자열이라 `{{` · `}}` 는 여전히 글자 중괄호 하나로 바뀐다.
- 근거: 2-summary 「동작 방식 (6)」 · 「문법 — 형태와 규칙」.

### 4. `exp` 가 서명된 페이로드 안에 있기 때문이다

- `verify` 는 받은 페이로드로 서명을 다시 계산해 붙어 온 서명과 비교한다.
- `exp` 숫자를 바꾸면 페이로드가 바뀌어 다시 계산한 서명이 원래 서명과 어긋난다 → `InvalidSignature`.
- 맞는 서명을 새로 만들려면 비밀키가 필요한데, 사용자는 비밀키를 모른다.
- 근거: 2-summary 「동작 방식 (3)」 · 「핵심 문장 3」.

### 5. 서명은 내용을 숨기지 않기 때문이다

- 페이로드는 평문으로 토큰에 실리고, 예제가 토큰 앞 30자를 찍으면 `user_1:admin:` 이 그대로 보인다.
- 서명은 「고쳤나」만 알려 줄 뿐, 토큰을 본 누구나 클레임을 읽는다.
- 근거: 2-summary 「동작 방식 (1)」 · 「어디서 틀리나 4」.

### 6. 「누구인가」와 「해도 되나」가 다른 질문이기 때문이다

- 실패 이유가 갈린다 — 인증 실패(누군지 모름)와 인가 거부(누군지 알지만 권한 없음)를 다른 메시지로 낼 수 있다.
- `authorize` 는 검증을 마친 `Claims` 만 받으므로, 위조된 역할을 믿을 길이 없다.
- 한 번 인증한 `Claims` 로 경로마다 요구 역할만 바꿔 인가를 되풀이할 수 있다.
- 근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 11」.

### 7. `.` 은 통과, `:` 는 `InvalidFormat`

- `"kim.lee"`: `rsplitn` 은 마지막 `.` 에서만 나누고, 16진수 서명에는 `.` 이 없으므로 페이로드가 온전히 남는다 → 통과한다.
- `"kim:lee"`: 서명은 맞지만 `split(':')` 이 5조각이 되어 4조각 검사에서 `InvalidFormat` 이다.
- 근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 1」.

### 8. 아직 유효하다 — `Ok(Claims)`

- 만료 검사는 `now > exp` 일 때만 `Expired` 다.
- 같은 값이면 조건이 거짓이라 `Ok(claims)` 로 끝난다.
- 근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 2」.

### 9. 소문자는 꺼내는 단계의 `InvalidFormat`, 빈 토큰은 검증 단계의 `InvalidFormat`

- `"bearer abc.def"`: `strip_prefix("Bearer ")` 가 대소문자까지 맞추므로 `None` → `extract_token` 에서 `InvalidFormat`.
- `"Bearer "`: 접두사는 떼어지고 토큰은 `""` 다.
  `""` 에는 `.` 이 없어 `rsplitn` 결과가 1조각 → `verify` 첫 검사에서 `InvalidFormat`.
  두 경우 모두 `handle_request` 는 「인증 실패: 잘못된 토큰 형식」을 찍는다.
- 근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 3」.

### 10. `?` 는 `None` 을 도메인 오류로 바꿔 돌려주고, `'a` 는 「반환값이 헤더를 빌린다」고 알린다

- `ok_or(AuthError::MissingToken)` 이 `Option<&str>` 를 `Result<&str, AuthError>` 로 바꾸고, `?` 가 `Err` 면 함수에서 바로 그 오류를 돌려준다.
  그래서 「헤더 없음」이 따로 `if` 없이 `MissingToken` 으로 이어진다.
- `strip_prefix` 가 돌려주는 것은 헤더 문자열의 일부를 가리키는 `&str` 다.
  그 참조는 헤더가 살아 있는 동안만 유효하므로, 반환 수명을 `self` 가 아니라 헤더의 `'a` 에 묶어 적는다.
- 근거: 2-summary 「동작 방식 (4)」 · 「문법 — 형태와 규칙」.

## 실습 정답

### 실습 1. 간소화 JWT 발급 · 검증 · 인증 미들웨어 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 클레임 네 필드 · derive | `#[derive(Debug, Clone)] struct Claims { sub, role, exp, iat }` |
| 2. 오류 다섯 변형 · 메시지 | `enum AuthError` · `impl std::fmt::Display for AuthError` 의 `match self` |
| 3. 서비스 생성 | `JwtService::new` |
| 4. 현재 Unix 초 | `JwtService::now_timestamp` (`SystemTime::now().duration_since(UNIX_EPOCH)`) |
| 5. 발급 | `JwtService::generate` — `format!("{}:{}:{}:{}", …)` · `self.sign(&payload)` · `format!("{}.{}", payload, signature)` |
| 6. 검증 | `JwtService::verify` — `rsplitn(2, '.')` · `self.sign(payload) != signature` · `split(':')` · `parse().map_err(…)?` · `now_timestamp() > claims.exp` |
| 7. Bearer 꺼내기 | `AuthMiddleware::extract_token<'a>` — `ok_or(AuthError::MissingToken)?` · `strip_prefix("Bearer ")` |
| 8. 인증 | `AuthMiddleware::authenticate` |
| 9. 인가 | `AuthMiddleware::authorize` — `claims.role == "admin" \|\| claims.role == required_role` |
| 10. 결과 줄 | `handle_request` 의 겹친 `match` |
| 11. 발급 · 앞 30자 · 검증 출력 | `main` 의 `jwt.generate(…)` · `&admin_token[..30]` · `match jwt.verify(&admin_token)` |
| 12. 다섯 시나리오 | `main` 의 `AuthMiddleware::new(JwtService::new("my-secret-key-2026", 3600))` 와 `handle_request` 다섯 번 |
| 13. 크레이트 사용 예 | `main` 끝의 `println!(r#"…{{…}}…"#)` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`rust/rust-project-structures/reference/auth-jwt.rs`

```rust
// [실무 프로젝트 구조] JWT 인증 구조
// 설명: JWT 토큰 생성, 검증, 미들웨어 패턴
// 팁: JWT는 Header.Payload.Signature 구조이며, 서명으로 위조를 방지한다. jsonwebtoken 크레이트가 Rust에서 가장 많이 사용된다. 토큰에 민감 정보(비밀번호 등)를 넣지 않는다. exp(만료), iat(발급), sub(주체) 클레임은 표준이다. 미들웨어에서 인증(authentication)과 인가(authorization)를 분리한다. 리프레시 토큰 패턴으로 긴 세션을 관리한다.
// Rust 모듈 시스템 특징: 인증 모듈은 보통 src/auth/ 디렉토리로 분리하고 mod.rs에 pub mod jwt; pub mod middleware; 같이 정의한다. JWT 비밀키는 feature flag로 환경별 설정(dev/prod)을 분리할 수 있다. 헥사고날 아키텍처에서는 AuthService를 도메인 포트로, JwtService를 어댑터로 둔다.

// 표준 라이브러리: HashMap (예시 데이터용)
use std::collections::HashMap;
// 시간 처리: 토큰 만료 검증에 필요
use std::time::{SystemTime, UNIX_EPOCH};

// === JWT 구조 (간소화) ===
// 클레임: 토큰에 담기는 페이로드 정보
#[derive(Debug, Clone)]
struct Claims {
    sub: String,       // subject (user_id)
    role: String,      // 역할
    exp: u64,          // 만료 시간 (Unix timestamp)
    iat: u64,          // 발급 시간
}

// 인증 관련 에러 타입 (도메인 에러)
#[derive(Debug)]
enum AuthError {
    MissingToken,
    InvalidFormat,
    Expired,
    InvalidSignature,
    InsufficientPermission,
}

// Display 구현으로 사용자 친화적 메시지 출력
impl std::fmt::Display for AuthError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            AuthError::MissingToken => write!(f, "토큰 없음"),
            AuthError::InvalidFormat => write!(f, "잘못된 토큰 형식"),
            AuthError::Expired => write!(f, "토큰 만료"),
            AuthError::InvalidSignature => write!(f, "잘못된 서명"),
            AuthError::InsufficientPermission => write!(f, "권한 부족"),
        }
    }
}

// === JWT 서비스 ===
// 토큰 생성/검증 책임을 가진 서비스
struct JwtService {
    secret: String,
    expiration_secs: u64,
}

impl JwtService {
    // 시크릿 키와 만료 시간을 받아 서비스 초기화
    fn new(secret: &str, expiration_secs: u64) -> Self {
        JwtService {
            secret: secret.to_string(),
            expiration_secs,
        }
    }

    // 현재 Unix timestamp 반환 (연관 함수)
    fn now_timestamp() -> u64 {
        SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs()
    }

    // 토큰 생성 (실제로는 jsonwebtoken 크레이트 사용)
    fn generate(&self, user_id: &str, role: &str) -> String {
        let now = Self::now_timestamp();
        // 클레임 구성
        let claims = Claims {
            sub: user_id.to_string(),
            role: role.to_string(),
            exp: now + self.expiration_secs,
            iat: now,
        };
        // 간소화된 토큰 (실제로는 Header.Payload.Signature)
        let payload = format!("{}:{}:{}:{}",
                              claims.sub, claims.role, claims.exp, claims.iat);
        // 서명 계산 후 페이로드와 결합
        let signature = self.sign(&payload);
        format!("{}.{}", payload, signature)
    }

    // 토큰 검증
    fn verify(&self, token: &str) -> Result<Claims, AuthError> {
        // 마지막 .을 기준으로 분리 (페이로드와 서명)
        let parts: Vec<&str> = token.rsplitn(2, '.').collect();
        if parts.len() != 2 {
            return Err(AuthError::InvalidFormat);
        }
        // rsplitn은 역순이므로 [0]이 서명, [1]이 페이로드
        let signature = parts[0];
        let payload = parts[1];

        // 서명 검증
        // 페이로드를 다시 서명하여 일치하는지 확인
        if self.sign(payload) != signature {
            return Err(AuthError::InvalidSignature);
        }

        // 페이로드 파싱
        // : 구분자로 분리하여 4개 필드 추출
        let fields: Vec<&str> = payload.split(':').collect();
        if fields.len() != 4 {
            return Err(AuthError::InvalidFormat);
        }

        // 클레임 재구성 (parse 에러는 InvalidFormat으로 변환)
        let claims = Claims {
            sub: fields[0].to_string(),
            role: fields[1].to_string(),
            exp: fields[2].parse().map_err(|_| AuthError::InvalidFormat)?,
            iat: fields[3].parse().map_err(|_| AuthError::InvalidFormat)?,
        };

        // 만료 검증
        if Self::now_timestamp() > claims.exp {
            return Err(AuthError::Expired);
        }

        Ok(claims)
    }

    // 서명 생성 (private 메서드)
    fn sign(&self, payload: &str) -> String {
        // 간소화된 서명 (실제로는 HMAC-SHA256)
        // 페이로드와 시크릿을 XOR 후 폴딩하여 해시 생성
        let hash: u64 = payload.bytes()
            .zip(self.secret.bytes().cycle())
            .fold(0u64, |acc, (a, b)| acc.wrapping_mul(31).wrapping_add((a ^ b) as u64));
        // 16자리 16진수 문자열로 출력
        format!("{:016x}", hash)
    }
}

// === 인증 미들웨어 패턴 ===
// JWT 서비스를 감싸 HTTP 헤더 처리까지 담당
struct AuthMiddleware {
    jwt: JwtService,
}

impl AuthMiddleware {
    // JwtService를 받아 미들웨어 생성
    fn new(jwt: JwtService) -> Self {
        AuthMiddleware { jwt }
    }

    // Bearer 토큰 추출
    // 라이프타임 'a로 입력 슬라이스의 일부를 반환
    fn extract_token<'a>(&self, auth_header: Option<&'a str>) -> Result<&'a str, AuthError> {
        let header = auth_header.ok_or(AuthError::MissingToken)?;
        // "Bearer " 접두사 제거
        header.strip_prefix("Bearer ")
            .ok_or(AuthError::InvalidFormat)
    }

    // 인증
    // 헤더에서 토큰 추출 후 검증까지 한 번에
    fn authenticate(&self, auth_header: Option<&str>) -> Result<Claims, AuthError> {
        let token = self.extract_token(auth_header)?;
        self.jwt.verify(token)
    }

    // 인가 (역할 확인)
    // admin은 모든 권한, 그 외는 정확히 일치해야 통과
    fn authorize(&self, claims: &Claims, required_role: &str) -> Result<(), AuthError> {
        if claims.role == "admin" || claims.role == required_role {
            Ok(())
        } else {
            Err(AuthError::InsufficientPermission)
        }
    }
}

// === 요청 처리 시뮬레이션 ===
// 인증 → 인가 → 결과 출력의 흐름을 보여주는 헬퍼
fn handle_request(middleware: &AuthMiddleware, auth_header: Option<&str>, required_role: &str) {
    match middleware.authenticate(auth_header) {
        Ok(claims) => {
            // 인증 성공 후 인가 체크
            match middleware.authorize(&claims, required_role) {
                Ok(()) => println!("  허용: user={}, role={}", claims.sub, claims.role),
                Err(e) => println!("  거부: {} (user={}, role={})", e, claims.sub, claims.role),
            }
        }
        Err(e) => println!("  인증 실패: {}", e),
    }
}

// 진입점: JWT 발급/검증/미들웨어 시연
fn main() {
    println!("=== JWT 인증 구조 ===");
    let jwt = JwtService::new("my-secret-key-2026", 3600); // 1시간

    // 토큰 생성
    // 서로 다른 권한의 토큰 발급
    let admin_token = jwt.generate("user_1", "admin");
    let user_token = jwt.generate("user_2", "user");
    println!("Admin 토큰: {}...", &admin_token[..30]);
    println!("User 토큰: {}...", &user_token[..30]);

    // 토큰 검증
    println!("\n--- 토큰 검증 ---");
    match jwt.verify(&admin_token) {
        Ok(claims) => println!("유효: {:?}", claims),
        Err(e) => println!("에러: {}", e),
    }

    // 미들웨어 테스트
    println!("\n--- 미들웨어 ---");
    let auth = AuthMiddleware::new(JwtService::new("my-secret-key-2026", 3600));

    // 시나리오 1: admin 권한 요구되는 곳에 admin 접근
    println!("1. Admin이 admin 페이지 접근:");
    handle_request(&auth, Some(&format!("Bearer {}", admin_token)), "admin");

    // 시나리오 2: admin 권한 요구되는 곳에 일반 user 접근 → 거부
    println!("2. User가 admin 페이지 접근:");
    handle_request(&auth, Some(&format!("Bearer {}", user_token)), "admin");

    // 시나리오 3: user 권한이면 충분
    println!("3. User가 user 페이지 접근:");
    handle_request(&auth, Some(&format!("Bearer {}", user_token)), "user");

    // 시나리오 4: 토큰이 아예 없음
    println!("4. 토큰 없음:");
    handle_request(&auth, None, "user");

    // 시나리오 5: 위조/변조된 토큰
    println!("5. 잘못된 토큰:");
    handle_request(&auth, Some("Bearer invalid.token.here"), "user");

    // 실제 크레이트
    println!("\n=== 실제 구현: jsonwebtoken 크레이트 ===");
    println!(r#"use jsonwebtoken::{{encode, decode, Header, Validation, EncodingKey, DecodingKey}};

let token = encode(
    &Header::default(),
    &claims,
    &EncodingKey::from_secret(secret.as_ref()),
)?;

let decoded = decode::<Claims>(
    &token,
    &DecodingKey::from_secret(secret.as_ref()),
    &Validation::default(),
)?;"#);
}
```

**실행 결과** — 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다).

**풀이 요점**
- 검증 차례는 나누기 → 서명 → 파싱 → 만료이고, 오류는 모두 `AuthError` 한 타입으로 모은다.
- `rsplitn(2, '.')` 의 결과는 오른쪽부터라 `[0]` 이 서명, `[1]` 이 페이로드다.
- `map_err(|_| AuthError::InvalidFormat)?` 로 숫자 변환 오류를 도메인 오류로 바꿔 전파한다.
- `extract_token` 은 헤더를 빌린 조각을 돌려주므로 반환 라이프타임을 헤더의 `'a` 에 묶는다.
- 미들웨어의 `JwtService` 는 발급과 같은 비밀키여야 시나리오 1 · 3 이 통과한다.
- 정답 코드의 `use std::collections::HashMap;` 은 쓰이지 않는 import 라 빼도 동작이 같다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다) |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
