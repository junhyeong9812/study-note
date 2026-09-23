# cs/issue/java/spring/framework-default-contracts — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 이슈 원문 기준. 복습 전 읽지 말 것.

태그: —

## 정답
<!-- 질문 1:1 대응 -->

1. **자기 호출은 프록시를 안 거친다.** 스프링은 `@Cacheable`·`@Transactional` 빈을 **프록시로 감싸** 등록하고, 다른 빈이 주입받는 것은 그 프록시다. 외부 호출은 프록시 → 어드바이스 → 실제 객체 순으로 가지만, 실제 객체 안의 `this.getCodes(id)`는 프록시를 거치지 않고 자기 메서드를 직접 부르므로 어드바이스가 건너뛰어진다.\
   우회는 `AopContext.currentProxy()`로 자기 프록시를 얻어 호출하는 것이고, 이를 위해 `exposeProxy = true` 설정이 필요하다. Mockito 단위 테스트에는 프록시가 없어 `currentProxy()`가 `IllegalStateException`을 던지므로, 단위 테스트는 캐시 메서드 자체만, 자기 호출 경로는 전체 컨텍스트 통합 테스트에서 검증했다.
   > **AOP 프록시** — 대상 빈을 감싸 메서드 호출 앞뒤에 부가 기능(캐시·트랜잭션)을 끼우는 대리 객체.

2. **save = merge.** Spring Data의 `save()`는 엔티티가 "새것"인지 판단해 새것이면 `persist`, 아니면 `merge`를 부른다. 기본 판단은 ID가 비어 있는가인데, 애플리케이션이 ID를 할당하는 엔티티는 항상 ID가 채워져 있으므로 **기존 엔티티로 판정되어 merge**(SELECT 후 INSERT 또는 UPDATE)로 간다.\
   merge는 "있으면 덮어쓰기"라서, 같은 키로 동시에 등록하면 한쪽이 다른 쪽을 **덮어쓸 수 있고** insert 키 충돌로 감지되지 않는다. 교정은 `Persistable`을 구현해 `isNew()`를 신규 플래그로 결정하거나, `EntityManager.persist`를 직접 호출해 persist 경로를 강제하는 것 — 그러면 중복 키가 제약 위반으로 드러난다.
   > **persist vs merge** — persist는 새 엔티티를 영속화(INSERT)하고, merge는 분리된 엔티티 상태를 영속 엔티티에 복사(조회 후 INSERT/UPDATE)한다.

3. **두 전제가 동시에 바뀐다.**
   - **무자격 주입**: 타입 기반 주입은 후보가 하나일 때만 결정적이다. 둘이 되면 `NoUniqueBeanDefinitionException`. 필드에 `@Qualifier`를 달아도 Lombok의 생성자 자동 생성은 기본 설정에서 그 어노테이션을 **생성자 파라미터로 복사하지 않는다**.
   - **자동설정 back-off**: `@ConditionalOnMissingBean` 기반 자동설정은 사용자가 같은 타입 빈을 **하나라도** 정의하면 통째로 물러난다 — 레거시 DB용 DataSource 하나를 추가하면 기본 DataSource 자동구성이 꺼지므로, 운영 DataSource를 `@Primary`로 명시하지 않으면 ORM·마이그레이션 등 운영 DataSource에 기대던 것이 전부 부팅에서 무너진다.\
   기존 주입을 건드리지 않는 교정: **기존(운영) 빈에 `@Primary`**, 새 빈은 **`@Qualifier("name")`로 명시 주입**. 자동설정이 물러난 빈은 `@Bean`으로 직접 선언한다. Lombok을 쓸 때는 명시 생성자에 `@Qualifier`(또는 설정으로 복사 허용).

4. **조건 평가 시점.** `@Import`된 설정은 사용자 `@Configuration`과 같은 단계에서 파싱되어, **자동구성(DataSource 자동구성 포함)보다 먼저** 조건이 평가된다. `@ConditionalOnBean`은 평가 시점까지 등록된 빈만 보므로 "DataSource 없음"이 되고, 그 설정과 그에 의존하는 서비스·컨트롤러가 연쇄로 빠져 404가 났다. `@AutoConfigureAfter`는 자동구성으로 등록된 클래스에만 효력이 있어 `@Import` 경로엔 소용없다.\
   정식 해결은 라이브러리 JAR에 `META-INF/spring/...AutoConfiguration.imports`를 두어 그 설정을 **자동구성 순서에 편입**하는 것. 진단은 `--debug`로 조건 평가 리포트를 보면 "did not find any beans"가 찍힌다. 이 수정 뒤에 가려져 있던 다음 결함이 드러났다.

