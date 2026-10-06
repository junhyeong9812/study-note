# security/02-threat-modeling — 자산·공격 표면·신뢰 경계·STRIDE, 데이터 흐름 다이어그램 — 정리 (힌트)

## 해결하는 문제

01번의 원칙은 "어디에" 적용할지를 알려 주지 않는다. 문은 수천 개이고, 보안 리뷰 시간은 한정돼 있다.

```text
  위협 모델링 없이 하는 보안 리뷰
    "SQL 인젝션 있나요?"  "XSS는요?"  "비밀번호 해시는?"   ← 체크리스트 = 알려진 구현 결함
    → 다 통과
    → 그런데 내부 서비스가 게이트웨이가 붙인 X-User-Role 헤더를 그대로 믿는다  ← 설계 결함
```

- 구현 결함은 고치면 된다. 설계 결함은 **필요한 통제가 애초에 없다**.
  - OWASP Top 10 2021 A04 Insecure Design: "안전하지 않은 설계는 완벽한 구현으로 고칠 수 없다. 정의상 필요한 보안 통제가 만들어진 적이 없기 때문이다."
  - 2025판에서는 같은 범주가 A06:2025 Insecure Design으로 남았다.
- *위협 모델링(threat modeling)*: 시스템의 표현(그림)을 분석해 보안·프라이버시 우려를 드러내는 일(Threat Modeling Manifesto 정의).

쉬운 예: 집의 방범 점검이다.
- 무엇이 귀중한가(자산) → 어디로 들어올 수 있나(공격 표면: 문·창·환기구) → 어디서부터 "집 안"인가(신뢰 경계: 현관) → 각 입구에서 무엇이 잘못될 수 있나(STRIDE).
- 현관문을 아무리 튼튼하게 해도 열린 창문은 못 막는다.

똑같은 구조다.\
코드 리뷰가 "현관문 자물쇠 품질"을 본다면, 위협 모델링은 "창문이 있다는 사실"을 찾는다.

## 동작·원리

### 1. 네 질문 — 절차의 뼈대

```text
  ① 무엇을 만들고 있나?          → 데이터 흐름 다이어그램(DFD)을 그린다
  ② 무엇이 잘못될 수 있나?        → 신뢰 경계를 건너는 흐름마다 STRIDE를 묻는다
  ③ 그것에 대해 무엇을 할 건가?    → 완화·수용·회피·이전, 담당·티켓
  ④ 충분히 잘했나?                → 다이어그램과 실제 구현 대조, 테스트로 확인
```

- 네 질문은 Shostack이 정리했고, Threat Modeling Manifesto(Shostack 포함 15인)가 그대로 채택했다.
- OWASP Threat Modeling Cheat Sheet: 설계 단계에서 하는 것이 이상적이고, 한 번 하고 끝나는 활동이 아니라 시스템과 함께 갱신한다. A04(2021)는 refinement(백로그 다듬기) 회의에 넣으라고 권한다.

### 2. 데이터 흐름 다이어그램과 신뢰 경계

```text
                      ║ 신뢰 경계 TB1: 인터넷 ↔ 우리 망
   (사용자 브라우저) ─────║──① HTTPS 요청 + 토큰──> [API 게이트웨이]
     외부 개체             ║                          │ ② X-User-Id, X-User-Role 붙여 전달
                      ║                          ▼
                      ║ ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄ TB2: 게이트웨이 ↔ 내부 서비스
                      ║                     [주문 서비스] ──③ SQL──> ═[주문 DB]═
                      ║                          │                      데이터 저장소
                      ║                          └──④ URL 가져오기──> (외부 이미지 서버) ── TB1 다시 건넘
```

- DFD 요소(OWASP Cheat Sheet): *외부 개체*(우리가 통제 못 함), *프로세스*(코드가 도는 곳), *데이터 저장소*, *데이터 흐름*, *신뢰 경계*.
  - *신뢰 경계(trust boundary)*: 그 선을 넘으면 통제 주체·권한 수준이 바뀌는 곳. 넘어오는 데이터는 "검증 전"이다.
  - *공격 표면(attack surface)*: 외부에서 닿을 수 있는 입력 지점 전체. 위 그림의 ①과 ④의 응답이다.
  - *자산(asset)*: 지켜야 할 것. 주문 DB의 개인정보, 결제 권한, 서명 키.
