# engineering-practice/13-build-vs-buy-and-adoption — 직접 만들기 vs SaaS·OSS 도입: 핵심 판별, 총소유비용, 종료 비용, OSS 건강도 — 정리 (힌트)

## 해결하는 문제

"이걸 직접 만들까, 사서 쓸까?"는 양쪽 모두로 틀릴 수 있다.

- 직접 만들어서 틀림: 인증·결제·검색 같은 범용 기능을 자체 구현하다 핵심 기능을 만들 사람이 남지 않는다.
- 사서 틀림: 회사를 남과 다르게 만드는 기능을 SaaS에 맡겼다가, 가격이 오르거나 API가 사라지면 대안이 없다.

쉬운 예: 이사할 때 가구다.

```text
  옷장       ── 어느 집이나 같다 ──> 사서 쓴다. 집을 옷장에 맞춘다
  작업실 책상 ── 내 일의 핵심이다 ──> 맞춤 제작한다. 남과 같은 것으로는 일이 안 된다
  렌털 가구   ── 초기 비용 작다 ────> 대신 매달 내고, 반납·교체 조건을 회사가 정한다
```

똑같은 구조다. 범용 기능은 사고 업무를 거기에 맞추고, 차별화 기능은 직접 만든다. 빌려 쓰면 초기 비용 대신 계속 내는 돈과 빠져나오는 비용이 생긴다.

실무 예:
- 오픈소스로 쓰던 Redis가 7.4부터 BSD 3-Clause가 아닌 RSALv2/SSPLv1 이중 라이선스로 바뀌었다(redis.io 2024-03-20). 경쟁 관계의 관리형 서비스를 하던 회사는 새 버전을 그냥 쓸 수 없게 됐다(장애 3).
- 무료 플랜에 올려 둔 사내 도구들이 Heroku의 공지(2022-08-25)대로 2022-11-28부터 무료 플랜 중단 대상이 됐다. 옮길 계획이 없던 팀이라면 급히 이전해야 했다. 공지 날짜는 사실이고, 팀의 급한 이전은 예시 상황이다(장애 2).

## 동작·원리

### 1. 첫 질문 — 이 기능이 차별화 요소인가

Fowler "UtilityVsStrategicDichotomy"(2010-07-29)의 주장이다.

```text
                 범용(utility)                      전략(strategic)
  예             급여 계산 — "그냥 돌아가면 됨"         남보다 잘하는 이유가 되는 기능
  가장 큰 위험    파국적 오류(하수관 파열, 급여 누락)    경쟁자보다 늦는 것
  비용           낮을수록 좋다                        기회비용이 개발비보다 훨씬 크다
  만들기/사기     패키지를 산다. 업무를 소프트웨어에 맞춘다  직접 만든다. 남과 같은 것은 차별화를 막는다
  비율           대부분                               소수 ("80/20보다 95/5에 가까울 수도")
```

- 구분 기준은 기술의 성질이 아니라 **그 기능이 사업에서 차별화 요소인가**다.
- 고정된 구분이 아니다. 전략이던 것이 시간이 지나 범용이 되고, 드물게 범용이 전략이 된다.
- 흔한 실수 두 가지(Fowler): 구분 자체를 모르는 것, 그리고 너무 많은 것을 전략이라 여기는 것. 범용 패키지를 사 놓고 거액을 들여 커스터마이징하는 것도 "똑같이 낭비"라고 쓴다.
- 같은 판단을 DDD 용어(핵심·지원·일반 서브도메인)로 정리한 것은 [domain-modeling/17-subdomains](../../domain-modeling/17-subdomains/2-summary.md)에 있다. 이 노트는 그 판단 뒤의 **비용·위험 계산**을 다룬다.
  - 흔한 오해: "직접 만들면 공짜, 사면 비싸다". 직접 만들어도 유지보수·온콜·보안 패치를 계속 낸다. 아래 실험에서 초기 개발비만 비교하면 직접 만들기가 싸 보였지만, 3년 총비용은 반대였다.

### 2. 총소유비용 — 보이는 것과 안 보이는 것