5. **필터 이중 실행과 체인 공백.** 스프링 부트는 `Filter` 타입 빈을 **서블릿 컨테이너 필터(`/*`)로 자동 등록**한다. 그 필터를 시큐리티 체인에도 넣으면 요청마다 **두 번** 실행되고, 체인 전용이어야 할 필터가 모든 요청에 걸린다. 교정은 `@Component` 없이 `new`로 만들어 체인에만 넣거나, `FilterRegistrationBean.setEnabled(false)`로 컨테이너 등록을 끄는 것.\
   여러 `SecurityFilterChain`이 있으면 `securityMatcher`가 맞는 **첫 체인만** 적용된다. 어느 체인에도 안 맞는 경로는 정책이 없는 공백이 된다. 그래서 가장 낮은 우선순위에 `anyRequest().denyAll()` 체인을 두어, 체인을 지우거나 매처를 빠뜨리면 해당 경로가 자동으로 거부되게 한다(fail-closed).

6. **조용히 무효인 기본 동작.**
   - `@CreatedDate`: `@EnableJpaAuditing`(+ 감사 리스너)가 없으면 상속만으로는 **아무 일도 일어나지 않고** 값이 null — 오류도 없다. 그 컬럼으로 집계하는 기능에서 치명적이다.
   - `@Query` DELETE: `@Query`는 기본적으로 조회로 실행된다 → `@Modifying`(+ 트랜잭션)을 명시해야 변경 쿼리 경로를 탄다(없으면 "DML 미지원" 예외).
   - `@Pattern`: Bean Validation 제약은 **null을 유효로 본다** → `@NotBlank`/`@NotNull`을 따로 달지 않으면 null이 인코더까지 흘러가 500.
   - 네이밍 전략: 기본 물리 네이밍 전략이 **따옴표로 감싼 식별자까지 소문자화**해, 대소문자를 구분하는 DB에서 대문자 테이블을 못 찾았다 → 따옴표 식별자는 그대로 두고 나머지만 위임하는 전략을 빈으로 노출.

7. **왜 늦게 드러나나.** 이 동작들은 **컨텍스트 조립·프록시·자동구성·실 DB** 단계에서 결정된다. 단위 테스트는 그 단계를 거치지 않고(프록시 없음·자동구성 없음·대체 DB), 컴파일러는 어노테이션의 의미를 검사하지 않는다.\
   드러낸 방법: `--debug` **조건 평가 리포트**로 어떤 조건이 왜 빠졌는지 확인, 자기 호출·감사·필터 체인은 **전체 컨텍스트 통합 테스트**, 네이밍·스키마는 **실 DB 통합 테스트**, 감사 필드는 `save` 후 `createdBy·createdDate != null`을 **명시적으로 단언**. 단언하지 않은 곳(다른 엔티티의 같은 감사 결함)은 아무도 모르고 남아 있었다.

## 문제 구조 (추상화 코드)

### 변형 A — 프록시 self-invocation
① 문제 코드
```java
@Service
public class LookupService {
    @Cacheable("codes") public List<Code> getCodes(String groupId) { /* DB */ }
    public String getName(String groupId, String code) {
        return getCodes(groupId).stream()...;              // this 호출 → 프록시 우회 → 캐시 미적용
    }
}
```
② 고친 코드
```java
@EnableAspectJAutoProxy(exposeProxy = true)                 // 자기 프록시 노출
// ...
    public String getName(String groupId, String code) {
        return ((LookupService) AopContext.currentProxy()).getCodes(groupId).stream()...;
    }
// 단위 테스트엔 프록시가 없어 IllegalStateException → 이 경로는 전체 컨텍스트 IT로 검증
```
무엇이 깨졌나: 어드바이스는 프록시를 통과한 호출에만 붙는데, 내부 호출은 프록시를 지나지 않았다.\
같은 구조: 권한 확인 서비스의 내부 `@Cacheable` 호출도 동일하게 미적용 → 자기 프록시 경유, 단일 키 캐시는 `key="'all'"`.

