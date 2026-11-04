# 검수 대기 목록 — 우선 검수할 cs 노트

cs 노트는 Claude 초안(`metadata.md` 「단계」 `초안`)으로 들어온 뒤, 직접 읽고 확정하면 `검수`가 된다(cs/README §4).\
초안이 수백 편이라 영역 표만으로는 무엇부터 볼지 묻힌다 — **직접 공부하며 만든 노트, 곧 다시 볼 노트**를 여기 올린다.\
검수를 마치면 행을 「완료」로 옮긴다.

## 검수 방법 (노트 하나)

1. `1-question.md`부터 맨기억으로 답해 본다 → 막히면 `2-summary.md` → `3-answer.md`.
2. 이해가 안 되거나 틀린 곳, 원 프로젝트에서 이해한 방식과 다른 설명을 짚는다 → 수정.
3. 아래 「남은 [?]」를 근거로 해소하거나 그대로 두기로 판정한다.
4. 확정: `metadata.md` 「단계」를 `검수`로, 「검수」 칸에 날짜 → `python3 scripts/notes/gen_area_readme.py` → `python3 scripts/notes/check_notes.py <노트>`.

## 대기

### react-portal 학습 (2026-11-04 초안) — 출처: [project/react-portal](../project/react-portal/README.md)

읽는 순서: 25 → 26 → 27 (선행 순서). 함께 볼 원 프로젝트 문서: [archive/frontend](../project/react-portal/archive/frontend/README.md)의 "이해의 흐름" 절.

| 순서 | 노트 | 질문 | 남은 [?] | 실브라우저로만 확인할 것 |
|---|---|---|---|---|
| 1 | [web-platform/25-stacking-context-and-containing-block](../cs/web-platform/25-stacking-context-and-containing-block/) | 9 | ① flex·grid 아이템 z-index 적용의 명세 절 번호(동작은 실험 B로 확인) ② iOS Safari에서 `overflow: hidden`만으로 터치 스크롤이 안 막히는 사례 | 휠·터치 스크롤 차단(실험은 스크롤바 폭·`scrollTo`로만 측정) |
| 2 | [web-platform/26-portals-and-two-trees](../cs/web-platform/26-portals-and-two-trees/) | 10 | ① React 17 릴리스 노트 URL·날짜(이벤트 위임 위치 `document` → 루트) | — |
| 3 | [web-platform/27-modal-dialog-behavior](../cs/web-platform/27-modal-dialog-behavior/) | 9 | ① UI Events·Pointer Events 이벤트 순서 절 번호 ② 드래그 시 click이 공통 조상에서 나는지(원문 대조) ③ click-through ④ `preventDefault` 없이 `first.focus()` 하면 한 칸 더 가는지 ⑤ `getEventListeners`가 DevTools 전용인지 ⑥ `showModal()`의 스크롤 처리 | 이벤트 순서, click-through, Tab 기본 이동 |

같은 작업에서 **보강만** 한 기존 노트(이미 초안 상태 — 보강 부분만 확인): [web-platform/04](../cs/web-platform/04-dom-and-event-model/) · [language/06](../cs/language/06-values-references-passing/) · [language/07](../cs/language/07-scope-closures-first-class-functions/) · [language/09](../cs/language/09-memory-management-models/) · [language/10](../cs/language/10-garbage-collection/) — 근거 `docs/plans/2026-11-04/react-portal-archive/log.md`.

## 완료

| 노트 | 검수일 | 메모 |
|---|---|---|
