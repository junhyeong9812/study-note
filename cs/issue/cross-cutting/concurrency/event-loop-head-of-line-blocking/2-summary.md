# cs/issue/concurrency/event-loop-head-of-line-blocking — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.

## 전체 흐름

```
[단일 수신 루프 — 처리를 직접 await]
  ws 수신 ──▶ msg1(prepare, 10분+) ── await ──────────────────────▶ 끝
              msg2(logs)   ─ 대기 ─────────────────────────────────▶ 10분 뒤
              msg3(status) ─ 대기 ─────────────────────────────────▶ 10분 뒤
  ▲ 줄 맨 앞(head)의 느린 일이 뒤 전부를 막음 = HOL blocking

[같은 모양 — 느린 구독자]
  msg(log_stream) ── await broadcast(msg) ── 좀비 탭 send 느림 ──▶ 수신 루프 정지
                                                                    → 다른 명령 응답 300s 타임아웃

[2차 증상 — keepalive 오진]
  상대 루프 막힘 → pong 지연 → 클라이언트 ping timeout(1011) → 살아 있는 연결 강제 종료
                   (약 40초마다 반복, 버퍼 가득 → 오래된 메트릭 폐기)

[교정]
  async for raw in ws:
      create_task(handle(raw))          ← 루프는 dispatch만
  broadcast → create_task(...) + send 타임아웃
  (작업 참조 보관 — 잃으면 GC 가능)

[남은 구조] 라인당 broadcast × 클라이언트당 순차 타임아웃 → fan-out 지연 누적 → 윈도우화(후속)
```

## 핵심 문장

- 단일 수신 루프에서 처리·송신을 **직접 await하면** 가장 느린 작업·구독자가 루프 전체를 막아 무관한 메시지까지 지연·타임아웃된다.
- `async`는 동시성을 "허용"할 뿐이다 — 루프 안의 `await`는 그 루프를 직렬로 만든다.
- 수신 루프는 **dispatch만**, 처리·응답·브로드캐스트는 별도 작업으로 떼어 낸다.
- 브로드캐스트는 fire-and-forget + send 타임아웃 — 한 구독자의 지연이 핵심 경로를 멈추지 않게.
- 루프 막힘은 keepalive 오진(살아 있는 연결 종료) 같은 **2차 증상**으로도 나타난다.
