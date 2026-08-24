# issue2 — 로그 규약: requestId로 꿰고, Redis 큐로 모은다

- 리포: https://github.com/junhyeong9812/study-note-deploy-system-llm
- 이슈 #2 · PR: https://github.com/junhyeong9812/study-note-deploy-system-llm/pull/5

## 1. 배경 (요구사항)

검색 한 번이 front → backend → llm 세 서버를 거친다. 문제가 나면 "그 요청"이
각 서버에서 뭘 했는지 이어 봐야 하는데, 서버마다 로그가 따로 놀면 짜맞추기가
불가능하다. 그래서:

- 요청마다 **requestId**(추적용 이름표)를 붙여 전 서버 로그에 같은 id가 찍히게 한다.
- 각 서버 로그를 **한 곳(중앙 큐)**으로도 흘려보내 나중에 한 화면에서 본다.
- **성공도 기록한다** — 오류만 남기면 "검색이 조용히 나빠지는" 상황(폴백만 계속
  타는 중)을 아무도 모른다.

## 2. 검토한 방식들

### 선택 — 포맷 규약 + Redis Stream(XADD)으로 보내기만

```
각 서버 ──stdout(항상)──▶ 컨테이너 로그
   └────XADD(있으면)────▶ Redis Stream "logs" (backend 호스트 :6379 예약)
```
- 포맷: `requestId:server-name:message` — 사람이 grep 한 줄로 추적 가능.
- requestId는 **모든 요청의 입구인 backend가 발행**, 하위 서버는 받은 걸 그대로 쓴다.
- 지금은 "보내기만" — 소비(조회 화면)는 후속. Redis Stream은 소비자가 없어도
  쌓아둘 수 있고 MAXLEN으로 메모리 상한을 걸 수 있어서 이 단계에 맞다.

### 대안 — 서버별 로그만 (탈락)

- 문제 날 때마다 서버 3대에 ssh 해서 시간대를 눈으로 짜맞춰야 한다. → 탈락.

### 대안 — ELK/Loki 같은 로그 수집 스택 (탈락)

- 검색·대시보드까지 다 주지만 상주 비용이 크다(ES만 GB급 메모리). 사용자 1명
  시스템의 1차 단계엔 과잉. 필요해지면 Redis 큐 소비자만 바꿔 붙이면 된다. → 보류.

## 3. 구현 워크플로우

```
usecase/api ──log(request_id, "rewrite ok 1305ms")──▶ logger.py
                                                        ├─① stdout에 기록 (항상 성공)
                                                        └─② Redis로 XADD 시도
                                                             ├─ LOG_REDIS_URL 비어있음? → 건너뜀
                                                             ├─ 최근 실패해서 쉬는 중? → 건너뜀 (백오프)
                                                             ├─ 전송 (0.3초 안에 안 되면 포기)
                                                             └─ 실패 → 30초간 전송 끔 + 예외 삼킴
```

**절대 규칙: 로그가 요청을 인질로 잡지 않는다.** Redis가 죽어 있어도, 느려도,
아예 없어도 사용자 요청은 평소처럼 처리된다. 그래서 (1) 타임아웃 0.3초,
(2) 실패하면 30초 쉬기(백오프 — 아픈 서버를 계속 두들기지 않기), (3) 어떤 예외도
밖으로 안 내보냄, 세 겹을 깔았다.

## 4. 코드 변경 (diff와 맥락)

```python
# logger.py 핵심
def format_line(request_id, message):
    return f"{request_id}:{SERVER_NAME}:{message}"      # 규약의 전부

except Exception:                                        # 전송 실패는
    self._disabled_until = time.monotonic() + 30         # 30초 쉬고 (고정 백오프)
                                                         # 조용히 넘어간다
```

```diff
 class RewriteIn(BaseModel):
+    request_id: str = Field(min_length=1, max_length=64)   # backend가 발행 — 필수
     query: str = Field(min_length=1, max_length=300)
```

XADD엔 `maxlen=10000(approximate)`을 걸었다 — 소비자가 안 붙어 있는 동안 Redis
메모리가 무한히 크는 걸 막는 상한.

## 5. 구현 중 마주친 문제

### 문제 — 이 요구가 다른 작업(리뷰 수정) 중간에 들어왔다

- **원인**: 진행 중이던 브랜치에 로깅 코드를 바로 섞기 시작했다.
- **수정**: 스코프를 떼어내 별도 이슈(#2)·별도 브랜치로 분리.
- **배경**: 커밋·PR 단위가 곧 리뷰 단위이자 기록 단위 — 섞이면 "이 변경이 왜
  들어왔지"를 나중에 알 수 없다. **새 요구는 이슈부터**가 작업 원칙으로 확정됐다.

## 6. 결론

`requestId:server-name:message` 한 줄 규약 + "stdout 항상, Redis는 있으면" 이중
기록. 실기동에서 성공·거절이 모두 규약 포맷으로 찍히는 것 확인
(`burst-2:llm-wrapper:rewrite ok 1305ms`). Redis 소비자(모아 보는 화면)와
backend의 requestId 발행은 backend 작업에서 이어진다. PR: #5
