# web-platform/01-browser-architecture — 브라우저 아키텍처: 멀티 프로세스·사이트 격리·렌더러 — 정리 (힌트)

## 해결하는 문제

웹 페이지는 남이 쓴 코드다. 그 코드를 브라우저가 한 프로세스 안에서 전부 돌리면 두 가지가 깨진다.

```text
  단일 프로세스 브라우저 (가상의 예)
  ┌──────────────────────────────────────────────┐
  │ UI · 네트워크 · 탭 A(은행) · 탭 B(광고) · 탭 C  │  ← 한 주소 공간, 한 스레드 묶음
  └──────────────────────────────────────────────┘
   탭 B가 무한 루프 → 전체 UI가 멈춤          (안정성)
   탭 B의 렌더러 버그·Spectre → 탭 A 메모리 읽기 (보안)
```

- Chromium 설계 문서는 출발점을 이렇게 적는다. "렌더링 엔진이 절대 죽거나 멈추지 않게 만드는 것은 거의 불가능하다." 그래서 운영체제처럼 프로세스를 나눠, 페이지 하나가 브라우저 전체를 끌고 가지 못하게 한다(Multi-process Architecture).
  - *렌더러(renderer) 프로세스*: 웹 콘텐츠(HTML·CSS·JS)를 실행하고 그리는 프로세스. Chromium에서는 Blink(렌더링 엔진)와 V8(JS 엔진)이 여기서 돈다.
  - *브라우저 프로세스*: 주소창·탭 같은 UI를 맡고 다른 프로세스를 관리하는 프로세스. 하나다.

쉬운 예: 아파트의 방화 구획이다.
- 한 집에 불이 나도 방화문이 번짐을 막는다. 관리사무소(브라우저 프로세스)는 그 집만 끄고 다시 들인다.

똑같은 구조다.\
프로세스 경계가 방화문이다. 운영체제가 주소 공간을 나눠 주므로(→ [os/04](../../os/04-process-and-lifecycle/2-summary.md)) 한 렌더러의 충돌·멈춤·메모리 오염이 다른 렌더러로 번지지 않는다.

실무 예:
- 한 탭의 스크립트가 무한 루프에 빠지면 그 탭(과 그 렌더러를 함께 쓰는 창)만 "응답 없음"이 된다. 다른 사이트 탭은 계속 반응한다(아래 실험).
- 광고 iframe(다른 사이트)이 렌더러 버그를 노려도, 그 iframe은 별도 프로세스에 있어 바깥 페이지의 DOM이 같은 주소 공간에 없다(사이트 격리). 단 다른 사이트의 이미지·스크립트 같은 하위 리소스는 페이지가 불러오면 그 렌더러로 들어온다(Site Isolation 문서, Limitations).
- 대가는 메모리다. Chromium은 사이트 격리의 메모리 부담을 "Chrome 67 데스크톱에서 모든 사이트를 격리하고 탭을 많이 열었을 때 약 10~13%"로 적었다(Site Isolation 문서, Tradeoffs).

## 동작·원리

### 1. 프로세스 지도 — 누가 무엇을 하나

```text
                       ┌───────────────────────┐
                       │   브라우저 프로세스(1)    │  UI, 탭·내비게이션 관리, 입력을 렌더러로 라우팅
                       └───┬──────────┬────────┘
              Mojo IPC     │          │       Mojo IPC
        ┌──────────────────┘          └───────────────────┐
  ┌─────▼──────────┐   ┌────────────────┐   ┌─────────────▼──┐
  │ 렌더러 (사이트 A) │   │ 렌더러 (사이트 B) │   │ 렌더러 (사이트 C) │   샌드박스 안
  │ 메인 스레드: JS·DOM│   │                │   │ (A 페이지 안의   │
  │ 컴포지터 스레드    │   │                │   │  C iframe)      │
  └───────┬────────┘   └────────────────┘   └────────────────┘
          │ 합성 프레임
  ┌───────▼──────────┐  ┌─────────────────┐  ┌──────────────────┐
  │ Viz(GPU) 프로세스 │  │ 네트워크 서비스    │  │ 스토리지 서비스     │
  │ 모든 렌더러의 프레임 │  │ (렌더러는 직접     │  │                  │
  │ 을 모아 화면에 그림 │  │  소켓을 못 연다)   │  │                  │
  └──────────────────┘  └─────────────────┘  └──────────────────┘
```

