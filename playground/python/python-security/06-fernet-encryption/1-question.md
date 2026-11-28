# python/python-security/06 — Fernet (대칭 암호화) — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 같은 평문을 두 번 암호화하면 (예측)

```python
# 질문용 발췌
f = Fernet(Fernet.generate_key())
a = f.encrypt(b"hello")
b = f.encrypt(b"hello")
print(a == b)
print(f.decrypt(a) == f.decrypt(b))
```

- 두 `print` 는 각각 무엇을 찍는가?

### 2. 다른 키로 만든 Fernet 으로 복호화하면 (예측)

```python
# 질문용 발췌
token = Fernet(Fernet.generate_key()).encrypt(b"secret")
try:
    Fernet(Fernet.generate_key()).decrypt(token)
except Exception as e:
    print(type(e).__name__)
```

- 이 코드는 무엇을 찍는가?

### 3. MultiFernet 의 키 순서를 거꾸로 두면 (예측)

```python
# 질문용 발췌
old_key, new_key = Fernet.generate_key(), Fernet.generate_key()
old_token = Fernet(old_key).encrypt(b"data")
multi = MultiFernet([Fernet(old_key), Fernet(new_key)])
rotated = multi.rotate(old_token)
Fernet(new_key).decrypt(rotated)
```

- 마지막 줄은 성공하는가, 실패하는가?

### 4. 잘못된 키와 변조된 토큰이 같은 예외로 끝나는 까닭 (왜)

- `decrypt` 가 키 오류와 변조를 한 가지 예외로 거부하게 되는 까닭은 무엇인가?

### 5. 키를 소스 코드에 적어 두지 않는 까닭 (왜)

- 키를 하드코딩하면 암호화한 데이터에 무슨 일이 생기는가?

### 6. TTL 을 거는 자리 (경계)

- 유효 시간은 `encrypt` 와 `decrypt` 중 어디에서 지정하며, 무엇을 기준으로 재는가?

### 7. 예제의 `SecureConfig` 를 그대로 다음 실행에서 쓰면 (경계)

- 예제처럼 실행마다 `generate_key()` 로 키를 만들면, 지난 실행에서 저장한 암호화 설정을 풀 수 있는가?

### 8. 설정 딕셔너리를 JSON 으로 바꾸는 까닭 (연결)

- `SecureConfig` 가 `json.dumps` 와 `encode` 를 거친 뒤에야 `encrypt` 를 부르는 것은 Fernet 의 어떤 성질 때문인가?

### 9. 무중단 키 교체와 `rotate` (연결)

- 옛 키를 언제 안전하게 버릴 수 있으며, 그 전까지 `MultiFernet` 이 서비스를 멈추지 않게 해 주는 까닭은 무엇인가?

## 실습

### 실습 1. Fernet 으로 암호화 · TTL · 키 로테이션 · 설정 암호화를 한 파일에 구현하기

**만들 것** — 키 생성부터 설정 딕셔너리 암호화까지, Fernet 의 주요 기능을 차례로 보여 주는 스크립트를 만든다.

**준비물** — `cryptography` 패키지가 필요하다(`pip install cryptography`).

**요구 조건**

1. 1단계 — `Fernet.generate_key()` 로 키를 만들고, 키와 키의 길이(`len`)를 출력한다.
2. 2단계 — 그 키로 `Fernet` 인스턴스를 만들고, 한글 문자열을 UTF-8 바이트로 바꿔 암호화한다. 평문 · 암호문 앞 50바이트 · 암호문 길이를 출력한다.
3. 2단계(이어서) — 암호문을 복호화해 문자열로 되돌리고, 원래 평문과 같은지(`True`/`False`)를 출력한다.
4. 3단계 — 새로 만든 다른 키의 `Fernet` 으로 같은 암호문을 복호화해 보고, 예외가 나면 예외 클래스 이름을 출력한다.
5. 4단계 — 같은 키로 만든 두 번째 인스턴스로 토큰을 만들고, `ttl=10` 으로 바로 복호화해 결과를 출력한다.
6. 4단계(이어서) — 1초 기다린 뒤 `ttl=0` 으로 복호화해 보고, 예외가 나면 예외 클래스 이름을 출력한다.
7. 5단계 — 옛 키 · 새 키를 만들고 옛 키로 데이터를 암호화한다. `[새 키, 옛 키]` 순서의 `MultiFernet` 으로 그 데이터를 복호화해 출력한다.
8. 5단계(이어서) — `MultiFernet.rotate` 로 옛 토큰을 다시 암호화하고, 새 키 하나만 가진 `Fernet` 으로 그 결과를 복호화해 출력한다.
9. 6단계 — 키를 받아 `Fernet` 을 묶어 두는 `SecureConfig` 클래스를 만든다. `encrypt_config(dict)` 는 JSON 직렬화 → UTF-8 바이트 → 암호화를, `decrypt_config(token)` 은 그 반대를 한다.
10. 6단계(이어서) — 민감 정보 세 항목이 든 딕셔너리를 암호화해 앞 40바이트를 출력하고, 복원한 딕셔너리를 출력한다.
11. 7단계 — Fernet 내부 구조(알고리즘 · 키 분할 · 토큰 구성 · 제공하는 성질)를 설명하는 네 줄을 출력한다.

