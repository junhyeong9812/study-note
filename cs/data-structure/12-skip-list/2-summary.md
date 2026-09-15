# data-structure/12-skip-list — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.
> 2026-09-14: 쉽게 풀어쓴 확장(Claude 작성) — 한눈에 절·동작 그림·용어 풀이 추가.

## 한눈에 — 쉽게 말하면

**스킵 리스트 = 완행 위에 급행을 얹은 지하철 노선도.** 완행(맨 아래층)은 모든 역에 서고, 급행(위층)은 큰 역에만 선다.\
19번 역에 가려면 — 급행으로 갈 수 있는 데까지 간 다음, 지나칠 것 같으면 한 단계 느린 노선으로 갈아타고, 마지막에 완행으로 도착한다.\
모든 역을 하나하나 지나는 것보다 훨씬 빠르다.

```text
급행   출발 ----------------> [큰역] ----------------------> 끝
완행   출발 -> [1] -> [3] -> [큰역] -> [7] -> [9] -> ... -> 끝

  목적지 찾기: 급행으로 크게 건너뛰다가, 지나칠 것 같으면 아래로 갈아탄다
```

스킵 리스트는 이 노선도와 똑같은 구조다 — 완행이 곧 "모든 원소를 담은 정렬된 연결 리스트(lv0)"이고, 급행들이 그 위에 쌓인 층이다.\
어떤 역을 급행 정차역으로 삼을지는 동전 던지기로 정한다(앞면이 나오는 동안 한 층씩 승격).\
그 확률 덕분에 위층 역 수가 평균 절반씩 줄어, 탐색이 평균 O(log n)이 된다.

> **연결 리스트(linked list)** — 각 칸이 "다음 칸이 어디인지"를 화살표(참조)로 들고 있는 줄.\
> 예: 중간에 끼우고 빼기는 쉽지만, 찾으려면 앞에서부터 걸어야 해서 맨 아래층만으로는 탐색이 O(n)이다.

> **O(log n)** — 원소가 2배로 늘어도 일이 1번만 더 늘어나는 속도.\
> 예: 역이 100만 개여도 급행-완행을 갈아타며 약 20번만 움직이면 도착한다.

실무에서도 똑같이 쓰인다 — Redis 의 정렬 집합(sorted set), Java 의 ConcurrentSkipListMap 이 이 구조다.\
트리처럼 "정렬 + 빠른 탐색 + 범위 조회"를 주면서, 균형 잡는 회전 코드가 없어 구현이 단순하다.

> **해시맵(hash map)** — 키를 해시로 흩어 담아 평균 O(1)에 찾는 구조.\
> 예: 찾기는 더 빠르지만 순서를 안 지켜서 "20 이하 중 가장 큰 키" 같은 질문에는 답하지 못한다.

## 문제 — 이 챕터가 시키는 것

06번 이진 탐색 트리가 정렬된 입력에서 높이 n으로 무너지는 문제를, **회전이 아니라 동전 던지기**로 고치는 구조를 직접 만든다.\
`OrderedMapContractTest.java` 를 따라 친 뒤 `SkipList` 의 TODO 9개를 채우는 것이 본체이고, `SkipListSet` 의 TODO 2개는 두 줄짜리다.\
`./run.sh 12` 로 시작하면 36개 중 35개가 실패한 상태에서 출발한다.

- `SkipList` — `randomLevel()`: 앞면(확률 P)이 나오는 동안 층을 올리되 `MAX_LEVEL` 을 넘지 않기
- `SkipList` — `findPredecessors(key)`: 층마다 "key보다 작은 마지막 노드"를 모으기 (한 층 내려갈 때 `head` 로 되돌리지 않기)
- `SkipList` — `get(key)`: 위층부터 내려오며 전진하고 레벨 0의 다음 노드를 확인하기
- `SkipList` — `put(key, value)`: 기존 키면 값만 갈기, 새 키면 레벨을 뽑고 새로 생긴 층의 앞 노드를 `head` 로 채운 뒤 링크 잇기
- `SkipList` — `remove(key)`: 층마다 앞 노드를 목표의 다음으로 잇되 목표가 없는 층에서 멈추기, 빈 층은 레벨 내리기(1 아래로는 금지)
- `SkipList` — `floorKey(key)` / `ceilingKey(key)`: 전진 조건 `<= 0` 과 `< 0` 의 차이로 이웃 찾기
- `SkipList` — `keysInRange(from, to)`: 시작점으로 O(log n) 에 내려간 뒤 레벨 0을 `to` 까지만 걷기
- `SkipList` — `lastKey()`: 위층부터 갈 데까지 가서 O(log n) 으로 마지막 키 찾기
- `SkipListSet` — `add(key)` / `remove(key)`: 맵의 반환값으로 "새로 들어갔는지 / 있었는지" 판정하기

