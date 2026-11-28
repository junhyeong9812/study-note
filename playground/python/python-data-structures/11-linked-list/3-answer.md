# python/python-data-structures/11 — 연결 리스트 (Linked List) — 정답

> 복습 때 이 파일은 **맨 마지막에만** 연다.\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈 정답

### 1. 0 이 맨 앞에 붙고, 3 이 빠진다

**출력**

```text
리스트: 1 -> 2 -> 3 -> 4 -> 5
prepend(0): 0 -> 1 -> 2 -> 3 -> 4 -> 5
delete(3): 0 -> 1 -> 2 -> 4 -> 5
```

**왜 그런가**

`prepend(0)` 은 옛 `head`(값 1)를 뒤에 단 새 노드를 `head` 로 삼는다.
`delete(3)` 은 `head` 가 대상이 아니므로 직전 노드(값 2)에서 멈추고, 그 `next` 가 값 3 노드를 건너뛰어 값 4 노드를 가리키게 한다.
근거: 2-summary 「동작 방식 (1)」.

### 2. 3 — 가운데 둘 중 뒤쪽

**출력**

```text
리스트: 1->2->3->4
중간 노드: 3
```

**왜 그런가**

1회에 `slow` 는 2, `fast` 는 3 으로 간다.
`fast.next` 가 4 로 있으므로 2회에 `slow` 는 3, `fast` 는 4 의 다음인 `None` 이 된다.
`fast` 가 `None` 이라 반복이 끝나고, 가운데 둘(2·3) 중 뒤쪽인 3 이 반환된다.
근거: 2-summary 「동작 방식 (3)」.

### 3. 새 head 는 `3 -> 2 -> 1`, 원래 `head` 는 `1` 만 찍는다

**예상** (실행하지 않음 — 코드를 읽어 추론한 것이다)

```text
3 -> 2 -> 1
1
```

**왜 그런가**

`reverse_list` 는 새 노드를 만들지 않고 `next` 만 뒤집는다.
반환된 `prev` 는 원래 마지막 노드(값 3)라서 거기서부터 `3 -> 2 -> 1` 이다.
`head` 변수는 여전히 값 1 노드를 가리키는데, 이 노드는 첫 바퀴에서 `curr.next = prev`(`None`)가 되어 꼬리가 되었다.
그래서 `__repr__` 은 `1` 하나만 모은다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 2」.

### 4. 크기는 6 — sentinel 은 세지 않는다

**출력**

```text
크기: 6
```

**왜 그런가**

`append` 다섯 번과 `prepend` 한 번이 각각 `size` 를 1 늘려 6 이다.
sentinel 두 개는 생성자에서 만들어지지만 `size` 는 0 에서 시작하고, `size` 를 바꾸는 곳은 `append` · `prepend` · `remove` 뿐이라 sentinel 은 수에 들지 않는다.
근거: 2-summary 「동작 방식 (6)」.

### 5. 나머지 노드로 가는 유일한 길을 잃는다

`curr.next` 는 `curr` 뒤의 노드들로 가는 유일한 참조다.
`curr.next = prev` 를 먼저 하면 그 참조가 덮여, 다음 바퀴에서 `curr` 를 어디로 옮길지 알 수 없다.
그래서 「다음을 기억 → 뒤집기 → 한 칸 전진」 차례가 지켜져야 한다.
근거: 2-summary 「동작 방식 (2)」 · 「어디서 틀리나 2」.

### 6. head 에서 시작점까지의 거리와 만난 점에서 시작점까지의 거리가 고리 단위로 같기 때문이다

만날 때까지 `slow` 는 a+b 걸음, `fast` 는 그 두 배인 2(a+b) 걸음을 갔다.
`fast` 가 더 걸은 a+b 는 고리를 k 바퀴 돈 거리이므로 a+b = k·c 이다.
따라서 a = k·c − b 이다.
`head` 에서 a 걸음 가면 시작점이고, 만난 점(시작점에서 b 지점)에서 a 걸음 가면 k 바퀴에서 b 를 뺀 자리, 곧 시작점이다.
둘이 한 칸씩 같은 속도로 가므로 시작점에서 처음 겹친다.
예제에서는 a = 2, b = 1, c = 3 이고 4 에서 만난 뒤 (2, 5) → (3, 3) 으로 3 에서 만난다.
근거: 2-summary 「동작 방식 (5)」.

