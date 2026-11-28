# python/python-security/07 — RSA (비대칭 암호화) — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 암호문은 서로 다르고, 복호화한 평문은 같다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
첫 `print` 는 `False`, 둘째 `print` 는 `True` 를 찍을 것이다.

**왜 그런가**
OAEP 는 평문에 무작위 값을 섞어 감싸므로 같은 평문도 매번 다른 암호문이 된다.
그러나 복호화하면 그 무작위 감싸개가 벗겨져 둘 다 원래의 같은 바이트로 돌아온다.
근거: 2-summary 「동작 방식 (3)」.

### 2. 둘 다 256 — 키 크기의 바이트 수다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`256 256` 이 찍힐 것이다.

**왜 그런가**
RSA 암호문과 서명의 길이는 평문 · 데이터의 길이와 상관없이 키 크기의 바이트 수다.
2048비트 ÷ 8 = 256 바이트이므로 짧은 `b"hi"` 의 암호문도, 긴 문서의 서명도 256 바이트다.
근거: 2-summary 「동작 방식 (3)」 · 「동작 방식 (4)」.

### 3. 변조 감지 문구가 찍힌다 — `verify` 가 `InvalidSignature` 를 던진다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)
`변조 데이터: 서명 무효! (변조 감지)` 가 찍힐 것이다.

**왜 그런가**
`verify` 는 `b"tampered data"` 를 SHA256 으로 해시하고, 그 해시가 서명에 담긴 원래 데이터의 해시와 맞는지 공개키로 확인한다.
데이터가 달라 해시가 다르므로 검증이 실패하고 `InvalidSignature` 예외가 난다.
`try` 안의 「유효함」 줄은 건너뛰어지고 `except` 의 줄이 찍힌다.
근거: 2-summary 「동작 방식 (4)」.

### 4. 「주인만 해야 하는 일」에 개인키가 가기 때문이다

암호화는 누구나 할 수 있어야 아무나 주인에게 비밀을 보낼 수 있고, 여는 일은 주인만 해야 기밀성이 생긴다 — 그래서 공개키로 잠그고 개인키로 연다.
서명은 주인만 만들 수 있어야 「주인이 썼다」는 증명이 되고, 확인은 누구나 할 수 있어야 쓸모가 있다 — 그래서 개인키로 서명하고 공개키로 검증한다.
두 쓰임 모두 「주인 전용 = 개인키, 누구나 = 공개키」라는 같은 규칙을 따르는데, 어느 쪽 동작이 주인 전용인지가 달라서 순서가 뒤집혀 보인다.
근거: 2-summary 「동작 방식 (5)」 · 「핵심 문장 1, 2」.

### 5. 복호화는 암호화 때 감싼 패딩을 정확히 거꾸로 벗겨야 하기 때문이다

RSA 는 평문을 그대로 계산하지 않고 OAEP 로 감싼 뒤 계산한다.
복호화는 RSA 계산을 되돌린 다음 그 감싸개를 벗겨야 하므로, 어떤 규격(MGF1 해시 · OAEP 해시 · label)으로 감쌌는지 알려 줘야 한다.
규격이 다르면 감싸개를 올바르게 벗기지 못해 올바른 개인키로도 복호화가 실패한다.
근거: 2-summary 「동작 방식 (3)」 · 「어디서 틀리나 4」.

### 6. 저장할 때와 같은 비밀번호를 줄 때만 열린다

`load_pem_private_key(encrypted_pem, password=b"my-password")` 처럼 저장 때 쓴 비밀번호를 주면 열리고, 불러온 키의 크기도 2048 그대로다.
잘못된 비밀번호를 주면 예외가 난다.
비밀번호 없이(`password=None`) 열려 해도 잠긴 개인키는 열리지 않는다 — `password=None` 은 평문 PEM 을 열 때 쓰는 값이다.
근거: 2-summary 「동작 방식 (2)」.

### 7. 크기 한도와 느린 속도 때문이다

첫째, 패딩이 자리를 차지하므로 RSA 한 번에 넣을 수 있는 평문은 키 크기보다 작다 — 큰 파일은 애초에 한 번에 들어가지 않는다.
둘째, 원본 팁대로 RSA 는 큰 데이터에 느리다.
그래서 큰 데이터는 하이브리드 암호화로 처리한다.
근거: 2-summary 「동작 방식 (3)」 · 「동작 방식 (5)」 · 「어디서 틀리나 5」.

