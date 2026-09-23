# cs/issue/infra/nginx-broadband-defense-friendly-fire — 광역 방어의 오사(self-DoS) — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> ⚠️ **이 질문 목록은 Claude 초안이다(2026-09-23).** 읽고 본인 질문으로 교체한 뒤 이 줄을 지운다.

## 질문
1. (왜) nginx에 `map $http_user_agent $bad_bot { ~*(…|curl/|…) 1; }` + `if ($bad_bot) { return 444; }`를 넣었더니 GitHub Actions의 배포/색인 curl이 끊겼다. Actions의 curl 기본 UA는 무엇이고, 왜 이 규칙에 걸렸는가(self-DoS).
2. (예측) 끊긴 쪽 로그에 `http: 000`과 `HTTP/2 stream ... PROTOCOL_ERROR`가 찍혔다. 444(응답 없이 연결 종료)가 왜 403/429 같은 코드가 아니라 이렇게 보이는가.
3. (경계) 해결 후보 (A) 차단 규칙에서 `curl` 제외 vs (B) 아군이 고유 UA로 자기를 밝힘. 왜 B인가 — A가 방어를 약화시키는 이유는(스캐너도 curl을 쓴다).
4. (왜) 수정 `-A "study-note-sync/1.0"`이 통과하는 이유는 — `~*curl/` 정규식이 무엇만 잡길래 이 UA는 안 걸리는가. 함께 붙인 `--http1.1`은 무엇을 고쳤는가.
5. (일반화) rate limit·봇 UA 차단 같은 **광역(broadband) 규칙**이 자기 자동화를 오사하기 쉬운 구조적 이유는? 규칙 설계 단계에서 "아군 식별"을 어떻게 넣는가.
6. (경계) UA 기반 아군 식별의 약점은 — 스캐너가 `study-note-sync/1.0`을 흉내 낼 수 있는데도 왜 실용적인가. 더 강한 식별(HMAC webhook 등)이 남는 이유는.

## 복습 기록
| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