```text
           직접 만들기                          사서 쓰기(SaaS)
   보임 ┌─────────────────┐            보임 ┌─────────────────┐
        │ 초기 개발        │                 │ 구독료           │
  ------└─────────────────┘------ 수면 ------└─────────────────┘------
   안 보임 유지보수(버그·요구 변경)        안 보임 연동 개발
         온콜·장애 대응                         벤더 관리·설정
         보안 패치·의존성 업그레이드              가격 인상
         인프라·모니터링                        종료 비용(데이터 반출·이관)
         채용·인수인계(아는 사람이 떠남)          벤더 장애 때 할 수 있는 일이 적음
```

- *총소유비용(TCO, total cost of ownership)*: 도입부터 폐기까지 드는 모든 비용의 합. 구매가·초기 개발비는 그 일부다.
- *종료 비용(exit cost)*: 지금의 선택에서 빠져나와 다른 것으로 옮기는 비용. 데이터 반출, 연동 코드 교체, 사용자 이전, 계약 해지 조건.
- *벤더 종속(vendor lock-in)*: 종료 비용이 커서 조건이 나빠져도 옮기지 못하는 상태.
- 계산 기간을 정한다(예: 3년). 기간이 짧으면 초기 비용이, 길면 운영 비용이 지배한다.
- 비용 추정 자체의 불확실성은 [12-estimation-and-planning](../12-estimation-and-planning/2-summary.md)에서 다룬다.

### 3. 종속의 원천과 줄이는 법

```text
  우리 코드 ──> [포트: 우리 언어의 인터페이스] ──> [어댑터: 벤더 SDK 호출] ──> 벤더
                     ▲ 핵심 코드는 이것만 안다          ▲ 바꿀 때 여기만 다시 쓴다
```

- 종속은 여러 층에서 생긴다: 데이터 형식·반출 가능성, API 표면, 벤더 고유 기능, 계약 조건.
- 코드 층의 종속은 벤더 모델을 우리 모델로 번역하는 계층으로 줄인다([domain-modeling/19-anti-corruption-layer](../../domain-modeling/19-anti-corruption-layer/2-summary.md)).
- 데이터 층의 종속은 "데이터를 실제로 내보내 다른 곳에 넣어 보는" 리허설로만 확인된다. 반출 기능이 있다는 문서와 실제 이관 가능성은 다르다.

### 4. OSS 도입 — 건강도와 라이선스

**건강도.** OpenSSF Scorecard는 저장소를 자동 점검해 항목마다 0~10점을 준다(ossf/scorecard README, docs/checks.md).

| 점검 예 | 위험 등급 | 무엇을 보나 |
|---|---|---|
| Maintained | High | 보관(archived)이면 최저점. 최근 90일간 주 1회 이상 커밋이면 최고점. 90일 미만 프로젝트는 판정 불가 |
| Code-Review | High | 병합 전 사람 리뷰를 하는가(최근 ~30커밋의 GitHub/GitLab 승인, 병합자≠커미터인 암묵 리뷰, Prow·Gerrit 표식) |
| Vulnerabilities | High | 고치지 않은 알려진 취약점(OSV 서비스) |
| Contributors | Low | 기여 5회 이상인 기여자의 회사·GitHub 조직이 3곳 이상이면 최고점. docs/checks.md는 "최근 30커밋"이라 쓰지만, main 소스는 GitHub 기여자 목록 API 한 페이지(기본 30명, 기여 많은 순)를 센다 — 그래서 아래 실험에 59곳 같은 값이 나온다. v5.2.0부터 CODEOWNERS 사용자도 목록에 합쳐진다(기여 0회로 들어가 5회 기준에는 안 걸린다) |
| License | Low | 라이선스 파일이 있나 |

- 집계 점수 = 항목 점수의 **위험 가중 평균**이다. Critical 10, High 7.5, Medium 5, Low 2.5(README "Aggregate Score").
- README "Project Non-Goals"가 스스로 밝히는 한계: 점검은 휴리스틱이라 거짓 양성·거짓 음성이 있다. 특히 집계 점수는 그 저장소가 **무엇을 하고 무엇을 안 하는지 알려 주지 않는다.** 같은 점수에 이르는 길이 여럿이다.
- Maintained 문서도 덧붙인다: 짝수 판정 같은 작은 유틸리티는 활동이 없어도 문제가 아닐 수 있다. 낮은 점수는 "더 조사하라"는 신호다.
- 공급망 위험 전반(SBOM·서명·재현 빌드)은 [security/25 supply-chain-security](../../security/25-supply-chain-security/2-summary.md).

