# database/31-cache-key-versioning-and-serialization — 캐시 키 설계와 값 직렬화 호환: 버전·테넌트·null·핫 키·TTL 지터 — 정리 (힌트)

## 해결하는 문제

DB 앞에 캐시(cache-aside)를 두면 읽기가 빨라진다. 패턴·무효화·3대 사고의 기초는 원고 [systems/server-design/04-caching.md](../../systems/server-design/04-caching.md)에 있다.\
이 노트는 그 캐시에 **무엇을 어떤 이름으로 어떤 모양으로 넣나**를 다룬다. 여기서 틀리면 캐시가 에러 없이 **틀린 데이터**를 주거나, 한꺼번에 비어 **DB를 때린다.**

```text
  캐시 항목 = 키 ────────────────────────────  값 ──────────────────────────────── 수명
             "이 값이 무엇에 대한 답인가"        "어떤 코드 버전이 쓴 어떤 모양인가"     "언제 사라지나"
  틀리면:     다른 사용자·테넌트·언어의 값 반환    배포 직후 역직렬화 실패               같은 순간 대량 만료
```

쉬운 예: 공용 냉장고에 반찬을 넣는다. 통에 이름을 안 쓰면 남의 반찬을 먹는다(키). 새 통으로 바꿨는데 뚜껑이 옛 통에 안 맞으면 못 연다(직렬화). 모두 같은 날 버리기로 하면 그날 장보기가 몰린다(TTL).\
똑같은 구조다. 캐시는 **여러 코드 버전과 여러 사용자가 함께 쓰는 저장소**다.

실무 예:
- 배포 직후 `SerializationException: Cannot deserialize`가 쏟아진다. 캐시를 비우자 모든 요청이 미스로 DB에 몰린다.
- 상품 캐시 키에 로캘이 없어 한국 사용자에게 영어 설명이 나간다. 테넌트가 없으면 다른 회사 데이터가 나간다.
- 새벽 배치가 10만 개 키를 같은 TTL 1시간으로 넣었다. 정확히 1시간 뒤 DB CPU가 치솟는다.
- AWS Builders' Library: 외부 캐시의 데이터는 **영속 저장소처럼** 다룬다. 새 코드는 옛 코드가 쓴 형식을 읽을 수 있어야 하고, 옛 코드는 새 형식·필드를 우아하게 다뤄야 한다(배포 중에는 둘이 섞여 돈다).

## 동작·원리

### 1. 키 = 값이 의존하는 모든 것

```text
  app:product:v3:tenant=42:locale=ko-KR:id=1001
  ─┬─ ───┬─── ┬─ ────┬──── ─────┬──── ───┬───
   │     │    │      │          │        └ 엔티티 식별자
   │     │    │      │          └ 응답을 바꾸는 요청 속성 (언어·통화·권한 범위 …)
   │     │    │      └ 격리 단위
   │     │    └ 값 스키마 버전 (직렬화 모양이 바뀌면 올린다)
   │     └ 엔티티 종류
   └ 네임스페이스 (서비스·환경)
```

- 규칙은 하나다. **값을 계산할 때 쓴 입력이 전부 키에 있어야 한다.** 빠진 입력이 있으면 그 입력만 다른 요청이 같은 키로 남의 값을 받는다.
- Redis 문서: `"object-type:id"`(예 `user:1000`) 같은 스키마를 지키라고 권한다. 1024바이트 같은 아주 긴 키는 메모리·비교 비용 때문에 나쁘다. 큰 값을 키로 써야 하면 SHA1 같은 **해시**가 낫다.
- Spring `@Cacheable`의 기본 키 생성기(`SimpleKeyGenerator`)는 **메서드 인자만** 본다. 인자가 하나이고 null·배열이 아니면 그 값 자체가 키다(그 밖에는 `SimpleKey`로 감싼다). 테넌트·로캘이 인자가 아니라 스레드 로컬·요청 컨텍스트에 있으면 키에 들어가지 않는다.
  - Spring Data Redis 기본 설정은 키 앞에 `캐시이름::`을 붙인다(`CacheKeyPrefix.simple()`).

### 2. 값 = 코드 버전 사이의 계약

