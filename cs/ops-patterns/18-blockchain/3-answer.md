# ops-patterns/18-blockchain — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 작성 방식: **2-summary를 닫고 기억만으로** 쓴다 → 실제 코드/원전으로 검증 → 틀린 부분만 수정.
> 기준 소스는 문서가 아니라 코드다.

⚠️ 정답은 Claude 초안(2026-09-14) — 원본 impl 코드·README 기준. 본인 검토 후 이 줄 삭제

## 정답

<!-- 1-question.md 의 절·번호와 1:1 대응. 질문 하나 = A 하나. -->

### A. 문제 (구현 대상: HashChain TODO 1~4 · ProofOfWorkChain TODO 5~6)

#### 1. HashChain — append / createBlock (TODO 1~2)

**정답 코드** (impl/HashChain.java):

```java
public Block append(List<String> transactions) {
    Block last = blocks.get(blocks.size() - 1);
    Block block = createBlock(blocks.size(), last.hash(), transactions);  // TODO 1
    blocks.add(block);                       // 맨 뒤 칸의 해시 = 새 칸의 앞 해시
    return block;
}

protected Block createBlock(int index, String previousHash, List<String> transactions) {
    Block draft = new Block(index, previousHash, transactions, 0, "");   // TODO 2
    return new Block(index, previousHash, transactions, 0, hashOf(draft));
}

// Block.payload() — 해시에 들어가는 것 전부:
//   index + "|" + previousHash + "|" + String.join(",", transactions) + "|" + nonce
```

- **"앞 해시를 안 담으면 그냥 목록"?**\
  → 각 칸이 독립이면 한 칸을 고쳐도 다른 칸이 아무것도 모른다.\
  내 해시가 **앞 칸의 해시를 포함해서** 계산되기 때문에 앞 칸의 변경이 뒤 칸의 불일치로 전파된다 — 이 한 줄이 목록을 사슬로 만든다.
- **블록 5를 고치면 왜 6에서 티가 나는가?**\
  → 5의 내용이 바뀌면 5의 payload 가 바뀌어 5의 해시가 달라진다.\
  그런데 6이 담고 있는 previousHash 는 옛 5의 해시라 안 맞는다.
- **payload 밖의 값?**\
  → 해시는 payload 문자열만 보고 계산되므로, 거기 안 들어간 값은 바꿔도 해시가 그대로다 — 검사가 잡을 수 없으니 보호되지 않는다.\
  **무엇을 넣을지가 무엇을 지킬지를 정한다.**
- **payload 의 구성?**\
  → 번호(index) | 앞 해시(previousHash) | 거래들(transactions) | nonce. 저장된 hash 자체는 안 들어간다(자기 지문을 자기 내용에 넣을 수 없다).
- **SHA-256 을 가져다 쓰는 이유?**\
  → 여기 필요한 성질은 "같은 해시가 나오는 다른 입력을 **일부러 만들 수 없다**"(충돌 저항)이다.\
  그런 성질은 직접 만드는 것이 아니라 검증된 것을 가져다 쓰는 것이다.\
  27번 머클 트리와 같은 자리.
- **05번 해시와의 차이?**\
  → 해시맵의 해시는 "고르게 흩어진다"(분포)면 충분했고 충돌은 체이닝으로 처리하면 그만이었다.\
  여기서는 충돌을 일부러 만들 수 있으면 위조가 성립하므로 암호학적 강도가 필요하다.

#### 2. HashChain — verify / rebuildFrom (TODO 3~4)

**정답 코드** (impl/HashChain.java):

```java
public TamperReport verify() {
    for (int i = 0; i < blocks.size(); i++) {
        Block block = blocks.get(i);
        if (block.index() != i) {                          // ① 번호
            return TamperReport.broken(i, "번호가 " + block.index() + " 다");
        }
        String recomputed = Hashing.sha256(block.payload());
        if (!recomputed.equals(block.hash())) {            // ② 내용 vs 해시
            return TamperReport.broken(i, "내용과 해시가 안 맞는다");
        }
        String expectedPrevious = i == 0 ? "0" : blocks.get(i - 1).hash();
        if (!block.previousHash().equals(expectedPrevious)) {  // ③ 앞 해시
            return TamperReport.broken(i, "앞 해시가 안 맞는다");
        }
        if (!meetsDifficulty(block)) {                     // ④ 작업 증명
            return TamperReport.broken(i, "작업 증명이 모자라다");
        }
    }
    return TamperReport.ok();
}

public int rebuildFrom(int index) {
    int rebuilt = 0;
    for (int i = index; i < blocks.size(); i++) {          // 연쇄: 끝까지
        Block old = blocks.get(i);
        String previous = blocks.get(i - 1).hash();        // 방금 다시 만든 앞 칸의 해시
        blocks.set(i, createBlock(i, previous, old.transactions()));
        rebuilt++;
    }
    return rebuilt;
}
```

