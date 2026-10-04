# web-platform/24-web-incidents — 정답

## 정답

### 1. 실린 스크립트는 페이지의 권한으로 돈다

- `<script src>`로 실은 코드는 출처가 어디든 **그 페이지의 출처로** 실행된다. 그래서 같은 DOM(결제 폼)·같은 저장소(localStorage, HttpOnly가 아닌 쿠키)를 본다([06-1](../06-browser-storage/2-summary.md)).
- 막는 것: 페이지가 **다른 출처의 응답을 읽는 것**(CORS가 허락하지 않으면 — [05](../05-fetch-from-browser/2-summary.md)).
- 막지 않는 것: 페이지가 **스스로 실은 남의 코드**가 페이지를 읽고, 다른 곳으로 보내는 것(보내기는 CSP로 좁힌다).

### 2. BA 사건의 사실

| 항목 | 값 | 출처 |
|---|---|---|
| 공격 시작 | 2018-06-22, 협력사(Swissport) 직원 계정으로 Citrix 원격 접속 게이트웨이 진입 | ICO 1.2·3.4~3.6 |
| 변조 코드 동작 | 2018-08-21 ~ 09-05, 15일 | ICO 3.25 |
| 발견 | 2018-09-05 제3자가 britishairways.com → BAways.com 전송을 알림. 90분 안에 무력화, 20분 뒤 URL 경로 차단 | ICO 3.26 |
| 영향 | 사건 전체(웹 변조 + 평문 카드 로그 접근)로 약 429,612명의 정보에 접근했을 가능성(이름·주소·카드·CVV 244,000 / 카드·CVV 77,000 / 카드 번호 108,000 등) | ICO 4.1 |
| 과징금 | 예고 £183.39m(2019-07-04) → 최종 £20m(2020-10-16) | ICO 5.3·1.7 |

- "22줄"·"Modernizr 2.6.2"·`mouseup`/`touchend`·`paymentForm` 직렬화는 RiskIQ 분석(2018-09-11, 보안 업체 — 2차)에서 왔다. ICO 원문은 "editing of a Javascript file"이라고만 쓰고 구체 부분은 가려져 있다.

### 3. 15일 동안 안 드러난 이유와 ICO의 대책

- 변조가 사용자 흐름을 깨지 않았다. ICO 3.25: "a copy was sent to the Attacker, without interrupting the normal BA booking and payment procedure." 에러율·결제 성공률 같은 가용성 지표에 아무것도 안 보인다(23번 "예외 없는 장애").
- ICO 6.92가 든 대책: **file integrity monitoring** — 코드 변경을 감지해 알린다.
  - 막는 것(정확히는 줄이는 것): 변조를 모른 채 지나가는 기간.
  - 못 막는 것: 변조 자체. 원문도 "While it does not stop an attacker from changing the code, it allows the organisation to detect that changes have been made"라고 쓴다.
- 해석: 변조 대상이 1st party 파일이라 공격자가 HTML의 SRI 해시까지 고칠 수 있었다면 SRI로는 부족하다. 서버 쪽 변경 감지와 `connect-src` 제한이 더 직접적이다.

### 4. polyfill.io — 바뀐 것은 URL의 주인

- 코드 저장소·버전은 그대로이고, `cdn.polyfill.io` **도메인의 주인**이 2024-02에 바뀌었다(Cloudflare·Sansec). 사이트들의 `<script src>` 한 줄이 그대로 새 주인의 응답을 실행했다.
- Sansec: "The polyfill code is dynamically generated based on the HTTP headers" — 응답이 요청 헤더마다 달라 해시 하나로 고정할 수 없다.
- 실험 24-A: 5번(데스크톱 해시 + 데스크톱) `libLoaded=true`, 6번(데스크톱 해시 + 모바일 UA) `libLoaded=false`, 콘솔 `Failed to find a valid digest …`. 그래서 근본 대책은 빌드 시 필요한 폴리필만 번들에 넣는 자체 호스팅이다([09](../09-js-modules-and-bundling/2-summary.md)).

### 5. 실험 24-A의 네 경우

