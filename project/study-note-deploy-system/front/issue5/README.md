# issue5 — codex 리뷰: 오탐을 가려내고 공개 경로를 굳히다

- 이슈 #9 · PR: https://github.com/junhyeong9812/study-note-deploy-system-front/pull/9

> ### 이 문서가 어떻게 바뀌었나 (2026-09-02 재작성)
> ```
> [기존 문서]                              [새 문서 — 지금 이것]
> "채택 3 / 기각 3 / 부분 1"       ──▶      각 지적마다: 무엇이 위험했나
>  판정 결과만 나열                        → 무엇을 고민했나 → 그래서 이렇게
> diff 조각만                     ──▶      실제 커밋 diff 전체 + 파일 경로
> in-memory·역참조 용어 던짐       ──▶      낯선 용어는 그 자리에서 한 줄 풀이
> ```

---

## 1. 배경 — 왜 codex 1회였나

front는 표시 계층(화면을 그리는 쪽)이라, 배포 서버(ci-cd)처럼 침해 반경이 크지 않다.
그래서 리뷰 강도를 낮춰 **다른 모델(codex)에게 1회 리뷰**만 받기로 했다(그 사유를 명세에
기록해놨다).

> 용어 — codex 리뷰: 지금까지 쓴 방식 — 전체 소스를 다른 모델에게 주고, 그 지적을 내가
> 하나씩 판정한다. 같은 모델은 같은 맹점을 공유하니, 다른 모델이 내가 못 본 걸 본다.

누적 diff를 보냈더니 7건이 왔다 — 그중 2건은 "빌드가 안 될 것"이라는 P1(가장 높은 심각도)
이었다. 그런데 실제로는 빌드도 배포도 엣지 200까지 이미 끝난 상태였다. 그래서 **오탐(잘못된
지적) 판정부터** 시작했다.

---

## 2. 판정 — 채택한 지적

### 채택 (1) — requestId가 backend로 전파되지 않아 로그가 끊겼다

**무엇이 위험했나:** issue4의 sync 중계는 front가 발행한 requestId를 backend에 넘기지
않았다. 그래서 "이 요청"이 front 로그에는 있는데 backend 로그에서는 다른(혹은 없는) id로
찍혀, 한 요청을 두 서버에 걸쳐 꿸 수 없었다.

**무엇을 고민했나:** issue1에서 세운 규약이 "진입 서버가 발행 → X-Request-Id로 전파"였다.
sync 중계는 이 규약을 지키지 않은 구멍이었다.

**그래서 이렇게:** 전파 헤더 한 줄을 추가했다. 파일 경로 `src/app/api/sync/route.ts`:

```diff
  const response = await fetch(`${BACKEND_URL}/internal/sync`, {
    method: "POST",
-   headers: { "Content-Type": "application/json", "X-Sync-Secret": secret },
+   headers: { "Content-Type": "application/json", "X-Sync-Secret": secret,
+              "X-Request-Id": requestId },             // 규약: 진입 서버 발행 id 전파
    body: body || "{}",
```

### 채택 (2) — 비밀 검증 전에 본문 전체를 메모리에 올리고 있었다

**무엇이 위험했나:** `/api/sync`는 공개 URL이다. 기존 코드는 비밀을 검증하기도 전에
`request.text()`로 본문 전체를 메모리에 올렸다. 즉 인증되지 않은 아무나 거대한 본문을
보내 front(.9)의 메모리를 압박할 수 있었다.

> 용어 — in-memory 적재: 요청 본문을 통째로 서버 메모리에 읽어 들이는 것. 본문이 크면
> 그만큼 메모리를 문다.

**무엇을 고민했나:** sync 본문은 `{commit_sha, request_id, full}` 정도로 아주 작다. 그
이상 클 이유가 없으니 상한을 두고, 헤더에 선언된 크기(`content-length`)를 **본문을 읽기
전에** 먼저 검사하면, 거대 본문은 읽지도 않고 거절할 수 있다.

**그래서 이렇게:** 4KB 상한을 두고, 선언 크기 검사(읽기 전) + 실제 크기 재확인(읽은 뒤)
이중으로 막았다. 파일 경로 `src/app/api/sync/route.ts`:

```diff
+const MAX_BODY_BYTES = 4096;   // sync 본문은 {commit_sha, request_id, full} 뿐 — 그 이상은 거절
+
 export async function POST(request: NextRequest) {
   const requestId = newRequestId();
   const secret = request.headers.get("x-sync-secret") ?? "";
-  const body = await request.text();
+  const declaredLength = Number(request.headers.get("content-length") ?? 0);
+  if (declaredLength > MAX_BODY_BYTES) {
+    return NextResponse.json(
+      { success: false, error: { code: "invalid_request", detail: "body too large" } }, { status: 413 });
+  }
   try {
+    const body = await request.text();                    // 공개 경로 — try 안에서, 상한 재확인
+    if (body.length > MAX_BODY_BYTES) {
+      return NextResponse.json(
+        { success: false, error: { code: "invalid_request", detail: "body too large" } }, { status: 413 });
+    }
```

> 용어 — 413: HTTP 상태 코드 "Payload Too Large"(본문이 너무 큼).

실기동 확인: `Content-Length: 99999` → **413**, 비밀 없는 요청 → **401**.

### 채택 (3) — hash 붙은 md 링크가 `.md.md`로 조회됐다

**무엇이 위험했나:** issue2에서 심은 `resolveHref`는 `.md`를 제거해 `/wiki` 경로를 만드는데,
`other.md#절`처럼 뒤에 hash(`#절`)나 query(`?tab=1`)가 붙으면 `.md`가 hash에 가려져 제거를
못 받았다. 그 결과 `/wiki/.../other.md#절` 같은 경로가 되고, 폴백이 다시 `.md`를 붙여
`other.md.md`를 조회해 404가 났다.