아래 서머리는 이 문제(README)를 분석·정리한 것이다.

## 전체 흐름

<!-- 이 자료구조가 동작하는 원리를 자기 말로 -->

## 계약 — OrderedMap (`src/main/java/com/datastructure/skiplist/OrderedMap.java`)

- `V put(K key, V value)`
- `V get(K key)`
- `boolean containsKey(K key)`
- `V remove(K key)`
- `int size()`
- `boolean isEmpty()`
- `void clear()`
- `K firstKey()`
- `K lastKey()`
- `K floorKey(K key)`
- `K ceilingKey(K key)`
- `List<K> keys()`
- `List<K> keysInRange(K from, K to)`

## 계약 — OrderedSet (`src/main/java/com/datastructure/skiplist/OrderedSet.java`)

- `boolean add(K key)`
- `boolean contains(K key)`
- `boolean remove(K key)`
- `int size()`
- `boolean isEmpty()`
- `void clear()`
- `K first()`
- `K last()`
- `K floor(K key)`
- `K ceiling(K key)`
- `List<K> toList()`
- `List<K> range(K from, K to)`

## 구현 — SkipList (`src/main/java/com/datastructure/skiplist/SkipList.java`)

<!-- 메서드마다 내 언어로. 복잡도는 "왜 그런지"까지. -->

### 구조

> **더미(sentinel) 노드** — 데이터 없이 "출발점" 역할만 하는 가짜 노드.\
> 예: head 는 key/value 없이 forward 32칸만 갖고 있어서, 맨 앞에 끼워 넣는 경우를 특별 취급하지 않아도 된다.

> **참조/포인터(forward)** — "다음 노드가 어디인지"를 가리키는 화살표.\
> 예: 층마다 하나씩 있어서 배열이고, 그 배열의 길이가 곧 그 노드의 층수다.

```
SkipList — 정렬된 연결 리스트를 여러 층으로 쌓아, 위층에서 멀리 건너뛴다
+---------------------------------------------------------------+
| MAX_LEVEL = 32,  P = 0.5                                      |
| head     더미(sentinel) 노드. key/value 가 없고 forward 는 32칸 |
| level = 4    지금 실제로 쓰는 층 수 (currentLevel())            |
| size = 9                                                      |
| random   randomLevel() 이 쓰는 난수원 (seed 생성자로 재현 가능)  |
+---------------------------------------------------------------+

    Node { final K key;  V value;  final Node<K,V>[] forward; }
        forward 배열의 길이가 곧 그 노드의 층수다 (별도 level 필드가 없다)
        forward[0] 이 최하위 층 — 여기가 모든 노드를 잇는 완전한 정렬 리스트다
        인덱스가 클수록 위층이고, 위층은 아래층의 부분집합이다

lv3   head------->[ 6]------------------------------------------> null
lv2   head------->[ 6]------------------------------>[21]------> null
lv1   head------->[ 6]------->[ 9]------->[17]------>[21]------> null
lv0   head->[ 3]->[ 6]->[ 7]->[ 9]->[12]->[17]->[19]->[21]->[25]-> null

    노드별 층수    3:1   6:4   7:1   9:2   12:1   17:2   19:1   21:3   25:1
    head 만 32칸을 갖고 있고, level(4) 이상의 칸은 전부 null 이다

    lv0 만 보면 그냥 정렬된 단일 연결 리스트다 — 탐색이 O(n).
    위층은 그 리스트 위에 놓인 "급행 노선"이고, 층이 올라갈수록 정차역이 줄어든다.
    BST 는 회전으로 모양을 균형 잡아 O(log n) 을 만든다.
    스킵 리스트는 균형을 잡지 않는다 — 층수를 동전 던지기로 정해 평균적으로 절반씩
    줄어드는 층을 만든다. 회전 코드가 한 줄도 없는 대신 확률에 기댄다
```

> **BST(이진 탐색 트리)** — 각 칸의 왼쪽엔 작은 값, 오른쪽엔 큰 값을 두는 트리.\
> 예: 정렬된 순서로 넣으면 한 줄로 쏠려 탐색이 O(n)까지 느려진다.

