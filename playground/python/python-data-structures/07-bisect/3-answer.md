# python/python-data-structures/07 — bisect (이진 탐색 모듈) — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 3 은 1 과 4, 4 는 둘 다 4 — 없는 값은 두 경계가 같다

**출력**

```text
bisect_left(3):  1
bisect_right(3): 4
bisect_left(4):  4
bisect_right(4): 4
```

**왜 그런가**

`bisect_left` 는 「x 이상인 첫 자리」, `bisect_right` 는 「x 초과인 첫 자리」를 준다.
3 은 인덱스 1~3 에 세 개 있으므로 앞 경계는 1, 뒤 경계는 4 다.
4 는 리스트에 없어 같은 값 무리가 없고, 4 이상인 첫 자리와 4 초과인 첫 자리가 모두 5 가 있는 인덱스 4 다.
그래서 없는 값은 두 결과가 같다.
근거: 2-summary 「동작 방식 (1)」.

### 2. `[1, 3, 4, 5, 7, 9]` 뒤에 `[1, 3, 4, 4, 5, 7, 9]` — 정수라 어느 4 인지 가릴 수 없다

**출력**

```text
삽입 전: [1, 3, 5, 7, 9]
insort(4): [1, 3, 4, 5, 7, 9]
insort_left(4): [1, 3, 4, 4, 5, 7, 9]
```

**왜 그런가**

`insort` 는 `bisect_right` 자리(2)에 4 를 넣는다.
`insort_left` 는 `bisect_left` 자리에 넣는데, 이미 있는 4 가 인덱스 2 이므로 새 4 도 인덱스 2 에 들어가 기존 4 를 한 칸 뒤로 민다.
즉 새 4 는 앞쪽에 들어갔다.
하지만 정수 4 는 서로 구별되지 않으므로 리스트만 보고는 어느 쪽이 새것인지 가릴 수 없다.
근거: 2-summary 「동작 방식 (3)」.

### 3. 70점은 C, 89점은 B, 90점은 A

**출력**

```text
  70점 -> C
  89점 -> B
  90점 -> A
```

**왜 그런가**

`bisect` 는 `bisect_right` 와 같아서, 분기점과 같은 점수는 분기점의 오른쪽 틈으로 간다.
70 은 `[60, 70, 80, 90]` 에서 70 초과인 첫 자리, 곧 인덱스 2 → `'FDCBA'[2]` = C 다.
89 는 80 과 90 사이라 인덱스 3 → B 다.
90 은 90 초과인 첫 자리가 맨 끝(4)이라 → A 다.
근거: 2-summary 「동작 방식 (6)」.

### 4. 두 경계가 모두 8 이라 0 을 돌려준다

**출력**

```text
6의 개수: 0
```

**왜 그런가**

6 은 리스트의 모든 값보다 크다.
그래서 6 이상인 첫 자리도, 6 초과인 첫 자리도 「맨 끝 뒤」인 `len(data)` = 8 이다.
`right - left` = 8 - 8 = 0 이다.
없는 값이면 두 틈이 겹치므로 차가 늘 0 이 된다.
근거: 2-summary 「동작 방식 (5)」.

### 5. 자리는 존재가 아니고, 자리가 리스트 바깥일 수 있어서다

`bisect_left` 는 값이 없어도 「들어갈 자리」를 준다 — 25 를 찾으면 6 이 나오지만 `nums[6]` 은 38 이다.
그래서 그 자리의 값이 `target` 과 같은지 견줘야 「있다」고 말할 수 있다.
또 `target` 이 모든 값보다 크면 자리가 `len(sorted_list)` 가 되어 `sorted_list[i]` 가 `IndexError` 를 낸다.
`i < len(...)` 을 `and` 앞에 두면 이 경우 뒤 조건을 계산하지 않아 안전하다.
근거: 2-summary 「동작 방식 (4)」, 「어디서 틀리나 2 · 3」.

### 6. 분기점과 똑같은 점수(60 · 70 · 80 · 90)가 한 등급 낮아진다 — 「이상」 구간에는 `right` 가 맞다

`bisect_left` 는 같은 값의 왼쪽 틈을 주므로, 70점은 인덱스 1 로 가서 D, 90점은 인덱스 3 으로 가서 B 가 된다.
분기점이 아닌 점수(77, 89 등)는 같은 값이 없어 두 함수의 결과가 같으므로 바뀌지 않는다.
등급 규칙이 「70 이상 80 미만은 C」처럼 경계 값을 위 구간에 넣으므로, 경계 값을 오른쪽 틈으로 보내는 `bisect`(= `bisect_right`)가 맞다.
근거: 2-summary 「동작 방식 (6)」, 「어디서 틀리나 4」.

