# rust/rust-project-structures/08 — JWT 인증 구조 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 시나리오 2 · 4 · 5 가 찍는 줄 (예측)

```rust
// 질문용 발췌 — auth 는 발급과 같은 비밀키를 쓴다
handle_request(&auth, Some(&format!("Bearer {}", user_token)), "admin"); // 2
handle_request(&auth, None, "user");                                    // 4
handle_request(&auth, Some("Bearer invalid.token.here"), "user");       // 5
```

- 2번은 「허용」「거부」「인증 실패」 중 무엇으로 시작하는 줄을 찍고, 뒤에 무엇이 붙는가?
- 4번이 찍는 줄은 무엇인가?
- 5번에서 찍히는 오류 메시지는 「잘못된 토큰 형식」과 「잘못된 서명」 중 어느 것인가?

### 2. 다른 비밀키로 검증하면 (예측)

```rust
// 질문용 발췌
let issuer   = JwtService::new("my-secret-key-2026", 3600);
let verifier = JwtService::new("another-secret", 3600);
let token = issuer.generate("user_1", "admin");
match verifier.verify(&token) {
    Ok(c) => println!("유효: {:?}", c),
    Err(e) => println!("에러: {}", e),
}
```

- `verify` 는 몇 번째 검사에서 멈추고, 어떤 줄이 찍히는가?

### 3. 원시 문자열 안의 겹 중괄호 (예측)

```rust
// 질문용 발췌
println!(r#"use jsonwebtoken::{{encode, decode}};"#);
```

- 화면에 찍히는 한 줄은 정확히 어떤 모양인가?

### 4. 토큰의 `exp` 숫자를 직접 늘려 보내면 막히는 이유 (왜)

- 사용자가 토큰 문자열 속 `exp` 숫자를 더 큰 값으로 바꿔 보내도 통과하지 못하는 까닭은 무엇인가?

### 5. 서명이 있어도 비밀번호를 넣으면 안 되는 이유 (왜)

- 서명된 토큰인데도 비밀번호 같은 민감 정보를 클레임에 넣으면 안 되는 까닭은 무엇인가?

### 6. 인증과 인가를 두 메서드로 나눈 이유 (왜)

- `authenticate` 와 `authorize` 를 한 메서드로 합치지 않고 나눠 두면 무엇이 좋은가?

### 7. `user_id` 에 들어간 특수 문자 (경계)

- `user_id` 가 `"kim.lee"` 일 때 발급한 토큰은 검증을 통과하는가?
- `user_id` 가 `"kim:lee"` 일 때는 어떻게 되는가?

### 8. 만료 시각과 정확히 같은 순간 (경계)

- `now_timestamp()` 가 `claims.exp` 와 똑같은 값을 낼 때 `verify` 의 결과는 무엇인가?

### 9. 헤더 접두사의 모양 (경계)

- 헤더가 `"bearer abc.def"`(소문자 b)이면 어느 단계에서 어떤 오류가 나는가?
- 헤더가 `"Bearer "` 하나뿐이면 어떤 오류로 끝나는가?

### 10. `?` 와 `'a` 가 이어 주는 것 (연결)

- `extract_token` 에서 `auth_header.ok_or(AuthError::MissingToken)?` 는 `Option` 과 `Result` 를 어떻게 이어 주는가?
- 반환 타입이 `Result<&'a str, AuthError>` 로 헤더의 라이프타임에 묶인 까닭은 무엇인가?

## 실습

### 실습 1. 간소화 JWT 발급 · 검증 · 인증 미들웨어 만들기

**만들 것** — 표준 라이브러리만으로 토큰을 발급 · 검증하는 `JwtService` 와, `Bearer` 헤더를 받아 인증 → 인가를 하는 `AuthMiddleware` 를 만들고 다섯 시나리오로 시연한다.

**준비물** — 외부 크레이트는 필요 없다. 서명은 HMAC-SHA256 대신 시작 코드에 준 흉내 해시 `sign` 을 쓰고, `jsonwebtoken` 사용법은 문자열로 찍기만 한다(흉내).

**요구 조건**

1단계 — 데이터
1. `Claims` 는 `sub`(String) · `role`(String) · `exp`(u64) · `iat`(u64) 네 필드를 갖고 `Debug` · `Clone` 을 derive 한다.
2. `AuthError` 는 `MissingToken` · `InvalidFormat` · `Expired` · `InvalidSignature` · `InsufficientPermission` 다섯 변형이고, `Display` 로 각각 「토큰 없음」「잘못된 토큰 형식」「토큰 만료」「잘못된 서명」「권한 부족」을 낸다.

2단계 — `JwtService`
3. `new(secret, expiration_secs)` 가 비밀키와 만료 초를 저장한다.
4. `now_timestamp()` 는 현재 Unix 초를 `u64` 로 돌려주는 연관 함수다.
5. `generate(user_id, role)` 는 `iat = 지금`, `exp = 지금 + 만료 초` 로 클레임을 만들고, `sub:role:exp:iat` 페이로드에 서명을 계산해 `페이로드.서명` 꼴의 토큰을 돌려준다.
6. `verify(token)` 은 마지막 `.` 에서 둘로 나눠(둘이 아니면 `InvalidFormat`), 페이로드를 다시 서명해 비교하고(다르면 `InvalidSignature`), `:` 로 4조각인지 보고(아니면 `InvalidFormat`), `exp` · `iat` 를 숫자로 바꾸고(실패하면 `InvalidFormat`), 지금이 `exp` 보다 크면 `Expired`, 아니면 `Ok(Claims)` 다.

