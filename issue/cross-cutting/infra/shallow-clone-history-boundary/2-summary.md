# issue/cross-cutting/infra/shallow-clone-history-boundary — 정리 (힌트)

## 전체 흐름

```
원격 이력   c1 ─ c2 ─ … ─ c10 ─ c11 ─ … ─ c20
얕은 clone                  [c16] ─ … ─ c20        depth 5 · c16 = 경계 커밋 (부모 c15 는 로컬에 없음)
                              ▲
                              └─ .git/shallow 에 경계 커밋 목록이 적혀 있다

[실패 1] diff
   git show c16  →  부모가 없는 커밋처럼 다룸  →  파일 전체가 "추가"   ← 이 커밋이 바꾼 줄이 아니다
   교정: 경계 목록에 든 커밋의 diff 는 "부모 없음" 갈래(404)로 답하고 바깥(원격 비교 화면)으로 넘긴다

[실패 2] 조상 판정
   A = c10 (객체는 이전 fetch 로 남아 있음)   B = c20
   merge-base --is-ancestor A B   →  c20 에서 거꾸로 걸어도 c16 에서 끊김  →  "조상 아님"
   응답: 200 not_ancestor · 빈 목록   ← 사실은 A 가 B 의 조상이다

   교정 — 판정 순서
     1. A 가 B 의 조상                         → ancestor
     2. B 의 조상 순회가 경계에 닿지 않음       → not_ancestor   (이력이 온전하니 믿는다)
     3. B 가 A 의 조상 (확실한 되돌림)          → not_ancestor
     4. 그 밖                                   → unknown        (목록 없음 · range_complete=false)
```

## 핵심 문장
- 얕은 clone 의 경계 커밋은 부모 객체가 로컬에 없다 — git 은 "부모 없음"을 "최초 커밋"처럼 다뤄 diff 를 만든다.
- 조상 판정은 로컬 그래프만 걷는다 — 경계에서 끊긴 길은 "길 없음"으로 답한다.
- 그래서 경계에 닿은 "부모 없음 · 조상 아님"은 "모름"이다. 경계에 닿았는지 먼저 보고, 모름을 세 번째 값으로 낸다.
- 거짓 답은 오류가 아니라 200 과 그럴듯한 데이터로 나간다 — 경계 판정이 없으면 아무도 모른다.
- 경계 목록 자체가 다른 프로세스에 의해 바뀔 수 있으면, 판정 전체를 한 시점의 목록 위에서 해야 한다([optimistic-read-validation](../../concurrency/optimistic-read-validation/)).
