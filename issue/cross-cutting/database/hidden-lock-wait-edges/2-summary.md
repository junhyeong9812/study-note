# issue/cross-cutting/database/hidden-lock-wait-edges — 정리 (힌트)

## 전체 흐름

```text
[변형 A — 외래 키 검사가 만든 숨은 간선]
 확정 X                                         정리 C (닫힌 그룹 g)
  SELECT … FROM child WHERE id = h FOR UPDATE    SELECT … FROM grp WHERE id = g FOR UPDATE   ← 부모 행 배타
  (h 를 쥠)                                       DELETE FROM child WHERE group = g AND 만료   ← h 에서 X 를 기다림
  INSERT INTO result (group_id = g, …)
   └─ FK 검사 = grp 행 g 에 FOR KEY SHARE        ← C 의 FOR UPDATE 와 충돌 → C 를 기다림
                    X ──기다림──▶ C ──기다림──▶ X     = 40P01 (한쪽 롤백)

 고침: C 의 DELETE 대상 = SELECT … FOR UPDATE SKIP LOCKED 로 고른 행만
       → C 는 h 를 건너뛰고 기다리지 않음 → 간선 C→X 가 사라짐
       → 남은 자식 행이 있으면 집계 행 삭제는 다음 실행으로 미룸(대상 = 닫힘 ∧ 집계 행 남음)

[변형 B — SKIP LOCKED + 고정 LIMIT 의 진행 막힘]
 틱: 청크1 = 후보 앞 k개 → 잠긴 것 건너뜀(남음)
     청크2 = 다시 "앞 k개" → 같은 후보 → 같은 건너뜀 …   진행 0
 고침: 진행형 커서 key > :after (앞 청크 후보의 최대 키) → 잠긴 후보가 뒤를 막지 않음
       틱당 청크 상한에 닿으면 커서를 다음 틱에 넘김(끝에 닿으면 버림) → 뒤쪽 후보도 차례가 옴

[잠금 순서가 반대인 두 경로]
 선점: 집계 행(기다림) → 대상 행(NOWAIT)    배치: 대상 행(SKIP LOCKED) → 집계 행(기다림)
 대상 행은 양쪽 모두 기다리지 않음 → 대상 행을 쥔 쪽으로 가는 대기 간선이 없음 → 고리 불가
```

## 핵심 문장

- 교착 고리는 "누가 무엇을 기다리나"의 그래프다 — 외래 키 검사(`FOR KEY SHARE`)·`DELETE`/`UPDATE`의 행 대기처럼 코드에 잠금 문장이 없는 대기도 간선이다.
- 부모 행을 배타 잠금하는 정리 작업은 그 부모를 가리키는 모든 `INSERT`(FK 검사)와 충돌한다.
- 정리·배치는 사용자 요청보다 늦어도 되므로 **기다리지 않는 쪽**이어야 한다 — `SKIP LOCKED`로 대기 간선을 없애고 건너뛴 것은 다음 실행에 맡긴다.
- 건너뛰면 "다 지웠다"가 아니다 — 남은 것을 새 문장으로 다시 확인하고, 불변식이 걸린 뒤 단계(집계 행 삭제)는 미룬다.
- `SKIP LOCKED` + 고정 `LIMIT`은 잠긴 앞쪽 후보가 매 청크를 다시 차지한다 — 진행형 커서로 그 뒤부터 고른다.
- 잠금 순서가 반대여도 한쪽 자원에서 양쪽 모두 기다리지 않으면 그 자원에서 고리가 닫히지 않는다.
- "고리 없음"은 고친 형태의 0건과 고치기 전 형태의 40P01 재현을 함께 두어야 증명이 된다.
