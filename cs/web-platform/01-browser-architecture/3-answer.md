# web-platform/01-browser-architecture — 정답

## 정답

### 1. 왜 멀티 프로세스인가

- 안정성: Chromium 설계 문서는 "죽거나 멈추지 않는 렌더링 엔진을 만드는 것은 거의 불가능하다"고 본다. 프로세스를 나누면 한 페이지의 충돌·멈춤이 그 렌더러에 갇힌다. 충돌하면 그 렌더러를 쓰는 탭·프레임만 "sad tab"이 되고 새로고침이 새 렌더러를 만든다.
- 보안: 렌더러를 샌드박스에 넣어 디스크·소켓 직접 접근을 막는다(네트워크는 네트워크 서비스 경유). 사이트 격리를 더하면, Spectre처럼 버그 없이도 같은 프로세스 메모리를 읽는 공격에 대해 다른 사이트 문서가 같은 주소 공간에 없게 된다. 다만 페이지가 불러온 다른 사이트 이미지·스크립트는 렌더러에 들어오고 CORB도 최선 노력이라, 다른 사이트 데이터가 전혀 없다는 보장은 아니다(Site Isolation 문서, Limitations).

### 2. 프로세스·스레드 지도

```text
  브라우저 프로세스(1): UI, 탭·내비게이션, 입력 라우팅, 다른 프로세스 관리
     │ Mojo IPC
  렌더러(사이트별, 여러 개, 샌드박스)
     ├ 메인 스레드: JS 실행, DOM, 스타일·레이아웃, HTML 파싱
     └ 컴포지터 스레드: 입력 처리, 스크롤, 일부 애니메이션
  Viz 프로세스(1): 모든 렌더러의 합성 프레임을 모아 GPU로 그림
  네트워크 서비스: 렌더러 대신 네트워크 요청
```

- 근거: RenderingNG architecture, Multi-process Architecture.

### 3. 출처와 사이트

- 출처 = `https://shop.example.co.kr:8443`(scheme + host + port).
- 사이트 = `https://example.co.kr`(scheme + eTLD+1, `co.kr`이 eTLD).
- `127.0.0.1:5000`과 `127.0.0.1:6000`: 포트가 달라 **다른 출처**, 포트는 사이트에서 무시되므로 **같은 사이트**다. IP 호스트는 등록 도메인이 없어 호스트 자체가 사이트 판정에 쓰인다.

### 4. iframe과 렌더러 수

(실험, headless Chrome 151, 스로틀 없음, 2026-10-04 — 3회 같은 값)

```text
iframe 없음                            renderer=3 OOPIF타깃=0
iframe 127.0.0.1:P2 (같은 사이트, 다른 출처)  renderer=3 OOPIF타깃=0
iframe localhost:P1 (다른 사이트)         renderer=4 OOPIF타깃=1
```

- (a) 늘지 않는다(+0, OOPIF 0). (b) 렌더러 +1, OOPIF 1.
- 기본값 3에는 about:blank 탭만 열어도 생기는 렌더러들이 들어 있다(하나는 `--top-chrome-webui`). 그래서 증가분만 본다.

### 5. 무한 루프의 영향 범위

(실험, headless Chrome 151, 2026-10-04 — 3회 같은 판정)

```text
   탭1 (루프 중인 문서)                            -> timeout (1502ms)
   팝업 (탭1이 연 같은 사이트, opener 연결)             -> timeout (1501ms)
   탭2 (같은 사이트, 별도 탭)                        -> ok (10ms)
   탭3 (다른 사이트)                              -> ok (11ms)
```

- 같은 이벤트 루프(메인 스레드)를 쓰는 문서만 멈춘다. opener로 이어진 같은 사이트 팝업은 탭1과 서로의 `window`에 동기 접근할 수 있어 같은 이벤트 루프에 있었다.
- 관계없는 같은 사이트 탭은 다른 프로세스에 배정되어 응답했다. 이 배정은 Chrome 구현의 결과이고 표준이 보장하는 것은 아니다(데스크톱에서 메모리 압박이 크면 같은 사이트 탭을 한 프로세스에 묶을 수 있다 — RenderingNG).
- 실험의 팝업은 탭1과 같은 출처이기도 하다. 같은 사이트·다른 출처 팝업은 따로 재지 않았다.

### 6. 사이트 격리의 경계

- 막는 것: 다른 사이트 문서(탭·새 탭·iframe)는 다른 프로세스에 둔다. 장악된 렌더러나 Spectre류 읽기가 다른 사이트의 메모리에 닿지 않게 한다.
- 막지 않는 것
  - 같은 사이트의 서브도메인끼리(`a.example.com`·`b.example.com`)는 같은 사이트라 같은 프로세스일 수 있다.
  - 출처 간 접근 통제는 프로세스가 아니라 SOP·CORS(security/21)가 맡는다.
  - 페이지가 불러온 다른 사이트의 이미지·스크립트는 그 렌더러로 들어온다. 민감한 응답을 거르는 CORB도 최선 노력이다(Site Isolation 문서, Limitations).
  - Android는 RAM 2GB 이상 기기에서 로그인 사이트 등 조건부로만 격리한다(Site Isolation 문서).
- 그래서 사용자 업로드 콘텐츠는 별도 등록 도메인에서 서빙한다.

### 7. PSL 자료구조

- Chromium은 PSL을 빌드 때 **DAFSA**(접미사·접두사를 공유하도록 최소화한 비순환 오토마톤 = 압축 트라이)로 바이트 배열에 넣는다(`registry_controlled_domain.cc`의 `kDafsa`, `effective_tld_names-reversed-inc.cc`).
- 도메인은 오른쪽이 상위(`kr` → `co` → `example`)다. 뒤집어 넣으면 트라이를 루트에서부터 따라가며 가장 긴 공개 접미사를 한 번의 순회로 찾을 수 있다. → data-structure/09-trie

### 8. iframe 많은 페이지의 재로드

- 확인: Chrome 작업 관리자의 iframe 행("Subframe: …", 영문 UI 기준) 수와 메모리, `chrome://process-internals`의 프레임별 프로세스 배정.
- 원인: 부모와 다른 사이트의 iframe은 OOPIF 렌더러로 간다(실험 +1). 한 탭 안의 같은 사이트 iframe끼리는 렌더러를 공유하므로, 사이트 수만큼 는다(RenderingNG). 사이트 격리는 Chrome 67 데스크톱에서 모든 사이트를 격리하고 탭이 많을 때 약 10~13% 메모리 부담으로 측정됐다(Site Isolation 문서).
- 대처: 화면 밖 iframe `loading="lazy"`, 위젯 통합, 불필요한 임베드 제거. 저사양 기기 탭이 OS에 의해 정리되는지 RUM으로 관찰한다.

### 9. 결제 팝업 후 원래 페이지가 굳음

- 가설: 팝업이 opener와 같은 사이트·opener 관계라 같은 이벤트 루프를 공유한다. 팝업의 무거운 동기 스크립트가 원래 페이지 메인 스레드도 막는다(5번 실험과 같은 모양).
- 대처: `window.open(url, '_blank', 'noopener')`로 opener 관계를 만들지 않는다. 결제 페이지 응답에 `Cross-Origin-Opener-Policy: same-origin`을 주면, opener와 출처가 다르거나 opener의 COOP가 `same-origin`이 아닐 때 브라우징 컨텍스트 그룹이 갈려 프로세스가 분리될 수 있다(MDN COOP). 팝업 쪽 긴 태스크도 쪼갠다(03).
