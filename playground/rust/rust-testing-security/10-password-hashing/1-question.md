# rust/rust-testing-security/10 — 비밀번호 해싱 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 반복 1000 인 해셔가 만든 저장 문자열의 길이 (예측)

```rust
// 질문용 발췌
let hasher = PasswordHasher::new(1000);
let hashed = hasher.hash_password("MySecureP@ssw0rd");
println!("길이: {} 문자", hashed.len());
```

- 이 줄은 몇 문자라고 찍나?

### 2. 같은 비밀번호를 두 번 해싱한 뒤 (예측)

```rust
// 질문용 발췌
let hashed = hasher.hash_password(password);
let hashed2 = hasher.hash_password(password);
println!("  동일: {}", hashed == hashed2);
println!("올바른 비밀번호: {}", hasher.verify_password(password, &hashed));
println!("틀린 비밀번호:   {}", hasher.verify_password("wrong", &hashed));
println!("올바른(해시2):   {}", hasher.verify_password(password, &hashed2));
```

- 네 줄에 찍히는 `true` / `false` 는 각각 무엇인가?

### 3. 반복 횟수가 다른 해셔로 검증하면 (예측)

```rust
// 질문용 발췌
let stored = PasswordHasher::new(1000).hash_password("pw");
let other = PasswordHasher::new(10);
println!("{}", other.verify_password("pw", &stored));
```

- 마지막 줄은 무엇을 찍나?

### 4. 솔트를 저장 문자열에 그대로 적어 두는 까닭 (왜)

- 솔트를 숨기지 않고 해시 옆에 hex 로 저장해도 되는 까닭은 무엇인가?

### 5. 빠른 해시가 비밀번호에 나쁜 까닭 (왜)

- SHA 처럼 빠른 해시가 비밀번호 저장에서 약점이 되는 까닭은 무엇이고, 반복 라운드는 그 약점을 어떻게 메우나?

### 6. 곱하는 값에 `| 1` 을 붙인 까닭 (왜)

- 라운드 식에서 `hash[(i + 7) % 32] | 1` 처럼 1 을 OR 하는 까닭은 무엇인가?

### 7. 비교를 `==` 대신 XOR · OR 누적으로 하는 까닭 (왜)

- `constant_time_compare` 가 끝까지 다 돈 뒤에야 답을 내는 까닭은 무엇인가?

### 8. 솔트 부분이 망가진 저장 문자열 (경계)

- 솔트 hex 가 32글자보다 짧은 저장 문자열을 넣으면 `verify_password` 는 어떻게 되고, hex 가 아닌 영문자가 섞이면 어떻게 되나?

### 9. 시각으로 만든 솔트의 한계 (경계)

- `generate_salt` 의 시각 기반 솔트는 원본이 말하는 「랜덤 솔트」 요구를 어디까지 채우고 어디서 모자라나?

### 10. 시뮬레이션과 `argon2` 크레이트의 대응 (연결)

- 시뮬레이션의 `generate_salt` · `hash_password` · 문자열 분해 · `verify_password` 는 `argon2` 크레이트의 어느 호출에 각각 대응하나?

## 실습

### 실습 1. 솔트 · 반복 · 상수 시간 비교를 갖춘 비밀번호 해싱 시뮬레이션 만들기

**만들 것** — 표준 라이브러리만으로 비밀번호를 솔트와 함께 반복 해싱해 `$반복$솔트$해시` 문자열로 저장하고, 그 문자열로 비밀번호를 검증하는 교육용 프로그램을 만든다.
마지막에 실제 알고리즘 목록 · `argon2` 사용법 · 보안 체크리스트를 화면에 찍는다.

**준비물** — 외부 크레이트는 필요 없다(std 만). `argon2` 크레이트는 흉내 낸 것이며, 그 코드는 실행하지 않고 문자열로만 찍는다.

**요구 조건**

1단계 — 해셔 구조체
1. `PasswordHasher` 구조체가 반복 횟수 `iterations: u32` 를 갖고, `new(iterations)` 로 만든다.

2단계 — 솔트
2. `generate_salt` 는 현재 시각을 유닉스 기원 이후 나노초로 얻고(실패하면 기본값), 그 값을 8비트씩 밀어 16바이트 배열 `[u8; 16]` 에 채워 돌려준다.

3단계 — 해싱
3. `hash_with_salt(password, salt)` 는 비밀번호 바이트 뒤에 솔트를 이어 붙이고, 그 바이트를 32칸 배열에 `i % 32` 자리로 XOR 해 초기 상태를 만든다.
4. 이어서 `iterations` 라운드 동안, 각 칸을 「(자기 + 다음 칸) × (7칸 뒤 칸 | 1) + 라운드 번호의 아래 8비트」로 새 배열에 계산해 바꿔 끼운다. 모든 덧셈 · 곱셈은 넘쳐도 감싸 돌게 한다.
5. 결과 `[u8; 32]` 를 돌려준다.