```text
  롤링 배포 중 (구버전 v2 인스턴스와 신버전 v3 인스턴스가 같은 캐시를 쓴다)
  시간 →
  v2 인스턴스:  write(product:1001, 모양 A) ──────── read(모양 B?) → 모르는 필드 → 실패?
  v3 인스턴스:        read(모양 A?) → 필드 없음 → 실패?        write(product:1001, 모양 B)
                ↑ 신버전이 옛 모양을 읽어야 하고, 구버전이 새 모양을 견뎌야 한다 (롤백도 같은 상황)
```

- **JDK 직렬화**: 클래스마다 `serialVersionUID`가 있다. 읽는 쪽 클래스의 값과 다르면 `InvalidClassException`이다. 선언하지 않으면 클래스 세부로 계산되므로, 필드 하나만 바꿔도 값이 바뀔 수 있다. Java 문서는 명시 선언을 강하게 권한다(`Serializable` Javadoc).
  - 로컬 재현(예시, Java 1.8.0_504): 직렬화한 `java.util.Date` 스트림의 UID 한 바이트를 바꿔 읽자 `java.io.InvalidClassException: java.util.Date; local class incompatible: stream classdesc serialVersionUID = 7523967970034938904, local class serialVersionUID = 7523967970034938905`.
- **Spring Data Redis 기본값**(`RedisCacheConfiguration.defaultCacheConfig()` 소스 주석)
  - 값 직렬화: `JdkSerializationRedisSerializer`. 실패하면 `SerializationException("Cannot deserialize", …)`.
  - TTL: 영구(eternal). null 값 캐싱: 예.
- **Spring 캐시의 기본 오류 처리**(`SimpleCacheErrorHandler`)는 캐시 get 오류를 **그대로 다시 던진다.** 그래서 역직렬화 실패는 "미스"가 아니라 **요청 실패**다. AWS 글이 말하는 poison pill이다.
  - *poison pill*: 읽기만 하면 처리하는 쪽을 죽이는 데이터 항목.
- **Jackson JSON**: `DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES`의 기본값은 `true`다(jackson-databind 소스).
  - Spring Data Redis의 `GenericJackson2JsonRedisSerializer` 기본 생성자는 자체 `new ObjectMapper()`를 쓴다. 그래서 이 기본값을 그대로 받는다. 구버전이 새 필드를 만나면 실패한다.
  - 값에 `@class` 타입 힌트를 넣으므로, 클래스 이름·패키지를 바꾸면 옛 값을 못 읽는다.
  - Spring의 `Jackson2ObjectMapperBuilder`는 이 기능을 끈다(소스 주석). "어느 ObjectMapper인가"에 따라 동작이 갈린다.
  - Spring Data Redis 4.0부터 Jackson 2 기반 직렬화기(`GenericJackson2JsonRedisSerializer`·`Jackson2JsonRedisSerializer`)는 deprecated다(Jackson 3 기반으로 이동). 이 절은 3.x 기준이다.

### 3. 버전을 어디에 두나

```text
  (a) 키에 버전   product:v3:1001          배포하면 v3 키는 전부 미스 → 콜드 스타트, DB 부하
                                          v2·v3 키가 공존 → 롤백해도 v2 키가 살아 있다. 옛 키는 TTL을 걸었을 때만 사라짐
                                          (Spring Data Redis 기본 TTL은 영구 → 따로 지워야 함. TTL이 짧으면 롤백 때 v2 키가 이미 없을 수도)
  (b) 값에 버전   {"_v":3, …} + 관대한 리더   같은 키. 리더가 모르는 필드는 무시하고, 옛 버전은 변환해 읽는다
                                          롤백·혼재에 강하지만 리더를 버전마다 유지해야 한다
```

- AWS 글: 형식 불일치를 감지해 캐시를 버리면 **대량 재적재**가 일어나 의존 서비스가 스로틀·브라운아웃될 수 있다. (a)도 같은 위험이다. 배포를 천천히 하거나 미리 데워 둔다.
- 호환 규칙(필드 추가만, 삭제·의미 변경은 새 버전)은 API 버저닝과 같은 문제다. [api-design/07-versioning-and-compatibility](../../api-design/07-versioning-and-compatibility/2-summary.md).

### 4. null 캐싱 — "없음"도 답이다

```text
  GET product:9999  → 미스 → DB: 없음
    캐시 안 함:   다음 요청도 DB로 → 없는 키를 반복 조회하면 DB 직격 (캐시 관통)
    null 캐싱:    "없음"을 짧은 TTL로 저장 → DB 보호
                  대신 그 사이 9999가 생성되면 TTL 동안 "없음"을 계속 준다
```