**라이선스 변경.** OSS가 계속 같은 조건이라는 보장은 없다.

| 날짜 | 무엇 | 출처 |
|---|---|---|
| 2023-08-10 | HashiCorp: 이후 릴리스를 MPL 2.0 → BSL(BUSL) 1.1. 추가 사용 허가(Additional Use Grant): 운영 사용은 허용하되, HashiCorp 유료 버전과 경쟁하려고 제3자에게 호스팅·내장 형태로 제공하는 것은 제외. 내부 사용, 다른 HashiCorp 도구로 경쟁 제품을 만드는 것은 막지 않는다고 FAQ가 밝힌다(해석·법률 자문 아님). API·SDK·대부분 라이브러리는 MPL 2.0 유지 | HashiCorp 블로그·라이선스 FAQ |
| 2023-09-20 | Linux Foundation이 OpenTofu 출범 발표 — MPLv2 Terraform의 오픈소스 후계(라이선스 변경에 대한 커뮤니티 대응) | Linux Foundation 보도자료 |
| 2024-03-20 | Redis: 7.4부터 BSD 3-Clause → RSALv2/SSPLv1 이중 라이선스. 둘 다 OSI 승인 라이선스가 아니라고 Redis 스스로 밝힘. 이전 버전은 BSD 그대로 | redis.io 블로그·FAQ |
| 2024-03-28 | Linux Foundation이 Redis 7.2.4 기반 BSD 포크 Valkey 결성 발표 | Linux Foundation 보도자료 |
| 2025-05-01 | Redis 8: AGPLv3를 세 번째 선택지로 추가(RSALv2·SSPLv1·AGPLv3 중 택일) | redis.io 블로그 |

- *OSI 승인 라이선스*: Open Source Initiative가 오픈소스 정의(OSD)를 충족한다고 승인한 라이선스. *소스 공개(source-available) 라이선스*: 소스는 공개하지만 사용 조건(예: 경쟁 관리형 서비스 금지)이 붙어 OSI 정의를 충족하지 않는 라이선스.
- 두 회사 모두 **변경은 소급하지 않는다**고 밝혔다. 이미 받은 버전은 옛 라이선스로 계속 쓸 수 있다. 문제는 그 뒤의 보안 패치·새 기능이다.
- 이 표는 사실(공지 날짜·내용)이다. 자기 회사가 영향을 받는지는 라이선스 원문과 사용 형태에 달렸다 — 해석·법률 자문 아님. 라이선스 기준 일반은 [17-legal-standards](../17-legal-standards/2-summary.md).

### 실험 A: 3년 TCO와 가중합 행렬 — 무엇을 넣느냐가 결론을 바꾼다

**모든 수치는 예시 가정이다.** 실제 가격·인건비가 아니다. 단위는 만원, 1인월 = 1,000.

| 항목 | 직접 만들기 | 사서 쓰기(SaaS) |
|---|---|---|
| 초기 | 개발 6인월 | 연동 1인월 |
| 매년 | 유지보수 0.3명 + 온콜·보안 패치 0.1명 + 인프라 600 | 구독 월 300 + 벤더 관리 0.05명 |
| 종료 | — | 3년 뒤 이관 3인월 |

```java
static double buy(boolean full, double yearlyIncrease, boolean exit) {
    double sub = 0;
    for (int y = 0; y < YEARS; y++) sub += 300 * 12 * Math.pow(1 + yearlyIncrease, y);  // 구독료, 매년 인상
    if (!full) return sub;
    return sub + 1 * PM + 0.05 * 12 * PM * YEARS + (exit ? 3 * PM : 0);                // 연동 + 관리 + 종료
}
// 가중합: Σ(가중치 × 점수) / Σ가중치 — 차별화 가중치를 1·3·5로 바꿔 가며 1위가 바뀌는지 본다
static double score(Map<String, Integer> s, List<Criterion> cs) {
    double sum = 0, w = 0;
    for (Criterion c : cs) { sum += c.weight() * s.get(c.name()); w += c.weight(); }
    return sum / w;
}
```

