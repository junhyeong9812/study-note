# python/python-security/07 — RSA (비대칭 암호화) — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 같은 메시지를 두 번 암호화하면 (예측)

```python
# 질문용 발췌
oaep = padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(), label=None)
c1 = public_key.encrypt("비밀 메시지입니다.".encode('utf-8'), oaep)
c2 = public_key.encrypt("비밀 메시지입니다.".encode('utf-8'), oaep)
print(c1 == c2)
print(private_key.decrypt(c1, oaep) == private_key.decrypt(c2, oaep))
```

- 두 `print` 는 각각 무엇을 찍는가?

### 2. 2048비트 키로 만든 암호문과 서명의 길이 (예측)

```python
# 질문용 발췌
private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
ciphertext = private_key.public_key().encrypt(b"hi", oaep)
signature = private_key.sign(b"a much longer document " * 3, pss, hashes.SHA256())
print(len(ciphertext), len(signature))
```

- 찍히는 두 수는 무엇인가?

### 3. 다른 데이터로 서명을 검증하면 (예측)

```python
# 질문용 발췌
signature = private_key.sign(data, pss, hashes.SHA256())
try:
    public_key.verify(signature, b"tampered data", pss, hashes.SHA256())
    print("변조 데이터: 유효함")
except Exception:
    print("변조 데이터: 서명 무효! (변조 감지)")
```

- 어느 줄이 찍히고, 그 사이 `verify` 안에서는 무슨 일이 일어나는가?

### 4. 암호화는 공개키로, 서명은 개인키로 하는 까닭 (왜)

- 왜 두 쓰임에서 키의 순서가 서로 뒤집히는가?

### 5. 복호화에 암호화와 같은 OAEP 설정을 넘겨야 하는 까닭 (왜)

- 왜 `decrypt` 에 패딩 설정을 다시 넘기고, 그 설정이 암호화 때와 같아야 하는가?

### 6. 비밀번호로 잠근 PEM 을 다시 열 때 (경계)

- `BestAvailableEncryption` 으로 저장한 개인키 PEM 은 어떤 경우에 열리고 어떤 경우에 열리지 않는가?

### 7. 큰 파일을 RSA 로 곧바로 암호화하려 하면 (경계)

- RSA 하나로 큰 데이터를 암호화하려는 시도는 어떤 두 가지 이유로 막히는가?

### 8. RSA 와 AES 를 묶는 하이브리드 암호화 (연결)

- 하이브리드 암호화에서 RSA 와 AES 는 각각 무엇을 맡고, 받는 쪽은 어떤 순서로 푸는가?

### 9. 서명과 해시 함수의 관계 (연결)

- `sign` 에 넘기는 `hashes.SHA256()` 은 서명 과정에서 무슨 일을 하고, 그것이 변조 감지와 어떻게 이어지는가?

## 실습

### 실습 1. RSA 키 쌍으로 저장 · 로드 · 암호화 · 서명을 한 파일에 해 보기

**만들 것** — RSA 키 쌍을 만들고, PEM 으로 저장했다가 불러오고, 공개키 암호화 · 개인키 복호화와 개인키 서명 · 공개키 검증(변조 감지 포함)을 차례로 해 보는 스크립트.

**준비물** — `cryptography` 패키지가 필요하다(`pip install cryptography`).

**요구 조건**

1단계 — 키 생성
1. `rsa.generate_private_key` 로 공개 지수 65537, 2048비트 개인키를 만든다.
2. 개인키에서 공개키를 꺼낸다.
3. 개인키의 키 크기를 찍는다.

2단계 — PEM 직렬화
4. 개인키를 PEM · PKCS8 · 암호화 없음으로 직렬화하고 앞 80바이트를 찍는다.
5. 개인키를 PEM · PKCS8 · `BestAvailableEncryption(b"my-password")` 로 직렬화하고 앞 80바이트를 찍는다.
6. 공개키를 PEM · `SubjectPublicKeyInfo` 로 직렬화하고 앞 80바이트를 찍는다.

3단계 — PEM 로드
7. 평문 개인키 PEM 을 `password=None` 으로, 공개키 PEM 을 공개키 로더로 불러와 각각 키 크기를 찍는다.
8. 잠긴 개인키 PEM 을 `b"my-password"` 로 불러와 키 크기를 찍는다.

4단계 — 암호화 / 복호화
9. 문자열 「비밀 메시지입니다.」를 UTF-8 바이트로 바꿔 공개키와 OAEP(MGF1-SHA256, SHA256, label 없음)로 암호화한다.
10. 암호문 길이와 Base64 로 바꾼 암호문의 앞 40자를 찍는다.
11. 개인키와 같은 OAEP 설정으로 복호화해 문자열로 되돌려 찍는다.