- AWS 글: 하위 서비스 오류는 **다른 TTL**의 negative cache로 저장하고 오류를 클라이언트에 전달하는 방법을 쓴다. 어느 방법이든 오류 때도 캐시에 **무언가가 있어야** 한다. 비어 있으면 같은 자원을 계속 두드려 장애를 키운다.
- Spring Data Redis 기본은 null 캐싱 "예", TTL "영구"다. 둘이 겹치면 "없음"이 영원히 남는다. 생성 시 해당 키를 지우는 무효화나 짧은 null TTL이 필요하다.

### 5. TTL 지터 — 만료 시각을 흩뿌린다

```text
  1만 개 키를 t=0에 TTL 3600초로 적재 (로컬 재현, Node 18 시뮬레이션)
  고정 TTL           60분째에 10,000개 만료        ██████████████████████████████
  TTL × U(0.9, 1.1)  54~65분에 분당 796~871개      ██ ██ ██ ██ ██ ██ ██ ██ ██ ██ ██ ██
```

- *지터(jitter)*: 일부러 더하는 무작위 편차.
- 같은 시각에 같은 TTL로 넣은 키들은 같은 시각에 만료된다. 그 순간 미스가 몰린다(눈사태). 지터는 가장 싼 방어다(원고 04-caching §4).
- AWS 글의 soft TTL / hard TTL: soft TTL이 지나면 갱신을 시도한다. 하위 서비스가 응답하지 않으면 hard TTL까지 기존 값을 계속 쓴다.

### 6. 핫 키 — 키 하나에 몰린다

```text
  인기 키 만료 순간                      lease (Facebook memcache)
  요청 1000개 → 미스 1000개 → DB 1000번    첫 미스에만 lease 토큰 → 그 클라이언트만 DB 조회·set
                                        나머지는 "잠깐 기다려" → 재시도 시 이미 캐시에 있음
```

- Nishtala 외(NSDI 2013): memcached가 키당 **10초에 한 번만** 토큰을 준다. 그 사이의 요청은 잠깐 기다리라는 통지를 받는다. 한 주 관측에서 DB 최대 질의율이 17K/s에서 1.3K/s로 줄었다.
- 같은 lease 토큰은 **stale set**도 막는다. 토큰을 받은 뒤 delete가 오면 토큰이 무효화되어, 늦게 도착한 옛 값 set이 거부된다.
- AWS 글의 request coalescing도 같은 발상이다. 캐시되지 않은 자원에 대해 진행 중인 요청을 하나로 제한한다.
- 핫 키의 노드 과부하(한 Redis 샤드만 포화)는 로컬 캐시 병행·키 복제로 푼다(원고 04-caching §5).

### 7. write-behind — 쓰기를 캐시에 먼저

```text
  write-through:  앱 → 캐시 → DB (동기)      응답 = DB에 들어감
  write-behind:   앱 → 캐시 → [큐] ~~~> DB     응답 = 캐시에만 들어감
                                   │
                                   └ 프로세스 재시작·큐 유실·DB 거부 → 이미 "성공" 응답한 쓰기가 사라짐
```

- write-behind는 쓰기 지연을 줄이는 대신 **내구성을 캐시 계층에 맡긴다.** 큐가 사라지면 손실이 조용하다. 사용자는 성공을 받았다.
- 같은 키의 쓰기 순서가 큐에서 뒤바뀌거나 DB 제약 위반으로 거부되면, 캐시와 DB가 갈라진다.
- DB가 원본(source of truth)이어야 하는 데이터(돈·재고·주문)에는 쓰지 않는다. 꼭 써야 하면 큐를 내구성 있게(outbox처럼) 만들고 적재 실패를 경보한다.

## 쓰이는 자료구조·알고리즘