행렬의 점수(1~5, 예시)와 가중치: 차별화(1·3·5로 바꿈) · TCO 3 · 출시 속도 2 · 종료 용이성 2 · 공급자 건강도 2 · 보안·규정 3.

| | 차별화 | TCO | 출시 속도 | 종료 용이 | 공급자 건강 | 보안·규정 |
|---|---|---|---|---|---|---|
| 직접 구현 | 5 | 2 | 2 | 5 | 3 | 2 |
| SaaS | 2 | 4 | 5 | 2 | 4 | 4 |
| OSS 자체 운영 | 3 | 3 | 3 | 4 | 3 | 3 |

(실험, eclipse-temurin:21-jdk(OpenJDK 21.0.12) `java Bvb.java`, `--network none --cpus=1`, 2026-10-05 — 결정적 계산)

```text
== 1. 3년 TCO (만원, 예시 가정)
  좁게 본 비교   직접: 초기 개발    6,000   구매: 구독료   10,800
  전체 TCO       직접:   22,200   구매:   13,600   구매+종료비용:   16,600
  구독료 연 20% 인상 시  구매+종료비용:   18,904
  구독료 연 50% 인상 시  구매+종료비용:   22,900
  구독료 연 80% 인상 시  구매+종료비용:   27,544
  손익분기: 구독료가 매년 약 46% 오르면 구매(+종료비용)가 직접 만들기보다 비싸진다
== 2. 가중합 행렬 (점수 1~5, 예시)
  차별화 가중치 1 →  직접 구현 2.85  SaaS 3.69  OSS 자체운영 3.15   ⇒ SaaS
  차별화 가중치 3 →  직접 구현 3.13  SaaS 3.47  OSS 자체운영 3.13   ⇒ SaaS
  차별화 가중치 5 →  직접 구현 3.35  SaaS 3.29  OSS 자체운영 3.12   ⇒ 직접 구현
```

- 관찰 1: 초기 개발비만 보면 직접(6,000)이 구독료(10,800)보다 싸 보인다. 유지보수·온콜·인프라를 넣으면 직접 22,200 vs 구매 13,600으로 뒤집힌다.
- 관찰 2: 종료 비용(3,000)을 넣어도 이 가정에서는 구매가 싸다. 구독료가 매년 약 46% 넘게 오르면 뒤집힌다. 손익분기점을 알면 "어느 정도 인상까지 견딜 수 있나"를 미리 말할 수 있다.
- 관찰 3: 행렬의 1위는 차별화 가중치에 따라 SaaS → 직접 구현으로 바뀐다. 가중치 5에서 3.35 vs 3.29는 사실상 동점이다. 가중합은 **결정을 대신하지 않는다.** 어떤 가정이 결론을 뒤집는지 드러내는 도구다.
- 해석: 차별화 가중치를 크게 주는 것이 맞는지는 1절의 질문(이것이 차별화 요소인가)에 달렸다. 숫자가 그 질문을 대신하지 못한다.

### 실험 B: Scorecard 공개 API로 OSS 건강도 보기

공개 API(`api.securityscorecards.dev`, 인증 없음)에서 결과를 받아, 집계 점수를 README의 가중치 규칙으로 다시 계산했다.

```js
const W = { Critical: 10, High: 7.5, Medium: 5, Low: 2.5 };      // README "Aggregate Score"
let num = 0, den = 0;
for (const c of r.checks) if (c.score >= 0) {                    // -1 = 판정 불가 → 제외
  num += W[RISK[c.name]] * c.score; den += W[RISK[c.name]];      // RISK = docs/checks.md 의 Risk 칸
}
```

(실험, Node 18.19.1 내장 fetch, 2026-10-05 조회 — API 값은 스캔마다 바뀐다)