> **회전(rotation)** — 쏠린 트리의 모양을 바로잡으려고 부모·자식을 맞바꾸는 재배치 연산.\
> 예: AVL·레드블랙 트리가 이걸 쓰지만, 스킵 리스트에는 회전 코드가 한 줄도 없다 — 확률이 그 일을 대신한다.

> **부분집합** — 어떤 집합의 원소 일부만 모은 집합.\
> 예: lv1 에 있는 노드는 반드시 lv0 에도 있다 — 위층 정차역은 아래층 정차역의 부분집합이다.

### 동작 — 탐색

**언제 쓰나**: get/containsKey 가 직접 쓰고, put/remove 도 "끼울 자리/지울 자리"를 찾을 때 같은 하강을 쓴다.

```
get(19) : 위층에서 크게 건너뛰고, 넘칠 것 같으면 한 층 내려간다
    cur = head 에서 시작해 i = level-1 = 3 부터 0 까지 내려간다.
    각 층에서 "다음 노드의 키가 19 보다 작은 동안" 전진한다 (같거나 크면 내려간다)

    i=3   head 의 다음은 [ 6] — 6 < 19 이므로 전진      cur = [ 6]
          [ 6] 의 lv3 다음은 null                       -> 내려간다     update[3] = [ 6]
    i=2   [ 6] 의 lv2 다음은 [21] — 19 보다 크다        -> 전진 없이 내려간다  update[2] = [ 6]
    i=1   [ 6] -> [ 9] -> [17]     (9 < 19, 17 < 19)
          [17] 의 lv1 다음은 [21] — 크다                -> 내려간다     update[1] = [17]
    i=0   [17] 의 lv0 다음은 [19] — 작지 않다           -> 정지         update[0] = [17]

    답 확인 : update[0].forward[0] = [19] 이고 키가 같다 -> 찾았다

    지나온 자리     head, [ 6], [ 9], [17], [19]      노드 9개 중 5개만 봤다
    lv0 만 있었다면 head, 3, 6, 7, 9, 12, 17, 19 를 전부 지나야 했다

    핵심 두 가지
        (1) 층을 내려갈 때 cur 을 head 로 되돌리지 않는다. 그 자리에서 이어 내려간다 (계단식 하강)
        (2) 각 층에서 "바로 다음 것"만 본다. 되돌아가는 일이 없다 (prev 참조가 필요 없는 이유)
    평균적으로 층마다 두어 칸만 전진하고 층수가 log n 이라 평균 O(log n)

findPredecessors(key) : 하강하면서 각 층의 "key 보다 작은 마지막 노드"를 배열에 적어 둔다
    update[0] = [17]      lv0 에서 19 바로 앞
    update[1] = [17]
    update[2] = [ 6]
    update[3] = [ 6]
    update[4..31] = null      level(4) 위쪽 칸은 채우지 않는다 (배열 길이는 늘 32)

    삽입과 삭제는 이 배열만 있으면 각 층의 링크를 고칠 수 있다.
    이중 연결 리스트가 prev 참조로 하던 일을 여기서는 "내려오면서 기록"으로 해결한다.
    get 은 이 배열이 필요 없어서 32칸을 만들지 않고 따로 하강한다
```

그림에서 일어난 일을 풀면 —

1. 맨 위층에서 출발해, 각 층에서 "다음 노드가 목표보다 작은 동안"만 오른쪽으로 간다.
2. 다음 노드가 목표보다 크거나 없으면(지나칠 것 같으면) 그 자리에서 한 층 내려간다 — head로 되돌아가지 않는다.

> **하강(계단식 하강)** — 층을 내려갈 때 출발점으로 되돌아가지 않고 멈춘 그 자리에서 이어 내려가는 탐색 방식.\
> 예: lv3 에서 [6]까지 갔으면 lv2 도 [6]에서 시작한다 — head로 되돌아가면 위층에서 번 이득이 사라진다.

3. 맨 아래층(lv0)에서 멈춘 자리의 다음 노드가 목표인지 확인한다.
4. findPredecessors 는 같은 하강을 하면서 "각 층에서 마지막으로 멈춘 자리"를 배열(update)에 적어 둔다 — 삽입·삭제가 링크를 고칠 때 이 배열을 쓴다.

