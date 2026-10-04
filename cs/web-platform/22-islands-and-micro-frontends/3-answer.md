# web-platform/22-islands-and-micro-frontends — 정답

## 정답

### 1. 푸는 문제와 나누는 기준

- Islands: 성능 문제. 대부분 정적인 페이지를 통째로 하이드레이션하는 비용을 없앤다. 기준은 **상호작용 여부**.
- 마이크로 프론트엔드: 조직 문제. 여러 팀이 한 화면을 만들 때 배포가 서로 묶이는 것을 푼다. 기준은 **소유 팀**.
- 공통: 조각 사이 경계(무엇을 공유하고 무엇을 격리하나)를 설계해야 한다.

### 2. Islands vs 진행형 하이드레이션, Astro 지시어

- 진행형 하이드레이션은 페이지를 한 트리로 보고 가지의 하이드레이션 순서만 정한다. Islands는 그 트리를 클라이언트에서 조립하지 않는다(섬마다 루트가 따로).
- Astro 지시어
  - `client:load`: 페이지 로드 즉시.
  - `client:idle`: 브라우저가 한가해질 때.
  - `client:visible`: 컴포넌트가 뷰포트에 들어올 때.
  - `client:only`: 서버 렌더 없이 클라이언트에서만 렌더.
  - (`client:media`: 미디어 쿼리 조건이 맞을 때.) 지시어가 없는 UI 프레임워크 컴포넌트는 JS를 내보내지 않는다(`.astro` 컴포넌트의 `<script>`는 지시어 없이도 브라우저로 간다).

### 3. 조합 장소와 방식

```text
  빌드 타임: npm 패키지로 합침
  서버:      SSI·ESI·템플릿으로 HTML 조각 조합
  브라우저:  iframe | JS 로드 후 마운트(Module Federation 포함) | Web Components
```

- 빌드 타임 통합: 한 부분을 바꿔도 마이크로 프론트엔드 하나하나를 다시 컴파일·릴리스해야 한다. 독립 배포라는 목적이 사라진다(Jackson).
- iframe: 격리가 쉽지만 그만큼 덜 유연하다. 앱의 다른 부분과 통합(라우팅·높이·통신)을 만들기 어렵다(Jackson).

### 4. React 사본 세 가지

`(실험, headless Chrome 151, React 19.2.8, 2026-10-04)`

```text
① remote-dup       JS 합계 204067B | 같은 React? false | 원격 오류: Cannot read properties of null (reading 'useState')
① remote-shared    JS 합계 194926B | 같은 React? true | 버튼 리뷰 0 → 클릭 후 리뷰 1
① remote-selfmount JS 합계 388968B | 같은 React? n/a | 버튼 리뷰 0 → 클릭 후 리뷰 1
```

- 자기 React를 넣은 컴포넌트를 셸이 렌더: 훅이 깨진다(`null`에서 `useState` 읽기 실패).
- 셸의 React 공유: 정상. 원격 번들 199B.
- 직접 마운트: 동작하지만 react-dom이 두 벌이라 JS가 약 두 배.

### 5. 깨지는 이유와 설정

- react.dev: 훅이 동작하려면 앱 코드의 `react` import가 `react-dom` 안의 `react` import와 같은 모듈로 풀려야 한다. 셸의 react-dom은 자기 React(A)의 내부 디스패처를 설정하는데, 원격 컴포넌트는 React(B)의 `useState`를 불러 비어 있는 디스패처를 읽는다.
- Module Federation `shared: { react: { singleton: true, requiredVersion: … } }`
  - `singleton`: 공유 범위에 한 버전만 허용한다(기본 `false`). 사용 전에 여러 버전이 등록돼 있으면 가장 높은 버전을 쓰고, 범위를 못 맞춘 소비자에 대해 경고한다. 이미 로드된 모듈은 교체되지 않는다(나중에 온 더 높은 버전은 경고 없이 무시 — webpack 문서).
  - `requiredVersion`: 허용 범위. 못 맞추면 — 대체 모듈 있고 비싱글턴이면 기본 `strictVersion: true`라 대체 모듈 사용, 싱글턴·대체 없음이면 기본 콘솔 경고, 여기에 `strictVersion: true`면 런타임 오류.

### 6. CSS 충돌

```text
② 팀 A 버튼 배경: rgb(255, 0, 0) | Shadow DOM 안 팀 A 버튼: rgb(0, 0, 255)
```

- 같은 선택자·같은 명시도면 나중 규칙이 이긴다 → 팀 A 버튼이 빨강.
- Shadow DOM 안 버튼은 문서 스타일시트의 선택자가 닿지 않아 파랑을 유지한다.

### 7. 섬 사이 이중 fetch

```text
③ bundled /api/cart 요청 2회 | 'cart-store 평가' 로그 2회 | …
③ module  /api/cart 요청 1회 | 'cart-store 평가' 로그 1회 | …
```

- 번들에 각자 넣으면 2회(모듈 인스턴스가 둘). 같은 URL의 ES 모듈을 import하면 1회.
- HTML 표준의 module map: (URL, 모듈 종류)를 키로, import된 모듈 스크립트를 Document·워커마다 한 번만 fetch·파싱·평가한다. 쿼리·조각이 다르면 다른 항목이다.

### 8. 통신 방법

- 이벤트(`CustomEvent` + `dispatchEvent`/`addEventListener`), 아래로 내려주는 콜백, URL(주소창 파라미터).
- Jackson: 메시지·이벤트로 통신하고 공유 상태를 피한다. 마이크로서비스가 DB를 공유하면 결합이 생기듯, 자료 구조와 도메인 모델을 공유하는 순간 큰 결합이 생긴다.
- 이벤트 이름과 `detail` 형태는 계약으로 문서화·버전 관리한다.

### 9. 메이저 업그레이드 뒤 한 원격만 깨짐

- `singleton`이면 한 버전만 쓰인다. 버전이 다르면(사용 전에 함께 등록된 경우) 높은 버전(셸의 새 React)이 쓰이고, 오래된 원격은 바뀐 동작을 견디지 못했다. 콘솔에는 허용 범위 불일치 경고가 남는다.
- 예방: 공유 라이브러리의 허용 범위를 팀 간에 합의하고, 메이저 업그레이드는 원격들의 호환을 확인한 뒤 올린다. 셸·원격 조합을 CI에서 띄워 보는 계약 테스트를 둔다.

### 10. 도입 전 질문

- "팀이 정말 독립 배포가 필요한가?" 아니면 한 저장소의 모듈 경계·소유 규칙으로 충분한가.
- 서버의 모놀리스 vs 마이크로서비스 판단과 같다. 독립 배포·팀 자율의 이득이 운영 복잡도·중복·통합 비용(번들 중복, 버전 협상, 스타일 격리, 통신 계약)보다 클 때만 나눈다.
