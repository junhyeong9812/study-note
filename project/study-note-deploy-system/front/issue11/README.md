# issue11 — 우측 채팅 패널: 스트림을 타자로 그리고, 쿠키를 왕복시킨다

- 이슈 #25 · PR: #26

> ### 이 문서가 어떻게 바뀌었나 (2026-09-02 재작성)
> ```
> [기존 문서]                              [새 문서 — 지금 이것]
> "쿠키 왕복이 핵심"              ──▶      왜 왕복해야 세션이 서나(서사)
>  코드 조각만                             각 결정을 문제→고민→선택으로
> 스트림 렌더 예시                ──▶      실제 route·ChatPanel 코드 + 레이아웃 diff
> 스트림·에스컬레이션 용어 던짐    ──▶      낯선 용어는 그 자리에서 한 줄 풀이
> ```

---

## 1. 배경 — 빈 우측 공간에 "문서에게 묻는" 채팅

문서 페이지 오른쪽 빈 공간에 채팅 패널(340px)을 둔다. **현재 문서에 대해** 묻고, 답은
ChatGPT처럼 타자 치듯 흐른다. 패널은 문서 페이지에서만 뜨고(폴더/트리 화면엔 없음).

---

## 2. 결정 (1) — ReadableStream을 조각조각 렌더한다

**무엇이 문제였나:** LLM 답변은 한 번에 완성돼 오지 않고 토큰(글자 조각) 단위로 흘러온다.
이걸 다 모아서 한 번에 보여주면 "몇 초간 멈춤 → 답 통째로 등장"이 되어 답답하다.

> 용어 — 스트림(ReadableStream): 응답이 한 덩어리가 아니라 조각들이 순차로 흘러오는 통로.
> 용어 — 토큰: 모델이 생성하는 최소 단위 조각(대략 단어 일부).

**무엇을 고민했나:** 조각이 도착할 때마다 마지막 assistant 메시지에 이어붙여 다시 그리면,
글자가 타자처럼 늘어나는 효과가 난다.

**그래서 이렇게:** 스트림 reader로 조각을 읽어 마지막 메시지에 누적했다. 파일 경로
`src/features/chat/ui/ChatPanel.tsx`:

```tsx
const reader = response.body.getReader();
const decoder = new TextDecoder();
while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  const token = decoder.decode(value, { stream: true });
  setMessages((previous) => {
    const next = [...previous];
    next[next.length - 1] = { ...next[next.length - 1],
      content: next[next.length - 1].content + token };   // 마지막 메시지에 이어붙임
    return next;
  });
}
```

생성 중에는 커서(`▌`)를 마지막 메시지 뒤에 붙여 "쓰는 중"을 표시한다.

---

## 3. 결정 (2) — BFF는 쿠키를 양방향으로 왕복시켜야 한다

**무엇이 문제였나:** 세션(대화가 누구 것인지 식별하는 상태)은 backend가 쿠키로 발급한다.
그런데 front가 그냥 요청만 넘기면, backend가 준 세션 쿠키가 브라우저에 도달하지 못하고,
브라우저가 가진 쿠키도 backend에 전달되지 못한다 — 매 요청이 "처음 온 사람"이 된다.

> 용어 — set-cookie / cookie: `set-cookie`는 서버가 브라우저에게 "이 쿠키를 저장해"라고
> 내려보내는 헤더(상류→브라우저). `cookie`는 브라우저가 서버로 도로 보내는 헤더(브라우저→상류).
> 세션이 서려면 둘 다 왕복해야 한다.

**무엇을 고민했나:** front 프록시가 `set-cookie`(상류→브라우저)와 `cookie`(브라우저→상류)를
양방향으로 전달해야 세션이 성립한다. 그리고 스트림 바디는 버퍼링(다 모아 뒀다 보내기)하지
말고 그대로 흘려야 타자 효과가 산다.

**그래서 이렇게:** 파일 경로 `src/app/api/chat/route.ts`:

```ts
/** app = 라우팅만 — 채팅 스트림 패스스루(쿠키 양방향 전달이 핵심: 세션은 backend가 발급) */
export async function POST(request: NextRequest) {
  const upstream = await fetch(`${BACKEND_URL}/api/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      cookie: request.headers.get("cookie") ?? "",       // 브라우저 → 상류
    },
    body: await request.text(),
    signal: AbortSignal.timeout(180_000),
  });
  const headers = new Headers({ "Content-Type": "text/plain; charset=utf-8" });
  const setCookie = upstream.headers.get("set-cookie");
  if (setCookie) headers.set("set-cookie", setCookie);    // 상류 → 브라우저
  return new Response(upstream.body, { status: upstream.status, headers });  // 스트림 그대로 (버퍼링 X)
}
```

```
[쿠키를 안 넘기면]  브라우저 ─(쿠키 없음)→ front ─(쿠키 없음)→ backend  → 매번 새 세션
[양방향 왕복]       브라우저 ──cookie──▶ front ──cookie──▶ backend
                    브라우저 ◀─set-cookie─ front ◀─set-cookie─ backend  → 세션 유지
