# ops-patterns/16-event-sourcing — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 작성 방식: **2-summary를 닫고 기억만으로** 쓴다 → 실제 코드/원전으로 검증 → 틀린 부분만 수정.
> 기준 소스는 문서가 아니라 코드다.

⚠️ 정답은 Claude 초안(2026-09-14) — 원본 impl 코드·README 기준. 본인 검토 후 이 줄 삭제

## 정답

<!-- 1-question.md 의 절·번호와 1:1 대응. 질문 하나 = A 하나. -->

### A. 문제 (구현 대상: EventStore TODO 1~2 · AccountProjection TODO 3~4 · AccountService TODO 5~7)

#### 1. EventStore — append / readFrom (TODO 1~2)

**정답 코드** (impl/EventStore.java):

```java
public synchronized int append(String streamId, int expectedVersion,
                               List<AccountEvent> events) {
    List<AccountEvent> stream = streams.computeIfAbsent(streamId, k -> new ArrayList<>());
    if (stream.size() != expectedVersion) {
        // 그 사이에 남이 붙였다. 내가 읽은 상태가 이미 낡았다.
        conflicts++;
        throw new ConcurrentModificationException(streamId, expectedVersion, stream.size());
    }
    stream.addAll(events);              // 덮어쓰지 않는다. 뒤에 붙인다
    appends += events.size();
    return stream.size();
}

public synchronized List<AccountEvent> readFrom(String streamId, int fromVersion) {
    List<AccountEvent> stream = streams.getOrDefault(streamId, List.of());
    if (fromVersion >= stream.size()) {
        return List.of();
    }
    return List.copyOf(stream.subList(fromVersion, stream.size()));  // fromVersion 포함
}
```

- **왜 expectedVersion 을 비교하는가?**\
  → "내가 읽고 판단한 상태가 아직 그대로인가"를 붙이는 순간 검사하기 위해서다.\
  사건 개수 = 버전이므로, 개수가 다르면 내가 읽은 뒤 남이 붙인 것 — 내 판단의 근거가 이미 낡았다.\
  이 검사가 낙관적 잠금의 전부다.
- **버전이 안 맞는데 그냥 붙이면?**\
  → 사건이 사라지지는 않는다.\
  내 사건이 **남의 사건 위에 얹혀** 순서가 뒤엉킬 뿐이다.\
  예: 잔액 1000을 보고 "1000 출금 가능"이라 판단했는데 그 사이 남이 900을 출금했다면, 내 Withdrawn(1000)이 그 뒤에 붙어 접으면 잔액 -900 — 검증을 통과한 적 없는 상태가 만들어진다.
- **왜 목록만 봐서는 안 보이는가?**\
  → 목록에는 멀쩡한 사건들이 순서대로 들어 있을 뿐이다.\
  "이 사건이 어떤 상태를 보고 만들어졌는가"(판단의 근거)는 목록에 없다.\
  틀린 것은 사건이 아니라 **사건을 만들 때의 전제**다.
- **고치기·지우기가 없는 이유?**\
  → 고칠 수 있으면 "왜 이 값이 됐나"에 답할 수 없게 된다.\
  감사 로그가 원본이라는 이 패턴의 존재 이유가 무너진다.\
  잘못 붙인 사건은 되돌리는 사건을 붙인다(08번 보상과 같은 모양).
- **readFrom 경계를 한 칸 틀리면?**\
  → 사건 하나가 조용히 빠진다.\
  스냅샷(버전 n까지 접은 상태) 뒤를 `readFrom(n)` 으로 이어 붙일 때 그 하나가 빠져, `replayFrom(스냅샷, ...)` 결과가 처음부터 접은 것과 달라진다.\
  빠진 순간이 아니라 **재생 결과를 비교할 때**에야 드러난다.\
  fromVersion 번째를 **포함**해서 끝까지가 맞다(subList(fromVersion, size)).
- **사건 개수 = 버전이 성립하는 근거?**\
  → append-only 라서다.\
  고치거나 지우지 않으니 개수가 단조 증가하고, 개수 하나가 스트림의 상태 변화 지점 전부와 1:1 대응한다.

