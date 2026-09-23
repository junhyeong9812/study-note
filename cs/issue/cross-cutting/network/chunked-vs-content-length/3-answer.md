# cs/issue/network/chunked-vs-content-length — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-23) — 이슈 README·코드 기준. 복습 전 읽지 말 것.

태그: `silent-failure`

## 정답
<!-- 질문 1:1 대응 -->

1. **본문 경계 두 방식.** HTTP 메시지는 헤더 다음에 본문이 온다. 수신측은 "어디까지가 본문인가"를 알아야 하는데 방법이 둘이다. **Content-Length: N** — 본문 총 바이트 수 N을 헤더에 명시하고, 수신측은 딱 N바이트를 읽는다(length-prefix). **Transfer-Encoding: chunked** — 총 길이 없이 본문을 조각(chunk)으로 나눠 각 조각 앞에 그 조각 크기를 붙여 흘리고, 크기 0인 조각으로 끝을 알린다(delimiter/framing). 송신측 선택 기준은 **송신을 시작하는 시점에 본문 전체 길이를 아는가**다. 알면 Content-Length가 간단하고, 모르면(생성 중 흘려보내야 하면) chunked를 쓴다.
   > **Content-Length** — 본문 총 바이트 수를 앞에 명시하는 헤더.
   > **chunked transfer-encoding** — 길이 없이 조각 단위로 흘리는 HTTP/1.1 전송 방식.

2. **왜 Map은 chunked, byte[]는 Content-Length인가.** `Map` 본문을 주면 클라이언트가 그것을 JSON으로 직렬화하는데, **직렬화가 끝나기 전에는 최종 바이트 수를 모른다** → 길이를 못 붙이니 chunked로 흘린다. 반면 `byte[]`(또는 `objectMapper.writeValueAsBytes(...)`로 미리 직렬화한 것)는 **이미 길이가 확정된 완성 버퍼**라 클라이언트가 `Content-Length`를 계산해 붙일 수 있다. 즉 차이의 뿌리는 "송신 시점에 길이를 아느냐"다. (단 이는 요청 팩토리가 본문을 스트리밍할 때의 동작이다 — 본문을 먼저 메모리에 버퍼링하는 팩토리·설정을 쓰면 `Map`도 직렬화를 마친 뒤 Content-Length를 붙일 수 있어, 같은 코드라도 클라이언트 구현·버전·설정에 따라 전송 방식이 달라진다.)

3. **서버냐 클라이언트냐 — 판별.** 같은 요청을 `curl`로 보내면 성공하고 RestClient로만 실패한다 → **서버는 두 요청에 동일하게 반응하므로 서버가 변수가 아니다. 갈리는 것은 클라이언트뿐** → 원인은 클라이언트가 만든 요청의 차이다. `curl`은 본문 길이를 알고 Content-Length를 붙이고, RestClient는 `Map`을 chunked로 흘린다. "한쪽 도구로는 되고 다른 도구로는 안 된다"는 서버가 아니라 **두 도구가 만든 바이트의 차이**를 보라는 신호다.

4. **왜 0바이트인가.** 파이썬 `http.server`(`BaseHTTPRequestHandler`)의 핸들러는 본문을 읽을 때 보통 `Content-Length` 헤더 값 N을 정수로 파싱해 `rfile.read(N)` 한다. chunked 요청에는 **Content-Length 헤더가 없다** → N이 0(또는 없음)으로 잡힘 → `read(0)` → 빈 바이트. 조각 크기 표식을 해석해 재조립(dechunk)하는 코드가 없으니 소켓에 실제 조각 데이터가 와 있어도 못 읽는다. 그래서 "짧게 잘림"이 아니라 **완전한 0바이트**이고, 빈 문자열을 JSON 파싱하면 첫 글자에서 값이 없어 `line 1 column 1 (char 0)`에서 실패한다.

5. **책임 경계.** 표준(HTTP/1.1)상 chunked는 필수 지원 대상이라 "구현 안 한 수신측"이 규격 미달이다. 하지만 교정은 **제어 가능하고 값싼 쪽**을 고른다 — 낡은 수신 서버(파이썬 기본 `http.server`)를 dechunk까지 하도록 바꾸는 것보다, 송신측 한 줄(`Map`→`byte[]`)로 Content-Length를 강제하는 게 확실하고 위험이 작다(대가는 본문 전체를 메모리에 먼저 올리는 것 — 작은 JSON이면 무시할 만하다). "누구 잘못인가"와 "어디를 고쳐야 값싼가"는 다른 질문이다.

6. **수신측 자기 방어.** 브리지 서버는 이후 `Transfer-Encoding` 헤더가 있으면 **411 `length_required`로 거절**하고 `Content-Length`가 정해진 범위(`1 ≤ N ≤ 상한`) 안인지 강제하도록 강화됐다. 조용히 0바이트로 읽어 "빈 본문"으로 처리하면 원인이 은폐되고 엉뚱한 곳(JSON 파서)에서 터진다. **못 다루는 입력은 명시적으로 거절**하면 실패가 발생 지점에서 이름을 갖고(`length_required`) 드러난다 — silent failure 방지.
   > **411 Length Required** — 서버가 Content-Length 없는 요청을 거부하는 상태코드.

