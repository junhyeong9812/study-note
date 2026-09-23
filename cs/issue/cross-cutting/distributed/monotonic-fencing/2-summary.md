# cs/issue/distributed/monotonic-fencing — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.

## 전체 흐름

```
권리(lease · fencing token · version)의 최고수위 = high-water mark
   규칙: 오직 증가만. 검증은 자원(sink) 쪽에서. 판정 시계는 하나.

[실패 지점 1] 결정권이 호출자에게 있음
   caller ─ INSERT(version = v1) ─▶ store (이미 v2 있음)
   UNIQUE(target,version) = "중복"만 막음 → v1 삽입 성공
   "현재 = MAX(version)" → 여전히 v2 → 성공한 토글이 무시됨
   교정: store가 MAX+1을 한 문장으로 계산 (동시 충돌은 UNIQUE가 한쪽 거부 → 재시도)

[실패 지점 2] 롤백이 수위까지 되돌림
   전환 실패 → restore(snapshot{slot, token}) → lastAcceptedToken 후퇴
   stale 실행자(token 낮음) ─▶ sink : 수락됨 (거절했어야 함)
   교정: 롤백은 slot만, token = max(before, current) 유지
         sink가 검증: 같은 token=멱등, 작은 token=거절(409)

[실패 지점 3] 확인 절차의 구멍
   서명된 HELD 응답이 결정론적 → 락 잃기 전 응답 재사용(replay)
   첫 확인 실패 → cleanup이 재확인 → 성공 → 권리 없이 부작용
   만료 비교를 앱 시계로 → 시계 편차로 만료 lease를 유효 판정
   교정: 요청마다 난수 confirmId 결박 / 실패는 세션에 영구 고정(sticky)
         만료 판정은 DB 시각으로 한 문장(EXISTS ... >= NOW())
```

## 핵심 문장
- 유일성 제약은 **중복**을 막지 **순서(단조성)**를 보장하지 않는다 — 번호 결정권은 호출자가 아니라 저장소에 둔다.
- 상태 복원(rollback)은 권리의 최고수위까지 되돌리면 안 된다 — fencing token은 `max`로만 움직인다.
- 권리 검증은 **자원(sink) 측**에서(비교와 쓰기를 원자적으로) 해야 창이 닫힌다. 명령 측 재확인은 "확인 후 실행" 사이 창이 남는다.
- 결정론적 서명 응답은 nonce가 없으면 재생 가능하고, 실패 상태가 끈적하지 않으면 정리 경로가 권리 없이 부작용을 낸다.
- 만료 판정은 **단일 권위 시계**에서 한 문장으로 — 여러 시계를 섞으면 편차가 곧 권리 오판이다.
