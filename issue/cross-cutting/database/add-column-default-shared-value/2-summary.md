# issue/cross-cutting/database/add-column-default-shared-value — 정리 (힌트)

## 전체 흐름

```text
[열 추가]  ALTER TABLE items ADD COLUMN updated_at timestamptz NOT NULL DEFAULT now();
           ├─ 테이블 재작성 없음 — 값 하나(그 트랜잭션의 now() = m)를 카탈로그에 둔다
           │    pg_attribute.atthasmissing = true · attmissingval = {m}
           └─ 기존 행 N개 전부: 읽으면 updated_at = m

[증분 대조 기동]  첫 하한 L = 기동 − 60초   (열 추가 직후 60초 안에 기동하면 L ≤ m)
  문제:  SELECT … WHERE updated_at >= L            → 기존 행 N개 전부가 후보
         (오류 없음 — 틱 하나가 N에 비례하는 정렬·탐지·메모리를 쓴다)

  교정 ① 기존 행 빼기 (L ≤ m인 틱만)
         범위 A  L ≤ updated_at < m     ┐ 둘 다 인덱스 범위 조건
         범위 B  updated_at > m          ┘ (값 = m 묶음은 인덱스에서도 건너뜀)
       ② 후보 상한 — 키셋 페이지
         (updated_at, k1, k2) > (마지막 키) ORDER BY … LIMIT N
         찬 페이지면 하한 고정 + 다음 틱이 이어 읽음

[m이 사라지는 때]  VACUUM FULL · 재작성 ALTER → 값이 행에 물리로 써지고 atthasmissing = false
  기동 때 1회 읽어 기억 → 기동 뒤 재작성돼도 같은 m으로 계속 뺀다
  기동 때 이미 없으면 → 제외 없이 원래 문장 + WARN("m 없음")

[남은 한계]  인덱스 = (updated_at) 단일 열
  같은 값 묶음 안에서는 (k1, k2) 위치를 인덱스가 못 찾는다 → 묶음 전체를 훑고 정렬
  → 같은 값 묶음이 크면 LIMIT N이 틱 비용을 묶지 못한다
```

## 핵심 문장

- 비휘발 DEFAULT로 열을 더하면 기존 행은 **모두 같은 값**(열을 더한 트랜잭션의 `now()`)을 갖는다 — "그 열로 바뀐 행 찾기"에는 모든 기존 행이 "방금 바뀐 행"으로 보인다.
- 증분의 첫 창이 열 추가 시각을 덮으면, 그 틱은 오류 없이 **기존 데이터 전부**를 읽는다 — 결함은 비용으로만 나타난다.
- 빼는 기준은 "시각 하한"이 아니라 **"값이 m인 행"**이다 — 열 추가 락을 기다린 트랜잭션의 변경(표시 < m)을 잃지 않는다.
- 제외는 `<> m` 걸러내기가 아니라 **m 앞뒤 두 인덱스 범위**로 — 걸러내기는 m 묶음을 다 훑는다.
- 카탈로그 값은 테이블 재작성으로 사라진다 — 기동 때 읽어 기억하고, 없으면 조용히 넘어가지 않고 WARN으로 남긴다.
- 키셋 페이지 상한은 인덱스가 키셋 전체 열을 덮을 때만 비용을 묶는다 — 단일 열 인덱스의 같은 값 묶음은 예외다.