5단계 — 서명 / 검증
12. 문자열 「이 문서는 변조되지 않았습니다.」의 UTF-8 바이트를 개인키와 PSS(MGF1-SHA256, 최대 솔트 길이), SHA256 으로 서명한다.
13. 서명 길이와 Base64 로 바꾼 서명의 앞 40자를 찍는다.
14. 원래 데이터로 공개키 검증을 하고, 성공하면 「유효함」, 예외면 「무효」를 찍는다.
15. 같은 서명을 `b"tampered data"` 로 검증해, 예외가 나면 변조 감지 문구를 찍는다.

6단계 — 요약
16. RSA 핵심 개념 · 패딩 방식 · 키 크기 요약 문구를 찍는다(시작 코드에 이미 있다).

**시작 코드**

```python
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.utils import Prehashed
import base64

# === RSA 키 생성 ===
print("=== RSA 키 생성 ===")
private_key = None  # TODO: 공개 지수 65537, 2048비트 개인키 생성
public_key = None   # TODO: 개인키에서 공개키 꺼내기

print(f"키 크기: {private_key.key_size}비트")
print()

# === 키를 PEM 형식으로 직렬화 ===
print("=== PEM 직렬화 ===")

private_pem = None    # TODO: PEM, PKCS8, 암호화 없음
print(f"개인키 PEM:\n{private_pem[:80].decode()}...")

encrypted_pem = None  # TODO: PEM, PKCS8, BestAvailableEncryption(b"my-password")
print(f"\n암호화된 개인키:\n{encrypted_pem[:80].decode()}...")

public_pem = None     # TODO: PEM, SubjectPublicKeyInfo
print(f"\n공개키 PEM:\n{public_pem[:80].decode()}...")
print()

# === PEM에서 키 로드 ===
print("=== PEM 로드 ===")
loaded_private = None  # TODO: 평문 개인키 PEM 로드 (password=None)
loaded_public = None   # TODO: 공개키 PEM 로드
print(f"개인키 로드 성공: {loaded_private.key_size}비트")
print(f"공개키 로드 성공: {loaded_public.key_size}비트")

loaded_encrypted = None  # TODO: 잠긴 PEM 을 b"my-password" 로 로드
print(f"암호화 키 로드: {loaded_encrypted.key_size}비트")
print()

# === 공개키 암호화 / 개인키 복호화 ===
print("=== 암호화/복호화 ===")
message = "비밀 메시지입니다."

ciphertext = None  # TODO: 공개키 + OAEP(MGF1-SHA256, SHA256, label=None) 로 암호화
print(f"암호문 길이: {len(ciphertext)} bytes")
print(f"암호문 (Base64): {base64.b64encode(ciphertext)[:40]}...")

plaintext = None   # TODO: 개인키 + 같은 OAEP 로 복호화
print(f"복호화: {plaintext.decode('utf-8')}")
print()

# === 디지털 서명 / 검증 ===
print("=== 디지털 서명 ===")
data = "이 문서는 변조되지 않았습니다.".encode('utf-8')

signature = None   # TODO: 개인키 + PSS(MGF1-SHA256, MAX_LENGTH) + SHA256 으로 서명
print(f"서명 길이: {len(signature)} bytes")
print(f"서명 (Base64): {base64.b64encode(signature)[:40]}...")

# TODO: 원래 data 로 검증 → 성공 "서명 검증: 유효함 ✓" / 예외 "서명 검증: 무효!"

# TODO: b"tampered data" 로 검증 → 성공 "변조 데이터: 유효함" / 예외 "변조 데이터: 서명 무효! (변조 감지)"
print()

print("--- RSA 핵심 개념 ---")
print("공개키 암호화 → 개인키 복호화: 기밀성 (누구나 암호화, 소유자만 복호화)")
print("개인키 서명 → 공개키 검증:   인증+무결성 (소유자만 서명, 누구나 검증)")
print("")
print("--- 패딩 방식 ---")
print("OAEP:  암호화용 (PKCS1v15보다 안전)")
print("PSS:   서명용 (PKCS1v15보다 안전)")
print("")
print("--- 키 크기 ---")
print("2048비트: 현재 최소 권장")
print("4096비트: 장기 보안 권장")
print("RSA는 큰 데이터에 느림 → 하이브리드 암호화 사용")
print("  (RSA로 AES 키를 암호화, AES로 데이터 암호화)")
```

**확인 방법** — `python rsa-encryption.py` 로 돌려, 키 크기 2048 이 세 번의 로드에서도 그대로 나오는지, 복호화 줄이 원래 메시지와 같은지, 원래 데이터 검증은 유효 · 변조 데이터 검증은 변조 감지 문구가 찍히는지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
