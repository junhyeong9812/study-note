# rust/rust-project-structures/08 — JWT 인증 구조 — 정리 (힌트)

> 출처 — study-site 항목 `rust/auth-jwt`(항목 데이터 `data/rust/project-structures.json`) · 정답 코드 study-practice `rust/rust-project-structures/reference/auth-jwt.rs`\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).\
> 실행 — 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다).

## 한눈에 — 쉽게 말하면

**JWT 인증은 「도장 찍힌 놀이공원 입장권」이다.**
매표소는 입장권에 이름 · 등급 · 유효 시각을 적는다.
그리고 매표소만 가진 도장 틀로 도장을 찍는다.
입구 직원은 먼저 도장이 진짜인지 본다.
도장이 진짜면 그다음에 「이 등급으로 이 구역에 들어가도 되나」를 본다.
글씨를 고쳐 쓰면 도장 자국과 맞지 않게 되어 들통난다.
JWT 인증도 똑같은 구조다.

| 비유 | 실체 |
|---|---|
| 입장권 | 토큰(`String`) |
| 적힌 이름 · 등급 · 유효 시각 · 발급 시각 | 클레임 `sub` · `role` · `exp` · `iat` |
| 매표소의 도장 틀 | 비밀키 `secret` |
| 도장 자국 | 서명 `signature` |
| 표를 내미는 손 | `Authorization: Bearer <토큰>` 헤더 |
| 입구 직원 | `AuthMiddleware` |
| 도장이 진짜인지 보기 | 인증 `authenticate` |
| 등급으로 구역 출입 판단 | 인가 `authorize` |

```text
[매표소: JwtService::generate]            [입구: AuthMiddleware]
 이름·등급·유효시각  ──도장(secret)──▶  토큰  ──"Bearer 토큰"──▶  ① 도장 진짜? (인증)
                                                                    ② 등급 맞나? (인가)
                                                                    ③ 허용 / 거부 / 인증 실패
```

> **토큰** — 서버가 발급하고 클라이언트가 요청마다 들고 오는 증명 문자열.\
> 예: `user_1:admin:<exp>:<iat>.<16자리 16진수>`.

> **클레임** — 토큰 안에 담긴 「이 사용자에 대한 주장」 한 조각.\
> 예: `sub = "user_1"`, `role = "admin"`.

## 이 주제가 답하려는 질문

1. 서버가 사용자 정보를 따로 저장하지 않고도, 들고 온 토큰이 자기가 발급한 진짜인지 어떻게 아나?
2. 토큰을 받은 쪽은 어떤 차례로 검사하고, 어느 단계에서 어떤 오류를 내나?
3. 「누구인가(인증)」와 「무엇을 해도 되나(인가)」를 왜, 어떻게 나누나?
4. 이 간소화 구현은 실제 JWT · `jsonwebtoken` 크레이트와 어디가 다른가?

## 동작 방식

### (1) 토큰 만들기 — `generate`

**언제 쓰나** — 로그인에 성공한 사용자에게 토큰을 내줄 때.

```text
generate("user_1", "admin")
   │ now = 현재 Unix 초
   ▼
Claims { sub:"user_1", role:"admin", exp: now+3600, iat: now }
   │ ":" 로 이어 붙임
   ▼
payload  = "user_1:admin:<exp>:<iat>"
   │ sign(payload)
   ▼
token    = "<payload>.<signature 16자리 16진수>"
```

- 현재 시각을 Unix 초로 얻는다(`now_timestamp`).
- 만료 시각 `exp` 는 발급 시각에 `expiration_secs` 를 더한 값이다(예제는 3600초 = 1시간).
- 네 클레임을 `:` 로 이어 페이로드 문자열을 만든다.
- 페이로드에 서명을 계산해 `.` 뒤에 붙인다.
- 페이로드는 **평문 그대로** 토큰에 들어간다.
  그래서 예제가 토큰 앞 30자를 찍으면 `user_1:admin:` 과 숫자들이 그대로 보인다.
  서명은 내용을 숨기지 않는다 — 고쳤는지 알아낼 뿐이다.

> **Unix timestamp** — 1970-01-01 00:00:00 UTC 부터 지난 초의 수.\
> 예: `exp: 1700003600` 꼴의 `u64`.

### (2) 서명 — `sign`

**언제 쓰나** — 발급할 때 한 번, 검증할 때 다시 한 번 같은 계산을 한다.

