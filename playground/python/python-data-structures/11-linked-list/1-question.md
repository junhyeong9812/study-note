# python/python-data-structures/11 — 연결 리스트 (Linked List) — 질문

> 맨기억으로 먼저 답한다. 막히면 [2-summary.md](2-summary.md), 그래도 막히면 [3-answer.md](3-answer.md).\
> 집필 — `claude-opus-5-5` 가 원본 재료를 뼈대로 쓴 **검수 전 초안**이다(2026-11-28).

## 퀴즈

### 1. 1~5 를 넣은 단일 리스트에 앞 삽입과 삭제를 차례로 하면 (예측)

- `SinglyLinkedList` 에 1, 2, 3, 4, 5 를 차례로 `append` 한 뒤 `prepend(0)` 과 `delete(3)` 을 하면, 두 연산 뒤의 `print` 는 각각 무엇을 찍나?

### 2. 노드가 넷인 리스트의 중간 (예측)

```python
# 질문용 발췌
head2 = ListNode(1, ListNode(2, ListNode(3, ListNode(4))))
print("리스트: 1->2->3->4")
print("중간 노드:", find_middle(head2).val)
```

- 두 줄의 출력은 무엇이고, 찍힌 값은 가운데 둘 중 어느 쪽인가?

### 3. 뒤집은 뒤 원래 `head` 변수를 찍으면 (예측)

```python
# 질문용 발췌
head = ListNode(1, ListNode(2, ListNode(3)))
new_head = reverse_list(head)
print(new_head)
print(head)
```

- 두 `print` 는 각각 무엇을 찍나?

### 4. 이중 리스트에 다섯 번 붙이고 한 번 앞에 넣은 뒤의 크기 (예측)

- `DoublyLinkedList` 에 1~5 를 `append` 하고 `prepend(0)` 한 뒤 `print(f"크기: {dll.size}")` 는 무엇을 찍나?
- 그 수에 sentinel 두 개는 들어가나?

### 5. 역전에서 `next_node = curr.next` 를 가장 먼저 쓰는 까닭 (왜)

- `curr.next = prev` 를 먼저 쓰면 무엇을 잃게 되나?

### 6. 만난 뒤 `slow` 를 `head` 로 돌려 한 칸씩 걸으면 시작점에서 만나는 까닭 (왜)

- head 에서 시작점까지의 거리 a, 시작점에서 만난 점까지 b, 고리 길이 c 로 놓으면 왜 둘이 시작점에서 만나나?

### 7. 사이클이 있는 `n1` 을 그대로 `print` 하면 (경계)

- `1→2→3→4→5→3` 으로 이은 `n1` 에 `print(n1)` 을 하면 `ListNode.__repr__` 은 어떻게 되나?

### 8. 만남 판정을 `slow.val == fast.val` 로 바꾸면 (경계)

- 이 바꿈은 어떤 리스트에서 틀린 답을 내나?

### 9. sentinel 과 단일 리스트의 `head` 특수 처리 (연결)

- `SinglyLinkedList.delete` 가 따로 다루는 경우들을 `DoublyLinkedList` 는 왜 따로 다루지 않아도 되나?

### 10. 파이썬 `list` 의 맨 앞 삽입과 `prepend` (연결)

- 맨 앞에 값을 자주 넣을 때 동적 배열과 연결 리스트는 왜 비용이 다르고, 그런데도 연결 리스트를 직접 쓸 일이 적은 까닭은 무엇인가?

## 실습

### 실습 1. 연결 리스트 다섯 가지 연산 만들기

**만들 것** — 단일 연결 리스트, 역전, 중간 노드 찾기, 사이클 감지 · 시작점 찾기, sentinel 을 쓴 이중 연결 리스트를 한 파일에 만들고 사용 예시를 찍는다.

**요구 조건**

1단계 — 단일 연결 리스트

1. `ListNode` 는 `val`(기본 0)과 `next`(기본 `None`)를 받아 저장한다.
2. `ListNode.__repr__` 은 자기부터 끝까지 값을 `' -> '` 로 이은 문자열을 돌려준다.
3. `SinglyLinkedList` 는 `head` 를 `None` 으로 시작한다.
4. `append(val)` 은 비었으면 새 노드를 `head` 로 두고, 아니면 마지막 노드까지 걸어가 뒤에 붙인다.
5. `prepend(val)` 은 새 노드를 맨 앞에 두고 `head` 로 삼는다.
6. `delete(val)` 은 빈 리스트면 아무것도 안 하고, `head` 가 대상이면 `head` 를 옮기고, 그 밖에는 직전 노드의 `next` 가 대상을 건너뛰게 해 첫 일치 하나만 지운다.
7. `SinglyLinkedList.__repr__` 은 비었으면 `'Empty'`, 아니면 `head` 의 표현을 돌려준다.
8. 1~5 를 붙인 뒤, `prepend(0)` 뒤, `delete(3)` 뒤의 리스트를 찍는다.

2단계 — 역전

9. `reverse_list(head)` 는 `prev` · `curr` · `next_node` 로 한 번 훑으며 방향을 뒤집고 새 `head` 를 돌려준다.
10. 1→2→3→4→5 를 만들어 원본과 역전 결과를 찍는다.

3단계 — 중간 노드

11. `find_middle(head)` 는 `slow` 를 한 칸, `fast` 를 두 칸씩 움직여 `fast` 가 끝에 닿을 때의 `slow` 를 돌려준다.
12. 노드 다섯 개, 넷인 리스트에 대해 중간 노드의 값을 찍는다.

