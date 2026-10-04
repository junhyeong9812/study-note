# web-platform/21-component-and-state-patterns — 정답

## 정답

### 1. 서버 상태 vs 클라이언트 상태

- 클라이언트 상태(모달 열림, 입력 중 글자)는 진실의 주인이 클라이언트다. 바꾸면 그것이 곧 진실이다.
- 서버 상태(주문 목록, 프로필)는 진실이 서버에 있다. 다른 사용자·다른 탭·다른 화면이 바꿀 수 있다. 클라이언트가 가진 것은 어느 시점의 복사본이다.
- 복사본이면 캐시 문제가 된다.
  - 키: 무엇의 복사본인가(`['orders', userId]`).
  - 신선도: 언제 오래됐다고 보나(TanStack Query 기본 `staleTime` 0).
  - 무효화: 변경 뒤 어떤 키를 다시 가져오나.

### 2. 단방향 흐름 셋

```text
  Flux   Action ─> Dispatcher ─> Store ─변경 이벤트─> View ─> Action …
  Redux  dispatch(action) ─> reducer(state, action) ─> store ─구독─> view ─> dispatch …
  Elm    Msg ─> update(msg, model) ─> Model ─> view(model) ─> HTML ─ 입력 ─> Msg …
```

- Redux 세 원칙: 단일 진실 원천(한 스토어의 객체 트리), 상태는 읽기 전용(바꾸려면 action을 내보냄), 변경은 순수 함수(reducer)로.
- 공통점: 상태 변경의 입구가 하나다. 데이터가 한 방향으로만 돈다. 그래서 변경 이유를 action·메시지 기록으로 추적할 수 있다.

### 3. 상태 위치별 재렌더

`(실험, headless Chrome 151, React 19.2.8, CPU 4×, 3회)`

```text
① global 10글자 입력 → 행 렌더 10000/10000/10000 | … | 스크립트 시간 합 251/217/230ms
① local  10글자 입력 → 행 렌더 0/0/0 | … | 스크립트 시간 합 78/72/80ms
① store  10글자 입력 → 행 렌더 0/0/0 | … | 스크립트 시간 합 144/156/183ms
```

- Context: 10 × 1000 = 10,000회. `memo`는 Context 구독을 막지 못한다.
- 로컬: 0회. 행은 바뀐 것을 읽지 않는다.
- 선택자 스토어: 렌더 0회지만 스크립트 시간은 로컬보다 크다(144~183ms). 변경마다 구독자 1000개의 선택자를 실행해 비교하기 때문이다.

### 4. props를 state로 복사

```text
② 가격 +500 두 번 → state 복사: 1000 / props 직접: 2000
```

- `useState`의 인자는 첫 렌더에만 쓰인다. 복사한 자식은 1000에 멈춘다.
- 첫 값만 쓰는 것이 의도라면 prop 이름을 `initialPrice`·`defaultPrice`처럼 짓는다(react.dev). 다른 대상으로 바뀔 때 초기화하려면 부모가 `key`를 바꿔 다시 마운트한다.

### 5. 요청 수와 무효화

```text
③ 첫 화면 /api/user 요청 수: 4 (각자 fetch 컴포넌트 2개 + 키 캐시 컴포넌트 2개 + 전역 복사 1개)
   이름 변경 + invalidate("user") 뒤 요청 수: 1 → 캐시: 김영희 김영희 | 전역 복사본: 김철수
```

- 4 = 각자 fetch 2 + 키 캐시 1(두 컴포넌트가 진행 중 promise를 공유) + 전역 복사 1.
- 무효화 뒤: 키 캐시는 1번 다시 가져와 두 컴포넌트 모두 새 이름. 전역 복사본은 아무도 갱신하지 않아 옛 이름. "각자 fetch" 컴포넌트는 `useEffect(…, [])`로 마운트 때 한 번만 가져오는 코드라 무효화 신호를 받지 않는다(이 값은 출력에 싣지 않았다 — 코드로 판단).

### 6. 제어·비제어와 경고

- 비제어: 중요한 정보를 자기 로컬 상태로 결정한다. 폼이면 `defaultValue`.
- 제어: 중요한 정보를 props가 결정한다. 폼이면 `value` + `onChange`.
- 경고(React 19.2.8 개발 빌드, 실험 ④)
  - `A component is changing an uncontrolled input to be controlled. This is likely caused by the value changing from undefined to a defined value, which should not happen. …`
  - `You provided a \`value\` prop to a form field without an \`onChange\` handler. This will render a read-only field. …` — 이 입력창은 `고정`에서 바뀌지 않았다.

### 7. 상태 위치 흐름

```text
  쓰는 컴포넌트가 하나 → 로컬
  몇 개 → 가장 가까운 공통 부모로 끌어올리기
  멀리 흩어짐 → Context(드물게 바뀜) / 선택자 스토어(자주 바뀜)
  서버 데이터 → 별도로 키 기반 캐시
```

- 가장 가까운 공통 부모 = 그 컴포넌트들의 최소 공통 조상(LCA). 그보다 위로 올리면 불필요한 재렌더 범위와 prop 전달이 늘어난다.

### 8. 폴드와 구조 공유

- 폴드: 현재 상태 = `actions.reduce(reducer, 초기상태)`. 같은 action 기록을 다시 적용하면 같은 상태가 나온다. 시간 여행 디버깅·이벤트 소싱과 같은 구조다.
- 구조 공유: 갱신 때 바뀐 경로의 노드만 새로 만들고 나머지는 이전 참조를 재사용한다. 그러면 "참조가 같다 = 그 아래가 안 바뀌었다"가 성립해, 깊은 비교 대신 참조 비교(O(1))로 변경을 판정할 수 있다. TanStack Query도 결과에 구조 공유를 적용한다.

### 9. 결제 후에도 "미결제"

- 찾을 것: 서버 응답을 전역 스토어로 복사하는 코드(`dispatch(setOrders(data))`)와, 결제 성공 경로에 그 복사본 갱신이 있는지.
- 원인: 서버 상태의 복사본을 클라이언트가 주인처럼 들고 있고, 결제 경로에서 무효화를 빠뜨렸다(실험 ③의 전역 복사본과 같은 모양).
- 고치기: 주문 목록을 키 기반 캐시로 옮기고, 결제 변경의 `onSuccess`에서 `['orders']` 키를 무효화한다. 복사본을 없앤다.

### 10. prop drilling의 첫 처방

- 합성: 중간 컴포넌트가 `children`(또는 슬롯 props)을 받게 바꾼다. 데이터를 가진 위쪽 컴포넌트가 완성된 요소를 바로 꽂으므로 중간이 그 값을 몰라도 된다.
- 그래도 깊고 넓게 퍼지면 Context를 쓴다. 자주 바뀌는 값이면 재렌더 범위를 함께 고려한다(3번 결과).
