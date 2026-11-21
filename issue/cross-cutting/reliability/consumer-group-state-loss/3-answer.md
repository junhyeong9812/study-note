# issue/reliability/consumer-group-state-loss — 정답

태그: `silent-failure`

## 정답
<!-- 질문 1:1 대응 -->

1. **브로커의 저장소에 있고, 재시작과 길이 상한이 지운다.**\
   그룹·미확인 목록·항목의 내용은 소비자가 명령으로 만들었지만 브로커의 메모리(또는 디스크)에 있다.\
   디스크에 저장하지 않는 브로커는 재시작하면 스트림과 그룹을 함께 잃는다.\
   길이 상한을 둔 스트림은 오래된 항목부터 밀어내는데, 그 항목이 아직 확인되지 않았는지는 따지지 않는다.\
   두 사건 모두 소비자에게 알림이 오지 않는다 — 소비자는 다음 명령의 결과로만 알게 된다.
   > **소비자 그룹(consumer group)** — 한 스트림을 여러 소비자가 나눠 읽게 하고, 항목마다 "누구에게 전달했고 확인(ack)됐는가"를 브로커가 기억하는 구조. Redis Streams·Kafka 등에 있다.
   > **미확인 목록(pending entries list)** — 전달됐지만 아직 확인되지 않은 항목의 ID 목록. 소비자가 죽으면 여기서 다시 받는다.

2. **"그룹 없음" 오류를 받고, 그 오류만 영원히 되풀이한다.**\
   재시작 뒤 스트림은 생산자가 다음 항목을 넣을 때 다시 생기지만, 그룹은 아무도 다시 만들지 않는다.\
   소비자는 `groupReady = true`를 기억하므로 그룹 만들기를 건너뛰고 곧장 그룹 읽기를 한다 — 결과는 "그룹 없음"(Redis 는 `NOGROUP`).\
   재시도 루프는 실패한 **읽기**만 다시 하고, 읽기의 **전제**인 그룹 만들기로 돌아가지 않는다.\
   그래서 바퀴마다 같은 오류가 나며 수집이 멈춘다 — 프로세스를 다시 띄우기 전까지.

3. **원인 분류에 기대지 않고 회복할 수 있고, 대가는 거의 없다.**\
   "그룹 없음"만 골라 내리려면 오류 문구나 코드를 정확히 알아야 하고, 클라이언트 라이브러리가 그 오류를 다른 예외로 감싸면 분류가 빗나간다.\
   어떤 실패든 내리면, 원인이 무엇이든 다음 바퀴는 그룹 만들기부터 한다.\
   그룹이 이미 있으면 만들기는 "이미 있음"(Redis 는 `BUSYGROUP`) 한 번으로 끝나고, 그 오류는 무시하면 된다.\
   실패는 드문 사건이므로 실패할 때마다 왕복 한 번이 더 드는 것은 문제가 되지 않는다.

4. **ID 만 있고 필드가 빈 채로 온다 — 그대로 저장하면 빈 행이 생긴다.**\
   미확인 목록은 항목의 ID 를 기억할 뿐 내용을 따로 보관하지 않는다.\
   내용이 길이 상한에 밀려 지워진 뒤 미확인 목록을 처음부터 다시 읽으면, 브로커는 그 ID 를 내용 없이 돌려준다.\
   평소처럼 "필드를 꺼내 파싱 → 저장"하면 오류 없이 내용이 빈 행이 저장된다.

5. **영원한 미확인이 남는다 — 확인하되 잃은 건수를 남긴다.**\
   저장하지도 확인하지도 않으면 그 ID 는 미확인 목록에 계속 남아, 미확인분을 다시 읽을 때마다 돌아온다.\
   미확인 건수를 보는 감시는 영원히 0 이 아닌 값을 보게 되고, 진짜로 밀린 것과 구별할 수 없다.\
   그래서 내용이 전부 없는 항목은 저장 대상에서 빼고, 확인 목록에는 넣는다.\
   대신 몇 건을 잃었는지 경고로 남긴다 — 확인은 "처리했다"가 아니라 "더는 다시 주지 마라"는 뜻으로 쓴 것이므로, 잃었다는 사실을 다른 곳에 드러내야 한다.

6. **"처음"은 재시작 뒤 들어온 것을 모두 받고, "지금 이후"는 그 사이 것을 놓친다(일반 의미로부터의 추론).**\
   재시작 직후 스트림은 비어 있다가, 소비자가 그룹을 다시 만들기 전에 생산자가 항목 몇 개를 넣을 수 있다.\
   시작 위치를 "처음"(Redis 는 `0`)으로 두면 그 항목들까지 받는다. 처음 뜰 때 이미 쌓여 있던 항목도 같은 이유로 받는다.\
   "지금 이후"(Redis 는 `$`)로 두면 그룹이 생기기 전의 항목은 그룹에 전달되지 않는다.\
   재시작 전에 남아 있던 미수집분은 어느 쪽이든 이미 사라졌다 — 디스크에 저장하지 않는 브로커를 택한 대가로 받아들인 유실이다.

