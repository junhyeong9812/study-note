# cs/issue/kotlin/spring/serialization-contract-leak — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-23) — 이슈 README·코드 기준. 복습 전 읽지 말 것.

태그: `contract-drift`

## 정답

<!-- 질문 1:1 대응 -->

1. **JSON 필드명이 코드의 프로퍼티명(관례)을 그대로 따라간다.** 리플렉션 직렬화기는 객체를 열어 프로퍼티 이름을 읽고 그걸 JSON 키로 쓴다 — 지시가 없으면 코틀린의 `itemType`(camelCase)가 그대로 `"itemType"`가 된다. 편한 이유는 매핑을 한 줄도 안 짜도 되기 때문이고, 누출인 이유는 **외부에 나갈 이름을 "정하지 않음"이 아니라 "코드 내부 관례에 묶음"으로 결정**해 버리기 때문이다. 기본값은 중립이 아니다.
   > **직렬화(serialization)** — 메모리의 객체를 전송·저장 가능한 형식(JSON 등)으로 바꾸는 것. 리플렉션 기반이면 필드명을 코드에서 자동으로 읽는다.

2. 두 경로는 **필드명을 누가 정하느냐**가 다르다. 손수 조립한 `mapOf("item_type" to meta.itemType)`는 개발자가 JSON 키를 문자열로 직접 쓰므로 키가 코드 프로퍼티명과 **독립**이다 — `meta.itemType`를 리팩토링해도 `"item_type"` 문자열은 그대로다. 반면 data class를 통째로 Jackson에 넘긴 트리 경로는 키를 **직렬화기가 프로퍼티명에서 유도**하므로 코드 관례(camelCase)에 종속된다. 그래서 같은 snake_case 규약을 쓰는 서비스에서 자동 경로 하나만 계약을 깼다.

3. **누출 추상화**는 "세부를 감춰 준다"고 약속한 추상이 실제로는 그 세부를 밖으로 새게 하는 것이다. "객체 ↔ JSON" 추상의 약속은 "직렬화 방식은 신경 끄라"인데, 리플렉션 기본값은 **내부 이름 관례라는 세부를 계약으로 노출**해 약속을 깬다. ORM 엔티티를 API로 직반환하면 테이블 구조·컬럼명·연관관계 로딩이 응답으로 새고, DB 컬럼명을 그대로 노출하면 스키마 변경이 API 변경이 된다 — 셋 다 **"내부 표현과 외부 계약을 분리하지 않아 내부 변경이 외부를 깨는"** 동일 원리다.
   > **누출 추상화(leaky abstraction)** — 하위 세부를 감추기로 한 추상이 그 세부를 완전히 감추지 못하고 밖으로 드러내는 현상(Joel Spolsky). 자동 매핑·자동 직렬화가 대표적.

4. `itemType → kind`로 바꾸면 JSON 키가 조용히 `"itemType" → "kind"`로 바뀐다. **컴파일러는 못 잡는다** — 코드 안에서는 타입이 일관되니까. 기존 단위 테스트도 대개 못 잡는다 — 객체 필드를 검사할 뿐 "직렬화된 JSON 키 문자열"을 계약으로 고정해 검증하지 않으니까. 결과는 front가 의존하던 필드가 사라지는 **런타임 계약 파손**인데, 신호가 없어 배포 후 클라이언트가 깨져서야 발견된다. "조용히"의 정체는 **계약을 지키는 주체가 코드 어디에도 없어서**다.

5. "200만 보는" 스모크였다면 이 사건은 **통과했을 것**이다 — 서버는 정상 200을 주고 몸통만 필드명이 틀렸으니까. 실제로는 스크립트가 `doc["item_type"]`를 파싱하다 `KeyError`로 터져 즉시 드러났다. 계약 검증의 최소 단위가 상태코드가 아니라 **필드명·모양**인 이유가 이것이다 — 상태코드는 "요청이 처리됐다"만 말하고, 클라이언트가 실제로 의존하는 것은 응답의 **구조**다. 스모크는 몸통을 파싱해 기대 필드를 되물어야 한다.
   > **계약(contract)** — API의 요청·응답이 지켜야 하는 약속(필드명·타입·모양). 상태코드는 계약의 일부일 뿐, 몸통 구조가 본체다.

