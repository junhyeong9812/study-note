# data-structure/35-allocator — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.

## 전체 흐름

<!-- 이 자료구조가 동작하는 원리를 자기 말로 -->

## 계약 — Allocator (`src/main/java/com/datastructure/allocator/Allocator.java`)

- `int FAIL = -1` (상수)
- `int allocate(int size)`
- `void free(int address)`
- `int capacity()`
- `int usedBytes()`
- `int freeBytes()`
- `int largestFreeBlock()`
- `int freeBlockCount()`
- `int wastedBytes()`

## 구현 — BumpAllocator (`src/main/java/com/datastructure/allocator/BumpAllocator.java`)

### 필드
- `capacity` — 역할:
- `next` — 역할:
- `handedOut` — 역할:
- `freeCalls` — 역할:

### `BumpAllocator(int capacity)`
- 하는 일:
- 논리:
- 비용(왜):

### `int allocate(int size)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `void free(int address)`
- 하는 일:
- 논리:
- 비용(왜):

### `int capacity()` / `int usedBytes()` / `int freeBytes()`
- 하는 일:
- 논리:
- 비용(왜):

### `int largestFreeBlock()` / `int freeBlockCount()` / `int wastedBytes()`
- 하는 일:
- 논리:
- 비용(왜):

### `int ignoredFrees()`
- 하는 일:
- 논리:
- 비용(왜):

### `void reset()`
- 하는 일:
- 논리:
- 비용(왜):

### `String toString()`
- 하는 일:
- 논리:
- 비용(왜):

## 구현 — FreeListAllocator (`src/main/java/com/datastructure/allocator/FreeListAllocator.java`)

### 필드
- `capacity` — 역할:
- `free` — 역할:
- `allocated` — 역할:
- `scanned` — 역할:
- `Block.start` / `Block.size` / `Block.end()` — 역할:

### `FreeListAllocator(int capacity)` (protected)
- 하는 일:
- 논리:
- 비용(왜):

### `abstract int choose(List<Block> blocks, int size)` (protected)
- 하는 일:
- 논리:
- 비용(왜):

### `int allocate(int size)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `void free(int address)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `void insertAndCoalesce(Block block)` (TODO, private)
- 하는 일:
- 논리:
- 비용(왜):

### `int capacity()` / `int usedBytes()` / `int freeBytes()`
- 하는 일:
- 논리:
- 비용(왜):

### `int largestFreeBlock()` / `int freeBlockCount()` / `int wastedBytes()`
- 하는 일:
- 논리:
- 비용(왜):

### `long scanned()` / `void countScan(long n)` (protected)
- 하는 일:
- 논리:
- 비용(왜):

### `List<String> freeBlocks()`
- 하는 일:
- 논리:
- 비용(왜):

### `static void requireSize(int size)` (protected)
- 하는 일:
- 논리:
- 비용(왜):

## 구현 — FirstFitAllocator (`src/main/java/com/datastructure/allocator/FirstFitAllocator.java`)

### 필드
- 없음 — `FreeListAllocator` 의 상태를 그대로 쓴다.

### `FirstFitAllocator(int capacity)`
- 하는 일:
- 논리:
- 비용(왜):

### `int choose(List<Block> blocks, int size)` (TODO, protected)
- 하는 일:
- 논리:
- 비용(왜):

### `String toString()`
- 하는 일:
- 논리:
- 비용(왜):

## 구현 — BestFitAllocator (`src/main/java/com/datastructure/allocator/BestFitAllocator.java`)

### 필드
- 없음 — `FreeListAllocator` 의 상태를 그대로 쓴다.

### `BestFitAllocator(int capacity)`
- 하는 일:
- 논리:
- 비용(왜):

### `int choose(List<Block> blocks, int size)` (TODO, protected)
- 하는 일:
- 논리:
- 비용(왜):

### `String toString()`
- 하는 일:
- 논리:
- 비용(왜):

## 구현 — WorstFitAllocator (`src/main/java/com/datastructure/allocator/WorstFitAllocator.java`)

### 필드
- 없음 — `FreeListAllocator` 의 상태를 그대로 쓴다.

### `WorstFitAllocator(int capacity)`
- 하는 일:
- 논리:
- 비용(왜):

### `int choose(List<Block> blocks, int size)` (TODO, protected)
- 하는 일:
- 논리:
- 비용(왜):

### `String toString()`
- 하는 일:
- 논리:
- 비용(왜):

## 구현 — BuddyAllocator (`src/main/java/com/datastructure/allocator/BuddyAllocator.java`)

### 필드
- `capacity` — 역할:
- `levels` — 역할:
- `freeByLevel` — 역할:
- `allocated` — 역할:
- `splits` — 역할:
- `merges` — 역할:

### `BuddyAllocator(int capacity)`
- 하는 일:
- 논리:
- 비용(왜):

### `int allocate(int size)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `void free(int address)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `int levelFor(int size)` (TODO, private)
- 하는 일:
- 논리:
- 비용(왜):

### `int capacity()` / `int usedBytes()` / `int freeBytes()`
- 하는 일:
- 논리:
- 비용(왜):

### `int largestFreeBlock()` / `int freeBlockCount()` / `int wastedBytes()`
- 하는 일:
- 논리:
- 비용(왜):

### `long splits()` / `long merges()`
- 하는 일:
- 논리:
- 비용(왜):

### `List<Integer> freeCountsByLevel()`
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
| BumpAllocator | | | |
| FirstFitAllocator | | | |
| BestFitAllocator | | | |
| WorstFitAllocator | | | |
| BuddyAllocator | | | |

## 핵심 문장

<!-- 지도 수준의 문장들 — 세부가 아니라 "왜 이 구조인가"를 담은 문장 -->

-
-
-

## 관련 자료

- 원본 README: `/home/jun/project/myway/data-structure/35-allocator/README.md`
- 구현 대상: `/home/jun/project/myway/data-structure/35-allocator/src/main/java/com/datastructure/allocator/`
- 테스트: `/home/jun/project/myway/data-structure/35-allocator/src/test/java/com/datastructure/allocator/`
- 정답 구현: `/home/jun/project/myway/data-structure/35-allocator/impl/`