```text
payload 바이트:  u  s  e  r  _  1  :  ...
secret 바이트 :  m  y  -  s  e  c  r  ...  (모자라면 cycle 로 되풀이)
                 └ XOR ┘
hash = hash*31 + (a^b)   (wrapping — 넘치면 감아 돈다)
   ▼
format!("{:016x}", hash)  → 16자리 16진수
```

- 페이로드 바이트와 비밀키 바이트를 짝지어(`zip`) XOR 한다.
- 비밀키가 짧으면 `cycle()` 로 되풀이해 길이를 맞춘다.
- `fold` 로 「곱하기 31, 더하기」를 되풀이해 `u64` 하나로 접는다.
- `wrapping_mul` · `wrapping_add` 라서 넘쳐도 패닉 없이 감아 돈다.
- 결과를 0을 채운 16자리 16진수로 적는다.
- 같은 페이로드 + 같은 비밀키 → 언제나 같은 서명이다.
  페이로드가 한 글자만 달라도, 비밀키가 달라도 서명이 (사실상) 달라진다.
- 원본 주석대로 이것은 **HMAC-SHA256 자리를 흉내 낸 것**이다 — 암호학적 서명이 아니다.

> **서명(signature)** — 비밀키를 아는 쪽만 만들 수 있는, 내용에 묶인 확인 값.\
> 예: `sign("user_1:admin:...")` → `"3fa2...c1"` 같은 16자리.

### (3) 토큰 검증 — `verify`

**언제 쓰나** — 요청에 실려 온 토큰을 믿기 전에.

```text
token
  │ rsplitn(2, '.')  → 마지막 '.' 에서 둘로
  ├─ 둘로 안 나뉨 ───────────────────────▶ InvalidFormat
  ▼ [0]=signature, [1]=payload
  │ sign(payload) == signature ?
  ├─ 다름 ───────────────────────────────▶ InvalidSignature
  ▼
  │ payload.split(':') 가 정확히 4조각?
  ├─ 아님 ───────────────────────────────▶ InvalidFormat
  ▼
  │ exp, iat 를 u64 로 parse
  ├─ 실패 ───────────────────────────────▶ InvalidFormat
  ▼
  │ now > exp ?
  ├─ 그렇다 ─────────────────────────────▶ Expired
  ▼
Ok(Claims)
```

- `rsplitn(2, '.')` 은 **오른쪽부터** 최대 2조각으로 나눈다.
  그래서 `[0]` 이 마지막 `.` 뒤(서명), `[1]` 이 그 앞 전부(페이로드)다.
- 서명은 16진수라 `.` 이 없으므로, 페이로드 안에 `.` 이 있어도 마지막 `.` 은 늘 서명 앞의 것이다.
- `.` 이 하나도 없으면 조각이 1개라 `InvalidFormat` 이다.
- **서명 검사가 파싱보다 먼저**다.
  그래서 생김새가 엉터리인 토큰도 `.` 만 있으면 「형식」보다 「서명」에서 먼저 걸린다.
  예: `invalid.token.here` → 서명 자리 `"here"` 는 4글자라 16자리 서명과 같을 수 없다 → `InvalidSignature`.
- `exp` 는 서명된 페이로드 안에 있다.
  누가 `exp` 숫자를 늘리면 페이로드가 바뀌어 다시 계산한 서명과 어긋난다 — 비밀키 없이는 맞는 서명을 새로 만들 수 없다.
- 만료 비교는 `now > exp` 다.
  `now == exp` 인 그 1초는 아직 유효하다.
- 숫자 변환 오류(`ParseIntError`)는 `map_err(|_| AuthError::InvalidFormat)?` 로 도메인 오류로 바꿔 바로 돌려준다.

### (4) Bearer 토큰 꺼내기 — `extract_token`

**언제 쓰나** — HTTP `Authorization` 헤더 값에서 토큰만 떼어 낼 때.

```text
Option<&str> 헤더
  │ ok_or(MissingToken)?
  ├─ None ─────────────────────▶ MissingToken
  ▼ "Bearer abc.def"
  │ strip_prefix("Bearer ")
  ├─ 접두사 없음 ──────────────▶ InvalidFormat
  ▼
"abc.def"   (헤더 문자열의 일부를 빌린 &str)
```

- 헤더가 없으면(`None`) `ok_or` 가 `Err(MissingToken)` 으로 바꾸고 `?` 가 바로 돌려준다.
- `strip_prefix("Bearer ")` 는 글자 그대로 맞을 때만 `Some(나머지)` 다.
  대소문자 · 공백 수까지 정확히 같아야 한다 — `"bearer abc"` 는 `None` → `InvalidFormat`.
