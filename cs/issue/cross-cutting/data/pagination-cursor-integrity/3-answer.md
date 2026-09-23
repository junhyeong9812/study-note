# cs/issue/data/pagination-cursor-integrity — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 사건 기록 원문 대조 작성. 복습 전 읽지 말 것.

태그: `silent-failure`

## 정답
<!-- 질문 1:1 대응 -->

1. **이어받기가 다른 집합을 가리켰다.** "모든 브랜치" 쿼리의 결과는 여러 브랜치 커밋이 시간순으로 섞인 목록이다.\
   2페이지를 "1페이지 마지막 커밋의 조상"으로 조회하면, 그 커밋의 조상이 **아닌** 다른 브랜치의 커밋은 이후 어떤 페이지에서도 도달할 수 없다.\
   실측: 708 커밋 중 279 만 도달했다.\
   원리: **DAG 를 선형 목록으로 페이징할 때, 이어받기 쿼리가 첫 쿼리와 다른 집합을 가리키면 가지가 통째로 빠진다.**
   > **DAG(방향 비순환 그래프)** — 커밋 그래프처럼 간선에 방향이 있고 순환이 없는 그래프. "조상"은 한 노드에서 거슬러 도달 가능한 노드들뿐이다.

2. **"전부다"라고 말하는 유실.** 누락 자체보다 나쁜 것은 마지막 페이지가 `truncated=false` 로 **"잘린 것 없음, 이게 전부"를 보증했다**는 점이다.\
   소비자는 이 신호를 믿고 표시를 끝내므로 항의할 근거조차 없다 — 실패가 성공 응답의 모양을 하고 있다.\
   오류가 나는 유실은 고쳐지지만, 성공 신호를 동반한 유실은 발견되지 않는다.

3. **tip 만 검사하는 커서 → 새 무음 유실.** 모든 페이지가 전체 목록을 읽고 offset 으로 위치만 잡도록 고쳤지만, 커서는 첫 원소(tip)만 같은지 봤다.\
   이미 넘겨준 구간 안에서 브랜치가 삭제되면(tip 은 그대로) 목록이 앞으로 당겨져 offset 이 가리키는 위치가 밀린다.\
   라이브 재현: `page1=[m5, m4, sB]` → 브랜치 삭제 → `page2=[m2, m1]` — **m3 이 존재하는데 어느 페이지에도 없고**, 응답은 `truncated=false`·`next_cursor=null` 이었다.\
   깨지는 조건은 "tip 변경"이 아니라 "**이미 받은 구간의 길이 변경**"이며, 브랜치 삭제·fetch·태그·gc·동률 재정렬이 전부 tip 검사를 통과한다.

4. **양 끝 검사와 잔여 창.** tip 은 앞쪽 변화를, seam(직전 페이지의 마지막 원소 `all[offset-1]`)은 구간 길이 변화를 잡는다.\
   seam 만으로는 부족했다 — 같은 초 타임스탬프 커밋에서 날짜순 정렬이 seam 은 제자리에 두고 **동률 원소끼리만** 재정렬하면 seam 검사를 통과한 채 순서가 바뀐다(seam 은 tip 검사의 상위집합이 아니다).\
   그래서 커서에 둘 다 싣고, 불일치 시 **명시적 에러**를 낸다(조용히 이어붙이지 않는다) — 수정 후 708/708.\
   그래도 양 끝만 비교하고 **내부는 읽지 않으므로**, 양 끝을 보존한 채 내부가 같은 길이로 바뀌는 창이 남는다. 이것은 계약에 "조건부 보장"으로 명시하고 문구를 약화했다.
   > **seam** — 이미 넘겨준 구간과 아직 안 넘긴 구간이 맞닿는 지점의 원소.

5. **필터 뒤 개수로 종료 → 조기 종료.** keyset 스캔이 n 개를 읽어도, 뒤 단계의 삭제 필터가 일부를 떨구면 결과는 n 개보다 적다.\
   이걸 "마지막 페이지"로 판정하면, 삭제 행이 몰린 윈도우에서 **뒤에 남은 데이터 전부를 버리고 종료**한다.\
   정상 데이터에서는 안 보이고 비정형 엣지(삭제가 몰린 구간)에서만 깨지는 결함으로, 교차 리뷰가 잡았다.\
   원리: 커서 전진(다음 `last`)과 종료 판정은 **스캔한 키 윈도우**(마지막으로 스캔한 키·스캔 건수)에서 나와야 한다. 필터는 최종 행에 적용한다.