6. 경계는 **"이 필드를 외부가 이름으로 의존하는가"** 다. 클라이언트가 파싱해 쓰는 응답 필드는 계약이니 이름을 명시한다. 내부 로그·디버그 전용 구조, 이름이 안 중요한 값은 자동이어도 된다. "모든 필드에 `@JsonProperty`"와의 차이는 **의도의 표시**다 — 전역 네이밍 전략(`PropertyNamingStrategies.SNAKE_CASE` — Jackson 2.12+, 이전엔 `PropertyNamingStrategy.SNAKE_CASE`)으로 일괄 변환할 수도 있지만(단 숫자가 낀 이름은 기대와 다르게 변환될 수 있다 — 변형 D), 계약 필드에 개별 `@JsonProperty`를 붙이는 것은 "이 이름은 바뀌면 안 되는 계약"이라는 신호를 코드에 남긴다. 핵심은 **"외부 이름을 코드 프로퍼티명이 우연히 결정하게 두지 않는다"** 이지, 데코레이터를 도배하는 것이 아니다.

## 발생한 문제 / 해결 (추상 원리)

**문제:** 내부 표현(코드 프로퍼티명)을 외부 계약(JSON 필드명)으로 새게 하는 자동 직렬화. 편의를 위해 기본값에 맡긴 순간, 계약이 코드 리팩토링에 종속되고 아무도 그 계약을 검증하지 않는다.

**해결:** ① 계약이 되는 필드는 경계에서 이름을 **명시적으로 고정**(`@get:JsonProperty("item_type")`)해 내부 표현과 외부 계약을 분리한다. ② 스모크는 상태코드가 아니라 **응답 몸통을 파싱**해 계약 불일치를 즉시 드러낸다. ③ 규약(snake_case 등)은 한 곳에서 일관되게 — 손수 조립이든 명시 애노테이션이든, "우연히 정해지는 이름"을 없앤다.

## 문제 구조 (추상화 코드)

### 변형 A — 자동 직렬화가 코드 프로퍼티명을 외부 계약으로 만든다
① 문제 코드
```kotlin
data class ItemRef(val path: String, val itemType: String)          // 자동 직렬화 → "itemType"
data class Node(val name: String, val docs: List<ItemRef>, val children: List<Node>) {
    val isLeaf: Boolean get() = docs.isNotEmpty() && children.isEmpty()   // → "isLeaf" (게터도 직렬화됨)
    // (jackson-module-kotlin 기준 — Kotlin 모듈 없이 순수 빈 규칙이면 is 접두사가 빠져 "leaf"가 된다: 이름이 모듈 유무에도 좌우)
}
// 다른 API는 손수 조립: mapOf("item_type" to meta.itemType, ...)  → snake_case
// 이 API만 camelCase — 스모크가 몸통을 파싱하다 KeyError: 'item_type'
```
② 고친 코드
```kotlin
data class ItemRef(val path: String, @get:JsonProperty("item_type") val itemType: String)   // 와이어 이름을 코드에 고정
data class Node(/* ... */) {
    @get:JsonProperty("is_leaf")
    val isLeaf: Boolean get() = docs.isNotEmpty() && children.isEmpty()
}
```
무엇이 깨졌나: 경로마다 이름이 "우연히" 정해졌고(손수 조립 vs 자동), 코드 리팩토링이 계약 변경이 됐다.\
같은 구조: 필드명 기반 암묵 매핑으로 직렬화 키 21건이 기대와 달라 역직렬화 19건이 이미 조용히 깨져 있었음 → 명시 이름 + 계약 테스트.\
같은 구조: 서비스 간 DTO에서 네이밍 전략 누락 필드·타입 불일치가 단위 테스트가 아니라 실구동·컨테이너 e2e에서만 드러남(양쪽이 독립 정의).\
같은 구조: 프론트 경로 값과 백엔드 enum 값이 서로 다른 코드(한쪽만 변경) → 검증 오류(422), 매핑에 없는 필드명으로 읽어 항상 None(해결은 미기록).

### 변형 B — 디버그 표현을 와이어 포맷으로 사용
① 문제 코드
```rust
let name = format!("{:?}", sig);             // 라이브러리의 이름 메서드가 비공개라 Debug 사용 → "Custom(\"FOO\")" 같은 내부 표현 누출
send(Event::Signal { name });
```
② 고친 코드
```rust
fn sig_name(sig: &Sig) -> String {            // 시그널 → 안정 이름 직접 매핑
    match sig { Sig::TERM => "TERM".into(), Sig::INT => "INT".into(), /* ... 시그널마다 표준 이름 */ }
}
```
무엇이 깨졌나: 디버그용 표현(안정성 약속 없음)이 소비자 계약이 됐다.