- 반환하는 `&str` 는 새 문자열이 아니라 **헤더 문자열의 일부를 빌린 것**이다.
  그래서 시그니처가 `fn extract_token<'a>(&self, auth_header: Option<&'a str>) -> Result<&'a str, AuthError>` 다 — 반환값의 수명이 `self` 가 아니라 헤더에 묶인다고 적는다.

> **라이프타임 `'a`** — 빌린 참조가 얼마 동안 유효한지 이름 붙인 것.\
> 예: 입력 `&'a str` 의 조각을 돌려주면 반환도 `&'a str`.

### (5) 인증과 인가 — `authenticate` · `authorize` · `handle_request`

**언제 쓰나** — 보호된 경로마다 「누구인가」와 「해도 되나」를 차례로 묻을 때.

```text
handle_request(헤더, required_role)
   │ authenticate = extract_token → verify
   ├─ Err(e) ─────────────────────────────▶ "  인증 실패: <e>"
   ▼ Ok(claims)
   │ authorize(&claims, required_role)
   │   role == "admin" || role == required_role ?
   ├─ 아니다 ─────────────────────────────▶ "  거부: 권한 부족 (user=…, role=…)"
   ▼
"  허용: user=…, role=…"
```

- 인증(authentication)은 「이 토큰이 진짜이고 만료되지 않았나」만 본다 → 결과는 `Claims`.
- 인가(authorization)는 그 `Claims` 를 받아 「이 역할로 이 자원을 써도 되나」만 본다.
- 둘을 나누면 실패 이유가 갈린다 — 인증 실패는 「누군지 모름」, 인가 거부는 「누군지 알지만 권한 없음」.
  거부 줄에는 `user` · `role` 을 찍을 수 있는데, 인증은 이미 통과했기 때문이다.
- 이 예제의 규칙: `admin` 은 무엇이든 통과, 그 밖의 역할은 `required_role` 과 **정확히 같아야** 통과한다.
  역할 사이의 위아래(예: `editor` 가 `user` 를 포함)는 없다.
- 예제의 미들웨어는 발급에 쓴 것과 **같은 비밀키**로 새 `JwtService` 를 만든다.
  비밀키가 같아야 다시 계산한 서명이 맞는다.
- 예제 `main` 의 다섯 시나리오가 이 갈래를 모두 지난다: admin→admin(허용), user→admin(거부), user→user(허용), 헤더 없음(인증 실패), 위조 토큰(인증 실패).
- 원본이 말하는 설계: 헥사고날 아키텍처라면 `AuthService` 를 도메인 포트로, `JwtService` 를 어댑터로 둔다.
  미들웨어는 「토큰을 어떻게 서명하나」를 몰라도 되고, 서명 방식을 바꿔도 미들웨어는 그대로다.

### (6) 실제 구현과의 차이 — `jsonwebtoken` 크레이트

**언제 쓰나** — 실제 서비스에서는 직접 만든 서명 대신 크레이트를 쓴다.

```text
이 예제                         실제 JWT
payload "a:b:c:d"               Header.Payload.Signature  (점 두 개, 세 조각)
sign = 곱하기31 흉내            HMAC-SHA256 등
직접 parse                      encode(&Header, &claims, &EncodingKey)
                                decode::<Claims>(&token, &DecodingKey, &Validation)
```

- 원본 팁: 실제 JWT 는 `Header.Payload.Signature` 세 부분이며 서명으로 위조를 막는다.
- 예제 마지막은 `jsonwebtoken` 사용법을 **문자열로 출력만** 한다(크레이트를 쓰지 않는다).
- 그 출력은 `println!(r#"…"#)` 로 한다.
  `r#"…"#` 는 원시 문자열이라 `"` 와 `\` 를 그대로 둔다.
  하지만 `println!` 의 첫 인자는 **포맷 문자열**이라 `{` `}` 는 여전히 자리표시자로 읽힌다.
  그래서 중괄호를 글자로 찍으려고 `{{` · `}}` 로 썼고, 화면에는 `{` · `}` 하나씩 찍힌다.

## 문법 — 형태와 규칙

최소 예제(직접 쓴 것):

```rust
// Option → Result, 접두사 떼기, 오른쪽에서 나누기
fn bearer(h: Option<&str>) -> Result<&str, String> {
    let h = h.ok_or("토큰 없음".to_string())?;      // None 이면 여기서 Err 반환
    h.strip_prefix("Bearer ").ok_or("형식 오류".to_string())
}