```text
== github.com/junit-team/junit5  스캔 2025-06-22  API 점수 8.3  재계산 8.3
   Maintained        10  30 commit(s) and 25 issue activity found in the last 90 days -- score 
   Code-Review        0  Found 0/27 approved changesets -- score normalized to 0
   License           10  license file detected
   Vulnerabilities   10  0 existing vulnerabilities detected
   Contributors      10  project has 59 contributing companies or organizations
== github.com/junit-team/junit-framework  스캔 2026-10-04  API 점수 7.9  재계산 7.9
   Maintained        10  30 commit(s) and 6 issue activity found in the last 90 days -- score n
   Code-Review        4  Found 5/12 approved changesets -- score normalized to 4
   License           10  license file detected
   Vulnerabilities   10  0 existing vulnerabilities detected
   Contributors      10  project has 62 contributing companies or organizations
== github.com/google/guava  스캔 2026-10-04  API 점수 8.8  재계산 8.8
   Maintained        10  30 commit(s) and 16 issue activity found in the last 90 days -- score 
   Code-Review        0  Found 1/27 approved changesets -- score normalized to 0
   License           10  license file detected
   Vulnerabilities   10  0 existing vulnerabilities detected
   Contributors      10  project has 11 contributing companies or organizations
== github.com/request/request  스캔 2026-09-28  API 점수 3.6  재계산 3.6
   Maintained         0  0 commit(s) and 0 issue activity found in the last 90 days -- score no
   Code-Review        7  Found 20/28 approved changesets -- score normalized to 7
   License           10  license file detected
   Vulnerabilities  undefined  
   Contributors     undefined
```

- 관찰 1: 네 저장소 모두 재계산이 API 점수와 같았다. 집계 = 위험 가중 평균(판정 불가 −1 제외)이 맞다.
- 관찰 2 — 낡은 데이터: `junit-team/junit5`는 지금 `junit-team/junit-framework`로 옮겨졌다(GitHub이 새 주소로 넘겨준다). 옛 이름의 결과는 2025-06-22 스캔에 멈춰 있었고 점수도 달랐다(8.3 vs 7.9). 조회 결과의 스캔 날짜와 저장소 이름부터 확인해야 한다.
- 관찰 3 — 휴리스틱의 한계: Guava는 Code-Review 0이다. 이 점검은 저장소에 남은 리뷰 흔적(GitHub/GitLab 승인, 병합자≠커미터, Prow·Gerrit 표식)을 센다(docs/checks.md). 이런 흔적이 남지 않는 곳에서 리뷰하는 프로젝트는 낮게 나올 수 있다. Guava의 실제 리뷰 방식은 이 노트에서 확인하지 않았다 `[?]`. README가 밝힌 거짓 음성의 예로 읽는다.
- 관찰 4 — 버려진 의존성: request는 Maintained 0, 집계 3.6이다. npm 레지스트리에서 마지막 버전 2.88.2(2020-02-11)에 "request has been deprecated" 표시가 있다(레지스트리 API로 확인). 저장소는 보관(archived) 상태가 아니었다(GitHub API `archived: false`). Vulnerabilities·Contributors 항목은 결과에 없었다.

## 쓰이는 자료구조·알고리즘

- **가중합(weighted sum)과 민감도 분석** — 기준별 점수 × 가중치의 합. 가중치를 훑어 1위가 바뀌는 지점을 찾는다(실험 A의 차별화 가중치 1·3·5).
- **손익분기 탐색** — 비용 함수 두 개가 교차하는 매개변수(구독료 인상률)를 찾는다. 실험은 1%씩 올리는 선형 탐색을 썼다. 단조 함수라 이분 탐색도 된다.
- **위험 가중 평균** — Scorecard 집계 점수. 판정 불가(−1) 항목은 분자·분모 모두에서 뺀다.
- **의존성 그래프** — 하나를 도입하면 그것의 전이 의존성까지 들어온다. 건강도·라이선스는 그래프 전체에 대해 봐야 한다(의존성 해석은 language/19-modules-and-dependency-resolution — [language 영역 표](../../language/README.md), 미작성).

## 적용 — 풀어나가는 법

### 1. 순서

