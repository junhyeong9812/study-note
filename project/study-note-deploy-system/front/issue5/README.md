# issue5 — codex 리뷰: 오탐 판정과 공개 경로 굳히기

- PR: https://github.com/junhyeong9812/study-note-deploy-system-front/pull/9

## 1. 배경

front는 표시 계층이라 듀얼 풀패스 대신 **codex 1회 리뷰**로 강도를 낮췄다(명세에 사유
기록). 누적 diff를 보냈더니 7건 — 그중 2건이 "빌드가 안 될 것"이라는 P1이었다.
실제로는 빌드도 배포도 끝난 상태. 오탐 판정부터 시작.

## 2. finding 판정 (7건)

### 기각 2 — "standalone 설정이 없다 / alias 설정이 없다" (packet 오탐)

리뷰어 주장: `next.config`·`tsconfig`가 없으니 빌드 실패할 것. 실제 원인은 **내가 만든
packet의 diff 기준 커밋이 잘못**돼 첫 커밋(스캐폴드 — 그 두 파일 포함)이 diff에서 빠진
것. 파일은 실재하고 빌드·배포·엣지 200까지 끝났다. → 기각. 교훈: **리뷰어의 입력을
만드는 것도 나** — finding이 이상하면 리뷰어보다 packet을 먼저 의심.

### 기각 1 → 이후 재채택 — "1/2/3 탭이 항상 3개여야 한다"

당시엔 "코테 2-summary는 의도된 부재"라는 이유로 기각했다. **이 기각은 나중에
뒤집혔다**: 사용자 확정(2026-08-28) — 코테 서머리는 문제 분석으로 작성 예정이라
부재는 "미작성"일 뿐. 3탭 고정 + "작성 전" 패널로 재채택(issue6). `docs[0]` 역참조
위험 지적은 `is_subject = docs.isNotEmpty && children.isEmpty` 정의상 성립 불가 — 그
부분 기각은 유지. **기각에도 유효기간이 있다** — 근거(사용자 의도)가 바뀌면 재판정.

### 채택 3 — 전부 공개 경로(/api/sync)와 링크 처리

**① requestId 미전파** — 중계에서 front가 발행한 id를 backend에 안 넘겨 로그가 끊김:

```diff
  headers: { "Content-Type": "application/json", "X-Sync-Secret": secret,
+            "X-Request-Id": requestId },     // 규약: 진입 서버 발행 id 전파
```

**② 본문 무제한 적재** — 비밀 검증 **전에** `request.text()`로 본문 전체를 메모리에
올린다. 공개 URL이니 누구나 거대 본문으로 .9 메모리를 압박 가능:

```diff
+ const MAX_BODY_BYTES = 4096;   // sync 본문은 {commit_sha, request_id, full} 뿐
+ if (Number(request.headers.get("content-length") ?? 0) > MAX_BODY_BYTES)
+   return NextResponse.json({ success:false, error:{ code:"invalid_request", ... } }, { status: 413 });
  try {
+   const body = await request.text();       // try 안으로 + 상한 재확인
```

실기동: `Content-Length: 99999` → **413**, 무인증 → **401** 확인.

**③ hash 붙은 md 링크 오변환** — `other.md#절`이 `.md` 제거를 못 받아
`/wiki/.../other.md#절` → 폴백이 `.md`를 다시 붙여 `other.md.md` 조회(404):

```diff
+ const hashIndex = href.search(/[#?]/);           // pathname과 #hash·?query 분리
+ const pathname = hashIndex === -1 ? href : href.slice(0, hashIndex);
- const clean = href.replace(/\.md$/, "");
+ const clean = pathname.replace(/\.md$/, "");     // pathname에만 .md 제거, suffix는 보존
```

### 부분 채택 1 — 단위 테스트 부재

명세 ⑤의 "md 렌더·트리 변환 최소 테스트"를 안 쓰고 있었다. vitest 6건 추가(findNode·
chapterTabs·resolveHref — hash 보존 케이스 포함).

## 3. 구현 중 마주친 문제

### vitest가 로컬에서 기동 실패, 도커에선 tsx 파싱 실패

**증상 1**: `SyntaxError: 'node:util' does not provide an export named 'styleText'`
→ 로컬 Node 18에는 없는 API(20.12+). 테스트도 빌드처럼 도커(node 22)로 통일.

**증상 2**: 도커에서 `Failed to parse source ... Markdown.tsx: jsx to preserve` —
`resolveHref`가 tsx 파일 안에 있어 vitest가 JSX까지 파싱해야 했다.
**수정**: 순수 함수를 `lib/links.ts`로 분리 — 테스트가 쉬워졌고, "로직은 lib·표시는
component"라는 결이 맞아졌다. **테스트하기 어려운 위치가 곧 설계 신호**였던 사례.

## 4. 결론

채택 3 + 테스트 6, 기각 3(전부 근거 기록). 공개 경로가 401/413으로 닫힌 걸 실기동
확인. PR: #9