| 경우 | `libLoaded` | 수집 서버 수신 | 비고 |
|---|---|---|---|
| (가) 변조 + 방어 없음 | true | `{"card":"TEST-0000"}` | 기능 정상인 채 유출 |
| (나) 변조 + SRI | false | 없음 | 콘솔 `Failed to find a valid digest in the 'integrity' attribute …` |
| (다) 변조 + CSP `connect-src 'self'` | true | 없음 | 위반 `connect-src http://127.0.0.1:PORT/c`, 콘솔 `Refused to connect …` |
| (라) 리다이렉트 + CSP `connect-src 'self'` | (이동함) | `LANDING` | 최상위 이동은 `connect-src` 대상 아님 |

- fail closed: 검사에 실패하면 **실행하지 않는 쪽**으로 닫힌다. 변조 코드뿐 아니라 원래 라이브러리 기능도 함께 사라진다(`libLoaded=false`). 유출 대신 기능 장애가 된다.

### 6. 변조 없이 막히는 SRI

- 콘솔: `Subresource Integrity: The resource '…' has an integrity attribute, but the resource requires the request to be CORS enabled to check the integrity, and it is not.`(실험 7번)
- 원인: 다른 출처 스크립트에 `crossorigin` 속성이 없어서 CORS 요청이 아니다. 또는 서버가 `Access-Control-Allow-Origin`을 주지 않는다.
- 고치는 법: `crossorigin="anonymous"`를 붙이고 공급자의 CORS 헤더를 확인한다. 주지 않으면 자체 호스팅한다. 폰트 preload의 `crossorigin` 누락(15-4)과 같은 계열이다.

### 7. Steam 2015 — 10-2와 같은 구조

- Valve 공지: DoS 대응 중 두 번째 캐시 설정이 "incorrectly cached web traffic for authenticated users". 11:50~13:20 PST 사이 약 34k 사용자의 스토어 페이지 요청이 다른 사용자에게 보였을 수 있다.
- 10-2: 쿠키에 따라 다른 HTML을 URL만 키로 공유 캐시에 저장하면 다른 사용자에게 간다(10 실험 `cookie user=bob /me → alice님의 주문 내역`).
- "다른 언어의 첫 화면": 언어도 요청(쿠키·`Accept-Language`)에 따라 응답을 바꾸는 입력이다. 캐시 키에 없으면 먼저 캐시된 언어가 모두에게 간다. 14-4의 `Vary: Accept` 누락과 같은 계열이다(해석).
- 퍼지 확인: 설정을 고쳐도 이미 잘못 저장된 응답은 엣지에 남는다. 07-1에서 서비스 워커 설정을 고쳐도 옛 캐시·waiting 워커가 남는 것과 같은 이유다.

### 8. 결제 페이지 스크립트 순서와 사건 대응

| 단계 | 끊는 경로 |
|---|---|
| 1. 실제 브라우저에서 실리는 스크립트 목록 → 불필요한 것 제거 | BA(수하물 페이지와 같은 라이브러리가 결제 페이지에도 실림), polyfill.io(잊힌 외부 의존) |
| 2. 판이 고정된 외부 스크립트에 SRI + `crossorigin` | 외부 CDN 파일 변조 일반(UA별 생성 서비스에는 부적합 — polyfill.io) |
| 3. 동적 외부 서비스를 자체 호스팅 | polyfill.io |
| 4. CSP를 report-only로 시작해 `script-src`·`connect-src` 강제 | BA(BAways.com으로의 전송), polyfill.io(그 도메인 스크립트 로드 자체) |
| 5. 서버 쪽 변경 감지(배포 산출물 해시와 비교) | BA(1st party 파일 변조 — ICO 6.92) |
| 6. 카드 입력을 결제 대행사 호스팅 필드(다른 출처 iframe)로 | BA(페이지 스크립트가 입력값을 직접 읽는 경로 — 해석) |

- Steam 사건은 스크립트가 아니라 캐시 규칙의 문제라서 이 표 대신 "개인화 응답엔 서버가 `private`/`no-store`, 규칙 변경 시 쿠키 다른 두 계정 비교 검사, 퍼지 경로 연습"으로 끊는다.