- RenderingNG 문서의 역할 분담
  - 브라우저 프로세스는 하나다. UI를 그리고 입력을 알맞은 렌더러로 보낸다.
  - 렌더러 프로세스는 여러 개다. "사이트·탭 조합" 하나의 렌더링·애니메이션·스크롤·입력 라우팅을 맡는다.
  - Viz 프로세스는 하나다. 모든 렌더러의 합성 결과를 모아 GPU로 화면에 그린다.
- 렌더러 안에는 스레드가 여럿이다.
  - *메인 스레드*: 스크립트 실행, DOM, 스타일·레이아웃, HTML 파싱. → [03 이벤트 루프](../03-event-loop/2-summary.md)
  - *컴포지터 스레드*: 입력 처리, 스크롤, 일부 애니메이션. 메인 스레드가 바빠도 스크롤이 굴러가는 이유다. 단 non-passive 터치·휠 리스너가 걸린 영역(non-fast scrollable region)에서는 컴포지터가 메인 스레드의 처리 결과를 기다린다(Inside look at modern web browser, part 4). → [02 렌더링 파이프라인](../02-rendering-pipeline/2-summary.md)
- 렌더러는 네트워크를 "Chromium의 네트워크 서비스를 통해" 쓴다. 파일·화면 접근도 OS 권한으로 막는다(Multi-process Architecture, Sandboxing 절).
  - *샌드박스*: 프로세스가 할 수 있는 시스템 호출·자원 접근을 OS 기능으로 좁힌 실행 환경. 렌더러가 장악돼도 디스크·소켓을 직접 못 만진다.
  - *IPC*: 프로세스 간 통신. Chromium은 Mojo(또는 레거시 IPC)를 쓴다. → [os/30-ipc](../../os/30-ipc/2-summary.md)

### 2. 사이트란 무엇인가 — 격리 단위

```text
  https://shop.example.co.kr:8443/cart
  └┬──┘   └──────┬──────────┘└┬─┘
  scheme      host           port

  출처(origin)  = scheme + host + port          → https://shop.example.co.kr:8443
  사이트(site)  = scheme + 등록 도메인(eTLD+1)   → https://example.co.kr
                  (서브도메인·포트·경로는 무시)
  IP 주소 호스트 = 등록 도메인이 없으므로 호스트 그대로 → http://127.0.0.1
```

- Site Isolation 문서의 정의: 사이트는 "scheme과 등록 도메인(public suffix 포함)이며, 서브도메인·포트·경로는 무시"한다. 예) `https://foo.example.com:8080`의 사이트는 `https://example.com`.
  - *eTLD(effective TLD, public suffix)*: `.com`, `.co.kr`, `github.io`처럼 그 아래에 남이 등록할 수 있는 접미사. Public Suffix List(PSL)가 목록이다.
  - *eTLD+1*: eTLD에 라벨 하나를 더한 것 = 등록 도메인.
- 그래서 **같은 사이트·다른 출처**가 생긴다. `127.0.0.1:P1`과 `127.0.0.1:P2`는 포트가 달라 출처는 다르지만 사이트는 같다.
  - 출처는 보안 정책(SOP·CORS)의 단위다. → security/21 `same-origin-and-cors`(미작성, [security README](../../security/README.md))
  - 사이트는 Chromium이 **프로세스를 나누는** 단위다. Site Isolation 문서가 든 이유는 호환성이다. "`document.domain`을 바꿔 한 사이트의 여러 서브도메인끼리 통신하는 기존 페이지를 깨지 않으려고" 출처 대신 사이트를 쓴다.

### 3. 사이트 격리 — 다른 사이트 문서는 다른 프로세스로

```text
  탭: https://a.test/ (사이트 a.test)
   ├─ <iframe src="https://a.test:8443/x">  같은 사이트 → 부모와 같은 렌더러
   └─ <iframe src="https://ads.example/">   다른 사이트 → 별도 렌더러 (OOPIF)

                 렌더러 #1 [a.test 문서들]      렌더러 #2 [ads.example 문서]
                      ▲                              ▲
                      └──── 브라우저 프로세스가 프레임 트리를 나눠 들고 조율 ────┘
```

- Site Isolation 문서: "다른 사이트 문서는 현재 탭이든, 새 탭이든, iframe이든 항상 다른 프로세스에 넣는다." (데스크톱 Chrome 기준. Android는 아래 조건)
  - *OOPIF(out-of-process iframe)*: 부모 페이지와 다른 프로세스에서 렌더링되는 iframe.