- **해시 기반 키** — 가변·긴 입력(검색 조건 등)을 정규화(정렬·기본값 채우기)한 뒤 SHA-256 같은 해시로 줄인다. 앞부분은 사람이 읽을 수 있게 둔다: `app:search:v2:t42:` + `sha256(정규화된 조건)`. [data-structure/05-hashmap](../../data-structure/05-hashmap/2-summary.md)
- **해시 슬롯·해시 태그** — Redis 클러스터는 키 해시로 슬롯을 고른다. `{…}` 안의 부분만 해시에 쓰면 여러 키를 같은 슬롯에 모을 수 있다(Redis keyspace 문서). 노드 간 분산 일반은 [data-structure/31-consistent-hashing](../../data-structure/31-consistent-hashing/2-summary.md).
- **난수 지터** — `ttl × U(0.9, 1.1)`. 균등 분포로 만료 시각을 흩는다. [math/12-randomness-and-prng](../../math/12-randomness-and-prng/2-summary.md).
- **lease 토큰** — 키에 묶인 64비트 토큰으로 set을 조건부로 만든다. 논문은 load-link/store-conditional에 비유한다.
- **축출 정책** — LRU·LFU. Redis의 LFU는 Morris 카운터로 빈도를 센다(Redis eviction 문서). `redis-cli --hotkeys`는 `maxmemory-policy`가 `*lfu`일 때만 동작한다. [data-structure/10-lru-cache](../../data-structure/10-lru-cache/2-summary.md), [data-structure/19-probabilistic-counting](../../data-structure/19-probabilistic-counting/2-summary.md)

## 적용 — 풀어나가는 법

### 1. 키를 한 곳에서 만든다 (Java)

```java
public final class CacheKeys {
    private static final String NS = "app";
    private static final int PRODUCT_V = 3;                 // 값 모양이 바뀌면 올린다

    public static String product(long tenantId, Locale locale, long id) {
        return String.join(":", NS, "product", "v" + PRODUCT_V,
                "t" + tenantId, locale.toLanguageTag(), Long.toString(id));
    }
    public static String search(long tenantId, SearchCond cond) {  // 긴 조건은 정규화 후 해시
        return String.join(":", NS, "search", "v2", "t" + tenantId, sha256Hex(cond.canonicalJson()));
    }
}
```

- `@Cacheable`을 쓰면 `key = "..."` SpEL이나 커스텀 `KeyGenerator`로 테넌트·로캘을 **명시적으로** 넣는다. 기본 생성기는 인자만 본다.

### 2. 직렬화 설정 (Spring Data Redis)

```java
ObjectMapper om = JsonMapper.builder()
        .disable(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES)   // 구버전이 새 필드를 견딘다
        .build();
RedisCacheConfiguration cfg = RedisCacheConfiguration.defaultCacheConfig()
        .prefixCacheNameWith("app:v3:")                                // 키 네임스페이스·버전
        .entryTtl(Duration.ofMinutes(10))                              // 기본은 영구
        .serializeValuesWith(SerializationPair.fromSerializer(
                new Jackson2JsonRedisSerializer<>(om, ProductView.class)));  // 타입 고정, @class 힌트 없음
```

- 캐시 전용 DTO(`ProductView`)를 둔다. 엔티티를 그대로 넣지 않는다. 엔티티의 필드 변경이 곧 캐시 형식 변경이 되기 때문이다.
- 역직렬화 실패를 미스로 처리할지(로그 + 재적재) 요청 실패로 둘지 정한다. 미스로 처리하면 3절의 대량 재적재 위험을 스로틀로 막아야 한다.

### 3. TTL 지터와 null TTL

```java
Duration ttlWithJitter(Duration base) {
    double f = 0.9 + ThreadLocalRandom.current().nextDouble() * 0.2;    // ±10%
    return Duration.ofMillis((long) (base.toMillis() * f));
}
// null(없음)은 짧게: 예) 정상 10분, 없음 30초 (예시)
```

### 4. 진단

```bash
redis-cli INFO stats | grep -E 'keyspace_(hits|misses)|expired_keys|evicted_keys'   # 히트율·만료·축출
redis-cli --bigkeys                    # 큰 키 (SCAN 기반)
redis-cli --hotkeys                    # 핫 키 — maxmemory-policy 가 *lfu 일 때만
redis-cli --scan --pattern 'app:product:v2:*' | head   # 옛 버전 키가 남아 있나
```

- 배포 대시보드에 **캐시 get 오류율**, 히트율, DB QPS를 나란히 둔다. 배포 직후 셋이 같이 움직이면 이 노트의 사고다.
- Redis의 `maxmemory-policy` 기본값은 `noeviction`이다(redis.conf). 가득 차면 새 데이터를 넣는 명령이 오류를 낸다. 캐시 용도면 LRU/LFU 계열로 바꾼다.

## 장애 시나리오와 대처

### 1. 배포 직후 역직렬화 실패 → 요청 실패, 그다음 DB 폭주