- **넷이 잡는 공격?**\
  → ① 번호가 이어지나 — 칸 재배치(tamperIndex) ② 저장된 해시가 내용과 맞나 — 내용만 몰래 고침(tamper) ③ 앞 해시가 앞 칸과 맞나 — 칸 끼움·빠짐·앞 칸 변경 ④ 작업 증명이 되어 있나 — 작업 없이 붙임(appendWithoutWork).\
  하나라도 빠지면 **그 공격만** 통과한다.
- **번호 검사를 빼면?**\
  → 내용도 해시도 서로 맞고 앞 해시도 맞는데 **번호만 다른** 사슬(tamperIndex 가 만드는 것 — 번호를 바꾸고 해시를 새 번호에 맞게 재계산)이 통과한다.
- **난이도 검사를 빼면?**\
  → 공격자는 작업 없이 붙이는데 검사가 안 잡으니 작업 증명이 아무 의미가 없어진다 — 정직하게 만드는 쪽만 힘들어진다.
- **"어디부터인지"가 필요한 이유?**\
  → "어딘가 이상하다"로는 아무것도 못 한다.\
  처음 깨진 자리가 나와야 **그 앞은 믿고 그 뒤만 다시 받을 수 있다.**
- **두 위조의 검사 결과?**\
  → 3번 내용만 고침 → `#3 부터 깨짐: 내용과 해시가 안 맞는다`(② 위반).\
  3번 해시까지 고침 → 3번 자체는 맞아 보이지만 4번의 previousHash 가 안 맞아 `#4 부터 깨짐: 앞 해시가 안 맞는다` — 문제가 한 칸 뒤로 **밀릴 뿐** 사라지지 않는다.
- **한 칸으로 안 끝나는 이유?**\
  → index 칸을 다시 만들면 그 칸의 해시가 바뀌고, 다음 칸의 previousHash 가 또 안 맞는다.\
  그래서 끝까지 연쇄된다.
- **위조 비용과 한계?**\
  → 사슬 1000칸 만드는 데 해시 1,001회, 500번부터 위조는 **501회** — 1초면 위조가 끝나고 검사를 통과한다.\
  이 구조가 지키는 것은 "못 바꾼다"가 아니라 **"모르게 바꿀 수는 없다"** 뿐이라는 것을 숫자로 보여준다.
- **"티가 난다" ≠ "못 고친다"?**\
  → 티가 난다 = 검사하면 잡힌다(들고 있는 사람이 검사할 때).\
  못 고친다 = 아예 불가능.\
  rebuildFrom 을 돌려보면 해시 사슬은 전자만 준다는 것을 알게 된다 — 검사를 통과하는 위조 사슬을 싸게 다시 만들 수 있다.

#### 3. ProofOfWorkChain — createBlock / meetsDifficulty (TODO 5~6)

**정답 코드** (impl/ProofOfWorkChain.java):

```java
protected Block createBlock(int index, String previousHash, List<String> transactions) {
    long nonce = 0;
    while (true) {                                   // TODO 5
        Block draft = new Block(index, previousHash, transactions, nonce, "");
        String hash = hashOf(draft);
        if (Hashing.leadingZeros(hash) >= difficulty) {   // 이상(>=)이지 초과가 아니다
            return new Block(index, previousHash, transactions, nonce, hash);
        }
        nonce++;
        if (nonce < 0) {                             // 오버플로 감지
            throw new IllegalStateException("nonce 가 넘쳤다");
        }
    }
}

protected boolean meetsDifficulty(Block block) {     // TODO 6: 같은 판정
    return Hashing.leadingZeros(block.hash()) >= difficulty;
}
```

- **작업 증명의 절차?**\
  → payload 에 nonce 를 0, 1, 2, ... 로 바꿔 넣어가며 해시를 반복 계산하고, 해시 앞이 0 으로 difficulty 개 이상 이어지는 nonce 를 찾으면 멈춘다.\
  그런 해시는 우연히만 나오므로 평균 16^difficulty 번쯤 계산해야 한다(16진수 한 자리당 1/16).
- **왜 이상(>=)인가?**\
  → 조건은 "0 이 difficulty 개 **이상**".\
  초과(>)로 쓰면 난이도 0 이 실은 1 이 된다(0 개 초과 = 최소 1개).\
  만드는 쪽과 검사하는 쪽이 **둘 다** 초과면 자기들끼리는 일관되게 맞아서 기능 테스트로는 안 드러난다.
