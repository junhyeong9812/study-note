# data-structure/01-data-structures-basics — 자료구조 개관: 연산 비용을 보고 구조를 고른다 — 정리 (힌트)

## 해결하는 문제

데이터를 "어딘가에 담는" 방법은 여러 가지다. 담는 방법에 따라 같은 일의 비용이 달라진다.

```text
  같은 일: "맨 앞 손님을 꺼낸다" (n명 대기)

  배열에 줄 세우기            [A][B][C][D][E] ... → A를 꺼내면 B..끝을 한 칸씩 당긴다 = n번 이동
  연결된 줄(앞 사람만 가리킴)  A → B → C → D → ... → 머리 표시만 B로 옮긴다       = 1번
```

- 이 차이를 모르고 고르면 데이터가 작을 때는 티가 안 나고, 커지면 갑자기 느려진다.
  - *자료구조(data structure)*: 데이터를 담는 배치와, 그 위에서 삽입·검색·삭제를 하는 방법을 함께 묶은 것.

쉬운 예: 은행 번호표 대기열이다.
- 번호표 기계는 "다음 번호"만 부른다. 앞사람이 빠질 때 나머지가 의자를 옮기지 않는다.
- 만약 의자를 한 칸씩 옮겨야 한다면, 대기 인원이 늘수록 한 명 부를 때마다 드는 수고가 커진다.

똑같은 구조다.\
원본 노트 §5의 `Queue`는 파이썬 `list.pop(0)`으로 꺼낸다. 이것이 "의자를 한 칸씩 옮기는" 큐다.

실무 예:
- 작업 대기열을 `list.pop(0)`(파이썬)이나 `ArrayList.remove(0)`(Java)로 만들었다. 테스트 큐 길이 100에서는 문제없다가, 운영에서 수만 건이 쌓이자 소비자가 밀린다.
- 정렬된 순서로 들어오는 키(자동 증가 ID, 시각)를 균형 잡히지 않은 이진 탐색 트리에 넣었다. 트리가 한 줄로 늘어져 검색이 선형 탐색이 된다.
- 원소 100만 개를 `LinkedList<Integer>`에 담았다. 같은 개수의 `ArrayList`보다 컨테이너 메모리가 약 5배 든다(아래 실험).

이 노트는 원본 [foundations/data-structures-basics](../../foundations/data-structures-basics/README.md)(부트캠프 ch11~13 따라 친 원고)를 이어받는다. 원본이 이미 설명한 정의·코드는 링크와 한두 줄 요약만 두고, 원본에 없는 **비용 관점·장애·실험**을 채운다.

## 동작·원리

### 1. 메모리 배치 두 가지 — 연속 vs 노드 연결

```text
  (가) 연속 배치 — 배열, ArrayList, Python list
  주소  0x1000 0x1004 0x1008 0x100C 0x1010
       +------+------+------+------+------+
       |  10  |  20  |  30  |  40  |  50  |      i번째 주소 = 시작 + i × 칸 크기  → 바로 계산
       +------+------+------+------+------+

  (나) 노드 연결 — 연결 리스트, 트리
  0x3000 [10|next]──┐
                    ▼
  0x7A00          [20|next]──┐
                             ▼
  0x5F00                   [30|null]           i번째 = head에서 next를 i번 따라간다
```

- (가)는 "i번째"를 주소 계산 한 번으로 찾는다. 대신 중간에 끼우거나 빼면 뒤 칸을 전부 민다.
- (나)는 끼우고 빼는 자리의 노드를 이미 쥐고 있으면 포인터 두세 개만 바꾼다. 대신 "i번째"를 찾으려면 i번 따라가야 한다.
  - *노드(node)*: 데이터 + 다른 노드를 가리키는 참조를 묶은 작은 상자.
  - *참조(reference) / 포인터(pointer)*: 다른 상자가 있는 위치를 담은 값.
- 기초는 원본 §1(배열·연결 리스트 그림, 스택/힙 세그먼트 연계)과 §3(연결 리스트 코드)에 있다.
  - 원본 §1의 결론("핵심 차이는 스택이냐 힙이냐가 아니라 한 블록 연속 할당 vs 노드마다 개별 할당")이 맞는 요지다. Java·Python에서는 배열도 힙에 있다.

