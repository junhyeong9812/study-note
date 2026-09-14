# data-structure/33-filesystem — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.
> 2026-09-14: 쉽게 풀어쓴 확장(Claude 작성) — 한눈에 절·동작 그림·용어 풀이 추가.

## 한눈에 — 쉽게 말하면

**비유: 물건을 정리하는 두 방식 — 서랍장 안의 서랍(트리) vs 이름표 붙인 보관함 목록(평면 맵).**

- 파일 시스템은 "폴더 안에 폴더, 그 안에 파일"을 저장하고 만들기/읽기/지우기/옮기기를 해 주는 자료구조다.
- 방법 1(트리): 진짜 서랍장처럼, 폴더 노드가 자식들을 직접 들고 있다. `/a/b/f.txt`를 열려면 루트에서 a → b → f.txt로 한 칸씩 내려간다.
- 방법 2(평면 맵): 서랍은 없고, "전체 경로 문자열 → 내용" 표 하나만 둔다. 열기는 표에서 한 번 찾으면 끝(빠르다). 대신 "이 폴더의 자식 누구?"는 표 전체를 뒤져야 안다.
- 둘 다 계약(FileSystem)은 같아서 답이 같다 — 다른 것은 각 연산의 **비용**이다. 이 대비가 이 문제의 요점이다.
- 이름과 내용을 분리해(Blob), 한 내용에 이름표를 여러 개 붙일 수 있다(하드 링크). 이름표가 다 떨어져야(links=0) 내용이 죽는다.

```text
  [트리]  폴더가 자식을 직접 안다        [평면 맵]  경로 문자열이 통째로 키
      /                                  +--------------+------+
      +-- a                              | "/a"         | dir  |
      |    +-- f.txt                     | "/a/f.txt"   | Blob |
      +-- log                            | "/log"       | Blob |
                                         +--------------+------+
```

이 두 방식과 **똑같은 구조**가 실무에 다 있다 — 리눅스/유닉스 파일 시스템(inode)이 트리 방식이고, Amazon S3 같은 객체 저장소가 "경로 문자열 = 키"인 평면 방식이다(S3에 폴더가 "진짜로는 없는" 이유).

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

언제 쓰나: 모든 연산의 맨 앞 — 사용자가 준 지저분한 경로("//a///b/../c")를 표준 모양 하나로 통일한다. 같은 곳을 가리키는 경로는 같은 문자열이 되어야 그다음 비교·조회가 성립한다. 아래 그림은 조각을 스택에 쌓으며 걷는 규칙표와, ".."가 스택에서 한 칸 빼는 모습이다.

  - *정규화(normalize)*: 여러 가지로 쓸 수 있는 표현을 표준 형태 하나로 바꾸는 것.
  - *스택(stack)*: 접시 쌓기처럼 위로만 넣고(push) 위에서만 빼는(pop) 자료구조. ".." = 맨 위 접시 하나 빼기.

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

언제 쓰나: 트리 방식에서 경로 문자열을 실제 노드로 바꾸는 모든 연산의 공통 관문(lookup). 아래 그림은 `/a/b/f.txt`를 조각으로 쪼갠 뒤 루트에서 한 칸씩 내려가는 과정 — 계단을 한 층씩 내려가는 것과 같고, 층수(visitedNodes)를 센다.

  - *노드(Node)*: 트리의 칸 하나. 폴더거나 파일이다.
  - *null*: 자바에서 "없음"을 뜻하는 값. 여기서는 "그런 경로 없음"의 신호로 쓴다.

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

언제 쓰나: 폴더 만들기. 엄격한 것(`mkdir` — 부모가 이미 있어야 함)과 너그러운 것(`mkdirs` — 없는 중간 폴더를 다 만들어 줌) 두 가지다. 아래 그림 [1]은 mkdir이 실패할 때 "절반만 만들어 두는 일이 없다"는 것, [2]는 mkdirs가 내려가며 없는 칸을 채우는 전/후다.

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

언제 쓰나: 폴더를 통째로 지울 때(`rmr`). 트리에서는 부모가 쥔 고리 하나만 끊으면 가지 전체가 떨어져 나간다 — 나뭇가지를 꺾으면 그 끝의 잎이 다 같이 떨어지는 것과 같다. 아래 그림은 그 한 줄(remove)과, 그 뒤 잎(파일)마다 Blob의 링크 수를 내리는 뒷정리(releaseAll)다.

  - *재귀(recursion)*: 자기 자신을 반복해 부르는 방식. "폴더를 지운다 = 자식 폴더마다 또 같은 지우기를 한다".
  - *서브트리(subtree)*: 어떤 노드와 그 아래 전부를 묶어 부르는 말(가지 하나).

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

