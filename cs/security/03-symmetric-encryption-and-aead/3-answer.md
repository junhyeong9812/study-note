# security/03-symmetric-encryption-and-aead — 정답

## 정답

### 1. 깨지는 곳은 사용법

- AES는 16바이트 블록을 키에 따라 섞는 순열이다. 이 부품에 대해서는 알려진 실용 공격이 없다.
- 사고는 부품을 **어떻게 잇느냐**(운용 모드), **nonce를 어떻게 고르느냐**, **인증을 붙였느냐**에서 난다.
  - 모드: ECB면 패턴이 남는다.
  - nonce: GCM에서 반복하면 평문 XOR·위조.
  - 인증: CBC·CTR만 쓰면 암호문을 바꿔 평문을 조작할 수 있다.

### 2. 네 모드 그림과 반복 평문

```text
  ECB  P1→[E]→C1  P2→[E]→C2           (블록 독립)
  CBC  IV⊕P1→[E]→C1, C1⊕P2→[E]→C2      (체인)
  CTR  Ci = Pi ⊕ E(N‖i)                (카운터 키스트림)
  GCM  CTR(N‖2부터) + 태그 = GHASH_H(AAD, C) ⊕ E(N‖1),  H = E_K(0^128)
       (N‖1 = J₀는 96비트 nonce일 때. 다른 길이면 J₀ = GHASH_H(IV‖…))
```

- 실험 E3 [A] — OpenJDK 21.0.12, 교육용 고정 키: ECB는 4블록이 모두 `8a21cef935d8587bea999da471a91c41`. GCM은 4블록이 모두 다르고 16바이트 태그가 붙는다.

### 3. `Cipher.getInstance("AES")`

- `AES/ECB/PKCS5Padding`이다. 실험 E3 [B]에서 두 변환의 출력이 같았다(`true`).
- Java `Cipher` 문서는 "algorithm"만 적으면 **provider별 기본값**을 쓴다고만 적는다. 어떤 값인지는 provider(SunJCE)의 동작이다 — 문서는 보장하지 않고, 실험은 이 판(21.0.12)에서 그렇다는 것을 보인다.
- 그래서 변환 문자열은 `AES/GCM/NoPadding`처럼 전부 적는다.

### 4. nonce 재사용의 결과

- `C1 ⊕ C2 = P1 ⊕ P2`. 키스트림이 같아 상쇄된다. 실험 E3 [C]에서 두 값이 바이트 단위로 같았다.
- `P2`를 알면 `C1 ⊕ C2 ⊕ P2 = P1`. 실험에서 `"transfer 100 to alice"`가 복원됐다.
- 기밀성 외: SP 800-38D 부록 A — 공격자가 해시 부분키 H를 알아낼 가능성이 높고, 그러면 그 IV로 나온 (암호문, 태그)를 바탕으로 같은 IV의 임의 암호문·AAD에 유효한 태그를 만든다. **인증 보장이 사실상 사라진다.** §8은 이 요구가 실무에서 "키의 비밀성에 거의 맞먹을 만큼 중요하다"(almost as important)고 적는다.

### 5. SunJCE가 막는 범위

| 경우 | 결과 |
|---|---|
| 같은 `Cipher` 객체를 같은 키·IV로 다시 `init` | 거부: `InvalidAlgorithmParameterException: Cannot reuse iv for GCM encryption`(실험 [E]) |
| 새 `Cipher` 객체, 같은 키·IV | 막지 않음(실험 [C]가 이 방식) |
| 다른 서버 인스턴스 | 서로 모름 |

- ChaCha20-Poly1305도 같은 객체에서만 `InvalidKeyException: Matching key and nonce from previous initialization`(실험 `Cc.java`).
- nonce 유일성은 애플리케이션 책임이다.

### 6. CBC 비트 조작

- 복호 결과: `"amount=900;to=bob"`, 예외 없음(실험 E3 [F]). CBC 첫 블록은 `P1 = D(C1) ⊕ IV`라 IV의 바이트를 x만큼 바꾸면 평문 같은 위치가 x만큼 바뀐다.
- GCM 암호문에 같은 조작: `AEADBadTagException: Tag mismatch`(실험 [F']). 평문은 나오지 않는다.

### 7. 무작위 nonce의 상한

- SP 800-38D §8.3: 무작위(RBG 기반) IV를 쓰면 한 키로 인증 암호화 함수 호출이 **2^32회를 넘으면 안 된다**. §8 요구(같은 키에서 IV 반복 확률 2^−32 이하)를 지키기 위해서다.
- 넘기 전에 키를 회전한다. 키별 사용 횟수를 센다. 또는 결정적 구성(인스턴스별 고정 필드 + 되돌아가지 않는 카운터)을 쓴다.

### 8. AAD와 복사 공격

- 복호 실패: `Tag mismatch`(실험 E3 [G]). AAD가 다르면 태그가 맞지 않는다.
- 막는 공격: 암호문 바꿔치기(cut-and-paste). 내 행에 관리자 행의 암호화된 값을 복사해 넣거나, 다른 사용자 문맥의 토큰을 재사용하는 것.

### 9. 배포 후 전체 `Tag mismatch`

- 원인 후보
  1. AAD 구성 변경(테이블명·키 컬럼·직렬화 방식).
  2. 키 버전 매핑 오류(옛 데이터를 새 키로 열려 함).
  3. 태그 길이·nonce 길이 설정 변경(`GCMParameterSpec`의 첫 인자, nonce 위치).
- 재발 방지: 저장 형식(버전 접두·키 ID·nonce 길이·태그 길이·AAD 규칙)을 계약으로 문서화하고, 형식 버전별 복호 경로를 둔다. 배포 전에 옛 데이터 샘플 복호 테스트.

### 10. 패딩 오라클 의심

- 의심: 인증 없는 CBC 토큰에 대한 패딩 오라클. 응답이 "패딩 오류"와 "그 밖의 오류"를 구분해 주면, 공격자는 암호문을 조금씩 바꿔 그 차이만으로 평문을 알아낸다(Vaudenay 2002, POODLE CVE-2014-3566과 같은 종류).
- 당장: 모든 복호 실패를 같은 응답·같은 처리 경로로 만들고(시간 차이도 줄임), 출처별 속도 제한.
- 근본: AEAD로 교체. CBC를 유지해야 하면 Encrypt-then-MAC — MAC을 먼저 상수 시간으로 검사하고 실패하면 복호를 시작하지 않는다.
