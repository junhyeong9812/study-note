# ops-patterns/12-leader-election — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 작성 방식: **2-summary를 닫고 기억만으로** 쓴다 → 실제 코드/원전으로 검증 → 틀린 부분만 수정.
> 기준 소스는 문서가 아니라 코드다 (`/home/jun/project/myway/ops-patterns/12-leader-election/impl/`).

⚠️ 정답은 Claude 초안(2026-09-14) — 원본 impl 코드·README 기준. 본인 검토 후 이 줄 삭제

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. -->

### A. 문제 (NaiveElection · LeaseElection 의 TODO)

#### 1. TODO 1 — NaiveElection.campaign

정답 코드 (impl/NaiveElection.java):

```java
if (leader != null && !leader.equals(node)) {
    return Optional.empty();
}
leader = node;
history.add("0 " + node + " 선출됨");
// 임기 번호가 없다. 늘 1 을 준다. 그래서 구별할 근거가 없다.
return Optional.of(1L);
```

- 존재 이유: **"번호가 없으면 옛 리더와 새 리더를 구별할 수 없다"** 를 보여주는 기준선.\
  심장 박동 개념도 없다(리더면 늘 참).
- 24시간 뒤: **리더는 여전히 A**(죽은 놈).\
  만료가 없어 아무도 못 가져간다 — 정산도 배치도 안 도는데 **서비스가 조용히 멈춘다.**
- 알림이 안 가는 이유: **"리더가 죽었다"는 이벤트 자체가 없다** — 죽음을 감지하는 장치(심장 박동·만료)가 없으니 상태 변화가 일어나지 않고, 일어나지 않은 일에는 알림도 없다.

#### 2. TODO 2 — LeaseElection.campaign

정답 코드 (impl/LeaseElection.java):

```java
long now = ticker.nowMillis();

if (leader != null && !isStale(now)) {
    // 살아 있는 리더가 있다. 자기 자신이면 그대로 인정한다.
    if (leader.equals(node)) {
        return Optional.of(term);       // 1. 같은 임기를 그대로 준다
    }
    return Optional.empty();
}

if (leader != null && !leader.equals(node)) {
    // 옛 리더가 아직 자기가 리더인 줄 안다. 물러날 목록에 넣는다.
    steppingDown.add(leader);           // 3. 물러나는 중 목록
    record(now, leader, "임기 잃음(임기 " + term + ")");
}

boolean changed = leader != null && !leader.equals(node);
leader = node;
term++;                                 // 2. 선출될 때마다 커진다. 이것이 계약이다
lastHeartbeatAt = now;
if (changed) {
    leaderChanges++;                    // 4. 실제로 바뀐 횟수
}
record(now, node, "선출됨(임기 " + term + ")");
return Optional.of(term);
```

- 현직이 다시 부를 때 임기를 올리면: 자기가 들고 있는 임기 번호(옛 값)로 보내는 **자기 심장 박동이 자기 임기를 무효로 만든다** — heartbeat 의 `heartbeatTerm != term` 검사에 자기가 걸린다.
- "유일한 근거": 옛 리더가 깨어나 "나 리더야"라고 할 때 **누가 더 최근인지 가릴 방법이 번호 비교뿐**이라는 뜻이다.\
  이름도 시각도 믿을 수 없다(둘 다 겹치거나 어긋날 수 있다).
- 목록에 안 넣으면: 옛 리더가 **자기 상태를 확인할 방법이 없고**(roleOf 가 FOLLOWER 라고만 답한다), **하던 일을 정리할 자리(STEPPING_DOWN)도 없다.**
- 안 세면: 사고가 **"가끔 배치가 두 번 돈다"로만 나타나고 원인을 못 찾는다.**\
  leaderChanges 는 임기 설정이 맞는지 판단하는 자다.
- 11번의 **펜싱 토큰**과 정확히 같은 일 — 커지기만 하는 번호로 낡은 놈을 가려낸다.

#### 3. TODO 3 — LeaseElection.heartbeat

정답 코드:

```java
long now = ticker.nowMillis();

if (!node.equals(leader) || heartbeatTerm != term) {
    // 내 임기가 아니다. 이 순간 이 노드가 자기 상태를 처음 안다.
    record(now, node, "심장 박동 거절(내 임기 " + heartbeatTerm + ", 현재 " + term + ")");
    return false;
}
if (isStale(now)) {
    // 내 임기인데 이미 끊긴 지 오래다. 아무도 안 가져갔을 뿐이다.
    record(now, node, "심장 박동이 늦었다");
    return false;
}
lastHeartbeatAt = now;
return true;
```

- 이름만 보면 뚫리는 시나리오: **같은 노드가 재기동해서 다시 뽑혔을 때, 재기동 전에 보낸 심장 박동이 뒤늦게 도착**한다 — 이름은 같으니 통과해버린다.\
  임기까지 봐야(옛 박동의 임기 ≠ 현재 임기) 걸린다.
- 옛 리더가 처음 아는 시점: **다음에 심장 박동을 보낼 때** — 거절(false)을 받는 그 순간이다.\
  그 사이에 하던 일이 있고, 그래서 정리할 자리가 필요하다.
- 살려주면 깨지는 약속: **"끊기면 잃는다."**\
  내 임기여도 끊긴 지 오래면 임기는 이미 끝난 것이다(아무도 안 가져갔을 뿐).
- "남들이 믿는다": 다른 노드들은 "임기만큼 박동이 없으면 리더 자리가 비었다"고 믿고 **새 리더를 뽑는다** — 죽은 줄 알았던 옛 임기를 살려주면 새 리더와 둘이 된다.

#### 4. TODO 4·5·6 — resign / currentLeader / roleOf

정답 코드:

```java
// resign
if (!node.equals(leader) || resignTerm != term) return false;
record(ticker.nowMillis(), node, "스스로 물러남(임기 " + term + ")");
leader = null;
// 임기 번호는 안 되돌린다. 되돌리면 옛 리더의 번호와 겹친다.
lastHeartbeatAt = 0;
return true;

// currentLeader
if (leader == null || isStale(ticker.nowMillis())) return Optional.empty();
return Optional.of(leader);

// roleOf
if (node.equals(leader) && !isStale(ticker.nowMillis())) return Role.LEADER;
if (steppingDown.contains(node)) return Role.STEPPING_DOWN;
return Role.FOLLOWER;
```

- 번호를 되돌리면: **옛 리더의 번호와 새 리더의 번호가 겹쳐** 둘을 구별할 수 없다 — "번호가 커지기만 한다"는 유일한 근거가 무너진다.
- currentLeader 의 거짓말: 만료를 안 보면 **대시보드가 죽은 리더를 살아 있다고 보여준다** — 사람이 그걸 믿고 판단한다.
- 셋이어야 하는 이유: "리더냐 아니냐" 둘로 나누면 임기를 잃은 옛 리더가 **하던 일을 그냥 계속한다**(자기가 아니라는 신호를 받을 자리가 없다).\
  그리고 그것이 조용하다.
- 뭉뚱그리면: FOLLOWER = "리더가 아니니 아무것도 안 한다"인데, 옛 리더는 **이미 뭔가를 하는 중이었다** — 정리(그리고 정리 완료 신고 `steppedDown`)를 할 자리가 사라진다.

#### 5. TODO 7 — isStale

정답 코드:

```java
private boolean isStale(long now) {
    return now - lastHeartbeatAt >= leaseMillis;
}
```

- 이 구현의 선택: `>=` — **정확히 임기만큼 지난 순간은 "끊긴" 것**이다.
- 한 칸(`>`) 틀리면: 평소에는 똑같고 **경계(정확히 leaseMillis 지난 순간)에서만** 어긋난다 — 그 순간 옛 리더의 박동이 한 번 더 살아남거나, 새 선출이 한 틱 늦는다.\
  경계에서만 어긋나는 결함은 일반 테스트로는 안 잡혀서, 그 경계를 실제로 밟는 테스트가 여덟 개다.

### B. 개념

#### 6. 락과 선출의 차이

- 락 = **한 번의 작업**을 한 놈만: 잡고, 하고, 놓는다.\
  선출 = **계속 그 역할**: 뽑히고, 유지하고, 잃는다.