fn split_sig(t: &str) -> Option<(&str, &str)> {
    let mut it = t.rsplitn(2, '.');                  // 오른쪽부터 최대 2조각
    let sig = it.next()?;                            // 마지막 '.' 뒤
    let payload = it.next()?;                        // 나머지 앞부분 전부
    Some((payload, sig))
}
```

규칙:

- `opt.ok_or(e)` — `Some(v)` → `Ok(v)`, `None` → `Err(e)`. 뒤에 `?` 를 붙이면 `Err` 일 때 함수에서 바로 돌아간다.
- `res.map_err(|_| 새오류)?` — 오류 타입을 도메인 오류로 바꾼 뒤 전파한다.
- `s.strip_prefix(p)` — 접두사가 글자 그대로 맞으면 `Some(나머지 &str)`, 아니면 `None`.
- `s.rsplitn(n, c)` — 오른쪽부터 최대 `n` 조각. 결과 차례도 오른쪽 조각부터다.
- `s.split(':')` — 모든 `:` 에서 자른다. 조각 수로 형식을 검사한다.
- `iter_a.zip(iter_b.cycle())` — 짧은 쪽을 되풀이해 짝을 맞춘다.
- `wrapping_mul` · `wrapping_add` — 넘침을 감아 돌리는 연산(패닉 없음).
- `format!("{:016x}", n)` — 16진수, 폭 16, 앞을 0으로 채움.
- `impl std::fmt::Display for AuthError` — `{}` 로 찍을 때의 사용자용 문장. `#[derive(Debug)]` 는 `{:?}` 용.
- 포맷 문자열 안의 글자 중괄호는 `{{` · `}}` 로 쓴다(원시 문자열이어도 같다).

원본이 말하는 모듈 배치:

```text
src/
└── auth/
    ├── mod.rs          // pub mod jwt; pub mod middleware;
    ├── jwt.rs          // Claims, JwtService
    └── middleware.rs   // AuthMiddleware
```

## 어디서 틀리나

### 1. 페이로드에 구분자 `:` 가 섞이면 진짜 토큰도 거부된다
`generate` 는 `user_id` · `role` 을 검사 없이 `:` 로 잇는다.
`user_id` 에 `:` 가 있으면 `split(':')` 이 5조각 이상이 되어, 서명은 맞는데도 `InvalidFormat` 이다.
반면 `.` 은 괜찮다 — `rsplitn` 이 마지막 `.` 만 쓰고, 서명에는 `.` 이 없다.

### 2. 만료 경계는 `>` 다
`now > exp` 일 때만 `Expired` 다.
`now == exp` 인 순간은 통과한다.
경계를 어느 쪽으로 둘지는 정하기 나름이지만, 테스트할 때 이 1초를 잊기 쉽다.

### 3. `Bearer ` 는 글자 그대로 맞아야 한다
`strip_prefix("Bearer ")` 는 대소문자와 공백 하나까지 맞춘다.
`"bearer x"` · `"Bearer  x"`(공백 둘은 떼어지지만 토큰이 `" x"` 가 됨) · `"Bearerx"` 는 모두 기대와 다르게 간다.
`"Bearer "` 뒤가 비면 토큰은 `""` 이고, `.` 이 없으니 `verify` 에서 `InvalidFormat` 이다.

### 4. 토큰에 민감 정보를 넣지 않는다
원본 팁: 비밀번호 같은 민감 정보를 넣지 않는다.
이 예제에서 보듯 페이로드는 평문으로 실린다 — 토큰을 본 누구나 읽는다.
서명은 「고쳤나」를 알려 줄 뿐 내용을 감추지 않는다.

### 5. `sign` 은 서명 흉내다
원본 주석대로 실제로는 HMAC-SHA256 을 쓴다.
이 해시는 암호학적 성질을 보장하지 않는다(원본에 근거 없음 — 추론).
특히 비밀키가 빈 문자열이면 `"".bytes().cycle()` 이 아무것도 내지 않아 `zip` 이 바로 끝나고, 모든 페이로드의 서명이 `0000000000000000` 이 된다 — 누구나 위조할 수 있다.