- 동기: Spectre 같은 부채널 공격은 "Chrome에 버그가 없어도" 같은 렌더러 프로세스의 임의 메모리를 읽게 할 수 있다. 다른 사이트 **문서**를 같은 주소 공간에 두지 않는 것이 방어선이다. 다만 페이지가 불러온 다른 사이트의 이미지·스크립트는 렌더러에 들어오고, 민감한 응답을 걸러 내는 CORB(현재 ORB)도 최선 노력 방식이다(Site Isolation 문서, Limitations). 그래서 `Cross-Origin-Resource-Policy`·COOP 헤더를 함께 권한다.
- 연혁(Site Isolation 문서)
  - Chrome 67: Windows·Mac·Linux·Chrome OS에서 모든 사이트에 기본 활성화.
  - Chrome 77: 장악된 렌더러에 대한 방어로 확장. Android는 RAM 2GB 이상 기기에서 "사용자가 로그인하는 사이트"부터.
- 같은 사이트라도 같은 프로세스라는 보장은 없다. RenderingNG 문서: 같은 사이트의 탭·창은 "대개 다른 렌더러 프로세스"에 가지만, 한쪽이 다른 쪽을 연 관계(opener)면 예외다. Multi-process Architecture 문서("Sharing the renderer process" 절)도 `window.open`으로 연 창은 "같은 출처(origin)면 프로세스를 함께 써야 한다"고 적는다. 데스크톱에서 메모리 압박이 크면 관계없는 같은 사이트 탭도 한 프로세스에 묶을 수 있다(RenderingNG).

### 실험: 사이트 격리와 무한 루프의 영향 범위

환경: headless Chrome 151.0.7922.173(`/usr/bin/google-chrome`), Playwright `playwright-core`, Node 20, 로컬 Node `http` 서버 2개(127.0.0.1의 임의 포트 P1·P2), 스로틀링 없음, 2026-10-04.\
프로세스 종류는 CDP `SystemInfo.getProcessInfo`, OOPIF는 `Target.getTargets`의 `type === 'iframe'` 개수로 셌다.

```js
// e01b-oopif.js 핵심 — 시나리오마다 새 브라우저
const cdp = await browser.newBrowserCDPSession();
const page = await browser.newPage();
await page.goto(url); await page.waitForTimeout(500);
const r = (await cdp.send('SystemInfo.getProcessInfo')).processInfo.filter(p => p.type === 'renderer').length;
const oopif = (await cdp.send('Target.getTargets')).targetInfos.filter(t => t.type === 'iframe').length;
```

(실험, headless Chrome 151, 스로틀 없음, 2026-10-04 — 3회 모두 같은 값)

```text
run1 iframe 없음                            renderer=3 OOPIF타깃=0
run1 iframe 127.0.0.1:P2 (같은 사이트, 다른 출처)  renderer=3 OOPIF타깃=0
run1 iframe localhost:P1 (다른 사이트)         renderer=4 OOPIF타깃=1
```

- 포트만 다른 iframe(같은 사이트·다른 출처)은 부모 렌더러에 그대로 있었다. `localhost` iframe(다른 사이트)만 OOPIF가 되어 렌더러가 하나 늘었다.
- 기본값 3은 페이지 하나에 렌더러 3개라는 뜻이 아니다. 시작 직후에는 렌더러가 0개(`GPU, browser, network.mojom.NetworkService, storage.mojom.StorageService`)였고, about:blank 탭 하나를 열자 3개가 됐다. 그중 하나는 `ps`에서 `--top-chrome-webui` 플래그가 붙은 렌더러였다. 나머지의 정체는 이 실험으로 가리지 않았다 [?]. 그래서 **증가분**만 해석한다.

같은 브라우저에서 탭1이 4초 동기 루프에 빠진 동안, 각 문서에 `evaluate(1+1)`을 1.5초 제한으로 보냈다(`e01-processes.js`).

(실험, headless Chrome 151, 스로틀 없음, 2026-10-04 — 3회 같은 판정, 응답 시간 10~13ms(사실 점검 재실행 3회 포함))

```text
   탭1 (루프 중인 문서)                            -> timeout (1502ms)
   팝업 (탭1이 연 같은 사이트, opener 연결)             -> timeout (1501ms)
   탭2 (같은 사이트, 별도 탭)                        -> ok (10ms)
   탭3 (다른 사이트)                              -> ok (11ms)
```