3단계 — `AuthMiddleware`
7. `extract_token` 은 헤더가 없으면 `MissingToken`, `"Bearer "` 로 시작하지 않으면 `InvalidFormat`, 아니면 접두사를 뗀 나머지를 헤더에서 빌린 `&str` 로 돌려준다.
8. `authenticate` 는 토큰을 꺼낸 뒤 `verify` 한다.
9. `authorize` 는 역할이 `admin` 이거나 요구 역할과 같으면 `Ok(())`, 아니면 `InsufficientPermission` 이다.

4단계 — 시연
10. `handle_request` 는 인증 실패면 `  인증 실패: <메시지>`, 인가 거부면 `  거부: <메시지> (user=<sub>, role=<role>)`, 통과면 `  허용: user=<sub>, role=<role>` 을 찍는다.
11. `main` 은 비밀키 `"my-secret-key-2026"`, 만료 3600초로 서비스를 만들고, `("user_1", "admin")` · `("user_2", "user")` 토큰을 발급해 앞 30자 뒤에 `...` 를 붙여 찍은 뒤, admin 토큰을 검증해 `유효: <Debug>` 또는 `에러: <메시지>` 를 찍는다.
12. `main` 은 같은 비밀키로 새 `JwtService` 를 만들어 미들웨어에 넣고, 다섯 시나리오(admin→admin · user→admin · user→user · 헤더 없음 · `"Bearer invalid.token.here"`)를 번호 머리줄과 함께 돌린다.
13. 마지막에 `jsonwebtoken` 의 `encode` · `decode` 사용 예를 원시 문자열로 찍는다.

**시작 코드**

```rust
use std::time::{SystemTime, UNIX_EPOCH};

#[derive(Debug, Clone)]
struct Claims {
    // TODO: sub, role, exp, iat
}

#[derive(Debug)]
enum AuthError {
    // TODO: 다섯 가지 실패
}

impl std::fmt::Display for AuthError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        // TODO: 변형마다 한국어 메시지
        todo!()
    }
}

struct JwtService {
    secret: String,
    expiration_secs: u64,
}

impl JwtService {
    fn new(secret: &str, expiration_secs: u64) -> Self {
        todo!() // TODO
    }

    fn now_timestamp() -> u64 {
        todo!() // TODO: UNIX_EPOCH 부터의 초
    }

    fn generate(&self, user_id: &str, role: &str) -> String {
        todo!() // TODO: 클레임 → "sub:role:exp:iat" → "페이로드.서명"
    }

    fn verify(&self, token: &str) -> Result<Claims, AuthError> {
        todo!() // TODO: 나누기 → 서명 → 파싱 → 만료
    }

    // 주어진 것: HMAC-SHA256 자리를 흉내 낸 서명 (고치지 않는다)
    fn sign(&self, payload: &str) -> String {
        let hash: u64 = payload.bytes()
            .zip(self.secret.bytes().cycle())
            .fold(0u64, |acc, (a, b)| acc.wrapping_mul(31).wrapping_add((a ^ b) as u64));
        format!("{:016x}", hash)
    }
}

struct AuthMiddleware {
    jwt: JwtService,
}

impl AuthMiddleware {
    fn new(jwt: JwtService) -> Self {
        todo!() // TODO
    }

    fn extract_token<'a>(&self, auth_header: Option<&'a str>) -> Result<&'a str, AuthError> {
        todo!() // TODO: 헤더 없음 / "Bearer " 떼기
    }

    fn authenticate(&self, auth_header: Option<&str>) -> Result<Claims, AuthError> {
        todo!() // TODO
    }

    fn authorize(&self, claims: &Claims, required_role: &str) -> Result<(), AuthError> {
        todo!() // TODO: admin 은 통과, 나머지는 정확히 같아야
    }
}

fn handle_request(middleware: &AuthMiddleware, auth_header: Option<&str>, required_role: &str) {
    // TODO: 인증 → 인가 → 허용 / 거부 / 인증 실패 줄 찍기
}

fn main() {
    println!("=== JWT 인증 구조 ===");
    // TODO: 서비스 생성, 토큰 두 개 발급, 앞 30자 출력
    println!("\n--- 토큰 검증 ---");
    // TODO: admin 토큰 검증 결과 출력
    println!("\n--- 미들웨어 ---");
    // TODO: 같은 비밀키로 미들웨어 생성, 시나리오 1~5
    println!("\n=== 실제 구현: jsonwebtoken 크레이트 ===");
    // TODO: encode / decode 사용 예를 원시 문자열로 출력
}
```

**확인 방법** — `rustc auth-jwt.rs && ./auth-jwt`(또는 `cargo run`)로 돌려, 시나리오 1 · 3 은 「허용」, 2 는 「거부: 권한 부족」, 4 · 5 는 「인증 실패」 줄인지, 그리고 마지막 줄들의 중괄호가 하나씩 찍히는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