### 2. 세 가지 질문 → 연산 비용 표

원본 §1은 "삽입·검색·삭제를 어떻게 하는가" 세 질문을 던진다. 여기에 **"그 연산이 n에 따라 얼마나 비싸지나"** 를 붙이면 구조 선택표가 된다.

```text
                       위치로 읽기   값으로 찾기   맨 뒤 추가        맨 앞 삭제   (바로 앞 노드를 쥔 채) 중간 삽입·삭제
  배열/동적 배열         O(1)         O(n)        분할상환 O(1)      O(n)        O(n)  ← 뒤를 민다
  단일 연결 리스트       O(n)         O(n)        O(1) (tail 보유)   O(1)        O(1)  ← 단, 그 자리를 찾는 데 O(n)
  스택(동적 배열 위)     top만        —           push O(1) 분할상환  —           —
  큐(원형 배열·deque)    앞·뒤만      —           O(1)               O(1)        —
  이진 탐색 트리(BST)    —            O(h)        insert O(h)        —           delete O(h)
                                                  h = 높이: 균형이면 약 log₂n, 한 줄로 늘어지면 n
```

- *O(n)*: 원소 수 n에 비례해 커지는 비용. 자세한 정의는 [algorithm/02-asymptotic-analysis](../../algorithm/02-asymptotic-analysis/2-summary.md).
- *분할상환(amortized) O(1)*: 가끔 비싼 일(배열 전체 복사)이 있지만, 연산 n번의 총비용이 O(n)이라 한 번당 평균이 상수라는 뜻. [01-dynamic-array](../01-dynamic-array/2-summary.md) 참조.
    - 흔한 오해: "평균적으로 빠르다(운이 좋으면 빠르다)"가 아니다. 입력이 무엇이든 n번 합계가 O(n)이라는 보장이다(CLRS 17장).
- 표의 근거
  - 동적 배열·연결 리스트: Java 21 Javadoc(`ArrayList`: get/set/size 상수 시간, add 분할상환 상수 시간, 나머지 대략 선형 / `LinkedList`: 인덱스 연산은 가까운 끝에서부터 순회) — 다음 편 [02-adt-and-cost-contracts](../02-adt-and-cost-contracts/2-summary.md)에서 원문과 측정으로 다룬다.
  - Python list: python.org 위키 TimeComplexity — append·pop(끝) 분할상환 O(1), 중간 pop·insert O(n), 양 끝 연산이 잦으면 `collections.deque`를 권한다.
  - BST: CLRS 3판 12장 — 검색·삽입·삭제 O(h).

### 3. 스택·큐 = "쓸 수 있는 연산을 줄인" 리스트

```text
  스택(LIFO)                     큐(FIFO)
   push ↓   ↑ pop                 enqueue →  [ 1 | 2 | 3 | 4 ]  → dequeue
       [ 4 ]  ← top                          tail               head
       [ 3 ]
       [ 2 ]
       [ 1 ]
```

- 원본 §4·§5가 ADT(`push/pop/peek/empty`, `enqueue/dequeue/peek/empty`)와 파이썬 구현을 보여 준다.
- 비용은 **어디서 꺼내느냐**로 갈린다.
  - 스택: 원본 `list.append` + `list.pop()`은 둘 다 **끝**을 건드린다 → 분할상환 O(1).
  - 큐: 원본 `list.pop(0)`은 **앞**을 뺀다 → 뒤 원소 전부를 한 칸씩 당긴다 → O(n). n개를 다 꺼내면 O(n²).
- Sedgewick 4판 1.3은 스택·큐 API를 "제한된 연산 집합"으로 본다. 원소를 i번째로 읽는 연산을 일부러 빼는 것이 ADT의 쓸모라고 쓴다(`java.util.Stack`이 i번째 접근을 허용하는 것을 비판).

### 실험: 원본 큐(`list.pop(0)`) vs `collections.deque` — 크기 두 배 → 시간 몇 배

원본 §5 `Queue` 클래스를 그대로 쓰고, 꺼내는 쪽만 `deque.popleft()`로 바꾼 것과 비교한다. n개를 넣은 뒤 전부 꺼내는 시간(3번 중 최소).

