# issue4 — Claude 브리지: 서브넷을 못 넘어서, 방향을 뒤집어 넘다

- 도구: deploy-study-note/tools/claude-bridge (server.py) · backend PR #27·#28·#29

---

## 1. 무엇이 문제였나 — 에스컬레이션은 PC의 claude를 써야 하는데 연결 방향이 막혔다

검색으로 답이 안 나오는 질문은 Claude에게 넘긴다(에스컬레이션). 그 Claude는 PC에 깔린
`claude -p`(구독 CLI)를 쓰기로 했다. 문제는 backend(홈랩)가 PC를 **부를 수 없다**는 것이었다.

> 용어 — 에스컬레이션(escalation): 하위 단계(검색)가 못 풀면 상위 단계(강한 모델)로
> 넘기는 것. 여기선 "검색이 못 찾은 질문을 PC의 Claude에게 물어보기".

**상황**: backend는 `192.168.55.x` 대역, PC는 `192.168.45.29` — 서로 다른 세그먼트다.

```
$ ssh …158  'ping -c1 192.168.45.29'   →  unreachable
   .158의 ip route: default via 192.168.55.1   (45.x로 가는 경로가 아예 없음)
```

홈랩 → PC 직접 경로가 없다. 두 대역이 라우팅으로 이어져 있지 않다.

---

## 2. 무엇을 고민했나 → 그래서 이렇게: 방향을 뒤집는다

홈랩 → PC는 못 가지만 **PC → 홈랩은 이미 뚫려 있다**(배포 ssh가 그 경로를 매일 쓴다).
그러면 연결을 PC 쪽에서 걸어 **역방향으로 노출**하면 된다.

```
backend → socat(.158:15100) → 역 SSH 터널(PC가 -R로 걺) → PC:15101→15100 브리지 → claude -p
```

- **역터널**: PC에서 `ssh -N -R 15101:localhost:15100 jun@.158`
  — "PC의 루프백 15100을 .158의 루프백 15101에 뚫어놓는다". 연결을 PC가 거니까 방향 문제가
  풀린다.
- **socat 컨테이너**: .158에서 `0.0.0.0:15100 → 127.0.0.1:15101` 릴레이
  — backend가 LAN 주소로 닿을 수 있게 하되(루프백은 컨테이너 밖에서 안 보이므로), sudo 없이
  컨테이너로 띄운다.

> 용어 — 역(reverse) SSH 터널 `-R`: 보통 ssh는 "내가 상대 포트로 나간다"인데, `-R`은 반대로
> "상대가 내 포트로 들어오게 구멍을 낸다". 방향이 막힌 쪽을 우회하는 고전적 방법.
> socat: TCP 포트를 다른 포트로 이어주는 얇은 릴레이 도구.

**브리지 본체** (`tools/claude-bridge/server.py` — PC에서 실행):

```python
result = subprocess.run(
    [CLAUDE, "-p", prompt, *CLAUDE_ARGS],
    capture_output=True, text=True, timeout=TIMEOUT_S,
)
```

---

## 3. 구현 중 마주친 문제 — "성공인데 빈 응답"

브리지를 띄우고 backend에서 호출하니 연결은 되는데 응답이 비어 왔다.

**증상 1 — chunked 본문을 브리지가 못 읽음**: backend가 Map 본문으로 POST하면 Spring이
`Transfer-Encoding: chunked`로 보내는데, 브리지(파이썬 `http.server`)는 chunked 요청을 못
읽어 **0바이트로 파싱**한다.

