# data-structure/24-lsm-tree — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 작성 방식: **2-summary를 닫고 기억만으로** 쓴다 → 실제 코드/원전으로 검증 → 틀린 부분만 수정.
> 기준 소스는 문서가 아니라 코드다.
> ⚠️ 이 정답은 Claude 초안(2026-09-15) — 본인 검토 후 이 줄 삭제

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

#### 1. LSM 트리는 왜 필요한가 — 임의 쓰기와 SSD의 페이지·블록

- Q: 15번 B+트리로 키 하나를 넣을 때 디스크에서 무슨 일이 일어나는가(임의 쓰기)?\
  A: 키가 들어갈 잎(leaf) 페이지를 먼저 **찾아가야** 한다.\
  루트에서 내부 노드를 거쳐 잎까지 내려가므로 높이만큼 읽기가 일어난다.\
  거기서 끝이 아니라 그 잎 페이지의 **원래 자리**에 값을 끼워 넣고 다시 써야 한다.\
  즉 파일 끝에 이어 쓰는 것이 아니라 파일 중간의 특정 위치를 고치는 것이고, 그것이 임의 쓰기다.\
  잎이 꽉 차 있으면 분할이 일어나 부모 페이지까지 같이 고쳐야 하므로 고쳐 쓰는 자리가 더 늘어난다.

```
15번 B+트리에 키 하나 넣기 : 자리를 찾아가 그 자리를 고친다

    [ 루트 ]                   1. 루트 페이지 읽기
        |                      2. 내부 페이지 읽기
    [ 내부 ]                   3. 내부 페이지 읽기
        |                      4. 잎 페이지 읽기       <- 여기까지가 읽기
    [ 잎 : ... k ... ]         5. 잎 안에 k 를 끼워 넣고
        ^                         그 잎 페이지를 "원래 있던 자리" 에 다시 쓴다
        |
        +-- 디스크의 특정 위치다. 파일 끝이 아니라 중간이다 -> 임의 쓰기
            잎이 꽉 찼으면 분할이 일어나 부모 페이지도 같은 방식으로 고쳐야 한다
```

> **임의 쓰기(random write)** — 파일이나 디스크의 특정 위치를 찾아가 그 자리를 고쳐 쓰는 것.\
> 예: B+트리의 잎 페이지에 키를 끼워 넣고 그 페이지를 원래 자리에 다시 쓰는 것이 임의 쓰기다.

> **순차 쓰기(sequential write)** — 이미 쓴 것을 건드리지 않고 뒤에 이어서만 쓰는 것.\
> 예: LSM 의 flush 는 정렬된 memtable 을 새 파일 한 장으로 처음부터 끝까지 흘려 쓰고 끝낸다.

- Q: 순차 쓰기가 임의 쓰기보다 수십~수백 배 빠른 이유는 SSD 에서 무엇 때문인가(페이지와 블록)?\
  A: SSD 의 NAND 플래시는 **읽고 쓰는 단위(페이지)보다 지우는 단위(블록)가 훨씬 크다**.\
  그리고 이미 쓴 페이지에 곧바로 덮어쓸 수 없고, 다시 쓰려면 먼저 지워야 한다.\
  그런데 지우기는 페이지 하나가 아니라 그 페이지가 속한 블록 전체를 대상으로만 된다.\
  그래서 "페이지 한 장을 제자리에서 고친다"는 요청이 실제로는 블록 전체를 다른 곳으로 옮겨 쓰고 옛 블록을 지우는 일이 된다.\
  순차로 쭉 쓰면 빈 블록을 앞에서부터 채우기만 하므로 옮길 것도 지울 것도 없다.

```
SSD 에서 "제자리를 고친다" 가 실제로 하는 일

    블록 (지우기 단위 = 페이지 여러 장 묶음)
    +------+------+------+------+  ...  +------+
    | p0   | p1   | p2   | p3   |       | pN   |
    +------+------+------+------+  ...  +------+
                    ^ 여기 한 장만 고치고 싶다

    NAND 는 이미 쓴 페이지에 덮어쓰기가 안 된다. 지워야 다시 쓴다
    그런데 지우기는 페이지 단위가 아니라 블록 단위다

    1. 블록 전체를 읽어 빈 블록으로 옮겨 쓴다 (p2 자리만 새 내용으로)
    2. 옛 블록을 통째로 지운다
    -> 페이지 한 장을 고치려고 블록 한 개 분량을 옮겨 쓰고 지웠다

    순차로 쓰면 : 빈 블록에 p0 부터 차례로 채운다. 옮길 것도 지울 것도 없다
```

> **페이지(page) / 블록(block)** — SSD 가 읽고 쓰는 최소 단위 / 지우는 최소 단위. 블록이 페이지 여러 장을 묶은 크기다.\
> 예: 페이지 한 장을 고치려면 그 장이 속한 블록 전체를 옮겨 쓰고 지워야 하므로 고친 양보다 훨씬 많이 쓰게 된다.

(구체적인 페이지·블록 크기 수치는 원본 README 에 없다 — README 는 "읽고 쓰는 단위보다 지우는 단위가 훨씬 크다"까지만 말한다.)

- Q: 그래서 어떤 워크로드에서 B+트리가 무너지는가?\
  A: **쓰기가 압도적으로 많은 워크로드**다 — README 는 로그, 시계열, 이벤트 스트림을 든다.\
  이런 데이터는 읽기보다 쓰기가 수십~수백 배 많고, 쓰기마다 임의 쓰기가 한 번씩 발생한다.\
  B+트리의 자랑인 "조회 O(log n) 한 번"은 이 워크로드에서 거의 쓰이지 않는 이점이다.\
  LSM 은 그 이점을 팔아서 쓰기를 전부 순차로 바꾼다.

**더 생각할 것**

- "B+트리가 느리다"가 아니라 "이 워크로드에서 B+트리의 이점이 안 팔린다"가 정확한 진술이다.\
  읽기가 압도적이면 15번이 여전히 맞는 답이다.
- 임의 쓰기의 비용은 회전 디스크에서는 탐색 시간(seek), SSD 에서는 지우기 단위 불일치로 서로 다른 이유로 발생하는데, 둘 다 "제자리를 고치는 것이 비싸다"는 같은 결론에 이른다.
- 이 장의 모든 설계가 이 한 문장에서 파생된다 — **고치지 않는다. 덧붙이기만 한다.**

#### 2. 거래를 어떻게 뒤집는가 — 네 가지 연산과 그 대가

- Q: 쓰기·읽기·삭제·정리 네 가지가 각각 어떻게 바뀌는가?\
  A: 쓰기는 디스크를 아예 안 건드리고 메모리의 정렬 구조(memtable)에만 넣는다.\
  읽기는 한 번에 끝나지 않고 memtable 부터 가장 오래된 SSTable 까지 차례로 뒤진다.\
  삭제는 지우지 않고 "지웠다"는 표식(tombstone)을 **새로 쓴다**.\
  정리는 연산이 아니라 별도의 대청소(compaction)로 빠져나가, 쌓인 장들을 나중에 한꺼번에 합친다.

```java
// impl/LsmTree.java — 쓰기 경로 전부다. 디스크를 찾아가는 코드가 한 줄도 없다
private void write(K key, Object value) {
    memtable.put(key, value);
    if (memtable.size() >= memtableThreshold) {
        flush();
    }
}

@Override
public void delete(K key) {
    requireKey(key);
    write(key, Tombstone.MARKER);   // 삭제도 그냥 쓰기다
}
```

> **MemTable** — 메모리에 있는 "쓰기를 받는 층". 항상 키 정렬 상태를 유지한다.\
> 예: impl/MemTable.java 는 `TreeMap<K, Object>` 한 개가 전부이고, 정렬을 디스크가 아니라 메모리에서 해치운다.

> **SSTable(Sorted String Table)** — MemTable 을 굳혀 만든 디스크의 정렬된 불변 파일 한 장.\
> 예: impl/SSTable.java 는 `keys` / `values` 두 배열과 바이트 수, 블룸 필터만 들고 있고 고치는 메서드가 없다.

- Q: 쓰기를 순차로 만든 대가를 누가 내는가?\
  A: **읽기와 공간이 낸다.**\
  읽기는 같은 키의 최신 판본이 어느 장에 있는지 모르므로 최신 장부터 차례로 내려가야 한다 — 장이 늘수록 비싸진다.\
  공간은 제자리를 안 고치므로 같은 키의 옛 판본이 지워지지 않고 그대로 쌓인다.\
  삭제조차 저장량을 **늘린다** — tombstone 이 엔트리 하나를 새로 차지하기 때문이다.\
  README 의 표현대로 공짜가 없고, 쓰기에서 아낀 것을 읽기와 공간이 청구서로 받는다.

| | B+트리 (15번) | LSM 트리 (24번) |
|---|---|---|
| 쓰기 | 임의 쓰기 | 순차 쓰기만 |
| 읽기 | O(log n) 한 번 | SSTable 장 수만큼 |
| 삭제 | 즉시 | tombstone, 나중에 정리 |
| 공간 증폭 | 낮다 | 높다 (같은 키의 옛 판본들) |
| 쓰는 곳 | MySQL, PostgreSQL | RocksDB, 카산드라, LevelDB, HBase |

- Q: 그 대가를 줄이려고 무엇이 붙는가?\
  A: 읽기 쪽에는 **블룸 필터**(11번)가 붙는다 — 장마다 "이 키는 확실히 없다"를 미리 답해 헛읽기를 잘라낸다.\
  공간 쪽에는 **compaction** 이 붙는다 — 쌓인 장들을 합쳐 같은 키의 옛 판본과 tombstone 을 함께 버린다.\
  둘 다 구조의 일부가 아니라 **대가를 깎으려고 나중에 덧댄 장치**라는 점이 중요하다.\
  그래서 둘 다 켜고 끌 수 있고(`bloomEnabled`), 언제 부를지도 호출자가 정한다(`compact()`).

> **compaction(다지기)** — 여러 SSTable 을 한 번 훑어 하나로 합치면서 같은 키의 옛 판본과 tombstone 을 정리하는 대청소.\
> 예: impl/Compactor.java 의 k-way 머지가 정렬된 여러 장을 앞에서 뒤로 한 번씩만 훑어 새 한 장을 만든다.

**더 생각할 것**

- 네 연산 중 "정리"만 사용자 요청이 아니라 **시스템이 스스로 빚을 갚는 행위**다.\
  그래서 실무 LSM 의 운영 난이도는 대부분 "언제 얼마나 compaction 을 돌릴 것인가"에 몰려 있다.
- 읽기·공간이 내는 대가는 시간이 지나면 저절로 커지지만 compaction 을 돌리면 즉시 되돌아온다 — **되돌릴 수 있는 빚**이라는 점이 이 거래를 성립시킨다.
- 반대로 되돌릴 수 없는 대가도 하나 있다 — 있는 키를 찾는 최소 비용 1회는 어떤 장치로도 못 없앤다(6번에서 다시 본다).

#### 3. 시그니처가 설계를 말한다 — `put` 이 `void` 인 이유