4단계 — 사이클

13. `has_cycle(head)` 는 두 포인터가 같은 객체에서 만나면 `True`, `fast` 가 끝에 닿으면 `False` 를 돌려준다.
14. `find_cycle_start(head)` 는 만난 뒤 `slow` 를 `head` 로 되돌리고 둘을 한 칸씩 움직여 다시 만나는 노드를 돌려준다. 사이클이 없으면 `None`.
15. `1→2→3→4→5→3` 리스트로 사이클 존재와 시작점의 값을, `1→2→3` 리스트로 사이클 없음을 찍는다.

5단계 — 이중 연결 리스트

16. `DoublyNode` 는 `val`(기본 0)과 `None` 인 `prev` · `next` 를 갖는다.
17. `DoublyLinkedList` 는 sentinel `head` · `tail` 을 만들어 서로 잇고 `size` 를 0 으로 둔다.
18. `append` 는 `tail` 직전에, `prepend` 는 `head` 직후에 노드를 끼우고 `size` 를 1 늘린다.
19. `remove(node)` 는 앞뒤 노드를 서로 잇고 `size` 를 1 줄인다.
20. `__repr__` 은 sentinel 을 빼고 값을 `' <-> '` 로 잇고, 비었으면 `'Empty'` 를 돌려준다.
21. 1~5 를 붙인 뒤, `prepend(0)` 뒤의 리스트와 크기를 찍는다.

**시작 코드**

```python
# 연결 리스트 연습 파일 — TODO 자리를 채운다

print("=== 단일 연결 리스트 ===")
class ListNode:
    def __init__(self, val=0, next=None):
        # TODO: 값과 다음 노드 참조를 저장한다
        pass

    def __repr__(self):
        # TODO: 이 노드부터 끝까지 값을 ' -> ' 로 이어 돌려준다
        pass

class SinglyLinkedList:
    def __init__(self):
        self.head = None

    def append(self, val):
        # TODO: 비었으면 head 로, 아니면 끝까지 걸어가 붙인다
        pass

    def prepend(self, val):
        # TODO: 맨 앞에 넣는다
        pass

    def delete(self, val):
        # TODO: 빈 리스트 · head 가 대상 · 그 밖의 경우
        pass

    def __repr__(self):
        # TODO: 비었으면 'Empty'
        pass

ll = SinglyLinkedList()
for v in [1, 2, 3, 4, 5]:
    ll.append(v)
print("리스트:", ll)
ll.prepend(0)
print("prepend(0):", ll)
ll.delete(3)
print("delete(3):", ll)

print("\n=== 연결 리스트 역전 ===")
def reverse_list(head):
    # TODO: prev / curr / next_node 세 포인터
    pass

head = ListNode(1, ListNode(2, ListNode(3, ListNode(4, ListNode(5)))))
print("원본:", head)
reversed_head = reverse_list(head)
print("역전:", reversed_head)

print("\n=== 중간 노드 (slow/fast pointer) ===")
def find_middle(head):
    # TODO: slow 는 한 칸, fast 는 두 칸
    pass

head = ListNode(1, ListNode(2, ListNode(3, ListNode(4, ListNode(5)))))
print("리스트: 1->2->3->4->5")
print("중간 노드:", find_middle(head).val)

head2 = ListNode(1, ListNode(2, ListNode(3, ListNode(4))))
print("리스트: 1->2->3->4")
print("중간 노드:", find_middle(head2).val)

print("\n=== 사이클 감지 ===")
def has_cycle(head):
    # TODO: 같은 객체에서 만나면 True
    pass

def find_cycle_start(head):
    # TODO: 만난 뒤 slow 를 head 로 되돌리고 같은 속도로
    pass

n1 = ListNode(1)
n2 = ListNode(2)
n3 = ListNode(3)
n4 = ListNode(4)
n5 = ListNode(5)
# TODO: n1→n2→n3→n4→n5→n3 으로 잇는다
print("사이클 존재:", has_cycle(n1))
print("사이클 시작:", find_cycle_start(n1).val)

no_cycle = ListNode(1, ListNode(2, ListNode(3)))
print("사이클 없음:", has_cycle(no_cycle))

print("\n=== 이중 연결 리스트 ===")
class DoublyNode:
    def __init__(self, val=0):
        # TODO: 값과 prev / next
        pass

class DoublyLinkedList:
    def __init__(self):
        # TODO: sentinel head · tail 을 만들어 잇고 size 를 0 으로
        pass

    def append(self, val):
        # TODO: tail 직전에 끼운다
        pass

    def prepend(self, val):
        # TODO: head 직후에 끼운다
        pass

    def remove(self, node):
        # TODO: 앞뒤를 서로 잇는다
        pass

    def __repr__(self):
        # TODO: sentinel 을 빼고 ' <-> ' 로 잇는다
        pass

dll = DoublyLinkedList()
for v in [1, 2, 3, 4, 5]:
    dll.append(v)
print("리스트:", dll)
dll.prepend(0)
print("prepend(0):", dll)
print(f"크기: {dll.size}")
```

**확인 방법** — `python linked-list.py` 로 돌려, 출력이 실습 정답의 실행 결과와 줄마다 같은지 본다. 사이클 절에서 프로그램이 멈추지 않고 끝까지 가는지도 본다.

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
