# 로그 규약 (횡단관심사 — 전 서버 공통)

> 정본. 각 리포는 이 규약을 구현만 한다. (llm: `wrapper/logger.py`)

## 포맷

```
{requestId}:{server-name}:{message}
```

- **requestId** — **backend가 발행**해 하위 호출(llm 등)에 전달한다. 하위 서버는 받은 값을 그대로 쓴다(자체 발행 금지). 요청 밖 컨텍스트(healthcheck 등)는 고정 문자열(`health`).
- **server-name** — env `SERVER_NAME` (예: `backend`, `llm-wrapper`, `front`).
- **message** — 자유 텍스트. **성공도 기록한다**(예: `rewrite ok 1234ms`) — 오류만 남기면 폴백·품질 열화가 관측되지 않는다.

## 이중 기록

1. **서버 로그(stdout)** — 항상. 컨테이너 로그로 수집.
2. **중앙 큐** — Redis Stream `XADD logs * level <level> line <formatted>` (MAXLEN ~10000).
   - Redis는 **backend 호스트에 backend와 함께 기동 예정 — 포트 6379 예약**(LAN 전용). 소비자는 후속 작업.
   - 각 서버는 env `LOG_REDIS_URL`(미설정 시 전송 생략)·`LOG_STREAM`(기본 `logs`).
   - **전송 실패는 요청 처리를 방해하지 않는다** — 짧은 타임아웃 + 백오프 + 예외 전량 흡수 (fire-and-forget).

## 기록 지점 (최소)

- 요청 성공(소요 ms) · 거절(busy) · 타임아웃 · 업스트림 오류 · 스키마 위반 · 재시도 발동.
