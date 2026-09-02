# issue2 — 로그 규약: requestId로 한 요청을 꿰고, Redis 큐로 모은다

- 리포: https://github.com/junhyeong9812/study-note-deploy-system-llm
- 이슈 #2 · PR: https://github.com/junhyeong9812/study-note-deploy-system-llm/pull/5

---

## 1. 무엇이 문제였나 — 세 서버에 흩어진 로그를 짜맞출 수 없다

검색 한 번이 **front → backend → llm** 세 서버를 거친다. 어딘가에서 문제가 나면 "그 요청"이
각 서버에서 무엇을 했는지 이어 봐야 하는데, 서버마다 로그가 따로 놀면 시각을 눈으로
짜맞추는 수밖에 없다. 그것도 세 대에 각각 ssh 해서.

게다가 오류만 기록하면 더 위험한 상황을 놓친다: 검색이 **조용히 나빠지는** 경우 —
예를 들어 llm이 매번 폴백만 타고 있는데 에러는 안 나는 상황 — 을 아무도 모른다.

그래서 세 가지를 규약으로 못박기로 했다.

```
① 요청마다 requestId(추적용 이름표)를 붙여, 전 서버 로그에 같은 id가 찍히게 한다
② 각 서버 로그를 한 곳(중앙 큐)으로도 흘려보내, 나중에 한 화면에서 본다
③ 성공도 기록한다 — 오류만 남기면 "조용한 열화"를 못 잡는다
```

---

## 2. 무엇을 고민했나 — 수집 스택을 통째로 넣을 것인가

### 갈래 A — 서버별 로그만 유지 (탈락)

문제 날 때마다 서버 3대에 ssh 해서 시간대를 눈으로 맞춘다. 지금 겪는 고통 그대로. → 탈락.

### 갈래 B — ELK/Loki 같은 로그 수집 스택 (보류)

검색·대시보드까지 다 주지만 상주 비용이 크다(ES만 GB급 메모리). 사용자 1명 시스템의 1차
단계엔 과잉이다. 필요해지면 나중에 Redis 큐의 **소비자만** 바꿔 붙이면 된다. → 보류.

### 갈래 C — 포맷 규약 + Redis Stream(XADD)으로 "보내기만" (선택)

```
각 서버 ──stdout(항상)──▶ 컨테이너 로그
   └────XADD(있으면)────▶ Redis Stream "logs" (backend 호스트 :6379 예약)
```

- 포맷: `requestId:server-name:message` — 사람이 `grep 요청id` 한 줄로 세 서버를 추적.
- requestId는 **모든 요청의 입구인 backend가 발행**하고, 하위 서버는 받은 걸 그대로 쓴다.
- 지금은 "보내기만" — 모아 보는 화면(소비자)은 후속. Redis Stream은 소비자가 없어도
  쌓아둘 수 있고 `MAXLEN`으로 메모리 상한을 걸 수 있어 이 단계에 딱 맞다.

> 용어 — Redis Stream / XADD: Redis의 "추가 전용 로그" 자료구조. `XADD logs * ...`는
> logs라는 스트림에 항목 하나를 덧붙이는 명령. 소비자가 나중에 붙어도 과거 항목을 읽을 수 있다.

→ C 채택.

---

## 3. 그래서 이렇게 — 로그가 요청을 절대 인질로 잡지 않게

```
usecase/api ──log(request_id, "rewrite ok 1305ms")──▶ logger.py
                                                        ├─① stdout에 기록 (항상 성공)
                                                        └─② Redis로 XADD 시도
                                                             ├─ LOG_REDIS_URL 비어있음? → 건너뜀
                                                             ├─ 최근 실패해 쉬는 중? → 건너뜀 (백오프)
                                                             ├─ 전송 (0.3초 안에 안 되면 포기)
                                                             └─ 실패 → 30초간 전송 끔 + 예외 삼킴
```