### 변형 C — 프레임워크 내부 구현 클래스를 그대로 직렬화
① 문제 코드
```java
@GetMapping("/subscribers")
Page<SubscriberDto> list(Pageable p) { return service.find(p); }   // 페이지 구현체 그대로 → number/size/totalElements/...
// 프레임워크가 "구조 안정성 비보장" 경고, BFF는 number→page 등 이 키에 결합
```
② 고친 코드
```ts
// BFF 쪽 adapter로 필요한 필드만 투영 → 영향면 격리
function toPage(raw: any) {
  return { items: raw.content, page: raw.number, size: raw.size, total: raw.totalElements, totalPages: raw.totalPages };
}
expect(toPage(sample)).not.toHaveProperty("createdDate");   // 투영 밖 필드가 새지 않음을 단언
// 후속: 서버 쪽 DTO 직렬화 모드로 전환 시 BFF adapter 동시 수정 필요를 기록
```
무엇이 깨졌나: 프레임워크 설정 변경이 곧 공개 API 변경이 되는 구조였다(사고 전 관찰).

### 변형 D — 쓰기 경로와 읽기 경로가 서로 다른 매핑 메타데이터를 씀
① 문제 코드
```java
@Document class Doc {
    @Field(name = "item_1_code") String item1Code;   // 색인(쓰기) 라이브러리만 읽는 애노테이션
}
// 읽기 경로는 다른 클라이언트 + 범용 JSON 매퍼(기본 camelCase) → 모든 필드 null → 필수 필드 NPE
```
② 고친 코드
```java
@Bean JsonpMapper jsonpMapper() {
    ObjectMapper om = new ObjectMapper().setPropertyNamingStrategy(PropertyNamingStrategies.SNAKE_CASE);
    return new JacksonJsonpMapper(om);
}
@JsonIgnoreProperties(ignoreUnknown = true)                   // 쓰기 라이브러리가 넣는 메타 필드(_class) 흡수
class Doc {
    @JsonAlias("item_1_code") String item1Code;       // SNAKE_CASE는 숫자 앞에 '_'를 안 넣음 → item1_code ≠ item_1_code
}                                                             // @JsonProperty는 직렬화명까지 바꿔 쓰기 경로에 영향 → 읽기 전용 별칭 선택
```
무엇이 깨졌나: 같은 문서를 두 라이브러리가 서로 다른 이름 규칙으로 읽고 써, 모르는 키가 오류 없이 null이 됐다.

## 검증 기록
- 2026-09-24: 사건 기록 대조·추상화(Claude 초안)

## 방안 비교

기본 방안(위 변형 A~D)은 "와이어 이름을 경계에서 명시 매핑하고, 실제 응답 몸통으로 확인한다"이다. 같은 원리(내부 이름·기본 전략이 외부 계약이 된다)에 다른 방안이 쓰인 사례:

### 방안 1 — 영속 식별자는 데이터 스키마: 개명 금지 + 부분 오류 격리
```ts
// 문제(조사로 발견, 사고는 설계에서 회피): 저장된 레이아웃의 패널 종류 문자열을 개명하면
try { api.fromJSON(savedLayout); } catch { /* 레이아웃 전체 폐기 */ }   // 미지 종류 하나 → 전 사용자 워크스페이스 통째 소실
// 같은 구조: OS 키링 서비스명 개명 → 저장된 자격증명 전부 고아 / 스냅샷 디렉터리 세그먼트 개명 → 전 스냅샷 고아
// 같은 구조: 모델명 문자열 부분 일치로 기능 분기 → 다른 모델에서 게이지 항상 0 (별도 필드 경로로 해결)
// 고친
const PANEL_KIND = "legacyterm";            // 내부 식별자 불변 — UI 문자열만 바꾼다
const NEW_KIND = "otherterm";               // 새 종류는 별도 식별자로 추가
// 개명이 불가피하면 fromJSON 앞단에서 구 식별자 → 신 식별자 치환 shim (권고)
```