#### 2. AccountProjection — replay / apply (TODO 3~4)

**정답 코드** (impl/AccountProjection.java):

```java
public AccountState replay(List<AccountEvent> events) {
    AccountState state = AccountState.empty();     // TODO 3: 빈 상태부터
    for (AccountEvent event : events) {
        state = apply(state, event);
    }
    return state;
}

public AccountState apply(AccountState state, AccountEvent event) {
    return switch (event) {                        // TODO 4: 검증 없음
        case AccountEvent.Opened e ->
                new AccountState(e.accountId(), e.owner(), 0, false);   // 처음으로 되돌림
        case AccountEvent.Deposited e ->
                new AccountState(state.accountId(), state.owner(),
                        state.balance() + e.amount(), state.closed());
        case AccountEvent.Withdrawn e ->
                new AccountState(state.accountId(), state.owner(),
                        state.balance() - e.amount(), state.closed());  // 음수여도 그대로
        case AccountEvent.Closed e ->
                new AccountState(state.accountId(), state.owner(), state.balance(), true);
    };
}
```

- **apply 에 if 를 달면 안 되는 이유?**\
  → 사건은 이미 일어난 일이라 거절할 수 없다.\
  if 를 다는 순간 **어제 저장된 사건이 오늘 규칙에 걸려** 재생이 터진다 — 어제까지 마이너스 통장이 허용됐다면 잔액이 음수가 되는 사건이 실제로 저장돼 있다.\
  오늘의 규칙은 오늘 들어오는 명령에만 적용한다.
- **재생 결과?**\
  → 잔액 **-4000** (0 + 1000 - 5000).\
  이게 정답이다 — 그 출금은 옛 규칙에서 검증을 통과해 실제로 일어난 일이니까.
- **왜 "과거 부정"인가?**\
  → 그 사건 뒤에 붙은 모든 사건은 그 사건이 반영된 상태를 전제로 만들어졌다.\
  재생 중 하나를 거절하면 그 뒤의 사건 전부가 다른 전제 위에 접혀 어긋난다 — 역사를 중간에 바꾸면 그 이후가 전부 거짓이 되는 것과 같다.
- **Opened 가 앞 상태를 물려받으면?**\
  → 계좌를 닫고 같은 번호로 다시 열었을 때(Opened, Deposited, Closed, Opened 스트림) **옛 주인의 잔액이 새 주인에게 넘어간다.**\
  그래서 Opened 는 잔액 0·새 주인·closed=false 로 상태를 처음으로 되돌려야 한다.
- **왜 안 드러나는가?**\
  → "Opened 는 늘 스트림 맨 앞"이라고 믿는 동안에는 앞 상태가 어차피 empty 라 물려받아도 차이가 없다.\
  재개설(Opened 가 중간에 오는 스트림)이 생겨야 드러난다 — 정상 경로에서는 아무 차이가 없는 조용한 결함.
- **모르는 사건을 던져야 하는 이유?**\
  → 조용히 무시하면 그 사건이 통째로 사라진 것처럼 상태가 접히고, 상태가 **조용히** 틀린다.\
  새 사건 종류를 배포했다가 되돌린 뒤 실제로 일어나는 일이다.\
  이 코드는 sealed interface 라 switch 누락을 컴파일러가 잡지만, 실전에서는 JSON→사건 변환 자리에서 터진다.
- **replayFrom 의 용도와 전제?**\
  → 스냅샷(중간까지 접은 상태)에서 이어 접기 위한 것.\
  `replayFrom(스냅샷, readFrom(n)) = replay(전체)` 가 성립하려면 ① readFrom 경계가 정확하고 ② apply 가 결정적(같은 입력 → 같은 결과)이어야 한다.

#### 3. AccountService — open / deposit / withdraw (TODO 5~7)

**정답 코드** (impl/AccountService.java):

