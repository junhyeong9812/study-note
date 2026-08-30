# data-structure/33-filesystem — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.

## 전체 흐름

<!-- 이 자료구조가 동작하는 원리를 자기 말로 -->

## 계약 — FileSystem (`src/main/java/com/datastructure/filesystem/FileSystem.java`)

- `void mkdir(String path)`
- `void mkdirs(String path)`
- `void touch(String path)`
- `void write(String path, String content)`
- `String read(String path)`
- `List<String> ls(String path)`
- `void rm(String path)`
- `void rmdir(String path)`
- `void rmr(String path)`
- `void mv(String src, String dst)`
- `void cp(String src, String dst)`
- `boolean exists(String path)`
- `boolean isDirectory(String path)`
- `long size(String path)`
- `List<String> find(String path, String name)`
- `void link(String existingPath, String newPath)`
- `int linkCount(String path)`

## 계약 — FsStats (`src/main/java/com/datastructure/filesystem/FsStats.java`)

- `long visitedNodes()`
- `long rewrittenEntries()`

## 보조 — TODO 없는 값·부품 클래스

- `Blob` (`Blob.java`) — 역할:
- `Node` (`Node.java`) — 역할:

## 구현 — Paths (`src/main/java/com/datastructure/filesystem/Paths.java`)

### 필드
- `ROOT` — 역할:

### `static String normalize(String path)` (TODO 1)
- 하는 일:
- 논리:
- 비용(왜):

### `static List<String> split(String path)` (TODO 2)
- 하는 일:
- 논리:
- 비용(왜):

### `static String parent(String path)` (TODO 3)
- 하는 일:
- 논리:
- 비용(왜):

### `static String name(String path)`
- 하는 일:
- 논리:
- 비용(왜):

### `static String join(String parent, String name)` (TODO 4)
- 하는 일:
- 논리:
- 비용(왜):

### `static boolean isAncestorOrSame(String ancestor, String path)` (TODO 5)
- 하는 일:
- 논리:
- 비용(왜):

## 구현 — TreeFileSystem (`src/main/java/com/datastructure/filesystem/TreeFileSystem.java`)

### 필드
- `root` — 역할:
- `visitedNodes` — 역할:
- `rewrittenEntries` — 역할:

### `Node lookup(String path)` (TODO 6, private)
- 하는 일:
- 논리:
- 비용(왜):

### `void mkdir(String path)` (TODO 7)
- 하는 일:
- 논리:
- 비용(왜):

### `void mkdirs(String path)` (TODO 8)
- 하는 일:
- 논리:
- 비용(왜):

### `void touch(String path)`
- 하는 일:
- 논리:
- 비용(왜):

### `void write(String path, String content)` (TODO 9)
- 하는 일:
- 논리:
- 비용(왜):

### `String read(String path)`
- 하는 일:
- 논리:
- 비용(왜):

### `List<String> ls(String path)` (TODO 10)
- 하는 일:
- 논리:
- 비용(왜):

### `boolean exists(String path)` / `boolean isDirectory(String path)`
- 하는 일:
- 논리:
- 비용(왜):

### `long size(String path)`
- 하는 일:
- 논리:
- 비용(왜):

### `long sizeOf(Node node)` (TODO 11, private)
- 하는 일:
- 논리:
- 비용(왜):

### `List<String> find(String path, String name)`
- 하는 일:
- 논리:
- 비용(왜):

### `void collect(Node node, String here, String name, List<String> out)` (TODO 12, private)
- 하는 일:
- 논리:
- 비용(왜):

### `void rm(String path)` (TODO 13)
- 하는 일:
- 논리:
- 비용(왜):

### `void rmdir(String path)`
- 하는 일:
- 논리:
- 비용(왜):

### `void rmr(String path)`
- 하는 일:
- 논리:
- 비용(왜):

### `void releaseAll(Node node)` (TODO 14, private)
- 하는 일:
- 논리:
- 비용(왜):

### `void mv(String src, String dst)` (TODO 15)
- 하는 일:
- 논리:
- 비용(왜):

### `Node rename(Node node, String newName)` (TODO 16, private)
- 하는 일:
- 논리:
- 비용(왜):

### `void cp(String src, String dst)`
- 하는 일:
- 논리:
- 비용(왜):

### `Node deepCopy(Node node, String newName)` (TODO 17, private)
- 하는 일:
- 논리:
- 비용(왜):

### `void link(String existingPath, String newPath)` (TODO 18)
- 하는 일:
- 논리:
- 비용(왜):

### `int linkCount(String path)`
- 하는 일:
- 논리:
- 비용(왜):

### `long visitedNodes()` / `long rewrittenEntries()`
- 하는 일:
- 논리:
- 비용(왜):

### `String toString()`
- 하는 일:
- 논리:
- 비용(왜):

## 구현 — FlatPathFileSystem (`src/main/java/com/datastructure/filesystem/FlatPathFileSystem.java`)

### 필드
- `entries` (`Map<String, Blob>`) — 역할:
- `visitedNodes` — 역할:
- `rewrittenEntries` — 역할:

### `FlatPathFileSystem()`
- 하는 일:
- 논리:
- 비용(왜):

### `void mkdir(String path)`
- 하는 일:
- 논리:
- 비용(왜):

### `void mkdirs(String path)`
- 하는 일:
- 논리:
- 비용(왜):

### `void touch(String path)`
- 하는 일:
- 논리:
- 비용(왜):

### `void write(String path, String content)`
- 하는 일:
- 논리:
- 비용(왜):

### `String read(String path)`
- 하는 일:
- 논리:
- 비용(왜):

### `List<String> ls(String path)` (TODO 19)
- 하는 일:
- 논리:
- 비용(왜):

### `boolean exists(String path)` / `boolean isDirectory(String path)`
- 하는 일:
- 논리:
- 비용(왜):

### `long size(String path)` (TODO 20)
- 하는 일:
- 논리:
- 비용(왜):

### `List<String> find(String path, String name)` (TODO 21)
- 하는 일:
- 논리:
- 비용(왜):

### `void rm(String path)`
- 하는 일:
- 논리:
- 비용(왜):

### `void rmdir(String path)`
- 하는 일:
- 논리:
- 비용(왜):

### `void rmr(String path)` (TODO 22)
- 하는 일:
- 논리:
- 비용(왜):

### `void mv(String src, String dst)` (TODO 23)
- 하는 일:
- 논리:
- 비용(왜):

### `void cp(String src, String dst)` (TODO 24)
- 하는 일:
- 논리:
- 비용(왜):

### `void link(String existingPath, String newPath)` (TODO 25)
- 하는 일:
- 논리:
- 비용(왜):

### `int linkCount(String path)`
- 하는 일:
- 논리:
- 비용(왜):

### `long visitedNodes()` / `long rewrittenEntries()` / `int entryCount()`
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
| TreeFileSystem | | | |
| FlatPathFileSystem | | | |

## 핵심 문장

<!-- 지도 수준의 문장들 — 세부가 아니라 "왜 이 구조인가"를 담은 문장 -->

-
-
-

## 관련 자료

- 원본 README: `/home/jun/project/myway/data-structure/33-filesystem/README.md`
- 구현 대상: `/home/jun/project/myway/data-structure/33-filesystem/src/main/java/com/datastructure/filesystem/`
- 테스트: `/home/jun/project/myway/data-structure/33-filesystem/src/test/java/com/datastructure/filesystem/`
- 정답 구현: `/home/jun/project/myway/data-structure/33-filesystem/impl/`