```python
class ListQueue:                      # 원본 §5 그대로
    def __init__(self): self.container = list()
    def enqueue(self, d): self.container.append(d)
    def dequeue(self): return self.container.pop(0)

class DequeQueue:                     # 꺼내는 쪽만 바꿈
    def __init__(self): self.container = collections.deque()
    def enqueue(self, d): self.container.append(d)
    def dequeue(self): return self.container.popleft()
```

(실험, CPython 3.12.14 `python:3.12-slim` 컨테이너 --cpus=2, 2026-10-05 — 시간은 실행마다 다르다. 3회 실행 중 1회 출력)

```text
ListQueue  n= 20,000      103.2 ms  -
ListQueue  n= 40,000      404.8 ms  x3.9
ListQueue  n= 80,000     1593.3 ms  x3.9
DequeQueue n= 20,000        3.6 ms  -
DequeQueue n= 40,000        7.8 ms  x2.2
DequeQueue n= 80,000       15.2 ms  x2.0
```

- 실행 범위(집필 3회 + 사실 점검 재실행 2회, 같은 환경): `ListQueue` 비율 ×3.3~×4.3, `DequeQueue` 비율 ×1.9~×2.2. n=80,000에서 `ListQueue` 1494~1593 ms, `DequeQueue` 12.9~15.2 ms.
- 관찰: 크기를 두 배로 하면 `list.pop(0)` 큐는 약 4배(= 2²), deque 큐는 약 2배다. 전자가 O(n²), 후자가 O(n) 총비용이라는 예측과 맞는다.
- 해석: 같은 "큐 ADT"인데 구현만 바꿔 80,000건에서 약 100배 차이가 난다. 이 비율은 이 환경·크기 한정이다. n이 커질수록 벌어진다.

### 4. 트리 — 높이 h가 비용을 정한다

```text
  같은 키 1..7을 넣은 BST

  무작위 순서로 넣으면(예: 4,2,6,1,3,5,7)      정렬된 순서로 넣으면(1,2,3,...,7)
             4                                1
           /   \                               \
          2     6                               2
         / \   / \                               \
        1   3 5   7                               3
                                                   \
  높이 3 ≈ log₂ 7                                   ... 7      높이 7 = n
```

- 트리 정의·용어(루트·리프·내부 노드·레벨·높이, 포화·완전 이진 트리)와 순회 3종은 원본 §8·§9, BST의 삽입·검색·삭제 코드는 원본 §10에 있다.
- 원본 §10의 BST는 균형을 맞추지 않는다. 그래서 검색 비용 O(h)의 h가 입력 순서에 달려 있다.
  - *균형(balance)*: 높이를 O(log n)으로 묶어 두는 규칙. 레드-블랙 트리 [16-red-black-tree](../16-red-black-tree/2-summary.md), B-트리 [15-b-tree](../15-b-tree/2-summary.md)가 이 규칙을 가진 트리다.
  - CLRS 3판 12.4: 서로 다른 키를 무작위 순서로 넣어 만든 BST의 기대 높이는 O(lg n)이다. 정렬된 순서는 이 "무작위" 가정을 깨는 입력이다.

### 실험: 원본 코드 그대로 돌려 보기 — 높이와 원본의 버그

원본 §9·§10 코드를 파이썬으로 옮겨(이름만 단순화) 실행했다.

(실험, CPython 3.12.14 `python:3.12-slim` 컨테이너, 2026-10-05)

```text
원본 postorder: [4, 5, 2, 3, 6, 7, 1]
수정 postorder: [4, 5, 2, 6, 7, 3, 1]
중복 6 삽입 후 중위: [1, 3, 4, 6, 6, 7, 8, 10, 13, 14]
remove(99): AttributeError 'NoneType' object has no attribute 'left'
n=1000: 정렬 순서 삽입 높이=1000, 무작위 순서 높이=20
n=2000: 정렬 순서 삽입 높이=2000, 무작위 순서 높이=24
```

- 높이: 정렬 순서로 넣으면 높이 = n. 무작위 순서(seed 1)는 20·24로 log₂n(약 10·11)의 두 배 남짓이다.
- 첫 시도에서 높이를 재귀 함수로 쟀더니 n=2000 정렬 트리에서 `RecursionError: maximum recursion depth exceeded`가 났다. CPython 기본 재귀 한도(1000)보다 트리가 깊었기 때문이다. 늘어진 트리는 느릴 뿐 아니라 재귀 순회를 터뜨린다. 그래서 반복형 높이 함수로 바꿔 쟀다.
- 나머지 세 줄은 원본 코드의 결함이다(아래 "원본 오류" 참고).

