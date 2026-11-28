# rust/rust-algorithms/02 — 정렬 알고리즘 (Sorting) — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. `partition` 을 다섯 원소에 한 번 부르면 (예측)

```rust
// 질문용 발췌
let mut a = [5, 2, 8, 1, 4];
let p = partition(&mut a);
println!("{:?} {}", a, p);
```

- `partition` 이 끝난 뒤 배열 `a` 와 돌려준 값 `p` 는 각각 무엇인가?

### 2. 키가 같은 튜플을 `sort_by_key` 로 정렬하면 (예측)

```rust
// 질문용 발췌
let mut v1 = vec![(1, 'b'), (1, 'a'), (2, 'c')];
v1.sort_by_key(|&(k, _)| k);
println!("{:?}", v1);
```

- 정렬 뒤 `v1` 의 세 원소는 어떤 차례인가?

### 3. 이미 정렬된 배열에 `bubble_sort` 를 부르면 (예측)

```rust
// 질문용 발췌
let mut a = [1, 2, 3, 4];
bubble_sort(&mut a);
```

- 바깥 루프는 몇 번 돌고, `arr[j] > arr[j + 1]` 비교는 모두 몇 번 일어나나?

### 4. `original` 을 다섯 번 대입해도 쓸 수 있는 이유 (왜)

- `let mut a1 = original;` 뒤에 `a1` 을 정렬해도 `original` 이 정렬 전 값 그대로이고 다시 대입할 수 있는 까닭은 무엇인가?

### 5. 머지 정렬 병합의 `<=` (왜)

- 병합 비교 `left[i] <= right[j]` 를 `<` 로 바꾸면 무엇이 깨지며, 왜 그런가?

### 6. 정렬된 입력과 Lomuto 퀵 정렬 (경계)

- `[1, 2, 3, 4, 5, 6, 7]` 처럼 이미 정렬된 입력을 이 `quick_sort` 에 넣으면 나뉘는 모양과 시간 복잡도는 어떻게 되며, 원본 표의 공간 O(log n) 은 이 경우에도 맞나?

### 7. `sort_unstable` 로 바꾸면 (경계)

- 2번의 `v1` 을 `sort_by_key` 대신 `sort_unstable_by_key(|&(k, _)| k)` 로 정렬하면 `(1, 'b')` 가 `(1, 'a')` 보다 앞에 온다고 장담할 수 있나?

### 8. 내림차순과 `Ordering` (연결)

- `sort_unstable_by(|a, b| b.cmp(a))` 가 내림차순이 되는 까닭을 `Ordering` 과 오름차순 `a.cmp(b)` 에 이어 설명하면?

### 9. `split_at_mut` 과 빌림 규칙 (연결)

- 퀵 정렬에서 `split_at_mut` 이 왼쪽 · 오른쪽 조각을 한꺼번에 `&mut` 로 내줄 수 있는 것은 Rust 의 어떤 빌림 규칙과 이어지나?

## 실습

### 실습 1. 다섯 가지 정렬 직접 구현과 표준 정렬 비교

**만들 것** — 버블 · 선택 · 삽입 · 퀵 · 머지 정렬을 `&mut [i32]` 를 받는 함수로 직접 짜고, 같은 원본 배열로 각각 정렬해 찍는다.
이어서 표준 라이브러리 정렬로 안정성 · 내림차순을 보이고, 비교 표를 찍는다.

**요구 조건**

1단계 — 버블 정렬

1. `bubble_sort` 는 바깥 루프 `i` 마다 인접한 두 원소를 비교해 앞이 더 크면 `swap` 한다.
2. 안쪽 루프는 이미 끝에 자리잡은 마지막 `i` 칸을 검사하지 않는다.
3. 한 패스 동안 교환이 없으면 바깥 루프를 끝낸다(조기 종료).

2단계 — 선택 정렬

4. `selection_sort` 는 `i` 마다 `(i..n)` 범위에서 값이 가장 작은 인덱스를 `min_by_key` 로 찾아 `i` 와 바꾼다.

3단계 — 삽입 정렬

5. `insertion_sort` 는 `i = 1` 부터 `key = arr[i]` 를 쥐고, `key` 보다 큰 앞 원소들을 한 칸씩 오른쪽으로 민 뒤 빈 자리에 `key` 를 넣는다.

4단계 — 퀵 정렬

6. `partition` 은 마지막 원소를 피벗으로 삼아(Lomuto), 피벗 이하 원소를 앞으로 모은 뒤 피벗을 그 경계로 옮기고 피벗의 인덱스를 돌려준다.
7. `quick_sort` 는 길이가 1 이하면 바로 돌아간다.
8. `quick_sort` 는 `split_at_mut` 으로 피벗 위치에서 둘로 나눠 왼쪽과, 피벗을 뺀 오른쪽을 재귀 정렬한다.

