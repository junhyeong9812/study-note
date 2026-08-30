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
