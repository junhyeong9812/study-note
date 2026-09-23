# typescript/react — 렌더링·상태·CSS

React 렌더링 모델, 상태 수명, CSS 캐스케이드에서 나오는 패턴이다.\
공통 원리: **상태와 스타일의 소유자를 정한다** — 컴포넌트는 리마운트되면 상태를 잃고, 클로저는 생성 시점을 보며, 크기·여백은 조상 컨텍스트가 결정한다.

## 공통 원리

```
  props/state 변경 ──▶ 렌더 ──▶ 커밋 ──▶ effect (deps 동등성)
        │               │                    │
        │               ├─ 리마운트 → 상태 소실
        │               └─ 클로저 = 그 렌더의 스냅샷 → stale
        └─ 상위 데이터 변경 → 종속 상태 리셋 필요
  CSS: 크기·스크롤·클리핑은 조상 컨텍스트가 결정
```

## 패턴 카드

- [async-subscription-cleanup](async-subscription-cleanup/) — 해제 핸들이 비동기로 도착하는 구독은 cleanup 시점에 핸들이 없을 수 있다 — disposed·세대 플래그로 도착 즉시 해제하고 등록 실패도 처리한다.
- [css-containing-context](css-containing-context/) — 요소의 크기·스크롤·클리핑·위치는 조상 컨텍스트(flex min-size·overflow·containing block·stacking·container query·cascade)가 결정한다 — 문제의 소유 조상을 찾아 고친다.
- [css-negative-margin-overflow](css-negative-margin-overflow/) — 부모 패딩을 상쇄하는 음수 마진·overflow 클리핑 경계가 여백 소유권과 어긋나면 가로 스크롤·이웃 노출이 생긴다 — 여백 소유권을 한쪽에 둔다.
- [dependent-state-reset](dependent-state-reset/) — 상위 데이터·컨텍스트가 바뀌면 거기서 파생된 종속 상태(선택·스크롤 앵커·실패 표시·기본 선택)를 재검증·리셋해야 유령 참조가 되지 않는다.
- [effect-dependency-and-timing](effect-dependency-and-timing/) — effect는 커밋 후 deps 값 동등성으로만 재실행된다 — 의도(정체성·액션)를 deps에 담고, 렌더에서 파생 가능한 상태를 effect로 동기화하지 않는다.
- [instance-scope-of-global-state](instance-scope-of-global-state/) — "전역 = 내 것" 가정(모듈 싱글턴·전역 버스·DOM id·창별 스토어·SSR 모듈 상태)은 인스턴스·창·요청이 둘이 되는 순간 누출된다 — 상태를 인스턴스 스코프로 내린다.
- [remount-lifecycle-state-loss](remount-lifecycle-state-loss/) — 가시성 전환·조건부 래퍼·DOM 재생성은 곧 리마운트다 — 컴포넌트에 둔 상태·구독·포커스 대상은 사라지므로 수명이 긴 상태는 밖에 두고 명시적으로 정리한다.
- [render-and-subscription-cost](render-and-subscription-cost/) — 렌더·구독 비용이 전체 데이터 크기×갱신 빈도에 비례하지 않게 한다 — 가상화·셀렉터·참조 동일성 유지·메모로 비용을 뷰포트·변경분에 묶는다.
- [separation-structure-vs-style](separation-structure-vs-style/) — 렌더러는 구조만, 표시는 CSS가 맡아야 한다(관심사 분리).
- [stale-render-state](stale-render-state/) — 핸들러·클로저는 생성 시점 렌더의 state 스냅샷을 본다 — 같은 틱의 연속 이벤트·async 콜백은 가변 ref로 최신 값을 읽어야 한다.
- [theming-token-reach](theming-token-reach/) — CSS 변수 테마는 우리 DOM 캐스케이드에만 닿는다 — canvas·JS 위젯·네이티브 컨트롤은 각자 API로 주입하고, 한 시각 단위의 색은 모두 같은 토큰에서 파생한다.
- [tree-position-semantics](tree-position-semantics/) — React는 DOM이 아니라 컴포넌트 트리 위치로 인스턴스 동일성·Context 공급·합성 이벤트 전파를 결정한다(포털 포함) — DOM 기반 판정과의 어긋남을 명시 처리한다.
- [xss-escape-then-assemble](xss-escape-then-assemble/) — 신뢰 불가 텍스트를 HTML·스크립트 위치에 삽입하면 XSS가 된다 — 전체를 이스케이프(또는 데이터 채널·sanitizer)한 뒤 필요한 마커만 조립한다.

> 이 폴더의 메타 태그: `resource-bounding`(2) · `least-privilege`(1) · `race-condition`(1) · `test-reliability`(1) · `single-source-of-truth`(1) — 태그별 전체 목록은 [cs/issue 태그 역인덱스](../../README.md#태그-역인덱스).
