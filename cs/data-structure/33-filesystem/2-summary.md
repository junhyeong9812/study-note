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

### 동작 — 경로 정규화

```
normalize(path) : 조각을 스택에 쌓으며 걷는다. 절대 경로만 받는다 ("/" 로 시작 안 하면 예외)

  입력           조각 훑기                  규칙                     결과
  "//a///b"      "" a "" "" b              빈 조각은 버린다      ->  "/a/b"
  "/a/b/"        a b ""                    후행 슬래시도 빈 조각 ->  "/a/b"
  "/a/./b"       a . b                     "." 은 제자리         ->  "/a/b"
  "/a/b/.."      a b ..                    ".." 은 한 칸 pop     ->  "/a"
  "/.."          ..                        스택이 비었으면 무시  ->  "/"
  "/a/../.."     a .. ..                   올라갈 곳 없으면 머문다 -> "/"

  스택으로 보면 : normalize("/a/b/../c")
      "a"   ->  [ a ]
      "b"   ->  [ a | b ]
      ".."  ->  [ a ]            (마지막 칸을 뺀다)
      "c"   ->  [ a | c ]
      비었으면 "/" , 아니면 "/" + 조각을 "/" 로 이음   ->   "/a/c"

  파생 연산 (전부 split 을 거친다 - 문자열을 그냥 자르지 않는다)
      split("/a/b")     = [ "a", "b" ]      루트는 빈 목록
      parent("/a/b")    = "/a"              루트의 부모는 루트
      name("/a/b")      = "b"               루트의 이름은 빈 문자열
      join("/", "a")    = "/a"              루트에 이을 때 슬래시가 겹치면 안 된다
      isAncestorOrSame("/a", "/ab") = false

  왜 자르지 않고 split 을 거치나
      parent("/a/b/..") 를 문자열로 자르면 "/a/b" 가 나온다 (정규화 전 모양을 자른 것)
      isAncestorOrSame 을 startsWith 로 하면 "/ab" 가 "/a" 의 자손으로 잡힌다
      -> 둘 다 조각 목록 단위로 비교해야 한다

비용: 경로 길이에 비례 O(L). 조각 수 d 만큼 스택 push/pop.
```

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

### 구조

```
TreeFileSystem
+------------------------------------------------------+
| root = Node.directory("")   (루트, 이름은 빈 문자열) |
| visitedNodes / rewrittenEntries  (측정용 카운터)     |
+-----|------------------------------------------------+
      v
  Node ""  (dir)  children = TreeMap<이름, Node>
  +---------+---------+
  |  "a"    |  "log"  |
  +----|----+----|----+
       |         +--------> Node "log" (file) ---> Blob{ content="...", links=1 }
       v
  Node "a" (dir)
  +---------+
  |  "b"    |
  +----|----+
       v
  Node "b" (dir)
  +-----------+
  | "f.txt"   |
  +-----|-----+
        v
  Node "f.txt" (file) ---> Blob{ content="hi", links=1 }

담고 있는 파일 시스템 :  /a/b/f.txt , /log

Node 필드
  name      자기 이름 조각 하나만 ("f.txt"). 전체 경로를 들고 있지 않다
  children  디렉터리면 TreeMap, 파일이면 null   ->  isDirectory() 는 children != null
  blob      파일이면 Blob, 디렉터리면 null
  TreeMap 인 이유: 순회가 이름 오름차순이라 ls 결과가 하나로 정해진다 (HashMap 이면 안 정해짐)

Blob 필드 (이름과 내용의 분리 = inode)
  content   내용 문자열
  links     이 내용을 가리키는 이름의 수. 하드 링크로 둘 이상이 될 수 있다
            0 이 되는 순간에만 내용이 죽는다
```

### 동작 — 경로 해석

```
lookup("/a/b/f.txt")
  Paths.split -> [ "a", "b", "f.txt" ]  로 쪼갠 뒤 루트부터 한 칸씩 내려간다

  current = root                        visitedNodes = 1
     |   children().get("a")
     v
  Node "a"                              visitedNodes = 2
     |   children().get("b")
     v
  Node "b"                              visitedNodes = 3
     |   children().get("f.txt")
     v
  Node "f.txt"   <- 결과                 visitedNodes = 4

못 찾는 두 경우 (둘 다 null 을 돌려준다)
  [1] 조각이 없다        lookup("/a/x")    "a" 의 children 에 "x" 없음        -> null
  [2] 파일을 뚫으려 한다  lookup("/log/x")  "log" 는 isDirectory() false      -> null

비용 = 깊이 d 번 내려가며 매번 자식 맵 조회 = O(d * log k)   (k = 그 디렉터리의 자식 수)
       평면 맵의 해시 1회와 대비되는 자리다. 깊이가 얕으면 이 비용만 남는다.
```

### 동작 — mkdir(부모 생성)