- Q: 15번 `put` 은 옛 값을 반환했는데 여기 `put` 은 왜 `void` 인가?\
  A: **옛 값을 돌려주려면 먼저 읽어야 하기 때문이다.**\
  이 저장소에서 읽기는 memtable 부터 마지막 SSTable 까지 내려가는 가장 비싼 연산이다.\
  쓰기 한 번에 그 읽기를 끼워 넣으면 "디스크를 안 건드리는 쓰기"라는 전제 자체가 무너진다.\
  README 의 문장이 정확하다 — **읽지 않는 것이 이 구조의 전부**다.\
  그래서 반환값을 못 주는 것이 아니라 **주지 않기로 한 것**이고, 그 결정이 시그니처에 박혀 있다.

```java
// impl/LsmTree.java — put 은 옛 값을 확인하지 않는다
@Override
public void put(K key, V value) {
    requireKey(key);
    if (value == null) {
        throw new IllegalArgumentException("값에 null 을 넣을 수 없다. 지우려면 delete 를 써라");
    }
    write(key, value);   // memtable.put 한 번. 그게 전부다
}
```

- Q: 같은 이유가 `delete` 에도 그대로 적용되는가?\
  A: 그렇다.\
  `delete(k)` 는 그 키가 실제로 있는지 **확인하지 않고** 무조건 tombstone 을 쓴다.\
  확인하려면 읽어야 하고, 읽는 순간 삭제가 쓰기가 아니라 조회+쓰기가 된다.\
  `LsmTreeTest.Empty.deleteOfAbsentKeyStillWrites` 가 이 성질을 못 박는다 — 없는 키 7 을 지웠는데 `size()` 는 0 이고 `storedEntryCount()` 는 1 이다.\
  즉 "지울 것이 없었다"는 사실조차 이 구조는 모른 채로 표식 하나를 더 저장한다.

> **쓰기 경로에 읽기를 섞지 않는다(read-free write)** — 쓰기 연산이 기존 상태를 조회하지 않고 끝나는 설계.\
> 예: `put` 이 옛 값을 반환하지 않고 `delete` 가 존재 여부를 확인하지 않는 것이 둘 다 같은 원칙의 결과다.

- Q: RocksDB 도 카산드라도 Put 이 값을 안 돌려주는 이유는?\
  A: 그 엔진들도 같은 LSM 구조 위에 서 있고, 같은 이유로 같은 선택을 했다.\
  Put 이 옛 값을 돌려주는 순간 모든 쓰기가 읽기 한 번을 동반하게 되어, 쓰기가 많은 워크로드에서 처리량이 무너진다.\
  대신 옛 값이 꼭 필요하면 호출자가 `get` 을 명시적으로 한 번 더 부르게 한다 — 비용이 어디서 나는지 코드에 드러나게 만드는 것이다.\
  **API 가 숨긴 비용이 없다**는 것이 이 시그니처의 진짜 의도다.

**더 생각할 것**

- 시그니처를 보고 구조를 역추적할 수 있다 — 반환값이 없다는 것은 "그 값을 알려면 읽어야 하는데 읽고 싶지 않다"는 자백이다.
- 반대로 15번 B+트리의 `put` 이 옛 값을 돌려줄 수 있었던 것은, 어차피 잎까지 내려가 그 페이지를 읽은 뒤에 고치기 때문이다 — 읽기가 이미 경로에 있었다.
- API 설계에서 "돌려줄 수 있는데 안 돌려준다"와 "돌려주려면 비싸진다"는 전혀 다른 이야기다. 여기는 후자이고, 그래서 타협의 여지가 없다.

#### 4. `Tombstone` 이 왜 필요한가 — `null` 로는 무엇을 구별 못 하는가

- Q: 값 자리에 `null` 을 쓰면 무엇과 무엇을 구별할 수 없게 되는가?\
  A: **"이 키는 지워졌다"와 "이 층에는 그 키가 없다"** 를 구별할 수 없게 된다.\
  이 저장소에서 `null` 은 이미 후자의 뜻으로 쓰이고 있다 — `MemTable.get` 도 `SSTable.rawValue` 도 못 찾으면 `null` 을 돌려준다.\
  같은 값 하나에 두 가지 뜻을 얹으면, 받는 쪽은 둘을 갈라낼 정보가 없다.\
  그래서 삭제 표식은 `null` 이 **아닌** 다른 무엇이어야 하고, 그 자리가 `Tombstone.MARKER` 다.

```
값 자리에 올 수 있는 것 세 가지와 그 뜻

    "old"      살아 있는 값                 -> 이 값을 답으로 삼고 멈춘다
    MARKER     이 키는 지워졌다             -> null 로 풀어서 답하고 멈춘다
    null       이 층에는 그 키가 없다       -> 아래 층을 더 봐야 한다


MARKER 대신 null 을 쓰면 위의 두 줄이 한 줄로 합쳐진다

    MemTable { 7 -> null }
                    |
                    +-- "7 을 지웠다" 인가?
                    +-- "7 을 넣은 적이 없다" 인가?
                        구별할 방법이 없다


구별을 못 하면 get 은 "이 층에 없다" 쪽으로 읽고 아래로 내려간다

    index 0   MemTable { 7 -> null }     지웠다는 뜻이었는데 없다고 읽혔다
    index 1   SST      { 7 -> "old" }    여기서 처음 만난 값이라 멈춘다
                                         -> get(7) = "old"
                                            지운 키가 되살아났다
```

> **tombstone(묘비)** — "이 키는 지워졌다"는 표식. 진짜로 지우는 대신 표식을 새 엔트리로 쓴다.\
> 예: `delete(k)` 는 `put(k, Tombstone.MARKER)` 와 정확히 같은 일을 하고, 그래서 삭제 비용이 쓰기 비용과 같다.

> **센티널(sentinel)** — "값이 아니지만 값 자리에 들어가 특별한 뜻을 나타내는 표시".\
> 예: `Tombstone.MARKER` 는 어떤 실제 값과도 겹치지 않도록 전용 타입의 인스턴스 하나로 만들어 둔 센티널이다.

- Q: 구별을 못 하면 무엇이 되살아나는가?\
  A: **아래 층에 가려져 있던 옛 값**이 되살아난다.\
  tombstone 은 옛 값을 지운 것이 아니라 위에서 **가리고 있는** 것이다.\
  가리개가 "없음"으로 읽히면 조회가 그 아래까지 내려가 이미 죽은 값을 물어온다.\
  그리고 이 잘못은 예외를 던지지 않는다 — 타입도 맞고 값도 있는 정상적인 답처럼 보인다.\
  8번의 부분 compaction 함정이 정확히 같은 실패를 다른 경로로 재현하는 것이다.

- Q: 동일성(`==`)으로 판별하는 것이 왜 안전한가?\
  A: `MARKER` 가 **하나뿐인 인스턴스**이기 때문이다.\
  생성자를 `private` 으로 막아 밖에서 새로 만들 수 없게 했으므로, 세상에 존재하는 tombstone 은 그 객체 하나뿐이다.\
  그러면 "내용이 같은가"를 물을 필요가 없고 "바로 그 물건인가"만 물으면 된다.\
  `equals` 로 비교하면 사용자 값이 `equals` 를 이상하게 구현해 tombstone 인 척할 수 있지만, `==` 는 그 통로 자체가 없다.\
  덤으로 `==` 는 참조 한 번 비교라 비용이 사실상 0 이고, 이 판별은 조회 경로마다 호출된다.

```java
// src/main/java/com/datastructure/lsm/Tombstone.java — TODO 가 없는 클래스다
public final class Tombstone {

    /** 하나뿐인 표식. 동일성(==) 으로 판별하므로 equals 를 쓸 일이 없다. */
    public static final Tombstone MARKER = new Tombstone();

    private Tombstone() {
    }

    public static boolean is(Object value) {
        return value == MARKER;      // 내용 비교가 아니라 "바로 그 객체인가"
    }
}
```

```java
// impl/LsmTree.java — 조회가 MARKER 를 null 로 "풀어서" 돌려준다
@SuppressWarnings("unchecked")
private V unwrap(Object value) {
    return Tombstone.is(value) ? null : (V) value;
}
```

> **동일성 비교(reference equality, `==`)** — 두 참조가 같은 객체를 가리키는지를 보는 비교. 내용 비교(`equals`)와 다르다.\
> 예: `MARKER` 는 인스턴스가 하나뿐이므로 `value == MARKER` 하나로 판별이 끝나고, 사용자 값이 흉내 낼 방법이 없다.

- Q: 그러면 사용자가 진짜로 `null` 값을 저장하고 싶으면 어떻게 되는가?\
  A: 못 한다 — `put` 이 `IllegalArgumentException` 을 던진다.\
  `LsmTreeTest.Basics.rejectsNull` 이 "값의 null 은 tombstone 과 구별이 안 된다"는 메시지로 이것을 못 박는다.\
  `SSTable` 생성자도 키와 값에 `null` 이 들어오면 거부한다.\
  즉 `null` 은 사용자 값의 영역에서 **완전히 추방되고**, "이 층에 없다"라는 내부 신호 전용으로 예약된다.

**더 생각할 것**

- 한 값에 두 가지 뜻을 얹는 것은 흔한 버그의 뿌리다 — `-1` 이 "못 찾음"이자 정당한 인덱스인 API 들이 같은 병을 앓는다.
- 이 구조는 "뜻이 셋이면 표현도 셋이어야 한다"를 타입 수준에서 지킨 예다. 값 타입이 `V` 가 아니라 `Object` 인 것도 그 대가다.
- `MARKER` 를 `enum` 으로 만들어도 같은 성질을 얻는다 — 핵심은 클래스가 아니라 "인스턴스가 하나뿐임을 언어가 보장한다"는 점이다.

#### 5. 읽기 증폭을 숫자로 — 10번, 5500번, 그리고 B+트리의 4번

- Q: SSTable 이 10장일 때 **없는 키** 하나를 확인하는 데 몇 번 뒤지는가?\
  A: **10번**이다.\
  `get` 은 처음 만난 값에서 멈추는데, 없는 키는 끝까지 아무 값도 못 만나므로 멈출 지점이 없다.\
  "없다"를 확신하려면 마지막 장까지 다 봐야 한다는 뜻이고, 이것이 읽기 증폭의 최악 형태다.\
  `ReadAmplificationTest.ReadAmplification.absentKeyProbesEveryTable` 이 `assertEquals(10, t.diskReads())` 로 이 값을 고정한다.

```java
// impl/LsmTree.java — 멈출 조건이 "값을 만났을 때" 하나뿐이다
for (SSTable<K, V> table : sstables) {
    if (!table.mightContain(key)) {
        continue;                       // 블룸이 없으면 이 가지는 절대 안 탄다
    }
    diskReads++;
    Object found = table.rawValue(key);
    if (found != null) {
        return unwrap(found);           // 처음 만난 값에서 멈춘다
    }
}
return null;                            // 없는 키는 여기까지 온다
```

> **읽기 증폭(read amplification)** — 값 하나를 읽으려고 실제로 몇 번을 들춰야 하는가의 배수.\
> 예: SSTable 이 10장일 때 없는 키 하나를 확인하는 데 10번을 뒤지면 읽기 증폭이 10배다.