- **현상**: 배포가 시작되자 특정 API가 500을 낸다. 급히 캐시를 비우자 이번에는 DB CPU가 100%다.
- **보이는 형태**
  - `org.springframework.data.redis.serializer.SerializationException: Cannot deserialize`, 원인 `java.io.InvalidClassException: … local class incompatible: stream classdesc serialVersionUID = …, local class serialVersionUID = …`.
  - 또는 Jackson 쪽 `SerializationException: Could not read JSON` + `UnrecognizedPropertyException`.
  - 캐시 비운 뒤: 히트율 급락, DB QPS 급등.
- **원인**
  - 캐시 값 클래스가 바뀌었는데 `serialVersionUID`를 선언하지 않았다(또는 JSON 필드가 늘었다).
  - Spring 기본 `SimpleCacheErrorHandler`가 오류를 다시 던진다.
  - 캐시를 비우면 모든 요청이 미스가 되어 DB로 간다(AWS: 대량 재적재 → 브라운아웃).
- **대처**
  - 긴급: 롤백하거나, 캐시 오류를 미스로 처리하게 바꾸되 DB 앞에 동시성 제한을 건다. 전체 flush 대신 새 버전 키 공간으로 옮긴다.
  - 근본: 캐시 전용 DTO + JSON + 관대한 리더. 호환이 깨지는 변경은 키 버전을 올리고 천천히 배포·예열한다. 스테이징에서 "구버전이 쓴 캐시를 신버전이 읽기"와 그 반대를 시험한다.

### 2. 키에 테넌트·로캘 누락 → 다른 사용자 데이터 반환

- **현상**: A사 관리자 화면에 B사 설정이 뜬다. 한국 사용자에게 영어 상품명이 섞인다. 새로고침하면 바뀌기도 한다.
- **보이는 형태**: 에러 없음. 캐시 키 `products::1001`에 테넌트·로캘이 없다. 캐시를 끄면 증상이 사라진다.
- **원인**: 값은 테넌트·로캘에 따라 다른데 키는 id만 담았다. `@Cacheable` 기본 키가 메서드 인자뿐이고, 테넌트는 컨텍스트에 있었다.
- **대처**
  - 긴급: 해당 캐시를 비우고 기능을 캐시 없이 돌린다. 노출 범위를 로그로 확인한다(보안 사고로 다룬다).
  - 근본: 키 생성 함수를 한 곳에 모으고, "값 계산에 쓴 입력 ⊆ 키"를 코드 리뷰·테스트로 검사한다. 두 테넌트로 같은 id를 조회하는 테스트를 둔다.

### 3. 같은 TTL 일괄 적재 → 동시 만료 눈사태

- **현상**: 매일 같은 시각 DB 부하가 치솟고 p99가 튄다. 배치 예열 한 시간 뒤다.
- **보이는 형태**: Redis `expired_keys` 증가 속도와 `keyspace_misses`가 특정 분에 급증. 로컬 재현 시뮬레이션: 고정 TTL이면 1만 개가 같은 분에 만료.
- **원인**: 같은 순간 같은 TTL로 넣었다.
- **대처**: TTL 지터(±10% 등). 인기 키는 lease·싱글플라이트로 한 번만 채운다. soft/hard TTL로 만료 직전 백그라운드 갱신한다.

### 4. "없음"이 너무 오래 캐시됨

- **현상**: 방금 만든 상품이 상세 페이지에서 계속 "없음"이다. 목록에는 보인다.
- **보이는 형태**: 캐시에 그 키의 null 표식이 있다. TTL이 영구(-1)거나 길다.
- **원인**: 생성 전에 누가 조회해 "없음"이 캐시됐다. Spring Data Redis 기본은 null 캐싱 예 + TTL 영구다.
- **대처**: null에는 짧은 별도 TTL을 준다. 생성·수정 시 해당 키를 지운다.

### 5. write-behind 큐 유실 → 조용한 데이터 손실

- **현상**: 사용자가 저장했다고 확인받은 변경 일부가 다음 날 사라져 있다. 에러 로그는 없다.
- **보이는 형태**: 캐시에는 새 값이 있었는데 DB에는 옛 값이다. 캐시 노드 재시작·장애 조치 시각과 손실 시각이 겹친다.
- **원인**: 쓰기를 캐시에 넣고 DB 반영은 메모리 큐로 미뤘다. 큐가 사라지면서 "성공" 응답한 쓰기가 사라졌다.
- **대처**: 원본 데이터는 DB에 먼저 쓴다(write-through 또는 cache-aside + 무효화). 비동기가 꼭 필요하면 내구성 있는 큐(outbox)와 적재 실패 경보를 둔다. [ops-patterns/07-outbox](../../ops-patterns/07-outbox/2-summary.md)