5단계 — 머지 정렬

9. `merge_sort` 는 길이가 1 이하면 돌아가고, 아니면 두 절반을 `to_vec` 으로 복사해 각각 재귀 정렬한다.
10. 두 정렬된 복사본을 앞에서부터 비교해 작은 쪽(같으면 왼쪽)을 원본에 차례로 쓰고, 남은 원소를 이어 쓴다.

6단계 — `main`: 직접 구현 비교

11. 원본 배열 `[64, 34, 25, 12, 22, 11, 90]` 을 찍는다.
12. 다섯 정렬마다 원본의 복사본을 새로 만들어 정렬하고 결과를 찍는다.

7단계 — `main`: 표준 라이브러리

13. `vec![(1, 'b'), (1, 'a'), (2, 'c')]` 를 튜플 첫 값 기준 `sort_by_key` 로 정렬해 찍는다.
14. 원본 복사본을 `sort()` 로, 또 다른 복사본을 `sort_unstable()` 로 정렬해 각각 찍는다.
15. 원본 복사본을 `sort_unstable_by` 와 비교 클로저로 내림차순 정렬해 찍는다.

8단계 — 비교 표

16. 다섯 알고리즘의 평균 · 최악 · 공간 · 안정 여부 표를 찍는다(시작 코드에 채워 둔 줄 그대로).

**시작 코드**

```rust
fn bubble_sort(arr: &mut [i32]) {
    let n = arr.len();
    for i in 0..n {
        // TODO: 교환 여부 추적 변수
        // TODO: 마지막 i 칸을 뺀 범위에서 인접 비교 · swap
        // TODO: 교환이 없었으면 break
    }
}

fn selection_sort(arr: &mut [i32]) {
    let n = arr.len();
    for i in 0..n {
        // TODO: (i..n) 중 arr[j] 가 최소인 j 를 min_by_key 로 찾고 i 와 swap
    }
}

fn insertion_sort(arr: &mut [i32]) {
    for i in 1..arr.len() {
        // TODO: key 를 쥐고, 큰 앞 원소를 오른쪽으로 밀고, 빈 자리에 key 넣기
    }
}

fn quick_sort(arr: &mut [i32]) {
    // TODO: 베이스 케이스
    // TODO: partition → split_at_mut → 좌/우(피벗 제외) 재귀
}

fn partition(arr: &mut [i32]) -> usize {
    // TODO: 마지막 원소를 피벗으로 한 Lomuto 파티션, 피벗 인덱스 반환
    0
}

fn merge_sort(arr: &mut [i32]) {
    // TODO: 베이스 케이스
    // TODO: 두 절반을 to_vec 으로 복사해 재귀 정렬
    // TODO: 병합 (같으면 왼쪽 먼저) + 남은 원소 복사
}

fn main() {
    let original = [64, 34, 25, 12, 22, 11, 90];
    println!("원본: {:?}", original);

    // TODO: a1..a5 를 original 에서 복사해 각 정렬 함수로 정렬
    // println!("버블 정렬:  {:?}", a1);
    // println!("선택 정렬:  {:?}", a2);
    // println!("삽입 정렬:  {:?}", a3);
    // println!("퀵 정렬:    {:?}", a4);
    // println!("머지 정렬:  {:?}", a5);

    println!("\n=== 표준 라이브러리 정렬 ===");
    let mut v1 = vec![(1, 'b'), (1, 'a'), (2, 'c')];
    // TODO: 첫 값 기준 sort_by_key
    println!("sort (안정):     {:?}", v1);

    // TODO: v2 = sort(), v3 = sort_unstable(), v4 = 내림차순 sort_unstable_by
    // println!("sort:            {:?}", v2);
    // println!("sort_unstable:   {:?}", v3);
    // println!("내림차순:        {:?}", v4);

    println!("\n=== 정렬 알고리즘 비교 ===");
    println!("알고리즘     | 평균       | 최악       | 공간    | 안정");
    println!("버블 정렬   | O(n²)     | O(n²)     | O(1)   | O");
    println!("선택 정렬   | O(n²)     | O(n²)     | O(1)   | X");
    println!("삽입 정렬   | O(n²)     | O(n²)     | O(1)   | O");
    println!("퀵 정렬     | O(n log n)| O(n²)     | O(log n)| X");
    println!("머지 정렬   | O(n log n)| O(n log n)| O(n)   | O");
}
```

**확인 방법** — `rustc sorting.rs && ./sorting` (또는 `cargo run`)으로 돌려, 다섯 직접 구현과 `sort` · `sort_unstable` 줄이 모두 같은 오름차순 배열인지, 안정 정렬 줄에서 `(1, 'b')` 가 `(1, 'a')` 앞에 있는지, 내림차순 줄이 큰 값부터인지 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
