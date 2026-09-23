# cs/issue/typescript/react/effect-dependency-and-timing — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.

## 전체 흐름

```
render ──▶ commit(DOM 반영) ──▶ paint ──▶ effect 실행 ──▶ (setState) ──▶ render ...
                                  ▲
                                  └ effect 로 동기화한 값은 이 프레임엔 아직 옛 값  → 한 프레임 불일치
                                                                                  (겹친 UI · 마운트 부작용)

effect 재실행 판정 = deps 각 원소의 Object.is 비교
   ┌ 너무 거친 키 (path 만)          같은 path 의 다른 엔티티 → 재실행 안 됨
   ├ 원시값 재선택 (같은 commit)      같은 값 → 재실행 안 됨 (액션인데 무시)
   ├ 같은 값의 새 회차 (180 → 180)    → memo/effect 가 새 회차를 모름
   ├ 매 렌더 새 객체                  항상 다름 → 매 렌더 재실행 (폭주)
   └ deps 밖 요인 (높이·폰트)          → effect 로는 못 봄 → 관찰자(ResizeObserver)

[교정]
   의도를 deps 에 명시     refreshKey(엔티티 id) · 액션마다 새 객체 · resetNonce(회차)
   안정 키                 객체 대신 키 문자열 · 실패도 sentinel 로 캐시
   렌더 파생               저장하지 말고 매 렌더 계산 (deadline → 남은 초)
   렌더 중 조정            prevRef 로 전환 감지 → 렌더 중 setState (페인트 전 재렌더)
   effect 안 setState      await 이후로 · 동기 변경은 이벤트 핸들러에
```

## 핵심 문장

- effect는 **커밋 후** 돈다 — 렌더에서 파생 가능한 값을 effect로 맞추면 한 프레임 옛 값이 화면(과 마운트 부작용)에 나온다.
- effect는 deps의 **값 동등성**으로만 다시 돈다 — 정체성·액션·회차라는 의도는 deps에 명시해야 한다.
- 매 렌더 새 객체를 deps에 넣으면 매번 돈다 — 키 문자열로 바꾸고 실패도 캐시한다.
- "중복 요청 방지"와 "언마운트 시 결과 폐기"를 함께 쓰면 결과가 어디에도 반영되지 않는 교착이 생긴다 — 결과는 키 스코프로 항상 캐시.
- 시간 경과는 tick 수가 아니라 **절대 마감시각**에서 매 렌더 도출한다.
- deps 밖 요인으로 바뀌는 크기는 effect가 아니라 **관찰자**로 본다.