- Q: 1000개를 전부 조회하면 왜 정확히 5500번인가?\
  A: 키가 사는 층의 깊이만큼만 내려가기 때문이고, 그 깊이가 100개씩 균등하게 퍼져 있기 때문이다.\
  손으로 계산해 보면 그대로 5500 이 나온다.

```
설정 : new LsmTree<>(100, false) 에 키 0..999 를 순서대로 put
       (ReadAmplificationTest.tenTables — 블룸을 꺼서 순수한 층 비용만 본다)

put 100 번마다 flush 가 일어나고, 새 장은 항상 sstables.add(0, frozen) 으로 맨 앞에 꽂힌다

    index     0           1           2                    9
          +---------+ +---------+ +---------+         +---------+
          | 900..999| | 800..899| | 700..799|   ...   |  0..99  |
          |  최신   | |         | |         |         | 가장 옛 |
          +---------+ +---------+ +---------+         +---------+


없는 키 하나 (123456)
    어느 장에도 없으므로 10 장을 전부 뒤진 뒤에야 null 이다   ->  10 번

있는 키 하나
    그 키가 사는 장이 index j 면, index 0..j 까지 j+1 번 뒤지고 멈춘다
        get(999) : index 0 에서 끝     ->  1 번
        get(500) : index 4 에서 끝     ->  5 번
        get(0)   : index 9 까지 내려감 -> 10 번

1000 개를 전부 조회한 합 (손계산)
    index 0 의 키 100 개  x  1 번  =   100
    index 1 의 키 100 개  x  2 번  =   200
    index 2 의 키 100 개  x  3 번  =   300
       ...
    index 9 의 키 100 개  x 10 번  =  1000

    합 = 100 x (1 + 2 + 3 + ... + 10)
       = 100 x (10 x 11 / 2)
       = 100 x 55
       = 5500
```

- Q: 계산과 테스트가 일치하는가?\
  A: 일치한다.\
  `ReadAmplificationTest.ReadAmplification.allPresentKeys` 가 `assertEquals(5500, t.diskReads())` 로 같은 값을 못 박는다.\
  그 테스트의 주석도 같은 식을 적어 둔다 — "층 i 에 있는 키는 i+1 번 뒤진다. 100개씩 10층이라 100*(10+9+...+1) = 5500".\
  중간 확인점인 `get(999)=1`, `get(500)=5`, `get(0)=10` 도 `costDependsOnLayer` 에 각각 assert 되어 있어, 층 배치 가정 자체가 검증된다.

- Q: 15번 B+트리는 어느 쪽이든 몇 번이었는가?\
  A: **4번**이다 — README 가 높이 4 를 기준으로 말한다.\
  중요한 것은 4 라는 수가 아니라 **있는 키든 없는 키든 같다**는 점이다.\
  B+트리는 키가 있어야 할 자리가 구조적으로 정해져 있어서, 거기까지 내려가면 있고 없음이 그 자리에서 결판난다.\
  LSM 은 그 자리가 정해져 있지 않다 — 같은 키가 여러 장에 있을 수 있고, 어느 장에도 없을 수도 있다.\
  그 불확실성의 값이 "10번 대 4번"으로 나타난다.

| | B+트리 (15번) | LSM, 블룸 없음 | LSM, 블룸 켬 |
|---|---|---|---|
| 없는 키 1개 | 4 | 10 | 대개 0 (오탐일 때만 1 이상) |
| 있는 키 1개 | 4 | 층 깊이 + 1 (1~10) | 최소 1 |
| 있는 키 1000개 합 | 4,000 | 5,500 | 1,051 |
| 없는 키 10,000개 합 | 40,000 | 100,000 | 955 |

(표의 B+트리 칸은 README 의 "높이 4" 를 그대로 곱한 값이다 — 원본에 합계가 명시되어 있지는 않다.)

- Q: 읽기 증폭은 되돌릴 수 있는가?\
  A: 되돌릴 수 있다 — **compaction 이 층 수를 줄이면 그대로 줄어든다**.\
  `compactionUndoesIt` 이 그 장면이다: 10장일 때 없는 키가 10번이었는데 `compact()` 뒤에는 1번이고 `sstableCount()` 도 1 이다.\
  다만 공짜가 아니다 — 같은 테스트가 `assertEquals(14_780 * 2, t.sequentialBytesWritten())` 로 그 값을 청구한다.\
  flush 로 14,780 바이트를 썼는데 compaction 이 살아 있는 1000개를 통째로 다시 써서 같은 양을 한 번 더 쓴 것이다.

**더 생각할 것**

- 5500 이라는 수는 "키가 층마다 100개씩 고르게 퍼져 있다"는 조건에서만 나온다.\
  최근 키만 계속 갱신되는 워크로드라면 대부분이 index 0 에서 끝나 훨씬 싸진다.
- 반대로 "오래된 키를 무작위로 읽는" 워크로드면 평균이 10 에 가까워진다 — 같은 구조인데 워크로드가 비용을 정한다.
- 층 수를 줄이는 방법은 compaction 하나뿐이고, compaction 은 쓰기로 값을 치른다 — 7번의 삼각형이 여기서 시작된다.

#### 6. 블룸 필터가 그 비용을 얼마나 지우는가 — 955 의 정체와 비대칭

- Q: 없는 키 1만 개 조회가 10만 번에서 955번이 되는 것의 계산 근거는?\
  A: 장마다 블룸 필터가 하나씩 붙어 있고, "확실히 없다"고 답한 장은 이진 탐색조차 하지 않아 `diskReads` 가 오르지 않는다.\
  그래서 실제로 디스크를 읽는 횟수는 **블룸이 통과시킨 횟수**와 같고, 없는 키에 대해 통과되는 것은 전부 오탐이다.

```
블룸 필터가 있을 때 없는 키 조회
(ReadAmplificationTest.BloomFilterEffect.absentKeysWithAndWithoutBloom)

    장마다 블룸이 하나씩 붙는다. 장당 엔트리 100 개, 목표 오탐률 1%
    (impl/SSTable.java 생성자 : new TinyBloomFilter(Math.max(1, n), 0.01))

        optimalBits(100, 0.01)      = 959 비트    원소당 9.59 비트
        optimalHashCount(959, 100)  = 7 개
        (두 값 다 SSTableStructureTest.Bloom.sameFormulaAsProblemEleven 에 assert 되어 있다)

    키 1000..10999 (1 만 개, 전부 없는 키) 를 조회한다

    블룸 없음 : 1 만 개  x  10 장  =  100,000 번 디스크를 뒤진다
    블룸 켬   : 10 만 번 물어서 955 번만 통과시킨다  ->  diskReads = 955

    955 / 100,000 = 0.955%     목표 1% 를 그대로 맞춘 수다
    100,000 / 955 = 104.7 배   README 의 "104배" 가 이 나눗셈이다
```

- Q: 955 라는 수의 정체는?\
  A: **오탐의 수**다 — 없는 키인데 블룸이 "있을 수도 있다"고 잘못 통과시킨 횟수다.\
  그 수가 하필 955 로 딱 떨어지는 것은 해시가 결정적이기 때문이다.\
  `TinyBloomFilter.mix64` 는 난수를 쓰지 않고 입력 하나에서 고정된 비트열을 만들어 내므로, 같은 키 집합·같은 크기·같은 해시 개수면 켜지는 비트가 매번 같다.\
  테스트 주석도 "두 숫자 다 파이썬 참조 구현으로 검산했다. 해시가 결정적이라 오탐 수까지 정확히 같다"고 못 박는다.\
  같은 성질이 `falsePositiveRateIsNearTheTarget` 에서도 보인다 — 10만 개 조회에 오탐이 정확히 1030 개다.

```java
// impl/TinyBloomFilter.java — 난수가 없다. 그래서 오탐 수까지 재현된다
static long mix64(long z) {
    z += 0x9E3779B97F4A7C15L;
    z = (z ^ (z >>> 30)) * 0xBF58476D1CE4E5B9L;
    z = (z ^ (z >>> 27)) * 0x94D049BB133111EBL;
    return z ^ (z >>> 31);
}
```

> **블룸 필터(Bloom filter)** — "확실히 없다 / 있을 수도 있다" 두 가지만 답하는 아주 작은 자료구조.\
> 예: 여기서는 SSTable 한 장마다 959 비트짜리 필터가 붙어 100개 키의 존재 여부를 미리 걸러낸다.

> **오탐(false positive)** — 없는데 "있을 수도 있다"고 답하는 것. 헛읽기 한 번으로 끝나고 정확성은 안 깨진다.\
> 예: 없는 키 1만 개를 조회하며 10만 번 물었을 때 955 번이 오탐이었고, 그 955 번만 실제로 디스크를 읽었다.

> **위음성(false negative)** — 있는데 "없다"고 답하는 것. 블룸 필터에는 **절대 일어나지 않아야 하는** 오류다.\
> 예: `neverSkipsAKeyThatIsThere` 가 담은 키 전부에 `mightContain` 이 true 인지 확인한다 — 이게 깨지면 조회가 조용히 틀린다.

- Q: 그런데 **있는 키에는 왜 별로 못 줄이는가**?\
  A: 있는 키의 비용은 두 부분으로 쪼개지는데, 블룸이 지울 수 있는 것은 그중 한쪽뿐이기 때문이다.

```
있는 키 1000 개를 전부 조회하면
(ReadAmplificationTest.BloomFilterEffect.presentKeysGainLess)

    블룸 없음 : 5,500
    블룸 켬   : 1,051

    5,500 =  1,000        +        4,500
             |                     |
             v                     v
    그 키가 실제로 사는 층    그 위의 "그 키가 없는" 층들
    블룸이 못 줄인다          블룸이 지우는 몫
    진짜 읽어야 하는 최소값

    1,051 =  1,000  +  51
                       ^ 4,500 번의 "없다" 질문 중 오탐 51 번 (약 1.1%)

    줄어든 비율 :  5,500 -> 1,051   약 5.2 배
    없는 키였다면 : 100,000 -> 955  약 104 배
```

- Q: 11번에서 본 비대칭이 여기서 어떻게 그대로 드러나는가?\
  A: 블룸 필터가 **확실히 아는 것은 "없다" 한쪽뿐**이라는 비대칭이다.\
  "없다"는 항상 옳으므로 그 장을 완전히 건너뛸 수 있다 — 디스크를 아예 안 읽는다.\
  "있을 수도 있다"는 확답이 아니므로 반드시 읽어 봐야 하고, 그래서 아무것도 절약하지 못한다.\
  있는 키의 조회는 마지막에 반드시 "있을 수도 있다"를 한 번 받게 되어 있으므로, 그 한 번은 구조적으로 못 지운다.\
  테스트가 `assertTrue(with.diskReads() >= 1000, "적어도 키마다 한 번은 진짜 읽어야 한다. 그건 못 줄인다")` 로 이 하한을 명시한다.\
  README 의 "한계" 절도 같은 말을 한다 — 있는 키를 찾는 최소 비용 1회는 어떤 필터로도 못 없앤다.

