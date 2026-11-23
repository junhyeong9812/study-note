# issue/kotlin/scope-function-receiver-shadowing — 정리 (힌트)

## 전체 흐름

```
class EngineTest {                         ← 바깥 암묵 수신자  this@EngineTest
    private val schema = "engine_test"
    val pool = Pool(PoolConfig().apply {   ← 안쪽 암묵 수신자  this = PoolConfig
        url = base + "?currentSchema=$schema"
    })                                  │
}                                       ▼
                     이름 찾기:  지역 선언 → 안쪽 수신자 → 바깥 수신자
                                       │
                     PoolConfig 에 getSchema()/setSchema() → Kotlin 프로퍼티 schema 로 보인다
                                       │
                                       ▼
                     $schema = PoolConfig.schema = null → "?currentSchema=null"
                                       │
                                       ▼
                     컴파일 OK · 경고 없음 → 준비 단계에서 23건 전부 실패

교정:  "?currentSchema=${this@EngineTest.schema}"
```

## 핵심 문장
- 수신자 람다(`apply`·`with`·`run`) 안에서는 수신자의 멤버가 바깥 클래스의 멤버보다 먼저 잡힌다.
- Java 의 get/set 쌍은 Kotlin 에서 프로퍼티 이름으로 보인다 — 우리가 만든 적 없는 이름이 범위에 들어온다.
- 타입이 맞으면 컴파일러는 침묵하고, 문자열 템플릿은 null 을 "null" 로 찍는다 — 실패는 엉뚱한 곳(접속·준비)에서 난다.
- 바깥 값을 쓰려면 `this@바깥클래스` 로 한정하거나, 값을 블록 밖에서 계산해 넣는다.
