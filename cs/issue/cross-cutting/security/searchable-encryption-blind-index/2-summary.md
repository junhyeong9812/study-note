# cs/issue/security/searchable-encryption-blind-index — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.

## 전체 흐름

```
[비결정 암호화 = 같은 입력, 다른 출력]
  encrypt("a@x.com") → 9f3c…   (salt₁)
  encrypt("a@x.com") → 41be…   (salt₂)
  WHERE email = encrypt(?)  → 절대 일치 안 함 → 중복 판정·조회 불가

[교정: 용도별 두 컬럼 (blind index)]
                       ┌─ email       = encrypt(norm(v))            복원·표시·발송
  입력 v ── norm() ────┤
   trim + lower        └─ email_hash  = HMAC-SHA256(pepper, norm(v)) 조회·유일키
                                        CHAR(64) UNIQUE

  조회:  WHERE email_hash = HMAC(pepper, norm(?))
  동시 가입:  두 INSERT 중 하나만 UNIQUE 통과 → 나머지 무결성 위반 → 409

[왜 HMAC(pepper)인가]
  SHA-256(email) → 이메일 사전으로 역추적 가능 (입력 공간 작음)
  HMAC(pepper, email) → 키 없이는 사전 대입 불가
```

## 핵심 문장

- salt·IV 암호화는 패턴 은닉을 위해 **의도적으로 비결정적**이라 암호문 동등 비교가 성립하지 않는다.
- 동등 조회가 필요하면 **결정적 해시 컬럼을 따로** 둔다(blind index). 대가로 그 컬럼은 "같은 값끼리 같은 해시"라는 동등성·빈도 정보를 다시 드러낸다. 부분 검색(LIKE)은 이것으로도 안 된다.
- 그 해시는 **비밀 키 기반 HMAC**이어야 한다 — 평문 해시는 작은 입력 공간에서 사전 공격에 뚫린다.
- 암호화와 해시는 **같은 정규화**를 거쳐야 한다 — 다르면 대소문자·공백으로 중복 방지가 우회된다.
- 유일성은 해시 컬럼의 **UNIQUE 제약**이 판정하고, 앱은 무결성 위반을 409로 바꾼다.