### 원본 오류와 바로잡기

- 참고: 원본 §9 `postorder_traverse`의 오른쪽 서브 트리 호출이 `self.preorder_traverse(cur.right, func)`다. 그래서 출력이 `4 5 2 3 6 7 1`로, 원본 그림의 정답 `4 5 2 6 7 3 1`과 다르다(위 실험). `self.postorder_traverse`로 고쳐야 한다.
- 참고: 원본 §10 `remove`는 대상이 없으면 `removed_node`가 `None`인데 `removed_node.left = ...`를 실행해 `AttributeError`가 난다. 원본 ADT 설명("데이터가 없으면 None을 반환")과 어긋난다. `if removed_node is None: return None`이 먼저 와야 한다.
- 참고: 원본 §10은 "이진 탐색 트리는 중복 데이터를 가질 수 없다"고 쓰지만, 원본 `insert`의 `else` 가지는 같은 값을 오른쪽에 넣는다(위 실험에서 6이 두 번). 중복을 금지하려면 `data == cur.data`일 때 무시하거나 갱신하는 가지가 필요하다. 중복을 허용하는 정의(CLRS 12.1은 왼쪽 ≤ 노드 ≤ 오른쪽)도 있으므로, 어느 쪽인지 ADT에 적어야 한다.
- 참고: 원본 §8은 "모든 레벨이 꽉 찬 트리"를 *포화 이진 트리(full binary tree)* 라 부른다. 용어가 교재마다 갈린다. NIST DADS는 full binary tree를 "모든 노드의 자식이 정확히 0개 또는 2개인 이진 트리"로 정의하고, 모든 레벨이 꽉 찬 트리는 *perfect binary tree*로 따로 둔다. 같은 항목에 일부 교재(Sahni, Carrano & Prichard)는 full을 perfect 뜻으로 쓴다고 적혀 있다. 원본의 그림·식(노드 수 2^(h+1)−1)은 perfect 뜻이므로, 영어 자료를 읽을 때 "full"이 어느 뜻인지 확인해야 한다.
- 참고: 원본 §6은 "연결 리스트는 추가·삭제가 빈번할 때"라고 쓴다. 이 말은 **삽입·삭제할 위치의 노드를 이미 쥐고 있을 때**만 맞다. 위치를 인덱스나 값으로 찾아야 하면 찾는 데 O(n)이 들어 배열과 같은 급이 되고, Java에서는 오히려 배열이 빠른 경우가 많다([02-adt-and-cost-contracts](../02-adt-and-cost-contracts/2-summary.md) 실험).

## 쓰이는 자료구조·알고리즘

- 이 주제가 다루는 구조 → 각 심화 노트
  - 배열·동적 배열 → [01-dynamic-array](../01-dynamic-array/2-summary.md)
  - 연결 리스트 → [02-linked-list](../02-linked-list/2-summary.md)
  - 스택 → [03-stack](../03-stack/2-summary.md)
  - 큐·덱 → [04-queue-deque](../04-queue-deque/2-summary.md)
  - 이진 탐색 트리 → [06-binary-search-tree](../06-binary-search-tree/2-summary.md), 균형 트리 → [16-red-black-tree](../16-red-black-tree/2-summary.md)
  - 해시 테이블 체이닝(원본 §1 그림) → [05-hashmap](../05-hashmap/2-summary.md)
  - 완전 이진 트리를 배열에 담은 것 → [07-heap](../07-heap/2-summary.md)
- 이 주제를 쓰는 곳(🔧)
  - 모든 컬렉션 선택의 출발점 — 다음 편 [02-adt-and-cost-contracts](../02-adt-and-cost-contracts/2-summary.md)가 "인터페이스는 같고 비용은 다르다"를 Java 컬렉션으로 이어 간다.
  - 재귀(원본 §7)는 트리 순회의 도구다 → [algorithm/03-recursion](../../algorithm/03-recursion/2-summary.md).
  - 비용 표기(O(n), 분할상환) → [algorithm/01-algorithm-basics](../../algorithm/01-algorithm-basics/2-summary.md), [algorithm/02-asymptotic-analysis](../../algorithm/02-asymptotic-analysis/2-summary.md).

