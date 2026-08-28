# issue4 — sync 중계 + Actions: push가 곧 색인이 되는 마지막 고리

- 이슈 #7 · PR: https://github.com/junhyeong9812/study-note-deploy-system-front/pull/8

## 1. 배경

지금까지 색인은 내가 backend에 직접 curl을 쳐서 돌렸다. 목표는 처음부터
"**study-note에 push하면 알아서**"였고, 남은 고리가 둘: ① 외부(GitHub Actions)에서
집 안(backend)까지 요청이 도달할 통로 ② push 때 그 요청을 쏘는 자동화.

## 2. 검토한 방식들

### 선택 — Actions → 엣지(www) → front 중계 → backend

```
GitHub Actions ──HTTPS──▶ www.junproject.xyz/api/sync ──▶ front ──LAN──▶ backend /internal/sync
                           (X-Sync-Secret 헤더)            패스스루        비밀 검증·멱등 판정
```

front 중계의 원칙 — **비밀을 저장도 검증도 하지 않는다**:

```ts
const secret = request.headers.get("x-sync-secret") ?? "";
await fetch(`${BACKEND_URL}/internal/sync`, {
  headers: { "X-Sync-Secret": secret, "X-Request-Id": requestId }, body });
```

비밀의 소유자(backend)가 판정해야 검증 로직이 한 곳에 남는다. front가 검증하면
비밀이 두 서버에 살게 되고, 로테이션 때 둘 다 고쳐야 한다.

### 대안 — GitHub webhook 직접 수신 (탈락)

webhook은 HMAC 서명 검증 코드·이벤트 파싱이 필요하다. 우리는 push "이벤트 내용"이
필요 없고 "일어났다"만 필요 — Actions에서 curl 한 방이 훨씬 단순하고, 보낼 값
(commit_sha)도 `${{ github.sha }}`로 명시적이다.

### Actions workflow (study-note에 추가)

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

`commit_sha`가 backend 멱등 키(재실행·중복 호출이면 skip), `request_id`를 run id로
주면 **Actions 실행 ↔ backend 로그가 같은 id로 꿰인다.**

## 3. E2E 실증 — 첫 실행 로그 그대로

workflow 커밋을 push하자 그 push 자체가 첫 트리거가 됐다:

```
[Actions]  {"success":true,"data":{"started":"incremental","request_id":"gh-33132935414"}}
           http:202                                  (7초 만에 완료)

[backend]  last_sha: 429b95cc                        ← push한 커밋과 일치
           result: {'outcome': 'ok', 'files': 1, 'chunks': 9, 'took_ms': 9686}
```

push → Actions → 엣지 → front → backend 색인까지 **약 10초**. 이 문서가 지금 위키에
보인다면, 바로 이 사슬을 타고 온 것이다.

## 4. 구현 중 마주친 문제

없음 — 단 이 이슈의 공개 경로(/api/sync)가 直후 리뷰에서 두 건(requestId 미전파·본문
무제한)을 지적받는다(issue5). "동작한다"와 "공개해도 된다" 사이의 거리.

## 5. 결론

시스템의 원래 목표 문장 — "공부한 걸 push하면 웹사이트에 배포되고 검색된다" — 이
이 PR로 완성됐다. PR: #8
