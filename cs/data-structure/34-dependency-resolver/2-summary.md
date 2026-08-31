# data-structure/34-dependency-resolver — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.

## 전체 흐름

<!-- 이 자료구조가 동작하는 원리를 자기 말로 -->

## 계약 — Resolver (`src/main/java/com/datastructure/depresolve/Resolver.java`)

- `List<String> resolve()`
- `List<String> cycle()`
- `List<List<String>> layers()`

## 보조

- `CycleException` (`src/main/java/com/datastructure/depresolve/CycleException.java`) — 역할:

## 구현 — DependencyGraph (`src/main/java/com/datastructure/depresolve/DependencyGraph.java`)

### 구조

```
DependencyGraph
+-------------------------------------------------------------------------+
| edges    : TreeMap<이름, TreeSet<이름>>                                 |
|            이름 -> "그 이름 뒤에 와야 하는 것들" (인접 리스트)          |
| inDegree : TreeMap<이름, Integer>                                       |
|            이름 -> "그 앞에 와야 하는 것의 개수" (진입 차수)            |
| 둘 다 Tree 계열이라 순회가 이름 오름차순이다 -> 답이 매번 같게 나온다   |
+-------------------------------------------------------------------------+

화살표의 방향 (실코드가 고른 쪽)
    dependsOn(dependent, dependency)  =  "dependent 가 dependency 에 기댄다"
    코드는 edges.get(dependency).add(dependent) 를 한다
        ->  간선은 dependency -> dependent,  즉 "먼저 와야 하는 것 -> 나중에 오는 것"
        ->  inDegree 가 올라가는 쪽은 dependent (기대는 쪽)
    "기댄다" 방향(A -> B)으로 그리면 답이 정확히 뒤집혀 나온다. 예외가 아니라 조용한 오답이다.
    순환 탐지는 방향을 뒤집어도 통과한다 - 순환은 뒤집어도 순환이라서.

예시 : dependsOn(b,a)  dependsOn(c,a)  dependsOn(d,b)  dependsOn(d,c)

             a                edges                    inDegree
            / \               a -> { b, c }             a : 0    <- 앞에 아무것도 없다
           v   v              b -> { d }                b : 1
           b   c              c -> { d }                c : 1
            \ /               d -> { }                  d : 2
             v
             d                after("a") = [b, c]       inDegreeOf("d") = 2
                              dependenciesOf("d") = [b, c]
                                (반대 방향이라 edges 전체를 훑어서 만든다 - O(V+E))
```

### 동작 — 간선 추가

```
dependsOn("d", "b")  :  d 가 b 에 기댄다  ->  간선 b -> d

  before                                after
    edges     a -> { b, c }               edges     a -> { b, c }
              b -> { }                              b -> { d }        <- d 를 담았다
              c -> { }                              c -> { }
              d -> { }                              d -> { }
    inDegree  a:0  b:1  c:1  d:0          inDegree  a:0  b:1  c:1  d:1
                                                                 ^ 기대는 쪽만 +1

  없는 이름이 나오면 add 로 먼저 만들어 넣는다 (edges 에 빈 집합, inDegree 에 0)

같은 의존을 두 번 걸면 (dependsOn(d,b) 를 또)
    edges.get("b").add("d")  ->  TreeSet 이라 false (이미 있다)
    false 면 inDegree 를 안 올린다
    두 번 올리면 d 의 진입 차수가 영원히 0 이 안 되고,
    순환이 없는데도 "순환이다" 로 보고된다.  중복 방어가 정확성의 일부인 자리다.

자기 자신에게 기대면 (dependsOn(x, x))
    edges[x] 에 x 를 넣고 inDegree[x] += 1  ->  길이 1 짜리 순환으로 그대로 다룬다

비용: add / dependsOn 모두 TreeMap+TreeSet 조회이므로 O(log V + log E)
      dependenciesOf 만 반대 방향이라 O(V + E) 로 훑는다
```

### 필드
- `edges` — 역할:
- `inDegree` — 역할:

### `void add(String name)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `void dependsOn(String dependent, String dependency)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `List<String> names()`
- 하는 일:
- 논리:
- 비용(왜):

### `List<String> after(String name)`
- 하는 일:
- 논리:
- 비용(왜):

### `int inDegreeOf(String name)`
- 하는 일:
- 논리:
- 비용(왜):

### `List<String> dependenciesOf(String name)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `int size()` / `int edgeCount()`
- 하는 일:
- 논리:
- 비용(왜):

### `String toString()`
- 하는 일:
- 논리:
- 비용(왜):

## 구현 — KahnResolver (`src/main/java/com/datastructure/depresolve/KahnResolver.java`)

### 동작 — 위상 정렬(단계별)