```java
public void open(String accountId, String owner) {
    int version = store.versionOf(accountId);        // [1] 읽은 버전을 기억
    AccountState state = projection.replay(store.read(accountId));
    if (state.exists()) {                            // TODO 5: 중복 개설 거절
        rejected++;
        throw new RejectedException("이미 있는 계좌다: " + accountId);
    }
    store.append(accountId, version, List.of(new AccountEvent.Opened(accountId, owner)));
}

public void deposit(String accountId, long amount) {
    int version = store.versionOf(accountId);        // TODO 6: 읽은 버전으로 붙인다
    AccountState state = require(accountId, version);
    if (state.closed()) { rejected++; throw new RejectedException("닫힌 계좌다: " + accountId); }
    store.append(accountId, version, List.of(new AccountEvent.Deposited(accountId, amount)));
}

public void withdraw(String accountId, long amount) {
    int version = store.versionOf(accountId);
    AccountState state = require(accountId, version);
    if (state.closed()) { rejected++; throw new RejectedException("닫힌 계좌다: " + accountId); }
    if (state.balance() < amount) {
        // 여기가 유일한 검증 자리다. 재생할 때는 이 판단을 안 한다.   // TODO 7
        rejected++;
        throw new RejectedException("잔액이 모자라다: " + state.balance() + " < " + amount);
    }
    store.append(accountId, version, List.of(new AccountEvent.Withdrawn(accountId, amount)));
}
```

- **네 단계?**\
  → ① 지금까지의 사건을 읽는다(read) ② 접어서 지금 상태를 만든다(replay) ③ 이 명령이 지금 상태에서 되는지 본다 — 검증은 여기뿐 ④ 되면 사건을 붙인다.\
  **①에서 읽은 버전**을 같이 준다.
- **중복 개설을 막는 이유?**\
  → 안 막으면 Opened 가 하나 더 붙고, apply 규칙상 그 사건이 상태를 처음으로 되돌린다 — 잔액이 0 이 되고 주인이 바뀐다.\
  사건 목록만 보면 멀쩡한 Opened 하나가 더 있을 뿐이라 이상이 안 보인다.
- **versionOf 를 다시 부르면?**\
  → append 의 버전 검사가 "지금 개수 == 지금 개수"가 되어 항상 통과한다.\
  읽은 뒤에 남이 붙였어도(내 판단 근거가 낡았어도) 그냥 통과 — 낙관적 잠금이 통째로 무의미해진다.\
  **자기가 [1]에서 읽은 버전**으로 붙여야 "내가 판단한 그 상태 그대로일 때만 붙는다"가 성립한다.
- **잔액 검증이 withdraw 에만 있는 이유?**\
  → 명령("출금해라")은 아직 안 일어난 일이라 거절할 수 있고, 사건("출금되었다")은 이미 일어난 일이라 거절할 수 없다.\
  검증은 명령을 사건으로 바꾸는 관문에서 한 번만 — 그 구별이 이 상자의 핵심이다.
- **두 예외의 구별?**\
  → RejectedException = **명령 거절**(잔액 부족·닫힌 계좌·중복 개설) — 업무 규칙 위반이니 재시도해도 소용없고, 사용자에게 알린다.\
  ConcurrentModificationException = **버전 충돌** — 규칙 위반이 아니라 타이밍 문제이니 **다시 읽고 다시 판단해서 다시 붙이면** 된다(고칠 수 있는 실패).
- **왜 매번 읽고 접는가?**\
  → 상태를 캐시로 들고 있으면 빠르지만 그 캐시가 낡았는지 알 방법이 없다 — 다른 프로세스가 그 사이 붙였을 수 있다.\
  그래서 매번 읽고, 읽은 버전을 붙일 때 같이 줘서 낡음을 append 순간에 잡는다.

### B. 개념

#### 4. 명령과 사건

- **차이 한 줄씩?**\
  → 명령 = "출금해라" — 하려는 일, 거절될 수 있다.\
  사건 = "출금되었다" — 이미 일어난 일, 거절할 수 없다.
- **과거형이 계약인 이유?**\
  → 이름이 과거형이라는 것 자체가 "이건 이미 일어났고 되돌릴 수 없다, 검증 대상이 아니다"를 코드 읽는 사람에게 강제하는 표식이다.
- **검증 시점?**\
  → 명령을 사건으로 바꿀 때(AccountService) 한 번만.\
  재생(apply)할 때는 절대 안 한다.
