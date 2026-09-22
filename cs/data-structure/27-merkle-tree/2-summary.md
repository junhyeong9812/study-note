# data-structure/27-merkle-tree — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.
> 2026-09-14: 쉽게 풀어쓴 확장(Claude 작성) — 한눈에 절·동작 그림·용어 풀이 추가.

## 한눈에 — 쉽게 말하면

**비유: 지문의 지문.** 두꺼운 책이 진짜인지 확인하려고 매번 전부 읽을 수는 없다.
페이지마다 지문(짧은 요약값)을 뜨고, 지문 두 개를 붙여 또 지문을 뜨고… 를 반복하면 맨 위에 지문 하나가 남는다.
페이지 한 장만 바뀌어도 그 위의 지문들이 연쇄적으로 바뀌어 맨 위 지문이 달라진다.
그래서 **맨 위 지문 하나만 믿을 수 있으면** 책 전체가 안 바뀌었는지 알 수 있다.
  - *해시(hash)*: 어떤 데이터든 넣으면 짧은 고정 길이 값이 나오는 함수. 내용이 조금만 달라도 값이 완전히 달라진다 — 이 문서의 "지문"이 곧 해시다.

```text
  블록:   [A]    [B]    [C]    [D]
           |      |      |      |
  지문:   h(A)   h(B)   h(C)   h(D)      <- 잎(맨 아래층)
             \   /         \   /
            h(AB)          h(CD)         <- 지문 둘을 합쳐 또 지문
                 \         /
                루트 h(ABCD)             <- 이 값 하나로 전체를 검증한다
```

머클 트리가 **똑같은 구조다**: 블록(데이터 조각)마다 해시를 뜨고, 둘씩 묶어 위로 올려 루트 해시 하나를 만든다.
실무에서 git 의 커밋, 비트코인 블록, rsync 의 파일 동기화, 인증서 투명성(CT) 로그가 전부 이 구조로 "전체를 안 보고 일부만 보고 믿는" 일을 한다.

## 문제 — 이 챕터가 시키는 것

원본 README는 01~26번이 전부 "**무엇이 들어 있나**"에 답했다면 27번은 "**이게 그대로인가**"에 답하는 상자라고 소개한다.\
해시 하나로 요약하면 같은지는 알지만 **다를 때 어디가 다른지를 모른다** — 머클 트리는 잎에 블록 해시를 두고 둘씩 합쳐 올려, 뿌리 하나로 전체를 요약하고 다르면 **O(log n)** 만에 어느 블록인지 찾는다.\
더 중요한 것은 포함 증명이다 — "3번 블록이 이 파일에 들어 있다"를 증명하는 데 파일이 필요 없고 경로의 형제 해시 log n 개면 된다(100만 블록이면 해시 20개).\
그리고 이 상자는 **걸음 수를 세는 것**이 과제의 절반이다 — 건너뛰기를 빼도 답은 똑같이 맞기 때문에 정답과 오답이 답으로는 안 갈린다.

과제 목록 — `src/main/java/com/datastructure/merkle/`의 TODO 9개:

- `PrefixedHashing` — TODO 1(`leafHash` — 0x00 을 앞에 붙여 해시) · TODO 2(`nodeHash` — 0x01 + 자식 둘 이어붙여 해시)
- `MerkleTree` — TODO 3(`build` — 잎 층을 만들고 하나 남을 때까지 위로 접기, 짝 없는 노드는 **승격**) · TODO 4(`proofFor` — 잎에서 뿌리까지 올라가며 형제와 방향을 줍기) · TODO 5(`findFirstDifference` — 뿌리부터 한 갈래로 내려가기) · TODO 6(`withLeafReplaced` — 층 배열 얕은 복사 + 경로만 재계산)
- `MerkleProof` — TODO 7(`verify` — 걸음을 방향대로 합쳐 올라가 뿌리와 견주기)
- `MerkleProblems` — TODO 8(`diffBlocks` — 같은 부분트리는 통째로 건너뛰기) · TODO 9(`verifyBatch` — 하나라도 틀리면 false)

순서: `MerkleTreeTest.java`를 먼저 따라 친다 → `PrefixedHashing` 2개 → `MerkleTree` 4개 → `MerkleProof` 1개 → `MerkleProblems` 2개.\
실행: `cd ~/project/myway/data-structure && ./run.sh 27` — README 기준 **79개 중 75개가 실패**한다.