## 핵심 문장

- 캐시 키에는 값이 의존하는 입력이 전부 있어야 한다. 테넌트·로캘이 빠지면 에러 없이 남의 값이 나간다.
- 외부 캐시의 값은 코드 버전 사이의 계약이다. 신버전은 옛 형식을 읽고, 구버전은 새 형식을 견뎌야 한다.
- JDK 직렬화는 `serialVersionUID`가 다르면 실패하고, Spring 기본 오류 처리는 그 실패를 요청 실패로 만든다. 캐시 전용 DTO와 관대한 JSON 리더를 쓴다.
- 버전은 키(공존·콜드 스타트)나 값(관대한 리더)에 둔다. 어느 쪽이든 대량 재적재로 DB를 치지 않게 천천히 옮긴다.
- 같은 TTL은 같은 만료다. 지터로 흩고, 핫 키는 lease·요청 합치기로 한 번만 채운다.
- write-behind는 "성공" 뒤의 손실을 조용히 만든다. 원본 데이터는 DB에 먼저 쓴다.

## 관련 주제·근거

- 선행
  - [30-caching-with-databases](../30-caching-with-databases/2-summary.md) — cache-aside·무효화·3대 사고. 원고: [systems/server-design/04-caching.md](../../systems/server-design/04-caching.md)
  - [api-design/07-versioning-and-compatibility](../../api-design/07-versioning-and-compatibility/2-summary.md) — 하위 호환 규칙.
- 연결
  - reliability `29-cache-stampede` — 원고: [ops-patterns/09-stampede](../../ops-patterns/09-stampede/2-summary.md)
  - [49-multi-level-caching](../49-multi-level-caching/2-summary.md) — 로컬 L1 + Redis L2, 무효화 전파
  - [43-row-level-security](../43-row-level-security/2-summary.md) — 테넌트 격리를 DB에서 강제. 캐시는 그 강제 밖이라 키로 격리해야 한다
- 문서·논문
  - AWS Builders' Library, "Caching challenges and strategies" — 캐시 데이터를 영속 저장소처럼, 형식 호환과 poison pill, 대량 재적재 위험, negative cache, soft/hard TTL, request coalescing, thundering herd <https://aws.amazon.com/builders-library/caching-challenges-and-strategies/>
  - R. Nishtala 외, "Scaling Memcache at Facebook", NSDI 2013 — demand-filled look-aside, 쓰기 시 delete(멱등), lease(stale set·thundering herd, 키당 10초, 17K/s → 1.3K/s), Gutter <https://www.usenix.org/system/files/conference/nsdi13/nsdi13-final170_update.pdf>
  - Redis 문서 — Keys and values(키 스키마·긴 키·해시·해시 태그) <https://redis.io/docs/latest/develop/using-commands/keyspace/> · redis-cli(`--hotkeys`는 `*lfu` 정책에서만) · Key eviction(정책·LFU Morris 카운터) · INFO(`keyspace_hits` 등) · `redis.conf`(`maxmemory-policy noeviction` 기본)
  - Java SE 21 `java.io.Serializable` — `serialVersionUID`, `InvalidClassException`, 명시 선언 권고
  - Spring Data Redis 소스 — `RedisCacheConfiguration.defaultCacheConfig()`(영구 TTL·null 캐싱·`JdkSerializationRedisSerializer`), `CacheKeyPrefix`(`::`), `JdkSerializationRedisSerializer`(`Cannot deserialize`), `GenericJackson2JsonRedisSerializer`(`new ObjectMapper()`, `@class`, `Could not read JSON`) <https://github.com/spring-projects/spring-data-redis>
  - Spring Framework 소스 — `SimpleKeyGenerator`(인자만으로 키), `SimpleCacheErrorHandler`(오류 재던짐), `Jackson2ObjectMapperBuilder`(FAIL_ON_UNKNOWN_PROPERTIES 끔) <https://github.com/spring-projects/spring-framework>
  - jackson-databind `DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES(true)`
- 로컬 재현(Java 1.8.0_504 Nashorn, Node 18.19.1): UID를 바꾼 직렬화 스트림의 `InvalidClassException` 메시지, TTL 고정 vs ±10% 지터의 분당 만료 분포(1만 키). Redis·Spring 동작은 문서·소스 확인(실행 재현 아님)