- **구별이 없으면?**\
  → 마이너스 통장 폐지처럼 규칙이 바뀐 순간, 옛 규칙에서 저장된 사건(음수 잔액을 만드는 출금)이 오늘 규칙의 검증에 걸려 재생이 터진다 — 데이터는 그대로인데 읽을 수 없는 계좌가 된다.

#### 5. 지우지 않고 붙인다

- **입금 중복 실수?**\
  → 지우는 것이 아니라 **반대되는 사건(Withdrawn(10000))을 붙인다.**
- **사건 개수?**\
  → 3개에서 4개로 **늘어난다.**\
  잔액은 원래대로 돌아가지만 기록은 는다.
- **08번과의 연결?**\
  → 사가의 보상과 같은 모양 — 롤백이 아니라 반대되는 일을 새로 한다.
- **실수가 남는 것?**\
  → 장점이다(이 패턴의 관점에서).\
  "실수가 있었고 언제 어떻게 고쳤다"까지가 감사 로그다 — 장부에서 줄을 긋지 않고 정정 항목을 새로 적는 것과 같다.\
  대가는 7절의 삭제 불가 문제로 돌아온다.

#### 6. 낙관적 잠금

- **펜싱 토큰과의 비교?**\
  → 같은 것: 낡은 근거로 하는 쓰기를 번호(버전/토큰)로 막는다.\
  다른 것: 락은 **먼저 잡고** 일하고(비관), 여기서는 **일단 하고 나서** 충돌이면 다시 한다(낙관) — 미리 잡지 않는다는 것뿐이다.
- **측정?**\
  → 스레드 8개 × 50번 = 성공 400건, 충돌로 거절 146건.\
  충돌이 나도 재시도로 전부 결국 성공했고 사건·잔액이 하나도 안 사라졌다는 것 — 즉 거절은 손실이 아니라 순서를 지키는 장치라는 것을 보여준다.
- **거절당하면?**\
  → 다시 읽고(새 버전·새 상태) 다시 판단해서 다시 붙인다.\
  고칠 수 있는 실패다.
- **언제 어느 쪽이 싼가?**\
  → 충돌이 드물면 낙관이 훨씬 싸다(잠그는 비용·대기가 없다).\
  같은 스트림에 경쟁이 심하면(conflicts 가 크면) 재시도가 반복돼 락(먼저 잡기)이 나아진다.

#### 7. 한계와 연결

- **읽기 비용?**\
  → 사건 수에 비례 — 사건이 만 개면 읽을 때마다 만 번 접는다(테스트 실측: 접기 횟수 = 사건 수).\
  **스냅샷**(버전 n까지 접어둔 상태 + `readFrom(n)` 이어 접기)으로 줄인다.
- **스냅샷의 역설?**\
  → 스냅샷은 다시 "저장된 상태"라서, 상태 저장을 피하려던 원래 문제(틀리면 왜 틀렸는지 모름)를 조금 되가져온다.\
  그래서 원칙: **스냅샷은 언제든 버리고 사건에서 다시 만들 수 있어야 한다** — 원본은 항상 사건이다.
- **삭제 요청이 어려운 이유?**\
  → 붙이기만 하는 저장소는 지울 수 없다는 것이 정체성이라, "이 사람 정보를 지워달라"(개인정보 삭제 요청)에 답이 없다.\
  개인정보를 사건에 직접 안 담고 참조만 담는 설계가 필요한데, 그건 이벤트 소싱을 택하는 순간 같이 오는 숙제다.
- **살아남았던 변종 셋?**\
  → ① Opened 의 상태 초기화 ② 읽은 버전으로 붙이기 ③ 중복 개설 막기.\
  공통점: **셋 다 정상 경로에서는 아무 차이가 없다** — 재개설·동시 쓰기·중복 open 이라는 비정상 경로를 테스트가 만들어야 드러난다.
- **17번과의 대비?**\
  → 이 챕터는 사건을 **전부** 들고 있었다(지우지 않는 것이 가치).\
  17번 타임시리즈는 시간에 따라 쌓이는 값을 **오래된 것부터 줄여가며** 들고 있다(다 들 수 없는 것이 전제).