**절대 규칙: 로그가 요청을 인질로 잡지 않는다.** Redis가 죽어 있어도, 느려도, 아예 없어도
사용자 요청은 평소처럼 처리돼야 한다. 그래서 세 겹을 깔았다 — (1) 타임아웃 0.3초,
(2) 실패하면 30초 쉬기(백오프 — 아픈 서버를 계속 두들기지 않기), (3) 어떤 예외도 밖으로
내보내지 않기.

> 용어 — 백오프(backoff): 실패한 대상을 곧바로 다시 두들기지 않고 일정 시간 쉬었다
> 재시도하는 것. 여기선 "한 번 실패하면 30초는 Redis 전송을 아예 끈다".

---

## 4. 코드 — 실제 커밋에서 (`feat b2b9dbc`)

**로거 본체** (`wrapper/logger.py` 신규):

```python
def format_line(request_id: str, message: str) -> str:
    return f"{request_id}:{SERVER_NAME}:{message}"      # 규약의 전부 — 이 한 줄

class _RedisSink:
    async def send(self, level: str, line: str) -> None:
        if not LOG_REDIS_URL or time.monotonic() < self._disabled_until:
            return                                       # 미설정·백오프 중이면 조용히 건너뜀
        try:
            if self._client is None:
                import redis.asyncio as redis_async
                self._client = redis_async.from_url(
                    LOG_REDIS_URL, socket_connect_timeout=0.3, socket_timeout=0.3
                )
            await self._client.xadd(LOG_STREAM, {"level": level, "line": line},
                                    maxlen=_STREAM_MAXLEN, approximate=True)
        except Exception:  # noqa — 로그 전송은 어떤 예외도 밖으로 내보내지 않는다
            self._disabled_until = time.monotonic() + _REDIS_BACKOFF_SECONDS   # 30초 쉼
```

`maxlen=10000(approximate)`을 건 이유: 모아 보는 소비자가 아직 안 붙어 있는 동안 Redis
메모리가 무한히 크는 걸 막는 상한이다.

**requestId를 입력 계약의 필수 필드로** (`wrapper/api.py`):

```diff
 class RewriteIn(BaseModel):
     model_config = ConfigDict(extra="forbid")
+    request_id: str = Field(min_length=1, max_length=64)   # backend가 발행 (로그 규약)
     query: str = Field(min_length=1, max_length=300)
```

**성공도 기록** — 라우터의 모든 경로가 log를 부른다 (`wrapper/api.py`):

```diff
         result = await rewrite.run(body.request_id, body.query, ...)
+        await log(body.request_id, f"rewrite ok {elapsed_ms()}ms")   # 성공도 기록 (규약)
         return result
     except rewrite.Busy:
+        await log(body.request_id, "rewrite rejected: busy", "warning")
         return JSONResponse({"error": "busy", "retry_after": 2}, status_code=503, ...)
```

---

## 5. 구현 중 마주친 문제

### 문제 — 이 요구가 다른 작업(직전 리뷰 수정) 도중에 끼어들었다

- **무엇이 문제였나**: 진행 중이던 브랜치에 로깅 코드를 바로 섞어 넣기 시작했다.
- **왜 위험한가**: 커밋·PR 단위가 곧 리뷰 단위이자 기록 단위다. 두 성격의 변경이 한
  커밋에 섞이면 나중에 "이 변경이 왜 들어왔지"를 되짚을 수 없다.
- **그래서 이렇게**: 로깅 스코프를 떼어 **별도 이슈(#2)·별도 브랜치**로 분리했다.
  이 경험으로 "새 요구는 이슈부터 분리한다"가 작업 원칙으로 굳었다.

---

## 6. 결론

`requestId:server-name:message` 한 줄 규약 + "stdout은 항상, Redis는 있으면" 이중 기록.
실기동에서 성공·거절이 모두 규약 포맷으로 찍히는 것을 확인했다
(`burst-2:llm-wrapper:rewrite ok 1305ms`). 모아 보는 화면(Redis 소비자)과 backend의
requestId 발행은 backend 작업에서 이어진다. PR: #5.