아래 서머리는 이 문제(README)를 분석·정리한 것이다.

## 전체 흐름

<!-- 이 자료구조가 동작하는 원리를 자기 말로 -->

## 계약 — HashFunction (`src/main/java/com/datastructure/merkle/HashFunction.java`)

- `byte[] hash(byte[] data)`

## 계약 — MerkleHashing (`src/main/java/com/datastructure/merkle/MerkleHashing.java`)

- `byte LEAF_PREFIX = 0x00` (상수)
- `byte NODE_PREFIX = 0x01` (상수)
- `byte[] leafHash(byte[] block)`
- `byte[] nodeHash(byte[] left, byte[] right)`
- `HashFunction function()`

## 보조 (TODO 없는 클래스)

- `UnprefixedHashing` (`src/main/java/com/datastructure/merkle/UnprefixedHashing.java`) — 역할:
- `Sha256Hash` (`src/main/java/com/datastructure/merkle/Sha256Hash.java`) — 역할:
- `ToyHash` (`src/main/java/com/datastructure/merkle/ToyHash.java`) — 역할:

## 구현 — PrefixedHashing (`src/main/java/com/datastructure/merkle/PrefixedHashing.java`)

### 구조

그림을 읽는 데 필요한 말 셋.
  - *바이트(byte)*: 컴퓨터가 다루는 데이터의 최소 단위 조각(8비트). 0x00, 0x01 은 바이트 하나를 16진수로 쓴 것이다.
  - *접두사(prefix)*: 데이터 맨 앞에 붙이는 표시. 여기서는 "이건 잎이다(0x00) / 내부다(0x01)"라는 딱지.
  - *잎(leaf) / 내부(internal) 노드*: 트리 맨 아래층의 노드(실제 블록의 해시) / 그 위층들의 노드(자식 해시 둘을 합친 해시).

```
PrefixedHashing (MerkleHashing 구현) - 접두사 한 바이트로 잎과 내부를 다른 값의 공간에 둔다

  leafHash(block)                       nodeHash(left, right)
  +------+-------------------+          +------+----------+----------+
  | 0x00 |      block        |          | 0x01 |   left   |  right   |
  +------+-------------------+          +------+----------+----------+
   LEAF_PREFIX  (원본 블록)               NODE_PREFIX  (자식 해시 둘, 순서대로)
       |                                     |
       v  function.hash(...)                 v  function.hash(...)
  +-----------+                         +-------------+
  |  잎 해시   |                         |  내부 해시   |
  +-----------+                         +-------------+

MerkleHashing.LEAF_PREFIX = 0x00 (상수) / NODE_PREFIX = 0x01 (상수)
버퍼 길이 : 잎 = 1 + block.length,  내부 = 1 + left.length + right.length
  (내부를 left.length * 2 + 1 로 잡아도 지금은 맞는다. 값이 아니라 "두 자식 길이가 같다"는
   가정에 기댄 줄이라 나중에 조용히 틀린다)
nodeHash(a, b) != nodeHash(b, a)  <- 좌우 순서가 값에 들어간다. 그래서 증명에 방향이 필요하다
```

### 동작 — 리프/내부 접두사

**언제 쓰나**: 잎 해시와 내부 해시를 만들 때마다, 항상. 접두사 한 바이트가 없으면 어떤 공격이 통하는지를 [1]이, 붙이면 왜 막히는지를 [2]가 보여준다.
  - *두 번째 원상 공격(second preimage attack)*: 같은 해시값이 나오는 "다른 입력"을 일부러 만들어내는 공격. 여기서는 내부 노드를 잎인 척 위장하는 것.
  - *RFC 6962*: 인증서 투명성(CT) 로그의 표준 문서. 이 접두사 규칙이 그 표준의 규칙이다.

