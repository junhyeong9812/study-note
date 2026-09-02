# issue2 — 위키 뷰: 라우트 하나로 폴더·주제·문서를 다 그린다

- 이슈 #3 · PR: https://github.com/junhyeong9812/study-note-deploy-system-front/pull/4

> ### 이 문서가 어떻게 바뀌었나 (2026-09-02 재작성)
> ```
> [기존 문서]                              [새 문서 — 지금 이것]
> "라우트 하나가 분기"            ──▶      왜 라우트를 나누지 않았나(대안 탈락 이유)
>  선택만 나열                              → 무엇을 고민했나 → 그래서 이렇게
> resolveHref 예시만              ──▶      그 함수의 실제 코드 + 이후 결함까지 예고
> is_subject·SSR 용어 던짐         ──▶      낯선 용어는 그 자리에서 한 줄 풀이
> ```

---

## 1. 배경 — 트리 하나로 세 종류 화면을 그려야 한다

backend의 `/api/tree`는 노트 전체를 트리(나무 구조)로 준다. 이 트리를 화면 세 종류로
바꾸는 것이 이 이슈다.

- **폴더 노드**면 → 하위 목록을 보여주는 탐색 화면
- **주제 노드**(리프 = 더 이상 하위 폴더가 없는 끝 노드)면 → 1/2/3 **3탭** 화면
- **단독 문서(post)**면 → 본문 하나만 그리는 화면

> 용어 — is_subject: 트리 노드가 "주제(리프)인가"를 알려주는 참/거짓 표시. backend가
> "하위 폴더 없이 문서만 있는 폴더 = 주제"라고 판정해 이 값을 넣어 보낸다.
> 용어 — SSR(Server-Side Rendering): 브라우저가 아니라 서버(front) 안에서 미리 HTML을
> 만들어 내려보내는 것. 여기선 front가 backend에서 데이터를 받아 HTML로 그려 내려준다.

md(마크다운)를 HTML로 바꾸는 렌더는 front 책임이다 — backend는 콘텐츠 JSON(원문 문자열)만
주고, 보이는 모양은 front가 만든다는 경계를 설계 때 정해뒀다.

주제 화면의 탭이 "3탭 가림 없음"인 것은 인터뷰에서 사용자가 결정한 사항이다.

---

## 2. 검토한 방식들

### 결정 (1) — 라우트를 나누지 않고, 하나가 노드 종류로 분기한다

**무엇이 문제였나:** 폴더·주제·문서 세 종류를 어떻게 URL과 코드로 나눌지가 문제였다.
직관적으로는 `/folder/...`, `/subject/...`, `/doc/...`처럼 라우트(주소별 처리기)를 셋으로
나누고 싶어진다.

**무엇을 고민했나:** 라우트를 셋으로 나누면, "이 경로가 폴더인가 주제인가 문서인가"라는
판단을 URL 설계에도, backend 모델에도, **두 곳에 이중으로** 유지해야 한다. 그런데 그
판단은 트리의 `is_subject` 값 하나가 이미 준다. 판단을 두 번 관리하면 언젠가 두 곳이
어긋난다.

**그래서 이렇게:** 라우트를 하나(`/wiki/[...slug]` — 슬래시로 이어진 경로 전체를 받는
캐치올 라우트)만 두고, 그 안에서 노드 종류로 분기했다. 파일 경로
`src/app/wiki/[...slug]/page.tsx`:

```tsx
const node = findNode(treeData.tree, currentPath);
if (node && !node.is_subject) {
  body = <FolderView node={node} />;                       // 폴더 탐색
} else if (node && node.is_subject) {
  const tabs = chapterTabs(node);                          // 주제(리프) — 1/2/3 탭
  if (tabs.length > 0) { /* Tabs 로 3탭 */ }
  else { /* post 단일 본문 */ }
} else {
  // 트리에 폴더가 없으면 문서 경로일 수 있다 (예: /wiki/cs/index)
  try { const doc = await fetchDoc(currentPath + ".md", requestId); ... }
  catch { notFound(); }                                    // 그래도 없으면 404
}
```

즉 흐름은 이렇다.

```
/wiki/<경로>  ──▶  findNode 로 트리에서 노드 찾기
                       │
        ┌──────────────┼───────────────────────────┐
   폴더(!is_subject)   주제(is_subject)        트리에 없음
        │                   │                        │
   하위 목록 렌더      탭 있으면 3탭          문서 직접 조회 폴백
   (FolderView)        없으면 post 본문       (cs/index 같은 폴더 직속 문서)
                                                  실패 → 404
```

### 결정 (2) — 탭은 "있는 것만" 보여준다 (당시 판단, 이후 뒤집힘)