### 7. 끼워 넣기가 O(n) 이라서 — 원본 팁은 `SortedContainers` 를 권한다

`insort` 의 비용은 자리 찾기 O(log n) 과 끼워 넣기 O(n) 의 합이다.
끼워 넣을 때 그 뒤의 원소를 모두 한 칸씩 밀어야 하므로, 리스트가 길고 삽입이 잦으면 O(n) 쪽이 전체를 좌우한다.
원본 팁은 삽입이 빈번하면 `SortedContainers` 라이브러리를 고려하라고 한다.
근거: 2-summary 「동작 방식 (3)」, 「어디서 틀리나 6」.

### 8. 오류는 나지 않지만, 돌려받은 수에 의미가 없다

`bisect` 함수들은 리스트가 정렬되었다고 가정할 뿐 검사하지 않는다.
이진 탐색은 「가운데 값보다 작으면 답은 오른쪽에 있다」는 정렬 전제로 한쪽 절반을 버리는데, 정렬되지 않으면 이 판단이 틀린다.
그래서 어떤 수든 돌려주지만 그 자리가 올바른 삽입 위치라는 보장이 없다.
근거: 2-summary 「동작 방식 (2)」, 「어디서 틀리나 1」.

### 9. `lower_bound` 는 `bisect_left`, `upper_bound` 는 `bisect_right`

`lower_bound` 는 「x 이상인 첫 위치」라 `bisect_left` 와 같은 일을 한다.
`upper_bound` 는 「x 초과인 첫 위치」라 `bisect_right`(= `bisect`)와 같은 일을 한다.
근거: 2-summary 「동작 방식 (1)」 — 원본 팁이 이 대응을 적고 있다.

### 10. `in` 이 `__contains__` 를 부르고, 그 안에서 `bisect_left` 를 쓴다 — 보통 리스트는 앞에서부터 훑는다

파이썬은 `5 in sl` 을 `sl.__contains__(5)` 로 바꿔 부른다.
`SortedList` 의 `__contains__` 는 `bisect_left` 로 자리를 찾고 그 자리 값을 확인하므로 O(log n) 에 답한다.
보통 리스트는 정렬되어 있다는 것을 모르므로 `in` 이 원소를 앞에서부터 하나씩 견준다.
`SortedList` 는 내부 리스트가 늘 정렬된다는 것(`add` 가 `insort` 를 쓴다)을 알기에 이진 탐색을 쓸 수 있다.
근거: 2-summary 「동작 방식 (7)」, 「구현 세부사항 대 언어 보장」.

## 실습 정답

### 실습 1. `bisect` 로 검색 · 개수 · 등급 · 정렬 컨테이너 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 3 · 4 의 두 경계와 `bisect(3)` 출력 | `bisect.bisect_left(sorted_list, 3)` 등 다섯 `print` 줄 |
| 2. `insort` 로 4 넣고 출력 | `bisect.insort(data, 4)` |
| 3. `insort_left` 로 4 한 번 더 | `bisect.insort_left(data, 4)` |
| 4. `bisect_left` 로 자리 찾기 | `binary_search` 의 `i = bisect.bisect_left(sorted_list, target)` |
| 5. 범위 · 값 확인 후 인덱스 또는 -1 | `if i < len(sorted_list) and sorted_list[i] == target: return i` / `return -1` |
| 6. 23 · 25 검색 출력 | `binary_search(nums, 23)` · `binary_search(nums, 25)` |
| 7. 두 경계의 차 | `count_value` 의 `left` · `right` · `return right - left` |
| 8. 2 · 4 · 6 개수 출력 | `count_value(data, 2)` 등 세 줄 |
| 9. 기본 분기점 · 등급 | `grade` 의 `breakpoints = [60, 70, 80, 90]` · `grades = 'FDCBA'` |
| 10. 자리 찾고 등급 문자 돌려주기 | `i = bisect.bisect(breakpoints, score)` · `return grades[i]` |
| 11. 점수마다 등급 출력 | `for score in scores:` 의 `print(f"  {score}점 -> {grade(score)}")` |
| 12. 빈 `data` 로 시작 | `SortedList.__init__` 의 `self.data = []` |
| 13. `insort` 로 넣기 | `add` 의 `bisect.insort(self.data, value)` |
| 14. 확인 후 `pop` | `remove` 의 `bisect_left` · `if ...: self.data.pop(i)` |
| 15. `in` 연산자 지원 | `__contains__` |
| 16. `SortedList([...])` 꼴 | `__repr__` |
| 17. 차례로 add · in · remove 출력 | `for v in [5, 2, 8, 1, 9, 3]:` 이하 |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-data-structures/reference/bisect.py`

```python
# [자료구조 & 알고리즘] bisect (이진 탐색 모듈)
# 설명: 정렬된 리스트에서 이진 탐색과 삽입 위치 결정. bisect_left/right, insort 활용
# 팁: bisect는 C로 구현되어 있어 순수 Python 이진 탐색보다 빠르다. bisect_left는 lower_bound, bisect_right는 upper_bound에 해당한다. insort는 O(log n) 탐색 + O(n) 삽입이므로, 삽입이 빈번하면 SortedContainers 라이브러리를 고려한다. 성적 등급 매기기 패턴은 공식 문서의 대표 예제이다.

