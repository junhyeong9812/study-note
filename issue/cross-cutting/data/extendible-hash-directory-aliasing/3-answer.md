# issue/cross-cutting/data/extendible-hash-directory-aliasing — 정답

태그: `silent-failure`

## 정답
<!-- 질문 1:1 대응 -->

1. **`2^(g-d)`개이고, 칸 번호의 끝 d비트가 그 버킷의 접미사(suffix)와 같은 칸들이다 — 접미사부터 `2^d` 간격으로 놓인다. 지역 깊이는 "이 버킷이 키를 구분하는 데 실제로 쓰는 비트 수"다.**\
   디렉터리는 해시의 하위 g비트로 칸을 고르지만, 버킷은 그중 하위 d비트만 본다. 나머지 g−d비트가 무엇이든 같은 버킷이므로 그만큼의 칸이 한 버킷을 함께 가리킨다.\
   10진수로 비유하면 "끝 두 자리가 37인 수"가 37부터 100 간격으로 놓이는 것과 같다.
   > **확장 해싱(extendible hashing)** — 해시 하위 g비트로 디렉터리 칸을 고르고, 칸이 버킷을 가리키는 2단 구조. 넘친 버킷만 나누고, 필요할 때만 디렉터리를 두 배로 한다.
   > **전역 깊이 / 지역 깊이** — 디렉터리가 보는 비트 수(g) / 버킷이 보는 비트 수(d). 항상 d ≤ g.

2. **디렉터리 두 배는 1번, 분할은 끝없이 반복된다 — 삽입이 끝나지 않는다.**\
   계측(분할·두 배마다 출력)으로 본 실제 순서는 `SPLIT d=0 g=0` → `DOUBLE` 1번 → 그 뒤 `SPLIT d=0 g=1`이 10초 동안 약 20만 번이었다.\
   삽입 루프는 "버킷이 용량 이하가 될 때까지 분할"인데, 분할이 아무것도 바꾸지 못하니 조건이 영영 참이 되지 않는다. 분할마다 새 페이지를 할당하므로 빈 버킷이 계속 쌓인다.

3. **두 배는 `d == g`일 때만 일어나는데 첫 두 배로 g만 1이 되고 d는 0에 머물러 다시는 같지 않고, 분할 비트 `1 << d`는 계속 첫 분할과 같은 비트이기 때문이다.**\
   첫 분할에서 그 비트가 1인 키는 이미 새 버킷으로 나갔다. 옛 버킷에 남은 키는 전부 그 비트가 0이라 두 번째 분할부터는 옮길 키가 없다.\
   처음엔 "매 분할마다 두 배 반복"으로 잘못 짐작했고, 계측으로 정정했다 — 무한 루프의 모양은 코드를 따라가기 전에 단정하지 않는다.

4. **시작을 `suffix`로 하면 남아야 할 칸을 새 버킷으로 옮기고(정반대), 간격을 `2^d`로 하면 끝 d비트만 지켜 남아야 할 칸이 섞인다.**\
   전역 3·d=1·suffix=1이면 분할 전 칸은 1, 3, 5, 7이다. 새 버킷이 받을 칸은 끝 2비트가 `suffix | bit = 01 | 10 = 11`인 칸 = 3, 7(시작 3, 간격 4).\
   시작 = suffix면 1, 5가 옮겨지고, 간격 = 2^d면 3, 5, 7이 옮겨진다 — 둘 다 키가 실제로 있는 버킷과 칸이 가리키는 버킷이 어긋나 조회가 틀린다.

5. **`[(10,100), (10,100), (20,200), (20,200)]` — 정답 `[(10,100), (20,200)]`과 다르다. 느려지는 문제가 아니라 결과가 틀리는 문제다.**\
   칸을 훑으면 버킷을 그 버킷이 차지한 칸 수만큼 반복해 방문한다. 정렬은 같은 원소를 붙여 놓을 뿐 지우지 않는다.\
   고친 방법: 쓰는 칸에서 버킷 번호만 모아 정렬하고 중복을 제거한 뒤, 버킷마다 한 번씩 키를 읽는다.

6. **0번 페이지, 즉 메타 페이지로 해석된다 — 메타 페이지를 버킷으로 읽게 된다.**\
   전역 깊이 2면 디렉터리 페이지의 앞 4칸만 쓰고 나머지는 0이다. 이 페이지에서 쓰는 칸 수는 `min(2^g − 페이지 앞까지의 칸 수, 페이지당 칸 수)`로 계산한다.\
   0이 "없음"이 아니라 유효한 페이지 번호로 해석되는 구조라, 고정 크기 저장 단위의 논리 길이를 따로 지켜야 한다.