### 7. 끝나지 않는다

`ListNode.__repr__` 은 `while node:` 로 `None` 을 만날 때까지 걷는다.
사이클이 있으면 3 → 4 → 5 → 3 … 을 끝없이 돌며 `None` 에 닿지 않으므로, 함수가 돌아오지 않고 문자열 목록만 계속 커진다.
그래서 예제는 사이클 리스트에 대해 `has_cycle` 결과와 `.val` 만 찍는다.
근거: 2-summary 「어디서 틀리나 5」.

### 8. 사이클이 없어도 값이 겹치는 리스트에서 틀린다

`is` 는 같은 노드인지를 보지만, `.val` 비교는 값만 본다.
사이클이 없는 리스트라도 서로 다른 두 노드가 같은 값을 갖고, 어떤 바퀴에서 `slow` 와 `fast` 가 마침 그 두 노드에 서면 `True` 를 돌려준다.
근거: 2-summary 「동작 방식 (4)」 · 「어디서 틀리나 4」.

### 9. sentinel 덕분에 실제 노드의 앞뒤가 언제나 노드이기 때문이다

`SinglyLinkedList.delete` 는 빈 리스트와 `head` 가 대상인 경우를 따로 다룬다. 첫 노드에는 「앞 노드」가 없고 `head` 변수를 직접 바꿔야 하기 때문이다.
`DoublyLinkedList` 는 빈 리스트에도 sentinel `head` · `tail` 이 있어서, 실제 노드는 늘 앞에 노드, 뒤에 노드를 둔다.
그래서 맨 앞 노드를 빼든 가운데 노드를 빼든 `node.prev.next = node.next`, `node.next.prev = node.prev` 두 줄로 같다.
근거: 2-summary 「동작 방식 (1)」 · 「동작 방식 (6)」 · 「어디서 틀리나 7」.

### 10. 동적 배열은 맨 앞 삽입에서 뒤 원소를 밀지만, 연결 리스트는 참조 두 개만 바꾼다

동적 배열은 원소를 연속된 칸에 두므로 맨 앞에 넣으면 뒤 원소를 한 칸씩 밀어야 한다.
연결 리스트의 `prepend` 는 새 노드의 `next` 를 옛 `head` 로, `head` 를 새 노드로 바꾸면 끝나는 O(1) 이다.
그런데도 직접 쓸 일이 적은 까닭은, 파이썬 `list` 가 번호로 바로 접근하는 동적 배열이라 대부분의 일에 충분하고, 연결 리스트는 k 번째 원소를 보려면 k 칸을 걸어야 하기 때문이다.
그래서 연결 리스트는 주로 코딩 테스트의 포인터 조작 문제로 만난다.
근거: 2-summary 「어디서 틀리나 1」 · 「언제 쓰고 언제 안 쓰나」.

## 실습 정답

### 실습 1. 연결 리스트 다섯 가지 연산 만들기

**요구 조건 → 정답 코드의 자리**