## 적용 — 풀어나가는 법

### 1. 구조를 고르는 순서

```text
  ① 가장 자주 하는 연산은?   위치로 읽기 / 값으로 찾기 / 앞·뒤 넣고 빼기 / 정렬 순서 유지
  ② 그 연산의 비용이 n에 따라 어떻게 커지나?   (위 표, Javadoc, 언어 문서)
  ③ n은 운영에서 얼마까지 가나?   테스트 크기 말고 운영 최대치
  ④ 상수 비용·메모리는?   노드당 포인터, 박싱, 캐시 지역성
```

- 예: "들어온 순서대로 처리, 앞에서 꺼냄" → 큐. Java는 `ArrayDeque`, 파이썬은 `collections.deque`. `ArrayList.remove(0)`·`list.pop(0)`은 피한다.
- 예: "키로 찾고, 정렬 순서로도 훑음" → 균형 트리(`TreeMap`). 직접 만든 비균형 BST는 정렬된 입력에서 한 줄이 된다.
- 예: 원본 §6의 비행기 게임 — 최대 개수(100)가 정해져 있으면 고정 배열 + 객체 풀로 생성·삭제를 없앤다. 다만 JVM에서 객체 풀은 오래 사는 객체를 늘려 GC에 불리할 수 있다(언어 영역 커리큘럼 "객체 풀링 반패턴" 항목, [language/12-object-layout-and-allocation-reduction](../../language/12-object-layout-and-allocation-reduction/2-summary.md)). 풀이 필요한지는 할당률 측정으로 정한다.

### 2. Java로 옮기면

```java
import java.util.*;

// 큐: 앞에서 꺼낸다 → ArrayDeque (원형 배열, 양 끝 분할상환 O(1))
Deque<Job> queue = new ArrayDeque<>();
queue.offerLast(job);
Job next = queue.pollFirst();      // ArrayList.remove(0)이면 뒤 원소 전부를 당긴다

// 스택: Deque를 스택으로 (Javadoc이 Stack 대신 권함)
Deque<Frame> stack = new ArrayDeque<>();
stack.push(f); stack.pop();

// 정렬 순서가 필요한 키 집합: 균형 트리
NavigableMap<Long, Order> byId = new TreeMap<>();   // 레드-블랙 트리, get/put O(log n)
```

- `ArrayDeque`는 null 원소를 받지 않는다(Javadoc). null을 큐에 넣던 코드는 바꿔야 한다.

### 3. 진단 — "데이터가 늘자 느려졌다"

- 크기를 두 배씩 늘려 시간을 잰다. 2배면 선형, 4배면 제곱이다([algorithm/02-asymptotic-analysis](../../algorithm/02-asymptotic-analysis/2-summary.md)의 두 배 실험).
- 실행 중인 JVM이면 스레드 덤프를 몇 번 떠서 같은 프레임이 반복되는지 본다. `java.util.LinkedList.node`가 계속 보이면 인덱스 접근 루프를 의심한다(덤프 실례는 [02-adt-and-cost-contracts](../02-adt-and-cost-contracts/2-summary.md)).
- 파이썬은 `py-spy dump`나 `cProfile`로 `list.pop` 호출 위치를 찾는다. `list.pop`의 호출 횟수는 같은데 누적 시간이 n에 따라 제곱으로 늘면 앞쪽 삭제다.

## 장애 시나리오와 대처

### 1. ⚠ `list.pop(0)` 큐 — 운영 적재량에서 소비자 지연 (잘못된 구조로 O(n²))

- 현상: 평소엔 괜찮던 작업 소비자가 백로그가 수만 건 쌓인 뒤부터 처리 속도가 급락한다. 밀릴수록 더 느려진다.
- 보이는 형태: 큐 길이 지표가 계속 오른다. 프로파일에서 `list.pop`(파이썬) 또는 `ArrayList.remove` → `System.arraycopy`(Java)의 비중이 크다.
- 원인: 앞에서 꺼낼 때마다 뒤 원소 전부를 당긴다. 꺼내는 비용이 큐 길이에 비례한다(위 실험: 80,000건에서 deque 대비 약 100배).
- 대처: `collections.deque.popleft()`, Java `ArrayDeque.pollFirst()`로 바꾼다. 처리량이 안 맞으면 큐 길이 상한·배압([reliability/12-backpressure-and-load-shedding](../../reliability/12-backpressure-and-load-shedding/2-summary.md))도 둔다.

