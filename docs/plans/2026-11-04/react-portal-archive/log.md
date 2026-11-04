# log — react-portal-archive

## 타임라인

| 시각 | 사건 | 결과/결정 |
|------|------|----------|
| 2026-11-04 | 명세 합의, auto. 브랜치 archive/2026-11-04-react-portal | SPEC=1 |
| 2026-11-04 | task01 커리큘럼 §16.3에 25·26·27 행 + 학습 순서·변경 이력 | gen_area_readme 재생성, --check "생성 문서 전부 생성기 출력과 같음" → A1 확인 |
| 2026-11-04 | 워커 5개 위임(Opus): W1 cs25 · W2 cs26 · W3 cs27 · W5 기존 노트 비교 · W4 issue | 메인은 project/react-portal 작성 |
| 2026-11-04 | project/react-portal: README + 이슈 01~07(§2-B) + archive(learning·frontend 26파일 복사) | 스니펫 전 줄을 인용 커밋의 `git show` 결과와 대조 → 05의 `…` 생략 1건 발견, 실제 줄로 교체(가이드 placeholder 금지). archive 상대 링크 미해결 0 |
| 2026-11-04 | W4 회수: 4건 모두 ⓒ(방안 비교) — N1 → issue/typescript/react/tree-position-semantics · N2 → issue/typescript/browser/input-event-model · N3·N4 → issue/typescript/react/instance-scope-of-global-state | 메인 교차 확인: +264/−0, 노출 스캔 0(메인 재실행), 내용 샘플 확인. 원 식별자: react-portal, mini-portal, createModal, createNaiveModal, getOpenModals, isLogicalDescendant, nodeOf, lockScroll/unlockScroll, savedOverflow, lockCount, trapTab, onPointerDown, onKeyDown, onKey, `.mini-*`, src/modal.js, src/registry.js, demo/naive-modal.js, demo/main.js |
| 2026-11-04 | W5 회수: 기존 5노트 모두 보강(04: 2단계 위임·같은 클릭=같은 객체·분리 노드 + 실험·Q10 / language/06·07·09·10: 흔한 오해·도식·약한 참조 실험) | 메인 교차 확인: 7파일 +159/−0, check_notes 5 PASS 0 FAIL, WARN 3건은 HEAD 기존 문장(추가분 단정어 0) |
| 2026-11-04 | W1 회수: cs/web-platform/25 (질문 9, 실험 4 — headless Chrome 155.0.8059.79) | 메인 교차 확인: check_notes PASS·WARN 0, 실험 C(c-fixed.html) 메인 재실행 출력이 노트 212~218행과 일치. [?] 2건(flex/grid 절 번호, iOS Safari) |
| 2026-11-04 | W2 회수: cs/web-platform/26 (질문 10, 실험 a 미니 두 트리·b React) | 메인 교차 확인: check_notes PASS·WARN 0, 실험 출력 65줄 전부 노트에 존재. [?] 1건(React 17 릴리스 노트 URL·날짜). 27 링크 없음 → 27 완료 후 보완 |
| 2026-11-04 | W3 회수: cs/web-platform/27 (질문 9, 실험 A·C·D·E — 프로젝트 코드 실험 B는 cs 일반성 위해 제외) | 메인 교차 확인: check_notes PASS·WARN 0, 실험 c·d·e 출력 전부 노트에 존재(a는 구분 라벨 2줄만 미포함). react-portal git status 깨끗 |
| 2026-11-04 | 메인: 25→26·27, 26→27 상호 링크 추가. 27의 "body overflow 뷰포트 전파" [?] 2건을 25의 확인 근거(CSS Overflow 3 §3.1.4)로 해소 | 8노트 check_notes 8 PASS 0 FAIL(WARN 3 = 기존 문장), gen --check 통과, 영역 표 25~27 `초안(Claude)`, project·issue 링크 140 중 깨짐 0 |
| 2026-11-04 | 커밋 | 7ba504d9 cs 신규 25~27 · fdbacd48 기존 노트 보강 · 6f6e2b2f / 700fc668 / 3f1d61a9 issue 3카드 · 0ee7af5b project/react-portal |
| 2026-11-04 | 아카이브 | issue/typescript/react/tree-position-semantics ⓒ 6f6e2b2f · issue/typescript/browser/input-event-model ⓒ 700fc668 · issue/typescript/react/instance-scope-of-global-state ⓒ 3f1d61a9 (N3·N4 한 카드) |

## 리뷰 ledger

- stakes 낮음 → 셀프체크. 워커 5개 산출물마다 메인이 교차 확인 1~2개(검사기 재실행·실험 재실행 또는 출력 대조·노출 스캔 재실행·diff 추가 전용 확인).

## 완료 요약

- **cs 신규 3편** web-platform/25 쌓임 맥락·containing block(headless Chrome 실험 4) · 26 portal과 두 트리(jsdom·React 실험 2) · 27 모달 상호작용 계약(jsdom 실험 4). 각 노트에 학습자의 실제 질문 기반 "처음 그림 vs 실제" 도식·흔한 오해.
- **cs 보강 5편** web-platform/04, language/06·07·09·10 — 추가 전용(+159).
- **issue 3카드 방안 비교**(4건 매칭, 신규 카드 0 — 모두 기존 원리와 같고 해결 방안이 다름).
- **project/react-portal** README(저장소·PR·커밋 링크) + 이슈 01~07(§2-B, 스니펫 전 줄 커밋 원문 대조) + archive(learning·frontend 26파일).
- 남은 것: main 병합·push 사용자 확인 대기. `[?]` 잔여: 25(2) 26(1) 27(10→8).
| 2026-11-04 | 후속: react-portal 메뉴 키보드(PR #4)로 Tab 한계 해소 → project 04·README·archive 동기화, issue 카드 tree-position-semantics에 `## 정정` append(노출 스캔 0) | 커밋 7c6bd683 · 619b4660 |
