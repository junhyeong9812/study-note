# cs/issue/infra/nginx-broadband-defense-friendly-fire — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.

## 전체 흐름

```
방어를 넓게 치면, 그물이 아군까지 걷는다 (friendly fire / self-DoS).

[규칙]  엣지 nginx 보안 설정
   map $http_user_agent $bad_bot { ~*(python-requests|curl/|wget/|…) 1; }
   사이트 conf:  if ($bad_bot) { return 444; }   # 444 = 응답 없이 연결 종료

[오사]  우리 자동화가 바로 그 curl로 엣지를 호출
   색인 동기화 워크플로 / 각 서비스 배포 워크플로 → curl POST
   GitHub Actions curl 기본 UA = curl/8.x  → ~*curl/ 에 걸림 → 444
   클라 관점:  http: 000 + HTTP/2 PROTOCOL_ERROR (응답 코드 못 받음 = 연결 끊김)

[진단]  UA만 바꿔 대조
   -A "curl/8.0"       POST /api/sync → 000  (차단됨)
   -A "wiki/1.0" POST /api/sync → 401  (엔드포인트는 정상)
   → 원인은 엣지 UA 차단 하나로 확정

[해결]  (A) 차단에서 curl 제외 → 스캐너도 curl 씀, 방어 약화. 탈락.
        (B) 아군이 고유 UA로 자기를 밝힘. 차단 유지, 아군만 통과. 선택.
   curl -sS --http1.1 -A "wiki-sync/1.0" -X POST ...
        --http1.1: 444 끊김의 HTTP/2 PROTOCOL_ERROR 회피 → 깔끔한 코드
        고유 UA:   ~*curl/ 은 "curl/ 포함"만 잡음, 이 UA는 안 걸림 → 통과(202)
```

## 핵심 문장
- 광역 방어(봇 차단·rate limit)의 목적은 "**정체불명** 트래픽 거르기"다 — 우리 자동화는 정체가 분명하니 그 **이름을 대면** 방어를 약화시키지 않고 오사만 없앤다.
- 방어 규칙을 넣을 때 "내 아군도 이 규칙에 걸리나"를 먼저 본다.
- 아군은 식별자(고유 UA·허용 IP)로 **명시적으로 통과**시킨다 — allowlist는 denylist(curl 제외)보다 방어를 안 깎는다.
- `444`는 응답 없이 끊으므로 클라이언트엔 `000`/`PROTOCOL_ERROR`로 보인다(정보 0 = 스캐너에 유리, 아군엔 진단 불편).
- "성공 로그가 아니라 산출물" 의 재판 — 초록/빨간불이 아니라 응답코드·UA 대조로만 원인을 좁힌다.
