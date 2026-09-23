# cs/issue/java/spring/framework-default-contracts — 명시하지 않으면 프레임워크 기본 동작이 조용히 다르게 움직인다 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> ⚠️ **이 질문 목록은 Claude 초안이다(2026-09-24).** 읽고 본인 질문으로 교체한 뒤 이 줄을 지운다.

## 질문
1. 같은 클래스 안에서 `this.getCodes(id)`로 자기 `@Cacheable` 메서드를 부르면 캐시가 안 걸린다. 프록시 기반 AOP의 구조로 이유를 설명하고, `AopContext.currentProxy()`로 우회할 때 필요한 설정과 단위 테스트에서 생기는 문제를 말하라.
2. 예측: ID를 애플리케이션이 직접 할당하는 엔티티(자연키·수동 복합키)를 `repository.save(entity)`로 등록한다. 같은 키로 두 요청이 동시에 등록하면 무슨 일이 일어나는가 — `save`가 내부에서 persist와 merge 중 무엇을 고르는지, 그 판단 기준은 무엇인가.
3. 기존 코드가 잘 돌던 애플리케이션에 **같은 타입의 빈을 하나 더** 등록했다(두 번째 DataSource, 두 번째 암호화 서비스). 그 순간 바뀌는 두 가지는 무엇인가 — 무자격 주입과 `@ConditionalOnMissingBean` 자동설정 관점에서. 기존 주입 지점을 건드리지 않고 고치는 방법은?
4. 라이브러리가 `@EnableX` → `@Import(XConfig.class)`로 설정을 끌어오는데, `XConfig`의 `@ConditionalOnBean(DataSource.class)`가 "빈 없음"으로 평가돼 기능 전체가 빠졌다(DataSource는 실제로 등록됐다). 왜 그런가, 그리고 정식 해결은 무엇인가.
5. 경계: 필터를 `@Component`(또는 `@Bean`)로 만들고 시큐리티 체인에도 `addFilterBefore`로 넣으면 몇 번 실행되는가? 여러 `SecurityFilterChain`이 있을 때 어느 체인의 `securityMatcher`에도 안 맞는 경로는 어떻게 되며, 왜 catch-all `denyAll` 체인을 두는가.
6. "오류 없이 조용히 무효"인 기본 동작을 3개 이상 들어라 — `@CreatedDate`, `@Query` DELETE, `@Pattern`, 대소문자 구분 DB에서의 따옴표 테이블명 — 각각 무엇을 명시하지 않아서 생겼는가.
7. 연결: 이 카드의 사례들이 단위 테스트나 컴파일에서 잘 안 잡히는 이유는 무엇이고, 어떤 방법으로 드러냈는가(조건 평가 리포트, 전체 컨텍스트·실 DB 통합 테스트, 명시적 단언).

## 복습 기록
| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