### 6. 발급과 검증의 비밀키가 다르면 전부 `InvalidSignature`
예제의 미들웨어는 `JwtService::new("my-secret-key-2026", 3600)` 를 새로 만든다.
같은 문자열이라 통한다.
비밀키를 설정에서 따로 읽다 어긋나면, 모든 요청이 「잘못된 서명」으로 실패한다.

### 7. `now_timestamp` 의 `unwrap`
시스템 시계가 1970년 이전이면 `duration_since(UNIX_EPOCH)` 가 `Err` 라 패닉한다.
또 `now + self.expiration_secs` 는 일반 `+` 라 아주 큰 만료 초를 주면 넘칠 수 있다.

### 8. 쓰지 않는 `use std::collections::HashMap`
정답 코드 주석은 「예시 데이터용」이라 하지만 코드 어디에서도 쓰지 않는다.
컴파일러가 쓰지 않는 import 경고를 낸다(확인 필요).

### 9. 「비밀키를 feature flag 로 환경별 분리」라는 원본 주장
원본의 주장 → feature flag 로 dev/prod 비밀키 설정을 나눌 수 있다.
왜 의심스러운가 → feature flag 는 컴파일 때 고르는 것이라, 비밀키 값을 바이너리에 굳히거나 환경마다 다시 빌드해야 한다.
비밀키 값 자체는 보통 실행 때 환경 변수나 설정 파일에서 읽는다(원본에 근거 없음 — 추론).
flag 로 나눌 만한 것은 「어디서 읽나」 같은 방식 쪽이다.

### 10. 긴 세션은 리프레시 토큰으로
원본 팁: 리프레시 토큰 패턴으로 긴 세션을 관리한다.
이 예제는 그 패턴을 구현하지 않는다 — 만료되면 `Expired` 로 끝난다.
`exp` 를 길게 잡아 세션을 늘리면 훔친 토큰도 오래 쓰인다.

### 11. 인증과 인가를 섞지 않는다
원본 팁: 미들웨어에서 인증과 인가를 분리한다.
`authorize` 는 이미 검증된 `Claims` 만 받는다 — 검증 안 된 토큰에서 역할을 읽어 판단하면 위조한 `role` 을 믿게 된다.

## 구현 세부사항 대 언어 보장

| 이 문서의 서술 | 누가 보장하나 |
|---|---|
| `rsplitn` 이 오른쪽 조각부터 돌려준다 | Rust 표준 라이브러리(문서화된 동작) |
| `strip_prefix` 가 글자 그대로 맞을 때만 `Some` | Rust 표준 라이브러리 |
| `wrapping_*` 는 넘쳐도 감아 돈다 | Rust 표준 라이브러리 |
| 일반 `+` 의 넘침은 디버그 빌드에서 패닉, 릴리스에서 감아 돎 | 컴파일 설정(빌드 프로필)에 달림 — 언어가 한 가지로 정하지 않음 (확인 필요) |
| `SystemTime` 은 뒤로 갈 수도 있는 벽시계다 | 표준 라이브러리 문서가 단조성을 보장하지 않는다고 적음 (확인 필요) |
| `{{` · `}}` 가 글자 중괄호로 찍힌다 | `format!` 계열 매크로 규칙(표준) |
| `exp` · `iat` · `sub` 가 표준 클레임이다 | JWT 규격(언어가 아님) |
| 실제 JWT 는 `Header.Payload.Signature`, HMAC-SHA256 | JWT 규격 · 고른 알고리즘 — 이 예제 코드는 흉내 |
| `encode` · `decode` · `Header::default()` · `Validation::default()` 의 꼴 | `jsonwebtoken` 크레이트 — 버전마다 다를 수 있음 (확인 필요) |
| `jsonwebtoken` 이 Rust 에서 가장 많이 쓰인다 | 원본의 주장 — 생태계 통계로 확인 필요 |
| 이 예제의 `sign` 결과 값 | 이 예제 코드만의 계산 — 아무 규격도 아님 |

## 언제 쓰고 언제 안 쓰나

| 상황 | 쓸 것 | 쓰지 말 것 |
|---|---|---|
| 여러 서버가 세션 저장소 없이 사용자를 확인 | 서명된 토큰(JWT) | 서버 메모리 세션만 |
| 실제 서비스의 서명 · 검증 | `jsonwebtoken` 크레이트 | 이 예제의 `sign` 같은 직접 만든 해시 |
| 토큰에 담을 정보 | 사용자 id · 역할 · 만료 | 비밀번호 · 개인정보 |
| 긴 로그인 유지 | 짧은 액세스 토큰 + 리프레시 토큰 | `exp` 를 아주 길게 |
| 요청 처리 경로 | 미들웨어에서 인증 → 인가 차례 | 핸들러마다 토큰 파싱을 복사 |
| 역할 판단 | 검증을 마친 `Claims` | 검증 전 토큰에서 읽은 값 |