- Q: 블룸을 켜면 답이 달라질 위험은 없는가?\
  A: 없다 — 그것이 블룸 필터의 유일한 보장이다.\
  `sameAnswers` 가 `keys()`, `rangeScan(200, 800)`, `storedEntryCount()` 를 켠 쪽과 끈 쪽에서 비교해 전부 같음을 확인한다.\
  `neverSkipsAKeyThatIsThere` 는 더 근본적인 곳을 본다 — 1000개 키 조회가 전부 맞는지, 그리고 각 장의 모든 키에 `mightContain` 이 true 인지.\
  블룸이 틀리는 방향은 "헛수고 한 번"뿐이고, "답이 바뀐다"는 방향은 없어야 한다.\
  `SSTable.mightContain` 이 `bloom == null` 일 때 무조건 true 를 돌려주는 것도 같은 안전 쪽으로 기울인 설계다.

```java
// impl/SSTable.java — 필터가 없으면 "모르니 일단 읽어 봐라" 쪽으로 답한다
public boolean mightContain(K key) {
    return bloom == null || bloom.mightContain(key);
}
```

**더 생각할 것**

- 블룸 필터는 읽기 증폭을 줄이지만 **공간 증폭은 전혀 못 줄인다** — `storedEntryCount` 가 그대로다.\
  장치마다 고칠 수 있는 증폭이 정해져 있다.
- 필터 비용은 키당 9.59 비트다. 1000만 키면 약 12MB 로, 없는 키 조회를 100배 싸게 만드는 값으로는 싸다.
- 오탐률을 0.1% 로 낮추면 비트가 늘고(약 14.4 비트/키) 해시 개수도 늘어 계산이 비싸진다 — 여기서도 공짜가 없다.

#### 7. 증폭이 셋이고 서로 민다

- Q: 읽기·쓰기·공간 증폭이 각각 무엇인가?\
  A: 읽기 증폭은 값 하나를 읽으려고 몇 번을 들추는가다 — 이 구현은 `diskReads()` 로 센다.\
  쓰기 증폭은 논리적으로 한 번 쓴 데이터를 실제로 몇 번 디스크에 쓰는가다 — `sequentialBytesWritten()` 으로 센다.\
  공간 증폭은 살아 있는 키 대비 실제로 저장하고 있는 엔트리가 몇 배인가다 — `spaceAmplification()` 이 그 비율이다.\
  세 계수기가 전부 `LsmTree` 의 필드에 그대로 있고, 테스트가 이 셋을 각각 고정한다.

```java
// impl/LsmTree.java — 세 증폭을 재는 계수기
private long diskReads;                 // 읽기 증폭
private long sequentialBytesWritten;    // 쓰기 증폭

@Override
public long storedEntryCount() {
    long total = memtable.size();
    for (SSTable<K, V> table : sstables) {
        total += table.size();
    }
    return total;
}

@Override
public double spaceAmplification() {
    return storedEntryCount() / (double) Math.max(1, size());   // 공간 증폭
}
```

> **쓰기 증폭(write amplification)** — 논리적으로 한 번 쓴 데이터를 저장 장치에 실제로 몇 번 쓰게 되는가의 배수.\
> 예: flush 로 14,780 바이트를 쓴 데이터에 compaction 이 80,300 바이트를 더 쓰면 총 95,080 바이트로 6.4배다.

> **공간 증폭(space amplification)** — 살아 있는 키 수 대비 실제 저장된 엔트리 수의 비율.\
> 예: 같은 키를 100번 갱신해 옛 판본 99개가 남아 있으면 `storedEntryCount()` 100 / `size()` 1 = 100.0 이다.

- Q: 같은 키를 100번 갱신하면 공간 증폭이 얼마인가?\
  A: **100배**다.

```
같은 키를 100 번 갱신 (SpaceAmplificationTest.hundredVersionsOfOneKey)

    LsmTree<Integer,String> t = new LsmTree<>(100);
    for (int i = 0; i < 100; i++) { t.put(42, "v"+i); t.flush(); }

    index   0      1      2              ...            99
        +------+------+------+                      +------+
        | v99  | v98  | v97  |          ...         |  v0  |    장 100 개
        +------+------+------+                      +------+

    sstableCount()      = 100
    storedEntryCount()  = 100      <- 산 키는 하나인데 100 개를 들고 있다
    size()              =   1
    spaceAmplification  = 100 / 1 = 100.0
    get(42)             = "v99"    <- 답은 그래도 최신이다

    compact() 뒤
        +------+
        | v99  |     storedEntryCount() = 1,   spaceAmplification = 1.0
        +------+
        (SpaceAmplificationTest.compactionCollapsesThem)
```

- Q: 100개마다 합치면 순차 쓰기가 왜 6.4배가 되는가?\
  A: compaction 이 **살아 있는 것 전부를 매번 다시 쓰기** 때문이다.\
  라운드가 뒤로 갈수록 다시 쓸 양이 누적되어 커지고, 그 누적치의 합이 원래 쓴 양을 훌쩍 넘는다.

```
100 개마다 합치면 순차 쓰기가 얼마나 늘어나는가
(SpaceAmplificationTest.compactionCostsWrites — 키 0..999, 임계 100, 블룸 끔)

    entryBytes = HEADER_BYTES(8) + 키 문자열 길이 + 값 문자열 길이
    (impl/SSTable.java, tombstone 은 값 길이를 0 으로 친다)

    게으른 쪽 (lazy) : flush 만 10 번, compaction 0 번
        키 0..9     : 8 + 1 + 2 = 11 바이트  x  10  =     110
        키 10..99   : 8 + 2 + 3 = 13 바이트  x  90  =   1,170
        키 100..999 : 8 + 3 + 4 = 15 바이트  x 900  =  13,500
        합계                                            14,780   (테스트 assert 값)

    부지런한 쪽 (eager) : 100 개마다 compact()
        k 라운드의 flush 량  F_k :  F_1 = 1,280,   F_2..F_10 = 1,500 씩
        k 라운드의 compaction 이 다시 쓰는 양 C_k = F_1 + ... + F_k  (그때까지 살아 있는 것 전부)

            C_1 =  1,280        C_6  =  8,780
            C_2 =  2,780        C_7  = 10,280
            C_3 =  4,280        C_8  = 11,780
            C_4 =  5,780        C_9  = 13,280
            C_5 =  7,280        C_10 = 14,780
                                 compaction 합계 = 80,300

        총 쓰기 = flush 14,780 + compaction 80,300 = 95,080   (테스트 assert 값)
        95,080 / 14,780 = 6.43 배

    같은 테스트가 그 대가로 산 것도 잰다
        lazy.get(999999)  -> diskReads = 10,  sstableCount = 10
        eager.get(999999) -> diskReads =  1,  sstableCount =  1
```

- Q: **셋을 동시에 줄일 수 없다**는 결론은 어디서 오는가?\
  A: 세 증폭을 줄이는 손잡이가 사실상 **compaction 빈도 하나**뿐인데, 그 손잡이를 돌리면 둘은 좋아지고 하나는 나빠지기 때문이다.\
  자주 합치면 장 수가 줄어 읽기 증폭이 내려가고, 옛 판본이 걷혀 공간 증폭도 내려간다.\
  그런데 합칠 때마다 살아 있는 것 전부를 다시 쓰므로 쓰기 증폭이 올라간다 — 위 계산의 6.4배가 그것이다.\
  반대로 안 합치면 쓰기는 딱 한 번씩만 하지만 층이 쌓여 읽기와 공간이 나빠진다.\
  같은 테스트 안에서 두 나무가 정확히 반대 방향으로 값을 내는 것이 이 결론의 실측 근거다.

```
증폭 삼각형 — 손잡이는 하나뿐인데 세 꼭짓점이 동시에 움직인다

                      +-------------------+
                      |     쓰기 증폭     |
                      |  (다시 쓴 바이트) |
                      +-------------------+
                       자주 합치면   올라감
                       안  합치면   내려감
                                |
        compaction 빈도 --------+--------
                          |               |
            +-------------------+   +-------------------+
            |     읽기 증폭     |   |     공간 증폭     |
            |   (뒤진 장 수)    |   |  (쌓인 옛 판본)   |
            +-------------------+   +-------------------+
             자주 합치면 내려감      자주 합치면 내려감
             안  합치면 올라감       안  합치면 올라감

    lazy  : 쓰기 14,780 / 없는 키 조회 10 / 장 10
    eager : 쓰기 95,080 / 없는 키 조회  1 / 장  1
    둘 다 같은 데이터를 담고 있고 답도 같다. 값만 다른 곳에서 치렀다
```

**더 생각할 것**

- 세 증폭은 "성능"이 아니라 **회계 항목**이다. 어디서 비용을 낼지 고르는 것이지 없애는 것이 아니다.
- 실무 LSM 의 튜닝 파라미터(레벨 크기 배수, compaction 트리거, memtable 크기)는 전부 이 삼각형 안에서 점을 옮기는 손잡이다.
- 서로 다른 키만 넣으면 공간 증폭이 1.0 이다(`distinctKeysDoNotAmplify`) — 공간 증폭은 구조의 성질이 아니라 **덮어쓰기 비율**의 함수다.

#### 8. 부분 compaction 에서 tombstone 을 지우면 왜 삭제가 되살아나는가

- Q: 왜 되살아나는가?\
  A: tombstone 은 옛 값을 **지운 것이 아니라 위에서 가리고 있는** 것이기 때문이다.\
  부분 compaction 은 위쪽 몇 장만 합치고 아래층은 손대지 않는다.\
  그 상태에서 가리개를 버리면 가려지던 옛 값은 그대로 남은 채 가리개만 사라진다.\
  그러면 조회가 합쳐진 장에서 아무것도 못 찾고 아래로 내려가, 죽었어야 할 값을 답으로 물어온다.

```
TombstoneTest.Resurrection.threeLayers() 가 만드는 상태

    t.put(7, "old"); t.flush();
    t.delete(7);     t.flush();
    t.put(1, "a");   t.flush();

    index 0 (최신)    SST { 1 = "a" }
    index 1           SST { 7 = MARKER }      <- 가리개
    index 2 (가장 옛)  SST { 7 = "old" }       <- 가려진 옛 값

    get(7) : index0 에 없음 -> index1 에서 MARKER 를 만나 멈춤 -> null      (맞다)


[ 틀린 경우 ]  compactNewest(2) 를 dropTombstones = true 로 합치면

    합친 결과 (index 0)                아래에 그대로 남은 장 (index 1)
    +--------------------+             +--------------------+
    | SST { 1 = "a" }    |             | SST { 7 = "old" }  |
    +--------------------+             +--------------------+
      7 의 흔적이 통째로 없어졌다

    get(7) : index0 에 없음 -> index1 에서 "old" 를 만나 멈춤 -> "old"     (틀렸다)
             지운 적 있는 키가 되살아났다


[ 맞는 경우 ]  dropTombstones = false 로 합치면

    합친 결과 (index 0)                아래에 그대로 남은 장 (index 1)
    +--------------------+             +--------------------+
    | SST { 1 = "a",     |             | SST { 7 = "old" }  |
    |       7 = MARKER } |             +--------------------+
    +--------------------+
      가리개를 결과에 데리고 내려왔다

    get(7) : index1 을 볼 일이 없다 -> null                                (맞다)
```