1. **차별화 질문**: 이 기능이 우리가 남보다 잘해야 하는 이유인가? (Fowler 범용/전략, [domain-modeling/17](../../domain-modeling/17-subdomains/2-summary.md))
2. **선택지 나열**: 직접 구현 / SaaS / OSS 자체 운영 / OSS + 상용 지원.
3. **TCO 표**: 같은 기간(예: 3년)으로 초기·매년·종료 비용을 채운다. 온콜·보안 패치·업그레이드를 빼먹지 않는다.
4. **종료 계획**: 데이터를 어떤 형식으로 뺄 수 있나? 실제로 빼서 다른 곳에 넣어 보았나? 계약 해지 조건은?
5. **OSS라면 건강도·라이선스**: Scorecard(스캔 날짜·저장소 이름 확인), 최근 릴리스, 유지보수자 수, 라이선스 종류와 최근 변경 이력.
6. **가중합 행렬과 민감도**: 어떤 가정이 결론을 뒤집는지 적는다.
7. **결정 기록**: 이유·가정·재검토 조건(예: "구독료 연 40% 이상 인상 시 재검토")을 ADR로 남긴다([software-design/47](../../software-design/47-architecture-decision-records/2-summary.md)).

### 2. 코드 — 벤더를 포트 뒤에 둔다 (Java)

```java
// 우리 언어의 포트 — 핵심 코드는 이것만 안다
public interface IdentityProvider {
    AuthResult verify(String token);
    void revokeSessions(UserId userId);
}

// 어댑터 — 벤더를 바꿀 때 이 클래스만 다시 쓴다
final class VendorXIdentityProvider implements IdentityProvider {
    private final VendorXClient client;   // 벤더 SDK
    VendorXIdentityProvider(VendorXClient client) { this.client = client; }

    @Override public AuthResult verify(String token) {
        var r = client.introspect(token);                          // 벤더 모델
        return r.active() ? AuthResult.ok(new UserId(r.subject())) // → 우리 모델로 번역
                          : AuthResult.rejected(r.reason());
    }
    @Override public void revokeSessions(UserId userId) { client.logoutAll(userId.value()); }
}
```

- 이 경계가 있어도 데이터(사용자·비밀번호 해시·감사 로그)의 종속은 남는다. 반출 리허설로 따로 확인한다.

### 3. 진단 명령

```sh
# OSS 건강도 — 스캔 날짜·저장소 이름부터 본다
curl -s https://api.securityscorecards.dev/projects/github.com/<owner>/<repo>
# npm 패키지가 폐기(deprecated) 표시됐나 — 최신 버전의 deprecated 필드
curl -s https://registry.npmjs.org/<패키지> | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{const r=JSON.parse(s),v=r["dist-tags"].latest;console.log(v,r.versions[v].deprecated||"-",r.time[v])})'
# GitHub 저장소가 보관됐나
curl -s https://api.github.com/repos/<owner>/<repo> | grep -E '"archived"|"pushed_at"'
```

## 장애 시나리오와 대처

### 1. 범용 기능(인증·결제·검색)을 자체 구현 → 핵심 인력 소진 (⚠ 커리큘럼)

- 현상: 1년째 자체 로그인·MFA·비밀번호 재설정을 고치는 중이다. 정작 차별화 기능의 로드맵은 밀렸다.
- 보이는 형태: 스프린트 대부분이 보안 패치·표준 대응(새 인증 방식, 규정 변경)이다. 핵심 개발자가 온콜에 묶인다.
- 원인: 초기 개발비만 비교했다(실험 A의 "좁게 본 비교"). 유지보수·온콜·보안 패치가 빠졌다.
- 대처: 전체 TCO로 다시 계산한다. 범용이면 사서 포트 뒤에 두고, 업무를 제품에 맞춘다(Fowler). 같은 장애를 서브도메인 관점에서 본 것은 [domain-modeling/17](../../domain-modeling/17-subdomains/2-summary.md) 장애 1.

### 2. 핵심 차별화 기능을 SaaS에 의존 → 가격 인상·API 폐기 때 대안 없음 (⚠ 커리큘럼)

- 현상: 추천 엔진을 SaaS에 맡겼다. 벤더가 가격을 크게 올리고 쓰던 API 버전을 폐기한다고 공지했다.
- 보이는 형태: 공지된 기한 안에 이관해야 한다. 우리 코드 곳곳에 벤더 SDK 타입이 퍼져 있다. 데이터 반출 형식이 벤더 고유다.
- 원인: 차별화 기능을 남과 같은 도구에 맡겼다. 종료 계획이 없었다. 벤더 조건이 바뀐 실제 예로는 Heroku의 무료 플랜 중단(2022-08-25 공지, 2022-11-28부터)이 있다.
- 대처
  - 차별화 기능은 직접 만드는 쪽으로 다시 본다(Fowler: 남과 같은 소프트웨어는 차별화 능력을 해친다).
  - 당장은 포트·어댑터로 벤더 SDK를 한곳에 가둔다. 데이터 반출 리허설을 한다.
  - 결정 기록에 재검토 조건(가격·API 수명)을 적어 둔다.