> **update 배열(findPredecessors)** — 하강하며 층마다 "목표보다 작은 마지막 노드"를 적어 둔 배열.\
> 예: 이중 연결 리스트가 prev 참조로 하던 일을, 여기서는 "내려오면서 기록"으로 대신한다.

**비용**: 층마다 평균 두어 칸 전진 × 층수 log n = 평균 O(log n).\
(운이 아주 나쁘면 O(n)이지만 확률적으로 드물다.)

### 동작 — 추가

**언제 쓰나**: 새 키를 넣거나(끼워 넣기), 이미 있는 키의 값을 바꿀 때(교체).

> **난수 / seed** — 컴퓨터가 만드는 무작위 숫자 / 그 난수열의 씨앗값.\
> 예: seed를 같게 주면 randomLevel()이 같은 층수를 내놓아서 테스트가 모양을 재현할 수 있다.

```
put(20, v) : 동전 던지기로 층수를 정하고, 그 층수만큼만 끼워 넣는다

    (1) update = findPredecessors(20)
            update[0] = [19]   update[1] = [17]   update[2] = [ 6]   update[3] = [ 6]
    (2) update[0].forward[0] 이 같은 키면 -> 값만 교체하고 끝
            size 도 level 도 모양도 전부 그대로다

    (3) lvl = randomLevel()
            int lvl = 1;
            while (lvl < MAX_LEVEL && random.nextDouble() < P) lvl++;

            동전을 던져 앞면(< 0.5)이면 한 층 더. 그래서
                층수 1 : 1/2      2 : 1/4      3 : 1/8      4 : 1/16   ...
            층이 하나 올라갈 확률이 절반이라 위층 노드 수가 평균 절반씩 줄어든다.
            이 확률 분포 하나가 "균형 잡힌 모양"을 회전 없이 만들어 낸다.
            층수는 넣는 키의 값과 무관하다 — 어떤 순서로 넣어도 모양의 분포가 같다
            (BST 가 정렬 입력에 무너지던 것과 대비되는 지점)

    (4) lvl > level 이면 (지금까지 없던 층이 생긴 경우)
            새 층에는 앞 노드가 head 뿐이다 -> update[level .. lvl-1] = head
            level = lvl

    (5) node = new Node(20, v, lvl);   i = 0 .. lvl-1 각 층에서
            node.forward[i] = update[i].forward[i];    <- 새 노드가 먼저 뒤를 잡고
            update[i].forward[i] = node;               <- 그 다음 앞 노드를 갈아끼운다
        순서를 뒤집으면 뒤쪽으로 가는 길을 잃는다 (02 장 중간 삽입과 같은 함정)

    lvl = 2 가 나왔다면 lv0 과 lv1 두 층에만 끼어든다
    before   lv1   ... [17]--------------->[21] ...
             lv0   ... [17]->[19]--------->[21] ...
    after    lv1   ... [17]-------->[20]-->[21] ...
             lv0   ... [17]->[19]-->[20]-->[21] ...
                                     ^ 위층(lv2, lv3)은 손대지 않는다
```

그림에서 일어난 일을 풀면 —

1. 먼저 하강하며 각 층의 "앞 노드"(update 배열)를 찾는다.\
   같은 키가 이미 있으면 값만 바꾸고 끝.
2. 동전 던지기로 새 노드의 층수를 정한다.\
   앞면(확률 1/2)이 나오는 동안 한 층씩 올라가서, 층수 1은 절반, 2는 1/4, 3은 1/8...\
   이 확률 하나가 회전 없이 균형을 만든다.
3. 정해진 층수만큼만, 각 층에서 "새 노드가 먼저 뒤를 잡고 → 앞 노드를 갈아끼운다".\
   순서를 뒤집으면 뒤로 가는 길을 잃는다.

**비용**: 자리 찾기 O(log n) + 링크 고치기 O(층수) = 평균 O(log n).

### 동작 — 삭제

**언제 쓰나**: 키를 지울 때.\
새 그림을 그리는 게 아니라 "그 노드를 건너뛰게" 링크만 고친다.

