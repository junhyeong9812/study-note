# security — 비밀·권한·신뢰 경계

비밀 관리, 인가 위치, 입력이 문법으로 해석되는 경계에서 나오는 패턴이다.\
공통 원리: **검사한 것과 실제로 쓰는 것이 같은 객체·같은 해석이어야 하고, 강제 지점은 모든 경로가 지나는 한 곳에 있어야 한다.**

## 공통 원리

```
  외부 입력 ──▶ [검사 지점] ──────────▶ [사용 지점]
                   │                        │
                   ├─ 문자열 패턴 검사      ├─ 셸·SQL·경로로 재해석
                   ├─ 일부 경로에만 존재     ├─ 링크 추종·재열람(TOCTOU)
                   └─ 판정 실패를 통과 처리  └─ 과거 승인·클라이언트 주장
                                    ▼
         검사 ≠ 사용 → 우회 / 비밀 노출 경로는 지우기 어렵다
```

## 패턴 카드

- [authorization-freshness-binding](authorization-freshness-binding/) — 인증·승인 신호는 "지금 이 행위"에 결속돼야 한다 — 서명은 신선도가 아니고, 신선도가 다른 소스를 OR로 합치면 과거 승인이 현재를 통과시키며, stateless 토큰은 명시 폐기해야 한다.
- [authorization-gate-placement](authorization-gate-placement/) — 인가는 모든 경로가 지나는 단일 지점에서, 부작용 이전에, 런타임이 보증하는 신원으로 판정해야 한다 — 클라이언트 주장·두 번째 입력 경로·앞단 필터의 조기 확정은 우회를 만든다.
- [browser-credential-policy](browser-credential-policy/) — 브라우저 자격(쿠키) 정책 — 자동 첨부되는 쿠키 인증은 CSRF 방어가 필요하고, `*`+credentials CORS는 금지되며, Secure 쿠키는 HTTPS에서만 전송된다.
- [complete-mediation](complete-mediation/) — 강제 지점이 쓰기·원격 변경 경로 일부(특정 API·명령 이름)에만 있으면 같은 효과를 내는 다른 경로가 보호 밖에 남는다(complete mediation 위반).
- [data-interpreted-as-syntax](data-interpreted-as-syntax/) — 데이터가 하위 인터프리터(argv 옵션·pathspec·셸·SQL·LIKE·템플릿·eval·로그 줄)의 문법으로 해석되면 인젝션이 된다 — 옵션 종결자·바인딩·리터럴 모드·화이트리스트로 데이터 채널을 분리한다.
- [local-endpoint-hardening](local-endpoint-hardening/) — 루프백·유닉스 소켓 바인드만으로는 같은 호스트의 다른 프로세스·브라우저 오리진을 막지 못한다 — 로컬 끝점도 인증·Origin 검증·입력 검증·자원 상한이 필요하다.
- [regex-is-not-a-shell-parser](regex-is-not-a-shell-parser/) — 셸 명령·자연어를 문자열 패턴으로 검사하면 셸의 실제 토큰화·리다이렉트·경로 해석과 desync된다 — 우회(false-allow)와 오탐(false-block)이 동시에 생기므로 보안 경계는 구조화된 신호로 세운다.
- [searchable-encryption-blind-index](searchable-encryption-blind-index/) — salt·IV를 쓰는 가역 암호화는 의도적으로 비결정적이라 동등 조회가 불가하다 — 조회용 키는 비밀 키 기반 HMAC 결정적 해시 컬럼으로 분리한다.
- [secret-ownership-least-privilege](secret-ownership-least-privilege/) — 비밀은 단일 소유·정본은 실사용처·최소 노출 경로여야 한다 — argv·URL·로그·git 히스토리·예시 파일·평문 사본처럼 지우기 어려운 곳으로 새지 않게 한다.
- [symlink-following-escape](symlink-following-escape/) — 검사와 사용의 링크 추종 의미가 다르면(exists vs open, 최종 성분만 검사, 폴백 copy) 심볼릭 링크로 경계를 탈출한다 — lstat·전체 경로 resolve·생성/읽기 모든 분기에 같은 링크 정책.
- [trust-on-first-use](trust-on-first-use/) — 호스트 신뢰는 일치·불일치·미지 세 상태이며, 신뢰 결정의 영속·판독이 실패하면 신뢰로 진행하지 않는다(fail-closed TOFU).
- [verify-what-you-use](verify-what-you-use/) — 검증한 것과 사용하는 것이 같은 객체·같은 해석이어야 한다 — 정규화·파서 차이, 문자열 vs 실제 전송 hop, 재열람 TOCTOU, 승인 표시 vs 실제 대상이 어긋나면 검증이 무의미해진다.

> 이 폴더의 메타 태그: `least-privilege`(9) · `fail-closed`(1) · `parser-differential`(2) — 태그별 전체 목록은 [cs/issue 태그 역인덱스](../../README.md#태그-역인덱스).