- 루프는 그 문서의 메인 스레드를 잡는다. 같은 메인 스레드(이벤트 루프)를 쓰는 문서만 함께 멈춘다.
- `window.open`으로 연 같은 사이트 팝업은 탭1과 함께 멈췄다. 같은 사이트의 **별도 탭**은 멀쩡했다. 해석: opener로 이어진 같은 사이트 창은 서로 `window` 객체를 동기 접근할 수 있어 같은 이벤트 루프에 있어야 하고, 관계없는 탭은 다른 프로세스에 배정됐다.
  - 이 실험의 팝업은 탭1과 URL이 같아 **같은 출처**이기도 하다. 같은 사이트·다른 출처 팝업은 따로 재지 않았다.

### 4. 충돌과 멈춤 — 브라우저가 보는 것

```text
  렌더러 충돌 ──> 브라우저 프로세스가 프로세스 핸들 신호를 감지
              ──> 그 렌더러를 쓰는 탭·프레임에 통지 ──> "sad tab"/"sad frame"(오류 화면) ──> 새로고침 = 새 렌더러
  렌더러 멈춤 ──> 입력 이벤트 ack가 오지 않음 ──> "페이지 응답 없음" 대화상자(기다리기/종료)
```

- 충돌 경로는 설계 문서에 있다. 브라우저가 프로세스 핸들을 감시하다 신호가 오면 렌더러가 죽은 것으로 보고 "영향받은 탭과 프레임"에 알린다. 사용자는 "sad tab"(iframe이면 "sad frame")을 보며, 새로고침하면 새 렌더러가 만들어진다.
- 멈춤 감지의 구체 조건(몇 초 동안 입력 응답이 없으면 대화상자를 띄우는지)은 이 노트에서 확인하지 못했다 [?].

## 쓰이는 자료구조·알고리즘

- **사이트 → 프로세스 대응표(해시 맵)**: 내비게이션마다 목적지 URL의 사이트를 계산하고, 그 사이트를 맡은 프로세스를 찾거나 새로 만든다. → [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)
- **Public Suffix List 조회 = DAFSA**: Chromium은 PSL을 빌드 때 DAFSA(결정적 비순환 유한 상태 오토마톤, 접미사를 공유하는 압축 트라이) 바이트 배열로 컴파일해 둔다. 호스트를 뒤집어 넣어 가장 긴 공개 접미사를 찾는다(`net/base/registry_controlled_domains/registry_controlled_domain.cc` — `kDafsa`, `effective_tld_names-reversed-inc.cc`, `make_dafsa.py`). → [data-structure/09-trie](../../data-structure/09-trie/2-summary.md)
- **프레임 트리**: 탭 하나의 frame들을 트리로 들고, 노드마다 담당 렌더러를 기록한다. 다른 사이트 노드는 다른 프로세스를 가리킨다.
- **메시지 큐(IPC)**: 프로세스 사이는 메시지로만 통한다. 각 프로세스는 받은 메시지를 자기 이벤트 루프의 태스크로 처리한다. → [data-structure/04-queue-deque](../../data-structure/04-queue-deque/2-summary.md)

## 적용 — 풀어나가는 법

1. **어느 프로세스가 무엇을 쓰는지 본다.**
   - Chrome 메뉴 → 도구 더보기 → 작업 관리자(Windows·Linux 단축키 Shift+Esc). 탭·iframe·서비스별 메모리·CPU가 행으로 나온다.
   - `chrome://process-internals`: 사이트 격리 모드와 프레임별 프로세스 배정을 보여 준다.
   - 자동화: CDP `SystemInfo.getProcessInfo`(위 실험).
2. **멈춤이 우리 페이지 메인 스레드 탓인지 가린다.**
   - 다른 탭·주소창이 반응하면 브라우저 전체가 아니라 그 렌더러의 메인 스레드다. DevTools Performance 패널에서 긴 태스크(빨간 삼각형)를 찾는다. → [03](../03-event-loop/2-summary.md)
3. **다른 사이트 iframe을 쓰면 비용을 계산한다.**
   - OOPIF 하나마다 렌더러가 늘 수 있다(실험: +1). 광고·위젯 iframe이 많은 페이지는 메모리가 커진다.
   - 부모-iframe 통신은 같은 프로세스여도 `postMessage`(비동기)로 설계한다. 다른 사이트 iframe은 어차피 동기 DOM 접근이 SOP로 막힌다.