```
같은 그래프                a          진입 차수  a:0  b:1  c:1  d:2
                          / \         간선      a->b  a->c  b->d  c->d
                         v   v
                         b   c
                          \ /
                           v
                           d

준비 : 진입 차수 0 인 것만 ready 에 넣는다.  remaining 은 진입 차수의 복사본이다.

 step  꺼낸 것   ready(꺼내기 전)   remaining a b c d      order
 ----  -------  ----------------  -----------------  ------------------
   0     -       [ a ]             0 1 1 2            []
   1     a       [ a ]             0 0 0 2            [a]
         after(a) = b, c  ->  b 1->0 (ready 에 넣음), c 1->0 (넣음)
   2     b       [ b, c ]          0 0 0 1            [a, b]
         after(b) = d     ->  d 2->1 (아직 0 이 아니라 안 넣음)
   3     c       [ c ]             0 0 0 0            [a, b, c]
         after(c) = d     ->  d 1->0 (넣음)
   4     d       [ d ]             0 0 0 0            [a, b, c, d]
         after(d) = 없음
   5     -       [ ]  비었다        ->  종료

order.size() == graph.size() 이므로 순환이 없다.  결과 [a, b, c, d]

결정성 : ready 는 PriorityQueue 다 (java.util.PriorityQueue<String>, 자연 순서).
    진입 차수 0 인 것이 여럿일 때 이름이 사전순으로 작은 것부터 꺼낸다.
    -> 이 구현의 답은 "사전순으로 가장 이른 위상 정렬" 하나로 고정된다.
       삽입 순서 큐가 아니다. 고정하지 않으면 같은 입력에 같은 답을 보장 못 해 기댓값을 못 쓴다.

층 나누기 layers() 는 같은 걸음에서 하나씩이 아니라 "그 시점의 ready 를 통째로" 꺼낸 것이다.
    층 0 : [a]      층 1 : [b, c]      층 2 : [d]
    한 개씩 처리하며 새로 0 이 된 것을 같은 층에 넣으면 층이 뭉개진다.

비용: 모든 노드 1회 + 모든 간선 1회 = O(V + E), 큐가 우선순위 큐라 O((V+E) log V).
      relaxations(진입 차수를 내린 횟수) 는 간선 수와 같아야 한다. 여기서는 4.
```

### 동작 — 사이클 감지

```
순환 그래프 : dependsOn(b,a)  dependsOn(c,b)  dependsOn(a,c)  dependsOn(e,c)

        a ---> b                진입 차수  a:1  b:1  c:1  e:1
        ^      |                간선      a->b  b->c  c->a  c->e
        |      v
        c <----+                e 는 순환에 안 들었지만 순환에 매달려 있다
        |
        +----> e

 step  ready        remaining a b c e     order
   0    [ ]  <- 처음부터 비었다  1 1 1 1     []
   -    꺼낼 것이 없으므로 즉시 종료

  order.size() = 0  <  graph.size() = 4    ->  순환이다
  a 는 c 를 기다리고, c 는 b 를 기다리고, b 는 a 를 기다린다.
  서로가 서로를 막아서 진입 차수가 영원히 0 이 안 된다.

  판정 : order.size() != graph.size()  ->  CycleException 을 던진다
         절반만 채운 부분 결과를 돌려주지 않는다 (절반만 설치된 상태가 더 나쁘다)

  cycle() 은 빈 목록을 준다
      남은 { a, b, c, e } 가 "순환에 걸린 것들" 인 것까지는 안다.
      그중 실제로 도는 고리가 a -> b -> c -> a 이고 e 는 딸려 남은 것뿐이라는 것은 모른다.
      모르는 것을 아는 척하지 않는다. 그 위치를 아는 쪽이 DfsResolver 다.
      (같은 문제를 푸는 두 알고리즘의 차이가 답이 아니라 실패했을 때 말해줄 수 있는 것에 있다)
```

### 필드
- `graph` — 역할:
- `relaxations` — 역할:

### `KahnResolver(DependencyGraph graph)`
- 하는 일:
- 논리:
- 비용(왜):

### `List<String> resolve()` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `List<String> cycle()`
- 하는 일:
- 논리:
- 비용(왜):

### `List<List<String>> layers()` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `long relaxations()`
- 하는 일:
- 논리:
- 비용(왜):

### `String toString()`
- 하는 일:
- 논리:
- 비용(왜):

## 구현 — DfsResolver (`src/main/java/com/datastructure/depresolve/DfsResolver.java`)

### 동작 — DFS 후위 + 색칠

