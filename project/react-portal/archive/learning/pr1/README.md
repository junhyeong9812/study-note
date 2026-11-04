# PR #1 학습 노트 — 순수 JS 미니 Portal

> 대상: [PR #1](https://github.com/junhyeong9812/react-portal/pull/1) (`feat/mini-portal`) · 작성: 2026-11-03
> 코드를 읽으며 대화로 정리한 내용. 줄 번호는 PR #1 시점 기준.

| 문서 | 내용 | 언제 읽나 |
|------|------|----------|
| [01-my-understanding.md](01-my-understanding.md) | 내가 머릿속에 정리한 전체 구조 (한 장 요약) | 복습할 때 가장 먼저 |
| [02-concepts.md](02-concepts.md) | 몰랐던 개념 사전 (DOM·이벤트·JS 문법·CSS) | 용어가 막힐 때 |
| [03-internals-qa.md](03-internals-qa.md) | 내부 동작 질문과 답 (질문한 순서대로, 헷갈렸던 지점 포함) | 같은 곳에서 다시 막힐 때 |
| [04-remaining-code.md](04-remaining-code.md) | 중복 방지·합성 이벤트·레이어 스택·테스트 읽는 법 | 01~03 다음 |

## 코드 읽는 순서 (다시 볼 때)

```
0. 데모 실행 (npm run dev) — 로그 순서 눈에 익히기
1. src/node.js        두 트리가 갈라지는 곳 (constructor, createNode)
2. src/portal.js      일반 노드와 딱 한 줄 차이 (domParent: target)
3. src/layers.js      z-index 스택
4. src/registry.js    DOM 요소 → 노드 다리 (nodeOf)
5. src/events.js      listen(등록) + dispatch(배분)
6. src/node.js 다시   inject, destroy
7. test/              동작 명세서
8. demo/main.js       종합 예제
```

## 아직 안 본 것

- 없음 — 남았던 `events.js:9-31`, `layers.js`, `test/`는 [04](04-remaining-code.md)에서 정리

## 관련 주제 문서

- [../../frontend/](../../frontend/README.md) — DOM·이벤트·CSS·메모리 동작 원리를 주제별로 (추상화 뒤에서 브라우저가 하는 일)