```
[1] 접두사 없음 (UnprefixedHashing) - 잎과 내부가 같은 값의 공간에 산다
    잎   : hash( block )
    내부 : hash( left || right )
    ==>  leafHash(x || y)  ==  nodeHash(x, y)     (같은 입력이므로 같은 값이다)

    정직한 파일 (블록 4개)              공격자의 위조 파일 (블록 2개)
                                        블록0 = h(A) || h(B)   <- 64바이트짜리 "블록"인 척
      h(A) h(B)  h(C) h(D)              블록1 = h(C) || h(D)
        \   /      \   /                       |            |
      +-----+    +-----+                    leafHash      leafHash
      |h(AB)|    |h(CD)|                       |            |
      +-----+    +-----+                       v            v
          \       /                          h(AB)        h(CD)   <- 값이 정확히 같다
         +---------+                             \         /
         |  root   |            ==               +---------+
         +---------+                             |  root   |   <- 뿌리가 같다
                                                 +---------+
    블록 수도 내용도 다른데 뿌리가 같다. 그래서 있지도 않은 블록의 포함 증명이 통과한다
    두 번째 원상 공격(second preimage). SecondPreimageTest 가 실제로 성공시킨다

[2] 접두사 있음 (PrefixedHashing) - 두 공간이 갈라진다
    위조 블록의 잎 해시 = hash( 0x00 || h(A) || h(B) )
    진짜 내부 노드 해시 = hash( 0x01 || h(A) || h(B) )
                                ^^^^ 첫 바이트가 달라 두 집합이 절대 안 겹친다
    ==> 어떤 내부 노드도 잎으로 위장할 수 없다. 위조 뿌리가 진짜 뿌리와 달라진다

    비용은 해시 입력 1바이트. 그것뿐이다 (RFC 6962 인증서 투명성 로그가 쓰는 규칙)
    함정: 접두사를 빼도 계약 테스트는 거의 다 통과한다. 뿌리도 나오고 증명도 검증되고
          차이도 찾아진다. 딱 하나, 위장 위조만 못 막는다. "왜 있는지 모르겠는 한 줄"이 그것이다
```

### 필드
- `function` — 역할:

### `PrefixedHashing(HashFunction function)`
- 하는 일:
- 논리:
- 비용(왜):

### `byte[] leafHash(byte[] block)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `byte[] nodeHash(byte[] left, byte[] right)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `HashFunction function()`
- 하는 일:
- 논리:
- 비용(왜):

## 구현 — MerkleTree (`src/main/java/com/datastructure/merkle/MerkleTree.java`)

### 구조

이 트리는 노드 객체를 안 만든다. 층별 배열에 해시만 담고, 부모-자식 관계는 번호 계산으로만 안다.
  - *포인터/참조(reference)*: "그 객체가 어디 있는지"를 가리키는 값. 여기서는 그것조차 없이 배열 인덱스 산술(2j, 2j+1)로 자식을 찾는다.
  - *참조 비교 vs 내용 비교*: `a == b`(그리고 배열의 `.equals`)는 "같은 객체인가"만 본다. 바이트 내용이 같은지는 `Arrays.equals` 로 봐야 한다.

```
MerkleTree - levels[k][j] = k 층 j 번 노드의 해시. 노드 객체도 포인터도 없다 (07번 힙과 같은 발상)

  데이터 블록    B0        B1        B2        B3
                 |         |         |         |     leafHash = hash(0x00 || block)
                 v         v         v         v
  levels[0]   +------+  +------+  +------+  +------+
  (잎)        | h(A) |  | h(B) |  | h(C) |  | h(D) |     leafCount() = 4
              +------+  +------+  +------+  +------+
                 \        /         \        /        nodeHash = hash(0x01 || left || right)
                  \      /           \      /
  levels[1]      +---------+        +---------+
                 |  h(AB)  |        |  h(CD)  |
                 +---------+        +---------+
                       \               /
                        \             /
  levels[2]            +---------------+
  (뿌리)               |    h(ABCD)    |  = rootHash()      height() = 2
                       +---------------+

  levels : byte[][][]  층 배열. levels[0] 이 잎, 마지막 층이 뿌리 하나
  levels[k][j] 의 자식은 levels[k-1][2j] 와 levels[k-1][2j+1] - 자리를 인덱스 산술로만 안다
  hashAt(level, index) 는 내부 배열을 그대로 준다(무복사). rootHash()/leafHash() 는 복사본을 준다
  sameNode 는 Arrays.equals 로 비교한다. byte[].equals 는 참조 비교라 언제나 false 를 준다
    -> 답은 맞을 수 있는데 "전부 다르다"가 되어 끝까지 내려가고 O(log n) 이 사라진다
```

