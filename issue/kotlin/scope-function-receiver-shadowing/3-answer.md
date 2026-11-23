# issue/kotlin/scope-function-receiver-shadowing — 정답

태그: —

## 정답
<!-- 질문 1:1 대응 -->

1. **`?currentSchema=null` 이 들어간다.**\
   `apply` 블록 안의 `$schema` 는 테스트 클래스의 `schema` 가 아니라 `PoolConfig` 의 `schema` 프로퍼티를 읽는다. 설정하지 않았으니 null 이다.\
   실제 사건에서는 연결 풀 설정 객체의 같은 이름 프로퍼티를 읽어, 실제 DB 를 쓰는 엔진 테스트 23건이 전부 준비 단계에서 실패했다.

2. **지역 선언 → 가장 안쪽의 암묵 수신자 → 바깥 수신자 순으로 찾는다.**\
   `apply { … }` 는 수신자 람다라서 블록 안의 `this` 가 설정 객체다. 이름 `schema` 는 먼저 그 객체의 멤버에서 찾아지고, 찾으면 바깥 클래스까지 가지 않는다.\
   Java 클래스의 `getSchema()`/`setSchema()` 쌍은 Kotlin 에서 합성 프로퍼티 `schema` 로 보인다. 그래서 Java 쪽 설정 객체를 `apply` 로 다룰 때 Java 의 수많은 getter 이름이 모두 범위에 들어온다.
   > **암묵 수신자(implicit receiver)** — `this.` 없이 멤버 이름만 써도 그 멤버를 찾게 해 주는 객체. 클래스 본문의 `this`, 수신자 람다의 `this` 가 겹겹이 쌓인다.
   > **합성 프로퍼티(synthetic property)** — Java 의 get/set 메서드 쌍을 Kotlin 이 프로퍼티 문법으로 보여 주는 것.

3. **두 `schema` 모두 문자열 계열이라 타입 검사가 통과하고, 템플릿은 null 을 글자 "null" 로 바꾼다.**\
   문자열 템플릿은 어떤 값이든 문자열로 바꾸므로 null 이어도 컴파일 오류가 없다. 이름 가림에 대한 경고도 나오지 않았다.\
   틀린 값은 접속 주소 안에 섞여 들어가 DB 준비 단계에서야 실패로 드러났다 — 원인과 증상이 떨어져 있다.

4. **`this@바깥클래스.schema` 로 한정한다. 같은 종류가 더 없는지는 나머지 `apply` 블록을 확인했다.**\
   고친 줄은 `"?currentSchema=${this@EngineTest.schema}"` 한 줄이다(이 글의 클래스 이름은 일반화했다).\
   테스트 작성 쪽이 같은 파일의 다른 `apply` 블록(요청 객체에 헤더를 더하는 블록 등)을 확인해, 같은 종류의 이름 가림은 다른 곳에 없다고 보고했다. 단언은 바꾸지 않았다.

5. **테스트는 명세에서 출발한 계약이라, 구현하는 쪽이 고치면 계약을 자기 구현에 맞출 수 있기 때문이다.**\
   이 작업은 테스트를 쓰는 쪽과 구현하는 쪽을 나눴고, 구현 쪽은 테스트를 바꾸지 않는다는 규칙이 있었다.\
   준비 코드의 결함은 단언과 무관하지만, 그 경계를 구현 쪽이 판단하지 않게 보고만 했고 테스트 작성 쪽이 한 줄을 고쳤다.

6. **두 방법 모두 이 결함을 만들지 않는다 — 블록 안에 바깥 이름과 겹칠 암묵 수신자가 없기 때문이다(일반론 — 이 사례에서 적용한 것은 한정 `this@` 이다).**\
   `also { it.url = … }` 에서는 설정 객체가 `it` 으로만 보이므로 `schema` 는 바깥 클래스의 것으로 찾아진다.\
   값을 블록 밖에서 `val url = base + "?currentSchema=$schema"` 로 먼저 만들어 넣어도 같다.\
   대신 `apply` 의 장점(설정 항목을 `this.` 없이 나열)은 줄어든다 — 바깥 값을 읽는 줄이 있는 블록에만 쓰는 편이 낫다.

## 문제 구조 (추상화 코드)

### 변형 A — 수신자 람다 안에서 바깥 프로퍼티를 이름만으로 읽는다
① 문제 코드
```kotlin
class EngineTest {
    private val schema = "engine_test"
    private val dataSource = PooledDataSource(PoolConfig().apply {   // PoolConfig: Java 클래스, getSchema()/setSchema()
        url = Database.url + "?currentSchema=$schema"                // → PoolConfig.schema (null) → "currentSchema=null"
        // ...
    })
}
```
② 고친 코드
```kotlin
class EngineTest {
    private val schema = "engine_test"
    private val dataSource = PooledDataSource(PoolConfig().apply {
        url = Database.url + "?currentSchema=${this@EngineTest.schema}"   // 바깥 클래스로 한정
        // ...
    })
}
```
깨진 것: 바깥 클래스의 이름이 블록 안에서도 그대로 보인다고 가정했다 — 수신자가 같은 이름을 가지면 수신자가 이긴다.

## 검증 기록
- 2026-11-23: 사건 기록·수정 커밋 대조·추상화. 증상(엔진 테스트 23건이 준비 단계에서 전부 실패)과 수정(한 줄, 단언 무변경, 같은 종류 없음 확인)은 사건 기록의 값이다. 질문 6 의 `also` · 블록 밖 계산은 이 사례에서 적용하지 않은 일반론이다.
