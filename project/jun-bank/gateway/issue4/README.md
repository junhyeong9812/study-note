# issue4 — /internal 관리 표면 HMAC 인가

- 원본 PR: gateway #12 · devlog: `jun-bank/gateway/docs/devlog/pr-06-internal-authz.md`

## 1. 무엇이 문제였나

게이트웨이의 `/internal` 관리 표면(배포 시 라우트를 전환하는 내부 API)은 배포 agent만 불러야 한다.\
그런데 그때까지 인증이 없었다 — LAN 경계(방화벽·NAT)에만 의존했다.

`/internal`에는 이미 fencing token 검증이 있었지만, 그건 인가가 아니다.

> **fencing은 순서, 인가는 신원** — fencing token은 "낡은 실행자의 순서"를 막는 장치이고, 인가는 "누가 부르는가"를 판정한다.\
> 예: 번호표(fencing)가 있어도, 아무나 번호표를 뽑아 창구에 설 수 있으면 신원 확인(인가)은 안 된 것이다.

LAN 안의 어떤 프로세스든 라우트 상태를 조회해 마지막 token을 읽고, 거기에 +1을 붙여 전환을 호출할 수 있었다.\
위협 모델은 제한적이지만(LAN 내부), 인가의 부재는 구조적이다.

## 2. 무엇을 고민했나

세 가지를 놓고 봤다.

- **HMAC 공유 비밀** — agent와 gateway가 공유 키로 요청을 서명한다.\
  배포 파이프라인이 이미 게이트 1(CI↔agent)에서 HMAC 계약을 쓰고 있어 패턴이 일관되고, 무엇보다 "누가 부르는가"를 실제로 판정한다. (채택)
- **관리 포트 분리** — `/internal`을 내부 인터페이스에만 바인딩한다.\
  LAN 의존을 또 다른 네트워크 의존으로 바꿀 뿐이고, 포트 분리만으로는 인가가 서지 않는다. (기각)
- **둘 다** — HMAC + 포트 분리를 함께 건다. (미채택 — HMAC만으로 인가가 성립)

> **HMAC(해시 기반 메시지 인증 코드)** — 공유한 비밀 키로 메시지에 지문을 찍는 것. 키가 없으면 같은 지문을 못 만든다.\
> 예: agent가 요청에 키로 지문을 찍어 보내면, 같은 키를 가진 gateway만 "정말 agent가 보냈다"를 확인할 수 있다.

canonical 서명 형식은 배포 게이트 1과 같은 계열이되, 관리 표면에 맞춰 4필드(method·path·body digest·timestamp)로 뒀다.\
키는 배포 게이트 1의 `AGENT_HMAC_KEY`와 **별도**다 — 관리 표면과 배포 요청은 다른 신뢰 경계이기 때문이다.

## 3. 그래서 이렇게

인가를 fencing보다 **먼저** 두는 최우선 WebFilter로 세웠다.\
무서명 요청은 body를 읽기 전에 즉시 판정하고(인증 전 body를 읽지 않는다), 서명 요청만 크기 제한 후 캐시해 컨트롤러에 재공급한다.\
오류가 어느 경로로도 chain으로 새지 않는다(fail-closed).

무중단으로 켜야 한다는 제약이 하나 더 있었다.\
인증을 붙이는 쪽(agent)과 검사하는 쪽(gateway)은 다른 시점에 배포된다.\
gateway를 바로 강제(enforce)로 켜면 아직 서명 안 붙이는 agent 호출이 401나서 배포가 끊긴다.

그래서 audit → enforce 두 단계로 켰다.

> **audit / enforce** — audit는 "검사는 하되 막지 않고 기록만", enforce는 "위반을 실제로 차단"하는 모드다.\
> 예: 새 검문소를 처음엔 통과시키며 로그만 남기다(audit), 다들 통과하는 게 확인되면 못 지나가게 막는다(enforce).

```text
agent가 서명을 붙이도록 먼저 배포
        ↓
gateway를 audit로 기동                서명 있으면 검증·없으면 통과+경고
        ↓
실제 배포에서 agent 호출이            "valid-signature 양성"으로 찍히는지 관측
"valid-signature 양성"으로 찍힘
        ↓
gateway를 enforce로 승격             무서명 차단
```

## 4. 코드 — 실제 커밋에서

최우선 WebFilter가 인가를 fencing보다 먼저 판정한다.

```kotlin
// InternalAuthWebFilter.kt (발췌) — 인가가 fencing보다 먼저
// 최우선 WebFilter가 /internal/**를 canonical-v1 HMAC로 인가한다. 무서명은 body를 읽기 전
// 즉시 판정하고(인증 전 body를 읽지 않는다), 서명 요청만 크기 제한 후 캐시해 컨트롤러에
// 재공급한다. 오류 어느 경로도 chain으로 새지 않는다(fail-closed).
```

모드 문자열은 정규화 없이 원문 그대로 정확 비교한다.

```kotlin
// InternalAuthWebFilter.kt (발췌) — 정확 비교
// 정확 비교(원문 그대로·대소문자 구분·주변 공백 불허). trim·lowercase 하면 ` AUDIT `·
// `AUDIT`이 audit로 접혀 무서명이 열린다(재현 — 실 fail-open).
fun parseMode(raw: String): InternalAuthMode = when (raw) {
    "audit" -> InternalAuthMode.AUDIT
    ...
```

## 5. 구현 중 마주친 문제

**되돌린 설계 — 요청만 서명 → 응답도 서명.**\
초안은 요청만 서명하려 했다.\
그러나 평문 HTTP에서 응답에 "서버가 만들었다는 증거"가 없으면 응답이 위조된다.\
그래서 응답도 HMAC으로 서명하도록 바꿨다.

**실 fail-open — 정규화가 안전장치를 뚫었다.**\
모드 값을 `trim().lowercase()`로 정규화하는 바람에, 계약상 기동을 거부해야 할 `AUDIT`·` audit `(대소문자·공백 변형)이 audit로 수락됐다.\
`GATEWAY_INTERNAL_AUTH_MODE=' AUDIT '`로 띄우면 무서명 GET이 200으로 통과하는 게 재현됐다.\
코드는 맞아 보였지만 정규화가 안전장치를 뚫은 것이다 — 수정은 위 §4의 원문 정확 비교였다.

**canonical 필드 수 불일치.**\
공용 `auth.Sign`이 6필드 canonical을 끌고 오는데, 관리 표면은 4필드다.\
그대로 부르면 전건 불일치라, interop 파손을 미리 막았다.

**pass-through env 함정.**\
agent 프로세스는 기동 시점의 `.env`를 메모리에 로드한다.\
그래서 host `.env`만 enforce로 바꿔도 agent가 여전히 구값(audit)을 compose에 주입한다.\
1차 enforce가 audit로 뜬 원인이었고, agent 재기동으로 해결했다 — runbook에 남긴 절차 지식이다.

## 6. 결론

`/internal` 관리 표면에 "누가 부르는가"를 판정하는 인가가 섰고, 실운영은 enforce까지 완료됐다.\
audit → enforce 무중단 이관으로 실배포를 끊지 않고 켰다.

인가가 서면서 fencing token의 rollback 재전송 창(전환 실패 후 30초 안에 원본 서명 재전송이 죽은 slot으로 재전환)이 별도 이슈(#11)로 분리됐다 — 인가와 fencing 재설계를 섞지 않는 판단이다.