```
잎이 홀수일 때 - 짝 없는 마지막 노드를 그대로 위로 올린다(승격). 다시 해시하지 않는다

  잎 3개 [A, B, C]
  levels[0]  +------+  +------+  +------+
             | h(A) |  | h(B) |  | h(C) |
             +------+  +------+  +------+
                \        /          |      <- 짝이 없다. nodeHash 를 부르지 않고 참조를 올린다
                 \      /           |
  levels[1]     +---------+      +------+
                |  h(AB)  |      | h(C) |   <- levels[1][1] 은 levels[0][2] 와 같은 객체
                +---------+      +------+
                      \           /
  levels[2]        +--------------------+
                   | h( h(AB), h(C) )   |  = root
                   +--------------------+

  다음 층 길이 = (현재 길이 + 1) / 2   <- 올림 나눗셈. +1 을 빼면 마지막 노드를 잃는다
  다른 방법: 마지막 노드를 자기 자신과 짝지어 nodeHash(h(C), h(C)) (비트코인 방식)
    -> [a, b, c] 와 [a, b, c, c] 의 뿌리가 같아진다. CVE-2012-2459 다
       OddLeafCountTest 가 두 규칙의 값을 나란히 계산해 보여준다
  승격의 대가: 승격 노드는 부모와 해시가 같아 그 자리의 증명이 한 걸음 짧다
    -> 증명 길이가 잎마다 다르고, 그 자체가 어느 잎인지에 대한 정보를 조금 흘린다
  참조를 그대로 올리므로 withLeafReplaced 가 무엇을 새로 만들었는지 참조 비교로 셀 수 있다
```

### 동작 — 빌드

**언제 쓰나**: 블록 목록으로 트리를 처음 만들 때. 순서는 늘 같다 — 잎 층을 깔고([1]), 둘씩 접어 한 층 올리고([2]), 하나가 남을 때까지 반복([3]).

```
build(blocks, hashing) : 잎 층을 만들고 하나가 남을 때까지 위로 접는다. 잎 5개 예

  [1] 잎 층 - 블록마다 leafHash 를 부른다 (블록이 null 이면 몇 번째인지 메시지에 넣어 예외)
      B0 B1 B2 B3 B4
       v  v  v  v  v
      levels[0] = [ h(A), h(B), h(C), h(D), h(E) ]              길이 5

  [2] 한 층 접기 - i 번 노드의 자식은 2i 와 2i+1. 2i+1 이 없으면 승격
      levels[0]   [ h(A)  h(B) ] [ h(C)  h(D) ] [ h(E) ]
                     \    /         \    /        |
                      v  v            v  v         v (승격 - 참조 그대로)
      levels[1] = [ h(AB) ,        h(CD) ,       h(E) ]         길이 (5+1)/2 = 3

  [3] 길이가 1이 될 때까지 반복
      levels[1]   [ h(AB)  h(CD) ] [ h(E) ]
                      \      /        |
      levels[2] = [ h(ABCD) ,       h(E) ]                      길이 (3+1)/2 = 2
      levels[3] = [ h(ABCDE) ]  = 뿌리                          길이 (2+1)/2 = 1

  해시 호출 = 잎 n 번 + 내부 n-1 번 이하  -> O(n).  층 수 = ceil(log2 n) + 1
  잎이 1개면 반복문이 한 번도 안 돌고 그 잎 해시가 곧 뿌리다 (height() = 0)
  블록이 null 이거나 비어 있으면 IllegalArgumentException
    - 잎 0개짜리 트리는 뿌리가 없다. "빈 목록의 해시"는 프로토콜이 정할 일이지 자료구조가 몰래
      정할 일이 아니다
```

### 동작 — 갱신(1개 변경)

**언제 쓰나**: 블록 하나가 바뀌었을 때. 트리를 처음부터 다시 짓지 않고, 바뀐 잎에서 뿌리까지 가는 길만 다시 계산한다(26번의 경로 복사와 같은 발상).
그림 먼저 — 왼쪽이 전 상태, 오른쪽이 후 상태. `*` 붙은 것만 새로 계산했고 나머지는 공유한다.
  - *얕은 복사(shallow copy)*: 겉 배열만 새로 만들고, 안에 든 것들은 같은 객체를 그대로 가리키게 복사하는 것. `clone()` 이 그렇게 한다.