### 8. AES 는 데이터를, RSA 는 AES 키를 맡는다

보내는 쪽은 무작위 AES 키를 하나 만들어 데이터를 AES 로 암호화하고(원본 주석은 AES-GCM), 그 AES 키만 받는 사람의 공개키와 RSA-OAEP 로 감싼다.
받는 쪽은 먼저 자기 개인키로 감싼 AES 키를 풀고, 그 AES 키로 데이터를 푼다.
RSA 의 크기 한도 · 느린 속도 문제는 피하면서, 「주인만 열 수 있다」는 RSA 의 성질은 그대로 얻는다.
근거: 2-summary 「동작 방식 (5)」.

### 9. 서명은 데이터 전체가 아니라 SHA256 해시값 위에 만들어진다

`sign` 은 먼저 데이터를 `hashes.SHA256()` 으로 해시하고, 그 해시값을 PSS 로 감싸 개인키로 서명한다.
검증 때는 받은 데이터를 같은 해시로 다시 해시해 서명과 맞춰 본다.
데이터가 한 글자만 달라도 해시가 달라지므로 검증이 실패하고, 이것이 무결성 확인, 곧 변조 감지가 된다.
근거: 2-summary 「동작 방식 (4)」.

## 실습 정답

### 실습 1. RSA 키 쌍으로 저장 · 로드 · 암호화 · 서명을 한 파일에 해 보기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 65537 · 2048비트 개인키 생성 | `rsa.generate_private_key(public_exponent=65537, key_size=2048)` |
| 2. 공개키 꺼내기 | `private_key.public_key()` |
| 3. 키 크기 찍기 | `print(f"키 크기: {private_key.key_size}비트")` |
| 4. 평문 개인키 PEM | `private_key.private_bytes(... PrivateFormat.PKCS8, ... NoEncryption())` → `private_pem` |
| 5. 잠긴 개인키 PEM | `private_bytes(... BestAvailableEncryption(b"my-password"))` → `encrypted_pem` |
| 6. 공개키 PEM | `public_key.public_bytes(... PublicFormat.SubjectPublicKeyInfo)` → `public_pem` |
| 7. 평문 개인키 · 공개키 로드 | `serialization.load_pem_private_key(private_pem, password=None)` · `serialization.load_pem_public_key(public_pem)` |
| 8. 잠긴 PEM 로드 | `serialization.load_pem_private_key(encrypted_pem, password=b"my-password")` |
| 9. OAEP 로 암호화 | `public_key.encrypt(message.encode('utf-8'), padding.OAEP(mgf=padding.MGF1(...), algorithm=hashes.SHA256(), label=None))` |
| 10. 암호문 길이 · Base64 찍기 | `len(ciphertext)` · `base64.b64encode(ciphertext)[:40]` |
| 11. 같은 OAEP 로 복호화 | `private_key.decrypt(ciphertext, padding.OAEP(...))` → `plaintext.decode('utf-8')` |
| 12. PSS 로 서명 | `private_key.sign(data, padding.PSS(mgf=..., salt_length=padding.PSS.MAX_LENGTH), hashes.SHA256())` |
| 13. 서명 길이 · Base64 찍기 | `len(signature)` · `base64.b64encode(signature)[:40]` |
| 14. 원래 데이터 검증 | 첫 `try: public_key.verify(signature, data, ...)` / `except Exception` |
| 15. 변조 데이터 검증 | 둘째 `try: public_key.verify(signature, b"tampered data", ...)` / `except Exception` |
| 16. 요약 문구 | `--- RSA 핵심 개념 ---` 부터 끝까지의 `print` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-security/reference/rsa-encryption.py`

```python
# [보안 & 암호화] RSA (비대칭 암호화)
# 설명: RSA 키 생성, 공개키 암호화/복호화, 디지털 서명/검증을 구현
# 팁: RSA 키는 최소 2048비트, 장기 보안은 4096비트를 사용한다. 개인키는 반드시 암호화하여 저장하고, 코드에 포함하지 않는다. OAEP(암호화)와 PSS(서명)가 PKCS1v15보다 안전하다. RSA는 큰 데이터에 느리므로 하이브리드 암호화(RSA로 AES 키를 감싸는 방식)를 사용한다.

