# rust/rust-testing-security/11 — 대칭 암호화 — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 23바이트 평문을 12바이트 nonce 로 암호화하면 (예측)

```rust
// 질문용 발췌
let plaintext = b"Hello, encrypted world!";
let nonce = generate_nonce();               // [u8; 12]
let encrypted = cipher.encrypt(plaintext, &nonce);
println!("암호문 길이: {} (nonce {} + 데이터 {})",
    encrypted.len(), nonce.len(), plaintext.len());
```

- 찍히는 길이 줄은 어떤 숫자들이 되나?
- `encrypted` 의 앞 12바이트는 무엇인가?

### 2. 다른 키로 복호화하면 (예측)

```rust
// 질문용 발췌
let wrong_cipher = SimpleCipher::new(b"wrong-key-wrong-key-wrong-key!!");
let wrong_result = wrong_cipher.decrypt(&encrypted, nonce.len()).unwrap();
println!("잘못된 키로: {:?} (깨진 데이터)", String::from_utf8_lossy(&wrong_result));
```

- 이 `unwrap()` 은 패닉하나, 아니면 값을 꺼내나?
- 꺼낸다면 그 바이트는 원래 평문과 어떤 관계인가?

### 3. 1ms 간격으로 만든 두 nonce 로 같은 평문을 암호화하면 (예측)

```rust
// 질문용 발췌
let nonce1 = generate_nonce();
std::thread::sleep(std::time::Duration::from_millis(1));
let nonce2 = generate_nonce();
let enc1 = cipher.encrypt(plaintext, &nonce1);
let enc2 = cipher.encrypt(plaintext, &nonce2);
println!("  enc1: {:02X?}...", &enc1[..8.min(enc1.len())]);
println!("  동일: {}", enc1 == enc2);
```

- `동일:` 뒤에는 무엇이 찍히나?
- `enc1[..8]` 로 찍힌 8바이트는 결과 벡터의 어느 부분인가?

### 4. 복호화가 암호화와 같은 XOR 연산으로 되는 까닭 (왜)

- `decrypt` 는 왜 새 알고리즘 없이 같은 키스트림을 한 번 더 XOR 하기만 하면 평문을 되찾나?

### 5. nonce 를 감추지 않고 암호문 앞에 붙여 보내는 까닭 (왜)

- nonce 를 드러내도 안전하고, 오히려 같이 보내야 하는 이유는 무엇인가?

### 6. 같은 키에서 nonce 를 두 번 쓰면 무엇이 새나 (경계)

- 같은 키 · 같은 nonce 로 두 평문을 암호화한 두 암호문을 가진 공격자는 키 없이 무엇을 알아낼 수 있나?

### 7. 시각 기반 `generate_nonce` 가 무너지는 경우 (경계)

- 이 함수가 같은 nonce 를 되풀이해 내놓을 수 있는 상황은 어떤 것들인가?

### 8. `to_bytes` 의 길이 헤더가 버티는 한계 (경계)

- `[nonce_len(1)][nonce][ciphertext]` 꼴에서 nonce 가 얼마나 길어지면 헤더가 틀리고, 그 까닭은 무엇인가?

### 9. 틀린 키에도 `Ok` 를 주는 장난감과 AES-GCM 의 차이 (연결)

- AES-GCM 이 「인증된 암호화(AEAD)」라는 점은 2번 문항의 결과를 어떻게 바꾸나?

### 10. 예제의 각 부품이 `aes-gcm` 에서는 무엇이 되나 (연결)

- `SimpleCipher::new` · `generate_nonce` · `encrypt` · `decrypt` 는 원본이 보여 준 `aes-gcm` 코드의 어느 호출에 대응하나?

## 실습

### 실습 1. XOR 장난감 암호로 대칭 암호화의 흐름 만들기

**만들 것** — 키와 nonce 로 키스트림을 만들어 XOR 로 암호화 · 복호화하고, nonce 의 효과와 메시지 직렬화까지 보이는 프로그램.
안전한 암호가 아니라 AES-GCM 사용 흐름을 흉내 내는 교육용이다.

**준비물** — Rust 표준 라이브러리만 쓴다. `aes-gcm` 크레이트는 흉내만 내고 실제로 가져오지 않는다(사용법을 글자로 찍기만 한다).

**요구 조건**

1단계 — 암호화기
1. `SimpleCipher` 는 키 바이트(`Vec<u8>`)를 담는다. `new` 는 빈 키를 `assert!` 로 거부한다.
2. `derive_keystream(nonce, len)` 은 상태를 0 에서 시작해 nonce 바이트를 `×31 + b`, 키 바이트를 `×37 + b` 로 섞은 뒤, `len` 번 `×6364136223846793005 + 1` 을 되풀이하며 `(state >> 33) as u8` 를 하나씩 모은다. 곱셈 · 덧셈은 넘쳐도 감아 돈다.
3. `encrypt(plaintext, nonce)` 는 평문과 키스트림을 바이트마다 XOR 하고, 결과 앞에 nonce 를 붙인 벡터를 돌려준다.
4. `decrypt(data, nonce_len)` 은 데이터가 `nonce_len` 보다 짧으면 `Err` 를 돌려주고, 아니면 앞을 nonce · 뒤를 암호문으로 나눠 같은 키스트림으로 XOR 해 `Ok(평문)` 을 돌려준다.

2단계 — nonce
5. `generate_nonce()` 는 `UNIX_EPOCH` 부터의 나노초(실패하면 0)를 읽어, 낮은 바이트부터 8비트씩 12칸에 펼친 `[u8; 12]` 를 돌려준다.