```java
// TombstoneTest.Resurrection.droppingItResurrectsTheOldValue — 함정을 그대로 재현한다
SSTable<Integer, String> wrong =
        Compactor.compact(List.of(newest, middle), true, false);
assertNull(wrong.rawValue(7), "tombstone 을 지우면 그 키의 흔적이 통째로 없어진다");
assertEquals("old", layeredGet(List.of(wrong, oldest), 7),
        "그래서 조회가 아래층까지 내려가 죽은 값을 물어온다");

SSTable<Integer, String> right =
        Compactor.compact(List.of(newest, middle), false, false);
assertTrue(Tombstone.is(right.rawValue(7)));
assertNull(layeredGet(List.of(right, oldest), 7), "남겨두면 삭제가 유지된다");
```

> **되살아남(resurrection)** — 지운 키가 아래층의 옛 값 때문에 다시 조회되는 현상.\
> 예: 가리개인 tombstone 만 버리고 그 아래 `7="old"` 를 남겨 두면 `get(7)` 이 `"old"` 를 돌려준다.

- Q: **합친 직후에는 왜 아무 증상이 없는가**?\
  A: 합친 결과 장만 놓고 보면 완벽하게 정상이기 때문이다.\
  키는 정렬되어 있고, 이진 탐색도 되고, 살아 있는 값도 다 맞다 — `1 = "a"` 는 그대로다.\
  틀린 것은 그 장 안이 아니라 **그 장과 아래층의 관계**이고, 관계는 장 하나를 검사해서는 보이지 않는다.\
  게다가 방금 합친 위쪽 두 장만 읽는 조회는 계속 맞는 답을 낸다.\
  증상은 조회가 아래층까지 내려갈 때, 즉 그 키를 실제로 찾을 때만 나타난다.

- Q: 아래층이 살아 있는 동안만 조용히 틀리는 이유는?\
  A: 되살아날 옛 값이 아래층에 남아 있어야 되살아나기 때문이다.\
  나중에 맨 아래층까지 포함하는 compaction 이 한 번 돌면 그 옛 값도 걷혀 증상이 저절로 사라진다.\
  즉 버그가 고쳐지지 않았는데 증상만 없어진다 — 재현이 안 되는 버그가 되는 것이다.\
  그 사이에 조회한 사용자는 이미 죽은 값을 받아 갔고, 로그에는 예외도 경고도 남지 않는다.\
  이런 종류의 실패는 "틀린 값이 나온다"보다 "언제 틀리는지 모른다"가 더 위험하다.

> **조용한 실패(silent failure)** — 예외도 경고도 없이 정상처럼 끝나는데 결과만 틀린 실패.\
> 예: 부분 compaction 이 tombstone 을 버려도 컴파일·실행·직후 조회가 전부 정상이고, 특정 키를 찾을 때만 옛 값이 나온다.

- Q: `dropTombstones` 가 언제만 `true` 여야 하는가?\
  A: **합치는 범위가 맨 아래층까지 포함할 때만** — 즉 bottommost 일 때만이다.\
  아래에 안 합친 장이 하나라도 남아 있으면 그 장에 옛 값이 있을 가능성이 있고, 그 가능성 자체를 확인할 방법이 없다.\
  impl 은 이 조건을 계산이 아니라 한 줄의 비교로 못 박는다.

```java
// impl/LsmTree.java — 조건이 딱 하나다
public void compactNewest(int count) {
    ...
    boolean bottommost = count == sstables.size();      // 여기가 전부다
    List<SSTable<K, V>> target = new ArrayList<>(sstables.subList(0, count));
    SSTable<K, V> merged = Compactor.compact(target, bottommost, bloomEnabled);
    ...
}

@Override
public void compact() {
    flush();
    if (sstables.isEmpty()) {
        return;
    }
    compactNewest(sstables.size());     // 전체이므로 항상 bottommost 다
}
```

```java
// impl/Compactor.java — 버릴지 말지의 실제 분기
if (dropTombstones && Tombstone.is(value)) {
    continue;                           // 이 키는 결과에 아예 안 넣는다
}
out.add(SSTable.cell(best, value));
```

> **bottommost(맨 아래까지)** — 합치는 범위가 가장 오래된 장까지 포함한다는 뜻.\
> 예: `compactNewest(count)` 는 `count == sstables.size()` 일 때만 bottommost 이고, 그때만 tombstone 을 버려도 안전하다.

- Q: 이 조건이 지켜지는 것을 무엇이 확인하는가?\
  A: `TombstoneTest.Resurrection` 의 다섯 케이스가 서로 다른 각도에서 확인한다.\
  `partialCompactionKeepsTombstone` — `compactNewest(2)` 뒤에도 tombstone 이 1개 남아 있고 `get(7)` 이 null 이다.\
  `bottommostCompactionDropsIt` — `compactNewest(3)` 뒤에는 tombstone 이 0개이고 남은 엔트리도 1개뿐이다.\
  `twoStepCompactionIsStillCorrect` — 2장씩 두 번에 나눠 합쳐도 답이 같다.\
  `manyKeys` — 20개 키를 넣고 절반 지우고 4개마다 갱신한 뒤, 부분·전체 compaction 전후의 `rangeScan` 이 완전히 같은지 본다.

**더 생각할 것**

- 안전 조건이 "가능성이 없음을 증명할 수 있을 때만"이라는 형태인 점이 중요하다 — 실무 LSM 도 같은 판정을 하고, 여기에 시간 조건(카산드라의 gc_grace 류)까지 얹는다.\
  (시간 조건은 이 구현에 없다 — 원본 코드에 근거 없음.)
- 이 함정은 "성능 최적화가 정확성을 깬" 전형이다. tombstone 을 버리는 것은 순수한 공간 최적화인데, 조건 하나를 빠뜨리면 답이 바뀐다.
- 최적화를 넣을 때는 "이 최적화가 성립하는 전제"를 코드에 이름으로 남겨야 한다 — `bottommost` 라는 변수명이 그 역할을 한다.

#### 9. 층 순서가 왜 이 문제의 전부인가

- Q: `get` · `mergedLive` · `Compactor` 셋 중 하나만 뒤집어도 무엇이 잡히는가?\
  A: `LsmTreeCrossCheckTest` 의 **TreeMap 대조**가 잡는다.\
  세 곳이 전부 "앞이 최신"이라는 같은 약속 위에 서 있고, 하나만 어겨도 옛 판본이 답으로 올라온다.\
  TreeMap 은 제자리 갱신을 하는 정상 맵이므로 항상 최신 값을 들고 있고, 두 답을 스텝마다 비교하면 즉시 어긋난다.

```
impl 에서 "앞이 최신" 이 걸려 있는 자리 셋

  LsmTree.get           for (SSTable<K,V> table : sstables)
                            index 0 -> 끝 순서로 내려가며 처음 만난 값에서 멈춘다

  LsmTree.mergedLive    memtable 먼저, 그 다음 sstables 를 index 0 -> 끝 순서로
                            newest.putIfAbsent(key, value)
                            "이미 있으면 안 덮는다" 가 곧 "먼저 본 것이 최신" 이다

  Compactor.mergeEntries  newestFirst 의 index 가 작을수록 최신
                            같은 키를 만나면 winner 로 뽑힌 쪽(가장 작은 index)의 값을 채택

  셋 중 하나만 뒤집으면
      컴파일 된다          타입이 그대로다
      예외가 안 난다       정렬도 이진 탐색도 멀쩡히 돈다
      층이 한 장뿐이면 답도 맞다
      층이 여러 장이 되고 같은 키가 겹쳐야 비로소 틀린 값이 나온다
```

```java
// impl/LsmTree.java — mergedLive 의 "먼저 본 것이 이긴다"
TreeMap<K, Object> newest = new TreeMap<>();
for (Map.Entry<K, Object> e : memtable.entriesInOrder()) {
    if (inRange(e.getKey(), from, to)) {
        newest.putIfAbsent(e.getKey(), e.getValue());   // 이미 있으면 안 덮는다
    }
}
for (SSTable<K, V> table : sstables) {                   // index 0 부터, 즉 최신부터
    for (int i = 0; i < table.size(); i++) {
        K key = table.keyAt(i);
        if (inRange(key, from, to)) {
            newest.putIfAbsent(key, table.valueAt(i));
        }
    }
}
```

- Q: 왜 층이 여러 개가 되어야만 잡히는가?\
  A: 순서라는 것은 비교 대상이 둘 이상일 때만 뜻이 있기 때문이다.\
  장이 하나뿐이면 어느 방향으로 훑든 결과가 같아서 어떤 구현이든 통과한다.\
  그래서 대조 테스트는 그 조건을 **강제로** 만든다.

```
LsmTreeCrossCheckTest.matchesTreeMap 이 조건을 만드는 방법

    임계치 4 종 {1, 3, 16, 128}  x  각 2 만 스텝
        임계 1   : 쓸 때마다 새 층이 생겨 층이 수십 개가 된다
        임계 128 : 대부분이 memtable 에 머문다
        두 극단에서 답이 같아야 한다

    한 스텝의 연산 분포 (키 공간은 0..299 로 좁다)
        put       45%     같은 키를 계속 덮어쓴다 -> 층마다 같은 키가 겹친다
        delete    23%     tombstone 이 층 사이에 섞여 들어간다
        get       22%     TreeMap 과 즉시 대조
        rangeScan  5%     mergedLive 경로를 대조
        flush      3%     층을 인위적으로 늘린다
        compact    2%     층을 인위적으로 합친다

    끝난 뒤에도 keys / size / rangeScan 을 전부 대조하고,
    한 번 더 compact() 한 뒤 "compact 가 답을 바꾸면 안 된다" 까지 확인한다
```

- Q: 뒤집으면 컴파일도 되고 예외도 안 나는데 답만 틀리는 종류의 버그를 뭐라고 불러야 하는가?\
  A: **조용한 실패(silent failure)** 이고, 더 구체적으로는 **타입으로 잡히지 않는 의미 오류**다.\
  컴파일러가 보는 것은 "SSTable 목록을 순회한다"까지이고, 그 목록의 순서가 의미를 갖는다는 사실은 타입에 적혀 있지 않다.\
  예외도 안 난다 — 어느 방향으로 훑어도 배열 범위 안이고 이진 탐색도 정상이다.\
  그래서 이런 버그는 **불변식을 다른 구현과 대조해야만** 드러난다.\
  8번의 tombstone 함정과 정확히 같은 계열이고, 이 장에서 같은 교훈이 두 번 나온 셈이다.

> **불변식(invariant)** — 프로그램이 도는 내내 항상 참이어야 하는 성질.\
> 예: 여기서는 "sstables 의 index 가 작을수록 최신"이 불변식이고, 코드 세 곳이 전부 이 하나에 기대고 있다.

> **대조 테스트(cross-check / differential testing)** — 같은 입력을 믿을 수 있는 다른 구현에도 먹여 두 결과를 비교하는 방식.\
> 예: `LsmTreeCrossCheckTest` 는 `TreeMap` 을 정답지로 삼아 2만 스텝 동안 `get` · `rangeScan` · `keys` 를 매번 비교한다.

