# index-lab — 직접 만든 인덱스로 "왜 B-tree가 기본인가"를 실측

페이지 기반 스토리지 엔진 위에서 인덱스 구조(B+tree, Hash 등)를 교체하며
**쿼리 패턴 × 데이터 규모 × 버퍼풀 크기**에 따른 성능 차이를 실측하는 실험 프로젝트.

- 원본 repo: [junhyeong9812/index-lab](https://github.com/junhyeong9812/index-lab) · 로컬 `/home/jun/project/lab/storage-labs/index-lab/`
- 스택: Rust (edition 2024) · 테스트 `proptest` · 상태: 로드맵 2/5 완료

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

### 2026-11-17 — 로드맵 2단계: Pager · 버퍼풀 · 페이지 B+tree · 페이지 Extendible Hash (2026-11-12 ~ 11-17)
- 대응 질문: Q1 · Q2 의 측정 재료 — 두 인덱스가 같은 버퍼풀·Pager 위에서 read/write/hit/miss/eviction 카운터를 낸다 (수치 측정은 3단계)
- 코드: index-lab @ `ab318ad` (마지막 코드 커밋 — 페이지 Hash 블라인드 테스트) · `838c33f` (diff 12 변이 점검·학습 노트) — 브랜치 `feat/stage2-pager-buffer-pool` (diff 01~08은 11-15에 main fast-forward)
- 원본 기록: repo `docs/plans/2026-11-12/stage2-pager-buffer-pool/`(명세·로그) · `docs/learning/stage2/`(storage · buffer-pool · btree-page · paged-btree · paged-btree-split-range · paged-btree-tests · paged-hash · paged-hash-insert · paged-hash-range-open · pool-mutations)
- 진행 방식: 1단계와 같은 lazy 모드 — diff 01~12마다 주관식 이해 게이트, 판정은 코드를 읽은 독립 워커. 11-14부터 게이트 질문·재질문·힌트마다 근거 코드를 파일:줄과 함께 다시 붙이는 규칙 적용(내가 "왜 자꾸 코드를 안 보여주고 질문해?"라고 한 뒤).

#### 한 것

- `storage`: `PAGE_SIZE`(16KB)·`PageId`(u64)·`Storage` trait 뒤에 `MemStorage`·`FileStorage`(`read_exact_at`/`write_all_at`, 위치 = id × 16KB) · `Pager`(성공한 read/write만 계수).
- `BufferPool`: 프레임별 `RefCell<Box<Page>>` + 장부(페이지 테이블·핀·dirty·last_used·통계) · `fetch`→`PageRef` / `fetch_mut`→`PageMut`(DerefMut 때만 dirty), drop 시 언핀 · write-back · LRU · `flush` · 모두 핀이면 `AllPinned`(panic 아님).
- `PagedBTree`·`PagedHash`: 1단계 메모리 구현은 그대로 두고 `Index` trait 구현을 2개 추가(총 4개). 페이지 0 = 메타(magic `IDXBTREE`/`IDXHASH_`), `flush` → 다시 `open`하면 같은 내용.
- 테스트 설계는 세 번 모두 블라인드 워커(구현 파일 열람 금지): `tests/buffer_pool.rs`(33) · `tests/paged_btree.rs`(31) · `tests/paged_hash.rs`(40).

#### 설계 결정 (인터뷰 Q1~Q11 + 트레이드오프 S1~S5 — 모두 권장안 선택)

| # | 결정 | 선택 | 이유 |
|---|---|---|---|
| Q1 | 1단계 구현 | 남기고 페이지 버전 추가 | 1단계 테스트 38개 무변경 green, 정답지·알고리즘 기준으로 계속 씀 |
| Q2·Q9 | 페이지 접근 | 핀 가드(RAII) + `&self` API + 프레임마다 `RefCell` | drop = 언핀이라 언핀 누락이 없음. 같은 페이지 이중 가변 빌림은 런타임에 잡힘(단일 스레드 전제) |
| Q3·S3 | Hash 디렉터리 | 페이지에 저장 — 메타에 디렉터리 페이지 번호 배열(최대 2044), 디렉터리 페이지당 칸 2048 | 두 배 쓰기가 카운터에 잡힘(4단계 더블링 스파이크 실험) |
| Q4 | 테스트 저장소 | 메모리(proptest) + 실제 파일(재열기) 둘 다 | P1: 같은 연산열 → 같은 내용·같은 계수 |
| Q5 | 쓰기 정책 | write-back | 내보낼 때·`flush` 때만 쓰기 |
| Q6 | 오류 | Pager·풀은 `Result`, `impl Index`에서만 `expect` | trait 무변경 |
| Q7·S4 | 영속성 | 인덱스 하나 = 파일 하나, 페이지 0 = 메타 | 재열기 경계 명확. 비정상 종료 안전성(WAL)은 범위 밖 |
| Q8 | 바이트 변환 | `bytemuck`(`#[repr(C)]` + `Pod`), `unsafe` 금지 | 크기 단언 `size_of == PAGE_SIZE`로 패딩·용량 실수를 컴파일 오류로 |
| Q10 | 카운터 | Pager read·write + 풀 hit·miss·eviction | 3단계 지표 |
| S1 | `PageId` | `u64` | 8바이트 정렬과 맞아 패딩 없음 |
| S2 | B+tree 용량 | `max_keys` 인자 유지, 상한 = 리프 1022 | 테스트는 2~6으로 분할 강제 |
| S5 | 삽입 중 핀 | 조상은 쥐고 내려가지 않음 — `Split`을 돌려받아 부모를 다시 fetch | P6 핀 상한. 잡은 채 재귀하면 E0502 컴파일 오류 — 빌림 검사가 S5를 강제. 실측 동시 핀 상한 2 (가정 A2는 ≤ 4) |

불변식 P1~P6: P1 Pager 계수 · P2 버퍼풀(핀≥1 안 내보냄 · dirty는 재사용 전 쓰기 · LRU · 적중이면 read 0) · P3 정답지 일치 · P4 구조(I2·I3, 각자 `check()`) · P5 재열기 · P6 핀 상한 = 풀 최소 프레임 수.

#### 도식 — 버퍼풀 `take_frame` (`pool.rs:245-265`)

```
fetch(id) 미스 → take_frame
 ① 빈 프레임 있음?        ─ 예 → 그 프레임
 ② 핀 0인 프레임 중 last_used 최소(LRU) ─ 없음 → Err(AllPinned)
 ③ victim이 dirty?        ─ 예 → pager.write(old_id, 프레임)  ← 실패하면 장부 무변경
 ④ 페이지 테이블에서 old_id 제거 · meta 초기화 · evictions += 1
 → 새 페이지를 그 프레임에 read (miss)
쓰기(③)가 적재보다 먼저 → 그 순간 프레임엔 아직 고친 옛 페이지가 있다. ③이 없으면 고친 값이 오류 없이 사라짐.
```

#### 도식 — 페이지 Hash 배치와 분할 칸 재지정

```
페이지 0 메타 [IDXHASH_ | global_depth | bucket_cap | dir_count | dir_pages[0..2044]]
                                                            │ dir_pages[slot / 2048]
             ▼  (배열 자리 ≠ 페이지 번호: 버킷이 중간에 할당돼 번호가 안 이어짐)
디렉터리 페이지 [slots[0..2048] = 버킷 페이지 번호]   slot = mix(key) & (2^전역 − 1)
             ▼  slots[slot % 2048]
버킷 페이지 [local_depth | count | keys[1023] | values[1023]]  (순서 없음, 원래 키 저장)

분할 (지역 d → d+1, bit = 1<<d) — 예: 전역 3, d = 1, 접미사 1
  이 버킷을 가리키던 칸 = 하위 d비트 = 접미사, 2^d 간격 → 1, 3, 5, 7
  새 비트가 1인 칸만 새 버킷: 시작 = 접미사|bit = 01|10 = 3, 간격 2^(d+1) = 4 → 3, 7
                         1, 5는 옛 버킷 그대로
  (1단계는 디렉터리 전체 훑기 → 이제 해당 칸만 건너뛰며 고쳐 그 디렉터리 페이지만 dirty)
두 배: 칸 < 2048이면 페이지 안 copy_within, 이상이면 디렉터리 페이지를 새 페이지로 통째 복사
       (쓰기 카운트 스파이크) · 2044 × 2048 = 전역 깊이 21 초과면 Err
```

#### 확인

- `cargo test` **78 + 33 + 31 + 40 green** (lib 78 = 1단계 38 + 저장소·풀·페이지 단위 테스트 · buffer_pool 33 · paged_btree 31(15.9s) · paged_hash 40(23.5s)) · `clippy -D warnings` · `fmt --check` 통과.
- **정답지 대조**: proptest가 작은 풀(프레임 2..=4)로 내보내기를 계속 일으키며 `BTreeMap`과 비교, 매 삽입 `check()`. 파일 저장소 케이스는 재열기 후 계속 삽입. 풀 테스트는 참조 모델과 매 연산 reads/writes/hits/misses/evictions 정확 일치.
- **`check()`를 검사하는 테스트**: 일부러 망가뜨린 구조(링크·정렬·구분자 범위·과적·메타·공유 자식 / 버킷 접미사 등)를 `check()`가 거부하는지 — fail-open 방지.
- **변이 점검**: diff마다 실코드 변이 → 블라인드 스위트가 전부 검출(B+tree 8종, Hash 8종 — 단위 테스트에서 생존했던 range 상한 `<`·range_rev 뒤집기 생략 포함). 마지막 diff 12는 버퍼풀 변이 3종 × 전체 스위트:

| 변이 | lib | buffer_pool | paged_btree | paged_hash |
|---|---|---|---|---|
| (a) 내보낼 때 dirty 쓰기 생략 | 16 | 10 | 21 | 31 |
| (b) LRU 대신 MRU | 1 | 7 | 생존 | 생존 |
| (c) 핀 무시 내보내기 | 1 | 6 | 생존 | 생존 |

  → (b)는 결과가 아니라 I/O 수만 바뀌고, (c)는 인덱스 연산에서 핀된 프레임이 늘 가장 최근 사용이라 LRU가 애초에 안 고른다. 인덱스 테스트는 카운터를 안 보므로 **카운터 정확성은 풀 단위 테스트만 지킨다**(3단계 NEXT 신호).
- 페이지 I/O 수치: 카운터만 준비, **미측정** (3단계).

#### 틀렸던 이해 (오답 노트 요약 — 원문은 repo `docs/learning/stage2/` 각 노트)

- **1단계 틈 재확인** ✓ — "저장값이 mix(key)면 check는 mix 다시 안 해도 됨"을 힌트 없이 정답(1단계 3연속 오답 지점). 단 range는 "mix 순서로 정렬"만 봄 → 정렬보다 먼저 필터 `lo <= k <= hi`가 깨진다(빈 Vec). "문자열 비교"도 오개념 — `mix`는 u64 → u64.
- **02** `(16384+100)/16384`를 "2" → "1.xxx" ✗ — 정수 나눗셈은 버림, 정확히 1. 꼬리 100바이트는 다음 할당이 조용히 덮어쓴다(힌트 없는 재질문에서 정답).
- **03** dirty 쓰기를 "롤백"으로 ✗ — `pager.write`는 프레임의 고친 내용을 디스크로 보낸다. "없으면"(값 소실)과 "항상"(값은 맞고 write만 낭비) 두 경우를 섞음.
- **04** 이중 패닉을 "스레드가 잡고 있다" ✗ — 스레드는 하나, 잡은 건 가드. 핀 무시 변이 → RefCell 패닉 → 되감는 중 가드 Drop의 `debug_assert!(pins > 0)` 2차 패닉 → abort. 2/2 fail → 설명 후 통과.
- **07** 리프 copy-up vs 내부 push-up — "구분자가 있어야 리프인지 안다"(✗ `kind`로 안다) · `children()`을 건너뛰어 읽음 · "카운트당 키 1·자식 2"(✗ 키 count·자식 count+1) · "30의 값은 왼쪽 리프"(✗ 오른쪽). 2/2 fail → 설명 후 통과.
- **08** `partition_point`를 "30이 있는 칸 번호 0 → c0"로 읽음 ✗ — 조건(`sep <= key`)을 만족하는 **개수** = 1 → c1. 같은 오류 2회 → 설명 후 통과. check 범위 `<`를 "효율 개선"으로 봄 ✗ — 정확성.
- **09** `slot / 2048 = 1`을 페이지 1로 ✗ — 1은 `dir_pages`의 자리, 페이지 번호는 거기 저장된 값(2단 간접 참조).
- **10** 칸 재지정을 "앞에 1이 붙어 4자리" ✗(그건 두 배) · 반례 계산에서 시작 칸 누락 · `1000`을 16으로, `1 << n`을 `1111`로 ✗. 2/2 fail → 설명 후 통과. 선행 갭: 2진 자리값·`<<`·OR.
- **11** buckets dedup을 "4번 탐색"(비용)으로 ✗ — 정확성(키가 두 번씩 결과에). `[A,A,B,B]`를 끝까지 안 돌려 B 중복 누락.
- **12** "핀 무시면 a에 C 내용이 보인다" — RefCell이 막아 panic이 맞다. 아래 정정 참고.
- **튜터 쪽 전제 정정 2건**: diff 10 Q2 — "지역 깊이 미갱신 변이 = 매 분할마다 두 배 반복"으로 기록·출제했으나 계측해 보니 두 배는 1회, 이후 같은 비트로 **분할만 무한 반복** → 내 답 무효 처리 후 올바른 전제로 재질문. diff 12 Q2 — "무엇이 보이나"가 RefCell 없는 풀 기준의 잘못된 전제 → 시도 미산정 후 재질문.
  > 기억할 한 줄: **루프·카운트 함수는 첫 몇 단계가 아니라 끝까지 손으로 돌린다.** (3단계 첫 게이트에 힌트 없이 1문 선행)

#### 막힌 것

- `bytemuck`의 `[u8; 16384]: Zeroable` 미구현(E0277 — 기본 배열 impl은 고정 길이 목록뿐) → feature `min_const_generics`. 정렬은 `align(8)` 없으면 오프셋에 따라 **간헐** 실패(항상 패닉이 아님).
- 저장소 "구멍 금지"가 버퍼풀과 충돌(새 페이지 5·6 중 6이 먼저 내보내지면 쓰기 실패) → "끝 뒤 쓰기 = 성장, 사이 0"으로 계약 변경. 할당 시 0 페이지 즉시 쓰기는 분할마다 write +1로 측정을 왜곡해 기각.
- Drop 안 패닉 → abort라 `catch_unwind`로도 못 잡고 뒤 테스트·요약 줄까지 사라짐 → `unpin`을 `debug_assert!(pins > 0 || thread::panicking())` + `saturating_sub`로.
- magic 검사 생략 변이가 처음엔 생존 — 0으로 찬 메타는 `max_keys = 0`이라 다른 검사가 먼저 거부 → "magic만 다른 메타"로 테스트 보강.
- 지역 깊이 미갱신 변이는 300s 타임아웃(끝나지 않는 분할) — 검출로 간주, 원인은 계측으로 확인.

#### cs/ 추출 후보

- 버퍼풀(핀·dirty write-back·LRU 내보내기·RAII 가드), 결과는 같고 I/O만 바뀌는 버그는 결과 대조 테스트가 못 잡음 → [database/07-buffer-pool](../../../cs/database/07-buffer-pool/) · 페이지 레이아웃(`bytemuck` Pod·크기 단언) → [database/06-pages-and-tuple-layout](../../../cs/database/06-pages-and-tuple-layout/)
- 디스크 Extendible Hash 3단 페이지(메타 → 디렉터리 → 버킷)와 칸 재지정 식 · 디렉터리 두 배 비용 → [data-structure/05-hashmap](../../../cs/data-structure/05-hashmap/) (범위 확인 필요)
- 페이지 B+tree에서 조상 핀을 쥐지 않는 삽입(`Split` 반환 + 재조회) → [database/08-btree-indexes](../../../cs/database/08-btree-indexes/)
- 블라인드 테스트 + 실코드 변이로 테스트를 검증, 테스트 대상 검사를 실제로 거치는지(magic 변이 생존) → [testing/15-mutation-testing](../../../cs/testing/15-mutation-testing/)
- Drop 중 패닉 → abort: 이미 [issue/rust/drop-panic-during-unwinding](../../../issue/rust/drop-panic-during-unwinding/)로 아카이브됨
