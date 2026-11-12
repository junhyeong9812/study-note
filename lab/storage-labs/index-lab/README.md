# index-lab — 직접 만든 인덱스로 "왜 B-tree가 기본인가"를 실측

페이지 기반 스토리지 엔진 위에서 인덱스 구조(B+tree, Hash 등)를 교체하며
**쿼리 패턴 × 데이터 규모 × 버퍼풀 크기**에 따른 성능 차이를 실측하는 실험 프로젝트.

- 원본 repo: [junhyeong9812/index-lab](https://github.com/junhyeong9812/index-lab) · 로컬 `/home/jun/project/lab/storage-labs/index-lab/`
- 스택: Rust (edition 2024) · 테스트 `proptest` · 상태: 로드맵 1/5 완료

> 아래 "목적"·"실험 설계"·"로드맵"은 원본 README에서 옮긴 것(질문 번호만 기록용으로 붙임). 고치지 않는다.

## 목적 (Questions)

1. RDBMS는 왜 B-tree를 기본 인덱스로 쓰는가?
2. 해시는 동등 조회에서 더 빠른데 왜 기본이 아닌가?
3. 데이터 유형과 워크로드에 따라 어떤 인덱스를 골라야 하는가?

이 질문에 "설명"이 아니라 **직접 구현한 엔진의 측정값**으로 답하는 것이 목표. 측정 핵심 지표는 실행 시간이 아니라 **디스크 페이지 읽기/쓰기 횟수**.

## 실험 설계

| 축 | 값 |
|---|---|
| 쿼리 패턴 | 동등 조회 / 범위 조회 / 순차 삽입 / 랜덤 삽입 |
| 데이터 규모 | 10^5 / 10^6 / 10^7 건 |
| 버퍼풀 크기 | 데이터 전체 적재 / 50% / 10% |
| 키 분포 | 단조 증가 / 균등 랜덤 / 편중(Zipf) |

추가 실험: B+tree fan-out(4 → 64 → 512)별 깊이·I/O · Hash 디렉토리 더블링 시점의 쓰기 스파이크 · 풀스캔 후 버퍼풀 오염.

## 로드맵

1. 메모리 내 B+tree, Hash 구현 및 속성 테스트
2. Pager + 버퍼풀 구현, 인덱스를 페이지 위로 이동
3. 벤치마크 하네스, 기본 격자 실험
4. fan-out / 디렉토리 더블링 / 캐시 오염 추가 실험
5. 결과 분석 및 "워크로드별 인덱스 선택 가이드" 정리

---

## 작업 기록

### 2026-11-12 — 로드맵 1단계: 메모리 내 B+tree · Extendible Hash + 속성 테스트 (2026-11-04 ~ 11-12)
- 대응 질문: Q1 · Q2 의 토대 (측정은 3단계부터 — 이번 단계는 정확성만)
- 코드: index-lab @ `9d9f99e` (마지막 코드 커밋 — Hash 테스트) · `b762795` (변이 점검·학습 문서) — 브랜치 `feat/stage1-hash-index`
- 원본 기록: repo `docs/plans/2026-11-04/stage1-inmemory-index/`(명세·로그) · `docs/learning/stage1/`(btree.md · btree-qa.md · hash.md)
- 진행 방식: lazy 모드 — diff 하나(01~10)마다 주관식 이해 게이트를 통과해야 다음으로. 판정은 코드를 읽은 독립 워커가 하고, 틀린 답은 오답 노트로 남김.

#### 한 것

- `Index` trait(`insert` · `get` · `range` · `range_rev`) 뒤에 `BTree`·`Hash` 두 구현. 키·값 `u64`, 같은 키 재삽입은 upsert(이전 값 반환).
- 3단계 러너가 `Box<dyn Index>`로 바꿔 끼울 수 있게 trait을 dyn 호환으로 유지(제네릭 메서드를 넣으면 E0038로 컴파일 실패하는 것을 변이로 확인).
- 구조 관찰 API 공개: B+tree `depth()`·`check()`, Hash `global_depth()`·`bucket_count()`·`check()` — 테스트와 3단계 실험이 같이 씀.

#### 설계 결정 (명세 T1~T14 — 후보를 놓고 직접 선택)

| # | 결정 | 선택 | 이유 |
|---|---|---|---|
| T1 | `range` 반환 | `Vec<(u64, u64)>` | 단순, 2단계 버퍼풀 빌림 수명과 충돌 없음 (iterator는 NEXT 후보) |
| T2 | 값 타입 | `u64` | 이번 단계 단순화 |
| T3 | 재삽입 | upsert | `BTreeMap`과 같은 의미 → 정답지 대조가 그대로 됨 |
| T4 | 삭제 | 없음 | trait에 없음. 병합·재분배·버킷 합치기까지 커지는 것을 피함 |
| T5 | 노드 표현 | arena `Vec<Node>` + `NodeId` | 디스크 B+tree도 페이지 번호로 연결(InnoDB·PostgreSQL) → `NodeId`가 2단계 `PageId`가 됨 |
| T6·T9 | fan-out·버킷 용량 | 생성자 인자 | 테스트는 작은 값으로 분할·두 배를 강제, 실험은 큰 값 |
| T7 | 리프 연결 | **양방향** `next`/`prev` | InnoDB `FIL_PAGE_PREV/NEXT`·PostgreSQL `btpo_prev/next`처럼 역방향 스캔. 대가 = 분할 시 오른쪽 형제 쓰기 +1 (2단계에서 측정) |
| T8 | 해시 함수 | splitmix64 finalizer(`mix`) | 키 그대로면 구조적 키(8의 배수 등)에서 디렉터리 폭주. 전단사라 다른 키는 반드시 갈라짐 |
| T10 | Hash `range` | 전체 스캔 → 필터 → 정렬 | 미지원으로 두면 실험 격자 칸이 빔. "해시는 범위에 약하다"를 3단계에서 그대로 측정 |
| T11 | 속성 테스트 | 평범한 proptest + `Vec<Op>` | 의존성 1개, 읽기 쉬움 |
| T13 | `range_rev` | trait에 추가 | Hash와 비교할 역순 범위 축 |
| T14 | 범위 경계 | 양끝 포함 `[lo, hi]` | SQL BETWEEN, `u64::MAX` 표현 가능, `lo > hi`면 빈 결과 |

#### 도식 — B+tree 분할과 구분자 규칙

```
리프 분할 (copy-up)                       내부 노드 분할 (push-up)
[10 20 30 40] 넘침                        N keys [30|50|70|90] 넘침, mid=2
  → A [10 20] ⇄ A' [30 40]                 → N [30|50]  N' [90]
  → 부모에 30 "복사" (리프에도 남음)          → 70을 부모로 "이동" (아래에 안 남음)
  → 링크: A.next=A' · A'.prev=A             (남기면 키 n·자식 n+1이 깨짐)
          A'.next=C · C.prev=A'
두 분할 모두 같은 Split = (구분자, 새 노드 번호)를 반환 → 부모·루트 코드 재사용.
루트가 넘치면 새 루트 Internal{[sep], [옛 루트, 새 노드]} — 깊이가 느는 유일한 곳.

구분자 규칙: 왼쪽 < 구분자 ≤ 오른쪽  (find_leaf: partition_point(|sep| sep <= key))
        P_lo    30     70    P_hi
          [  c0  ][  c1  ][  c2  ]     c0 [P_lo,30) · c1 [30,70) · c2 [70,P_hi)
```

#### 도식 — Extendible Hash의 두 분할

```
key ─mix→ 해시 ─하위 global_depth 비트→ 디렉터리 칸 → 버킷(local_depth)
지역 d < 전역 : 디렉터리 그대로. 그 버킷을 가리키던 2^(전역−d)칸 중
               d번 비트(1<<d)가 1인 절반만 새 버킷으로 재지정
지역 d = 전역 : 디렉터리를 먼저 두 배(뒤 절반 = 앞 절반 복사, 전역+1) → 위와 같이 분할
               복사가 맞는 이유: 모든 지역 ≤ 이전 전역 → 새 최상위 비트를 보는 버킷이 없음
               두 배 순간 옮겨지는 키 = 0개 (키는 넘친 버킷을 나눌 때만 이동)
나눠도 새 비트가 모든 키에서 같으면 또 넘침 → loop가 directory[slot(key)]로 재조회해 반복
```

| | B+tree | Hash |
|---|---|---|
| range 시작 | `find_leaf(lo)`로 바로 | 출발점 없음 — 전체 버킷 |
| 다음 키 | 리프 `next` | 연결 없음(이웃 버킷 링크 없음) |
| 순서 | 리프가 이미 정렬 | 모은 뒤 원래 키로 정렬 |
| range_rev | `prev` 따라 필요한 만큼 | `range` 결과 뒤집기 |
| 비용 | 높이 + 결과 크기 | 항상 n + 정렬 |

#### 확인

- `cargo test` **38/38** (B+tree 15 = 단위 13 + proptest 2 · Hash 23 = 단위 11 + `check()` 손상 검증 10 + proptest 2) · `clippy -D warnings` · `fmt --check` 통과. 런타임 의존성 0.
- **정답지 대조**: proptest가 무작위 삽입열을 `BTreeMap`과 나란히 적용 — insert 반환값 · get · range · range_rev를 비교하고 `&dyn Index` 경유로 한 번 더.
- **삽입마다 구조 검사**: `structure_holds_after_every_insert`가 매 삽입 뒤 `check()`(B+tree I2: 리프 깊이·구분자 범위·하한·next/prev 대칭 / Hash I3: 칸 수 2^(전역−지역)·`mix(k)` 접미사 일치·고아 버킷). 끝에서 한 번만 보면 중간에 깨졌다 덮인 상태와 "몇 번째 삽입에서" 깨졌는지를 놓친다.
- **블라인드 테스트 설계**: 테스트는 구현 본문을 보지 않은 워커가 명세(불변식)에서 출발해 설계. `check()` 자체도 일부러 망가뜨린 구조로 검증(`should_panic(expected=…)`로 어느 검사가 터져야 하는지까지 지정).
- **변이 점검** (스크래치 사본, 각 변이 후 원복·38/38 재확인) — 4종 모두 검출:

| 변이 | 바꾼 곳 | 실패 테스트 |
|---|---|---|
| B1 | `split_leaf` 구분자 = 왼쪽 리프 마지막 키 | 10 |
| B2 | `find_leaf` `sep <= key` → `sep < key` | 4 (키 = 구분자가 왼쪽으로 → `get` None) |
| H1 | 칸 재지정 `bit != 0` → `== 0` | 15 |
| H2 | 칸 재지정 생략 | 8 (proptest 축소에 ~110초) |

- 페이지 I/O·시간: **미측정** (2·3단계).

#### 틀렸던 이해 (오답 노트 요약 — 원문은 repo `btree-qa.md`·`hash.md` §6)

- **"가운데 키는 리프에서 올라온다"** ✗ — 내부 분할의 70은 넘친 내부 노드 안의 키를 꺼낸 것. 리프의 70은 예전 copy-up 때 남은 원본.
- **"중간값은 내부 노드에서 더 빨리 도달"** ✗ — B+tree는 값이 리프에만 있고 `get`은 항상 리프까지 간다(내부에 값을 두는 건 B-tree).
- **"루트가 없으면 첫 키가 부모 노드가 된다"** ✗ — 구분자 1개 + 자식 2개를 가진 새 내부 노드가 루트가 된다.
- **해시 분할에서 next/prev에 끼운다** ✗ — B+tree와 혼동. 해시 버킷엔 연결이 없고 디렉터리 칸이 가리키는 번호만 바뀐다. 두 배 때도 복사하는 건 디렉터리(번호표)뿐, 지역 깊이는 그대로.
- **저장 값 = `mix(key)`** ✗ — **세 게이트 연속(09a·09b·10) 힌트 없이 처음 물었을 때 틀림.** 버킷엔 원래 키가 저장되고(`push(key)`), `mix`는 칸을 고르거나 `check()`가 제자리를 검사할 때만 쓴다. 실제 버킷 출력을 보고서야 정리됨 → 2단계 첫 게이트에서 힌트 없이 1문 선행 예정.
  > 기억할 한 줄: **저장은 원래 키, 위치는 `mix(key)`.**
- **"삽입마다 check로 깨짐을 방지"** ✗ — 테스트는 **방지가 아니라 검출**한다. 얻는 것은 깨진 삽입·키의 위치와 shrink된 최소 재현.
- 그 밖: `1 << d`를 0b1로 읽음(d=1이면 `0b10` — 1을 d칸 민 값) · "깊이 2면 2의 2배"(2^2) · `mix`와 mask의 −1 혼동 · `pub mod` 줄을 라이브러리 import로 오해(모듈 트리 연결 선언).

#### 막힌 것

- src가 아직 미추적일 때 `git checkout`으로 변이 원복이 안 돼 변이가 남음 → 이후 변이는 스크래치 사본에서만.
- `#[expect(dead_code)]`가 기대한 경고가 안 나면 `unfulfilled_lint_expectations`가 나고 `-D warnings`가 오류로 올림.
- Hash 스모크를 debug + cap 1 + 매 삽입 전체 검사로 돌려 120초 초과(cap 1은 전역 깊이 15 → 32768칸) → proptest 용량을 2..=4로(1은 너무 깊고, 100은 분할이 거의 안 일어남).

#### cs/ 추출 후보

- copy-up vs push-up · 구분자 규칙 · 양방향 리프 링크와 역순 스캔(`ORDER BY … DESC LIMIT`) → [data-structure/15-b-tree](../../../cs/data-structure/15-b-tree/) · [database/08-btree-indexes](../../../cs/database/08-btree-indexes/)
- Extendible Hash(전역/지역 깊이, 두 분할, 디렉터리 복사, 해시 함수가 디렉터리 폭주를 막는 이유) → [data-structure/05-hashmap](../../../cs/data-structure/05-hashmap/) (해당 챕터 범위 확인 필요)
- 정답지 대조 속성 테스트 · 매 연산 구조 검사 · 변이 점검으로 테스트를 검증 → [testing/14-property-based-testing](../../../cs/testing/14-property-based-testing/) · [testing/15-mutation-testing](../../../cs/testing/15-mutation-testing/)