- Q: 그래서 README 가 `get` 부터 하라고 하는 이유는?\
  A: 세 곳 중 `get` 이 가장 짧고, 층 순서의 뜻이 가장 명확하게 드러나는 자리이기 때문이다.\
  `get` 에서 "최신부터, 처음 만난 것에서 멈춘다"를 몸으로 이해하면 `mergedLive` 의 `putIfAbsent` 도 `Compactor` 의 winner 선택도 같은 규칙의 다른 표현으로 읽힌다.\
  README 의 표현 그대로 "층 순서가 이 문제의 전부라서, 거기가 잡히면 나머지가 따라온다".

**더 생각할 것**

- 순서가 의미를 갖는 자료구조는 그 순서를 타입이나 이름으로 드러내야 한다 — 인자 이름이 `newestFirst` 인 것이 최소한의 방어다.
- 더 강한 방어는 순서를 못 뒤집게 만드는 것이다. 예를 들어 세대 번호를 엔트리에 달고 큰 쪽을 이기게 하면 순회 방향이 정확성에서 빠진다(그 대신 엔트리마다 공간이 든다 — 이 구현의 선택은 아니다).
- 무작위 대조는 "무엇이 틀렸는지"는 못 알려주고 "틀렸다"만 알려준다. 그래도 이런 버그에는 그것이 유일하게 통하는 그물이다.

#### 10. 최악의 사용 패턴과 가장 잘 맞는 워크로드

- Q: 있는 키를 무작위로 많이 읽는 패턴은 왜 나쁜가?\
  A: 블룸 필터가 못 줄이는 비용만 남는 패턴이기 때문이다.\
  키가 어느 층에 있는지 예측할 수 없으므로 평균 깊이가 층 수의 절반 이상이 된다.\
  블룸은 그 키가 **없는** 위층들만 건너뛰게 해 주는데, 마지막에 반드시 한 번은 진짜로 읽어야 한다.\
  1000개 조회에서 5,500 → 1,051 로 줄었지만 1,000 은 구조적 하한이다.\
  B+트리였다면 어느 키든 4번으로 끝났을 일이다.

- Q: 삭제 후 즉시 공간 회수를 기대하면 왜 나쁜가?\
  A: **삭제가 공간을 늘리기 때문이다.**\
  `TombstoneTest.StillThere.deleteGrowsStorage` 가 그 장면이다 — 10개를 넣고 flush 한 뒤 하나를 지우고 flush 하면 `storedEntryCount()` 가 10에서 **11로 늘고** `size()` 만 9로 준다.\
  지운 키를 지우는 데 엔트리 하나를 더 쓴 것이다.\
  tombstone 도 순차 쓰기 바이트를 낸다 — `tombstonesCostBytes` 가 키 하나 삭제에 9바이트(머리 8 + 키 1 + 값 0)를 assert 한다.\
  공간은 compaction 이 돌아야 비로소 줄고, 그전까지는 늘기만 한다.

- Q: `size()` 를 자주 부르면 왜 나쁜가?\
  A: `size()` 가 **전체 병합**이기 때문이다.\
  `impl/LsmTree.java` 의 `size()` 는 `mergedLive(null, null).size()` 이고, `mergedLive` 는 memtable 과 모든 SSTable 의 모든 엔트리를 훑어 TreeMap 하나를 새로 만든다.\
  즉 한 번 부를 때마다 O(저장된 전체 엔트리 x log(산 키 수)) 가 들고, 임시 TreeMap 만큼의 메모리도 그때그때 잡는다.\
  20만 개가 들어 있으면 `size()` 한 번이 20만 엔트리 순회다.\
  `isEmpty()` 도 `size() == 0` 이라 같은 비용이고, `keys()` 와 `rangeScan` 도 같은 경로를 탄다.

```java
// impl/LsmTree.java — 셋 다 mergedLive 를 탄다
@Override
public int size() {
    return mergedLive(null, null).size();
}

@Override
public boolean isEmpty() {
    return size() == 0;          // 전체 병합을 한 번 더 한다
}

@Override
public List<K> keys() {
    List<K> out = new ArrayList<>();
    for (Map.Entry<K, V> e : mergedLive(null, null)) {
        out.add(e.getKey());
    }
    return out;
}
```

> **워크로드(workload)** — 실제로 어떤 연산이 어떤 비율로 들어오는가의 분포.\
> 예: 같은 LSM 이라도 "쓰기 99% / 최근 키 읽기"면 최적이고 "오래된 키 무작위 읽기 + size() 폴링"이면 최악이다.

- Q: 반대로 가장 잘 맞는 워크로드는?\
  A: **쓰기가 압도적으로 많고, 읽더라도 최근에 쓴 것을 읽는** 워크로드다.\
  README 가 든 로그·시계열·이벤트 스트림이 정확히 그 모양이다.\
  쓰기는 memtable 한 번이라 디스크를 아예 안 건드리고(`memtableIsFree` 가 `diskReads()` 0을 assert 한다), 최근 키는 index 0 에서 끝난다(`get(999)` 가 1번).\
  키가 대체로 서로 다르면 공간 증폭도 1.0 에 머문다(`distinctKeysDoNotAmplify`).\
  범위 조회도 잘 맞는다 — 모든 장이 정렬되어 있어 `rangeScan` 이 훑기로 끝난다.\
  즉 "덧붙이기만 하고, 최근 것을 읽고, 정렬 순서로 훑는" 패턴이 이 구조가 설계된 모양 그 자체다.

| 패턴 | 이 구조에서 | 근거 |
|---|---|---|
| 순차 쓰기 폭주 (로그·시계열) | 최적 — 디스크 접근 0 | `memtableIsFree` |
| 최근 키 읽기 | 최적 — 1회 | `costDependsOnLayer` (get(999)=1) |
| 정렬 범위 훑기 | 좋음 — 모든 장이 정렬됨 | `rangeScanIsInclusive` |
| 오래된 키 무작위 읽기 | 나쁨 — 층 깊이만큼 | 5500 / 1051 |
| 없는 키 조회 | 블룸 켜면 최적, 끄면 최악 | 955 vs 100,000 |
| 삭제 후 즉시 공간 회수 기대 | 나쁨 — 오히려 는다 | `deleteGrowsStorage` |
| `size()` 폴링 | 나쁨 — 매번 전체 병합 | `size()` = `mergedLive(null,null)` |
| 같은 키 고빈도 갱신 | 공간 증폭 폭발 | 100.0 |

- Q: "삭제했는데 디스크가 안 줄어든다"는 카산드라 운영의 고전적 질문에 대한 답은?\
  A: README 의 답 그대로 **"compaction 이 돌 때까지 기다려라"** 다.\
  삭제는 데이터를 지우는 명령이 아니라 "지웠다"는 기록을 추가하는 명령이고, 그래서 실행 직후에는 저장량이 오히려 는다.\
  실제로 줄어드는 시점은 그 tombstone 과 그것이 가리던 옛 값이 **같은 compaction 범위에 함께 들어갈 때**다.\
  게다가 8번에서 본 이유로, 그 compaction 이 맨 아래층까지 포함해야만 tombstone 자체도 버릴 수 있다.\
  그러니 답은 두 겹이다 — 기다려야 하고, 기다리는 대상은 "아무 compaction"이 아니라 "맨 아래까지 포함하는 compaction"이다.

**더 생각할 것**

- `containsKey` 는 `get(key) != null` 이라 조회 한 번 비용이고, `size()` 는 전체 병합 비용이다.\
  이름만 보면 둘 다 가벼워 보이는데 비용 차이가 수십만 배가 날 수 있다.
- 실무 LSM 저장소들이 정확한 count API 를 잘 안 주는 이유가 이것이다 — 줄 수는 있지만 그 비용을 사용자가 예상하지 못한다.\
  대신 근사치나 별도 카운터를 준다.
- "최악의 패턴"은 대개 API 를 잘못 써서가 아니라 **다른 저장소의 습관을 그대로 가져와서** 생긴다.\
  B+트리 감각으로 `size()` 를 부르면 여기서는 재앙이다.

#### 11. 구현 전략의 트레이드오프

- Q: memtable 임계치를 키우면/줄이면 무엇이 어떻게 변하는가?\
  A: 키우면 층이 적어져 읽기가 싸지고, 같은 키의 갱신이 메모리 안에서 흡수되어 공간·쓰기 증폭도 줄어든다.\
  대신 메모리를 더 오래 더 많이 붙잡고, WAL 이 없는 이 구현에서는 잃을 수 있는 데이터의 양이 그만큼 커진다.\
  줄이면 반대다 — 메모리는 적게 쓰고 유실 창도 짧지만 층이 폭발해 읽기가 나빠진다.

```
임계치가 만드는 차이 (전부 테스트에 assert 된 값이다)

    임계 4    + 키 12 개    ->  SSTable 3 장,   flushCount 3,   136 바이트
                                (LsmTreeTest.AutoFlush.threeTables)

    임계 100  + 키 1000 개  ->  SSTable 10 장,  14,780 바이트
                                (ReadAmplificationTest.tenTables / SpaceAmplificationTest)

    임계 4096 + 키 20 만 개 ->  SSTable 48 장   (200000 / 4096 의 정수 몫)
                                (LsmTreeCrossCheckTest.twoHundredThousand)

    임계 1   : 쓸 때마다 새 층. 층이 수십 개가 된다
    임계 128 : 대부분이 memtable 에 머문다
                                (LsmTreeCrossCheckTest.matchesTreeMap 주석)


임계치는 "키 개수" 로 재지 바이트로 재지 않는다
    LsmTree.write : if (memtable.size() >= memtableThreshold) flush();
    memtable 은 맵이라 같은 키를 덮어쓰므로 size 가 안 는다

    임계 4 인데 put(42, ...) 를 100 번 해도
        sstableCount  = 0        flush 가 한 번도 안 일어났다
        memtableSize  = 1
        get(42)       = "v99"
                                (LsmTreeTest.AutoFlush.sameKeyNeverFills)
    -> 큰 memtable 은 갱신을 메모리 안에서 흡수해 디스크로 내려보내지 않는다
       그만큼 쓰기 증폭과 공간 증폭이 함께 준다
```

> **flush** — 가득 찬 MemTable 을 SSTable 로 굳혀 내리고 MemTable 을 비우는 것.\
> 예: 정렬이 이미 끝나 있으므로 앞에서부터 흘려 쓰기만 하면 되고, 이것이 "순차 쓰기"의 실제 내용이다.

- Q: 블룸 필터를 켜고 끄는 것은?\
  A: 켜면 **없는 키 조회가 사실상 공짜**가 되고(100,000 → 955), 있는 키도 위층 헛읽기가 잘려 5,500 → 1,051 이 된다.\
  끄면 `SSTable.mightContain` 이 항상 true 라 필터가 없는 것과 같아져 모든 장을 실제로 뒤진다.\
  대가는 메모리와 생성 비용이다 — 장당 엔트리 100개에 959비트(원소당 9.59비트)를 더 들고, flush 마다 키 개수만큼 해시 7번씩을 계산한다.\
  답은 어느 쪽이든 같다(`sameAnswers`), 저장 엔트리 수도 같다 — **블룸은 읽기 증폭만 건드리고 다른 두 증폭에는 아무 영향이 없다.**\
  그래서 "메모리를 조금 내고 읽기를 크게 산다"는 거래이고, 없는 키 조회가 많은 워크로드일수록 이득이 커진다.

