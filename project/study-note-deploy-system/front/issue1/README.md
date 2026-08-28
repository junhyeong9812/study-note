# issue1 — 스캐폴드: BFF의 뼈대와 "엣지 재활용" 가정의 실증

- 리포: https://github.com/junhyeong9812/study-note-deploy-system-front
- 이슈 #1 · PR: https://github.com/junhyeong9812/study-note-deploy-system-front/pull/2

## 1. 배경

front는 두 얼굴이다 — 사용자에겐 위키 화면, 시스템에겐 **유일한 외부 노출 지점**(BFF).
브라우저는 backend(.158)의 존재를 모르고, front(.9:11000)만 안다. 그리고 첫 이슈에서
실증해야 할 가정이 있었다: **local-llm 시절의 오라클 www conf(→집:11000)를 한 글자도
안 고치고 재활용할 수 있는가.**

## 2. 검토한 방식들

### 선택 — create-next-app 없이 수제 스캐폴드

create-next-app이 만들어주는 것(예제 페이지·svg·폰트 설정)의 대부분이 바로 지울
파일들이다. 필요한 건 다섯 개뿐이라 손으로 쓴다:

```
package.json      의존성 8개 (next·react·react-markdown·remark-gfm·rehype-highlight·ioredis)
next.config.mjs   output: 'standalone'   ← 도커 이미지에 node_modules 전체 대신 필요분만
tsconfig.json     paths: {"@/*": ["./src/*"]}
src/lib/          backend.ts(봉투 해제) · logger.ts(로그 규약)
src/app/          layout·page
```

### 선택 — 봉투 해제를 한 곳에서 (`lib/backend.ts`)

backend의 모든 응답은 `{success, data|error}` 봉투다. 페이지마다 success를 검사하면
누락이 생기니, 해제를 헬퍼 하나로 강제한다:

```ts
export async function backendGet<T>(path: string, requestId: string): Promise<T> {
  const response = await fetch(`${BACKEND_URL}${path}`, {
    headers: { "X-Request-Id": requestId },      // 규약 v2: 진입 서버(front)가 발행해 전파
    signal: AbortSignal.timeout(10_000),
  });
  const body = await response.json().catch(() => null);
  if (!body || typeof body.success !== "boolean") throw new BackendError("invalid_envelope", ...);
  if (!body.success) throw new BackendError(body.error?.code ?? "unknown", ...);
  return body.data as T;                          // 페이지는 data만 본다
}
```

**requestId 규약이 여기서 한 번 진화했다**: 원래 "backend가 발행"이었는데, 이제 요청의
진입점이 front라서 **진입 서버가 발행 → X-Request-Id로 전파**로 갱신. backend는 받은
id를 검증(acceptOrIssue — 형식이 틀리면 재발행)해서 그대로 쓴다.

## 3. 워크플로우

```
브라우저 ──HTTPS──▶ 오라클 nginx (www.junproject.xyz conf — 무수정) ──▶ .9:11000 front
                                                                          │ SSR: fetch
                                                                          ▼ (LAN)
                                                                    .158:8090 backend
```

## 4. 실증 — 가정이 맞았나

배포 직후 엣지 실호출:

```
$ curl -o /dev/null -w "edge:%{http_code} %{time_total}s" https://www.junproject.xyz/
edge:200 0.157142s
```

**오라클 conf·인증서·포워딩 무수정 재활용 성공.** 홈 SSR도 즉시 검증:

```
공부 노트 위키 · 커밋 4979164f
cs 주제 163개 · practice 주제 47개 · project 주제 14개 ...
```

front 로그가 규약 포맷으로 backend의 Redis 큐에 합류한 것도 확인:

```
req-19df1abbb201:front:/api/tree ok 25ms
```

## 5. 구현 중 마주친 문제

이 이슈에선 없었다 — 대신 배포 순서를 "가정 실증(엣지 200)"이 가장 먼저 나오도록
설계한 것이 요점이다. 가정이 틀렸다면(conf 부적합) 이후 이슈 전부가 재설계였다.

## 6. 결론

BFF 뼈대 + 봉투 해제 단일 창구 + requestId 규약 v2 + **엣지 재활용 실증(200, 157ms)**. PR: #2