### 3. OSS 라이선스 변경 후 대응 불가 (⚠ 커리큘럼)

- 현상: 의존하던 OSS의 다음 버전이 소스 공개 라이선스로 바뀌었다. 우리 사용 형태(예: 고객에게 관리형으로 제공)가 새 조건에 걸릴 수 있다.
- 보이는 형태: 라이선스 점검 도구가 새 버전에서 경고를 낸다. 보안 패치가 새 라이선스 버전에만 나온다.
- 원인: 라이선스를 도입 때 한 번만 봤다. 변경을 감시하지 않았고 대체 경로가 없었다. 실제 사례: HashiCorp(2023-08-10, MPL → BSL), Redis(2024-03-20, 7.4부터 BSD → RSALv2/SSPLv1).
- 대처
  - 당장: 옛 라이선스 버전에 고정한다(두 회사 모두 소급하지 않는다고 밝힘). 보안 패치 공급이 언제까지인지 확인한다. Redis는 BSD 버전에 치명적 보안 패치를 Redis Community Edition 9.0 출시 때까지 백포트한다고 FAQ에 적었다.
  - 대체 경로를 평가한다: 포크(OpenTofu, Valkey), 상용 라이선스, 다른 제품. 이후 원래 프로젝트가 조건을 다시 바꾸기도 한다(Redis 8의 AGPLv3 추가, 2025-05-01).
  - 의존성 라이선스를 CI에서 계속 확인한다([17-legal-standards](../17-legal-standards/2-summary.md)).
  - 영향 판단은 법무와 원문으로 한다 — 이 노트는 해석·법률 자문 아님.

### 4. 범용 패키지를 사 놓고 대규모 커스터마이징

- 현상: ERP를 샀는데 우리 업무에 맞추느라 커스터마이징 비용이 직접 개발비를 넘었다. 버전 업그레이드도 못 한다.
- 원인: 범용 기능인데 업무를 바꾸지 않고 소프트웨어를 바꿨다. Fowler는 이것을 "똑같이 낭비"라고 쓰고, 범용 기능은 패키지를 사서 **업무 절차를 소프트웨어에 맞추라**고 권한다(정치적으로 어렵다는 것도 인정한다).
- 대처: 커스터마이징 요구마다 "이것이 차별화 요소인가"를 묻는다. 아니면 업무를 바꾼다. 맞으면 그 부분은 패키지 밖에서 직접 만든다.

### 5. Scorecard 점수 하나로 도입·거절

- 현상: "집계 7점 미만 금지" 규칙 때문에 성숙한 라이브러리가 거절되고, 이름이 바뀐 저장소의 옛 결과로 승인이 났다.
- 보이는 형태: 실험 B에서 옛 이름(junit5)은 2025-06-22 스캔의 8.3, 새 이름은 7.9였다. Guava의 Code-Review는 0이었다.
- 원인: 집계 점수는 무엇을 하고 안 하는지 알려 주지 않는다(README Non-Goals). 점검은 휴리스틱이다.
- 대처: 스캔 날짜·저장소 이름을 확인한다. 집계 대신 우리에게 중요한 개별 항목(Maintained, Vulnerabilities, 보관 여부)을 정책으로 본다. 낮은 점수는 거절 사유가 아니라 "조사하라"는 신호로 쓴다(Maintained 문서의 권고).

## 핵심 문장