**무엇이 문제였나:** 주제 하나에는 1·질문 / 2·정리 / 3·정답 세 종류 문서가 있을 수
있는데, 코딩테스트 주제에는 "2·정리(summary)"가 없었다.

**무엇을 고민했나:** 없는 탭을 빈 채로 보여줄지, 아예 감출지. 당시에는 "없는 건 감춘다"로
판단했다.

**그래서 이렇게:** 있는 종류만 정렬해 탭으로 냈다. 파일 경로 `src/lib/tree.ts`(당시):

```ts
const KIND_ORDER = { question: 1, summary: 2, answer: 3 };
export function chapterTabs(node) {
  return node.docs.filter(d => KIND_ORDER[d.doc_kind])
                  .sort((a, b) => KIND_ORDER[a.doc_kind] - KIND_ORDER[b.doc_kind]);
}
```

**이 판단은 나중에 뒤집혔다.** 사용자 확정(2026-08-28) — 코딩테스트의 정리 문서는
**추후 문제 분석으로 작성할 예정**이라, 그 부재는 "설계된 부재"가 아니라 단지 "아직
미작성"이었다. 그래서 issue6에서 3탭 고정 + "작성 전" 패널로 바꿨다(리뷰 finding을 새
근거로 재채택). 당시 "의도된 부재"라는 서술은, rename 때의 합의("빈 파일을 만들지 않는다")를
내가 과장한 오류였다. 자세한 뒤집힘 과정은 issue5·issue6.

### 결정 (3) — 상대 링크 치환을 렌더 시점에 한다

**무엇이 문제였나:** 노트 원문에는 `](../kafka-why-fast/)`나 `](2-summary.md)` 같은
**상대 마크다운 링크**가 흔하다. 이걸 그대로 두면 브라우저는 실제로 없는 경로로 이동해
링크가 깨진다.

**무엇을 고민했나:** 링크를 backend에서 미리 고쳐 보낼 수도 있지만, backend는 "콘텐츠
JSON만"이라는 경계를 정해뒀다. 링크를 `/wiki/...` 웹 경로로 바꾸는 것은 화면(front)의
일이다.

**그래서 이렇게:** react-markdown이 링크를 그릴 때 쓰는 `a` 컴포넌트를 갈아끼워, 문서
위치를 기준으로 상대 링크를 `/wiki/...`로 계산해 치환했다. 파일 경로
`src/components/Markdown.tsx`(당시):

```ts
/** 노트 내 상대 md 링크를 /wiki 경로로 치환 — docPath 기준 상대 해석 */
function resolveHref(href: string | undefined, docDir: string): string {
  if (!href || /^(https?:|mailto:|#)/.test(href)) return href ?? "";
  const clean = href.replace(/\/$/, "").replace(/\.md$/, "");
  const stack = docDir === "" ? [] : docDir.split("/");
  for (const segment of clean.split("/")) {
    if (segment === "..") stack.pop();
    else if (segment !== ".") stack.push(segment);
  }
  return "/wiki/" + stack.join("/");
}
```

동작 예:

```
resolveHref("../kafka-why-fast/", "cs/systems/lsm-tree")  → "/wiki/cs/systems/kafka-why-fast"
resolveHref("2-summary.md",       "cs/lsm-tree")          → "/wiki/cs/lsm-tree/2-summary"
```

이 함수에는 **결함이 하나 숨어 있었다** — `.md` 뒤에 `#절`(hash)이나 `?query`가 붙은
링크를 처리하지 못한다. `other.md#절` 같은 링크가 이상하게 변환되는 문제인데, 이건
issue5의 코드 리뷰에서 잡혀 수정된다. 5장을 보라.

---

## 3. 실증

```
$ curl .../wiki/cs/systems/lsm-tree
tabs: ['1 · 질문', '2 · 정리', '3 · 정답']    본문 포함: True    사이드바: True
folder:200  post:200  404:404               edge-subject:200
```

폴더·주제·문서 세 경로 모두 200, 없는 경로는 404, 엣지(오라클)를 통한 주제 페이지도 200.

---

## 4. 구현 중 마주친 문제

이 이슈 자체는 순항했다. 다만 여기서 심은 `resolveHref`의 결함(hash 붙은 링크)이
issue5의 리뷰에서 잡힌다. **"순항한 이슈의 코드가 곧 무결한 코드라는 뜻은 아니다"**의
사례다 — 빌드가 통과하고 화면이 뜬다고 해서 모든 입력을 다룬다는 보장은 없다.

---

## 5. 결론

트리를 한 번만 fetch해 사이드바·본문 분기를 전부 해결했고, 탭 문서는 `Promise.all`로
병렬 로드했다. 라우트 하나가 노드 종류로 분기하는 구조라, backend 모델과 URL 설계를
이중 관리하지 않는다. PR: #4