### 2. ⚠ 정렬된 키를 비균형 BST에 — 검색이 O(n)으로

- 현상: 직접 만든 트리 인덱스·캐시가 데이터가 늘수록 선형으로 느려진다. 재귀 순회 코드는 스택이 터진다.
- 보이는 형태: Python `RecursionError: maximum recursion depth exceeded`, Java `java.lang.StackOverflowError`. 높이를 찍어 보면 원소 수와 같다(위 실험: n=2000 → 높이 2000).
- 원인: 자동 증가 ID·시각처럼 정렬된 순서로 키가 들어왔다. 원본 §10의 BST처럼 균형 규칙이 없는 트리는 한 줄로 늘어진다.
- 대처: 표준 균형 트리(`TreeMap`)를 쓴다. 직접 구현해야 하면 레드-블랙·AVL 같은 균형 규칙을 넣거나, 키 순서가 필요 없으면 해시 맵으로 바꾼다.

### 3. ⚠ 연결 리스트로 대량 보관 — 메모리 낭비와 캐시 미스

- 현상: 같은 원소 수인데 힙 사용량이 예상의 몇 배이고, 순회가 느리다.
- 보이는 형태: 힙 덤프 히스토그램(`jcmd <pid> GC.class_histogram`)에서 `java.util.LinkedList$Node` 인스턴스 수가 원소 수만큼 있다.
- 원인: 노드마다 객체 헤더와 참조 3개(item·next·prev)가 붙는다. 아래 실험에서 원소 100만 개 기준 `LinkedList` 컨테이너는 약 24 MB, `ArrayList`는 약 4.9 MB였다. 노드가 힙 여기저기 흩어지면 순회가 캐시를 덜 탄다(원본 §1 지역성 설명).
- 대처: 인덱스·끝 연산 위주면 `ArrayList`/`ArrayDeque`. 원시형이면 `int[]`·`long[]`로 박싱도 없앤다.

(실험, OpenJDK 21.0.12 Temurin, `-Xmx1g -XX:+UseSerialGC`, 압축 참조 기본, 2026-10-05 — 원소 `Integer` 객체는 미리 만들어 공유하고 컨테이너만 잰 값. 2회 실행 동일)

```text
ArrayList  1,000,000개: 4,861,992 bytes (원소당 4.9 B)
LinkedList 1,000,000개: 24,000,032 bytes (원소당 24.0 B)
int[]      1,000,000개: 4,000,016 bytes (원소당 4.0 B)
```

- 해석: `ArrayList` 값 4,861,992는 내부 배열 용량 1,215,487칸 × 참조 4바이트(4,861,948)에 배열 헤더·`ArrayList` 객체 몇십 바이트를 더한 값과 맞는다(용량은 1.5배씩 커져 원소 수보다 크다 — [algorithm/02-asymptotic-analysis](../../algorithm/02-asymptotic-analysis/2-summary.md) 실험). `LinkedList` 노드는 원소당 24바이트다. `Integer` 객체(원소마다 따로)는 두 경우 모두 이 수치에 빠져 있다.

### 4. 원본 코드를 그대로 가져다 쓴 경우 — 조용히 틀린 순회, 없는 키 삭제에서 예외

- 현상: 후위 순회로 "자식부터 해제/합산"하는 코드가 잘못된 순서로 처리한다. 없는 키를 지우면 서버가 500을 낸다.
- 보이는 형태: 순회 결과 `4 5 2 3 6 7 1`(기대 `4 5 2 6 7 3 1`), `AttributeError: 'NoneType' object has no attribute 'left'`.
- 원인: 원본 §9의 오타(오른쪽에 전위 순회 호출), 원본 §10의 None 검사 누락.
- 대처: 위 "원본 오류와 바로잡기". 순회 순서·없는 키 삭제를 단위 테스트로 고정한다.

## 핵심 문장