```
withLeafReplaced(2, X) : 바뀐 잎에서 뿌리까지 경로 위의 노드만 다시 계산한다 (26번 경로 복사)

  before                                  after (원본 트리는 그대로 살아 있다)

  levels[2]      h(ABCD)                  levels[2]      h(ABXD)   *새로 계산
                 /     \                                /     \
  levels[1]   h(AB)   h(CD)               levels[1]   h(AB)   h(XD)  *새로 계산
              /  \    /  \                            /  \    /  \
  levels[0] h(A) h(B) h(C) h(D)           levels[0] h(A) h(B) h(X) h(D)
                       ^                             공유 공유  *새  공유
                       이 잎이 바뀐다                            (leafHash(X))

  1. 층마다 levels[k].clone() - 참조 배열만 얕게 복사한다 (byte[] 안의 값은 안 복사)
  2. copy[0][2] = hashing.leafHash(newBlock)
  3. 위로 올라가며 parent = index / 2 를 다시 계산한다
       부모의 자식은 2*parent 와 2*parent+1. 내 형제는 안 바뀌었으니 그대로 읽는다
       오른쪽 자식이 없으면 승격이므로 왼쪽 자식 참조를 그대로 올린다
  4. private 생성자로 새 트리를 만든다

  해시 재계산 = 경로 길이 = height() = O(log n).  잎 1024개면 2047번 -> 11번
  경로 밖의 노드는 옛 트리와 같은 객체를 공유한다. 안전한 이유는 이 트리가 해시 배열을
  절대 제자리에서 고치지 않기 때문이지, 복사가 비싸서가 아니다
  함정: 3번에서 자식을 복사본에서 읽어야 한다. 원본에서 읽으면 아래층에서 방금 고친 값 대신
        옛 값을 합치고, 새 뿌리가 옛 뿌리와 같아진다 - 이 자료구조에서 그것은 "아무 일도 안
        일어났다"는 뜻이라 예외 없이 조용히 틀린다
  한계: 잎을 끼워 넣거나 빼면 뒤의 자리가 전부 밀려서 트리를 다시 지어야 한다
        이 자료구조는 "자리가 고정된 목록"에만 쓸 수 있다
```

### 필드
- `hashing` — 역할:
- `levels` (`byte[][][]`) — 역할:
- `comparisons` — 역할:

### `MerkleTree(List<byte[]> blocks, HashFunction function)` / `MerkleTree(List<byte[]> blocks, MerkleHashing hashing)`
- 하는 일:
- 논리:
- 비용(왜):

### `private MerkleTree(byte[][][] levels, MerkleHashing hashing)`
- 하는 일:
- 논리:
- 비용(왜):

### `static byte[][][] build(List<byte[]> blocks, MerkleHashing hashing)` (TODO, private)
- 하는 일:
- 논리:
- 비용(왜):

### `byte[] rootHash()`
- 하는 일:
- 논리:
- 비용(왜):

### `byte[] leafHash(int leafIndex)`
- 하는 일:
- 논리:
- 비용(왜):

### `MerkleProof proofFor(int leafIndex)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `int findFirstDifference(MerkleTree other)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `MerkleTree withLeafReplaced(int leafIndex, byte[] newBlock)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `boolean sameNode(MerkleTree other, int level, int index)`
- 하는 일:
- 논리:
- 비용(왜):

### `byte[] hashAt(int level, int index)`
- 하는 일:
- 논리:
- 비용(왜):

### `int levelSize(int level)` / `int leafCount()` / `int height()`
- 하는 일:
- 논리:
- 비용(왜):

### `MerkleHashing hashing()`
- 하는 일:
- 논리:
- 비용(왜):

### `long comparisons()` / `void resetComparisons()`
- 하는 일:
- 논리:
- 비용(왜):

### `int requireLeafIndex(int leafIndex)` / `void requireComparable(MerkleTree other)` (private)
- 하는 일:
- 논리:
- 비용(왜):

## 구현 — MerkleProof (`src/main/java/com/datastructure/merkle/MerkleProof.java`)

### 구조

증명(proof)이란: "이 블록이 그 루트 아래에 진짜 있다"를 보여주는 최소한의 재료 묶음. 전체 트리 대신, 잎에서 뿌리까지 올라가며 만나는 **형제들의 해시**만 담는다.
  - *record*: 자바에서 "필드 몇 개 묶은 값"을 짧게 정의하는 문법. 자동으로 equals 를 만들어주는데, 그 equals 가 배열을 참조로만 비교해서 여기서는 일부러 안 쓴다.
  - *clone*: 배열의 복사본을 만드는 것. 받은 배열을 그대로 들고 있으면 바깥에서 내용을 바꿀 수 있어서, 생성자에서 복사해 둔다.