## 핵심 문장

1. **토큰 = 평문 클레임 + 그에 묶인 서명** — 서명은 위조를 막지만 내용을 숨기지 않는다.
2. **검증 차례는 나누기 → 서명 → 파싱 → 만료** — 서명이 먼저라 엉터리 토큰은 대개 「잘못된 서명」에서 걸린다.
3. **`exp` 는 서명 안에 있다** — 고치면 서명이 어긋나므로 만료를 몰래 늘릴 수 없다.
4. **인증은 「누구인가」, 인가는 「해도 되나」** — 인증이 낸 `Claims` 를 인가가 받는다.
5. **실제로는 `jsonwebtoken` 과 HMAC** — 이 예제는 구조를 보이는 흉내다.

## 관련 자료

- `rest-api-axum` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- [middleware-tower](../09-middleware-tower/2-summary.md)
- `error-handling-app` — 같은 사이트의 관련 항목(이 폴더에 없어 링크를 걸지 않았다)
- 원본: study-site 항목 데이터 `data/rust/project-structures.json` 의 `auth-jwt`

## 용어 풀이

- **JWT** — JSON Web Token. `Header.Payload.Signature` 로 된 서명 토큰 꼴.
- **토큰** — 서버가 발급하고 클라이언트가 요청마다 들고 오는 증명 문자열.
- **클레임(claims)** — 토큰에 담긴 사용자에 대한 주장들.
- **`sub`** — subject, 토큰의 주체(여기선 user id).
- **`iat`** — issued at, 발급 시각.
- **`exp`** — expiration, 만료 시각.
- **서명(signature)** — 비밀키로 만든, 내용에 묶인 확인 값.
- **비밀키(secret)** — 서명을 만들고 검증하는 쪽만 아는 값.
- **HMAC-SHA256** — 비밀키와 SHA-256 해시로 만드는 메시지 인증 코드.
- **Bearer 토큰** — `Authorization: Bearer <토큰>` 꼴로 「가진 사람이 곧 주인」인 토큰.
- **인증(authentication)** — 상대가 누구인지 확인하기.
- **인가(authorization)** — 확인된 상대가 그 일을 해도 되는지 판단하기.
- **미들웨어** — 요청이 핸들러에 닿기 전에 공통 처리를 하는 층.
- **리프레시 토큰** — 만료된 액세스 토큰을 다시 받는 데 쓰는, 수명이 긴 토큰.
- **헥사고날 아키텍처** — 도메인을 포트(인터페이스)로, 바깥 기술을 어댑터로 나누는 구조.
- **Unix timestamp** — 1970-01-01 UTC 부터의 초.
- **라이프타임** — 참조가 유효한 범위에 붙인 이름.
- **`?` 연산자** — `Err`/`None` 이면 바로 돌려주고, 아니면 안의 값을 꺼낸다.

## 더 들어가면

- 실제 JWT 의 Header · Payload 는 JSON 을 base64url 로 인코딩한 것이다 — 암호화가 아니라 누구나 디코딩해 읽는다 (확인 필요).
- 서명 비교는 일정 시간 비교(constant-time)로 해야 시간 차로 서명을 맞혀 가는 공격을 막는다고 알려져 있다 — 이 예제의 `!=` 는 그렇지 않다 (확인 필요).
- `jsonwebtoken` 의 `Validation::default()` 는 기본으로 `exp` 를 검사하고, 시계 오차를 위한 여유(leeway)를 둔다 (확인 필요).
- 헤더의 `alg` 를 믿고 알고리즘을 고르면 `alg: none` 같은 공격이 생긴 역사가 있다 — 검증 쪽에서 허용 알고리즘을 정해 둔다 (확인 필요).
- HTTP 에서는 흔히 인증 실패를 401, 인가 거부를 403 으로 돌려준다 (확인 필요).
- JWT 는 발급 뒤 서버가 개별로 취소하기 어렵다 — 그래서 액세스 토큰을 짧게 두고 리프레시 토큰 쪽을 저장소에서 관리하는 설계가 쓰인다 (확인 필요).
