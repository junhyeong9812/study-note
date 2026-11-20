# distributed — 원격 결과와 권리의 단조성

프로세스·호스트를 넘는 호출과 권리(lease)에서 나오는 패턴이다.\
공통 원리: **원격 결과는 성공·실패·모름의 3상태이고, 권리는 자원 쪽에서 단조 증가로만 검증한다.**

## 공통 원리

```
  호출자 ──요청──▶ 네트워크 ──▶ 원격 실행
     ▲                             │
     └── 타임아웃 ≠ 실패 ──────────┘  (실행됐을 수도 있다)

  권리 보유자 A (token 5) ──쓰기──▶ 자원: max_seen=6 → 거부
  권리 보유자 B (token 6) ──쓰기──▶ 자원: 허용, max_seen=6
```

## 패턴 카드

- [active-instance-from-routing-truth](active-instance-from-routing-truth/) — 무중단 교체로 두 인스턴스가 겹쳐 뜰 때 주기 작업의 소유권은 "신호를 받았는가"가 아니라 "프록시가 지금 누구에게 보내는가"로 정한다 — 신호는 힌트로만 쓰고, 이어받을 상태는 맡는 순간 공유 저장소에서 읽으며, 대기 인스턴스는 헬스에 역할을 드러낸다.
- [monotonic-fencing](monotonic-fencing/) — 권리(lease·fencing token)의 최고수위는 단조 증가만 해야 하며 검증은 자원(sink) 측에서 단일 시계로 한다 — 유일성 제약은 단조성을 보장하지 않는다.
- [three-state-rpc-outcome](three-state-rpc-outcome/) — 원격 호출의 타임아웃·유실은 "실패"가 아니라 "결과 모름"이다 — 미실행 보증·UNKNOWN·성공의 3상태로 다루고 늦은 성공 신호를 버리지 않는다.

> 이 폴더의 메타 태그: `race-condition`(1) · `single-source-of-truth`(1) — 태그별 전체 목록은 [issue 태그 역인덱스](../../README.md#태그-역인덱스).