```
[1] mkdir("/a/b/c") : 부모가 이미 있어야 한다. 중간 디렉터리를 자동으로 만들지 않는다.

    before                    mkdir("/a/b/c")
      /                       requireParent -> lookup("/a/b") == null
      +-- a                     -> IllegalArgumentException("없는 경로다: /a/b")

    after = before 그대로. 절반만 만들어 두는 일이 없다.
    (부모는 있는데 이름이 이미 쓰이고 있으면 -> "이미 있다" 예외)

[2] mkdirs("/a/b/c") : 없는 중간 디렉터리를 내려가며 만든다

    before                ->        after
      /                              /
      +-- a                          +-- a
                                          +-- b        <- 새로 만듦
                                               +-- c   <- 새로 만듦

    루트부터 조각마다
        children().get(part) == null  ->  Node.directory(part) 를 put 하고 그리로 내려간다
        이미 디렉터리면                ->  그냥 내려간다 (있어도 예외가 아니다)
        중간이 파일이면                ->  "경로 중간이 파일이다" 예외

비용: mkdir = 부모까지 d-1 칸 내려가기 + put 1회 = O(d * log k)
      mkdirs = 조각마다 get 또는 put 1회 = O(d * log k)
```

### 동작 — 삭제(재귀)

```
rmr("/a") : 부모의 children 에서 링크 하나만 끊으면 서브트리 전체가 사라진다

  before                                after
    /                                     /
    +-- a        <- parent.children["a"]  +-- log
    |    +-- b                                     ("a" 아래 4 개가 통째로 떨어져 나감)
    |    |    +-- f.txt
    |    +-- g.txt
    +-- log

  parent.children().remove("a")     <- 이 한 줄. 아래에 몇 개가 있든 상관없다
  releaseAll(a)                     <- 그 뒤 서브트리를 돌며 각 파일의 Blob.links 를 하나씩 내린다
                                       (링크를 끊었다고 Blob 참조 수가 저절로 줄지는 않는다.
                                        0 이 되어야 내용이 죽는다 - 하드 링크 때문)

  좁은 삭제 둘
    rm("/log")     파일만. 디렉터리면 예외. remove 후 blob().release()
    rmdir("/a/b")  빈 디렉터리만. children 이 비어 있지 않으면 예외

비용: 트리에서 떼어내는 것 자체는 O(1) 링크 하나.
      releaseAll 이 서브트리 m 개를 훑으므로 전체 O(m). 평면 맵은 여기서 전체 키 n 을 훑는다.
```

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

### 구조

```
FlatPathFileSystem
+---------------------------------------------------------------------+
| entries : HashMap<전체 경로 문자열, Blob>                           |
|   값이 null 이면 디렉터리, null 이 아니면 파일이다                  |
|   생성자에서 "/" -> null 을 미리 넣어둔다 (루트는 항상 있다)        |
+---------------------------------------------------------------------+

  키               값
  +--------------+---------------------------+
  | "/"          | null                (dir) |
  | "/a"         | null                (dir) |
  | "/a/b"       | null                (dir) |
  | "/a/b/f.txt" | Blob{ "hi", links=1 }     |
  | "/log"       | Blob{ "...", links=1 }    |
  +--------------+---------------------------+

같은 파일 시스템을 트리로 그리면 (위 TreeFileSystem 구조와 같은 내용)

    /
    +-- a
    |    +-- b
    |         +-- f.txt
    +-- log

차이는 하나다 : 부모-자식 관계가 어디에도 안 적혀 있다. 오직 키 문자열 안에만 있다.
  트리   "a" 의 children 을 보면 자식이 바로 나온다
  평면   자식을 알려면 모든 키의 parent 를 계산해 봐야 한다
```

### 동작 — 조회 / 디렉터리 나열

```
[1] 조회 exists("/a/b/f.txt") / read(...) : 해시 한 번
        "/a/b/f.txt" --(hash)--> 값 있음 -> true            O(1). 깊이와 무관하다.
        트리는 같은 일에 4 칸을 내려간다. 깊은 경로를 열기만 한다면 이쪽이 이긴다.

[2] 나열 ls("/a") : 관계가 없으므로 전체 키를 훑어 되살린다
        키              Paths.parent(키)     "/a" 인가
        "/"             "/"                  아니오
        "/a"            "/"                  자기 자신이라 제외
        "/a/b"          "/a"                 예  -> "b" 를 담는다
        "/a/b/f.txt"    "/a/b"               아니오
        "/log"          "/"                  아니오
        HashMap 순회 순서는 정해져 있지 않으므로 마지막에 out.sort(null) 로 정렬한다
        자식 하나를 얻으려고 항목 n 개를 전부 본다.

[3] 재귀 삭제 rmr("/a") / size / find : 역시 전체 키를 훑는다
        Paths.isAncestorOrSame("/a", 키) 인 키를 모아서 지운다
        키.startsWith("/a") 로 하면 "/ab" 까지 끌려간다 -> 조각 단위 비교가 필요한 이유

[4] 디렉터리 mv("/a", "/z") : 경로가 키라서 아래 키를 전부 다시 쓴다
        "/a"          -> "/z"
        "/a/b"        -> "/z/b"          rewrittenEntries += 1 씩
        "/a/b/f.txt"  -> "/z/b/f.txt"
        트리는 링크 하나만 고치고 rewrittenEntries = 1 로 끝낸다. 답은 같고 일이 다르다.

비용 대비
  연산                TreeFileSystem              FlatPathFileSystem
  조회/읽기           O(d log k)  깊이만큼 내려감    O(1)  해시 한 번
  ls                  O(k)  자식 맵만              O(n)  전체 키 훑기 + 정렬
  size / find / rmr   O(m)  서브트리만             O(n)  전체 키 훑기
  디렉터리 mv         O(1)  링크 하나              O(m)  아래 키 전부 재기록
    d = 깊이, k = 자식 수, m = 서브트리 크기, n = 전체 항목 수
```

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
