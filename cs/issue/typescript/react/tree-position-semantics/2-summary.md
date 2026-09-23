# cs/issue/typescript/react/tree-position-semantics — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.

## 전체 흐름

```
React가 판단에 쓰는 것 = 컴포넌트 트리의 위치 (DOM 위치 아님)

  판단                     React 트리 기준                 어긋나는 DOM 기준 판단
  ─────────────────────   ─────────────────────────────   ──────────────────────────
  인스턴스 동일성          타입 + 트리 위치 + key          "화면에 계속 보인다"
  Context 공급             조상 프로바이더                 "논리적으로 같은 영역"
  합성 이벤트 전파         React 조상으로 버블             DOM 조상 (포털은 body 끝)
                                                           contains() / closest()

[실패 1] cond ? <Group><A/><B/></Group> : <A/>   → A의 위치 변경 → 리마운트 → 로컬 상태 소실
[교정]   Group 상시 렌더 + keyed 자식 (근본: 상태 승격)

[실패 2] <Provider>{main}</Provider> {sidebar}   → sidebar에서 훅 호출 → throw (의도된 오용 방지)
[교정]   sidebar 가지에도 Provider 배선

[실패 3] Panel(onKeyDown) ─React 조상→ Portal(Modal)   키가 Panel 핸들러까지 버블
[교정]   열림 상태를 모듈 소유 + 창 루트 레이어가 렌더 → 조상 경로 자체 제거 (+ 백스톱)

[실패 4] 바깥클릭: trigger.contains(t)            → 포털 팝오버 안 클릭 = "바깥" → 즉시 닫힘
         부모 onClick ← 중첩 포털 클릭(React 버블) + closest()는 래퍼 못 찾음 → 부모 메뉴 닫힘
[교정]   판정에 popRef 포함, 닫기 조건 = popRef.contains(t) 가드
         버그를 고정한 테스트 제거 + 중첩 포털 테스트 (가드 제거 시 실패하는지 확인)
```

## 핵심 문장

- React는 **타입·트리 위치·key**로 인스턴스를 식별한다 — 조건부 래퍼로 위치가 바뀌면 같은 컴포넌트라도 리마운트된다.
- Context는 **트리상 조상 프로바이더**에서만 온다 — 다른 가지는 별도 배선이 필요하고, 밖에서의 호출은 throw로 시끄럽게 드러내는 게 낫다.
- 포털은 DOM 위치만 옮긴다 — 합성 이벤트는 **React 트리**를 따라 조상 핸들러로 버블한다.
- `contains`·`closest` 같은 DOM 판정과 React 이벤트 전파가 만나는 곳은 어긋남을 **명시적으로** 처리한다.
- `transform`(및 `filter`·containment 등)이 있는 조상은 `fixed` 자손의 기준 상자가 된다 — 포털을 쓰는 이유이자, 포털이 만드는 이벤트 어긋남의 출발점.
