# issue/distributed/active-instance-from-routing-truth — 정답

태그: `single-source-of-truth`

## 정답
<!-- 질문 1:1 대응 -->

1. **주기 작업은 프록시를 거치지 않기 때문이다.**\
   요청은 프록시가 활성 자리 하나로만 보내므로, 두 인스턴스가 떠 있어도 일하는 쪽은 하나다.\
   주기 작업은 각 인스턴스 안의 타이머가 스스로 돌린다 — 떠 있는 만큼 돈다.\
   그래서 겹치는 동안 같은 알림이 두 번 나가고, 하루 한 번 하는 일은 교체 시각에 걸리면 두 번 한다.\
   반대로 양쪽 모두 "내 일이 아니다"라고 판단하면 아무도 하지 않는다.
   > **활성 자리(active slot)** — 프록시가 지금 요청을 보내는 인스턴스. 교체는 이 자리를 옮기는 일이다.

2. **주기 작업은 꺼지고, 헬스는 정상으로 남는다.**\
   신호를 받은 구 인스턴스는 약속대로 주기 작업을 멈춘다.\
   그런데 배포기가 "프록시가 아직 이 인스턴스로 보낸다"를 보고 정지를 보류하면, 그 인스턴스는 계속 활성 자리다.\
   헬스 응답은 "정리 중이면 살아 있는 것으로 본다"로 짜여 있었으므로 200을 낸다.\
   결과: 감시가 통째로 꺼졌는데 프록시를 거쳐 보는 모든 관측자에게 정상으로 보인다 — 다음 배포 전까지.\
   되돌릴 경로도 없었다(신호를 취소하는 호출이 없었다).

3. **신호는 의도이고, 프록시의 응답은 사실이기 때문이다.**\
   "신호를 받았다"는 배포기가 그렇게 **하려 했다**는 뜻이지, 전환이 **유지됐다**는 뜻이 아니다 — 되돌림·정지 보류가 그 사이에 낀다.\
   각 인스턴스가 매 주기 프록시에 물어 "지금 보내는 자리가 나인가"로 판정하면, 전환이 어떻게 끝났든 판정은 실제 라우팅을 따라간다.\
   신호는 **힌트**로 남긴다: 받으면 곧바로 대기로 내려가 겹치는 시간을 줄이고, 다음 주기의 확인이 다시 판정한다.\
   프록시가 여전히 이 인스턴스로 보내면 한 주기 뒤 다시 맡는다 — 2번의 상태가 한 주기 이상 이어지지 않는다.

4. **판정한 적이 있으면 직전 판단 유지, 한 번도 못 했으면 유예 뒤 스스로 맡기.**\
   전환은 프록시를 거쳐야만 일어나므로, 프록시에 닿지 못하는 동안에는 자리가 바뀌지 않았다고 보는 것이 맞다 — 직전 판단 유지.\
   뜬 뒤 한 번도 판정하지 못한 인스턴스는 유지할 판단이 없다. 영원히 대기하면 "아무도 안 함"이 되므로, 유예 시간(이 사례는 2분)이 지나면 활성으로 본다.\
   이는 **두 번 하는 쪽**의 실패를 받아들인 선택이다 — 감시·알림에서는 중복 알림이 누락보다 싸다.\
   돈을 보내는 일처럼 두 번 하면 안 되는 작업이라면 반대로 골라야 하고, 그때는 자원 쪽 검증(fencing)이 필요하다.

5. **이미 알린 복구를 다시 알린다 — 상태는 맡는 순간에 읽어야 한다.**\
   새 인스턴스의 메모리에는 뜰 때의 "장애 중"이 남아 있다.\
   교체 뒤 첫 확인이 성공하면 "장애 → 정상"의 변화로 보고 복구 알림을 낸다. 구 인스턴스가 이미 낸 알림이다.\
   교정: 대기에서 활성으로 바뀌는 그 주기에 메모리 상태를 비우고 저장소에서 다시 읽는다.\
   같은 이유로 "같은 사건은 10분에 한 번만" 같은 중복 억제 창도 메모리가 아니라 기록으로 판정해야 교체를 넘어 이어진다.

6. **같은 알림이 두 번 나간다 — 한쪽이 내려놓고, 다른 쪽은 조금 기다렸다 되살린다.**\
   구 인스턴스의 재시도 대기열과 새 인스턴스가 기록에서 되살린 대기열이 같은 건을 각자 보낸다.\
   교정: 대기로 내려가는 인스턴스는 메모리의 재시도 대상을 내려놓는다(기록에는 미발송으로 남아 있다). 맡는 인스턴스가 기록에서 되살린다.\
   남는 틈: 내려놓는 순간 **이미 보내는 중**이던 한 건. 구 인스턴스가 곧 성공시킬 수 있는데 새 인스턴스가 먼저 되살리면 두 번 나간다.\
   그래서 되살리는 대상을 "기록된 지 한 건의 발송 상한(이 사례 60초)이 지난 것"으로 제한하고, 그보다 새 건은 뒤의 주기로 미룬다.\
   기록을 읽지 못한 주기에는 되살리기를 끝났다고 치지 않는다 — 다음 주기에 다시 읽는다.