- 세 가지가 필요한 이유: 역할이 계속되므로 ① 옛 리더와 새 리더가 시간축에서 겹칠 수 있다 → **임기 번호**로 최근을 가린다 ② "아직 그 역할인가"를 계속 알려야 한다 → **심장 박동** ③ 역할을 잃는 순간 하던 일이 있다 → **물러나기(STEPPING_DOWN)**.
- 심장 박동은 락의 **갱신(renew)** 에 대응한다 — 점유를 연장하는 주기적 신호다.

#### 7. 옛 리더 문제

- 위험한 이유: A는 **자기가 멈췄다는 것을 모른다** — 깨어나서도 자기가 리더인 줄 알고 하던 일(쓰기·배치)을 계속한다.\
  그 사이 B가 이미 리더다.
- 조용한 이유: 예외도 로그도 없다 — 둘 다 "정상 동작 중"이라고 생각한다.\
  결과만 어긋난다(배치 두 번).
- steppedDown(): **옛 리더 자신이, 하던 일을 정리한 뒤에** 부른다 — "물러나기를 끝냈다"는 신고이고, 그제서야 목록에서 빠져 FOLLOWER 가 된다.

#### 8. 고칠 수 없는 것

- 버그가 아닌 이유: 비동기 네트워크에서는 **원리적으로** 응답 없음이 "죽음"인지 "느림"인지 구별이 안 된다 — 어떤 구현으로도 못 고친다.
- 생길 수 있는 것: 느린 리더를 죽었다고 치고 새로 뽑으면 **리더가 둘**이 된다.\
  유일한 대책은 둘이 됐을 때 **피해를 줄이는 것** — 그것이 임기 번호다.
- 실험(박동 1000ms 기준): 임기 500ms → 교체 **19회**, 1500ms → 0회, 5000ms → 0회.
- 트레이드오프: 짧으면 **멀쩡한 리더가 자꾸 쫓겨나고** 그때마다 하던 일이 끊긴다.\
  길면 **진짜 죽었을 때 그만큼 오래 멈춰 있다.**\
  고를 수밖에 없다 — 정답이 없고 선택만 있다.

#### 9. 조용한 결함들

- 살아남은 둘: **"심장 박동이 임기를 안 본다"** 와 **"물러날 때 번호를 되돌린다"** — 둘 다 **같은 노드가 재기동해서 다시 뽑히는** 경우를 만들어야 드러났다(이름이 같아서 이름 검사로는 안 걸리는 경우).
- history 가 없으면: **사고 조사에서 아무것도 못 한다** — 리더가 언제 왜 바뀌었는지 재구성할 수 없다.
- "배치가 두 번 돈다"의 원인: **leaderChanges(교체 횟수)와 history(교체 기록)** 가 있어야 "그 시각에 리더가 바뀌었고 옛 리더가 물러나는 중이었다"로 짚을 수 있다.

#### 10. 연결

- 임기 번호 vs 펜싱 토큰: 공통점 — **커지기만 하는 번호로 낡은 놈의 행동을 가려낸다.**\
  차이 — 펜싱 토큰은 점유(락)마다, 임기 번호는 선출마다 커지고, 검사하는 쪽이 각각 저장소/선출 장치다.\
  (차이 서술은 내 정리 — 원본은 "정확히 같은 일을 한다"까지)
- 13번과의 차이: 여기서 임기 번호는 **한 곳(선출 장치)에서** 나왔다.\
  13-snowflake 는 여러 대가 겹치지 않는 번호를 **조율 없이** 만들어야 한다.
- 실무 대응: Raft 의 **term** = 임기 번호, Kubernetes leader election 의 lease = 이 구현의 임대(lease) 구조 그대로다.

## 근거

- 기준 소스: `/home/jun/project/myway/ops-patterns/12-leader-election/impl/NaiveElection.java`, `impl/LeaseElection.java`
- 계약: `src/main/java/com/ops/leader/Election.java`, `Role.java`
- 문제 원문: `src/main/java/com/ops/leader/` 의 TODO 1~7, `README.md` "특히 생각해볼 것" 1~8
