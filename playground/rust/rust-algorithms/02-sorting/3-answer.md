# rust/rust-algorithms/02 — 정렬 알고리즘 (Sorting) — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. `[2, 1, 4, 5, 8]` 과 `2` — 피벗 4 가 인덱스 2 에 자리잡는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

`a` 는 `[2, 1, 4, 5, 8]`, `p` 는 `2` 다.

**왜 그런가**

- 피벗은 마지막 원소 `4`, `i = 0` 에서 시작한다.
- `j=0` 의 5 는 4 보다 커서 그냥 지나간다.
- `j=1` 의 2 는 4 이하라 `swap(0, 1)` → `[2, 5, 8, 1, 4]`, `i = 1`.
- `j=2` 의 8 은 지나간다.
- `j=3` 의 1 은 4 이하라 `swap(1, 3)` → `[2, 1, 8, 5, 4]`, `i = 2`.
- 끝으로 `swap(2, 4)` 가 피벗을 경계로 옮겨 `[2, 1, 4, 5, 8]`, `2` 를 돌려준다.
- 피벗 왼쪽 `[2, 1]` 은 아직 정렬되지 않았다 — 그것은 재귀가 맡는다.
- 근거: 2-summary 「동작 방식 (4)」.

### 2. `[(1, 'b'), (1, 'a'), (2, 'c')]` — 키가 같은 둘은 원래 순서 그대로

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

`[(1, 'b'), (1, 'a'), (2, 'c')]` 다.

**왜 그런가**

- 키는 튜플의 첫 값이라 `(1, 'b')` 와 `(1, 'a')` 는 키가 같다.
- `sort_by_key` 는 `sort` 계열이라 안정 정렬이다 — 키가 같은 원소의 원래 앞뒤를 지킨다.
- 두 번째 값 `'a'` · `'b'` 는 비교에 쓰이지 않으므로 `'a'` 가 앞으로 오지 않는다.
- 원본 코드의 주석도 「(1,'b'),(1,'a') 순서 유지」라고 적는다.
- 근거: 2-summary 「동작 방식 (6)」.

### 3. 바깥 루프 1 번, 비교 3 번 — 조기 종료

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

바깥 루프는 `i = 0` 한 번만 돌고, 비교는 3 번이다.

**왜 그런가**

- `n = 4` 라서 `i = 0` 일 때 안쪽 범위는 `0..3`, 비교가 3 번 일어난다.
- 모든 비교에서 `arr[j] > arr[j + 1]` 이 거짓이라 `swapped` 가 `false` 로 남는다.
- `if !swapped { break; }` 가 바깥 루프를 끝낸다.
- 그래서 이미 정렬된 입력에서 버블 정렬은 O(n) 이다.
- 근거: 2-summary 「동작 방식 (1)」.

### 4. `[i32; 7]` 은 `Copy` 라 대입이 복사다

- 원소 `i32` 가 `Copy` 이므로 고정 길이 배열 `[i32; 7]` 도 `Copy` 다.
- `let mut a1 = original;` 은 소유권 이동이 아니라 원소 7 개의 복사다.
- 정렬은 `a1` 의 복사본만 고치고 `original` 은 손대지 않는다.
- 그래서 다음 정렬을 위해 `original` 을 다시 대입할 수 있다.
- `Vec` 였다면 `Copy` 가 아니라 대입이 이동이 되어 두 번째 대입부터 컴파일 오류다 — 이 경우는 `.clone()` 이 필요하다 (원본에 근거 없음 — 추론).
- 근거: 2-summary 「동작 방식 (7)」.

### 5. `<` 로 바꾸면 안정성이 깨진다

- 값이 같을 때 `<=` 는 왼쪽(원래 앞에 있던 원소)을 먼저 쓴다.
- `<` 로 바꾸면 같은 값에서 조건이 거짓이 되어 오른쪽(원래 뒤에 있던 원소)이 먼저 쓰인다.
- 그러면 같은 값의 원래 앞뒤가 뒤집혀 머지 정렬이 불안정해진다.
- 정렬 결과의 값 차례는 여전히 맞다 — 깨지는 것은 같은 값끼리의 순서뿐이다.
- 근거: 2-summary 「동작 방식 (5)」 · 「어디서 틀리나 2」.

### 6. 한쪽으로 몰려 O(n²), 재귀 깊이도 n 에 가까워진다