# bisect 모듈: 정렬된 리스트에 대한 이진 탐색과 삽입 유틸 제공
import bisect

# === bisect_left / bisect_right ===
# 경계 함수 비교 섹션
print("=== bisect_left / bisect_right ===")
# 중복 원소가 있는 정렬 리스트
sorted_list = [1, 3, 3, 3, 5, 7, 9]
print("리스트:", sorted_list)

# bisect_left: 같은 값의 왼쪽(앞) 위치
# bisect_right: 같은 값의 오른쪽(뒤) 위치
# bisect_left(3): 3이 처음 등장하는 위치 (1)
print(f"bisect_left(3):  {bisect.bisect_left(sorted_list, 3)}")   # 1
# bisect_right(3): 3이 끝난 직후 위치 (4)
print(f"bisect_right(3): {bisect.bisect_right(sorted_list, 3)}")  # 4
# 없는 값(4)은 left/right 결과가 같음
print(f"bisect_left(4):  {bisect.bisect_left(sorted_list, 4)}")   # 4
print(f"bisect_right(4): {bisect.bisect_right(sorted_list, 4)}")  # 4

# bisect = bisect_right (별칭)
# bisect는 bisect_right의 별칭
print(f"bisect(3):       {bisect.bisect(sorted_list, 3)}")  # 4

# === insort: 정렬 유지하며 삽입 ===
# insort 섹션
print("\n=== insort ===")
# 정렬된 리스트
data = [1, 3, 5, 7, 9]
print("삽입 전:", data)
# insort: 정렬을 유지하며 삽입 (탐색 O(log n) + 삽입 O(n))
bisect.insort(data, 4)     # insort_right와 동일
print("insort(4):", data)   # [1, 3, 4, 5, 7, 9]
# 같은 값이 있을 때 왼쪽에 삽입
bisect.insort_left(data, 4)
print("insort_left(4):", data)  # [1, 3, 4, 4, 5, 7, 9]

# === 값 검색 (존재 여부) ===
# 검색 섹션
print("\n=== 이진 탐색으로 값 검색 ===")
# bisect를 활용한 표준 이진 탐색 패턴
def binary_search(sorted_list, target):
    """정렬된 리스트에서 target의 인덱스 반환 (없으면 -1)"""
    # bisect_left로 target이 들어갈 위치 찾기
    i = bisect.bisect_left(sorted_list, target)
    # 그 위치 값이 target과 일치하는지 확인
    if i < len(sorted_list) and sorted_list[i] == target:
        return i
    return -1

# 테스트 데이터
nums = [2, 5, 8, 12, 16, 23, 38, 56, 72, 91]
print("리스트:", nums)
print("23 검색:", binary_search(nums, 23))  # 5
print("25 검색:", binary_search(nums, 25))  # -1

# === 개수 세기 ===
# 개수 세기 섹션
print("\n=== 특정 값의 개수 ===")
# right - left = target의 개수 (O(log n))
def count_value(sorted_list, target):
    # 처음 등장 위치
    left = bisect.bisect_left(sorted_list, target)
    # 마지막 등장 직후 위치
    right = bisect.bisect_right(sorted_list, target)
    # 차이가 개수
    return right - left

# 중복 데이터에서 개수 세기
data = [1, 2, 2, 2, 3, 4, 4, 5]
print("리스트:", data)
print("2의 개수:", count_value(data, 2))  # 3
print("4의 개수:", count_value(data, 4))  # 2
print("6의 개수:", count_value(data, 6))  # 0

# === 성적 등급 매기기 ===
# 등급 매기기 섹션 (공식 문서 대표 예제)
print("\n=== 성적 등급 ===")
# 점수를 등급(A~F)으로 매핑
def grade(score, breakpoints=None, grades=None):
    # 기본 분기점: 60, 70, 80, 90
    if breakpoints is None:
        breakpoints = [60, 70, 80, 90]
    # 기본 등급: F < 60 < D < 70 < C < 80 < B < 90 <= A
    if grades is None:
        grades = 'FDCBA'
    # bisect로 분기점 인덱스를 찾고 그 인덱스의 등급 반환
    i = bisect.bisect(breakpoints, score)
    return grades[i]

# 여러 점수 테스트
scores = [33, 99, 77, 70, 89, 90, 100]
for score in scores:
    print(f"  {score}점 -> {grade(score)}")

