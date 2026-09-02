# issue4 — sync 중계 + Actions: "push하면 색인"의 마지막 고리

- 이슈 #7 · PR: https://github.com/junhyeong9812/study-note-deploy-system-front/pull/8

> ### 이 문서가 어떻게 바뀌었나 (2026-09-02 재작성)
> ```
> [기존 문서]                              [새 문서 — 지금 이것]
> "front는 비밀을 저장 안 함"     ──▶      왜 그래야 하나(로테이션 비용 서사)
> "webhook 탈락"                  ──▶      무엇을 고민해 curl로 갔나
> 첫 실행 로그만                  ──▶      로그 + push→색인 사슬 ASCII
> 멱등·패스스루 용어 던짐          ──▶      낯선 용어는 그 자리에서 한 줄 풀이
> ```

---

## 1. 배경 — 남은 고리는 둘이었다

이때까지 색인(노트를 검색 가능하게 만드는 작업)은 내가 backend에 직접 curl을 쳐서
돌렸다. 하지만 이 시스템의 처음 목표 문장은 **"study-note에 push하면 알아서 배포되고
검색된다"**였다. 그 자동화를 완성하려면 고리 둘이 남아 있었다.

1. 바깥(GitHub Actions)에서 집 안(backend)까지 요청이 **도달할 통로**
2. push가 일어날 때 그 요청을 **쏘는 자동화**

> 용어 — 색인(indexing): 문서를 검색 엔진이 찾을 수 있는 형태로 정리해 넣는 것.
> 용어 — GitHub Actions: GitHub에 코드를 push할 때 자동으로 스크립트를 돌려주는 기능.

---

## 2. 검토한 방식들

### 결정 (1) — Actions → 엣지(www) → front 중계 → backend

**무엇이 문제였나:** 색인 요청은 바깥 인터넷(Actions)에서 시작되는데, backend는 집 안
LAN에만 있어 바깥에서 직접 닿을 수 없다.

**무엇을 고민했나:** 바깥 노출 지점은 front 하나뿐이다. 그러니 요청은 front를 거쳐야
한다. 그런데 sync 요청에는 비밀(공유 시크릿)이 실린다 — front가 이 비밀을 어떻게
다뤄야 하나?

**그래서 이렇게:** front는 **비밀을 저장도 검증도 하지 않고** 그대로 넘기기만 한다.
파일 경로 `src/app/api/sync/route.ts`:

```ts
/** Actions → backend sync 중계. front는 비밀을 저장·검증하지 않는다 —
 * X-Sync-Secret을 그대로 넘기고 판정은 backend(진짜 소유자)가 한다. */
export async function POST(request: NextRequest) {
  const requestId = newRequestId();
  const secret = request.headers.get("x-sync-secret") ?? "";
  const body = await request.text();
  try {
    const response = await fetch(`${BACKEND_URL}/internal/sync`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Sync-Secret": secret },
      body: body || "{}",
      signal: AbortSignal.timeout(10_000),
    });
    ...
```

> 용어 — 패스스루(pass-through): 받은 것을 열어보거나 바꾸지 않고 그대로 통과시키는 것.

**왜 front가 검증하지 않나:** 비밀의 진짜 소유자는 backend다. backend가 판정해야 검증
로직이 한 곳에만 산다. 만약 front도 검증하면 비밀이 두 서버에 살게 되고, 비밀을 교체
(로테이션)할 때마다 두 곳을 다 고쳐야 한다 — 언젠가 한 곳만 고치고 다른 곳을 잊는다.

```
GitHub Actions ──HTTPS──▶ www.junproject.xyz/api/sync ──▶ front ──LAN──▶ backend /internal/sync
                           (X-Sync-Secret 헤더)            패스스루        비밀 검증·멱등 판정
                                                          (저장·검증 X)    (진짜 소유자)
```

### 결정 (2) — GitHub webhook을 쓰지 않고 Actions의 curl로 갔다 (webhook 탈락)

**무엇이 문제였나:** push를 감지하는 방법으로 GitHub webhook(GitHub이 이벤트를 우리
서버로 POST해주는 기능)도 있다.

**무엇을 고민했나:** webhook은 HMAC 서명 검증 코드와 이벤트 파싱이 필요하다. 그런데 우리는
push "이벤트의 내용"이 필요 없다 — "일어났다"는 사실과 커밋 해시만 있으면 된다.

**그래서 이렇게:** Actions에서 curl 한 방으로 쐈다. 훨씬 단순하고, 보낼 값도 `${{ github.sha }}`로
명시적이다. 파일 경로(study-note 리포) `.github/workflows/sync.yml`:

```yaml
on: { push: { branches: [main] } }
jobs:
  notify:
    runs-on: ubuntu-latest
    steps:
      - run: |
          curl -sS -X POST "https://www.junproject.xyz/api/sync" \
            -H "X-Sync-Secret: ${{ secrets.SYNC_SECRET }}" \
            -d "{\"commit_sha\": \"${{ github.sha }}\", \"request_id\": \"gh-${GITHUB_RUN_ID}\"}"
```

> 용어 — 멱등(idempotent): 같은 요청을 여러 번 보내도 결과가 한 번 보낸 것과 같음.
> 여기선 `commit_sha`가 멱등 키 — 같은 커밋이 다시 오면 backend가 "이미 했음"으로 skip한다.

`commit_sha`는 backend의 멱등 키가 되고(재실행·중복 호출이면 skip), `request_id`를 Actions의
run id로 주면 **Actions 실행 로그와 backend 로그가 같은 id로 꿰인다.**

---

## 3. E2E 실증 — 첫 실행 로그 그대로

workflow를 추가하는 커밋을 push하자, 그 push 자체가 첫 트리거가 됐다.

```
[Actions]  {"success":true,"data":{"started":"incremental","request_id":"gh-33132935414"}}
           http:202                                  (7초 만에 완료)

[backend]  last_sha: 429b95cc                        ← push한 커밋과 일치
           result: {'outcome': 'ok', 'files': 1, 'chunks': 9, 'took_ms': 9686}
```

push → Actions → 엣지 → front → backend 색인까지 **약 10초.** 이 사슬을 그림으로:

```
git push (main)
   │
   ▼
GitHub Actions ── curl ──▶ www ──▶ front /api/sync ──패스스루──▶ backend /internal/sync
                                                                      │
                                                                 색인(약 10초)
                                                                      ▼
                                                          위키·검색에 반영
```

이 문서가 지금 위키에 보인다면, 바로 이 사슬을 타고 온 것이다.

---

## 4. 구현 중 마주친 문제

없었다. 다만 이 이슈가 공개한 경로(`/api/sync`)가 **바로 다음 리뷰에서 두 건을 지적받는다**
(issue5) — requestId를 backend로 전파하지 않아 로그가 끊기는 문제, 그리고 본문 크기 상한이
없어 공개 URL이 메모리 압박에 노출되는 문제. **"동작한다"와 "공개해도 된다" 사이의 거리**를
보여준 사례다.

---

## 5. 결론

시스템의 원래 목표 문장 — "공부한 걸 push하면 웹사이트에 배포되고 검색된다" — 이 PR로
색인 쪽 사슬이 완성됐다. front는 비밀을 만지지 않는 순수 중계로 남았다. PR: #8