```

---

## 4. 결정 (3) — 페이지별 대화 + 수동 에스컬레이션

**페이지별 대화:** `docPath`가 바뀌면 이력을 다시 로드한다(문서마다 다른 대화). backend의
Redis 키가 path별이라 자연스럽게 갈린다. 파일 경로 `src/features/chat/ui/ChatPanel.tsx`:

```tsx
useEffect(() => {                                    // 페이지(doc)별 이력 로드
  setMessages([]);
  fetch(`/api/chat/history?doc_path=${encodeURIComponent(docPath)}`)
    .then((response) => response.json())
    .then((body) => { if (body.success) setMessages(body.data.messages); })
    .catch(() => {});
}, [docPath]);
```

**에스컬레이션 — 자동이 아니라 수동:**

> 용어 — 에스컬레이션(escalation): 로컬 모델(작은 7B)이 답한 뒤, 더 강한 모델(Claude)에게
> 다시 물어 더 정확한 답을 받는 것.

**무엇이 문제였나:** 로컬 7B 모델이 스스로 "내 답이 부족하니 Claude로 넘겨야겠다"를 판정하게
할 수도 있다. 그런데 작은 모델의 자가 판정은 과신하기 쉽다(틀린 답을 자신 있게 낸다).

**그래서 이렇게:** 자동 전환을 하지 않고, 답변 아래 **"더 정확한 답변 (Claude)" 버튼**을
두어 사용자가 직접 트리거하게 했다. 누르면 마지막 질문을 escalate로 보내고, Claude 답변은
테두리로 구분한다. 브리지(Claude 연결 통로)가 오프라인이면 "지금은 로컬 답변만 가능"으로
우아하게 안내한다. 파일 경로 `src/features/chat/ui/ChatPanel.tsx`:

```tsx
next[next.length - 1] = body.success
  ? { role: "assistant", content: body.data.answer, source: "claude" }
  : { role: "assistant", source: "claude",
      content: body.error?.code === "escalate_unavailable"
        ? "지금은 로컬 답변만 가능합니다 (Claude 브리지 오프라인)."
        : "Claude 응답에 실패했습니다." };
```

---

## 5. 레이아웃 — 문서 페이지에서만 3열로

**무엇이 문제였나:** 채팅 패널은 문서 페이지에서만 필요하다(폴더/트리 화면엔 붙일 문서가
없다).

**그래서 이렇게:** `chatDocPath`가 있을 때만 3열(사이드바·본문·채팅), 없으면 기존 2열.
파일 경로 `src/features/wiki/ui/WikiView.tsx`:

```diff
+  const columns = chatDocPath ? "260px minmax(0, 1fr) 340px" : "260px minmax(0, 1fr)";
   return (
     <div>
       <Header />
-      <div style={{ display: "grid", gridTemplateColumns: "260px minmax(0, 1fr)" }}>
+      <div style={{ display: "grid", gridTemplateColumns: columns }}>
         <aside ...><DrillSidebar folder={folder} folderPath={folderPath} /></aside>
         <main ...><div style={{ maxWidth: 860 }}>{body}</div></main>
+        {chatDocPath && (
+          <aside style={{ borderLeft: "1px solid var(--line)", background: "var(--bg)" }}>
+            <ChatPanel docPath={chatDocPath} />
+          </aside>
+        )}
       </div>
```

```
[폴더/트리 화면]  [사이드바 260px][본문 1fr]
[문서 화면]       [사이드바 260px][본문 1fr][채팅 340px]
```

주제 페이지에서는 채팅 컨텍스트로 정리(summary) 문서를 우선 쓴다(없으면 첫 문서).

---

## 6. 결론

엣지 최종 E2E: `www.junproject.xyz` 문서 페이지에서 채팅 스트림("블룸 필터는…")이 타자로
흐르고, 에스컬레이션 버튼으로 Claude 답변까지 확인. BFF는 쿠키를 양방향 왕복시켜 세션을
세우고, 스트림을 버퍼링 없이 흘린다. PR: #26