```
MerkleProof - 잎에서 뿌리까지 경로의 형제 해시 목록 + 방향. 블록은 하나도 안 담는다

  MerkleProof
  +-----------------------------------------------------------------+
  | steps   : List<Step>      잎 쪽부터 뿌리 쪽 순서 (순서가 곧 계약) |
  | hashing : MerkleHashing   검증하는 쪽도 같은 규칙을 써야 한다      |
  +--------------------------------+--------------------------------+
                                   |
                                   v
  Step  (record 가 아니다 - record 의 equals 는 byte[] 를 참조로 비교해 조용히 틀린다)
  +-----------------------------------------------------------------+
  | siblingHash   : byte[]    형제 노드의 해시 (생성자에서 clone 한다)|
  | siblingIsLeft : boolean   형제가 왼쪽이면 true, 오른쪽이면 false  |
  +-----------------------------------------------------------------+
    siblingHash()    복사본을 준다 (바깥용)
    rawSiblingHash() 무복사. 검증 안쪽 전용 - 걸음마다 32바이트를 새로 뜨지 않으려고 둔다
    flipped()        방향만 뒤집은 걸음. 잘못된 증명이 거부되는지 보는 테스트가 쓴다

  방향은 형제 기준이다. "내가 왼쪽인가"로 담아 놓고 형제 기준으로 읽으면
  verify 가 좌우를 바꿔 합쳐 뿌리가 안 맞는다. 담는 쪽과 읽는 쪽이 같은 기준이어야 한다
  크기 : 잎 100만 개 -> 걸음 20개, SHA-256 이니 640바이트. size() 가 log n 이어야 한다
  승격 때문에 증명 길이가 잎마다 다를 수 있다 (잎 3개 트리에서 2번 잎의 증명은 높이가 2인데 1걸음)
```

### 동작 — 증명 생성/검증

**언제 쓰나**: 만드는 쪽([1] proofFor)은 트리를 가진 서버가 "이 블록은 트리에 있다"의 증거를 만들 때. 검증하는 쪽([2] verify)은 트리 없이 루트 하나만 아는 클라이언트가 그 증거를 확인할 때.
그림 먼저 — [1]은 형제를 주워 담으며 올라가는 길, [2]는 담아온 형제와 합쳐 다시 뿌리를 만들어 보는 길이다.

```
[1] proofFor(1) : 잎에서 뿌리까지 올라가며 형제를 주워 담는다

  levels[2]            h(ABCD)              담는 규칙
                      /       \              내 index 가 짝수 -> 형제 = index + 1, 형제는 오른쪽
  levels[1]     h(AB)          h(CD)                     홀수 -> 형제 = index - 1, 형제는 왼쪽
                /   \           ^ 형제                  그리고 index /= 2 로 부모 자리로 올라간다
  levels[0]  h(A)    h(B)                       형제 자리가 그 층 길이를 넘으면 승격이라
              ^        ^ 잎 1 (시작)              형제가 없다 -> 그 걸음은 안 담고 넘어간다
              형제                              마지막 층(뿌리)에서는 담을 것이 없다

  steps = [ Step(h(A),  siblingIsLeft = true ),   <- 0층: index 1 은 홀수라 형제가 왼쪽
            Step(h(CD), siblingIsLeft = false) ]  <- 1층: index 0 은 짝수라 형제가 오른쪽
  걸음 수 = 경로 길이 = O(log n). 형제 해시만 담고 파일은 안 담는다

[2] verify(leafHash, expectedRoot) : 검증하는 쪽에는 트리가 없다. 잎 해시 1개 + 증명 + 뿌리뿐이다

  cur = h(B)                        <- 검증자가 자기가 가진 블록에서 직접 계산한 값
    |
    | step0 : siblingIsLeft = true   -> cur = nodeHash( h(A) , cur   )
    v                                                   형제   나
  cur = h(AB)
    |
    | step1 : siblingIsLeft = false  -> cur = nodeHash( cur  , h(CD) )
    v                                                   나     형제
  cur = h(ABCD)
    |
    v
  Arrays.equals(cur, expectedRoot) ?   ->  true 면 통과

  해시 계산 = 걸음 수 = O(log n). 파일 전체(블록 n 개)를 받지 않는다
  방향이 없으면 어느 쪽에 붙일지 몰라 반반 확률로 실패한다. 방향 비트 목록 + 형제 해시 목록이
  합쳐져 "그 잎이 트리 어디에 있는가" 곧 경로 그 자체다
  걸음 0개인 증명도 정상이다 - 잎이 하나뿐인 트리는 잎 해시가 곧 뿌리라 바로 비교한다
  함정 1: cur.equals(expectedRoot) 는 참조 비교라 언제나 false. 모든 증명이 거부되는데
          "잘못된 증명을 거부한다" 쪽 테스트는 통과해서 더 헷갈린다
  함정 2: 길이만 보거나 앞 몇 바이트만 보면 어떤 위조든 통과한다. 전부 보거나 안 보거나다
  보장하는 것은 "이 뿌리 아래 있다" 한 문장뿐이다. 그 뿌리가 진짜인지는 이 물건 밖의 문제다
    (공격자가 자기 뿌리를 주면 자기 증명이 통과한다. 그래서 실무는 뿌리를 서명하거나
     블록체인 같은 다른 경로로 받는다)
```