- 피벗이 늘 마지막 원소 = 최댓값이므로, 파티션 뒤 왼쪽에 n−1 개, 오른쪽(피벗 제외)에 0 개가 남는다.
- 매 단계 크기가 하나씩만 줄어 비교 횟수가 (n−1) + (n−2) + … 가 되어 O(n²) 이다 — 원본 표의 「최악 O(n²)」 경우다.
- 재귀도 한 단계에 하나씩 깊어지므로 스택 깊이가 n 에 가깝다.
- 원본 표의 공간 O(log n) 은 평균 재귀 깊이라, 이 최악 경우에는 맞지 않고 O(n) 까지 간다 (원본에 근거 없음 — 추론).
- 근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 4」.

### 7. 장담할 수 없다

- `sort_unstable` 계열은 같은 키의 원래 순서를 보존한다고 약속하지 않는다.
- 결과가 `(1, 'b')` 먼저일 수도, `(1, 'a')` 먼저일 수도 있고, 어느 쪽이든 API 약속에 맞는다.
- 「반드시 뒤집힌다」도 아니다 — 약속이 없을 뿐이다.
- 원래 순서를 지켜야 하면 `sort_by_key` 처럼 안정 판을 쓴다.
- 근거: 2-summary 「동작 방식 (6)」 · 「구현 세부사항 대 언어 보장」.

### 8. 비교 결과를 반대로 내 주기 때문이다

- 정렬은 비교 클로저가 `Less` 라고 하는 쪽을 앞에 둔다.
- `a.cmp(b)` 는 `a` 가 작으면 `Less` 라 작은 값이 앞에 온다 — 오름차순.
- `b.cmp(a)` 는 `a` 가 크면 `Less` 가 되어 큰 값이 앞에 온다 — 내림차순.
- 즉 인자 순서를 바꾸는 것만으로 모든 `Ordering` 이 뒤집힌다.
- 근거: 2-summary 「동작 방식 (6)」 · 「어디서 틀리나 7」.

### 9. 같은 데이터에 `&mut` 는 동시에 하나만 — 겹치지 않음을 보증해 둘을 준다

- Rust 는 같은 데이터를 가리키는 가변 참조를 동시에 둘 둘 수 없게 한다.
- `arr` 하나에서 `&mut arr[..p]` 와 `&mut arr[p..]` 를 동시에 쥐려 하면, 컴파일러는 둘이 겹치지 않는다는 것을 스스로 증명하지 못한다.
- `split_at_mut` 은 표준 라이브러리가 두 조각이 겹치지 않음을 보증하고 두 `&mut` 슬라이스를 함께 내준다.
- 그래서 빌림 규칙을 어기지 않고 왼쪽과 오른쪽을 따로 재귀할 수 있다.
- 근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 5」.

## 실습 정답

### 실습 1. 다섯 가지 정렬 직접 구현과 표준 정렬 비교

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 인접 비교 · `swap` | `bubble_sort` 의 `if arr[j] > arr[j + 1] { arr.swap(j, j + 1); … }` |
| 2. 마지막 `i` 칸 제외 | `for j in 0..n - 1 - i` |
| 3. 조기 종료 | `let mut swapped = false;` · `if !swapped { break; }` |
| 4. 최솟값 인덱스와 교환 | `selection_sort` 의 `(i..n).min_by_key(\|&j\| arr[j]).unwrap()` · `arr.swap(i, min_idx)` |
| 5. key 를 쥐고 밀고 넣기 | `insertion_sort` 의 `let key = arr[i];` · `while j > 0 && arr[j - 1] > key` · `arr[j] = key;` |
| 6. Lomuto 파티션 | `partition` 의 `let pivot = arr[arr.len() - 1];` · `if arr[j] <= pivot` · `arr.swap(i, arr.len() - 1); i` |
| 7. 베이스 케이스 | `quick_sort` 의 `if arr.len() <= 1 { return; }` |
| 8. 나눠서 재귀 | `arr.split_at_mut(pivot_idx)` · `quick_sort(left)` · `quick_sort(&mut right[1..])` |
| 9. 절반 복사 · 재귀 | `merge_sort` 의 `arr[..mid].to_vec()` · `arr[mid..].to_vec()` · 재귀 두 번 |
| 10. 병합 · 남은 원소 | `if left[i] <= right[j]` 의 `while` 과 뒤따르는 두 `while` |
| 11. 원본 찍기 | `println!("원본: {:?}", original);` |
| 12. 복사본마다 정렬 | `let mut a1 = original;` … `a5` 와 각 정렬 호출 |
| 13. 튜플 안정 정렬 | `v1.sort_by_key(\|&(k, _)\| k);` |
| 14. `sort` · `sort_unstable` | `v2.sort();` · `v3.sort_unstable();` |
| 15. 내림차순 | `v4.sort_unstable_by(\|a, b\| b.cmp(a));` |
| 16. 비교 표 | `=== 정렬 알고리즘 비교 ===` 아래 `println!` 여섯 줄 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`rust/rust-algorithms/reference/sorting.rs`

