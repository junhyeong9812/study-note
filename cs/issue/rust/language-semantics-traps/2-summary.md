# cs/issue/rust/language-semantics-traps — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.

## 전체 흐름

```
[임시값 수명]
   for id in self.registry().ids() {    ← registry() 가드(임시값)가 여기서 생성
       self.kill(id);                   ← kill() 이 같은 락 재잠금 → 자기 교착 💥
   }                                    ← 가드는 루프 전체가 끝나야 drop
   교정: let ids = self.registry().ids();   (문장 끝에서 가드 drop)
         for id in ids { self.kill(id); }

[결정론]   RandomState → 실행마다 랜덤 시드 / DefaultHasher::new() → 알고리즘 비명세(릴리스 간 변동) → 영속 키가 바뀜 💥
           교정: FNV-1a 같은 결정론 해시 + basename

[산술]     a + b 오버플로 → debug: panic / release: 조용히 wrap 💥
           교정: saturating_add / checked_add (정책을 코드로)

[평가 시점] x.or(expensive())      → expensive() 가 항상 먼저 실행 (부작용: 키체인 프롬프트) 💥
           교정: x.or_else(|| expensive())

[소유권 API] take_writer() → 한 번만 성공, 두 번째는 거부 💥
           교정: 최초 1회 취득 → 공유 핸들(또는 전용 writer 스레드 + 큐)로 배분
```

## 핵심 문장

- `for`/`match`의 head(scrutinee)에서 만든 임시값은 **블록 전체가 끝날 때** drop된다 — 락 가드라면 본문 내내 락을 쥔다.
- 표준 `HashMap` 해셔(`RandomState`)는 해시 DoS 방어용 **랜덤 시드**이고, `DefaultHasher` 알고리즘도 릴리스 간 보장이 없다 — 영속 식별자에는 명세된 결정론 해시를 쓴다.
- 정수 오버플로는 기본 설정에서 **debug에서 panic, release에서 wrap**이다(`overflow-checks`로 바뀜) — 외부 입력 누적은 saturating/checked로 정책을 명시한다.
- `or`/`unwrap_or`의 인자는 **즉시 평가**된다 — 비용·부작용이 있으면 `or_else`/`unwrap_or_else`.
- `take` 류 API는 **소유권을 한 번만** 넘긴다 — 여러 소비자에게는 최초 취득 후 공유로 배분한다.