```
remove(21)
    (1) update = findPredecessors(21)
            update[0] = [19]   update[1] = [17]   update[2] = [ 6]   update[3] = [ 6]
    (2) target = update[0].forward[0] = [21].  키가 다르거나 null 이면 없는 것 -> null 반환
    (3) i = 0 부터 level-1 까지
            update[i].forward[i] != target 이면 break
                (그 층에 target 이 없다 = 더 위층에도 없다. 위를 볼 필요가 없다)
            아니면 update[i].forward[i] = target.forward[i]     <- 건너뛰게 만든다

            i=0   [19].forward[0] :  [21]  ->  [25]
            i=1   [17].forward[1] :  [21]  ->  null
            i=2   [ 6].forward[2] :  [21]  ->  null
            i=3   [ 6].forward[3] 은 null 이라 target 이 아니다  -> break

    before
    lv2   head------->[ 6]------------------------------>[21]------> null
    lv1   head------->[ 6]------->[ 9]------->[17]------>[21]------> null
    lv0   head->[ 3]->[ 6]->[ 7]->[ 9]->[12]->[17]->[19]->[21]->[25]-> null

    after
    lv2   head------->[ 6]------------------------------------> null
    lv1   head------->[ 6]------->[ 9]------->[17]------------> null
    lv0   head->[ 3]->[ 6]->[ 7]->[ 9]->[12]->[17]->[19]->[25]-> null

    (4) 빈 위층 걷어내기
            while (level > 1 && head.forward[level-1] == null) level--;
        맨 위층에 아무도 없으면 층수를 줄인다. 1 아래로는 내려가지 않는다.
        위 예에서는 lv3 에 [ 6] 이 남아 있어 level 은 4 그대로다.
        [ 6] 을 지웠다면 lv3 가 비어 level 이 3 으로 내려갔을 것이다
        (안 줄이면 빈 층을 훑느라 탐색이 쓸데없이 길어진다)
```

그림에서 일어난 일을 풀면 —

1. 하강하며 각 층의 앞 노드(update)를 찾고, lv0 에서 target 이 진짜 있는지 확인한다.\
   없으면 null 반환.
2. 아래층부터 위로, 앞 노드의 화살표를 target 의 다음으로 갈아끼운다 — target 을 건너뛰게 만든다.\
   target 이 없는 층을 만나면 그 위층에도 없으니 break.
3. 마지막으로 맨 위층이 텅 비었으면 level 을 줄인다(빈 층을 훑는 낭비 방지).

**비용**: 자리 찾기 O(log n) + 링크 고치기 O(층수) = 평균 O(log n).

### 동작 — 이웃과 범위

**언제 쓰나**: "20 이하 중 가장 큰 키는?"(floorKey), "20 이상 중 가장 작은 키는?"(ceilingKey), "from~to 사이 전부"(keysInRange)\
— 정렬을 유지하는 자료구조만 답할 수 있는 질문들이다.

> **이중 연결 리스트 / prev 참조** — 앞뒤 양방향 화살표를 가진 연결 리스트 / 앞 노드를 가리키는 화살표.\
> 예: 스킵 리스트는 prev가 없어서 lastKey가 O(log n)이 되고, 삽입·삭제는 update 배열이 그 자리를 메운다.

```
floorKey / ceilingKey — get 과 같은 하강인데, 부등호 하나와 "답을 어디서 읽느냐"만 다르다

    get / ceilingKey :  while (다음.key <  key) 전진   -> 멈춘 자리의 "다음"이 key 이상
    floorKey         :  while (다음.key <= key) 전진   -> 멈춘 자리 자체가 key 이하 중 최대

    lv0   ... ->[17]->[19]->[21]->[25]-> ...
    floorKey(20)     19 까지 전진하고 멈춘다  -> 답은 멈춘 자리 [19]   (cur == head 면 null)
    ceilingKey(20)   19 에서 멈춘다           -> 답은 그 다음 [21]     (다음이 null 이면 null)

    BST 는 내려가면서 후보(best)를 따로 기억해야 했다.
    여기서는 lv0 이 완전한 정렬 리스트라 "멈춘 자리"와 "그 다음"이 곧 양쪽 이웃이다 —
    후보 변수가 아예 필요 없다

firstKey()  = head.forward[0]                             O(1)
lastKey()   = 각 층에서 갈 수 있는 데까지 오른쪽으로 간다   O(log n)   <- first 와 비대칭이다
              (뒤 방향 포인터가 없어서 끝을 바로 알 수 없다)
keys()      = head.forward[0] 부터 lv0 을 따라 끝까지 걷는다 -> 정렬 순서 그대로

keysInRange(from, to)
    lv3/lv2/lv1 로 from 자리까지 빠르게 하강한 다음, lv0 을 따라 to 이하인 동안 담는다
        head =====> ... =====> [from 직전]        위층으로 찾아가기      O(log n)
                                   |
        lv0                        +--> [ ] -> [ ] -> [ ] -> ... (to 를 넘으면 정지)   결과 개수
    -> O(log n + 결과 개수). 해시맵으로는 할 수 없는 질문이고, BST 의 범위 순회와 같은 성질이다
```