7. **앞 단계의 버킷 중복 제거에 기댄다 — 버킷이 한 번씩만 방문돼야 키가 한 번씩만 나온다.**\
   이 주석은 맞지만 그 전제는 다른 함수가 만든다. 중복 제거를 빼는 변이는 이 주석을 거짓으로 만들고, 결과 비교 테스트에서 여러 개 실패로 드러났다.

## 문제 구조 (추상화 코드)

### 변형 A — 분할에서 지역 깊이를 올리지 않음 (진행 없는 루프)
① 문제 코드
```rust
fn insert(&mut self, key: u64, val: u64) -> Result<()> {
    let b = self.bucket_for(key);
    self.put(b, key, val);
    while self.count(b) > self.cap { self.split(b)?; }      // 분할이 진행을 만든다고 가정
    Ok(())
}

fn split(&mut self, b: Id) -> Result<()> {
    let d = self.local_depth(b);
    if d == self.global_depth { self.double()?; }           // g += 1
    let bit = 1u64 << d;
    let nb = self.new_bucket()?;
    self.move_keys_where(b, nb, |h| h & bit != 0);
    // old.local_depth = d + 1;   ← 빠짐: 다음 분할도 같은 bit, 옮길 키 0개
    self.repoint_slots(b, nb, d);
    Ok(())
}
```
② 고친 코드
```rust
fn split(&mut self, b: Id) -> Result<()> {
    let d = self.local_depth(b);
    if d == self.global_depth { self.double()?; }
    let bit = 1u64 << d;
    let nb = self.new_bucket()?;
    self.move_keys_where(b, nb, |h| h & bit != 0);
    self.set_local_depth(b, d + 1);                          // 다음 분할은 다음 비트
    self.set_local_depth(nb, d + 1);
    // 끝 d+1비트 = suffix|bit 인 칸만: 시작 suffix|bit, 간격 2^(d+1)
    let mut s = (suffix(b, d) | bit) as usize;
    while s < (1 << self.global_depth) { self.set_slot(s, nb); s += 1 << (d + 1); }
    Ok(())
}
```
무엇이 깨졌나: 분할의 진행을 만드는 상태(지역 깊이)가 갱신되지 않아, 같은 비트로 나누기를 무한히 반복했다.

### 변형 B — 칸을 훑어 버킷을 중복 방문
① 문제 코드
```rust
fn range(&self, lo: u64, hi: u64) -> Result<Vec<(u64, u64)>> {
    let mut out = vec![];
    for slot in 0..SLOTS_PER_PAGE {                       // 쓰지 않는 칸(0 = 메타 페이지)까지
        let b = self.slot(slot);
        out.extend(self.keys_of(b)?.filter(|(k, _)| lo <= *k && *k <= hi));
    }
    out.sort_unstable_by_key(|e| e.0);                    // 순서만 — 중복은 남는다
    Ok(out)
}
```
② 고친 코드
```rust
fn buckets(&self) -> Result<Vec<Id>> {
    let len = 1usize << self.global_depth;
    let mut ids = vec![];
    for (p, dir) in self.directory_pages()?.enumerate() {
        let n = (len - p * SLOTS_PER_PAGE).min(SLOTS_PER_PAGE);   // 이 페이지에서 쓰는 칸만
        ids.extend_from_slice(&dir.slots[..n]);
    }
    ids.sort_unstable();
    ids.dedup();                                          // 칸 → 버킷: 다대일을 일대일로
    Ok(ids)
}
// range: buckets()의 각 버킷을 한 번씩 읽어 거르고 정렬 (키 중복이 없으니 불안정 정렬로 충분)
```
무엇이 깨졌나: 별칭 칸 수만큼 같은 버킷의 키가 결과에 반복됐고, 정렬이 그것을 감췄다(오류 없이 틀린 결과).

## 검증 기록
- 2026-11-17: 사건 기록 대조·추상화(Claude 초안) — 지역 깊이 미갱신 변이를 계측 재실행해 두 배 1회 후 같은 비트 분할 약 20만 회(10초)를 확인(처음 "매번 두 배" 기록을 정정). 중복 제거 생략·쓰지 않는 칸 읽기·재지정 시작/간격 변이가 결과 대조 테스트에서 실패로 검출됨을 확인.

## 참고
- Fagin et al., "Extendible Hashing — A Fast Access Method for Dynamic Files" (ACM TODS, 1979): https://doi.org/10.1145/320083.320092

## 관련 카드
- [lookup-cost-and-indexing](../lookup-cost-and-indexing/) — 같은 확장 해싱에서 해시 함수가 디렉터리 깊이를 정하는 이야기(방안 비교 — 확장 해싱).
- [graph-traversal-invariants](../graph-traversal-invariants/) — 여러 참조가 한 노드로 모이는 구조를 순회할 때의 중복 방문. 저쪽은 visited 집합, 이쪽은 버킷 번호 중복 제거.
- [property-test-cost-budget](../../testing/property-test-cost-budget/) — 같은 구조의 삽입마다 전체 검사 비용.