### 필드
- `steps` — 역할:
- `hashing` — 역할:
- `Step.siblingHash` / `Step.siblingIsLeft` — 역할:

### `Step(byte[] siblingHash, boolean siblingIsLeft)` / `byte[] siblingHash()` / `boolean siblingIsLeft()` / `byte[] rawSiblingHash()` / `Step flipped()`
- 하는 일:
- 논리:
- 비용(왜):

### `MerkleProof(List<Step> steps, MerkleHashing hashing)`
- 하는 일:
- 논리:
- 비용(왜):

### `boolean verify(byte[] leafHash, byte[] expectedRoot)` (TODO)
- 하는 일:
- 논리:
- 비용(왜):

### `List<Step> steps()` / `int size()` / `MerkleHashing hashing()`
- 하는 일:
- 논리:
- 비용(왜):

## 구현 전략 비교

| 전략 | 장점 | 단점 | 적합한 경우 |
|------|------|------|-------------|
| PrefixedHashing (MerkleHashing) | | | |
| UnprefixedHashing (MerkleHashing) | | | |
| Sha256Hash (HashFunction) | | | |
| ToyHash (HashFunction) | | | |
| 짝 없는 마지막 노드: 승격 | | | |
| 짝 없는 마지막 노드: 자기 자신과 짝짓기(비트코인) | | | |

## 문제 — MerkleProblems (`src/main/java/com/datastructure/merkle/MerkleProblems.java`)

### 문제 1. 다른 블록 전부 찾기 — `diffBlocks(MerkleTree local, MerkleTree remote)`

> 문제 설명: 두 트리에서 다른 블록을 전부 찾는다. 인덱스 오름차순.
> `findFirstDifference` 는 처음 하나만 찾았다. 여기서는 전부 찾는다.
> 전수 비교와 답이 같아야 하고, 비교한 노드 수는 훨씬 적어야 한다.
> 블록 1024개 중 3개가 다르면 전수는 1024번이고 이 방법은 60번 안쪽이다.
> 잎 개수가 다르면 IllegalArgumentException.
> 생각할 것: 이것이 rsync 의 델타 전송과 카산드라의 anti-entropy 복구다.
> 다른 블록만 골라 보내려면 먼저 어느 블록이 다른지 싸게 알아야 한다.

- 내 접근:
- 논리:
- 비용(왜):

### 문제 2. 증명 여러 개 한 번에 검증 — `verifyBatch(byte[] root, List<MerkleProof> proofs, List<byte[]> leafHashes)`

> 문제 설명: 증명 여러 개를 한 번에 검증한다. 하나라도 틀리면 false.
> `proofs.get(i)` 가 `leafHashes.get(i)` 에 대한 증명이다.
> 개수가 다르거나 null 이 섞이면 IllegalArgumentException.
> 생각할 것: 검증하는 쪽에는 트리가 없다. 뿌리 하나와 증명들뿐이다.
> 인증서 투명성 로그를 감시하는 쪽이 정확히 이 자세로 서 있다.