**시작 코드**

```python
from cryptography.fernet import Fernet, MultiFernet
import base64
import os
import json
import time

# === 키 생성 ===
print("=== Fernet 키 생성 ===")
key = None  # TODO: 새 키 만들기
print(f"키: {key}")
print(f"키 길이: {len(key)} bytes (Base64 인코딩된 256비트)")
print()

# === 기본 암호화/복호화 ===
print("=== 암호화/복호화 ===")
f = None  # TODO: 키를 묶은 Fernet 인스턴스

plaintext = "민감한 데이터: 비밀번호, API 키 등"
encrypted = None  # TODO: plaintext 를 바이트로 바꿔 암호화
print(f"평문:     {plaintext}")
print(f"암호문:   {encrypted[:50]}...")
print(f"암호문 길이: {len(encrypted)} bytes")

decrypted = None  # TODO: 복호화
print(f"복호화:   {decrypted.decode('utf-8')}")
print(f"일치:     {decrypted.decode('utf-8') == plaintext}")
print()

# === 잘못된 키로 복호화 시도 ===
print("=== 잘못된 키 ===")
# TODO: 다른 키로 Fernet 을 만들고 encrypted 복호화를 시도한다
try:
    pass
except Exception as e:
    print(f"복호화 실패: {type(e).__name__}")
    print("  → 잘못된 키 또는 변조된 데이터")
print()

# === TTL (시간 제한) ===
print("=== TTL (시간 제한) ===")
f2 = Fernet(key)
token = f2.encrypt(b"time-limited data")

result = None  # TODO: 10초 TTL 로 복호화
print(f"TTL 내 복호화: {result}")

print("TTL=0으로 테스트:")
time.sleep(1)
try:
    pass  # TODO: TTL 0 으로 복호화
except Exception as e:
    print(f"  TTL 만료: {type(e).__name__}")
print()

# === 키 로테이션 (MultiFernet) ===
print("=== 키 로테이션 ===")
old_key = Fernet.generate_key()
new_key = Fernet.generate_key()

old_fernet = Fernet(old_key)
old_encrypted = old_fernet.encrypt(b"old data encrypted")

multi = None  # TODO: 새 키로 암호화하고 두 키로 복호화를 시도하는 MultiFernet

decrypted = None  # TODO: old_encrypted 복호화
print(f"기존 데이터 복호화: {decrypted}")

rotated = None  # TODO: old_encrypted 를 새 키로 다시 암호화
print(f"로테이션 후: 새 키로 재암호화됨")

new_only = Fernet(new_key)
result = None  # TODO: 새 키만으로 rotated 복호화
print(f"새 키로 복호화: {result}")
print()

# === 실무 패턴: 설정 파일 암호화 ===
print("=== 설정 파일 암호화 ===")

class SecureConfig:
    def __init__(self, key):
        pass  # TODO: Fernet 묶어 두기

    def encrypt_config(self, config_dict):
        """딕셔너리를 암호화된 문자열로"""
        pass  # TODO: JSON → bytes → 암호화

    def decrypt_config(self, encrypted_data):
        """암호화된 데이터를 딕셔너리로"""
        pass  # TODO: 복호화 → str → JSON 역직렬화

config_key = Fernet.generate_key()
sc = SecureConfig(config_key)

sensitive_config = {
    "database_url": "postgresql://user:pass@host/db",
    "api_secret": "sk-1234567890abcdef",
    "redis_password": "r3d!s_p@ss"
}

encrypted_config = sc.encrypt_config(sensitive_config)
print(f"암호화된 설정: {encrypted_config[:40]}...")

restored = sc.decrypt_config(encrypted_config)
print(f"복원된 설정: {restored}")
print()

print("--- Fernet 내부 구조 ---")
# TODO: 알고리즘 · 키 분할 · 토큰 구성 · 제공하는 성질을 네 줄로 출력
```

**확인 방법** — `python fernet-encryption.py` 로 돌려, 복호화 결과가 원래 평문과 일치하고(`일치: True`), 잘못된 키 · TTL 0 에서 예외 이름이 찍히며, 새 키만으로 로테이션된 데이터가 풀리고, 복원된 설정이 원래 딕셔너리와 같은지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
