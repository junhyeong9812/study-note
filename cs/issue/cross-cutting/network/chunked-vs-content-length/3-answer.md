# cs/issue/network/chunked-vs-content-length — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-23) — 이슈 README·코드 기준. 복습 전 읽지 말 것.

## 정답
<!-- 질문 1:1 대응 -->

1. **본문 경계 두 방식.** HTTP 메시지는 헤더 다음에 본문이 온다. 수신측은 "어디까지가 본문인가"를 알아야 하는데 방법이 둘이다. **Content-Length: N** — 본문 총 바이트 수 N을 헤더에 명시하고, 수신측은 딱 N바이트를 읽는다(length-prefix). **Transfer-Encoding: chunked** — 총 길이 없이 본문을 조각(chunk)으로 나눠 각 조각 앞에 그 조각 크기를 붙여 흘리고, 크기 0인 조각으로 끝을 알린다(delimiter/framing). 송신측 선택 기준은 **송신을 시작하는 시점에 본문 전체 길이를 아는가**다. 알면 Content-Length가 간단하고, 모르면(생성 중 흘려보내야 하면) chunked를 쓴다.
   > **Content-Length** — 본문 총 바이트 수를 앞에 명시하는 헤더.
   > **chunked transfer-encoding** — 길이 없이 조각 단위로 흘리는 HTTP/1.1 전송 방식.

2. **왜 Map은 chunked, byte[]는 Content-Length인가.** `Map` 본문을 주면 클라이언트가 그것을 JSON으로 직렬화하는데, **직렬화가 끝나기 전에는 최종 바이트 수를 모른다** → 길이를 못 붙이니 chunked로 흘린다. 반면 `byte[]`(또는 `objectMapper.writeValueAsBytes(...)`로 미리 직렬화한 것)는 **이미 길이가 확정된 완성 버퍼**라 클라이언트가 `Content-Length`를 계산해 붙일 수 있다. 즉 차이의 뿌리는 "송신 시점에 길이를 아느냐" 하나다.

3. **서버냐 클라이언트냐 — 판별.** 같은 요청을 `curl`로 보내면 성공하고 RestClient로만 실패한다 → **서버는 두 요청에 동일하게 반응하므로 서버가 변수가 아니다. 갈리는 것은 클라이언트뿐** → 원인은 클라이언트가 만든 요청의 차이다. `curl`은 본문 길이를 알고 Content-Length를 붙이고, RestClient는 `Map`을 chunked로 흘린다. "한쪽 도구로는 되고 다른 도구로는 안 된다"는 서버가 아니라 **두 도구가 만든 바이트의 차이**를 보라는 신호다.

4. **왜 0바이트인가.** 파이썬 `http.server`(`BaseHTTPRequestHandler`)의 핸들러는 본문을 읽을 때 보통 `Content-Length` 헤더 값 N을 정수로 파싱해 `rfile.read(N)` 한다. chunked 요청에는 **Content-Length 헤더가 없다** → N이 0(또는 없음)으로 잡힘 → `read(0)` → 빈 바이트. 조각 크기 표식을 해석해 재조립(dechunk)하는 코드가 없으니 소켓에 실제 조각 데이터가 와 있어도 못 읽는다. 그래서 "짧게 잘림"이 아니라 **완전한 0바이트**이고, 빈 문자열을 JSON 파싱하면 첫 글자에서 값이 없어 `line 1 column 1 (char 0)`에서 실패한다.

5. **책임 경계.** 표준(HTTP/1.1)상 chunked는 필수 지원 대상이라 "구현 안 한 수신측"이 규격 미달이다. 하지만 교정은 **제어 가능하고 값싼 쪽**을 고른다 — 낡은 수신 서버(파이썬 기본 `http.server`)를 dechunk까지 하도록 바꾸는 것보다, 송신측 한 줄(`Map`→`byte[]`)로 Content-Length를 강제하는 게 확실하고 위험이 없다. "누구 잘못인가"와 "어디를 고쳐야 값싼가"는 다른 질문이다.

6. **수신측 자기 방어.** 브리지 서버는 이후 `Transfer-Encoding` 헤더가 있으면 **411 `length_required`로 거절**하고 `Content-Length`가 정해진 범위(`1 ≤ N ≤ 상한`) 안인지 강제하도록 강화됐다. 조용히 0바이트로 읽어 "빈 본문"으로 처리하면 원인이 은폐되고 엉뚱한 곳(JSON 파서)에서 터진다. **못 다루는 입력은 명시적으로 거절**하면 실패가 발생 지점에서 이름을 갖고(`length_required`) 드러난다 — silent failure 방지.
   > **411 Length Required** — 서버가 Content-Length 없는 요청을 거부하는 상태코드.

7. **연결 — length-prefix vs delimiter framing.** 이 대립은 HTTP 고유가 아니라 **바이트 스트림 위에 메시지 경계를 어떻게 긋느냐**의 일반 문제다. TCP는 경계 없는 바이트 흐름이라, 그 위에 메시지를 얹으려면 (a) 길이를 앞에 붙이거나(length-prefixed frame, 대부분의 바이너리 프로토콜·gRPC 메시지 프레이밍) (b) 구분자·종료 표식을 쓴다(개행으로 끊는 NDJSON, 0-크기 조각으로 끝내는 chunked). 길이 프리픽스는 미리 길이를 알아야 하고, 구분자 방식은 스트리밍·미지 길이에 강한 대신 파서가 표식을 해석해야 한다 — 정확히 이 이슈의 두 방식이다.

## 이번 프로젝트 사례
- [backend/issue12](../../../../../project/study-note-deploy-system/backend/issue12/) — RestClient의 `Map` 본문이 chunked로 나가 브리지가 0바이트 파싱(`char 0`) 오류, 본문을 `byte[]`로 바꿔 Content-Length 명시(#28).
- [ci-cd/issue4](../../../../../project/study-note-deploy-system/ci-cd/issue4/) — 같은 chunked 0바이트 증상을 브리지(파이썬 `http.server`) 관점에서 기록 + 방어로 `Transfer-Encoding` 거부(411)·Content-Length 범위 강제(F7).

## 검증 기록
- 2026-09-23: 이슈 README(backend/issue12 §4, ci-cd/issue4 §3·§4) + `tools/claude-bridge/server.py`(411/범위 강제 코드) 대조 작성 (Claude 초안).