- 내 접근:
- 논리:
- 비용(왜):

## 핵심 문장

<!-- 지도 수준의 문장들 — 세부가 아니라 "왜 이 구조인가"를 담은 문장 -->

-
-
-

## 관련 자료

- 원본 README: `/home/jun/project/myway/data-structure/27-merkle-tree/README.md`
- 구현 대상: `/home/jun/project/myway/data-structure/27-merkle-tree/src/main/java/com/datastructure/merkle/`
- 테스트: `/home/jun/project/myway/data-structure/27-merkle-tree/src/test/java/com/datastructure/merkle/`
- 정답 구현: `/home/jun/project/myway/data-structure/27-merkle-tree/impl/`

## 용어 풀이

- **해시(hash)**: 어떤 데이터든 넣으면 짧은 고정 길이 값이 나오는 함수/그 결과값. 내용이 조금만 달라도 값이 완전히 달라진다. 데이터의 "지문".
- **SHA-256**: 실무에서 널리 쓰는 해시 함수. 결과가 항상 32바이트(256비트)다.
- **바이트(byte)**: 데이터의 최소 단위 조각(8비트). `byte[]` 는 바이트가 줄지어 선 배열.
- **머클 트리(Merkle tree)**: 블록마다 해시를 뜨고 둘씩 묶어 위로 올려, 루트 해시 하나로 전체를 대표하게 만든 트리.
- **잎(leaf) / 내부(internal) 노드 / 루트(root)**: 트리 맨 아래층 노드 / 그 위층들의 노드 / 맨 꼭대기 노드 하나.
- **접두사(prefix)**: 데이터 맨 앞에 붙이는 표시 바이트. 잎(0x00)과 내부(0x01)를 다른 세계로 갈라놓는다.
- **두 번째 원상 공격(second preimage attack)**: 같은 해시값이 나오는 "다른 입력"을 만들어내는 공격.
- **인증서 투명성(CT) 로그 / RFC 6962**: 발급된 웹 인증서를 공개 장부에 다 적어 감시하게 하는 제도 / 그 표준 문서.
- **CVE-2012-2459**: 비트코인의 "마지막 노드를 자기 자신과 짝짓기" 규칙 때문에 서로 다른 블록 목록이 같은 루트를 갖게 된 실제 보안 결함 번호.
- **승격**: 짝이 없는 마지막 노드를 다시 해시하지 않고 참조 그대로 위층에 올리는 규칙.
- **포함 증명(inclusion proof)**: "이 블록이 그 루트 아래 있다"를 형제 해시 목록 + 방향만으로 보여주는 증거.
- **형제(sibling)**: 같은 부모를 가진 다른 쪽 노드.
- **포인터/참조(reference)**: 객체가 어디 있는지 가리키는 값. 참조 비교(`==`, 배열의 `.equals`)는 "같은 객체인가"만 본다.
- **Arrays.equals**: 배열의 내용(바이트 하나하나)이 같은지 비교하는 자바 함수.
- **얕은 복사(shallow copy)**: 겉 배열만 새로 만들고 안의 것들은 같은 객체를 가리키게 하는 복사.
- **clone**: 배열/객체의 복사본을 만드는 자바 메서드.
- **record**: 자바에서 값 묶음을 짧게 정의하는 문법. 자동 생성되는 equals 가 배열을 참조로 비교하는 게 여기서의 함정.
- **경로 복사(path copying)**: 바뀐 자리에서 뿌리까지 가는 길 위의 노드만 새로 만들고 나머지는 공유하는 방법(26번 참고).
- **O(n) / O(log n)**: 일의 양이 데이터 개수에 비례 / 데이터가 2배 되어도 한 걸음만 늘어남. n은 블록(잎) 수.
- **ceil(올림 나눗셈)**: 나누고 소수점이 남으면 올리는 것. `(길이+1)/2` 가 정수 나눗셈으로 올림을 구현한다.
- **델타 전송(rsync)**: 파일 전체가 아니라 달라진 조각만 골라 보내는 동기화 방식.
- **anti-entropy(카산드라)**: 분산 저장소의 복제본끼리 머클 트리를 비교해 어긋난 부분만 고치는 복구 절차.
- **IllegalArgumentException**: "잘못된 값을 인자로 줬다"를 알리는 자바의 오류 신호.