# rsa: 키 생성, padding: 안전한 패딩 방식 (OAEP/PSS)
from cryptography.hazmat.primitives.asymmetric import rsa, padding
# hashes: 해시 알고리즘, serialization: PEM/DER 형식 변환
from cryptography.hazmat.primitives import hashes, serialization
# Prehashed: 사전 해시된 데이터 처리 보조
from cryptography.hazmat.primitives.asymmetric.utils import Prehashed
# base64: 바이너리 → 텍스트 출력 인코딩
import base64

# === RSA 키 생성 ===
print("=== RSA 키 생성 ===")
# 2048비트 RSA 키 페어 생성
private_key = rsa.generate_private_key(
    # 65537: 표준 공개 지수 (안전성+성능 균형)
    public_exponent=65537,  # 표준 값
    # 2048비트: NIST 최소 권장 (~2030년까지)
    key_size=2048           # 2048비트 이상 권장
)
# 공개키는 개인키에서 도출 (반대는 불가능)
public_key = private_key.public_key()

print(f"키 크기: {private_key.key_size}비트")
print()

# === 키를 PEM 형식으로 직렬화 ===
print("=== PEM 직렬화 ===")

# 개인키 → PEM (암호화 없이)
# 학습용; 실무에선 절대 평문 저장 금지
private_pem = private_key.private_bytes(
    # PEM: Base64 텍스트 형식 (저장/전송 용이)
    encoding=serialization.Encoding.PEM,
    # PKCS8: 표준 개인키 컨테이너
    format=serialization.PrivateFormat.PKCS8,
    # 암호화 없음 (위험)
    encryption_algorithm=serialization.NoEncryption()
)
print(f"개인키 PEM:\n{private_pem[:80].decode()}...")

# 개인키 → PEM (비밀번호 보호)
# 실무 권장 방식: 패스프레이즈 보호
encrypted_pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    # BestAvailableEncryption: 라이브러리가 강력한 암호 자동 선택
    encryption_algorithm=serialization.BestAvailableEncryption(b"my-password")
)
print(f"\n암호화된 개인키:\n{encrypted_pem[:80].decode()}...")

# 공개키 → PEM
# 공개키는 누구나 가져도 안전
public_pem = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    # SubjectPublicKeyInfo: X.509 표준 공개키 형식
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)
print(f"\n공개키 PEM:\n{public_pem[:80].decode()}...")
print()

# === PEM에서 키 로드 ===
print("=== PEM 로드 ===")
# 평문 PEM 로드
loaded_private = serialization.load_pem_private_key(private_pem, password=None)
loaded_public = serialization.load_pem_public_key(public_pem)
print(f"개인키 로드 성공: {loaded_private.key_size}비트")
print(f"공개키 로드 성공: {loaded_public.key_size}비트")

# 비밀번호 보호된 키 로드
# 잘못된 비밀번호는 예외 발생
loaded_encrypted = serialization.load_pem_private_key(encrypted_pem, password=b"my-password")
print(f"암호화 키 로드: {loaded_encrypted.key_size}비트")
print()

# === 공개키 암호화 / 개인키 복호화 ===
print("=== 암호화/복호화 ===")
message = "비밀 메시지입니다."

# 공개키로 암호화
# OAEP: 패딩 무작위화 → 동일 평문도 매번 다른 암호문 (CCA 공격 방어)
ciphertext = public_key.encrypt(
    message.encode('utf-8'),
    padding.OAEP(
        # MGF1: 마스크 생성 함수 (OAEP의 일부)
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )
)
print(f"암호문 길이: {len(ciphertext)} bytes")
print(f"암호문 (Base64): {base64.b64encode(ciphertext)[:40]}...")

# 개인키로 복호화
# 개인키 소유자만 복호화 가능 → 기밀성 확보
plaintext = private_key.decrypt(
    ciphertext,
    # 암호화와 동일한 패딩 방식 사용 필수
    padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )
)
print(f"복호화: {plaintext.decode('utf-8')}")
print()