**그래서 이렇게** (backend `ClaudeBridgeClient.kt`, `fix 44c4f52` PR #28) — byte 본문으로
바꿔 Content-Length를 명시:

```diff
+        // byte[] 본문 = Content-Length 명시 — Map 본문은 chunked 전송이 되는데
+        // 브리지(파이썬 http.server)는 chunked 요청을 못 읽는다 (실측: 0바이트 파싱 오류)
+        val payload = objectMapper.writeValueAsBytes(mapOf("prompt" to prompt))
         val response = client.post().uri("/ask")
-            .header("Content-Type", "application/json")
+            .header("Content-Type", "application/json; charset=utf-8")
             .header("X-Request-Id", requestId)
-            .body(mapOf("prompt" to prompt))
+            .body(payload)
```

**증상 2 — socat 이미지 부재**: 첫 시도에서 `Unable to find image 'alpine/socat'` —
`docker pull alpine/socat`을 선행해서 관통.

---

## 4. 리뷰 반영 — 인증 없는 원격 실행은 위험하다 (codex F2~F8)

리뷰가 정확히 짚었다: 이대로면 relay 포트에 닿는 누구나 PC의 Claude를 임의 실행한다.
브리지는 결국 "임의 프롬프트로 남의 PC에서 프로세스를 돌리는" 표면이라, 배포 서버만큼
위험하다. 지적을 받아 강화했다:

```
F2 인증        : X-Bridge-Secret 공유 시크릿 상수시간 검증, 빈 시크릿이면 전부 거절
F3 주입 완화   : claude -p --allowedTools "" — 문서에 "파일 읽어라" 같은 지시가 있어도
                 도구를 못 써서 순수 텍스트 답만 나오게
F4 동시 1건    : 세마포어 — 느린 요청 하나가 전체를 점유하지 못하게, 초과는 503
F6 출력 상한   : 프롬프트 60KB·출력 20KB
F7 본문 범위   : Content-Length 범위 검증 + chunked 요청 거부
F8 stderr 비노출: 실패해도 내부 오류를 밖으로 흘리지 않음
```

**브리지 방어 코드** (`tools/claude-bridge/server.py`):

```python
CLAUDE_ARGS = ["--output-format", "text", "--allowedTools", ""]   # F3: 도구 전면 차단
_inflight = threading.Semaphore(1)                                # F4: 동시 1건

def do_POST(self):
    ...
    provided = self.headers.get("X-Bridge-Secret", "")
    if not SECRET or not hmac.compare_digest(provided, SECRET):   # F2: 인증·상수시간
        return self._json(401, {"error": "unauthorized"})
    if self.headers.get("Transfer-Encoding"):                     # F7: chunked 거부
        return self._json(411, {"error": "length_required"})
    if not (1 <= length <= MAX_PROMPT + 1024):                    # F7: 범위 강제
        return self._json(413, {"error": "bad_length"})
    if not _inflight.acquire(blocking=False):                     # F4: 초과는 503
        return self._json(503, {"error": "busy"})
    ...
    if result.returncode != 0:
        return self._json(502, {"error": "claude_failed"})        # F8: stderr 비노출
    self._json(200, {"answer": result.stdout.strip()[:MAX_OUTPUT]})  # F6: 출력 상한
```

**backend도 시크릿 헤더를 붙이도록** (`ClaudeBridgeClient.kt`, `fix b79040f` PR #29):

```diff
     private val bridgeUrl = System.getenv("CLAUDE_BRIDGE_URL") ?: ""
+    private val bridgeSecret = System.getenv("BRIDGE_SECRET") ?: ""
     ...
         val response = client.post().uri("/ask")
             .header("X-Request-Id", requestId)
+            .header("X-Bridge-Secret", bridgeSecret)
             .body(payload)
```

**검증**: 무인증 401 · 인증 200 · 엣지 에스컬레이션 재관통("SSTable은 …" 답이 실제로 돌아옴).

---

## 5. 결론

서브넷 격리는 "연결 방향을 뒤집어" 풀었고(역터널 + socat), 원격 실행 표면은 인증·동시
제한·크기 상한·도구 차단으로 좁혔다. 브리지는 세션 프로세스라 상시 운용은 PC에서 스크립트로
기동한다(README에 절차 기록). 미설정 시 backend는 `available=false`로 우아하게 부재를
안내한다. backend PR #27·#28·#29.
