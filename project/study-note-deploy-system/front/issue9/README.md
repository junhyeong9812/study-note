# issue9 — 검색 자동완성: ES가 찾고, front는 이스케이프 후 강조만 한다

- 이슈 #18 · PR: #21 (backend issue11과 쌍)

> ### 이 문서가 어떻게 바뀌었나 (2026-09-02 재작성)
> ```
> [기존 문서]                              [새 문서 — 지금 이것]
> "마커 프로토콜"                 ──▶      왜 <mark> HTML을 안 받았나(XSS 서사)
>  결론만                                  → 무엇을 고민했나 → 그래서 이렇게
> 흐름 한 줄                      ──▶      실제 SearchBar·mark·suggest 코드 + 흐름도
> 디바운스·collapse 용어 던짐      ──▶      낯선 용어는 그 자리에서 한 줄 풀이
> ```

---

## 1. 배경 — 검색을 "입력 중"으로 앞당기다

기존 헤더 검색은 Enter 전용이었다. 요구는 둘이다.

- 돋보기 클릭으로도 검색되게.
- **입력 중 자동완성** — 제목이든 내용이든 일치하면 리스트업하고, 내용 일치면 그 일치
  부분을 포함한 1문장을 보여주되 일치 부분을 강조.

---

## 2. 방식 — 마커 프로토콜로 XSS를 구조적으로 차단한다

**무엇이 문제였나:** "일치 부분을 강조"하려면 그 부분을 `<mark>` 같은 걸로 감싸야 한다.
가장 쉬운 방법은 backend(ES)가 `<mark>정렬</mark>`처럼 HTML을 만들어 보내고, front가 그걸
그대로 화면에 꽂는 것이다. 그런데 노트 본문에 악의적이거나 우연한 HTML이 들어 있으면,
그 HTML이 그대로 실행된다.

> 용어 — ES(Elasticsearch): 검색 엔진. highlight 기능으로 "일치한 부분"을 표시해준다.
> 용어 — XSS(Cross-Site Scripting): 화면에 남의 HTML/스크립트를 심어 실행시키는 공격.

**무엇을 고민했나:** front가 backend의 HTML을 그대로 삽입하려면 `dangerouslySetInnerHTML`
(React에서 HTML 문자열을 이스케이프 없이 꽂는, 이름부터 "위험한" 통로)을 써야 하는데,
이건 XSS 통로를 여는 것과 같다. 반대로, 강조 위치만 **일반 문자로는 안 나올 마커**로
표시해 보내면, front는 텍스트를 통째로 이스케이프한 뒤 마커 위치에만 `<mark>`를 끼우면
된다 — HTML을 삽입하는 게 아니라 React 요소를 조립하는 것이라, 이스케이프를 우회할 길
자체가 없다.

> 용어 — 이스케이프(escape): `<`, `>` 같은 특수문자를 화면에 "글자 그대로" 보이게 바꾸는
> 것. React는 텍스트를 넣으면 자동으로 이스케이프한다.

**그래서 이렇게:** backend는 일치 부분을 `⟦m⟧정렬⟦/m⟧`처럼 마커로 감싸 보낸다. front는
텍스트를 마커로 쪼개, 사이의 조각만 `<mark>`로 재조립한다. 파일 경로
`src/features/search/lib/mark.tsx`:

```tsx
/** ⟦m⟧…⟦/m⟧ 마커를 <mark>로 — 텍스트는 React가 이스케이프하므로 HTML 주입 원천 차단 */
export function renderMarked(text: string): ReactNode[] {
  return text.split("⟦m⟧").flatMap((piece, index) => {
    if (index === 0) return [piece];
    const [marked, ...rest] = piece.split("⟦/m⟧");
    return [
      <mark key={index} style={{ background: "var(--accent-bg)", color: "var(--accent)",
                                 padding: 0, fontWeight: 700 }}>{marked}</mark>,
      rest.join("⟦/m⟧"),
    ];
  });
}
```

```
[탈락한 방식]  backend가 "<mark>정렬</mark>" HTML → front가 dangerouslySetInnerHTML
               → 노트 본문의 HTML도 그대로 실행됨 (XSS)
[택한 방식]    backend가 "⟦m⟧정렬⟦/m⟧" 마커 → front가 이스케이프 후 <mark> 조립
               → HTML 삽입 경로가 없음 (구조적으로 XSS 불가)
```

---

## 3. 흐름 — 디바운스와 프록시

```
입력 → 200ms 디바운스 → front /api/suggest(BFF) → backend ES(collapse·highlight)
리스트: 제목(강조) + 경로 + 스니펫(강조) · ↑↓ 선택 · Enter/돋보기 → /search · 클릭 → 해당 문서
```

> 용어 — 디바운스(debounce): 입력이 멈추고 일정 시간(여기선 200ms) 지난 뒤에야 요청을
> 보내는 것. 타자 한 글자마다 요청이 쏟아지는 걸 막는다.
> 용어 — collapse: ES가 같은 문서의 여러 히트를 하나로 접어 문서당 한 줄만 내는 것.

입력 → 디바운스 → 자동완성 요청은 `SearchBar`에서. 파일 경로 `src/shared/ui/SearchBar.tsx`:

```tsx
useEffect(() => {                                   // 입력 → 200ms 디바운스 → ES 자동완성
  if (debounce.current) clearTimeout(debounce.current);
  const trimmed = query.trim();
  if (!trimmed) { setItems([]); setActive(-1); return; }
  debounce.current = setTimeout(() => {
    fetch(`/api/suggest?q=${encodeURIComponent(trimmed)}`)
      .then((response) => response.json())
      .then((body) => { if (body.success) { setItems(body.data.items); setActive(-1); } })
      .catch(() => {});
  }, 200);
}, [query]);
```

`↑↓`로 항목 선택, Enter는 선택 항목이 있으면 그 문서로 없으면 검색 페이지로:

```tsx
onKeyDown={(event) => {
  if (event.key === "ArrowDown") { event.preventDefault(); setActive((a) => Math.min(a + 1, items.length - 1)); }
  if (event.key === "ArrowUp") { event.preventDefault(); setActive((a) => Math.max(a - 1, -1)); }
  if (event.key === "Escape") setItems([]);
}}
```

BFF 프록시는 issue3의 검색 프록시처럼 봉투 그대로 중계. 파일 경로 `src/app/api/suggest/route.ts`:

```ts
/** app = 라우팅만 — ES 자동완성 프록시 (봉투 그대로) */
export async function GET(request: NextRequest) {
  const query = request.nextUrl.searchParams.get("q") ?? "";
  try {
    const response = await fetch(
      `${BACKEND_URL}/api/suggest?q=${encodeURIComponent(query)}`,
      { headers: { "X-Request-Id": newRequestId() }, signal: AbortSignal.timeout(5_000) },
    );
    return NextResponse.json(await response.json(), { status: response.status });
  } catch {
    return NextResponse.json({ success: false, error: { code: "backend_unreachable" } }, { status: 503 });
  }
}
```

제목·스니펫을 그릴 때 `renderMarked`를 통과시켜 일치 부분만 강조된다(SearchBar의 드롭다운).

---

## 4. 결론

자동완성이 portfolio 글까지 즉시 잡는다(issue8의 재구조화 시너지). 강조는 마커 프로토콜로
XSS 없이 구현했다 — front는 찾지 않고 이스케이프 후 강조만 한다. 상세 워크플로우는
deploy-study-note `docs/workflow/search.md`. PR: #21