| 요구 조건 | 정답 코드 |
|---|---|
| 1. 노드에 값 · 다음 저장 | `ListNode.__init__` 의 `self.val` · `self.next` |
| 2. ` -> ` 로 이은 표현 | `ListNode.__repr__` 의 `while node:` 와 `' -> '.join(result)` |
| 3. 빈 리스트로 시작 | `SinglyLinkedList.__init__` 의 `self.head = None` |
| 4. 끝에 붙이기 | `append` 의 `if not self.head:` 와 `while curr.next:` |
| 5. 맨 앞에 넣기 | `prepend` 의 `self.head = ListNode(val, self.head)` |
| 6. 첫 일치 하나 지우기 | `delete` 의 세 갈래와 `curr.next = curr.next.next` |
| 7. 리스트 표현 | `SinglyLinkedList.__repr__` 의 `'Empty'` 갈래 |
| 8. 단일 리스트 사용 예시 | `ll` 을 만든 뒤 `print("리스트:" …)` 부터 `print("delete(3):" …)` |
| 9. 세 포인터 역전 | `reverse_list` 의 `next_node` · `curr.next = prev` · `return prev` |
| 10. 원본과 역전 출력 | `print("원본:" …)` · `print("역전:" …)` |
| 11. 중간 노드 | `find_middle` 의 `while fast and fast.next:` |
| 12. 홀수 · 짝수 리스트 | `head` · `head2` 와 두 `print("중간 노드:" …)` |
| 13. 사이클 감지 | `has_cycle` 의 `if slow is fast: return True` |
| 14. 시작점 찾기 | `find_cycle_start` 의 `slow = head` 와 안쪽 `while slow is not fast:` |
| 15. 사이클 · 무사이클 예시 | `n5.next = n3` 줄과 `no_cycle` |
| 16. 이중 노드 | `DoublyNode.__init__` |
| 17. sentinel 과 크기 | `DoublyLinkedList.__init__` 의 `self.head.next = self.tail` · `self.tail.prev = self.head` · `self.size = 0` |
| 18. 양 끝 삽입 | `append` 의 `prev_node = self.tail.prev`, `prepend` 의 `next_node = self.head.next` |
| 19. O(1) 제거 | `remove` 의 `node.prev.next = node.next` · `node.next.prev = node.prev` |
| 20. sentinel 뺀 표현 | `DoublyLinkedList.__repr__` 의 `while curr != self.tail:` |
| 21. 이중 리스트 사용 예시 | `dll` 을 만든 뒤 세 `print` |

**정답 코드** — study-practice 의 줄 단위 주석판이다(코드 동작은 원본 예제와 같다).

`python/python-data-structures/reference/linked-list.py`