3단계 — 직렬화
6. `EncryptedMessage { nonce, ciphertext }` 는 `Debug` 를 파생한다.
7. `to_bytes` 는 `[nonce 길이 1바이트][nonce][ciphertext]` 를 만든다.
8. `from_bytes` 는 빈 입력이면 `Err("빈 데이터")`, 첫 바이트가 가리킨 만큼 데이터가 없으면 `Err("데이터 부족")`, 아니면 구조체를 돌려준다.

4단계 — `main` 시연
9. 「기본 암호화/복호화」: 키로 암호화기를 만들고, 평문을 새 nonce 로 암호화해 평문 · 암호문 앞 20바이트(hex) · 길이 구성(전체 · nonce · 데이터)을 찍는다. 복호화한 값을 찍고 `assert_eq!` 로 평문과 같은지 확인한다.
10. 「잘못된 키」: 다른 키의 암호화기로 같은 암호문을 복호화해 `from_utf8_lossy` 로 찍는다.
11. 「Nonce 중요성」: nonce 두 개를 1ms 간격으로 만들어 같은 평문을 각각 암호화하고, 두 결과의 앞 8바이트(hex)와 두 벡터가 같은지를 찍는다.
12. 「메시지 직렬화」: 처음 암호문에서 nonce 를 떼어 `EncryptedMessage` 를 만들고, `to_bytes` → `from_bytes` 왕복 뒤 nonce 길이와 암호문 길이를 찍는다.
13. 마지막에 미리 채워 둔 `aes-gcm` 사용법 줄과 핵심 규칙 네 줄을 찍는다.

**시작 코드**

```rust
struct SimpleCipher {
    key: Vec<u8>,
}

impl SimpleCipher {
    fn new(key: &[u8]) -> Self {
        // TODO: 빈 키를 거부하고 키를 복사해 담는다
        todo!()
    }

    fn encrypt(&self, plaintext: &[u8], nonce: &[u8]) -> Vec<u8> {
        // TODO: 키스트림을 만들고 XOR 한 뒤, nonce 를 앞에 붙여 돌려준다
        todo!()
    }

    fn decrypt(&self, data: &[u8], nonce_len: usize) -> Result<Vec<u8>, String> {
        // TODO: 길이 검사 → nonce / 암호문 분리 → 같은 키스트림으로 XOR
        todo!()
    }

    fn derive_keystream(&self, nonce: &[u8], len: usize) -> Vec<u8> {
        let mut stream = Vec::with_capacity(len);
        let mut state: u64 = 0;
        // TODO: nonce(×31), key(×37) 를 섞어 시작 상태를 만든다
        // TODO: len 번 LCG 를 돌려 (state >> 33) as u8 를 모은다
        stream
    }
}

fn generate_nonce() -> [u8; 12] {
    // TODO: 나노초 시각을 읽어 12바이트로 펼친다
    todo!()
}

// TODO: Debug 를 파생한다
struct EncryptedMessage {
    nonce: Vec<u8>,
    ciphertext: Vec<u8>,
}

impl EncryptedMessage {
    fn to_bytes(&self) -> Vec<u8> {
        // TODO: [nonce 길이][nonce][ciphertext]
        todo!()
    }

    fn from_bytes(data: &[u8]) -> Result<Self, String> {
        // TODO: 빈 데이터 · 데이터 부족 검사 후 나눠 담는다
        todo!()
    }
}

fn main() {
    println!("=== 기본 암호화/복호화 ===");
    let key = b"my-secret-key-32bytes-padding!!";
    let plaintext = b"Hello, encrypted world!";
    // TODO: 암호화기 · nonce · 암호화 · 찍기 · 복호화 · assert_eq!

    println!("\n=== 잘못된 키 ===");
    // TODO: b"wrong-key-wrong-key-wrong-key!!" 로 복호화해 찍는다

    println!("\n=== Nonce 중요성 ===");
    // TODO: nonce 두 개(1ms 간격) → 암호화 두 번 → 앞 8바이트 · 동일 여부

    println!("\n=== 메시지 직렬화 ===");
    // TODO: EncryptedMessage 왕복 후 nonce_len · ct_len 을 찍는다

    println!("\n=== 실제 aes-gcm 코드 ===");
    println!("// Cargo.toml: aes-gcm = \"0.10\"");
    println!("// use aes_gcm::{{Aes256Gcm, Key, Nonce, aead::{{Aead, KeyInit}}}};");
    println!("// use aes_gcm::aead::OsRng;");
    println!("// ");
    println!("// 키 생성:");
    println!("// let key = Aes256Gcm::generate_key(&mut OsRng);");
    println!("// let cipher = Aes256Gcm::new(&key);");
    println!("// ");
    println!("// 암호화:");
    println!("// let nonce = Aes256Gcm::generate_nonce(&mut OsRng);");
    println!("// let ciphertext = cipher.encrypt(&nonce, plaintext.as_ref())?;");
    println!("// ");
    println!("// 복호화:");
    println!("// let plaintext = cipher.decrypt(&nonce, ciphertext.as_ref())?;");

    println!("\n=== 암호화 핵심 규칙 ===");
    println!("1. Nonce는 절대 재사용하지 않는다 (같은 키에서)");
    println!("2. 인증된 암호화(AES-GCM) 사용 -> 변조 감지");
    println!("3. 키를 코드에 하드코딩하지 않는다");
    println!("4. 자체 암호화 구현 금지 -> 검증된 라이브러리 사용");
}
```

**확인 방법** — `rustc encryption.rs && ./encryption` (또는 `cargo run`)으로 돌린다.
`assert_eq!` 에서 패닉하지 않고 끝까지 가는지, 복호문이 평문과 같은지, 잘못된 키 줄이 깨진 글자인지, 「동일:」 이 `false` 인지, 직렬화 줄이 `nonce_len=12, ct_len=23` 인지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