**무엇을 고민했나:** 링크를 `경로 부분`과 `#hash·?query 부분`으로 먼저 나눈 뒤, 경로
부분에만 `.md` 제거를 적용하고 뒷부분은 그대로 보존하면 된다.

**그래서 이렇게:** hash/query를 분리해 보존하도록 고쳤다. 파일 경로 `src/lib/links.ts`
(이 커밋에서 `Markdown.tsx` 안에 있던 함수를 순수 함수 파일로 분리하며 함께 수정):

```diff
+export function resolveHref(href: string | undefined, docDir: string): string {
   if (!href || /^(https?:|mailto:|#)/.test(href)) return href ?? "";
+  const hashIndex = href.search(/[#?]/);                 // pathname 과 #hash·?query 분리
+  const pathname = hashIndex === -1 ? href : href.slice(0, hashIndex);
+  const suffix   = hashIndex === -1 ? "" : href.slice(hashIndex);
-  const clean = href.replace(/\/$/, "").replace(/\.md$/, "");
+  const clean = pathname.replace(/\/$/, "").replace(/\.md$/, "");   // pathname 에만 .md 제거
   const stack = docDir === "" ? [] : docDir.split("/");
   for (const segment of clean.split("/")) {
     if (segment === "..") stack.pop();
     else if (segment !== ".") stack.push(segment);
   }
-  return "/wiki/" + stack.join("/");
+  return "/wiki/" + stack.join("/") + suffix;            // suffix(#절·?query) 되붙임
 }
```

동작 차이:

```
[기존]  resolveHref("other.md#section", "cs/x")  →  "/wiki/cs/x/other.md#section"  → 폴백이 .md.md 조회 → 404
[변경]  resolveHref("other.md#section", "cs/x")  →  "/wiki/cs/x/other#section"     → 정상
```

### 부분 채택 — 단위 테스트 부재

명세 ⑤(검증 방법)에 "md 렌더·트리 변환 최소 테스트"를 적어놓고 안 쓰고 있었다. vitest
6건을 추가했다(`findNode`·`chapterTabs`·`resolveHref` — hash 보존 케이스 포함). 파일 경로
`src/lib/__tests__/links.test.ts`:

```ts
it("hash·query 보존 — other.md#절 이 .md.md 가 되지 않는다 (리뷰 수정)", () => {
  expect(resolveHref("other.md#section", "cs/x")).toBe("/wiki/cs/x/other#section");
  expect(resolveHref("index.md?tab=1", "cs")).toBe("/wiki/cs/index?tab=1");
});
```

---

## 3. 판정 — 기각한 지적 (근거를 남긴다)

### 기각 (1)·(2) — "standalone 설정이 없다 / alias 설정이 없다" (packet 오탐)

**리뷰어 주장:** `next.config`·`tsconfig`가 없으니 빌드가 실패할 것(P1).

**실제 원인:** 내가 리뷰용으로 만든 packet의 **diff 기준 커밋이 잘못**돼, 그 두 파일을
포함한 첫 커밋(스캐폴드)이 diff에서 빠진 것이었다. 파일은 실재하고 빌드·배포·엣지 200까지
끝났다. → 기각.

**교훈:** 리뷰어의 입력(packet)을 만드는 것도 나다. finding이 이상하면 리뷰어보다 **packet을
먼저 의심**해야 한다.

### 기각 (3) → 이후 재채택 — "1/2/3 탭이 항상 3개여야 한다"

당시엔 "코테 2-summary는 의도된 부재"라며 기각했다. **이 기각은 나중에 뒤집혔다** —
사용자 확정(2026-08-28)으로 코테 정리 문서는 추후 작성 예정이라, 부재는 "미작성"일 뿐이었다.
3탭 고정 + "작성 전" 패널로 재채택(issue6).

> 용어 — 역참조(docs[0]): 배열의 첫 원소를 꺼내는 것. 배열이 비어 있으면 없는 걸 꺼내려다
> 오류가 난다.

같은 지적에 딸려온 "`docs[0]` 역참조가 위험하다"는 부분은, `is_subject`의 정의
(`docs.isNotEmpty && children.isEmpty`)상 주제 노드에는 docs가 반드시 하나 이상 있으므로
성립 불가 → 그 부분 기각은 유지. **기각에도 유효기간이 있다** — 근거(사용자 의도)가 바뀌면
재판정한다.

---

## 4. 구현 중 마주친 문제

### vitest가 로컬에서 기동 실패, 도커에선 tsx 파싱 실패

**증상 1:** `SyntaxError: 'node:util' does not provide an export named 'styleText'`
→ 로컬 Node 18에는 없는 API(20.12+에서 생김). 테스트도 빌드처럼 도커(node 22)로 통일했다.

**증상 2:** 도커에서 `Failed to parse source ... Markdown.tsx: jsx to preserve` —
`resolveHref`가 tsx(JSX가 섞인) 파일 안에 있어, 테스트 러너가 JSX까지 파싱해야 했다.

**수정:** 순수 함수를 `src/lib/links.ts`로 분리했다(채택 3의 diff가 바로 이 분리다).
테스트가 쉬워졌고, "로직은 lib·표시는 component"라는 결도 맞아졌다. **테스트하기 어려운
위치가 곧 설계 신호**였던 사례다.

---

## 5. 결론

채택 3 + 테스트 6, 기각 3(전부 근거 기록). 공개 경로(`/api/sync`)가 401/413으로 닫힌
것을 실기동으로 확인했다. 오탐 2건은 코드가 아니라 내 packet 실수였다는 것이 남긴 교훈이다.
PR: #9