6. **OR 로 묶은 두 신호.** 생산자가 마지막 페이지에 `truncated=true` 를 "상한만큼 읽었음"의 뜻으로 싣자, 소비자의 OR 판정이 "더 있음"으로 읽어 「더 보기」를 띄웠다.\
   눌러보면 `from == total` 로 조회해 **빈 결과**가 나온다 — 없는 잘림을 지어낸 것이다.\
   두 신호의 의미가 다를 때 OR 은 둘 중 느슨한 쪽의 오류를 그대로 들여온다.\
   교정: 개수(`from + received < total`)를 **정본**으로, 플래그는 개수가 스스로 모순일 때만 보는 **백스톱**으로.

7. **픽스처가 결함을 구조적으로 못 만든다.** 단일 브랜치에서는 모든 커밋이 마지막 커밋의 조상이라 "조상 집합 = 전체 집합"이다 — 1번 결함이 원리상 드러날 수 없고, 테스트는 초록이었다.\
   픽스처는 결함이 성립하는 구조(미머지 브랜치 2개: main 5 + side 4)를 가져야 하고, 대조 기준은 구현과 독립적인 전체 개수(`rev-list --all --count`)여야 한다 — "페이지를 이어붙인 합 == 독립 oracle 의 전체".

## 문제 구조 (추상화 코드)

### 변형 A — 이어받기 쿼리가 첫 쿼리와 다른 집합
```rust
// ① 문제
fn page(cursor: Option<Hash>, n: usize) -> Page {
    let items = match cursor {
        None       => log(&["--all"], n),           // 전체 refs
        Some(last) => log(&[last.as_str()], n),     // last 의 조상만
    };
    Page { items, truncated: items.len() == n }
}

// ② 고친 코드
fn page(cursor: Option<Cursor>, n: usize) -> Result<Page> {
    let all = log(&["--all"], MAX);                  // 모든 페이지가 같은 집합
    let offset = cursor.map(|c| c.verify(&all)).transpose()?.unwrap_or(0);
    // ...
}
```
무엇이 깨졌나: 다른 브랜치가 2페이지부터 도달 불가, 마지막 페이지는 "잘림 없음".\
같은 구조: 동일 사건을 다른 소비 측에서도 기록 — 그쪽은 페이징 없이 상한 1회 수신으로 회피.

### 변형 B — 넘겨준 구간 검증이 불완전한 오프셋 커서
```rust
// ① 문제
struct Cursor { offset: usize, tip: Hash }
fn verify(&self, all: &[Hash]) -> Result<usize> {
    if all[0] != self.tip { return Err(Changed) }    // tip 만 — 구간 길이 변화는 통과
    Ok(self.offset)
}

// ② 고친 코드
struct Cursor { offset: usize, tip: Hash, seam: Hash }
fn verify(&self, all: &[Hash]) -> Result<usize> {
    if all[0] != self.tip || all[self.offset - 1] != self.seam {
        return Err(Changed)                          // 명시적 에러
    }
    // 양 끝만 비교, 내부는 보지 않음 → 계약에 "조건부 보장"으로 명시
    Ok(self.offset)
}
```
무엇이 깨졌나: 구간 삭제·재정렬을 커서가 흡수해 무음 유실; seam 단독은 동률 재정렬을 못 잡음.

### 변형 C — 필터 뒤 개수로 전진·종료
```java
// ① 문제
long last = 0;
while (true) {
    List<Row> rows = scan("WHERE id > :last ORDER BY id LIMIT :n", last, n);
    List<Row> kept = rows.stream().filter(r -> !r.deleted()).toList();
    emit(kept);
    if (kept.size() < n) break;                       // 필터가 떨군 만큼 조기 종료
    last = kept.get(kept.size() - 1).id();
}

// ② 고친 코드
while (true) {
    List<Row> rows = scan("WHERE id > :last ORDER BY id LIMIT :n", last, n);
    emit(rows.stream().filter(r -> !r.deleted()).toList());   // 필터는 최종 행에
    if (rows.size() < n) break;                               // 스캔 건수로 종료
    last = rows.get(rows.size() - 1).id();                    // 마지막 스캔 키로 전진
}
```
무엇이 깨졌나: 삭제가 몰린 윈도우에서 남은 데이터 전체가 무음 누락.

### 변형 D — 의미가 다른 두 신호의 OR
```ts
// ① 문제
const hasMore = resp.truncated || from + resp.items.length < resp.total;

// ② 고친 코드
const byCount = from + resp.items.length < resp.total;         // 정본
const hasMore = countIsConsistent(resp) ? byCount : resp.truncated;   // 플래그는 백스톱
```
무엇이 깨졌나: 생산자 플래그("상한만큼 읽음")가 "더 있음"으로 해석돼 가짜 잘림 → 빈 결과 조회.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log