### 변형 B — 빈 해석: 후보 선택·이름·생성자
① 문제 코드
```java
@Component class Lexicon {
    Lexicon() {}                                    // 생성자 2개 + 표시 없음 → no-arg 선택
    Lexicon(DbClient client) { ... }                // 의존성 null
}
@RequiredArgsConstructor class FileUtil {
    @Qualifier("fileIdSource") private final IdSource idGen;   // Lombok 생성자엔 @Qualifier 미복사 → 모호
}
@TestConfiguration class TestSupport {
    @Bean Helper helper() { ... }
    @Component static class Helper { ... }          // 스캔 + @Bean 이중 경로 → 빈 2개
}
record ApiProps(String key, String url, int timeout) {
    ApiProps(String key, String url) { this(key, url, 5); }   // 생성자 2개 → 바인딩 생성자 모호 → 부팅 실패
}
```
② 고친 코드
```java
@Component class Lexicon { Lexicon(DbClient client) { ... } }       // 단일 생성자 + 배선 테스트
class FileUtil { FileUtil(@Qualifier("fileIdSource") IdSource idGen) { ... } }   // 명시 생성자
@TestConfiguration class TestSupport { @Bean Helper helper() { ... } static class Helper { ... } }
record ApiProps(String key, String url, int timeout) {}              // 보조 생성자 제거
```
무엇이 깨졌나: 프레임워크가 여럿 중 하나를 "기본 규칙"으로 고르거나 못 고르는 자리에서, 의도를 명시하지 않았다.\
같은 구조: 같은 타입 빈 2개 → `required a single bean, but 2 were found` → `List<T>` 주입 + 합성(composite), 또는 `@Primary`.\
같은 구조: 설정 프로퍼티 활성화 어노테이션이 만드는 빈 이름은 `<prefix>-<FQCN>` 형식이라 표현식의 `@shortName` 참조가 실패.\
같은 구조: 이름 없는 `@PathVariable`은 컴파일 파라미터 메타데이터(`-parameters`)에 의존 — 최신 버전은 없으면 요청 시점에 실패 → `@PathVariable("userId") String userNo`로 와이어 이름 고정.

### 변형 C — 자동설정·자동등록·조건 평가 순서
① 문제 코드
```java
@Import(MonitoringConfig.class) public @interface EnableFeature {}
@Configuration
@ConditionalOnBean(DataSource.class)                   // 자동구성보다 먼저 평가 → "없음" → 설정 전체 누락
class MonitoringConfig { ... }

@Bean DataSource oldDataSource() { ... }            // 같은 타입 1개 추가 → 기본 DataSource 자동구성 back-off
@Bean CryptoService secondaryCrypto() { ... }         // 기존 무자격 주입이 모호해짐

@Component class KeyAuthFilter extends OncePerRequestFilter { ... }   // 서블릿 /* 자동 등록
http.addFilterBefore(keyAuthFilter, UsernamePasswordAuthenticationFilter.class);   // + 체인 → 2회 실행
```
② 고친 코드
```text
# 라이브러리 JAR: META-INF/spring/...AutoConfiguration.imports
com.example.feature.MonitoringConfig                   # 자동구성 순서에 편입
```
```java
@Bean @Primary @ConfigurationProperties("app.datasource")
DataSource dataSource(...) { ... }                      // 운영 DataSource를 명시 + @Primary
@Bean @Qualifier("legacy") DataSource oldDataSource() { ... }
@Bean @Primary CryptoService crypto() { ... }           // 기존 주입 무수정 보존
@Bean @Qualifier("secondaryCrypto") CryptoService secondaryCrypto() { ... }

@Bean FilterRegistrationBean<KeyAuthFilter> off(KeyAuthFilter f) {
    var r = new FilterRegistrationBean<>(f); r.setEnabled(false); return r;   // 체인 등록만 유효
}
@Bean @Order(Ordered.LOWEST_PRECEDENCE)
SecurityFilterChain defaultChain(HttpSecurity http) throws Exception {
    return http.authorizeHttpRequests(a -> a.anyRequest().denyAll()).build();  // 매처 밖 = 거부
}
```
무엇이 깨졌나: 빈 하나의 추가·선언 위치가 조건 평가·자동설정·필터 등록의 전역 기본 동작을 바꿨다.\
같은 구조: 클래스패스에 XML 데이터포맷 라이브러리를 추가하자 자동설정이 **모든** HTTP 클라이언트에 XML 컨버터를 끼워 다른 연동이 회귀(전체 스위트가 포착).\
같은 구조: 표현식의 `@bean` 참조는 표현식 핸들러에 애플리케이션 컨텍스트(BeanResolver)가 주입돼 있어야 해석됨 → 핸들러에 컨텍스트 주입.