그림에서 일어난 일을 풀면 —

1. floorKey/ceilingKey 는 get 과 같은 하강인데, 부등호 하나(`<` vs `<=`)와 "멈춘 자리를 읽나, 그 다음을 읽나"만 다르다.
2. keysInRange 는 위층으로 from 직전까지 빠르게 간 뒤, lv0(완행)을 따라 to 를 넘을 때까지 담는다.
3. lastKey 는 firstKey 와 달리 O(log n) — 뒤로 가는 화살표가 없어 각 층에서 오른쪽 끝까지 걸어야 한다.

**비용**: floor/ceiling/last O(log n), first O(1), 범위는 O(log n + 결과 개수).

> **O(1)** — 원소가 몇 개든 연산 횟수가 일정한 비용.\
> 예: firstKey 는 `head.forward[0]` 한 번 읽기라 크기와 무관하다.

### `필드`

- `static final int MAX_LEVEL = 32` — 역할:
- `static final double P = 0.5` — 역할:
- `static final class Node<K, V> { final K key; V value; final Node<K, V>[] forward; }` — 역할:
- `final Node<K, V> head` — 역할:
- `private final Random random` — 역할:
- `int level` — 역할:
- `private int size` — 역할:

### `SkipList()`

- 하는 일:
- 논리:
- 비용(왜):

### `SkipList(long seed)`

- 하는 일:
- 논리:
- 비용(왜):

### `int randomLevel()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `Node<K, V>[] findPredecessors(K key)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `V get(K key)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `V put(K key, V value)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `V remove(K key)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `K floorKey(K key)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `K ceilingKey(K key)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `List<K> keys()`

- 하는 일:
- 논리:
- 비용(왜):

### `List<K> keysInRange(K from, K to)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `K firstKey()`

- 하는 일:
- 논리:
- 비용(왜):

### `K lastKey()` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `boolean containsKey(K key)`

- 하는 일:
- 논리:
- 비용(왜):

### `int size()`

- 하는 일:
- 논리:
- 비용(왜):

### `boolean isEmpty()`

- 하는 일:
- 논리:
- 비용(왜):

### `int currentLevel()`

- 하는 일:
- 논리:
- 비용(왜):

### `void clear()`

- 하는 일:
- 논리:
- 비용(왜):

## 구현 — SkipListMap (`src/main/java/com/datastructure/skiplist/SkipListMap.java`)

### 구조 — 감싸기만 한다

> **위임(delegation)** — 일을 직접 하지 않고 안에 품은 다른 객체에게 그대로 넘기는 설계.\
> 예: SkipListMap 은 자기 자료구조 없이 put/get/remove를 전부 SkipList 에 넘긴다 — "비서가 전화를 대신 돌려주는" 방식.

```
SkipListMap — SkipList 하나를 감싸는 순수 위임이다. 자기 자료구조가 없다
    +--------------------------------+
    | list ----> SkipList<K, V>      |
    +--------------------------------+
    put / get / remove / firstKey / lastKey / floorKey / ceilingKey / keys / keysInRange ...
    전부 그대로 넘긴다

    유일하게 더하는 규칙 : put 의 value 가 null 이면 거부한다
        get 이 "없음"을 null 로 답하기 때문이다.
        null 값을 허용하면 "없다"와 "null 이 들어 있다"를 구분할 수 없고,
        containsKey 가 get(k) != null 로 구현되어 있어 곧장 틀린 답이 된다

    SkipList 는 OrderedMap 계약을 몰라도 되고, 계약을 맞추는 일은 이 클래스가 맡는다.
    seed 생성자를 그대로 뚫어 두어 테스트가 층수를 재현할 수 있게 한다
```

> **null** — "아무것도 없음"을 뜻하는 값.\
> 예: get 이 "없음"을 null 로 답하므로, 값으로 null 을 허용하면 "없다"와 "null 이 들어 있다"를 구분할 수 없어 put 에서 거부한다.

> **계약(interface, OrderedMap/OrderedSet)** — "이 메서드들을 이렇게 제공하겠다"는 약속 목록.\
> 예: SkipList 자체는 이 약속을 몰라도 되고, 계약을 맞추는 일은 SkipListMap 이 맡는다.