### 방안 2 — 입력 바인딩 쪽의 명명 불일치 (잠재 — 미실측)
```text
클라이언트:  { "limit_n": 3 }            // 이전 구현(snake) 시절 필드명
서버 DTO:    data class Req(val limitN: Int = 6)   // 기본 camelCase 바인딩 → limit_n 무시 → 항상 기본값 6
             (Spring Boot 기본 ObjectMapper는 모르는 키를 무시(FAIL_ON_UNKNOWN_PROPERTIES=false) — 순수 Jackson 기본값이면 예외로 드러났을 것)
교정 후보:   서버 쪽 명시 이름(@JsonProperty("limit_n")) 또는 클라이언트 필드명 정합 — 미해결 TODO로 등재
```
출력 누출과 방향만 반대다 — 모르는 키가 오류 없이 버려져 **기본값으로 조용히 동작**한다.

### 방안 3 — ORM 매퍼의 명명 변환 기본값
```xml
<!-- 문제: 언더스코어→카멜 자동 변환 설정이 기본 false → ITEM_NO 가 itemNo 에 매핑되지 않고 조용히 null -->
<select id="find" resultType="Item">SELECT ITEM_NO, BODY FROM item WHERE ...</select>
<!-- 고친: 신규 쿼리는 AS 별칭으로 이름을 명시 (이식한 쿼리는 resultMap 병존) -->
<select id="find" resultType="Item">SELECT ITEM_NO AS itemNo, BODY AS body FROM item WHERE ...</select>
```

### 방안 4 — 불변식은 객체가 아니라 실제 직렬화 경계를 통과한 payload로 판정
```java
// 문제: 같은 객체가 경로마다 다른 JSON — 색인 매퍼(SNAKE_CASE·NON_NULL) vs HTTP 응답(프레임워크 기본 매퍼)
//       null 키 유무·날짜 표현이 달라, 동작 보존 리팩토링(Map → typed)의 "같다" 판정이 흔들림
assertEquals(oldMap, newRecord);                          // 객체 비교 — 직렬화 차이를 못 봄
// 고친
@SpringBootTest class GoldenTest {
    @Autowired JsonpMapper prodMapper;                    // 운영과 같은 매퍼 빈으로 실직렬화
    @Test void same() {
        JsonNode a = tree(prodMapper, legacy), b = tree(prodMapper, typed);
        assertEquals(a, b);                               // 트리 비교
    }
}
// 재현 조건 고정: JVM 타임존(날짜 타입 직렬화가 의존), 테스트 매퍼에 날짜 모듈 등록(운영과 같은 ISO 문자열)
// 상세 응답 어댑터는 null 정책(스칼라 null 유지 / 전부 생략)을 원천별 현행 모양대로 보존
```

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 기본: 경계에서 명시 매핑 + 몸통 확인 | 계약 이름을 코드가 소유한다 | 필드마다 애노테이션·매핑 | 새 필드에서 명시 누락 | API 응답·서비스 간 DTO |
| 1. 영속 식별자 불변 + 치환 shim | 이름이 이미 디스크·키체인에 저장됐다 | 내부 이름과 표시 이름 분리 유지 | 통째 catch가 부분 오류를 전체 손실로 증폭 | 저장된 레이아웃·키·경로 세그먼트 |
| 2. 입력 명명 정합 | 서버가 모르는 키를 무시한다 | 양쪽 조율 | 기본값으로 조용히 동작 | 언어·구현이 바뀐 클라이언트 |
| 3. 쿼리 별칭으로 이름 명시 | 매퍼가 정확히 같은 이름만 매핑 | 쿼리마다 AS | 별칭 누락 컬럼이 조용히 null | SQL 매퍼 기반 영속 계층 |
| 4. 실직렬화 payload 비교 | 매퍼 설정이 경로마다 다르다 | 운영 매퍼로 통합 테스트 | 테스트 매퍼가 운영과 다르면 거짓 green | 동작 보존 리팩토링·골든 테스트 |

**결론**: 이름이 **어디에 저장되어 있느냐**가 방안을 고른다.\
와이어 위에서만 사는 이름이면 경계에서 명시 매핑하고(기본·2·3), 이미 디스크에 저장된 이름이면 바꾸지 않는 게 원칙이다(1).\
어느 쪽이든 "같다"의 판정은 객체가 아니라 **실제 직렬화 결과**로 한다(4) — 모르는 키를 조용히 버리도록 설정된 매퍼가 흔해(예: Spring Boot 기본 ObjectMapper·Gson — 순수 Jackson·kotlinx.serialization은 기본이 오류) 오류가 나지 않는 경우가 많기 때문이다.