- 핵심 관찰: 위협은 대부분 **경계를 건너는 흐름**에 몰린다. 경계 안쪽끼리의 흐름도 "안쪽이니 안전"이라고 가정하면 안 된다(장애 1).

### 3. STRIDE — 흐름마다 여섯 가지를 묻는다

| 위협 | 깨지는 성질 | 위 그림에서 물을 것 |
|---|---|---|
| **S**poofing(위장) | 인증 | ② 내부 서비스는 헤더를 붙인 게 진짜 게이트웨이인지 아나? |
| **T**ampering(변조) | 무결성 | ① 클라이언트가 `X-User-Role`을 직접 넣으면 게이트웨이가 지우나? |
| **R**epudiation(부인) | 부인 방지 | 주문 취소를 "내가 안 했다"고 하면 증거(감사 로그)가 있나? |
| **I**nformation disclosure(정보 노출) | 기밀성 | ③ 에러 응답에 SQL·스택 트레이스가 나가나? |
| **D**enial of service(서비스 거부) | 가용성 | ④ 외부 이미지 서버가 느리면 주문 스레드가 다 묶이나? |
| **E**levation of privilege(권한 상승) | 인가 | ② 헤더 하나로 관리자가 되나? ④ URL로 내부 주소(메타데이터)를 부르게 되나? |

- STRIDE는 Microsoft가 SDL(보안 개발 생명주기)에서 쓰는 분류다. Microsoft Threat Modeling Tool 문서가 여섯 범주와 예를 정의한다.
- STRIDE는 **질문 생성기**다. 완전한 목록이 아니다. 비즈니스 로직 남용(예: 좌석 수백 개 선점 — A04 시나리오 2)은 따로 묻는다.
- 요소별로 묻는 방법(STRIDE-per-element): 데이터 흐름엔 T·I·D, 데이터 저장소엔 T·I·D(로그 저장소면 R도), 프로세스엔 여섯 전부, 외부 개체엔 S·R. 표의 구체 배정은 Shostack 『Threat Modeling』(2014) 3장 [?].

### 4. 로컬 재현 — 경계 안쪽 입력을 믿을 때

자기 예제(실험 E2): 게이트웨이가 토큰을 검증하고 `X-User-Role`을 붙여 내부 서비스로 보낸다. 내부 서비스는 그 헤더만 본다.

```text
  (실험, OpenJDK 21.0.12 eclipse-temurin, 127.0.0.1 서버 3개, --network none, 2026-10-07)
  [1] 취약 게이트웨이(클라이언트 X- 헤더를 그대로 전달)
        /admin/users [Authorization, Bearer tok-…] -> 403 role=user
        /admin/users [Authorization, Bearer tok-…, X-User-Role, admin] -> 200 role=admin
  [2] 고친 게이트웨이(경계에서 X-User-*를 지우고 자기가 다시 씀)
        /admin/users [Authorization, Bearer tok-…, X-User-Role, admin] -> 403 role=user
  [3] 내부 포트에 직접 (경계 우회 — 네트워크 정책이 막아야 하는 경로)
        /admin/users [X-User-Role, admin] -> 200 role=admin
```

- [1]: STRIDE의 T(헤더 변조) → E(권한 상승). 게이트웨이가 경계에서 신원 헤더를 **지우지 않고** 클라이언트 값을 통과시켰다.
- [2]: 경계에서 덮어쓰자 막혔다.
- [3]: 그래도 내부 포트에 직접 닿을 수 있으면 다시 뚫린다. 내부 서비스가 "게이트웨이 경유"라는 사실을 확인하지 않기 때문이다(S — 위장). 네트워크 정책(게이트웨이만 접근 허용)이나 mTLS([network/32](../../network/32-mtls-and-cert-operations/2-summary.md)), 서명된 내부 토큰으로 막는다.

## 쓰이는 자료구조·알고리즘