7. **"브로커 불통"으로 보인다 — 그래서 그룹을 먼저 확인한다.**\
   헬스가 미확인 건수를 물으면 그룹이 없는 브로커는 "그룹 없음"으로 답하고, 헬스는 이를 "브로커에 닿지 못함"으로 판정한다.\
   그 사이 실제로 실패하고 있던 것이 저장소의 스키마 만들기였다면, 헬스는 엉뚱한 원인을 보인다.\
   바퀴 안에서 그룹 확인을 가장 먼저 두면, 브로커가 살아 있는 한 그룹은 다시 생기고 헬스의 미확인 건수도 답한다 — 남는 실패가 진짜 원인이다.\
   헬스 판정의 다른 면은 [silent-failure-vs-artifact](../silent-failure-vs-artifact/)의 방안 비교 "헬스가 정상이라 말하는 근거"에 있다.

## 문제 구조 (추상화 코드)

### 변형 A — 원격의 "준비됨"을 한 번 확인하고 기억함
① 문제 코드
```kotlin
class Consumer(private val broker: Broker) {
    private var groupReady = false

    fun runOnce(): Int = try {
        if (!groupReady) { broker.createGroup(STREAM, GROUP, from = "0"); groupReady = true }
        collect()
    } catch (error: Exception) {
        lastFailure = error.javaClass.simpleName      // 다음 바퀴도 그룹 만들기를 건너뛴다
        0
    }
}
```
② 고친 코드
```kotlin
fun runOnce(): Int = try {
    if (!groupReady) { broker.ensureGroup(STREAM, GROUP, from = "0"); groupReady = true }   // "이미 있음"은 무시
    if (!schemaReady) { sink.createSchema(); schemaReady = true }    // 그룹 확인보다 뒤
    collect()
} catch (error: Exception) {
    // 저장 실패든 브로커 불통이든 확인하지 않고 물러나고, 원격 상태에 대한 기억도 버린다
    groupReady = false
    lastFailure = error.javaClass.simpleName
    0
}

fun Broker.ensureGroup(stream: String, group: String, from: String) {
    try { createGroup(stream, group, from, makeStream = true) }     // 스트림이 없으면 함께 만든다
    catch (error: BrokerException) { if (!error.isAlreadyExists()) throw error }
}
```
깨진 것: 브로커가 가진 상태를 소비자가 기억으로 대신했고, 재시도가 그 기억을 다시 확인하지 않아 "그룹 없음"이 영구 정지가 됐다.

### 변형 B — 내용이 밀려난 미확인 항목을 평소처럼 저장함
① 문제 코드
```kotlin
fun storeAndAcknowledge(records: List<Record>) {
    val rows = records.map { parse(it.id, it.fields["level"], it.fields["line"]) }   // 필드가 없으면 빈 행
    sink.insertAll(rows)
    broker.acknowledge(records.map { it.id })
}
```
② 고친 코드
```kotlin
fun storeAndAcknowledge(records: List<Record>) {
    val rows = ArrayList<Row>(records.size)
    var lost = 0
    for (record in records) {
        val id = parseId(record.id) ?: continue                  // 읽을 수 없는 ID 도 아래에서 함께 확인한다
        if (record.fields.isEmpty()) { lost++; continue }        // 미확인인 채로 상한에 밀려났다 — 내용 없음
        rows += parse(id, record.fields["level"], record.fields["line"])
    }
    if (lost > 0) log.warn("{} unacknowledged entries were trimmed before storing — lost", lost)
    sink.insertAll(rows)                                         // 실패하면 예외 → 확인하지 않는다
    broker.acknowledge(records.map { it.id })                    // 영원히 미확인으로 남지 않게
}
```
깨진 것: 미확인 목록이 내용까지 지켜 준다고 가정해, 내용 없는 ID 를 정상 항목으로 저장했다.

확인 범위: 두 변형 모두 가짜 브로커의 단위 테스트(재시작 = 스트림·그룹·미확인 목록을 비움)와 실제 Redis 7.4 에 대고 도는 테스트로 확인했다.\
실제 Redis 테스트에서 재시작은 스트림 삭제로 흉내 냈고(그룹이 함께 사라진다), 밀려남은 길이 0 으로 다듬기로 만들었다.\
브로커 프로세스를 실제로 재시작해 보지는 않았다.

## 검증 기록
- 2026-11-21: 사건 기록·수정 전후 코드 대조·추상화(Claude 초안).