```
색은 Map<String, Integer> color 하나에 int 상수로 담는다 (enum 도 Set 도 아니다)
    WHITE = 0   아직 안 봤다
    GRAY  = 1   지금 내려가는 중이다 (path 에 있다 = 재귀 스택 위)
    BLACK = 2   다 보고 돌아왔다

상태 전이 :  WHITE --(walk 진입)--> GRAY --(자식 다 보고 돌아옴)--> BLACK
             GRAY 를 다시 만나면 back edge = 순환

[1] 순환 없는 경우 - 같은 그래프 (a->b, a->c, b->d, c->d)

    walk(a)  a: W->G   path=[a]                   after(a) = b, c
      walk(b)  b: W->G   path=[a,b]               after(b) = d
        walk(d)  d: W->G   path=[a,b,d]           after(d) = 없음
                 d: G->B   path=[a,b]   postorder=[d]        <- 자식을 다 본 뒤에 자기를 적는다
               b: G->B   path=[a]       postorder=[d,b]
      walk(c)  c: W->G   path=[a,c]               after(c) = d
               d 는 이미 BLACK -> 다시 안 내려간다. 순환도 아니다
               c: G->B   path=[a]       postorder=[d,b,c]
             a: G->B   path=[]          postorder=[d,b,c,a]

    postorder =            [ d, b, c, a ]
    reverse   ->  결과      [ a, c, b, d ]

    왜 뒤집으면 위상 순서인가
        후위는 "내 뒤에 와야 하는 것들이 전부 끝난 다음에" 나를 적는다
        -> 후위 목록에서 나는 내 뒤에 올 것들보다 항상 뒤에 있다
        -> 통째로 뒤집으면 나는 내 뒤에 올 것들보다 항상 앞에 온다 = 위상 순서
    칸 알고리즘의 답 [a,b,c,d] 와 다르다. 둘 다 맞다 (위상 정렬은 답이 여럿).

[2] 순환 있는 경우 - a->b, b->c, c->a

    walk(a)  a: W->G  path=[a]
      walk(b)  b: W->G  path=[a,b]
        walk(c)  c: W->G  path=[a,b,c]      after(c) = a
                 color[a] == GRAY  ->  지금 내려온 길 위에서 다시 만났다 = back edge

                   path = [ a, b, c ]
                            ^        |
                            +--------+  from = path.indexOf("a") = 0
                   loop = path.subList(0, 3) + "a" = [a, b, c, a]
                          (처음과 끝을 같게 해서 고리임을 드러낸다)
                 walk 가 false 를 돌려주며 그대로 되감아 올라간다 -> CycleException(loop)

    BLACK 을 다시 만나는 것은 순환이 아니다. 색을 둘로 줄이면 이 둘을 구별 못 해서
    다이아몬드 모양(a->b, a->c, b->d, c->d)의 d 를 순환으로 잘못 보고한다.

비용: 각 노드에 한 번만 내려간다(WHITE 일 때만) -> visits == V 여야 한다.
      간선도 한 번씩 보므로 O(V + E). 재귀 깊이만큼 스택을 쓴다.
      layers() 는 이 알고리즘의 부산물이 아니라 후위 순서를 다시 훑어 따로 계산한다
      (내 층 + 1 을 뒤엣것에 max 로 퍼뜨린다). 칸에서는 그냥 나오던 값이다.
```

### 필드
- `WHITE` / `GRAY` / `BLACK` — 역할:
- `graph` — 역할:
- `visits` — 역할:
- `foundCycle` — 역할:

### `DfsResolver(DependencyGraph graph)`
- 하는 일:
- 논리:
- 비용(왜):

### `List<String> resolve()` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `boolean walk(String name, Map<String, Integer> color, List<String> path, List<String> postorder)` (TODO, private)
- 하는 일:
- 논리:
- 비용(왜):

### `List<String> cycle()`
- 하는 일:
- 논리:
- 비용(왜):

### `List<List<String>> layers()` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `long visits()`
- 하는 일:
- 논리:
- 비용(왜):

### `String toString()`
- 하는 일:
- 논리:
- 비용(왜):

## 구현 전략 비교

| 전략 | 장점 | 단점 | 적합한 경우 |
|------|------|------|-------------|
| KahnResolver | | | |
| DfsResolver | | | |

## 핵심 문장

<!-- 지도 수준의 문장들 — 세부가 아니라 "왜 이 구조인가"를 담은 문장 -->

-
-
-

## 관련 자료

- 원본 README: `/home/jun/project/myway/data-structure/34-dependency-resolver/README.md`
- 구현 대상: `/home/jun/project/myway/data-structure/34-dependency-resolver/src/main/java/com/datastructure/depresolve/`
- 테스트: `/home/jun/project/myway/data-structure/34-dependency-resolver/src/test/java/com/datastructure/depresolve/`
- 정답 구현: `/home/jun/project/myway/data-structure/34-dependency-resolver/impl/`