- **데이터 흐름 다이어그램 = 방향 그래프.** 노드 = 외부 개체·프로세스·저장소, 간선 = 데이터 흐름, 신뢰 경계 = 노드 집합의 분할([data-structure/08-graph](../../data-structure/08-graph/2-summary.md)).
  - "경계를 건너는 흐름" = 양 끝 노드가 서로 다른 분할에 속하는 간선. 위협 후보를 이 간선 집합으로 좁힌다.
  - "외부 입력이 닿는 내부 노드" = 외부 개체에서 시작한 도달 가능성(BFS·DFS — [algorithm/11-bfs](../../algorithm/11-bfs/2-summary.md)). 내부 서비스라도 외부에서 도달 가능하면 공격 표면이다.
- **STRIDE-per-element = (요소 종류 → 위협 집합) 표 조회.** 요소마다 해당 위협을 체크리스트로 펼친다.
- **위험 우선순위 = 가능성 × 영향.** 점수 체계(CVSS 등)는 정렬 키일 뿐이고, 상위 몇 개부터 처리한다.

## 적용 — 풀어나가는 법

### 1. 한 시간짜리 위협 모델링 순서 (기능 단위)

1. 그 기능의 DFD를 화이트보드에 그린다. 신뢰 경계를 점선으로.
2. 경계를 건너는 흐름에 번호를 붙인다.
3. 흐름마다 STRIDE 여섯 질문. 답이 "모름"이면 그것이 발견이다.
4. 발견마다 대응(완화·수용·회피·이전)과 담당자, 티켓 번호.
5. ④번 질문: 구현 후 다이어그램과 실제가 같은지, 완화가 테스트로 확인되는지 본다.

### 2. 신뢰 경계에서 신원 헤더를 다시 쓴다

```java
// 취약: 클라이언트가 보낸 헤더를 그대로 내부로 전달
request.getHeaderNames().asIterator().forEachRemaining(h ->
        upstream.header(h, request.getHeader(h)));

// 고친 판: 경계에서 신원·내부 헤더를 지우고, 검증한 값으로 다시 쓴다
Set<String> RESERVED = Set.of("x-user-id", "x-user-role", "x-internal-auth");
request.getHeaderNames().asIterator().forEachRemaining(h -> {
    if (!RESERVED.contains(h.toLowerCase())) upstream.header(h, request.getHeader(h));
});
upstream.header("X-User-Id", verified.subject());
upstream.header("X-User-Role", verified.role());
```

- 내부 서비스 쪽 짝: 헤더만 믿지 말고 "게이트웨이에서 왔음"을 증명받는다 — 네트워크 정책, mTLS, 또는 게이트웨이가 서명한 짧은 수명 토큰(12번).
- Azure 아키텍처 센터 Gateway Offloading도 백엔드를 게이트웨이 경로로만 열고 전달 헤더를 검증 없이 신원으로 믿지 말라고 한다([api-design/19](../../api-design/19-api-gateway-and-bff/2-summary.md)).

### 3. 내부망 SSRF를 위협 모델에서 먼저 찾는다

- DFD의 ④처럼 "서버가 사용자가 준 URL을 대신 가져오는" 흐름은 신뢰 경계를 거꾸로 건넌다. 외부 입력이 내부 주소로 가는 요청을 만든다.
- 질문: 그 URL이 `169.254.169.254`(클라우드 메타데이터)·`localhost`·사설 대역이면?
- AWS는 IMDSv2를 "열린 방화벽·리버스 프록시·SSRF에 대한 심층 방어"로 설명한다(EC2 사용자 안내서가 링크하는 AWS 보안 블로그 글의 제목). 안내서 본문: 세션 토큰을 `PUT`으로 받아야 하고, `X-Forwarded-For`가 붙은 `PUT`은 거부하며, `PUT` 응답의 홉 제한 기본값은 1이다. 단, 계정 기본값을 IMDSv2로 두면 새 인스턴스의 기본값은 2이고, 홉 제한을 따로 정하지 않았을 때 AMI가 `ImdsSupport: v2.0`이면 2(아니면 1)다. 컨테이너가 IMDS를 쓰면 AWS는 2를 권장한다(안내서 "Configure instance metadata options for new instances").
- 자세한 방어(허용 목록·DNS 재바인딩)는 [security/22-ssrf](../22-ssrf/2-summary.md).