4단계 — 저장 문자열
6. `hash_password(password)` 는 새 솔트를 만들어 해싱하고, 솔트와 해시를 두 자리 소문자 hex 로 바꿔 `$반복횟수$솔트hex$해시hex` 문자열을 돌려준다.

5단계 — 검증
7. `verify_password(password, stored)` 는 `$` 로 나눈 조각이 4개가 아니거나 반복 횟수를 숫자로 읽지 못하면 `false` 를 돌려준다.
8. 솔트 hex 를 두 글자씩 바이트로 되돌리고(읽지 못하면 0), **저장 문자열의 반복 횟수**로 새 해셔를 만들어 입력을 다시 해싱한다.
9. 다시 계산한 해시 hex 와 저장된 해시 hex 를 상수 시간 비교 함수로 견준 결과를 돌려준다.

6단계 — 상수 시간 비교
10. 자유 함수 `constant_time_compare(a, b)` 는 길이가 다르면 `false`, 같으면 모든 바이트 쌍의 XOR 을 OR 로 누적해 0 인지로 답한다.

7단계 — `main` 시연
11. 반복 1000 해셔로 `"MySecureP@ssw0rd"` 를 해싱해 비밀번호 · 해시 · 문자열 길이를 찍는다.
12. 같은 비밀번호를 한 번 더 해싱해 두 해시와 둘이 같은지를 찍는다.
13. 올바른 비밀번호(첫 해시) · `"wrong"`(첫 해시) · 올바른 비밀번호(둘째 해시)의 검증 결과를 찍는다.
14. SHA 를 쓰면 안 되는 이유 · 올바른 알고리즘 목록 · `argon2` 코드 · 보안 체크리스트를 절 제목과 함께 찍는다.

**시작 코드**

```rust
// 교육용 시뮬레이션 — 실제로 쓰면 안 된다

struct PasswordHasher {
    // TODO: 반복 횟수 필드
}

impl PasswordHasher {
    fn new(iterations: u32) -> Self {
        // TODO
        todo!()
    }

    fn generate_salt(&self) -> [u8; 16] {
        let now = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap_or_default()
            .as_nanos();
        let mut salt = [0u8; 16];
        // TODO: now 를 8비트씩 밀어 각 칸에 채운다
        salt
    }

    fn hash_with_salt(&self, password: &str, salt: &[u8; 16]) -> [u8; 32] {
        let mut hash = [0u8; 32];
        // TODO: password 바이트 + salt 를 이어 붙여 hash[i % 32] 에 XOR
        // TODO: self.iterations 라운드 동안 wrapping 연산으로 섞기
        hash
    }

    fn hash_password(&self, password: &str) -> String {
        // TODO: 솔트 생성 → 해싱 → hex 변환 → "$반복$솔트$해시"
        todo!()
    }

    fn verify_password(&self, password: &str, stored: &str) -> bool {
        // TODO: split('$') → 조각 4개 확인 → 반복 횟수 파싱
        // TODO: 솔트 hex → 16바이트
        // TODO: 저장된 반복 횟수로 다시 해싱 → hex → 상수 시간 비교
        todo!()
    }
}

fn constant_time_compare(a: &str, b: &str) -> bool {
    // TODO: 길이 검사 후 XOR 을 OR 로 누적
    todo!()
}

fn main() {
    let hasher = PasswordHasher::new(1000);

    println!("=== 비밀번호 해싱 ===");
    let password = "MySecureP@ssw0rd";
    // TODO: 해싱하고 비밀번호 · 해시 · 길이를 찍는다

    // TODO: 한 번 더 해싱해 두 해시와 동일 여부를 찍는다

    println!("\n=== 비밀번호 검증 ===");
    // TODO: 올바른 비밀번호 / "wrong" / 해시2 로 검증 결과를 찍는다

    println!("\n=== 비밀번호에 SHA를 쓰면 안 되는 이유 ===");
    println!("1. SHA는 빠르다 -> 브루트포스 공격에 취약");
    println!("   GPU로 초당 수십억 개 해시 가능");
    println!("2. 솔트 없으면 레인보우 테이블 공격 가능");
    println!("3. 비밀번호 해싱 전용 알고리즘은 의도적으로 느림");

    println!("\n=== 올바른 비밀번호 해싱 알고리즘 ===");
    println!("1. Argon2id (권장) - 메모리 하드, 2015 PHC 우승");
    println!("2. bcrypt          - 오래되었지만 여전히 안전");
    println!("3. scrypt          - 메모리 하드");
    println!("4. PBKDF2          - 가장 오래된 표준, 반복 기반");

    // TODO: "=== 실제 argon2 코드 ===" 절 — Cargo.toml 줄, use 줄, 해싱 · 검증 코드를 문자열로 찍는다
    // TODO: "=== 비밀번호 보안 체크리스트 ===" 절 — [필수] 3개, [권장] 1개, [금지] 3개
}
```

**확인 방법** — `rustc password-hashing.rs && ./password-hashing` 로 돌려, 두 해시가 서로 다르고 검증 결과가 올바른 비밀번호에만 `true` 인지, 해시 문자열 길이가 형식에서 계산한 값과 맞는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