```python
# [자료구조 & 알고리즘] 연결 리스트 (Linked List)
# 설명: 단일/이중 연결 리스트 구현, 역전, 중간 노드 찾기, 사이클 감지
# 팁: Python 리스트가 동적 배열이라 연결 리스트를 직접 쓸 일은 적지만, 코딩 테스트에서 자주 출제된다. 역전은 prev/curr/next 세 포인터로 구현한다. 중간 노드와 사이클 감지는 Floyd의 토끼와 거북이 알고리즘이다. 이중 연결 리스트는 sentinel 노드를 쓰면 경계 조건 처리가 깔끔하다.

# === 단일 연결 리스트 ===
# 단일 연결 리스트: 각 노드가 다음 노드만 가리킨다. 삽입/삭제 O(1)(노드 참조 시), 탐색 O(n).
print("=== 단일 연결 리스트 ===")
# 노드 클래스: 값 + 다음 포인터
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

    # 디버깅용: 1 -> 2 -> 3 형태로 출력
    def __repr__(self):
        result = []
        node = self
        while node:
            result.append(str(node.val))
            node = node.next
        return ' -> '.join(result)

# 단일 연결 리스트 자료구조
class SinglyLinkedList:
    def __init__(self):
        self.head = None

    # append: 끝에 추가. 끝까지 순회하므로 O(n).
    def append(self, val):
        if not self.head:
            self.head = ListNode(val)
            return
        curr = self.head
        while curr.next:
            curr = curr.next
        curr.next = ListNode(val)

    # prepend: 앞에 추가. O(1).
    def prepend(self, val):
        self.head = ListNode(val, self.head)

    # delete: 값 일치 노드 제거. 최악 O(n).
    def delete(self, val):
        if not self.head:
            return
        # 헤드가 대상이면 헤드 갱신
        if self.head.val == val:
            self.head = self.head.next
            return
        # 그 외엔 직전 노드의 next를 건너뛰게 변경
        curr = self.head
        while curr.next:
            if curr.next.val == val:
                curr.next = curr.next.next
                return
            curr = curr.next

    def __repr__(self):
        return repr(self.head) if self.head else 'Empty'

# 사용 예시
ll = SinglyLinkedList()
for v in [1, 2, 3, 4, 5]:
    ll.append(v)
print("리스트:", ll)  # 1 -> 2 -> 3 -> 4 -> 5
ll.prepend(0)
print("prepend(0):", ll)  # 0 -> 1 -> 2 -> 3 -> 4 -> 5
ll.delete(3)
print("delete(3):", ll)  # 0 -> 1 -> 2 -> 4 -> 5

# === 연결 리스트 역전 ===
# prev/curr/next 세 포인터로 한 번 순회하며 방향 뒤집기. 시간 O(n), 공간 O(1).
print("\n=== 연결 리스트 역전 ===")
def reverse_list(head):
    prev = None
    curr = head
    while curr:
        # 다음 노드 임시 저장 (링크를 끊기 전에)
        next_node = curr.next
        # 현재 노드의 다음을 prev로 뒤집음
        curr.next = prev
        # prev/curr 한 칸씩 진행
        prev = curr
        curr = next_node
    # 마지막의 prev가 새 head
    return prev

# 1 -> 2 -> 3 -> 4 -> 5 만들기
head = ListNode(1, ListNode(2, ListNode(3, ListNode(4, ListNode(5)))))
print("원본:", head)  # 1 -> 2 -> 3 -> 4 -> 5
reversed_head = reverse_list(head)
print("역전:", reversed_head)  # 5 -> 4 -> 3 -> 2 -> 1

# === 중간 노드 찾기 (토끼와 거북이) ===
# slow는 1칸, fast는 2칸씩 이동. fast가 끝나면 slow는 정확히 중앙. O(n).
print("\n=== 중간 노드 (slow/fast pointer) ===")
def find_middle(head):
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
    return slow

head = ListNode(1, ListNode(2, ListNode(3, ListNode(4, ListNode(5)))))
print("리스트: 1->2->3->4->5")
print("중간 노드:", find_middle(head).val)  # 3

head2 = ListNode(1, ListNode(2, ListNode(3, ListNode(4))))
print("리스트: 1->2->3->4")
print("중간 노드:", find_middle(head2).val)  # 3 (짝수면 뒤쪽 중간)

# === 사이클 감지 ===
# Floyd의 사이클 감지: 사이클이 있으면 fast가 결국 slow를 따라잡는다. O(n) 시간, O(1) 공간.
print("\n=== 사이클 감지 ===")
def has_cycle(head):
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        # 같은 노드(객체)에서 만나면 사이클 존재
        if slow is fast:
            return True
    return False

# 사이클 시작점 찾기: 만난 후 slow를 head로 옮기고 같은 속도로 진행하면 시작점에서 만난다 (수학적 증명 존재).
def find_cycle_start(head):
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow is fast:
            # 만남 -> slow를 head로 리셋 후 같은 속도로 이동
            slow = head
            while slow is not fast:
                slow = slow.next
                fast = fast.next
            return slow
    return None

# 사이클 있는 리스트: 1->2->3->4->5->3(사이클)
n1 = ListNode(1)
n2 = ListNode(2)
n3 = ListNode(3)
n4 = ListNode(4)
n5 = ListNode(5)
n1.next = n2; n2.next = n3; n3.next = n4; n4.next = n5; n5.next = n3
print("사이클 존재:", has_cycle(n1))  # True
print("사이클 시작:", find_cycle_start(n1).val)  # 3

# 사이클 없는 리스트
no_cycle = ListNode(1, ListNode(2, ListNode(3)))
print("사이클 없음:", has_cycle(no_cycle))  # False

# === 이중 연결 리스트 ===
# 이중 연결: prev/next 양방향 포인터. sentinel 노드(더미 head/tail)로 경계 조건 단순화.
print("\n=== 이중 연결 리스트 ===")
# 이중 노드: 값 + 양방향 포인터
class DoublyNode:
    def __init__(self, val=0):
        self.val = val
        self.prev = None
        self.next = None

class DoublyLinkedList:
    def __init__(self):
        # sentinel 노드: 실제 데이터가 아닌 경계용. None 검사 제거.
        self.head = DoublyNode(0)  # sentinel head
        self.tail = DoublyNode(0)  # sentinel tail
        self.head.next = self.tail
        self.tail.prev = self.head
        self.size = 0

    # append: tail 직전에 삽입. O(1).
    def append(self, val):
        node = DoublyNode(val)
        prev_node = self.tail.prev
        # 새 노드를 prev_node와 tail 사이에 끼워넣음
        prev_node.next = node
        node.prev = prev_node
        node.next = self.tail
        self.tail.prev = node
        self.size += 1

    # prepend: head 직후에 삽입. O(1).
    def prepend(self, val):
        node = DoublyNode(val)
        next_node = self.head.next
        self.head.next = node
        node.prev = self.head
        node.next = next_node
        next_node.prev = node
        self.size += 1

    # remove: 노드 참조만 있으면 O(1)에 제거 (단일 연결 리스트와의 핵심 차이)
    def remove(self, node):
        node.prev.next = node.next
        node.next.prev = node.prev
        self.size -= 1

    # 디버깅 출력 (sentinel 제외)
    def __repr__(self):
        result = []
        curr = self.head.next
        while curr != self.tail:
            result.append(str(curr.val))
            curr = curr.next
        return ' <-> '.join(result) if result else 'Empty'

dll = DoublyLinkedList()
for v in [1, 2, 3, 4, 5]:
    dll.append(v)
print("리스트:", dll)  # 1 <-> 2 <-> 3 <-> 4 <-> 5
dll.prepend(0)
print("prepend(0):", dll)  # 0 <-> 1 <-> 2 <-> 3 <-> 4 <-> 5
print(f"크기: {dll.size}")

# 출력:
# === 단일 연결 리스트 ===
# 리스트: 1 -> 2 -> 3 -> 4 -> 5
# === 연결 리스트 역전 ===
# 역전: 5 -> 4 -> 3 -> 2 -> 1
# === 중간 노드 ===
# 중간 노드: 3
# === 사이클 감지 ===
# 사이클 존재: True
# 사이클 시작: 3
# === 이중 연결 리스트 ===
# 리스트: 1 <-> 2 <-> 3 <-> 4 <-> 5
```

