# data-structure/28-rope — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.

## 전체 흐름

<!-- 이 자료구조가 동작하는 원리를 자기 말로 -->

## 계약 — CharSequenceStore (`src/main/java/com/datastructure/rope/CharSequenceStore.java`)

- `int length()`
- `char charAt(int index)`
- `String substring(int from, int to)`
- `CharSequenceStore concat(CharSequenceStore other)`
- `CharSequenceStore insert(int index, String s)`
- `CharSequenceStore delete(int from, int to)`
- `Split split(int index)`
- `String toString()`
- `long charsCopiedByLastOp()`
- `long charsCopiedTotal()`

## 보조 — (TODO 없는 값 객체 · 보조 타입)

- `Edit` (`Edit.java`) — 역할:
- `Edit.Insert(int index, String text)` — 역할:
- `Edit.Delete(int from, int to)` — 역할:
- `CharSequenceStore.Split(CharSequenceStore left, CharSequenceStore right)` — 역할:
- `RopeProblems.Lcp(int length, long comparedChars)` — 역할:

## 구현 — StringBuilderStore (`src/main/java/com/datastructure/rope/StringBuilderStore.java`)

### 필드
- `buf` — 역할:
- `copiedByLastOp` — 역할:
- `copiedTotal` — 역할:

### `StringBuilderStore(String text)`
- 하는 일:
- 논리:
- 비용(왜):

### `int length()` / `char charAt(int index)` / `String substring(int from, int to)`
- 하는 일:
- 논리:
- 비용(왜):

### `StringBuilderStore concat(CharSequenceStore other)` (TODO 1)
- 하는 일:
- 논리:
- 비용(왜):

### `StringBuilderStore insert(int index, String s)` (TODO 2)
- 하는 일:
- 논리:
- 비용(왜):

### `StringBuilderStore delete(int from, int to)` (TODO 3)
- 하는 일:
- 논리:
- 비용(왜):

### `Split split(int index)`
- 하는 일:
- 논리:
- 비용(왜):

### `String toString()` / `long charsCopiedByLastOp()` / `long charsCopiedTotal()`
- 하는 일:
- 논리:
- 비용(왜):

## 구현 — Rope (`src/main/java/com/datastructure/rope/Rope.java`)

### 필드
- `DEFAULT_LEAF_MAX` (public static final) — 역할:
- `root` — 역할:
- `leafMax` — 역할:
- `copiedByLastOp` / `copiedTotal` — 역할:
- `charAtVisits` — 역할:
- `EMPTY` — 역할:
- `Node.text` — 역할:
- `Node.left` / `Node.right` — 역할:
- `Node.weight` — 역할:
- `Node.length` — 역할:
- `Node.depth` — 역할:

### `Rope(String text)` / `Rope(String text, int leafMax)`
- 하는 일:
- 논리:
- 비용(왜):

### `int length()`
- 하는 일:
- 논리:
- 비용(왜):

### `char charAt(int index)` (TODO 5)
- 하는 일:
- 논리:
- 비용(왜):

### `String substring(int from, int to)`
- 하는 일:
- 논리:
- 비용(왜):

### `void appendRange(Node node, int from, int to, StringBuilder out)` (TODO 9, private static)
- 하는 일:
- 논리:
- 비용(왜):

### `Node concatNodes(Node a, Node b)` (TODO 4, static)
- 하는 일:
- 논리:
- 비용(왜):

### `Rope concat(CharSequenceStore other)`
- 하는 일:
- 논리:
- 비용(왜):

### `Split split(int index)`
- 하는 일:
- 논리:
- 비용(왜):

### `Node[] splitNode(Node node, int index, long[] copied)` (TODO 6, static)
- 하는 일:
- 논리:
- 비용(왜):

### `Rope insert(int index, String s)` (TODO 7)
- 하는 일:
- 논리:
- 비용(왜):

### `Rope delete(int from, int to)` (TODO 8)
- 하는 일:
- 논리:
- 비용(왜):

### `Rope rebalance()` (TODO 10)
- 하는 일:
- 논리:
- 비용(왜):

### `String toString()`
- 하는 일:
- 논리:
- 비용(왜):

### `long charsCopiedByLastOp()` / `long charsCopiedTotal()`
- 하는 일:
- 논리:
- 비용(왜):

### `int leafMax()` / `int depth()` / `int leafCount()` / `int nodeCount()` / `List<String> leaves()`
- 하는 일:
- 논리:
- 비용(왜):

### `long charAtVisits()` / `void resetCharAtVisits()`
- 하는 일:
- 논리:
- 비용(왜):

## 구현 전략 비교

| 전략 | 장점 | 단점 | 적합한 경우 |
|------|------|------|-------------|
| StringBuilderStore (연속 배열) | | | |
| Rope (트리 + 조각) | | | |
| Rope, leafMax 작게 | | | |
| Rope, leafMax 크게 | | | |

## 문제 — RopeProblems (`src/main/java/com/datastructure/rope/RopeProblems.java`)

### 문제 1. 편집 목록을 순서대로 적용한다 — `applyEdits(CharSequenceStore doc, List<Edit> edits)` (TODO 11)

> 문제 설명: 에디터가 하는 일이 이것이다. 키 입력 하나가 편집 하나이고, 문서는 그때마다 새로 만들어진다.
> 같은 목록을 `StringBuilderStore` 와 `Rope` 에 주고 `charsCopiedTotal` 을 비교하는 것이 이 박스의 한계 측정이다.
> 답은 반드시 같고 옮긴 글자 수만 다르다.
> `Edit` 은 sealed 이므로 두 경우(`Insert`, `Delete`)를 다 덮을 수 있다.
> 생각할 것: 이 계약에서 `doc` 은 안 바뀐다. 편집 목록이 비었으면 무엇을 돌려주는가.

- 내 접근:
- 논리:
- 비용(왜):

### 문제 2. 두 문서의 공통 접두사 — `longestCommonPrefix(CharSequenceStore a, CharSequenceStore b)` (TODO 12: `sharedAwarePrefix`)

> 문제 설명: 두 문서의 공통 접두사 길이를 구한다. 비교한 글자 수(`Lcp.comparedChars`)도 같이 돌려준다.
> 로프 둘이면 구조를 이용하고, 아니면 나이브(`naiveLongestCommonPrefix`, 미리 채워져 있음)로 간다.
> `longestCommonPrefixLength` 는 길이만 필요할 때 쓰는 형태다.
> 생각할 것: 잎 크기가 다른 두 로프도 들어온다. 잎 경계가 어긋나도 답이 같아야 한다.
> 나이브는 두 문서가 실제로 같은 조각을 공유하고 있어도 알 길이 없다 — 왜인가.

- 내 접근:
- 논리:
- 비용(왜):

## 핵심 문장

<!-- 지도 수준의 문장들 — 세부가 아니라 "왜 이 구조인가"를 담은 문장 -->

-
-
-

## 관련 자료

- 원본 README: `/home/jun/project/myway/data-structure/28-rope/README.md`
- 구현 대상: `/home/jun/project/myway/data-structure/28-rope/src/main/java/com/datastructure/rope/`
- 테스트: `/home/jun/project/myway/data-structure/28-rope/src/test/java/com/datastructure/rope/`
- 정답 구현: `/home/jun/project/myway/data-structure/28-rope/impl/`
