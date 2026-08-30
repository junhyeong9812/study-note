# data-structure/27-merkle-tree — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 작성 방식: 내가 먼저 기억으로 흐름을 서술하고, Claude는 빠지거나 틀린 곳을 짚는다. 대신 써주지 않는다.
> 이미 따라 치며 만든 정리본이 따로 있으면(organize류) 이 파일은 핵심 문장 압축 + 링크만 담는다.

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