**실행 결과** — 원본 예제(`component`)를 실제로 돌린 출력이다. 환경 `Python 3.12.3` · 2026-11-28 · exit 0 · 두 번 돌려 출력이 같았다.

````text
$ python3 -I example.py
=== 단일 연결 리스트 ===
리스트: 1 -> 2 -> 3 -> 4 -> 5
prepend(0): 0 -> 1 -> 2 -> 3 -> 4 -> 5
delete(3): 0 -> 1 -> 2 -> 4 -> 5

=== 연결 리스트 역전 ===
원본: 1 -> 2 -> 3 -> 4 -> 5
역전: 5 -> 4 -> 3 -> 2 -> 1

=== 중간 노드 (slow/fast pointer) ===
리스트: 1->2->3->4->5
중간 노드: 3
리스트: 1->2->3->4
중간 노드: 3

=== 사이클 감지 ===
사이클 존재: True
사이클 시작: 3
사이클 없음: False

=== 이중 연결 리스트 ===
리스트: 1 <-> 2 <-> 3 <-> 4 <-> 5
prepend(0): 0 <-> 1 <-> 2 <-> 3 <-> 4 <-> 5
크기: 6
````

**풀이 요점**

- 단일 연결의 `delete` 는 대상의 한 칸 앞에서 멈춰야 한다 — 노드가 자기 앞을 모르기 때문이다.
- 역전은 「다음을 기억 → 뒤집기 → 전진」 차례가 전부이고, 반환값이 새 `head` 다.
- `find_middle` · `has_cycle` · `find_cycle_start` 는 같은 `slow` / `fast` 골격을 공유한다. 조건 `fast and fast.next` 의 순서가 오류를 막는다.
- 만남 판정은 `is` 다 — 값이 아니라 노드가 같아야 한다.
- 이중 연결은 sentinel 덕분에 `append` · `prepend` · `remove` 에 경계 검사가 하나도 없다.
- 사이클 리스트는 `print` 하지 않는다 — `__repr__` 이 끝나지 않는다.

## 실행 검증

| 무엇을 | 결과 |
|---|---|
| 예제 실행 | 원본 예제를 `Python 3.12.3` 에서 2회 돌렸다 |
| 퀴즈 · 정리 · 실습의 서술 | `claude-opus-5-5` 가 원본 재료에서 쓴 것 — **사람 검수 전** |
| 다시 볼 것 | 언어 · 라이브러리 버전이 바뀌면 「예제 실행」 |