### `필드`

- `private final SkipList<K, V> list` — 역할:

### `SkipListMap()`

- 하는 일:
- 논리:
- 비용(왜):

### `SkipListMap(long seed)`

- 하는 일:
- 논리:
- 비용(왜):

### `V put(K key, V value)`

- 하는 일:
- 논리:
- 비용(왜):

### `V get(K key)`

- 하는 일:
- 논리:
- 비용(왜):

### `boolean containsKey(K key)`

- 하는 일:
- 논리:
- 비용(왜):

### `V remove(K key)`

- 하는 일:
- 논리:
- 비용(왜):

### `int size()`

- 하는 일:
- 논리:
- 비용(왜):

### `boolean isEmpty()`

- 하는 일:
- 논리:
- 비용(왜):

### `void clear()`

- 하는 일:
- 논리:
- 비용(왜):

### `K firstKey()`

- 하는 일:
- 논리:
- 비용(왜):

### `K lastKey()`

- 하는 일:
- 논리:
- 비용(왜):

### `K floorKey(K key)`

- 하는 일:
- 논리:
- 비용(왜):

### `K ceilingKey(K key)`

- 하는 일:
- 논리:
- 비용(왜):

### `List<K> keys()`

- 하는 일:
- 논리:
- 비용(왜):

### `List<K> keysInRange(K from, K to)`

- 하는 일:
- 논리:
- 비용(왜):

## 구현 — SkipListSet (`src/main/java/com/datastructure/skiplist/SkipListSet.java`)

### 구조 — 값 자리에 자리표시자 하나

> **포함(composition) vs 상속(inheritance)** — 다른 클래스를 "부품으로 안에 품기" vs "부모를 물려받기".\
> 예: SkipListSet 은 SkipListMap 을 상속하지 않고 필드로 품어서, 맵의 메서드가 밖으로 새지 않는다.

> **자리표시자(placeholder, PRESENT)** — 내용은 아무래도 좋고 "자리가 차 있다"는 표시로만 쓰는 값.\
> 예: 모든 키가 같은 PRESENT 객체 하나를 가리켜서, 원소마다 객체를 새로 만들지 않는다.

```
SkipListSet — 상속이 아니라 포함이다. SkipListMap 의 값 자리에 자리표시자를 넣는다
    private static final Object PRESENT = new Object();
    +-----------------------------------+
    | map ----> SkipListMap<K, Object>  |
    +-----------------------------------+

    키    [ 3]      [ 6]      [ 7]      [ 9]      [12]  ...
           |         |         |         |         |
           +---------+---------+---------+---------+---> PRESENT (객체는 딱 하나뿐)

    값이 무엇인지는 아무 의미가 없다. 필요한 것은 "그 키가 있다"뿐이라서
    모든 항목이 같은 객체 하나를 가리킨다 (원소마다 객체를 만들지 않는다)

    add(k)     = map.put(k, PRESENT) == null      <- 옛 값이 없었으면 새로 넣은 것 -> true
    remove(k)  = map.remove(k) != null            <- 옛 값이 있었으면 지운 것      -> true
        둘 다 조회를 따로 하지 않고 반환값만으로 판정한다 (같은 길을 두 번 훑지 않는다)

    이름만 바꿔 넘긴다
        first / last / floor / ceiling / toList / range
          ->  firstKey / lastKey / floorKey / ceilingKey / keys / keysInRange
```

### `필드`

- `private static final Object PRESENT` — 역할:
- `private final SkipListMap<K, Object> map` — 역할:

### `SkipListSet()`

- 하는 일:
- 논리:
- 비용(왜):

### `SkipListSet(long seed)`

- 하는 일:
- 논리:
- 비용(왜):

### `boolean add(K key)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `boolean contains(K key)`

- 하는 일:
- 논리:
- 비용(왜):

### `boolean remove(K key)` (TODO)

- 하는 일:
- 논리:
- 비용(왜):

### `int size()`

- 하는 일:
- 논리:
- 비용(왜):

### `boolean isEmpty()`

- 하는 일:
- 논리:
- 비용(왜):

### `void clear()`

- 하는 일:
- 논리:
- 비용(왜):

### `K first()`

- 하는 일:
- 논리:
- 비용(왜):

### `K last()`

- 하는 일:
- 논리:
- 비용(왜):

### `K floor(K key)`