- 자료구조는 "담는 배치 + 그 위의 연산"이고, 같은 연산도 배치에 따라 비용이 O(1)과 O(n)으로 갈린다.
- 배열은 위치로 읽기가 싸고 앞·중간 변경이 비싸다. 연결 리스트는 쥔 노드 주변 변경이 싸고 위치 찾기가 비싸다.
- 큐를 앞에서 빼는 배열로 만들면 n개 처리에 O(n²)이 든다. 크기를 두 배로 하면 시간이 약 4배가 되는 것으로 알아챈다.
- 비균형 BST의 비용 O(h)는 입력 순서에 달려 있다. 정렬된 입력이면 h = n이다.
- 구조를 고를 때는 가장 잦은 연산, 운영 최대 n, 상수·메모리 비용을 순서대로 본다.

## 관련 주제·근거

- 원본: [foundations/data-structures-basics](../../foundations/data-structures-basics/README.md) — 부트캠프 ch11~13 이관본(§1 배치, §2 ADT, §3 연결 리스트, §4 스택, §5 큐, §6 선택 기준, §7 재귀, §8~§10 트리·BST)
- 후속: [02-adt-and-cost-contracts](../02-adt-and-cost-contracts/2-summary.md) — ADT = 연산 + 비용 계약, Java 컬렉션 측정
- 심화 노트: [01-dynamic-array](../01-dynamic-array/2-summary.md) · [02-linked-list](../02-linked-list/2-summary.md) · [03-stack](../03-stack/2-summary.md) · [04-queue-deque](../04-queue-deque/2-summary.md) · [05-hashmap](../05-hashmap/2-summary.md) · [06-binary-search-tree](../06-binary-search-tree/2-summary.md) · [07-heap](../07-heap/2-summary.md) · [16-red-black-tree](../16-red-black-tree/2-summary.md)
- 알고리즘: [algorithm/01-algorithm-basics](../../algorithm/01-algorithm-basics/2-summary.md) · [algorithm/02-asymptotic-analysis](../../algorithm/02-asymptotic-analysis/2-summary.md) · 재귀 [algorithm/03-recursion](../../algorithm/03-recursion/2-summary.md)
- 다른 영역: 메모리 계층·지역성 [foundations/memory-management](../../foundations/memory-management/README.md) · 컴퓨터 구조 커리큘럼 [architecture/README.md](../../architecture/README.md) · Java 컬렉션 문법 [languages/java/syntax/39-collections-framework-map](../../../languages/java/syntax/39-collections-framework-map/2-summary.md)
- 교재·문서
  - 컴퓨터사이언스 부트캠프 with 파이썬 ch11~13(원본 출처)
  - CLRS 3판 10장(Elementary Data Structures: 10.1 스택·큐, 10.2 연결 리스트), 12장(Binary Search Trees: 12.1 BST 성질, 12.4 무작위로 만든 BST의 기대 높이)
  - Sedgewick·Wayne 『Algorithms』 4판 1.3 Bags, Queues, and Stacks <https://algs4.cs.princeton.edu/13stacks/>
  - Java SE 21 API: `ArrayList` <https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/ArrayList.html>, `LinkedList`, `ArrayDeque`(스택·큐로 `Stack`·`LinkedList`보다 빠를 가능성이 높다, null 불가)
  - Python wiki TimeComplexity <https://wiki.python.org/moin/TimeComplexity> — list의 앞쪽 삭제·삽입 O(n), 양 끝이면 deque
  - NIST Dictionary of Algorithms and Data Structures — "full binary tree"(자식 0개 또는 2개, 교재별 다른 용법 주석) <https://xlinux.nist.gov/dads/HTML/fullBinaryTree.html>
- 실험 목록(2026-10-05, scratchpad `dsa/ds-01/`)
  - `queue_cost.py`: 원본 `list.pop(0)` 큐 vs `deque` — CPython 3.12.14(`python:3.12-slim`, --cpus=2), 3회
  - `orig_bugs.py`: 원본 후위 순회·remove·중복 삽입 재현, 정렬/무작위 삽입 BST 높이 — 같은 환경
  - `MemCost.java`: `ArrayList`/`LinkedList`/`int[]` 100만 개 컨테이너 메모리 — OpenJDK 21.0.12 Temurin, `-XX:+UseSerialGC`, 2회
