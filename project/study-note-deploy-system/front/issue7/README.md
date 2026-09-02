# issue7 — /api/deploy 중계 + 절대경로 임포트 정책 고정

- 이슈 #12·#14·#15 · PR: #13(중계)·#14(임포트 정책)·#16(Actions)

> ### 이 문서가 어떻게 바뀌었나 (2026-09-02 재작성)
> ```
> [기존 문서]                              [새 문서 — 지금 이것]
> "sync와 동형"                   ──▶      왜 같은 패턴을 재사용했나(서사)
> "패턴이 두 번째라 지적 없음"     ──▶      실제 relay.ts 코드 + Actions·compose diff
> alias 함정 요약                 ──▶      [기존]↔[변경] + 도구별 리졸버 설명
> ```

---

## 1. /api/deploy 중계 — sync와 완전 동형

**무엇이 문제였나:** 배포 요청도 색인(sync)과 똑같이 바깥(GitHub Actions)에서 집 안
(ci-cd master)으로 들어와야 한다. 바깥 노출 지점은 front 하나뿐이니, front가 중계해야 한다.

> 용어 — ci-cd master: 배포 요청을 접수해 어느 agent로 보낼지 정하는 배포 서버의 접수부.
> front는 이 master에게 요청을 넘기기만 한다.

**무엇을 고민했나:** 이 요청 형태는 issue4·issue5에서 sync 중계로 이미 다뤄봤다. 비밀
패스스루, 4KB 본문 상한, requestId 전파 — 그때 리뷰로 배운 것들을 그대로 옮기면 된다.
새로 발명할 게 없다.

**그래서 이렇게:** sync에서 확립한 원칙 그대로 옮겼다. app 라우트는 위임만 하고, 실제
로직은 feature의 `relay.ts`에 뒀다. 파일 경로 `src/features/deploy/lib/relay.ts`:

```ts
/** Actions → ci-cd master 배포 중계. sync와 동형 — front는 비밀을 저장·검증하지 않는다. */
export async function relayDeploy(secret: string, declaredLength: number,
                                  readBody: () => Promise<string>): Promise<RelayResult> {
  const requestId = newRequestId();
  if (declaredLength > MAX_BODY_BYTES) {                 // 읽기 전 선언 크기 검사 (issue5 교훈)
    return { status: 413, body: { success: false, error: { code: "invalid_request", detail: "body too large" } } };
  }
  try {
    const body = await readBody();
    if (body.length > MAX_BODY_BYTES) { ... }            // 읽은 뒤 재확인
    const response = await fetch(`${MASTER_URL}/deploy`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Deploy-Secret": secret,
                 "X-Request-Id": requestId },            // 비밀 패스스루 + requestId 전파
      body: body || "{}",
      signal: AbortSignal.timeout(10_000),
    });
    ...
```

app 라우트는 HTTP 껍데기만 — 파일 경로 `src/app/api/deploy/route.ts`:

```ts
/** app = 라우팅만 — HTTP 껍데기, 로직은 feature */
export async function POST(request: NextRequest) {
  const result = await relayDeploy(
    request.headers.get("x-deploy-secret") ?? "",
    Number(request.headers.get("content-length") ?? 0),
    () => request.text(),
  );
  return NextResponse.json(result.body as object, { status: result.status });
}
```

**패턴이 두 번째라, 리뷰 지적 없이 처음부터 맞게 나왔다** — 첫 구현(sync)에서 리뷰로
배운 것(requestId 전파·본문 상한)이 재사용된 사례다.

이 중계가 부르는 master 주소는 compose 환경변수로 주입한다. 파일 경로 `docker-compose.yml`:

```diff
       LOG_REDIS_URL: ${LOG_REDIS_URL:-}
       SERVER_NAME: front
+      DEPLOY_MASTER_URL: ${DEPLOY_MASTER_URL:-}   # ci-cd master(.9:15000) — 배포 .env
```

그리고 study-note가 아니라 **front 리포 자신의** main push 때 배포를 부르는 Actions.
파일 경로 `.github/workflows/deploy.yml`:

```yaml
on: { push: { branches: [main] } }
jobs:
  trigger:
    runs-on: ubuntu-latest
    steps:
      - name: trigger deploy (빌드는 대상 호스트에서 — git pull 방식)
        run: |
          curl -sS -X POST "https://www.junproject.xyz/api/deploy" \
            -H "X-Deploy-Secret: ${{ secrets.DEPLOY_SECRET }}" \
            -H "Content-Type: application/json" \
            -d "{\"service\": \"front\", \"commit_sha\": \"${{ github.sha }}\", \"request_id\": \"gh-${GITHUB_RUN_ID}\"}"
```

```
front main push ── Actions curl ──▶ www ──▶ front /api/deploy ──relay──▶ ci-cd master /deploy
                                            (비밀 패스스루·4KB·reqId)      (git pull + 재빌드)
```

---

## 2. 절대경로 임포트 정책 (사용자 확정)

**무엇이 문제였나:** issue6의 features 재편 때, 파일 내부의 상대 임포트만 3회에 걸쳐
빌드를 깨뜨렸다. 근본 원인은 개별 실수가 아니라 **정책 부재** — 상대/절대가 섞여 있으면
파일 이동이 임포트를 깨뜨린다.

**무엇을 고민했나:** 같은 사고를 다시 겪지 않으려면, "같은 폴더 안이라도 절대경로만
쓴다"를 정책으로 못 박고 잔존 상대 임포트를 전수 제거해야 한다.

**그래서 이렇게:** `@/...` 절대경로만 사용하도록 정하고, 잔존 상대 임포트 7건을 전수
제거했다. 파일 경로 `src/features/wiki/ui/WikiView.tsx`:

```diff
 import Header from "@/shared/ui/Header";
-import Markdown from "./Markdown";
-import Sidebar from "./Sidebar";
-import Tabs from "./Tabs";
+import Markdown from "@/features/wiki/ui/Markdown";
+import Sidebar from "@/features/wiki/ui/Sidebar";
+import Tabs from "@/features/wiki/ui/Tabs";
 import type { DocData, TreeData, TreeNode } from "@/shared/api/backend";
-import { CHAPTER_KINDS, KIND_LABEL, otherDocs } from "../lib/tree";
+import { CHAPTER_KINDS, KIND_LABEL, otherDocs } from "@/features/wiki/lib/tree";
```

### 그리고 함정 하나 — alias는 도구마다 따로 알려줘야 한다

**무엇이 문제였나:** 테스트 파일의 임포트를 `@/`로 바꾸자 vitest(테스트 러너)만 깨졌다.

```
Test Files 2 failed — Cannot find module '@/features/wiki/lib/tree'
```

**무엇을 고민했나:** `@` alias(별칭 — `@/`를 `./src/`로 풀어주는 규칙)는 `tsconfig.json`의
`paths`에 있다. 그런데 그건 **Next와 타입체커가 읽는 설정**이다. vitest는 자기 리졸버
(vite)를 쓰므로, 같은 alias를 별도로 또 알려줘야 한다.

> 용어 — 리졸버(resolver): `@/foo` 같은 임포트 문자열을 실제 파일 경로로 바꿔 찾아주는
> 부품. 빌드·타입체크·테스트 러너가 각자 다른 리졸버를 가진다.

**그래서 이렇게:** `vitest.config.ts`에 같은 alias를 추가했다. 파일 경로 `vitest.config.ts`:

```ts
import { defineConfig } from "vitest/config";
import { fileURLToPath } from "node:url";

export default defineConfig({
  resolve: {
    alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) },  // 절대경로 임포트 정책
  },
});
```

```
[기존]  @ alias 정의 = tsconfig(paths) 한 곳
        → Next·타입체크는 OK, vitest는 "모듈 못 찾음"
[변경]  @ alias 정의 = tsconfig + vitest.config 두 곳
        → 세 도구 모두 같은 alias 해석
```

**원칙:** alias는 "프로젝트 설정"이 아니라 **도구마다의 설정**이다 — 빌드·타입체크·테스트
러너가 각자 리졸버를 가진다.

---

## 3. 결론

배포 요청 경로가 완성됐다(비밀 없는 요청이 401로 관통하는 것 확인) + 절대경로 임포트
정책이 고정됐다. 중계 패턴은 sync에서 배운 것을 그대로 재사용해 리뷰 지적 없이 통과했다.
PR: #13·#14·#16