- Q: 전체 compaction 과 부분 compaction 은?\
  A: 전체(`compact()`)는 flush 부터 하고 모든 장을 한 번에 합치므로 **항상 bottommost** 이고, 그래서 tombstone 을 버릴 수 있다.\
  대가는 한 번의 비용이 데이터 전체 크기라는 점이다 — 1000개를 합칠 때 14,780 바이트를 통째로 다시 쓴다.\
  부분(`compactNewest(k)`)은 위 k 장만 건드려 한 번의 비용이 작지만, k < 전체이면 tombstone 을 못 버려 공간 회수가 불완전하다.\
  또 부분 compaction 을 반복하면 같은 데이터를 여러 번 다시 쓰게 되어 누적 쓰기 증폭이 커진다 — 7번의 80,300 이 그 누적이다.\
  정확성은 둘 다 보장된다 — `twoStepCompactionIsStillCorrect` 와 `manyKeys` 가 "부분 compaction 이 답을 바꾸면 안 된다"를 확인한다.

| 전략 | 얻는 것 | 내주는 것 | 언제 |
|---|---|---|---|
| 큰 memtable | 층 적음, 갱신 흡수 | 메모리, 유실 창 | 쓰기 폭주·갱신 많음 |
| 작은 memtable | 메모리 적음, 유실 창 짧음 | 층 폭발, 읽기 증폭 | 메모리가 빠듯할 때 |
| 블룸 켬 | 없는 키 조회 104배 | 키당 9.59비트, 해시 계산 | 없는 키 조회가 많을 때 |
| 블룸 끔 | 메모리 0 | 모든 장을 실제로 읽음 | 키가 거의 항상 존재할 때 |
| 전체 compaction | tombstone 회수, 층 1장 | 한 번의 비용 = 전체 크기 | 조용한 시간대 |
| 부분 compaction | 한 번이 쌈, 멈춤 짧음 | tombstone 못 버림, 누적 쓰기 | 상시 백그라운드 |

- Q: 실무 LSM 과 다른 점 셋이 각각 무엇을 못 하게 하는가?\
  A: README 가 드는 셋은 **평평한 층 · WAL 없음 · TreeMap memtable** 이다.

```
1. 평평한 층 (leveled compaction 이 없다)

    여기 : SSTable 이 그냥 한 줄로 쌓인다. 크기 제한도 층 개념도 없다
           compact() 는 언제나 전부를 합친다 -> 한 번의 비용이 데이터 전체 크기

    못 하는 것 : "지금 합쳐야 이득인 장들만 고른다" 는 판단
                 데이터가 100GB 면 compaction 한 번이 100GB 다
                 겹치는 키 범위가 없는 장들을 병렬로 합치는 것도 불가능하다

2. WAL 이 없다

    여기 : memtable 은 메모리에만 있고, flush 전에는 디스크에 흔적이 없다
           impl 에 복구 경로도 로그 파일도 아예 없다

    못 하는 것 : 죽었다 살아나기
                 프로세스가 꺼지면 memtable 에 있던 것은 그대로 잃는다
                 임계치를 키울수록 잃을 양이 커진다 -> "큰 memtable" 이 공짜가 아닌 진짜 이유

3. memtable 이 TreeMap 이다

    여기 : java.util.TreeMap 한 개. 단일 스레드 전제다

    못 하는 것 : 락 없는 동시 삽입
                 실무는 12번 스킵 리스트를 쓰는데, 리스트 연결만 갈아끼우면 되어
                 여러 스레드가 동시에 넣어도 전역 락이 필요 없기 때문이다
                 TreeMap 은 회전으로 구조가 광범위하게 바뀌어 그 방식이 안 통한다
```

> **WAL(Write-Ahead Log, 선행 기록 로그)** — 메모리에 반영하기 전에 "이런 변경을 할 것이다"를 먼저 순차로 기록해 두는 파일.\
> 예: 실무 LSM 은 memtable 에 넣기 전에 WAL 에 써 두어, 죽었다 살아나면 WAL 을 다시 읽어 memtable 을 복원한다.

> **leveled compaction(레벨 다지기)** — SSTable 을 크기가 정해진 여러 레벨로 나누고, 레벨 간으로만 합치는 정책.\
> 예: 이 구현은 층이 평평해 compaction 대상을 고를 정책 자체가 없고, 그래서 `compact()` 가 언제나 전부를 다시 쓴다.

> **스킵 리스트(skip list)** — 여러 층의 연결 리스트로 정렬 순서를 유지하는 확률적 자료구조(12번).\
> 예: 삽입이 링크 몇 개를 갈아끼우는 것으로 끝나 락 없는 동시 삽입이 가능하고, 그래서 실무 LSM 의 memtable 자리에 쓰인다.

**더 생각할 것**

- 세 차이가 전부 같은 방향이다 — **동시성과 장애 복구를 뺐다.** 자료구조의 뼈대를 보기 위해 운영의 살을 발라낸 것이다.
- 그래서 이 구현의 벤치마크 수치는 실무 수치가 아니다. WAL 이 있으면 쓰기가 한 번 더 늘고, leveled 면 compaction 비용의 모양이 완전히 달라진다.
- 반대로 뼈대는 그대로다 — 증폭 셋의 삼각형, tombstone 의 bottommost 조건, 층 순서 불변식은 실무 엔진에서도 똑같이 성립한다.

#### 12. 구조 테스트가 리플렉션으로 못 박는 것

- Q: 리플렉션으로 무엇을 보는가?\
  A: 밖에서 값만 봐서는 확인할 수 없는 **"고칠 통로가 아예 없다"** 를 본다.\
  `SSTableStructureTest.Immutable` 의 세 테스트가 각각 다른 통로를 막는다.

```java
// SSTableStructureTest.Immutable.allFieldsFinal
for (Field f : SSTable.class.getDeclaredFields()) {
    assertTrue(Modifier.isFinal(f.getModifiers()),
            "SSTable." + f.getName() + " 이 final 이 아니다");
}
assertTrue(Modifier.isFinal(SSTable.class.getModifiers()),
        "SSTable 자체도 final 이어야 상속으로 뚫을 수 없다");
```

```java
// SSTableStructureTest.Immutable.noMutators
String[] forbidden = {"set", "add", "put", "remove", "delete", "clear", "insert",
        "update", "merge", "sort", "fill"};
for (Method m : SSTable.class.getDeclaredMethods()) {
    for (String prefix : forbidden) {
        assertFalse(m.getName().startsWith(prefix),
                "SSTable." + m.getName() + " 은 고치는 메서드로 보인다");
    }
}
```

```java
// SSTableStructureTest.Immutable — 필드를 이름으로 꺼내 온다
private static Object[] internal(SSTable<Integer, String> t, String name) throws Exception {
    Field f = SSTable.class.getDeclaredField(name);   // "keys" / "values"
    f.setAccessible(true);
    return (Object[]) f.get(t);
}
```

> **리플렉션(reflection)** — 실행 중에 클래스의 필드·메서드·수식어를 프로그램이 직접 들여다보는 기능.\
> 예: `SSTable.class.getDeclaredFields()` 로 필드 목록을 받아 전부 `final` 인지 확인하는 것이 리플렉션이다.

> **불변(immutable)** — 만든 뒤 절대 바꾸지 않는 것. 자바에서는 필드 `final` + 클래스 `final` + 고치는 메서드 없음이 그 최소 조건이다.\
> 예: `SSTable` 은 세 조건을 다 갖춰, "제자리를 안 고친다"는 설계 원칙이 문법 수준에서 강제된다.

- Q: `final` 세 겹이 각각 막는 것은 무엇인가?\
  A: 필드 `final` 은 만들어진 뒤 다른 배열로 **갈아끼우는 것**을 막는다.\
  클래스 `final` 은 상속해서 메서드를 덮어쓰고 고치는 동작을 끼워 넣는 것을 막는다.\
  고치는 메서드가 없다는 것은 **정상 API 에 고치는 통로가 아예 없음**을 뜻한다.\
  여기에 `copiesTheInput` 이 네 번째 통로를 막는다 — 생성자에 넘긴 목록을 밖에서 비워도 테이블은 그대로다.\
  `entriesIsACopy` 가 다섯 번째를 막는다 — `entries()` 가 매번 새 목록이라 밖에서 고쳐도 내부가 안 흔들린다.\
  `readsDoNotChangeAnything` 은 1000번 무작위 조회 뒤에 `keys` / `values` 배열이 `Arrays.equals` 로 같은지 본다 — 읽기가 내부를 바꾸지 않음까지 확인한다.

- Q: **필드 이름이 계약**이라는 것이 무슨 뜻인가?\
  A: 테스트가 `getDeclaredField("keys")` 처럼 **이름 문자열로** 내부를 꺼내 보기 때문에, 이름을 바꾸면 컴파일은 되는데 테스트가 깨진다는 뜻이다.\
  보통 `private` 필드 이름은 구현 세부라 자유롭게 바꿔도 되는데, 여기서는 그렇지 않다.\
  README 가 못 박는 대로 `keys`, `values`, `bytes`, `bloom` 이 이름 그대로 계약의 일부다.\
  이것은 "구조 자체가 요구사항"인 문제에서 나오는 성질이다 — 값이 맞느냐가 아니라 **어떻게 담고 있느냐**를 채점하기 때문이다.\
  대가도 분명하다 — 리팩토링 자유도가 줄고, 테스트가 구현에 단단히 묶인다.

> **구조 테스트** — 결과값이 아니라 내부 구조(필드·수식어·메서드 목록)를 검사하는 테스트.\
> 예: "제자리를 안 고친다"는 성질은 어떤 입출력으로도 증명할 수 없어서, 통로가 없다는 것을 직접 확인하는 수밖에 없다.

- Q: 그런데 여기서도 테스트가 못 잡는 코드가 나온다 — `h2 == 0` 은 무엇인가?\
  A: 블룸 필터의 이중 해싱에서 두 번째 해시가 0 이 되는 경우를 막는 방어다.

```java
// impl/TinyBloomFilter.java
int[] indexes(Object item) {
    long h = mix64(item == null ? 0 : item.hashCode());
    int h1 = (int) h;
    int h2 = (int) (h >>> 32);
    if (h2 == 0) {          // 이 두 줄을 지워도 72 개가 다 통과한다
        h2 = 1;
    }
    int[] out = new int[hashCount];
    for (int i = 0; i < hashCount; i++) {
        out[i] = Math.floorMod(h1 + i * h2, bits);
    }
    return out;
}
```

> **이중 해싱(double hashing)** — 해시 두 개(h1, h2)를 섞어 `h1 + i*h2` 로 여러 개의 자리를 싸게 만들어 내는 요령.\
> 예: 해시 함수를 7개 따로 만드는 대신 64비트 해시 하나를 위아래로 쪼개 h1, h2 로 쓰고 7개 자리를 계산한다.

