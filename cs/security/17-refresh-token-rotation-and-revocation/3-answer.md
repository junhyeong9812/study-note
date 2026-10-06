# security/17-refresh-token-rotation-and-revocation — 정답

## 정답

### 1. 수명을 나누는 이유

- access는 API마다 내밀어 노출이 잦다. 짧게 두면 탈취돼도 피해 창이 좁다.
- 로그인 경험은 길어야 하므로, 새 access를 받는 권리(refresh)를 길게 둔다. refresh는 토큰 엔드포인트에만 간다.
- RFC 9700 §4.14.1: refresh 토큰은 클라이언트에 허락된 전체 범위를 대표하고 특정 리소스 서버에 묶이지 않는다. 탈취해 재생하면 access를 계속 찍어 낼 수 있다.

### 2. 탈취 토큰 재사용

```text
  RT1(used) → RT2(used) → RT3(유효)
  공격자: RT2 제출 → "이미 쓴 토큰" → 재사용 탐지 → 패밀리 폐기 → RT3도 무효
```

- 서버는 RT2를 낸 쪽이 공격자인지 정상 클라이언트인지 구별하지 못한다(RFC 9700 §4.14.2). 그래서 패밀리의 활성 토큰을 폐기해 공격을 멈추고, 정상 클라이언트는 다시 인가를 받는다.
- 실험 2: `attacker uses stolen : invalid_grant(reuse detected …)`, `legit uses its new rt : invalid_grant(family revoked)`.

### 3. RFC 9700 §4.14.2의 두 방법

- sender-constrained refresh 토큰: 토큰을 클라이언트 인스턴스의 키에 암호학적으로 묶는다(mTLS RFC 8705, DPoP RFC 9449). 훔쳐도 키 없이는 못 쓴다 → **막는다**.
- 회전: 갱신마다 새 토큰, 옛 것은 무효로 하되 관계를 기억. 두 쪽이 같은 토큰을 쓰면 한쪽이 무효 토큰을 내 → **알아챈다**.
- 둘 중 하나는 MUST(public client).

### 4. 탭 경합 실험

- 유예 0초: 한 탭은 새 토큰, 다른 탭은 `reuse detected` → 패밀리 폐기 → 이긴 탭의 다음 갱신도 `family revoked`. 공격자 없이 전원 로그아웃.
- 유예 10초: 두 탭 모두 새 토큰(패밀리가 두 갈래), 다음 갱신도 성공.
- 단일 비행: `requests sent=1`, 두 탭이 같은 결과(`same=true`)를 공유.
- 어느 탭이 먼저인지는 실행마다 다를 수 있다.

### 5. 유예 창의 대가

- 창 안에서는 재사용 탐지가 꺼진다. 공격자가 훔친 직후 창 안에서 쓰면 탐지되지 않고 새 토큰을 받는다. 그래서 몇 초 단위로 짧게 둔다.
- Auth0 문서: 기본 꺼짐, 초 단위 설정. 창 안에서는 **직전 토큰만** 재사용할 수 있고, 그 이전 토큰을 내면 탐지가 걸린다.

### 6. 회전과 최종 만료

- 남은 수명 = 8시간 − 10분 = 7시간 50분(RFC 10017 §6.3.2.3 예). 처음 정한 만료 너머로 늘리면 안 된다(MUST NOT, 만료가 미리 정해진 경우).
- 회전마다 수명이 다시 8시간으로 늘면, 훔친 토큰을 주기적으로 회전시키는 공격자가 영원히 쓸 수 있다. 실험 5: 한 시간마다 회전해도 8시간째 `expired`.

### 7. 비밀번호 변경 후 계속되는 호출

- refresh: 그 사용자의 refresh 패밀리 상태를 본다. 비밀번호 변경 때 폐기하지 않았다면 그대로 유효다. 대처는 변경 시 패밀리 전체 폐기(RFC 9700 §4.14.2 MAY)와 `valid_after` 기록. 실험 4: `invalid_grant(revoked: password changed)`.
- 자기 포함 access: 리소스 서버가 서명·`exp`만 보면 폐기가 전달되지 않는다(RFC 7009 3절). 대처는 `iat < valid_after` 거부, introspection, `jti` 폐기 목록(TTL = 남은 수명).
- 539초: 비밀번호 변경 1초 뒤 시점에 그 access 토큰이 `exp`까지 남은 시간이다. `exp`만 보면 그동안 200, `valid_after`를 보면 401.

### 8. 경합에 약한 코드와 고친 형태

- 약한 이유: 두 요청이 거의 동시에 `used_at IS NULL`을 읽으면 둘 다 "처음 사용"으로 판단해 둘 다 새 토큰을 받거나, 순서에 따라 엇갈린 판정이 난다.
- 고친 형태: 판정과 표시를 한 문장으로.

```java
int won = jdbc.update("""
    UPDATE refresh_tokens SET used_at = now()
     WHERE token_hash = ? AND used_at IS NULL AND NOT revoked AND abs_exp > now()""", h);
if (won == 1) return issueNext(h);
// won == 0: 무효·만료·폐기·재사용 중 무엇인지 다시 읽어 가린다 → 재사용이면 패밀리 폐기 + 보안 로그
```

### 9. 저장 위치와 XSS

- localStorage: 같은 출처 스크립트가 다 읽는다. 한 번에 탈취(RFC 10017 §8.5, web-platform/06 실험).
- 메모리·클로저: 노출 창이 줄지만 프로토타입 오염으로 인자를 가로챌 수 있다(§8.4). 새로고침에 사라진다.
- BFF: 토큰이 브라우저 JavaScript에 없다(클라이언트 측 세션이면 HttpOnly 쿠키 안에 들 수는 있다, §6.1.2.3). 쿠키는 `HttpOnly`·`Secure` MUST, `SameSite=Strict` SHOULD, HTTP 설정을 나타내는 접두사(예: `__Host-Http-`) SHOULD(§6.1.3.2). 남는 위험은 사용자 브라우저를 통해 BFF에 요청을 대신 보내는 것(§5.1.4).
- 저장소 격리로도 못 막는 것: §5.1.3 — 악성 스크립트가 숨은 iframe으로 새 인가 코드 흐름을 돌려 **독립된 새 토큰**을 받는다. 짧은 수명·회전·DPoP도 효과가 없다고 RFC가 적는다. BFF(confidential client)는 이 흐름을 막는다.

### 10. `invalid_grant` 원인 가리기

- 서버 로그에서 이유(unknown·expired·revoked·reuse)를 먼저 나눈다. RFC 6749 §5.2는 무효·만료·폐기를 모두 `invalid_grant`로 응답한다.
- 탭 경합 쪽 신호: 같은 사용자·같은 IP·같은 UA에서 수백 ms~몇 초 간격의 reuse, 브라우저에 동시 `/refresh` 요청.
- 탈취 쪽 신호: 다른 IP·UA에서, 직전 사용 뒤 몇 시간 지나 reuse. 같은 시각대 여러 사용자에서 동시에 발생하면 스크립트 변조·대량 유출을 의심.