- **무엇을 세야 보이는가?**\
  → 비용(hashCalls).\
  난이도 0 인데 해시 계산이 12회가 아니라 235회쯤 나오면(실은 난이도 1의 비용) 판정이 어긋났다는 것이 보인다.
- **nonce 넘침?**\
  → long 이 오버플로하면 음수로 돌아 같은 nonce 들을 다시 도는 무한 루프가 될 수 있다.\
  난이도가 높으면 실제로 도달할 수 있으므로 `nonce < 0` 에서 던진다.
- **생성자 순서 문제?**\
  → 자바는 부모 생성자가 끝난 뒤에 자식 필드를 초기화한다.\
  부모 생성자(super())가 제네시스를 만들려고 자식의 createBlock 을 부르는 시점에 `difficulty` 필드는 아직 0 이라, 제네시스가 난이도 0 으로 만들어진다.\
  그래서 생성자 끝에서 `blocks.set(0, createBlock(0, "0", List.of()))` 로 **다시 만든다.**\
  (가상 메서드를 생성자에서 부르는 자바의 고전적 함정.)
- **같은 판정이어야 하는 이유?**\
  → 만들 때의 종료 조건과 검사할 때의 합격 조건이 다르면, 정직하게 만든 블록이 검사에 떨어지거나(만들기가 더 관대) 작업 안 한 블록이 통과한다(검사가 더 관대).\
  생산자와 검증자는 같은 계약을 봐야 한다.

### B. 개념

#### 4. 무엇을 지키고 무엇을 못 지키는가

- **지키는 것 한 문장?**\
  → "못 바꾼다"가 아니라 **"모르게 바꿀 수는 없다"** — 사슬을 들고 있는 사람이 검사만 하면 어디부터 바뀌었는지 안다.
- **해시 사슬 위조가 1초인 이유?**\
  → 다시 만드는 비용이 칸당 해시 1회뿐이라서다.\
  500칸 다시 만들기 = 해시 501회 — 위조를 막는 것이 구조에 아무것도 없다.
- **비대칭이 전부인 이유?**\
  → 만들기 = 평균 16^difficulty 회, 검사 = 해시 1회.\
  위조자는 고친 지점부터 칸마다 그 비용을 다시 치러야 하는데 검사자는 여전히 싸게 잡아낸다.\
  이 비용 차이가 작업 증명이 파는 것의 전부다.
- **난이도별 측정?**\
  → 10칸 만드는 데: 난이도 0 → 12회, 1 → 235회, 2 → 2,173회, 3 → **25,807회** — 난이도 한 칸마다 대략 16배씩 자란다.
- **실제 방어?**\
  → 위조자가 다시 만드는 **동안 정직한 사람들이 새 칸을 더 붙여서** 따라잡을 수 없게 되는 경쟁이다.\
  작업 증명은 그 경쟁을 성립시키는 도구일 뿐이고, 이 상자는 비용의 비대칭까지만 다룬다.
- **한 곳에만 있으면?**\
  → 그 한 곳을 가진 사람이 통째로 다시 만들면 그만이다(비교할 상대가 없다).\
  진짜 방어는 **여러 곳이 같은 사슬을 들고 비교하는 것**인데, 이 상자는 그것(분산·합의)을 안 다룬다.

#### 5. 연결 — 앞뒤 챕터와의 다리

- **규칙 vs 구조?**\
  → 16번의 "지우지 않고 붙인다"는 규칙이라 저장소를 만지는 사람이 어길 수 있었다.\
  여기서는 앞 해시 연결이라는 구조라 어기면(고치면) 검사에서 티가 난다 — 지키는 주체가 사람의 규율에서 자료구조로 옮겨갔다.
- **머클 트리와 같은 자리?**\
  → "같은 값을 일부러 만들 수 없다"는 암호학적 해시를 직접 만들지 않고 가져다 쓴다는 것, 그리고 해시로 변조를 감지하되 여러 곳의 비교가 진짜 방어라는 것.
- **살아남은 변종 셋의 공통점?**\
  → **전부 검사(verify) 쪽**이었다.\
  번호 검사·난이도 검사를 빼도 정상 경로(정직한 사슬)에서는 아무 차이가 없다 — 그 검사만 통과하는 공격(tamperIndex, appendWithoutWork)을 각각 만들어야 잡혔다.
- **19번으로의 다리?**\
  → 여기까지는 만드는 것·지키는 것을 다뤘다.\
  19번 우아한 종료는 **끝낼 때 무엇을 잃는가** — 여기까지 만든 것들이 종료 순간에 어떻게 무너지는지를 다룬다.