- Q: 왜 안 잡히는가?\
  A: `h2 == 0` 이면 `h1 + i*h2` 가 i 와 무관하게 전부 `h1` 이 되어, 7개 자리를 켜는 대신 **한 자리만** 켠다.\
  그 키의 오탐 확률이 그 키에 한해서만 나빠질 뿐, **위음성은 생기지 않는다** — `add` 와 `mightContain` 이 같은 `indexes` 를 쓰므로 담은 키는 여전히 통과한다.\
  즉 정확성이 안 깨지고 품질만 살짝 나빠지는데, 그 "살짝"이 관측되려면 `mix64` 결과의 상위 32비트가 정확히 0 인 키가 테스트 입력에 들어와야 한다.\
  그 확률이 키 하나당 약 2^-32 이고, 이 테스트들이 다루는 키 수로는 사실상 절대 안 나온다.\
  그래서 두 줄을 지워도 72개가 전부 통과한다 — 방어가 필요하다는 것을 테스트가 증명해 주지 못한다.

- Q: 같은 자리에 있는 `SSTable` 생성자의 정렬 전제 검사는 왜 다른가?\
  A: 도달 불가능하다는 점은 같은데 **테스트가 직접 그 입력을 만들 수 있다**는 점이 다르다.\
  정상 경로에서 생성자에 들어오는 목록은 항상 `MemTable.entriesInOrder()` 나 `Compactor.mergeEntries()` 의 결과라 이미 정렬되어 있다.\
  그런데 생성자가 **공개 API** 라서 테스트가 어긋난 목록을 직접 넣어 볼 수 있다.\
  그래서 이 검사를 지우면 2개가 무너진다 — `rejectsUnsorted`(3 다음에 1) 와 `rejectsDuplicates`(같은 키 두 번).\
  README 의 표현대로 "정상 경로에서는 도달할 수 없지만" 이쪽은 테스트가 잡고 `h2 == 0` 은 못 잡는다.

```
두 방어의 차이

                      정상 경로에서 도달?   테스트가 그 입력을 만들 수 있나?   지우면
    h2 == 0 방어            불가능                  불가능 (확률 2^-32)         72개 다 통과
    정렬 전제 검사          불가능                  가능 (생성자가 공개 API)     2개 실패

    -> "도달 불가" 와 "검증 불가" 는 다른 말이다
       공개 API 는 도달 불가여도 밖에서 두드려 볼 수 있다
```

- Q: 11번 · 16번 · 18번 · 22번에 이은 다섯 번째에서 반복되는 교훈은?\
  A: **"테스트가 다 통과했다"는 "코드가 다 맞다"가 아니다** — 같은 문장이 다섯 번째로 확인된 것이다.\
  README 가 든 목록은 16번 뿌리 색, 18번 `nextSetBit`, 22번 패딩 `Arrays.fill`, 그리고 11번의 같은 `h2 == 0` 이다.\
  다섯 개 전부 "지워도 다 통과하는데 지우면 안 되는" 코드이고, 그 이유도 같다 — **발생 확률이 아주 낮거나 정상 경로에서 도달 불가라 그물에 안 걸린다.**\
  그래서 남기는 방식도 같다: 지우지 않되, **테스트가 못 잡는다는 것을 알고** 남긴다.\
  테스트 스위트는 "무엇이 틀렸나"를 알려주는 도구이지 "무엇이 필요한가"를 알려주는 도구가 아니라는 것이 이 반복의 요점이다.

**더 생각할 것**

- 커버리지 100% 여도 이 두 줄은 실행된다 — 실행되지만 `h2 == 0` 가지가 안 타는 것이다.\
  분기 커버리지로 재도 그 가지는 영원히 0% 다.
- 이런 코드를 지키는 방법은 테스트가 아니라 **주석과 기록**이다. 원본이 README 에 다섯 개를 나열해 둔 것이 그 방법이다.
- 반대 위험도 있다 — "테스트가 못 잡으니 필요하겠지"로 아무 방어나 남기면 죽은 코드가 쌓인다.\
  구별 기준은 "지웠을 때 무엇이 어떤 확률로 나빠지는지 말할 수 있는가"이고, 여기서는 말할 수 있다(오탐률 저하, 2^-32).

#### 13. 챕터 전체의 매듭 — 자료구조 선택이 아니라 워크로드 선택

- Q: 15번은 제자리를 고쳐 **읽기**를 샀고 24번은 덧붙이기만 해서 **쓰기**를 샀다 — 이 대비를 어떻게 읽어야 하는가?\
  A: 두 구조가 **같은 물건을 서로 반대 방향으로 팔았다**고 읽어야 한다.\
  B+트리는 쓰기 때마다 제자리를 고치는 비용을 미리 내고, 그 대가로 조회를 언제나 높이 한 번(4번)으로 끝낸다.\
  LSM 은 그 비용을 안 내는 대신 조회가 층 수만큼 늘고 옛 판본이 쌓이는 빚을 진다.\
  어느 쪽도 총비용을 줄이지 않았다 — **비용을 내는 시점과 주체만 바꿨다.**\
  그래서 "무엇이 더 빠른가"라는 질문은 성립하지 않고, "내 워크로드에서 어느 쪽 계정이 싼가"만 성립한다.

```
같은 데이터, 같은 답, 다른 계산서

    15번 B+트리                        24번 LSM 트리
    ------------------------------     ------------------------------
    쓰기 : 잎을 찾아가 그 자리를 고침   쓰기 : memtable 에만. 디스크 0
           임의 쓰기 + 분할                   순차 쓰기만
    읽기 : 높이만큼 (4번)              읽기 : 층 수만큼 (최대 10번)
    삭제 : 즉시 자리에서 지움          삭제 : tombstone 을 새로 씀 (공간이 는다)
    공간 : 산 것만                     공간 : 옛 판본이 쌓임 (최대 100배)
    정리 : 필요 없음                   정리 : compaction 이 나중에 갚음

    읽기가 많으면 왼쪽이 싸고, 쓰기가 많으면 오른쪽이 싸다
    구조가 우열을 정하는 것이 아니라 워크로드가 정한다
```

- Q: "자료구조 선택이 아니라 워크로드 선택"이라는 말의 뜻은 무엇인가?\
  A: 자료구조를 고르는 행위가 사실은 **어떤 연산을 싸게 만들고 어떤 연산을 비싸게 둘지 고르는 행위**라는 뜻이다.\
  그래서 고르기 전에 알아야 하는 것은 자료구조의 성질이 아니라 내 워크로드의 비율이다 — 읽기 대 쓰기가 몇 대 몇인가, 읽는 키가 최근 것인가 오래된 것인가, 같은 키를 얼마나 자주 덮어쓰는가, 삭제가 얼마나 되는가.\
  이 장의 숫자들이 그 비율에 따라 얼마나 크게 갈리는지를 보여 준다 — 같은 구현에서 같은 조회가 1번이기도 하고 10번이기도 하다.\
  거꾸로 말하면 **워크로드를 재지 않고 고른 자료구조는 대개 틀린다.**\
  README 가 "다음" 절에서 이 말로 챕터를 닫는 이유가 그것이다.

> **워크로드 비율** — 연산 종류별 빈도의 분포. 자료구조의 실제 비용은 이 비율과 곱해져야 나온다.\
> 예: 없는 키 조회가 많으면 블룸 필터가 104배를 벌어 주지만, 키가 항상 존재하는 워크로드면 그 메모리가 그냥 낭비다.

- Q: 23번(조회가 쓰기)과 24번(쓰기를 미룸)의 대비는 어떻게 읽어야 하는가?\
  A: 둘 다 **연산의 비용이 그 연산 시점에 다 드러나지 않는** 구조인데, 미루는 방향이 정반대다.\
  23번 스플레이 트리는 조회가 구조를 바꾼다 — 접근한 노드를 뿌리로 끌어올리므로 읽기가 곧 쓰기다(23번 README 의 표에 "조회가 쓰기인가: 그렇다"가 그대로 적혀 있다).\
  즉 **읽는 순간에 미리 정리해 두고**, 그 덕에 다음 접근이 싸진다.\
  24번 LSM 은 반대다 — 쓰기가 정리를 전혀 안 하고 나중으로 미룬다.\
  그 미룬 일이 층으로 쌓여 읽기와 공간을 무겁게 만들고, compaction 이 돌 때 한꺼번에 청구된다.\
  한쪽은 비용을 **앞당겨** 지역성을 사고, 다른 쪽은 **미뤄서** 쓰기 처리량을 산다.

```
비용을 언제 내는가

    23번 스플레이 트리                   24번 LSM 트리
    ---------------------------          ---------------------------
    조회 시점에 미리 정리                쓰기 시점에는 아무것도 안 함
        읽기가 구조를 바꾼다                 정리를 전부 나중으로 미룬다
        얻는 것 : 최근 쓴 것이 얕다          얻는 것 : 쓰기가 순차 한 번
        내는 것 : 읽기에 쓰기 비용이 섞임    내는 것 : 읽기·공간의 빚, compaction

    공통점 : 한 연산의 비용을 그 연산 밖으로 옮긴다
    차이점 : 앞당기느냐(23) 미루느냐(24)
    상환 분석이 둘 다에 필요한 이유도 같다 - 한 번의 비용이 아니라 전체 비용을 봐야 한다
```

(23번과 24번의 이 대비는 원본 README 에 명시되어 있지 않다 — 두 챕터의 성질에서 끌어낸 해석이다. 원본이 명시한 것은 15번과 24번의 대비까지다.)

> **상환 분석(amortized analysis)** — 연산 하나의 최악이 아니라 연속된 n 번의 총비용을 n 으로 나눠 보는 회계.\
> 예: LSM 의 compaction 은 한 번이 데이터 전체 크기지만, 그 비용을 그 사이의 수많은 싼 쓰기가 나눠 갚는다.

- Q: 그래서 이 챕터를 한 문장으로 묶으면?\
  A: **디스크에서 비싼 것은 제자리를 고치는 일이고, 그 일을 안 하기로 하면 나머지 전부가 따라 바뀐다.**\
  삭제가 쓰기가 되고, 조회가 여러 층을 보게 되고, 공간이 부풀고, 대청소라는 새 연산이 생긴다.\
  블룸 필터도 tombstone 도 bottommost 조건도 전부 그 한 결정의 파생물이다.\
  그리고 그 결정이 옳은지는 구조가 아니라 워크로드가 답한다.

**더 생각할 것**

- 15번과 24번을 같이 쓰는 시스템도 흔하다 — 쓰기 경로는 LSM, 보조 인덱스는 B+트리 식으로 계정을 나눠 쓴다.\
  (이 구현에 근거는 없다 — 일반적인 설계 관행에 대한 내 서술이다.)
- 이 장에서 배운 판단 순서가 다른 주제에도 그대로 간다: 비싼 연산을 찾는다 → 그것을 안 할 수 있는지 본다 → 안 하면 무엇이 대신 비싸지는지 센다 → 그 비용이 내 워크로드에서 실제로 발생하는지 잰다.
- 마지막 단계를 건너뛰는 것이 가장 흔한 실수다. 앞의 셋은 문서로 할 수 있지만 넷째는 재 봐야만 안다.
