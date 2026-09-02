# issue8 — 드릴다운 사이드바: "펼치는 트리"를 버리고 "들어가는 목록"으로

- 이슈 #17·#23 · PR: #20(드릴다운)·#24(횡스크롤)

> ### 이 문서가 어떻게 바뀌었나 (2026-09-02 재작성)
> ```
> [기존 문서]                              [새 문서 — 지금 이것]
> "접이식 트리 → 드릴다운"        ──▶      왜 파일탐색기 은유를 버렸나(서사)
>  피드백 6개 목록                          각 결정을 문제→고민→선택으로
> 횡스크롤 요약                   ──▶      실제 [기존]↔[변경] diff + 원인 그림
> 리프·풀블리드 용어 던짐          ──▶      낯선 용어는 그 자리에서 한 줄 풀이
> ```

---

## 1. 배경 — 사이드바 모델을 바꾸다

첫 시안은 **접이식 트리**였다 — 전체 트리를 사이드바에 통째로 두고 `▸`를 눌러 펼치는
방식(파일 탐색기 같은). 그런데 사용자 사양으로 재설계했다.

- 사이드바에는 **현재 폴더의 하위만** 보여준다.
- 콘텐츠 영역에는 그 폴더의 README를 그린다.
- 위에는 `< 뒤로`(상위 폴더로)와 `전체트리 >`(전체 구조는 별도 화면)를 둔다.

즉 파일 탐색기가 아니라 **정보 사이트의 섹션 내비게이션** 모델이다 — 지금 있는 곳의
이웃만 보이고, 위아래로 "들어가고 나온다".

> 용어 — 드릴다운(drill-down): 상위에서 하위로 한 단계씩 파고들어가는 탐색 방식.

---

## 2. 화면 확인 반복으로 다듬은 것들

각 항목이 사용자 피드백 1회에 대응한다.

```
1  가운데 정렬 컨테이너 → 전체 폭: 사이드바가 화면 왼쪽 끝, 헤더 아래 전체 높이
2  버튼 스타일 → 글자 링크(< 뒤로 · 전체트리 >), 색 선명하게
3  구분선을 사이드바 좌우 끝까지 (풀블리드)
4  📁/📄 아이콘 제거 → 카테고리(굵게 + 하위 개수 "12 ›") vs 문서(제목만)
5  전체트리: 모달 → /tree 페이지(콘텐츠 영역 렌더), 접기/펼치기, 기본 전부 접힘
6  뒤로가기 = 경로 문자열 계산이 아니라 트리 객체의 prev 링크(backend #21)
```

> 용어 — 풀블리드(full-bleed): 요소를 컨테이너 안쪽 여백까지 무시하고 좌우 끝까지 꽉 채우는 것.

### 결정 (4) 아이콘 제거의 이유

**무엇이 문제였나:** 처음엔 폴더에 📁, 문서에 📄 아이콘을 붙였다.

**무엇을 고민했나:** 폴더 은유는 구현(파일시스템)을 화면에 노출한다. 사용자에게 중요한
건 "이게 카테고리인가 문서인가, 카테고리면 안에 몇 개 있나"이지 "폴더냐"가 아니다.

**그래서 이렇게:** 아이콘을 버리고, 카테고리는 굵게 + 하위 개수(`12 ›`), 문서는 제목만.
개수 표기가 직관·접근성 모두 낫다. 파일 경로 `src/features/wiki/ui/DrillSidebar.tsx`:

```tsx
{folder.children.map((child) => (
  <Link href={`/wiki/${child.path}`} style={{ fontWeight: child.is_subject ? 400 : 600 }}>
    <span>{child.name}</span>
    {!child.is_subject && (                                  // 카테고리에만 개수
      <span style={{ color: "var(--muted)", fontSize: "0.72rem" }}>
        {child.children.length + child.docs.length} ›
      </span>
    )}
  </Link>
))}
```

### 결정 (6) 뒤로가기는 prev 링크로

**무엇이 문제였나:** 상위 폴더로 가는 "뒤로"를 경로 문자열을 잘라서 계산하면(예:
`cs/systems/lsm` → `cs/systems`), 루트나 특수 경우에서 어긋난다.

