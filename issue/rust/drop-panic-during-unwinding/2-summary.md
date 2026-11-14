# issue/rust/drop-panic-during-unwinding — 정리 (힌트)

## 전체 흐름

```text
[패닉 1번 — 정상 경로]
  테스트 함수 ── panic! ──▶ 되감기 시작
                              │  스택을 거슬러 오르며 살아 있는 값의 Drop 실행
                              ▼
                   catch_unwind (cargo test가 테스트마다 감쌈)
                              └─▶ 이 테스트만 FAILED, 다음 테스트 계속 ✅

[되감는 중 Drop 안에서 패닉 2번]
  테스트 함수 ── panic! (1차) ──▶ 되감기
                              │
                              ├─ guard.drop()
                              │     └─ debug_assert!(count > 0)  ← 장부가 이미 0
                              │           └─ panic! (2차) 💥
                              ▼
                   "panic in a destructor during cleanup … aborting"
                   SIGABRT — Drop도 catch_unwind도 없음
                              └─▶ 남은 테스트 전부 미실행, 결과 요약 줄 없음 ❌

[고친 뒤]
  debug_assert!(count > 0 || std::thread::panicking())
     평소        → 검사 켜짐: 이중 해제 같은 장부 버그를 잡는다
     되감는 중   → 검사 꺼짐: 1차 패닉만 전파 → catch_unwind가 잡음 → 테스트 하나의 FAILED
  count = count.saturating_sub(1)   ← 0에서 멈춤 (debug 오버플로 패닉·release 감김 둘 다 회피)
```

## 핵심 문장

- 되감기는 패닉 **하나**를 위로 운반하며 Drop을 실행한다 — 도중에 두 번째 패닉이 나면 Rust는 abort한다.
- abort는 `catch_unwind`로 잡히지 않는다 — 테스트 러너의 격리가 깨져 실행 전체가 사라진다.
- `Drop` 안에서는 패닉하지 마라 — 불변식 검사는 `std::thread::panicking()`일 때 건너뛴다.
- 카운터 감소는 `saturating_sub` — `-=`는 debug에서 패닉(또 Drop 안 패닉), release에서 최댓값으로 감긴다.
- 변이 테스트가 assert 실패가 아니라 abort로 끝나면, 그 자체가 정리 경로(Drop)의 결함 신호다.