7. **연결 — length-prefix vs delimiter framing.** 이 대립은 HTTP 고유가 아니라 **바이트 스트림 위에 메시지 경계를 어떻게 긋느냐**의 일반 문제다. TCP는 경계 없는 바이트 흐름이라, 그 위에 메시지를 얹으려면 (a) 길이를 앞에 붙이거나(length-prefixed frame, 대부분의 바이너리 프로토콜·gRPC 메시지 프레이밍) (b) 구분자·종료 표식을 쓴다(개행으로 끊는 NDJSON, 0-크기 조각으로 끝내는 chunked). 길이 프리픽스는 미리 길이를 알아야 하고, 구분자 방식은 스트리밍·미지 길이에 강한 대신 파서가 표식을 해석해야 한다 — 정확히 이 이슈의 두 방식이다.

## 문제 구조 (추상화 코드)

### 변형 A — 송신 측이 길이를 모르는 본문을 넘겨 chunked로 전송
① 문제 코드
```kotlin
val response = client.post().uri("/ask")
    .header("Content-Type", "application/json")
    .body(mapOf("prompt" to prompt))            // Map → 직렬화 길이 미정 → Transfer-Encoding: chunked
    .retrieve()
```
② 고친 코드
```kotlin
// byte[] 본문 = Content-Length 명시 — 수신 측(저수준 서버)은 chunked를 못 읽는다
val payload = objectMapper.writeValueAsBytes(mapOf("prompt" to prompt))
val response = client.post().uri("/ask")
    .header("Content-Type", "application/json; charset=utf-8")
    .body(payload)
    .retrieve()
```
무엇이 깨졌나: 송신 측 프레이밍(chunked)을 수신 측이 해석하지 못하는데, 송신 방식이 본문 타입에 따라 암묵적으로 정해졌다.

### 변형 B — 수신 측이 chunked를 조용히 0바이트로 삼킴
① 문제 코드
```python
def do_POST(self):
    length = int(self.headers.get("Content-Length", 0))   # chunked엔 헤더 없음 → 0
    body = self.rfile.read(length)                          # 0바이트
    data = json.loads(body)                                 # "line 1 column 1 (char 0)"
```
② 고친 코드
```python
def do_POST(self):
    if self.headers.get("Transfer-Encoding"):               # 못 다루는 프레이밍은 명시 거절
        return self._json(411, {"error": "length_required"})   # 본문을 안 읽고 거절 → 이 연결은 닫아야 한다(keep-alive 재사용 금지)
    try:
        length = int(self.headers.get("Content-Length", ""))
    except ValueError:                                       # 헤더 없음·숫자 아님
        return self._json(411, {"error": "length_required"})
    if length < 1:                                           # 범위 강제 — 빈 본문은 잘못된 요청
        return self._json(400, {"error": "empty_body"})
    if length > MAX_BODY:                                    # 413은 '너무 큼'에만
        return self._json(413, {"error": "too_large"})
    data = json.loads(self.rfile.read(length))
```
무엇이 깨졌나: 해석할 수 없는 입력을 "빈 본문"으로 처리해, 실패가 엉뚱한 곳(JSON 파서)에서 드러났다.

## 검증 기록
- 2026-09-24: 사건 기록 대조·추상화(Claude 초안)

## 방안 비교

기존 방안은 **송신 측을 Content-Length로 고정**(변형 A)하고 **수신 측은 chunked를 거절**(변형 B)하는 것이다. 같은 원리(송수신의 길이 채널 불일치)에 대해 반대 방향의 방안이 쓰인 사례가 있다.

### 방안 2 — 수신 측이 chunked를 직접 디코드 (저수준 서버)
```python
def _read_body(self) -> bytes:
    if self.headers.get("Transfer-Encoding", "").lower() == "chunked":
        data = b""
        while True:
            size = int(self.rfile.readline().strip() or b"0", 16)   # 크기(16진)\r\n — 확장(";ext")은 미지원, EOF(빈 줄)도 끝으로 오인
            if size == 0:
                self.rfile.readline()                                # 마지막 \r\n — trailer 필드가 오면 미지원
                break
            data += self.rfile.read(size)
            self.rfile.readline()                                    # 조각 뒤 \r\n
        return data
    return self.rfile.read(int(self.headers.get("Content-Length", 0)))   # Content-Length 폴백
```
증상은 같았다(같은 클라이언트가 보낸 POST 본문이 비거나 잘려 `json.loads` 실패) — 이번엔 송신 측을 고치지 않고 수신 측이 표준 프레이밍을 받아들였다.

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 송신 측 Content-Length 고정 + 수신 측 거절 | 송신 측을 통제할 수 있다 | 송신 코드 1줄 + 거절 분기 | 다른 송신자가 chunked로 보내면 411(시끄럽게 실패) | 송신자가 소수·내부이고 수신 서버는 최소 구현으로 두고 싶을 때 |
| 수신 측 chunked 디코드 | 송신자를 모두 통제할 수 없다 | 디코더 직접 구현·유지 | 수제 파서의 경계 오류(trailer·확장 무시 등), 본문 상한 없으면 자원 고갈 | 여러 클라이언트가 붙는 브리지·다양한 HTTP 라이브러리 수용 |

**결론**: 둘 다 "길이 채널을 한쪽이 맞춘다"이다 — 어느 쪽을 맞출지는 **누구를 통제할 수 있는가**로 정한다.\
송신 측을 통제하면 송신 측을 고정하고 수신 측은 못 다루는 입력을 **명시 거절**하는 편이 표면이 작다.\
송신자가 다양하면 수신 측이 표준 프레이밍을 디코드하되, 수제 디코더는 **본문 상한**을 함께 둬야 한다(원문의 디코더에는 상한이 기록돼 있지 않다 — 적용 시 확인할 점).