**무엇을 고민했나:** backend가 트리 노드마다 `prev`(상위 폴더 경로, 루트는 null)를 이미
넣어준다(backend #21). 문자열을 계산하지 말고 이 값을 그대로 쓰면 된다.

**그래서 이렇게:** `TreeNode`에 `prev` 필드를 받고, 그것으로 뒤로 링크를 만들었다.
파일 경로 `src/shared/api/backend.ts`:

```diff
 export interface TreeNode {
-  name: string; path: string; docs: TreeDocRef[]; children: TreeNode[]; is_subject: boolean;
+  name: string; path: string; prev: string | null;   // 상위 폴더 경로 — 루트는 null (backend #21)
+  docs: TreeDocRef[]; children: TreeNode[]; is_subject: boolean;
 }
```

파일 경로 `src/features/wiki/ui/DrillSidebar.tsx`:

```tsx
// 뒤로 = 트리 객체의 prev 링크 (경로 문자열 계산 아님 — backend #21)
const backHref = folder.prev === null && folderPath === ""
  ? null
  : folder.prev === "" || folder.prev === null ? "/" : `/wiki/${folder.prev}`;
```

---

## 3. 곁가지 — portfolio가 트리에서 뭉개진 문제

**무엇이 문제였나:** `portfolio/k-brand-guard` 아래 `01_….md ~ 05_….md`가 폴더 바로
밑에 나열돼 있었다. 우리 트리 모델에서 "하위 폴더 없이 문서만 있는 폴더"는 **리프(주제)**다.

> 용어 — 리프(leaf): 트리에서 더 이상 자식이 없는 끝 노드. 여기선 "주제"로 취급된다.

리프를 클릭하면 문서 하나만 렌더되므로, 5편 중 1편만 보이고 나머지 4편이 화면에서 사라졌다.

**무엇을 고민했나:** 두 갈래가 있었다. (a) 트리 모델을 바꿔 리프에서 문서 목록을 렌더
(b) 각 문서를 폴더로 승격.

**그래서 이렇게:** (b)를 택했다 — `NN_제목/post.md`로 재구조화(study-note 쪽 커밋). 각
글이 트리의 노드가 되고, `post` 종류라 검색·자동완성에도 잡힌다. 실제로 issue9의 자동완성
스모크에서 portfolio 글이 최상위로 올라온 게 이 재구조화의 효과다.

---

## 4. 구현 중 마주친 문제 — 사이드바 횡스크롤 (#23)

**무엇이 문제였나:** 구분선을 사이드바 좌우 끝까지(풀블리드) 보내려고, 패딩이 있는
컨테이너 안에서 **음수 마진**을 썼다: `margin: 0 -1rem; padding: 0 1rem`. 그랬더니 가로
스크롤바가 생겼다 — 음수 마진만큼 nav 콘텐츠 폭이 컨테이너를 넘쳤기 때문이다.

```
[원인]  aside 에 padding: 0 1rem  (안쪽 여백)
          내부 요소가 그 여백을 상쇄하려고 margin: 0 -1rem
          → 요소 폭 = 컨테이너 + 2rem  → 가로 스크롤 발생
```

**무엇을 고민했나:** "부모 패딩 상쇄용 음수 마진"은 overflow 컨테이너와 만나면 스크롤을
만든다. 전폭이 필요하면, 애초에 **부모가 패딩을 갖지 않게** 설계하는 쪽이 정직하다 —
각 섹션이 자기 패딩을 갖게 하면 음수 마진이 필요 없다.

**그래서 이렇게:** aside의 패딩을 없애고, 각 행이 자기 패딩을 갖게 재배치했다.
`overflow-x: hidden`은 안전벨트로 추가. 파일 경로 `src/features/wiki/ui/DrillSidebar.tsx`:

```diff
     <nav style={{ padding: "1rem 0", position: "sticky", top: 53,
-                  maxHeight: "calc(100vh - 53px)", overflowY: "auto" }}>
+                  maxHeight: "calc(100vh - 53px)", overflowY: "auto", overflowX: "hidden" }}>
       <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center",
-                    margin: "0 -1rem 0.9rem", padding: "0 1rem 0.7rem",
+                    padding: "0 1rem 0.7rem", marginBottom: "0.9rem",
                     borderBottom: "1px solid var(--line)" }}>
```

그리고 aside 자체의 좌우 패딩을 제거해, 구분선 행은 자기 패딩만으로 전폭을 자연히 확보한다.
파일 경로 `src/features/wiki/ui/WikiView.tsx`:

```diff
-        <aside style={{ borderRight: "1px solid var(--line)", padding: "0 1rem",
+        <aside style={{ borderRight: "1px solid var(--line)",
                         minHeight: "calc(100vh - 53px)", background: "var(--bg)" }}>
```

---

## 5. 결론

들어가는 목록 + README 콘텐츠 + prev 뒤로가기 + `/tree`(기본 전부 접힘). 파일탐색기 은유를
버리고 섹션 내비게이션으로 갔고, 풀블리드 구분선의 음수 마진 함정도 정직한 방식으로 고쳤다.
PR: #20·#24