### 4. 산출물은 짧게

```text
  기능: 주문 이미지 첨부        날짜: 2026-10-07(예시)
  흐름 ④ 주문 서비스 → 사용자 제공 URL
    S: -   T: 응답 변조(중간자) → HTTPS만 허용
    I: 내부 주소 응답이 사용자에게 → 내부 대역 차단, 응답 본문 그대로 반환 금지
    D: 느린 서버 → 연결·읽기 타임아웃 2초, 크기 상한 5MB
    E: 메타데이터 접근 → IMDSv2 필수, 허용 목록       담당: … 티켓: …
```

- 길이보다 **갱신**이 중요하다. 흐름이 바뀌는 PR에 DFD 갱신을 리뷰 항목으로 둔다.

## 장애 시나리오와 대처

### 1. 경계 안쪽 입력을 검증 안 함 → 권한 상승 ⚠

- **현상**: 일반 사용자가 관리 API를 호출하는 데 성공한다.
- **보이는 형태**
  - 접근 로그: 같은 토큰 주체가 평소 403이던 `/admin/**`에서 200.
  - 요청 원본(게이트웨이 앞단 로그)에 클라이언트가 보낸 `X-User-Role: admin`·`X-Forwarded-User` 같은 헤더가 있다.
- **원인**: 내부 서비스가 "게이트웨이가 붙였을 것"이라 가정하고 신원 헤더를 믿었다. 게이트웨이가 클라이언트 헤더를 지우지 않았다(실험 E2의 [1]).
- **대처**: 경계에서 예약 헤더 삭제 후 재작성. 내부 서비스는 출처를 증명받는다(네트워크 정책·mTLS·서명 토큰). 위협 모델의 ② 흐름에 S·T·E를 명시.

### 2. 경계 안쪽 서버가 내부 주소를 대신 부름 → 내부망 SSRF ⚠

- **현상**: 이미지 가져오기·웹훅 테스트 같은 기능으로 내부 관리 API나 클라우드 메타데이터의 자격 증명이 노출된다.
- **보이는 형태**: 아웃바운드 요청 로그에 `169.254.169.254`, `127.0.0.1`, 사설 대역 목적지. 사용자 응답에 내부 서비스의 본문.
- **원인**: "서버에서 나가는 요청"을 위협 모델에서 흐름으로 그리지 않았다. 내부망은 신뢰한다는 가정.
- **대처**: DFD에 아웃바운드 흐름을 그리고 E·I를 묻는다. 목적지 허용 목록, IMDSv2 필수화, 이그레스 정책([security/22-ssrf](../22-ssrf/2-summary.md), [network/48](../../network/48-firewalls-and-network-policy/2-summary.md)).

### 3. 위협 모델이 실제와 달라짐 (다이어그램 부패)

- **현상**: 위협 모델 문서는 있는데 사고가 난 경로는 문서에 없다.
- **보이는 형태**: 문서의 마지막 수정이 1년 전. 그 뒤 추가된 큐·서드파티 연동이 그림에 없다.
- **원인**: 한 번 하고 끝냈다. 흐름이 바뀌는 변경에 갱신 트리거가 없다.
- **대처**: "새 외부 연동·새 저장소·권한 모델 변경" PR에 DFD 갱신을 리뷰 항목으로. Cheat Sheet 권고대로 시스템과 함께 유지한다.

### 4. 체크리스트만 통과, 비즈니스 로직 남용

- **현상**: 인젝션·XSS 점검은 통과했는데, 봇이 한정 상품·좌석을 수백 개 선점한다.
- **보이는 형태**: 정상 응답 코드(200)뿐인데 특정 계정·IP의 주문 수가 비정상. 보안 경보는 없다.
- **원인**: STRIDE의 D와 "정상 기능의 비정상 사용"을 묻지 않았다(A04 2021 시나리오 2·3).
- **대처**: "이 기능을 정상 API로 대량 실행하면?"을 위협 질문에 넣는다. 수량 한도·속도 제한([security/28-dos-and-abuse](../28-dos-and-abuse/2-summary.md), [reliability/11](../../reliability/11-rate-limiter/2-summary.md)).