```rust
// [알고리즘 & 자료구조] 정렬 알고리즘 (Sorting)
// 설명: 버블/선택/삽입/퀵/머지 정렬 직접 구현과 Rust sort vs sort_unstable 비교
// 팁: sort()는 안정 정렬(TimSort 기반)로 같은 값의 상대 순서를 보존한다. sort_unstable()은 pdqsort(pattern-defeating quicksort) 기반으로 안정성은 없지만 더 빠르고 추가 메모리를 쓰지 않는다. 대부분의 경우 sort_unstable()이 성능이 좋다. sort_by_key로 특정 필드 기준 정렬, sort_by로 커스텀 비교가 가능하다.

// 버블 정렬 O(n²): 인접 원소 비교/교환을 반복
fn bubble_sort(arr: &mut [i32]) {
    let n = arr.len();
    for i in 0..n {
        // 한 번이라도 교환이 있었는지 추적 (없으면 이미 정렬됨)
        let mut swapped = false;
        // 매 패스마다 큰 값이 끝으로 가므로 마지막 i개는 검사 제외
        for j in 0..n - 1 - i {
            if arr[j] > arr[j + 1] {
                // 슬라이스의 swap: 메모리 안전한 인덱스 교환
                arr.swap(j, j + 1);
                swapped = true;
            }
        }
        // 조기 종료 최적화 (Best case O(n))
        if !swapped { break; }
    }
}

// 선택 정렬 O(n²): 매번 최솟값을 찾아 앞에 배치
fn selection_sort(arr: &mut [i32]) {
    let n = arr.len();
    for i in 0..n {
        // (i..n) 범위의 인덱스 중 arr[j]가 최소인 j 찾기
        // min_by_key는 클로저의 결과가 최소인 원소를 반환
        let min_idx = (i..n).min_by_key(|&j| arr[j]).unwrap();
        arr.swap(i, min_idx);
    }
}

// 삽입 정렬 O(n²): 거의 정렬된 데이터에 효율적 (Best case O(n))
fn insertion_sort(arr: &mut [i32]) {
    for i in 1..arr.len() {
        // 현재 삽입할 키 값
        let key = arr[i];
        let mut j = i;
        // key보다 큰 원소들을 오른쪽으로 한 칸씩 밀기
        while j > 0 && arr[j - 1] > key {
            arr[j] = arr[j - 1];
            j -= 1;
        }
        // 알맞은 위치에 key 삽입
        arr[j] = key;
    }
}

// 퀵 정렬 O(n log n) 평균, O(n²) 최악
fn quick_sort(arr: &mut [i32]) {
    // 베이스 케이스: 0 또는 1개면 이미 정렬됨
    if arr.len() <= 1 { return; }
    // 분할 → 피벗 인덱스 반환
    let pivot_idx = partition(arr);
    // split_at_mut: 슬라이스를 두 가변 슬라이스로 분리 (대여 검사 통과)
    let (left, right) = arr.split_at_mut(pivot_idx);
    // 좌/우 재귀 정렬
    quick_sort(left);
    quick_sort(&mut right[1..]); // 피벗 제외
}

// Lomuto 파티션: 마지막 원소를 피벗으로
fn partition(arr: &mut [i32]) -> usize {
    let pivot = arr[arr.len() - 1];
    // i = 피벗보다 작은 영역의 경계
    let mut i = 0;
    for j in 0..arr.len() - 1 {
        // 피벗 이하 원소를 앞으로 모음
        if arr[j] <= pivot {
            arr.swap(i, j);
            i += 1;
        }
    }
    // 마지막에 피벗을 알맞은 위치로 배치
    arr.swap(i, arr.len() - 1);
    i
}

// 머지 정렬 O(n log n): 분할 + 병합. 안정 정렬
fn merge_sort(arr: &mut [i32]) {
    if arr.len() <= 1 { return; }
    let mid = arr.len() / 2;
    // 좌/우 절반을 별도의 Vec으로 복사 (to_vec)
    let mut left = arr[..mid].to_vec();
    let mut right = arr[mid..].to_vec();
    // 분할: 재귀 정렬
    merge_sort(&mut left);
    merge_sort(&mut right);
    // 병합: 두 정렬된 배열을 합쳐서 원본 슬라이스에 다시 씀
    let (mut i, mut j, mut k) = (0, 0, 0);
    while i < left.len() && j < right.len() {
        // 작은 쪽을 먼저 (<= 로 안정성 보장)
        if left[i] <= right[j] {
            arr[k] = left[i]; i += 1;
        } else {
            arr[k] = right[j]; j += 1;
        }
        k += 1;
    }
    // 남은 원소들 그대로 복사
    while i < left.len() { arr[k] = left[i]; i += 1; k += 1; }
    while j < right.len() { arr[k] = right[j]; j += 1; k += 1; }
}

fn main() {
    let original = [64, 34, 25, 12, 22, 11, 90];
    println!("원본: {:?}", original);

    // 각 정렬마다 원본 복사본을 만들어 정렬
    let mut a1 = original;
    bubble_sort(&mut a1);
    println!("버블 정렬:  {:?}", a1);

    let mut a2 = original;
    selection_sort(&mut a2);
    println!("선택 정렬:  {:?}", a2);

    let mut a3 = original;
    insertion_sort(&mut a3);
    println!("삽입 정렬:  {:?}", a3);

    let mut a4 = original;
    quick_sort(&mut a4);
    println!("퀵 정렬:    {:?}", a4);

    let mut a5 = original;
    merge_sort(&mut a5);
    println!("머지 정렬:  {:?}", a5);

    // Rust 표준: sort (안정, TimSort) vs sort_unstable (불안정, pdqsort)
    println!("\n=== 표준 라이브러리 정렬 ===");
    // 같은 키(1)를 가진 'b','a'의 상대 순서가 유지되는지 확인
    let mut v1 = vec![(1, 'b'), (1, 'a'), (2, 'c')];
    // sort_by_key: 키 함수 결과 기준 정렬
    v1.sort_by_key(|&(k, _)| k);
    println!("sort (안정):     {:?}", v1); // (1,'b'),(1,'a') 순서 유지

    let mut v2 = original;
    // sort: 안정 정렬 (TimSort)
    v2.sort();
    println!("sort:            {:?}", v2);

    let mut v3 = original;
    // sort_unstable: 불안정이지만 더 빠름 (pdqsort)
    v3.sort_unstable();
    println!("sort_unstable:   {:?}", v3);

    // 커스텀 비교: 내림차순
    let mut v4 = original;
    // sort_unstable_by: 비교 클로저 |a, b| → Ordering
    // b.cmp(a) → 큰 값이 먼저 = 내림차순
    v4.sort_unstable_by(|a, b| b.cmp(a));
    println!("내림차순:        {:?}", v4);

    // 정렬 알고리즘 비교 표 출력
    println!("\n=== 정렬 알고리즘 비교 ===");
    println!("알고리즘     | 평균       | 최악       | 공간    | 안정");
    println!("버블 정렬   | O(n²)     | O(n²)     | O(1)   | O");
    println!("선택 정렬   | O(n²)     | O(n²)     | O(1)   | X");
    println!("삽입 정렬   | O(n²)     | O(n²)     | O(1)   | O");
    println!("퀵 정렬     | O(n log n)| O(n²)     | O(log n)| X");
    println!("머지 정렬   | O(n log n)| O(n log n)| O(n)   | O");
}
```

**실행 결과** — 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다).

**풀이 요점**

- 다섯 함수가 모두 `&mut [i32]` 를 받아 제자리에서 고치므로, `main` 은 `&mut a1` 처럼 배열 참조를 넘기기만 한다.
- 안정성은 버블 · 삽입의 `>`, 머지의 `<=` 에서 나오고, 선택 · 퀵은 멀리 `swap` 하므로 불안정이다.
- 퀵 정렬은 피벗이 제자리를 찾으므로 `right[1..]` 로 피벗을 빼고 재귀한다.
- 머지 정렬은 `to_vec` 복사본을 정렬한 뒤 원본에 병합해 쓰므로 O(n) 추가 메모리를 쓴다.
- `original` 이 `Copy` 배열이라 복사본을 몇 번이든 새로 만들 수 있다.
- 표준 정렬에서는 안정성이 필요하면 `sort` · `sort_by_key`, 아니면 `sort_unstable` 계열, 방향은 비교 클로저 `b.cmp(a)` 로 바꾼다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 실행하지 않음 — Rust 예제는 이 문서를 만들 때 컴파일 · 실행하지 않았다(cargo 로 돌려 확인한다) |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