7. **배포기는 "떴는가"를 보고, 감시자는 "하고 있는가"를 봐야 하기 때문이다.**\
   배포기는 전환 **전에** 새 인스턴스의 헬스를 확인한다. 그때 새 인스턴스는 당연히 대기다 — 200이 아니면 영원히 전환하지 못한다.\
   반면 프록시를 거쳐 보이는 인스턴스가 계속 대기라면, 활성 자리가 일을 하지 않는다는 뜻이다.\
   그래서 응답은 200으로 두되 본문에 역할(`standby`)을 적고, 밖의 감시자는 그 값이 연속으로 보이면 실패로 센다.\
   전환 직후 한 주기쯤은 대기가 보일 수 있으므로 감시자의 연속 실패 기준이 그보다 길어야 한다.

## 문제 구조 (추상화 코드)

### 변형 A — 소유권을 신호로 정함
① 문제 코드
```kotlin
class PeriodicJob {
    @Volatile var draining = false              // 배포기가 POST /drain 으로 켠다. 끄는 경로 없음

    fun tick() {
        if (draining) return                    // 신호를 받았으면 하지 않는다
        checkAndNotify()
    }
}
fun health() = if (job.draining || job.ranRecently()) ok() else unavailable()   // 정리 중 = 정상
```
② 고친 코드
```kotlin
class Ownership(private val mySlot: String, private val proxy: () -> String?) {
    @Volatile var active = false
    private var determined = false

    fun refresh(): Boolean {
        val serving = proxy()                    // 프록시 응답 헤더: 지금 보내는 자리. 불통이면 null
        if (serving != null) { determined = true; active = serving == mySlot }
        else if (!determined && uptime() >= GRACE) active = true    // 알리는 쪽으로 실패
        return active                            // 불통 + 판정 이력 있음 = 직전 판단 유지
    }
    fun standDown() { active = false }           // 신호는 힌트 — 다음 refresh 가 뒤집을 수 있다
}

fun tick() {
    if (!slot.refresh()) return
    checkAndNotify()
}
fun health() = when {
    !slot.active -> ok(status = "standby")       // 프로세스는 정상, 역할은 부재
    job.ranRecently() -> ok(status = "ok")
    else -> unavailable(status = "stalled")
}
```
깨진 것: 의도(신호)를 사실(라우팅)로 취급해, 전환이 유지되지 않은 경우에 주기 작업이 꺼진 채 정상으로 보였다.

### 변형 B — 이어받을 상태를 뜰 때 읽음
① 문제 코드
```kotlin
class PeriodicJob(store: Store) {
    private val states = store.loadDownStates().toMutableMap()   // 뜰 때 한 번
    fun tick() { /* states 로 변화 판정 → 알림 */ }
}
```
② 고친 코드
```kotlin
fun tick() {
    if (!slot.refresh()) { holding = false; return }
    if (!holding) {                               // 대기 → 활성으로 바뀐 주기
        states.clear()
        states.putAll(store.loadDownStates())     // 지금의 사실을 읽는다
        holding = true
    }
    // ...
}
// 중복 억제도 기록으로: 메모리에 없으면 store.sentSince(key, now - window) 를 본다
```
깨진 것: 새 인스턴스가 낡은 "장애 중"을 들고 있다가, 앞 인스턴스가 이미 알린 복구를 다시 알렸다.

### 변형 C — 보내지 못한 일의 소유권이 둘로 갈림
① 문제 코드
```kotlin
// 구 인스턴스: 대기로 내려간 뒤에도 메모리의 재시도 대기열을 계속 보낸다
// 새 인스턴스: 맡을 때 기록의 미발송 건을 전부 되살린다        → 같은 건을 둘이 보낸다
```
② 고친 코드
```kotlin
fun tick() {
    if (!slot.refresh()) {
        if (holding) sender.abandonPending()      // 기록에는 미발송으로 남는다
        holding = false; return
    }
    if (!holding) { tookOverAt = now(); restoreDone = false; holding = true /* ... */ }
    if (!restoreDone) {
        val rows = store.undelivered() ?: return@tick   // 못 읽으면 끝났다고 치지 않는다
        rows.filter { it.at <= tookOverAt && it.at <= now() - SETTLE }   // 앞 인스턴스가 보내는 중일 수 있는 건은 미룬다
            .forEach { sender.restore(it) }
        if (now() - SETTLE >= tookOverAt) restoreDone = true
    }
    // ...
}
```
깨진 것: 메모리의 대기열과 기록에서 되살린 대기열이 같은 일을 각자 가졌다.

## 검증 기록
- 2026-11-21: 사건 기록·리뷰 기록·수정 전후 코드 대조·추상화(Claude 초안). 실측(같은 기록): 두 인스턴스가 겹친 12초 동안 중복 알림 0건, 전환 뒤 한 주기 안에 이어받음(장애 1건 승계·재알림 없음), 활성 인스턴스에 신호만 간 경우 다음 주기에 다시 맡음. 변형 C의 고친 코드는 단위 테스트로만 확인했다.