### 변형 D — JPA/Spring Data 기본 동작
① 문제 코드
```java
@Entity class CodeGroup { @Id String code; }             // 할당 ID
repo.save(new CodeGroup("A"));                           // ID 있음 → merge → 동시 등록 덮어쓰기

@Query("DELETE FROM Session s WHERE s.startedAt < :t")   // @Modifying 없음 → DML 미지원 예외
int deleteOld(Instant t);

@MappedSuperclass class BaseTime { @CreatedDate Instant createdDate; }   // 감사 미활성 → 조용히 null

@Table(name = "`LEGACY_TABLE`")                          // 기본 네이밍 전략이 소문자화 → 대소문자 구분 DB에서 없음
```
② 고친 코드
```java
@Entity class CodeGroup implements Persistable<String> {
    @Id String code;
    @Transient boolean newEntity = true;
    public boolean isNew() { return newEntity; }          // persist 경로 강제
}
@Modifying @Transactional
@Query("DELETE FROM Session s WHERE s.startedAt < :t") int deleteOld(Instant t);

@Configuration @EnableJpaAuditing class AuditConfig {
    @Bean AuditorAware<String> auditor() { return () -> currentUser().or(() -> Optional.of("SYSTEM")); }  // 미인증이면 SYSTEM
}
// 켜기 전 기존 상속 엔티티의 감사 컬럼 nullable 확인, 마이그레이션 시드는 감사를 안 타므로 직접 기입

class QuotedAwareNaming implements PhysicalNamingStrategy {  // 따옴표 식별자는 그대로, 나머지는 기존 전략 위임
    public Identifier toPhysicalTableName(Identifier id, JdbcEnvironment env) {
        return id.isQuoted() ? id : delegate.toPhysicalTableName(id, env);
    }
}
```
무엇이 깨졌나: 식별자 할당·쿼리 종류·감사·네이밍의 기본값이 코드의 가정과 달랐고, 대부분 오류 없이 지나갔다.\
같은 구조: SQL 매퍼 → JPA 전환에서 수동 복합키 `save`=merge(선조회) → `persist`, 명시 컬럼 UPDATE를 변경 감지로 바꾸면 과·소 갱신 → bulk update로 동치 유지, left join 대상 조건을 where에 두면 inner join으로 변질 → `on`에.\
같은 구조: 값 컬렉션(`@ElementCollection`) 테이블은 기본적으로 (부모, 값) 유일 제약이 없어 같은 값이 두 번 들어갈 수 있음 → 서비스에서 `Set.add` 반환값으로 중복 흡수.

### 변형 E — 그 밖의 기본 계약
① 문제 코드
```java
@Pattern(regexp = "...") String password;                // null은 통과 → 인코더에서 IllegalArgumentException → 500
UserDetails loadUserByUsername(String id) { throw new IllegalArgumentException(); }  // 인증 실패로 변환 안 됨

Cache.ValueWrapper hit = cache.get(key);
return hit.get();                                         // 미스면 hit == null → NPE (cold 캐시 500)

InputStreamResource part = new InputStreamResource(in);  // contentLength()가 스트림을 끝까지 읽음 → 본문 소진
```
```yaml
# application-integration.yml
spring.profiles.active: integration                      # 프로파일 전용 파일 안의 활성화 선언 → 부팅 실패
```
② 고친 코드
```java
@NotBlank @Pattern(regexp = "...") String password;     // (권고)
throw new UsernameNotFoundException("not found");        // (권고) 인증 예외 계열 → 사용자 열거 은닉 유지

Cache.ValueWrapper hit = cache.get(key);                  // 3상태: null=미스 / wrapper(null)=캐시된 null / wrapper(v)
if (hit == null) return null;
return (T) hit.get();

new InputStreamResource(in) {
    @Override public String getFilename() { return file.getOriginalFilename(); }
    @Override public long contentLength() { return file.getSize(); }   // 길이 산정용 read 방지
};
```
```java
@ActiveProfiles("integration")                            // 활성화는 파일 밖에서
```
무엇이 깨졌나: 검증·인증 예외·캐시 반환·멀티파트 길이·프로파일 활성화의 기본 계약을 코드가 다르게 가정했다.\
같은 구조: 템플릿 엔진이 보안 정책상 표현식의 정적 클래스 접근(`T(...)`)·객체 생성을 금지 → 가공은 모델/유틸에서.\
같은 구조: `@PostConstruct`는 인프라 준비를 보장하지 않고 cron은 zone이 없으면 JVM 기본 타임존 → 초기 적재는 `ApplicationReadyEvent`, `@Scheduled(cron = ..., zone = "<서비스 타임존>")`.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log
