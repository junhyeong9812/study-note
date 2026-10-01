# database/31-cache-key-versioning-and-serialization — 정답

## 정답

### 1. 키 규칙

- **값을 계산할 때 쓴 입력은 전부 키에 있어야 한다.**
- Spring 기본 `SimpleKeyGenerator`는 메서드 인자만 본다. 인자가 하나이고 null·배열이 아니면 그 값 자체가 키다(그 밖에는 `SimpleKey`). Spring Data Redis는 앞에 `products::`를 붙인다.
- 그래서 키는 `products::1001` 하나뿐이다. 먼저 조회한 테넌트·로캘의 값이 저장되고, 다른 테넌트·로캘 사용자도 그 값을 받는다. 에러는 없다.
- `key = "…"` SpEL이나 커스텀 `KeyGenerator`로 테넌트·로캘을 명시적으로 넣는다.

### 2. 긴 키

- Redis 문서: 1024바이트 같은 아주 긴 키는 메모리와 키 비교 비용 때문에 나쁘다. 큰 값을 키로 써야 하면 SHA1 같은 해시가 낫다. `"object-type:id"` 같은 스키마를 지키라고 권한다.
- 해시 전에 할 일은 **정규화**다. 필드 순서를 정렬하고, 기본값을 채우고, 대소문자를 통일한다. 같은 뜻의 조건이 같은 해시가 되게 한다.
- 앞부분은 읽을 수 있게 둔다. 예: `app:search:v2:t42:<sha256>`.

### 3. 필드 추가 + JDK 직렬화

- `serialVersionUID`를 선언하지 않았다면 클래스 변경으로 계산값이 달라질 수 있다.
- 그러면 `InvalidClassException: … local class incompatible: stream classdesc serialVersionUID = …, local class serialVersionUID = …`가 난다. 로컬 재현에서 같은 형태의 메시지를 확인했다.
- Spring Data Redis는 이것을 `SerializationException("Cannot deserialize")`로 감싼다.
- Spring 기본 `SimpleCacheErrorHandler`는 get 오류를 **다시 던진다.** 미스가 아니라 **요청 실패**다. 읽을 때마다 죽는 poison pill이 된다.

### 4. 버전 혼재의 조건

- 신버전은 구버전이 쓴 형식을 읽을 수 있어야 한다.
- 구버전은 신버전이 쓴 새 형식·필드를 우아하게 다뤄야 한다. 롤백도 같은 상황이다(AWS: 캐시 데이터를 영속 저장소처럼 다룬다).
- Jackson `FAIL_ON_UNKNOWN_PROPERTIES`의 기본값은 `true`다. 구버전이 신버전 값의 새 필드를 만나면 실패한다.
  - `GenericJackson2JsonRedisSerializer` 기본 생성자는 자체 `new ObjectMapper()`라 이 기본값을 받는다.
  - `@class` 타입 힌트 때문에 클래스 이름·패키지 변경도 깨진다.

### 5. 키 버전 vs 값 버전

| | 키에 버전 (`product:v3:…`) | 값에 버전 (`{"_v":3,…}`) |
|---|---|---|
| 배포 직후 | 새 키 전부 미스(콜드 스타트) | 같은 키 그대로 적중 |
| 혼재·롤백 | 두 키 공간 공존, 롤백해도 옛 키가 산다(만료 전이면) | 관대한 리더가 두 형식을 다 읽어야 한다 |
| 비용 | 메모리 이중 사용, 옛 키는 TTL을 걸었을 때만 사라짐(기본 영구면 따로 삭제) | 버전별 읽기 코드 유지 |

- 공통 위험: **대량 재적재.** 형식 불일치로 캐시를 버리거나 새 키 공간이 비면 요청이 한꺼번에 하위 서비스·DB로 간다. 스로틀·브라운아웃으로 이어진다(AWS). 천천히 배포하고, 예열하고, DB 앞 동시성을 제한한다.

### 6. null 캐싱

- 캐시하지 않으면: 없는 id를 반복 조회할 때마다 DB로 간다(캐시 관통). 공격에 쓰일 수 있다.
- 캐시하면: 그 id가 새로 생성돼도 TTL 동안 "없음"을 준다.
- Spring Data Redis `defaultCacheConfig()`는 null 캐싱 "예", TTL "영구"다. 둘이 겹치면 "없음"이 만료되지 않는다.
- 대처: null에는 짧은 별도 TTL을 준다(AWS의 negative cache도 다른 TTL). 생성 시 해당 키를 지운다.

### 7. 지터

- 고정 TTL: 1만 개가 모두 60분째에 만료된다.
- ±10% 지터: 54~65분에 걸쳐 분당 약 800개씩 만료된다(로컬 재현 시뮬레이션: 796~871개).
- soft/hard TTL(AWS): soft TTL이 지나면 갱신을 시도한다. 하위 서비스가 응답하지 않으면 hard TTL까지 기존 값을 계속 쓴다. 만료가 곧 장애로 번지는 것을 막는다.

### 8. lease

- **stale set**: 동시 갱신 순서가 뒤바뀌어 옛 값이 캐시에 남는 문제.
  - 미스 때 키에 묶인 64비트 토큰을 준다. set은 토큰과 함께만 받는다.
  - 그 사이 delete가 오면 토큰이 무효화되어 늦은 set이 거부된다.
- **thundering herd**: 자주 쓰이고 자주 무효화되는 키에 미스가 몰리는 문제.
  - 키당 10초에 한 번만 토큰을 준다. 나머지 요청은 잠깐 기다렸다 재시도한다. 보통 그때는 값이 채워져 있다.
- 효과: 한 주 관측에서 DB 최대 질의율이 17K/s에서 1.3K/s로 줄었다(Nishtala 외 2013).

### 9. write-behind 손실

- 의심: **write-behind.** 쓰기를 캐시에 넣고 "성공"을 응답한 뒤, DB 반영을 메모리 큐로 미뤘다. 캐시 노드 재시작·장애 조치로 큐가 사라졌다. 손실은 조용하다.
- 대처
  - 원본 데이터는 DB에 먼저 쓴다(write-through, 또는 cache-aside + 무효화).
  - 비동기가 필요하면 내구성 있는 큐(outbox)를 쓰고, DB 적재 실패·지연에 경보를 둔다.
  - 캐시와 DB를 주기적으로 대조한다.

### 10. 500 → flush → DB 100%

- 1단계(500)
  - 값 형식이 바뀌어 역직렬화가 실패했다(`InvalidClassException`·`UnrecognizedPropertyException` → `SerializationException`).
  - Spring 기본 오류 처리가 이를 요청 실패로 올렸다.
- 2단계(DB 100%)
  - 캐시를 전부 비우자 모든 요청이 미스가 되어 DB로 몰렸다.
  - AWS 글이 경고한 대량 재적재 → 브라운아웃이다.
- 처음부터 했어야 할 것
  - 캐시 전용 DTO + JSON + 관대한 리더(`FAIL_ON_UNKNOWN_PROPERTIES` 끔), `serialVersionUID` 명시.
  - 깨지는 변경은 키 버전을 올리고 천천히 배포·예열한다.
  - 캐시 오류를 미스로 처리할 때는 DB 앞에 동시성 제한을 둔다.
  - 스테이징에서 신·구 버전의 교차 읽기를 시험한다.