## 핵심 문장

- 위협 모델링은 네 질문이다: 무엇을 만드나, 무엇이 잘못될 수 있나, 무엇을 할 건가, 충분했나.
- 위협은 신뢰 경계를 건너는 흐름에 몰린다. 그래서 먼저 데이터 흐름 다이어그램에 경계를 긋는다.
- STRIDE는 위장·변조·부인·노출·서비스 거부·권한 상승을 묻는 질문 생성기이고, 각각 인증·무결성·부인 방지·기밀성·가용성·인가의 위반이다.
- 경계 안쪽에서 온 값도 "누가 붙였는지"가 증명되지 않으면 검증 전 입력이다.
- 안전하지 않은 설계는 완벽한 구현으로 고칠 수 없다. 필요한 통제가 애초에 없기 때문이다.

## 관련 주제·근거

- 선행: [01-security-principles](../01-security-principles/2-summary.md) — CIA, 완전한 중재, 최소 권한
- 후속(같은 영역 — [영역 표](../README.md))
  - [security/15-access-control-models](../15-access-control-models/2-summary.md) — 객체 수준 인가
  - [security/22-ssrf](../22-ssrf/2-summary.md) — 내부망 SSRF 방어
  - [security/26-security-logging-and-audit](../26-security-logging-and-audit/2-summary.md) — 부인 방지(R)의 증거
  - [security/28-dos-and-abuse](../28-dos-and-abuse/2-summary.md) — 서비스 거부·남용
- 연결
  - [api-design/19-api-gateway-and-bff](../../api-design/19-api-gateway-and-bff/2-summary.md) — 게이트웨이 오프로딩, 전달 헤더 신뢰 금지
  - [network/32-mtls-and-cert-operations](../../network/32-mtls-and-cert-operations/2-summary.md) — 서비스 간 상호 인증
  - [network/48-firewalls-and-network-policy](../../network/48-firewalls-and-network-policy/2-summary.md) — 경계를 네트워크로 강제
  - [engineering-practice/15-security-standards](../../engineering-practice/15-security-standards/2-summary.md) — 위협 모델링은 사람의 리뷰 몫(A06:2025)
  - [data-structure/08-graph](../../data-structure/08-graph/2-summary.md) — DFD를 그래프로
- 1차 출처
  - Threat Modeling Manifesto — 정의, 네 질문, 저자 15인(Adam Shostack 포함) <https://www.threatmodelingmanifesto.org/>
  - Adam Shostack, 『Threat Modeling: Designing for Security』, Wiley, 2014 — 네 질문 틀, STRIDE-per-element(본문 미열람, 장 단위 [?])
  - OWASP Threat Modeling Cheat Sheet — DFD 요소, STRIDE 표, 설계 단계·지속 갱신 <https://cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html>
  - OWASP Top 10 2021 A04 Insecure Design — 설계 vs 구현 결함, refinement 회의, 시나리오 3개 <https://top10.owasp.org/2021/A04_2021-Insecure_Design>
  - OWASP Top 10:2025 목록 — A06:2025 Insecure Design <https://top10.owasp.org/2025/>
  - Microsoft Threat Modeling Tool — STRIDE 범주 정의 <https://learn.microsoft.com/en-us/azure/security/develop/threat-modeling-tool-threats>
  - AWS EC2 사용자 안내서 "Use the Instance Metadata Service" — IMDSv2 세션 토큰, `X-Forwarded-For` 붙은 `PUT` 거부, 홉 제한 기본 1 <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html>, 계정 기본값 IMDSv2·AMI `ImdsSupport: v2.0`이면 기본 2, 컨테이너 권장 2 <https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-IMDS-new-instances.html>
- 실험
  - E2 `Boundary.java` — 127.0.0.1의 게이트웨이 2종(취약·고친 판) + 내부 서비스, 헤더 스푸핑과 경계 우회. OpenJDK 21.0.12(eclipse-temurin:21-jdk), `--network none`, 2026-10-07.
