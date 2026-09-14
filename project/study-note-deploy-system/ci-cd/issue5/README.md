# issue5 — 봇 차단이 자기 파이프라인을 쐈다: curl UA 자책골

- 관련: deploy-study-note/docs/study-note-deploy-system-ci-cd/TODO.md (2026-09-13)
- PR: study-note sync.yml + backend/front/llm deploy.yml (UA 수정)

---

> ### 이 문서는 무엇인가
> 운영 중 발견한 회귀(regression) 기록. 5부에서 엣지 nginx에 넣은 봇 차단이,
> 우리 자동 배포·색인 파이프라인 자신을 막아버린 사건과 그 수정.

---

## 1. 배경 — 왜 이 일이 생겼나

바로 앞 작업(엣지 502/504 정리)에서 오라클 nginx에 "봇 user-agent 차단"을 넣었다.
스캐너가 흔히 쓰는 UA(`curl/`, `python-requests/`, `wget/` 등)를 연결 단계에서 끊는 규칙이다.

그런데 우리 자동화가 **바로 그 curl로** 엣지를 호출한다:
- study-note `sync.yml`: `curl ... POST /api/sync` (push 시 색인 갱신)
- 각 서비스 `deploy.yml`: `curl ... POST /api/deploy` (push 시 자동 배포)

GitHub Actions의 curl 기본 UA는 `curl/8.x`. 즉 **내가 넣은 차단 규칙이 내 파이프라인을
스캐너로 오인해 끊은 것**이다. "봇 차단"이 아군을 오사했다.

## 2. 증상과 진단

**증상** (sync.yml 실행 로그):
```
curl: (92) HTTP/2 stream 1 was not closed cleanly: PROTOCOL_ERROR
http: 000
```
- `000` = 응답 코드를 못 받음(연결이 끊김).
- PROTOCOL_ERROR = nginx가 HTTP/2 연결 도중 444(응답 없이 종료)로 끊어, 클라이언트가
  "스트림이 깨끗하게 안 닫혔다"고 본 것.

**진단** — UA만 바꿔 대조:
```
curl -A "curl/8.0"        POST /api/sync   → 000 (끊김)      ← 차단 규칙에 걸림
curl -A "study-note/1.0"  GET  /           → 200            ← 통과
curl -A "study-note/1.0"  POST /api/sync   → 401 (인증필요)  ← 엔드포인트는 정상
```
→ 백엔드·sync 엔드포인트는 멀쩡하고, **엣지의 UA 차단만이 원인**임을 확정.
(5부의 "성공 로그가 아니라 산출물을 봐야 한다"의 재판 — Actions가 초록불이 아니라
빨간불이라도, 왜 빨간불인지는 응답 코드·UA 대조로만 좁혀진다.)

## 3. 해결 — 봇 차단은 유지하되, 아군은 자기를 밝힌다

두 선택지가 있었다:
```
(A) 엣지 UA 차단에서 curl 제외        → 스캐너도 curl을 쓰므로 방어가 약해진다. 탈락.
(B) 우리 자동화가 고유 UA로 자기를 밝힘 → 차단은 그대로, 아군만 통과.  선택.
```

**왜 B인가:** 차단의 목적은 "정체불명 스캐너 거르기"다. 우리 자동화는 정체가 분명하니
그 이름을 대면 된다 — 방어를 약화시키지 않고 오사만 없앤다.

**수정** — 4개 워크플로 전부:
```yaml
# [기존]
curl -sS -X POST "https://www.junproject.xyz/api/sync" ...
# [변경]
curl -sS --http1.1 -A "study-note-sync/1.0" -X POST "https://www.junproject.xyz/api/sync" ...
#         ^^^^^^^^   ^^^^^^^^^^^^^^^^^^^^^^^
#         HTTP/1.1   고유 UA (curl/ 로 시작 안 하므로 map 차단에 안 걸림)
```
- `-A "study-note-sync/1.0"` (배포는 `study-note-deploy/1.0`): 엣지 map은 `~*curl/`을
  차단하는데 이 UA는 `curl/`로 시작하지 않아 통과.
- `--http1.1`: 444로 끊길 때의 HTTP/2 PROTOCOL_ERROR를 피하고 실패를 깔끔한 코드로.

## 4. 검증

수정 push 후 4개 워크플로 전부 재실행:
```
study-note sync.yml   → http 202   (이전 000)
backend    deploy.yml → http 202
front      deploy.yml → http 202
llm        deploy.yml → http 202
```
`--http1.1 + 고유 UA`로 전부 엣지를 통과(202=접수). 파이프라인 복구.

## 5. 결론과 남긴 것

- **원칙:** 방어 규칙을 넣을 때 "내 아군도 이 규칙에 걸리나"를 먼저 본다. 봇 차단·
  rate limit 같은 광역 규칙은 자기 자동화를 오사하기 쉽다 — 아군은 식별자(고유 UA·
  허용 IP)로 명시적으로 통과시킨다.
- **당시 대응:** 발견 시점엔 수동 동기화(backend 직접 호출, 엣지 우회)로 사이트를
  최신화하고, 워크플로 수정으로 근본 해결.
- **남긴 것(TODO):** GitHub webhook(`POST /hooks/github`)을 저장소에 등록하면 Actions
  없이도 동기화 가능(HMAC 시크릿 필요) — 후속. 지금은 Actions curl 방식으로 충분.
