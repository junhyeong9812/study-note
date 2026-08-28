# issue2 — 위키 뷰: 트리 하나로 폴더·주제·문서를 다 그린다

- 이슈 #3 · PR: https://github.com/junhyeong9812/study-note-deploy-system-front/pull/4

## 1. 배경

backend `/api/tree`가 주는 트리(리프 폴더=주제)를 화면 세 종류로 바꾼다:
폴더면 탐색 목록, 주제면 1/2/3 **3탭**(가림 없음 — 인터뷰 결정), post면 단일 본문.
md→HTML 렌더는 front 책임(설계: backend는 콘텐츠 JSON만).

## 2. 검토한 방식들

### 선택 — 라우트 하나(`/wiki/[...slug]`)가 노드 종류로 분기

```tsx
const node = findNode(treeData.tree, currentPath);
if (node && !node.is_subject)      body = <FolderView node={node} />;      // 폴더
else if (node && node.is_subject)  body = tabs.length > 0 ? <Tabs .../> : <Markdown .../>;  // 주제/post
else { /* 트리에 없는 경로 → 문서 직접 조회 폴백 (cs/index 같은 폴더 직속 문서) → 실패면 404 */ }
```

- 대안이었던 "폴더/주제/문서 라우트 분리"는 URL 설계를 backend 모델과 이중으로
  유지해야 해서 탈락 — 트리의 `is_subject` 하나가 이미 그 판단을 준다.

### 선택 — 탭은 "있는 것만" (3슬롯 고정 아님)

```ts
const KIND_ORDER = { question: 1, summary: 2, answer: 3 };
export function chapterTabs(node) {
  return node.docs.filter(d => KIND_ORDER[d.doc_kind])
                  .sort((a, b) => KIND_ORDER[a.doc_kind] - KIND_ORDER[b.doc_kind]);
}
```

코테(practice)는 **2-summary가 의도적으로 없다**(문제→풀이 구조). 3슬롯을 고정하고
"작성 전" 패널을 채우면 '의도된 부재'와 '깜빡한 부재'를 화면이 구분 못 한다.
(이 선택은 이후 리뷰어가 "3탭 보장 위반"으로 지적했지만 이 근거로 기각 — issue5.)

### 선택 — 상대 링크 치환을 렌더 시점에

노트에는 `](../kafka-why-fast/)` `](2-summary.md)` 같은 상대 md 링크가 흔하다.
그대로 두면 브라우저가 깨진 경로로 간다. react-markdown의 `a` 컴포넌트를 갈아끼워
문서 위치 기준으로 `/wiki/...`로 치환:

```ts
resolveHref("../kafka-why-fast/", "cs/systems/lsm-tree")  → "/wiki/cs/systems/kafka-why-fast"
resolveHref("2-summary.md",       "cs/lsm-tree")          → "/wiki/cs/lsm-tree/2-summary"
```

## 3. 실증

```
$ curl .../wiki/cs/systems/lsm-tree
tabs: ['1 · 질문', '2 · 정리', '3 · 정답']    본문 포함: True    사이드바: True
folder:200  post:200  404:404               edge-subject:200
```

## 4. 구현 중 마주친 문제

이 이슈 자체는 순항 — 단 여기서 심은 `resolveHref`의 결함(hash 붙은 링크)이 issue5의
리뷰에서 잡힌다. "순항한 이슈의 코드가 무결하다는 뜻은 아니다"의 사례.

## 5. 결론

트리 한 번 fetch로 사이드바·본문 분기 전부 해결, 탭 문서는 `Promise.all` 병렬 로드. PR: #4