언제 보나: 평면 맵 방식의 밝음과 어두움이 한 절에 다 있다. [1] 조회는 해시 한 번(깊이 무관, 트리보다 빠르다). [2]~[4]는 그 대가 — 부모-자식 관계가 키 문자열 안에만 있어서, 자식 나열·재귀 삭제·폴더 이동이 전부 "전체 키 훑기"가 된다. 마지막 비용 대비 표가 이 문제의 결론이다.

  - *해시 조회*: 키 문자열을 숫자로 바꿔 표의 칸을 바로 찾는 것. 항목이 몇 개든 한 번에 O(1).
  - *재기록(rewrittenEntries)*: 폴더 이동 때 경로가 키라서 아래 키들을 전부 지우고 새 키로 다시 넣는 일. 그 횟수를 세는 계수기.

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

## 용어 풀이

- **트리(tree)**: 뿌리(루트)에서 가지가 갈라져 내려가는 구조. 폴더 안의 폴더가 정확히 이 모양이다.
- **루트(root)**: 트리의 맨 꼭대기. 여기서는 경로 `/`.
- **노드(node)**: 트리의 칸 하나 — 폴더(디렉터리)거나 파일.
- **서브트리(subtree)**: 한 노드와 그 아래 전부(가지 하나).
- **경로(path)**: 루트부터 목적지까지의 주소 문자열(`/a/b/f.txt`).
- **정규화(normalize)**: 여러 표기(`//a/./b/..`)를 표준 형태 하나로 통일하는 것.
- **스택(stack)**: 위로만 넣고 위에서만 빼는 자료구조. 경로의 `..` 처리가 "맨 위 하나 빼기"다.
- **재귀(recursion)**: 자기 자신을 반복해 부르는 방식. 폴더 지우기·크기 재기·찾기가 전부 재귀다.
- **inode**: 유닉스 파일 시스템에서 "이름"과 "실제 내용·정보"를 분리해 두는 구조. 이 구현의 Blob이 그 역할이다.
- **Blob**: 파일의 실제 내용 + 그 내용을 가리키는 이름 수(links)를 담은 상자.
- **하드 링크(hard link)**: 같은 내용(Blob)에 이름표(경로)를 하나 더 붙이는 것. 한쪽 이름을 지워도 내용은 남고, 이름 수가 0이 되어야 내용이 죽는다.
- **참조 계수(links)**: 무언가를 가리키는 손가락의 수를 세어 두고, 0이 되면 치우는 관리 방식.
- **HashMap / TreeMap**: 자바의 표(맵). HashMap은 순서 없이 빠르고(O(1)), TreeMap은 항상 키 정렬 순서를 유지한다(O(log n)) — ls 결과가 하나로 정해지려면 TreeMap.
- **해시(hash)**: 문자열을 숫자로 바꿔 표의 칸을 바로 찾게 하는 함수.
- **null**: 자바의 "없음" 값. 여기서는 "그런 경로 없음"(lookup), "파일 아님"(children) 등의 신호.
- **O(1) / O(log k) / O(d) / O(m) / O(n)**: 걸리는 시간의 규모. 각각 일정 / 자식 수 k의 로그 / 깊이 d에 비례 / 서브트리 크기 m에 비례 / 전체 항목 수 n에 비례.
- **IllegalArgumentException**: 자바에서 "잘못된 입력이다"를 알리는 예외(에러 신호).
- **깊은 복사(deep copy)**: 겉상자만 복사하는 게 아니라 안의 내용물까지 전부 새로 복사하는 것. `cp`가 이것이다.
- **계약(인터페이스)**: 두 구현(트리/평면)이 똑같이 지키는 메서드 목록(FileSystem). 답은 같고 비용만 다르다.
- **계수기(visitedNodes / rewrittenEntries)**: 정답 여부가 아니라 "일을 얼마나 했나"를 재는 측정용 카운터.

## 관련 자료

- 원본 README: `/home/jun/project/myway/data-structure/33-filesystem/README.md`
- 구현 대상: `/home/jun/project/myway/data-structure/33-filesystem/src/main/java/com/datastructure/filesystem/`
- 테스트: `/home/jun/project/myway/data-structure/33-filesystem/src/test/java/com/datastructure/filesystem/`
- 정답 구현: `/home/jun/project/myway/data-structure/33-filesystem/impl/`