- 하는 일:
- 논리:
- 비용(왜):

### `K ceiling(K key)`

- 하는 일:
- 논리:
- 비용(왜):

### `List<K> toList()`

- 하는 일:
- 논리:
- 비용(왜):

### `List<K> range(K from, K to)`

- 하는 일:
- 논리:
- 비용(왜):

## 구현 전략 비교

| 전략 | 장점 | 단점 | 적합한 경우 |
|------|------|------|-------------|
| SkipList | | | |
| SkipListMap | | | |
| SkipListSet | | | |

## 핵심 문장

<!-- 지도 수준의 문장들 — 세부가 아니라 "왜 이 구조인가"를 담은 문장 -->

-
-
-

## 관련 자료

<!-- 원본 문서·코드 경로. 기준 소스는 문서가 아니라 코드/원전이다. -->

- 원본 README: `/home/jun/project/myway/data-structure/12-skip-list/README.md`
- 구현: `/home/jun/project/myway/data-structure/12-skip-list/src/main/java/com/datastructure/skiplist/`
- 테스트: `/home/jun/project/myway/data-structure/12-skip-list/src/test/java/com/datastructure/skiplist/`
- 참고 구현: `/home/jun/project/myway/data-structure/12-skip-list/impl/`

## 용어 풀이

본문에 등장한 자리에서 이미 푼 용어를 포함해, 이 문서의 전문용어를 한곳에 모았다.

- **연결 리스트(linked list)**: 각 칸이 "다음 칸이 어디인지"를 화살표로 들고 있는 줄. 끼우고 빼기는 쉽지만 찾기는 앞에서부터 걸어야 한다.
- **참조/포인터(forward)**: 다른 노드가 "어디에 있는지"를 가리키는 화살표. 스킵 리스트 노드는 층마다 하나씩, 배열로 갖는다.
- **더미(sentinel) 노드**: 데이터 없이 출발점 역할만 하는 가짜 노드. 맨 앞 특별 처리를 없애 준다.
- **BST(이진 탐색 트리)**: 왼쪽엔 작은 값, 오른쪽엔 큰 값을 두는 트리. 정렬된 입력이 들어오면 한 줄로 쏠려 느려진다.
- **회전(rotation)**: 쏠린 트리 모양을 바로잡는 재배치 연산. 스킵 리스트에는 없다 — 확률이 그 일을 대신한다.
- **난수 / seed**: 컴퓨터가 만드는 무작위 숫자 / 그 난수열의 씨앗값. seed 가 같으면 같은 순서가 나와 테스트 재현이 가능하다.
- **O(1), O(log n), O(n)**: 원소 수 n에 대해 연산 횟수가 어떻게 늘어나는지의 표기. O(1) 상수, O(log n) 은 n이 2배 돼도 1번만 더, O(n) 은 n에 비례.
- **부분집합**: 어떤 집합의 원소 일부만 모은 집합. 위층 정차역은 아래층 정차역의 부분집합이다.
- **하강(계단식 하강)**: 층을 내려갈 때 출발점으로 되돌아가지 않고 멈춘 그 자리에서 이어 내려가는 탐색 방식.
- **update 배열(findPredecessors)**: 하강하며 층마다 "목표보다 작은 마지막 노드"를 적어 둔 배열. 삽입·삭제가 링크를 고칠 때 쓴다.
- **이중 연결 리스트 / prev 참조**: 앞뒤 양방향 화살표를 가진 연결 리스트 / 앞 노드를 가리키는 화살표. 스킵 리스트는 prev 없이 update 배열로 대신한다.
- **해시맵(hash map)**: 키를 해시로 흩어 담아 평균 O(1)에 찾는 구조. 대신 정렬·범위 조회는 못 한다.
- **위임(delegation)**: 일을 안에 품은 객체에게 그대로 넘기는 설계.
- **포함(composition) vs 상속(inheritance)**: 부품으로 품기 vs 부모를 물려받기. SkipListSet 은 SkipListMap 을 품는다.
- **자리표시자(placeholder, PRESENT)**: 내용 없이 "자리가 차 있다"는 표시로만 쓰는 값.
- **null**: "아무것도 없음"을 뜻하는 값. 값으로 null 을 허용하면 "없다"와 구분이 안 돼서 put 에서 거부한다.
- **계약(interface, OrderedMap/OrderedSet)**: "이 메서드들을 이렇게 제공하겠다"는 약속 목록. 구현과 분리된 명세.