# === 정렬된 리스트 유지하며 동적 삽입 ===
# 동적 정렬 리스트 섹션
print("\n=== 동적 정렬 리스트 ===")
# 정렬을 유지하는 컨테이너 클래스
class SortedList:
    # 빈 리스트로 초기화
    def __init__(self):
        self.data = []

    # 정렬 유지 삽입 (O(log n) 탐색 + O(n) 삽입)
    def add(self, value):
        bisect.insort(self.data, value)

    # 값 제거 (O(log n) 탐색 + O(n) 삭제)
    def remove(self, value):
        i = bisect.bisect_left(self.data, value)
        # 위치 검증 후 pop
        if i < len(self.data) and self.data[i] == value:
            self.data.pop(i)

    # 'in' 연산자 지원: 이진 탐색으로 O(log n)
    def __contains__(self, value):
        i = bisect.bisect_left(self.data, value)
        return i < len(self.data) and self.data[i] == value

    # 디버그용 표현
    def __repr__(self):
        return f"SortedList({self.data})"

# 사용 예시
sl = SortedList()
# 무작위 순서로 삽입해도 정렬 유지
for v in [5, 2, 8, 1, 9, 3]:
    sl.add(v)
    print(f"  add({v}): {sl}")
# in 연산자 사용
print(f"  5 in sl: {5 in sl}")   # True
print(f"  6 in sl: {6 in sl}")   # False
# 제거
sl.remove(5)
print(f"  remove(5): {sl}")

# 출력:
# === bisect_left / bisect_right ===
# bisect_left(3):  1
# bisect_right(3): 4
# bisect_left(4):  4
# bisect_right(4): 4
# === insort ===
# insort(4): [1, 3, 4, 5, 7, 9]
# === 이진 탐색으로 값 검색 ===
# 23 검색: 5
# 25 검색: -1
# === 특정 값의 개수 ===
# 2의 개수: 3
# === 성적 등급 ===
# 33점 -> F
# 99점 -> A
# 77점 -> C
```

**실행 결과** — 원본 예제(`component`)를 실제로 돌린 출력이다. 환경 `Python 3.12.3` · 2026-11-28 · exit 0 · 두 번 돌려 출력이 같았다.

````text
$ python3 -I example.py
=== bisect_left / bisect_right ===
리스트: [1, 3, 3, 3, 5, 7, 9]
bisect_left(3):  1
bisect_right(3): 4
bisect_left(4):  4
bisect_right(4): 4
bisect(3):       4

=== insort ===
삽입 전: [1, 3, 5, 7, 9]
insort(4): [1, 3, 4, 5, 7, 9]
insort_left(4): [1, 3, 4, 4, 5, 7, 9]

=== 이진 탐색으로 값 검색 ===
리스트: [2, 5, 8, 12, 16, 23, 38, 56, 72, 91]
23 검색: 5
25 검색: -1

=== 특정 값의 개수 ===
리스트: [1, 2, 2, 2, 3, 4, 4, 5]
2의 개수: 3
4의 개수: 2
6의 개수: 0

=== 성적 등급 ===
  33점 -> F
  99점 -> A
  77점 -> C
  70점 -> C
  89점 -> B
  90점 -> A
  100점 -> A

=== 동적 정렬 리스트 ===
  add(5): SortedList([5])
  add(2): SortedList([2, 5])
  add(8): SortedList([2, 5, 8])
  add(1): SortedList([1, 2, 5, 8])
  add(9): SortedList([1, 2, 5, 8, 9])
  add(3): SortedList([1, 2, 3, 5, 8, 9])
  5 in sl: True
  6 in sl: False
  remove(5): SortedList([1, 2, 3, 8, 9])
````

**풀이 요점**

- 1단계의 결과에서 「3 은 경계가 둘로 갈리고, 없는 4 는 하나로 겹친다」는 것이 뒤의 모든 패턴의 바탕이다.
- 검색은 `bisect_left` 자리에 대해 「범위 안인가 → 값이 같은가」를 그 순서로 확인한다 — 순서를 바꾸면 `IndexError` 가 날 수 있다.
- 개수는 이진 탐색 두 번의 차라 리스트를 훑지 않는다.
- 등급은 `bisect`(= `bisect_right`)라서 분기점과 같은 점수(70, 90)가 위 등급으로 간다.
- `SortedList` 는 `add` 가 정렬을 지켜 주기 때문에 `remove` 와 `__contains__` 가 이진 탐색을 믿고 쓸 수 있다.
- `remove` 는 값이 없으면 아무것도 하지 않는다 — 보통 리스트의 `remove` 와 달리 예외를 내지 않는다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 원본 예제를 `Python 3.12.3` 에서 2회 돌렸다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