# === 디지털 서명 / 검증 ===
print("=== 디지털 서명 ===")
data = "이 문서는 변조되지 않았습니다.".encode('utf-8')

# 개인키로 서명
# PSS: 무작위 솔트 포함 서명 (PKCS1v15보다 안전, RFC 8017 권장)
signature = private_key.sign(
    data,
    padding.PSS(
        mgf=padding.MGF1(hashes.SHA256()),
        # 솔트 길이를 최대로 → 보안 강도 최대
        salt_length=padding.PSS.MAX_LENGTH
    ),
    hashes.SHA256()
)
print(f"서명 길이: {len(signature)} bytes")
print(f"서명 (Base64): {base64.b64encode(signature)[:40]}...")

# 공개키로 검증
try:
    # verify: 실패 시 InvalidSignature 예외
    public_key.verify(
        signature,
        data,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    print("서명 검증: 유효함 ✓")
except Exception:
    print("서명 검증: 무효!")

# 변조된 데이터 검증
try:
    # 데이터 한 글자만 바꿔도 서명 무효 → 무결성 보장
    public_key.verify(
        signature,
        b"tampered data",
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    print("변조 데이터: 유효함")
except Exception:
    # 변조 감지 성공
    print("변조 데이터: 서명 무효! (변조 감지)")
print()

# RSA 사용 패턴 요약
print("--- RSA 핵심 개념 ---")
# 암호화: 공개키로 암호화 → 개인키로만 복호화 가능
print("공개키 암호화 → 개인키 복호화: 기밀성 (누구나 암호화, 소유자만 복호화)")
# 서명: 개인키로 서명 → 공개키로 누구나 검증
print("개인키 서명 → 공개키 검증:   인증+무결성 (소유자만 서명, 누구나 검증)")
print("")
# 패딩 방식 비교
print("--- 패딩 방식 ---")
# OAEP: CCA 안전, 암호화 표준
print("OAEP:  암호화용 (PKCS1v15보다 안전)")
# PSS: 위조 불가능성 증명, 서명 표준
print("PSS:   서명용 (PKCS1v15보다 안전)")
print("")
# 키 크기 가이드
print("--- 키 크기 ---")
# 2048: 2030년까지 안전
print("2048비트: 현재 최소 권장")
# 4096: 장기 보안 (성능 저하 ~5배)
print("4096비트: 장기 보안 권장")
# 하이브리드 암호화 패턴
print("RSA는 큰 데이터에 느림 → 하이브리드 암호화 사용")
# RSA-OAEP로 AES 키만 보호, 실 데이터는 AES-GCM
print("  (RSA로 AES 키를 암호화, AES로 데이터 암호화)")

# 출력:
# === RSA 키 생성 ===
# 키 크기: 2048비트
# === 암호화/복호화 ===
# 복호화: 비밀 메시지입니다.
# === 디지털 서명 ===
# 서명 검증: 유효함
# 변조 데이터: 서명 무효! (변조 감지)
```

**실행 결과** — 실행하지 않음 — 외부 라이브러리 `cryptography` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다.

**풀이 요점**

- 공개키는 따로 만들지 않고 `private_key.public_key()` 로 꺼낸다 — 거꾸로는 안 된다.
- 개인키는 `private_bytes`, 공개키는 `public_bytes` 이고, 개인키만 `encryption_algorithm` 을 받는다.
- 복호화의 OAEP, 검증의 PSS · 해시는 각각 암호화 · 서명 때와 똑같이 적어야 한다.
- `verify` 는 반환값이 아니라 예외로 실패를 알리므로 `try` / `except` 로 감싼다; 더 정확히 하려면 `InvalidSignature` 만 잡는다.
- 들여온 `Prehashed` 는 정답 코드에서 쓰이지 않는다 — 지워도 동작은 같다.
- `NoEncryption()` 과 코드 속 `b"my-password"` 는 학습용이며, 실무에서는 개인키를 잠가 저장하고 비밀번호도 코드 밖에 둔다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — 외부 라이브러리 `cryptography` 가 있어야 도는 예제다 — 그것 없이 만들어 실행하지 않았다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