- 첫 질문은 "이 기능이 차별화 요소인가"다. 범용은 사고 업무를 맞추고, 차별화는 직접 만든다(Fowler 2010). 대부분은 범용이다.
- 직접 만들기의 비용은 초기 개발비가 아니라 유지보수·온콜·보안 패치를 포함한 TCO다. 실험 가정에서 초기비만 보면 직접(6,000)이 쌌지만 3년 TCO는 직접 22,200 vs 구매 13,600이었다.
- 사서 쓰기의 숨은 비용은 가격 인상과 종료 비용이다. 손익분기(실험: 연 약 46% 인상)를 알면 재검토 조건을 미리 적을 수 있다.
- 가중합 행렬은 결정을 대신하지 않는다. 어떤 가중치가 결론을 뒤집는지 보여 준다.
- OSS도 조건이 바뀐다. HashiCorp(2023)·Redis(2024)는 이후 버전의 라이선스를 바꿨고, 이전 버전에는 소급하지 않았다.
- Scorecard 집계는 위험 가중 평균이다. 스캔 날짜·저장소 이름을 확인하고 개별 항목을 본다.

## 관련 주제·근거

- 선행
  - [12-estimation-and-planning](../12-estimation-and-planning/2-summary.md) — 비용 추정의 불확실성
  - [domain-modeling/17-subdomains](../../domain-modeling/17-subdomains/2-summary.md) — 핵심·지원·일반 분류
  - [security/25-supply-chain-security](../../security/25-supply-chain-security/2-summary.md)
- 후속·연결
  - [domain-modeling/19-anti-corruption-layer](../../domain-modeling/19-anti-corruption-layer/2-summary.md) — 벤더 모델 번역 계층
  - [software-design/47-architecture-decision-records](../../software-design/47-architecture-decision-records/2-summary.md) — 결정과 재검토 조건 기록
  - [10-technical-debt](../10-technical-debt/2-summary.md) — 직접 만든 것의 유지 비용
  - [17-legal-standards](../17-legal-standards/2-summary.md) (라이선스·개인정보)
- 글·문서
  - Martin Fowler, "UtilityVsStrategicDichotomy"(2010-07-29) <https://martinfowler.com/bliki/UtilityVsStrategicDichotomy.html>
  - OpenSSF Scorecard README(Aggregate Score 가중치, Project Non-Goals)·docs/checks.md(항목별 Risk, Maintained·Contributors 기준)·소스 `checks/raw/contributors.go`·`clients/githubrepo/contributors.go`·`probes/contributorsFromOrgOrCompany/impl.go`(main, 2026-10-05 확인)·v5.2.0 릴리스 노트(CODEOWNERS) <https://github.com/ossf/scorecard> · API <https://api.securityscorecards.dev/> · <https://securityscorecards.dev/>
  - HashiCorp, "HashiCorp adopts Business Source License"(2023-08-10) <https://www.hashicorp.com/en/blog/hashicorp-adopts-business-source-license> · 라이선스 FAQ("The license change is not retroactive") <https://www.hashicorp.com/license-faq> · BSL 원문의 Additional Use Grant <https://www.hashicorp.com/en/bsl> · FAQ 갱신 글(내부 사용·다른 도구로 경쟁 제품 개발) <https://www.hashicorp.com/en/blog/hashicorp-updates-licensing-faq-based-on-community-questions>
  - Linux Foundation, "Linux Foundation Launches OpenTofu"(2023-09-20) <https://www.linuxfoundation.org/press/announcing-opentofu> · "Linux Foundation Launches Open Source Valkey Community"(2024-03-28) <https://www.linuxfoundation.org/press/linux-foundation-launches-open-source-valkey-community>
  - Redis, "Redis adopts dual source-available licensing"(2024-03-20, FAQ 포함) <https://redis.io/blog/redis-adopts-dual-source-available-licensing/> · "Redis is now available under the AGPLv3 open source license"(2025-05-01) <https://redis.io/blog/agplv3/>
  - Heroku, "Heroku's Next Chapter"(2022-08-25) <https://www.heroku.com/blog/next-chapter>
- 실험 목록
  - 실험 A: TCO·가중합 — `scratchpad/ep/09/bvb/Bvb.java`, `docker run --rm --name sn-ep-w09-bvb ... eclipse-temurin:21-jdk java Bvb.java`. 출력 `bvb-out.txt`.
  - 실험 B: Scorecard — `scratchpad/ep/09/bvb/scorecard.js`(Node 18.19.1), 2026-10-05 조회. 출력 `scorecard-out.txt`. 보조 확인: npm 레지스트리 API(request 2.88.2 deprecated), GitHub API(`archived: false`).