4. **팝업과 결합을 끊는다.**
   - 결제창 같은 `window.open` 대상은 opener와 같은 이벤트 루프를 공유할 수 있다(실험: 함께 멈춤). `noopener`로 열거나, 응답에 `Cross-Origin-Opener-Policy: same-origin`을 준다. 그러면 opener와 출처가 다르거나 opener의 COOP가 `same-origin`이 아닐 때 브라우징 컨텍스트 그룹이 갈려 `window.opener`가 `null`이 되고 프로세스가 분리될 수 있다(MDN COOP).

```js
// 팝업을 열되 opener 관계를 만들지 않는다
window.open('https://pay.example/checkout', '_blank', 'noopener');
```

5. **보안 가정을 프로세스 경계 위에 두지 않는다.**
   - 사이트 격리는 다른 사이트 사이의 방어선이다. 같은 사이트의 서브도메인끼리(`a.example.com`·`b.example.com`)는 같은 프로세스일 수 있다. 사용자 업로드 콘텐츠는 별도 등록 도메인(예: `usercontent.example.net`)에서 서빙한다.

## 장애 시나리오와 대처

### 1. 한 탭 무한 루프 → 그 렌더러만 "응답 없음" (⚠ 커리큘럼)

- **현상**: 특정 탭이 클릭·스크롤에 반응하지 않는다. 다른 탭은 정상이다.
- **보이는 형태**: "페이지 응답 없음" 대화상자. 작업 관리자에서 그 탭 프로세스 CPU 100%(코어 하나). DevTools를 열면 일시 정지 버튼으로 루프 위치를 볼 수 있다.
- **원인**: 메인 스레드에서 끝나지 않는 동기 코드(조건이 틀린 `while`, 거대한 JSON 동기 처리). 같은 이벤트 루프의 opener 팝업도 함께 멈춘다.
- **대처**: 루프 조건을 고친다. 무거운 계산은 Web Worker로 옮기거나 조각내 양보한다(→ [16 `long-tasks-and-web-workers`](../16-long-tasks-and-web-workers/2-summary.md)). 결제 팝업은 `noopener`·COOP로 분리한다.

### 2. 렌더러 충돌 → "sad tab"

- **현상**: 탭 내용이 오류 화면으로 바뀐다.
- **보이는 형태**: "앗, 이런!" 류 오류 페이지와 오류 코드(예: 메모리 부족). 다른 탭은 살아 있다.
- **원인**: 렌더러 메모리 한도 초과, 렌더러 버그, 확장 프로그램 충돌 [?: 원인별 오류 코드 목록은 미확인].
- **대처**: 메모리 프로파일(DevTools Memory 패널 힙 스냅샷)로 누수를 찾는다(→ [04](../04-dom-and-event-model/2-summary.md) 리스너 누수). 새로고침은 새 렌더러를 만들 뿐 원인을 고치지 않는다.

### 3. iframe 많은 페이지의 메모리 폭증

- **현상**: 광고·임베드 위젯이 많은 페이지에서 저사양 기기 탭이 자주 재로드된다.
- **보이는 형태**: 작업 관리자에 iframe 행("Subframe: https://…" — 영문 UI 기준)이 다수. 탭 전체 메모리 합이 크다.
- **원인**: 부모와 다른 사이트의 iframe은 OOPIF 렌더러로 간다(실험: 다른 사이트 iframe 하나에 렌더러 +1). 한 탭 안의 같은 사이트 iframe끼리는 렌더러를 함께 쓰므로 iframe 수가 아니라 다른 사이트 수만큼 는다(RenderingNG). 사이트 격리의 메모리 부담(Chrome 67 데스크톱, 탭이 많을 때 약 10~13%, Site Isolation 문서).
- **대처**: 화면 밖 iframe은 `loading="lazy"`, 같은 공급자 위젯은 하나로 묶는다. 꼭 필요한 임베드만 남긴다.

### 4. "같은 출처니까 같이 멈추겠지/안 멈추겠지" 오판

- **현상**: 탭 간 동기화(같은 사이트 탭 둘)가 한쪽이 무거울 때 다른 쪽까지 느려진다고 가정하고 설계했는데 실제로는 안 그렇다(또는 반대).
- **보이는 형태**: 재현이 기기·Chrome 판마다 다르다.
- **원인**: 프로세스 배정은 사이트·opener 관계·프로세스 수 한도·플랫폼(Android 조건부 격리)에 따라 달라진다. 표준이 정하는 것은 이벤트 루프의 의미론뿐이고, 프로세스 배치는 브라우저 구현이다.
- **대처**: 탭 간 통신은 `BroadcastChannel`·`storage` 이벤트 같은 비동기 메시지로 짜고, 같은 프로세스를 전제하지 않는다.

## 핵심 문장

- 브라우저는 렌더링 엔진이 죽거나 멈추는 것을 막을 수 없다고 보고, 프로세스로 나눠 피해를 한 렌더러에 가둔다.
- 브라우저 프로세스는 UI·조율, 렌더러는 웹 콘텐츠, Viz는 화면 출력, 네트워크 서비스는 소켓을 맡는다. 렌더러는 샌드박스 안에 있다.
- 사이트는 scheme + eTLD+1이다. 포트·서브도메인이 달라도 사이트는 같을 수 있고, Chromium은 사이트 단위로 프로세스를 나눈다.
- 다른 사이트 iframe은 OOPIF가 되어 다른 렌더러에서 돈다(실험: 렌더러 +1). 같은 사이트·다른 출처 iframe은 부모와 함께 남았다.
- 무한 루프는 그 문서의 메인 스레드를 막는다. opener로 이어진 같은 사이트 창은 함께 멈췄고, 별도 탭은 멀쩡했다.

## 관련 주제·근거

- 선행
  - [os/04-process-and-lifecycle](../../os/04-process-and-lifecycle/2-summary.md) — 프로세스·주소 공간 분리
  - [os/30-ipc](../../os/30-ipc/2-summary.md) · [os/07-threads-and-context-switch](../../os/07-threads-and-context-switch/2-summary.md)
- 후속·연결
  - [02-rendering-pipeline](../02-rendering-pipeline/2-summary.md) — 렌더러 안 메인 스레드·컴포지터 스레드의 일
  - [03-event-loop](../03-event-loop/2-summary.md) — 메인 스레드가 일을 고르는 규칙
  - [04-dom-and-event-model](../04-dom-and-event-model/2-summary.md)
  - [16 `long-tasks-and-web-workers`](../16-long-tasks-and-web-workers/2-summary.md)
  - security 21 `same-origin-and-cors`, 24 `memory-safety-exploits` — 미작성, [security README](../../security/README.md)
  - [languages/web-api/24-document-lifecycle-events](../../../languages/web-api/24-document-lifecycle-events/2-summary.md) — 문서 수명 이벤트 문법
- 문서·소스
  - Chromium, "Multi-process Architecture" <https://www.chromium.org/developers/design-documents/multi-process-architecture/> — 동기, 브라우저/렌더러 역할, Mojo IPC, 충돌 감지·sad tab, 샌드박스, Sharing the renderer process(opener 창은 같은 출처면 프로세스 공유)
  - Chromium, "Site Isolation" <https://www.chromium.org/Home/chromium-security/site-isolation/> — 사이트 정의와 `document.domain` 호환 이유, Chrome 67/77, Android 2GB 조건, Spectre, 메모리 10~13%(Chrome 67 데스크톱), Limitations(하위 리소스·CORB 최선 노력)
  - Chrome for Developers, "Inside look at modern web browser (part 4)" <https://developer.chrome.com/blog/inside-browser-part4> — 컴포지터 스크롤과 non-fast scrollable region, passive 리스너
  - Chrome for Developers, "RenderingNG architecture" <https://developer.chrome.com/docs/chromium/renderingng-architecture> — 브라우저·렌더러·Viz 프로세스, 같은 사이트 탭의 프로세스 배정(opener 예외·메모리 압박), 한 탭 안 같은 사이트 프레임은 같은 렌더러, 메인·컴포지터 스레드
  - MDN, "Cross-Origin-Opener-Policy" <https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cross-Origin-Opener-Policy> — `window.open()` 정책 표(둘 다 같은 출처·`same-origin`이면 같은 그룹)
  - Chromium 소스 `net/base/registry_controlled_domains/registry_controlled_domain.cc` — PSL DAFSA 조회
- 실험 목록(headless Chrome 151.0.7922.173, Playwright `playwright-core`, Node 20, 127.0.0.1 로컬 서버, 2026-10-04)
  - `e01b-oopif.js`: iframe 없음 / 같은 사이트·다른 출처 / 다른 사이트 iframe의 렌더러 수·OOPIF 수(3회)
  - `e01c-baseline.js`: 시작 직후·about:blank·이동 후 프로세스 종류
  - `e01-processes.js`: 4초 동기 루프 중 탭1·opener 팝업·같은 사이트 탭·다른 사이트 탭의 응답(3회)
