# cs/issue/testing/verification-environment-parity — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-24) — 이슈 원문 기준. 복습 전 읽지 말 것.

태그: `test-reliability`

## 정답
<!-- 질문 1:1 대응 -->

1. **동작을 구현하지 않는 더블.** jsdom은 Tab 키의 **기본 포커스 이동을 구현하지 않는다**. 그래서 Tab/Shift+Tab 이벤트를 쏴도 포커스는 원래 자리에 그대로 있고, "포커스가 모달 안에 남았나"를 단언하면 트랩 코드가 맞든 틀리든 **항상 참**이 된다 — 결과가 결함 유무와 무관하다.\
   고친 방법은 단언을 더블이 재현하는 것으로 바꾸는 것이다: 핸들러가 `preventDefault` 후 **지정한 위치(first/last)로 포커스를 옮겼는가**를 본다.\
   검출력은 뮤테이션으로 실증한다 — 판정 코드를 취약 버전으로 되돌리면 해당 테스트 1건만 실패해야 한다.
   > **테스트 더블** — 테스트에서 실제 구성요소 대신 쓰는 대역(mock·fake·에뮬레이터·인메모리 DB 등).
   > **뮤테이션 검증** — 일부러 결함을 넣어 테스트가 실패하는지 보고 테스트의 검출력을 확인하는 것.

2. **create-drop이 못 보는 것.** 테스트는 통과하고 운영은 `missing table` 으로 기동·조회가 실패한다.\
   `ddl-auto=create-drop`은 **엔티티 정의에서 스키마를 만들어 낸다** — 엔티티가 단수형 이름을 가리키면 단수형 테이블이 생기므로 엔티티와 스키마는 항상 일치한다.\
   운영 스키마는 마이그레이션 DDL(복수형)이 만든다. 불일치는 "엔티티 ↔ DDL" 사이에 있는데, create-drop은 DDL을 아예 쓰지 않으니 **원리적으로 볼 수 없다**. 같은 이유로 DDL에 없는 감사 컬럼, `columnDefinition`과 필드 타입 불일치도 숨는다.\
   여기에 인메모리 DB의 **방언 차이**(예약어 `USER` 등, 날짜 집계 함수)가 겹친다. 이런 것은 실 DB 컨테이너 통합 테스트로만 실증된다.
   > **ddl-auto** — ORM이 기동 시 엔티티를 기준으로 스키마를 생성·검증하는 모드(create-drop·update·validate·none).

3. **빌드 스테이지 ≠ 런타임 스테이지.** 빌드 스테이지에는 소스 전체가 있으므로 설정 파일의 `import`가 풀리고 빌드는 통과한다.\
   런타임 스테이지는 빌드 산출물·의존성·설정 파일**만** 복사하므로, 설정이 import하던 앱 소스 폴더가 없다 → 서버 시작 시 설정 로드가 `MODULE_NOT_FOUND`로 실패 → 설정(여기선 base path)이 적용되지 않은 채 떠서 그 경로가 404, 컨테이너는 크래시 루프.\
   빌드 green이 "런타임에서 로드된다"를 증명한다고 믿게 만들기 때문에 **그린 위장**이다.\
   진단 요령: 404 응답에 앱 프레임워크 헤더가 있으면 프록시가 아니라 앱 빌드 문제다. 교정은 설정 파일을 **자체완결**(앱 소스 import 없이 리터럴·환경변수)로 만들고 이미지를 재빌드하는 것.

4. **실행 모드 일반화 금지.** 안 된다. 실행 모드가 바뀌면 **출력 포맷·능력 보고·타이밍**이 달라질 수 있다.\
   한 CLI 도구는 헤드리스 모드에서 사용자 입력을 문자열로 기록했지만 대화형 모드에서는 `[{type:"text"}]` 배열로 기록해, 헤드리스에서만 실측한 파서 규칙이 대화형 입력을 전부 놓쳤다.\
   헤드리스 브라우저는 포인터 hover 능력을 false로 보고하므로 `@media (hover:hover)`로 감싸 생성된 hover 스타일이 적용되지 않는다 — hover UI를 헤드리스로 검증할 수 없다(같은 규칙쌍의 `focus-within`으로 대체 검증하고, 실브라우저 확인은 사람에게). 또 `visibility:hidden` 요소는 포커스를 받을 수 없다.

5. **도구 차이.** 서버 버그가 아니다. 브라우저(`encodeURIComponent`·`EventSource`)는 비ASCII를 퍼센트 인코딩해 보내지만, curl은 넣은 바이트를 그대로 보내고 서버는 인코딩되지 않은 문자가 든 URL을 400으로 거부한다.\
   판단 근거는 "같은 요청을 실제 클라이언트와 같은 형태로 만들어 보내면 통과하는가"다 — `curl -G --data-urlencode`로 인코딩하면 정상이고, 코드 변경은 필요 없다.

6. **운영 컨텍스트의 일부만 올리는 도구들.**
   - standalone MockMvc: 컨트롤러 인스턴스와 주어진 mock만으로 디스패치를 흉내 낸다 → `@ControllerAdvice`·AOP(권한 어노테이션)·필터 체인이 빠진다. 권한은 전체 컨텍스트/필터 체인 통합 테스트로.
   - `new ObjectMapper()`: 프레임워크가 자동 구성하며 등록하는 모듈(JSR310 등)이 없다 → `Instant` 직렬화 실패. 테스트는 `findAndRegisterModules()` 또는 컨텍스트의 매퍼를 쓴다. mock 응답 객체는 원시 `Set-Cookie` 헤더를 쿠키 모델로 해석하지 않으므로 헤더 문자열로 검증한다.
   - `@DataJpaTest` 슬라이스: `@Configuration`을 읽지 않아 필요한 설정을 `@Import`해야 하고, 전역 감사 설정이 없으면 `@CreatedDate`가 null, self-proxy 캐시는 mock으로 검증 불가, 마이그레이션 시드는 실행되지 않는다.\
   공통점: **횡단 동작(프록시·감사·마이그레이션·advice)은 통합 테스트에서만 검증된다.**

7. **컴파일 OK ≠ 기동 OK.** Spring Data는 **리포지토리 빈을 만들 때 `@Query` JPQL을 파싱·검증**한다. 호출 여부와 무관하게 빈 생성 단계에서 실패하므로 오타 하나가 애플리케이션 기동 자체를 막는다. 컴파일러는 문자열 안의 JPQL을 보지 않는다.\
   실 DB 이관은 스키마·방언 결함을 잡지만 기동 경로 전체를 보지는 않는다. 기동 스모크는 빈 생성 시 검증되는 것(JPQL·와이어링)을 잡지만, 생성자 투영 인자 수 불일치처럼 **쿼리가 실행될 때만** 드러나는 결함은 못 잡는다 — 둘은 대체재가 아니라 층이 다르다(아래 방안 비교).

## 문제 구조 (추상화 코드)

### 변형 A — 테스트 더블이 검증 대상 동작을 구현하지 않음
① 문제 코드
```ts
// jsdom: Tab 기본 포커스 이동 미구현
const isInsideTrap = dialog.contains(active);          // DOM 포함 ≠ 탭 순서 포함
if (e.shiftKey && (!isInsideTrap || active === first)) { e.preventDefault(); last.focus(); }
// test
fireEvent.keyDown(document, { key: "Tab", shiftKey: true });
expect(dialog.contains(document.activeElement)).toBe(true);   // 포커스가 안 움직이니 항상 참
```
② 고친 코드
```ts
const isInsideTrap = active !== null && focusable.includes(active);   // disabled 된 요소 제외
// test: 핸들러가 "지정 위치로 옮겼나"를 단언 → 판정을 되돌리면 이 테스트만 실패(뮤테이션 확인)
expect(document.activeElement).toBe(lastFocusable);
```
무엇이 깨졌나: 에뮬레이터가 Tab 이동을 안 하니 "안에 남았다"는 단언이 결함과 무관하게 참이었다.\
같은 구조: 문서 레이아웃 검사가 `pdftotext -bbox`(단어만 출력, `<line>` 없음)를 파싱해 겹침 0건으로 거짓 통과 → 줄 구조를 출력하는 `-bbox-layout`으로 교체.

### 변형 B — 대체 DB가 스키마·방언을 재현하지 않음
① 문제 코드
```java
@Entity                                   // @Table 없음 → 단수형 기본 매핑
public class Grant extends BaseEntity {    // BaseEntity 감사 컬럼 4개는 마이그레이션 DDL에 없음
    @Column(columnDefinition = "tinyint default '0'") Integer flag;   // 타입 검증 불일치
}
# test: spring.jpa.hibernate.ddl-auto=create-drop (H2, 마이그레이션 off)  → green
# prod: MySQL + 마이그레이션(복수형 테이블)                              → missing table
```
② 고친 코드
```java
@Entity @Table(name = "grants")           // 마이그레이션과 같은 이름을 명시
public class Grant extends BaseEntity {
    Integer flag;                          // 기본값은 DDL, 타입은 ORM 추론 (columnDefinition 제거)
}
// 누락 컬럼은 새 마이그레이션 ALTER로 추가
// H2: NON_KEYWORDS=USER,...   /  날짜 집계·시드는 실 DB 컨테이너 IT로만 검증
```
무엇이 깨졌나: create-drop은 엔티티에서 스키마를 만들어 엔티티↔DDL 불일치를 볼 수 없었다(`update`/`none`으로 바꿔도 검증 에러는 남았다).\
같은 구조: 테스트 슬라이스가 설정을 안 읽어 `@Import` 필요, 전역 감사 설정 부재로 `@CreatedDate` null, 시드는 실행 안 됨 → 감사 설정 활성화 + 시드·캐시 검증은 실 DB IT.\
같은 구조: 운영 DB에만 정제 테이블이 있고 테스트 DB엔 원천 테이블만 있어, 코드 변경 없이 테스트 DB에서 "테이블 없음" 500 → 환경 모드로 SQL을 명시 분기(원천 모드는 삭제행 제외·그룹핑·누락 컬럼 `NULL as alias`로 결과 시그니처 통일).

### 변형 C — 빌드 스테이지에만 있는 파일
① 문제 코드
```dockerfile
FROM node AS build
COPY . .                                   # src/shared 포함 → build OK
RUN npm run build
FROM node AS runtime
COPY --from=build /app/.next /app/public /app/node_modules /app/app.config.ts ./
# app.config.ts: import { BASE } from "./shared/config/base"   → 런타임엔 shared 없음
```
② 고친 코드
```ts
// app.config.ts — 자체완결 (앱 소스 import 없음)
const BASE_PATH = process.env.PUBLIC_BASE_PATH || "/app";
```
무엇이 깨졌나: 설정 로드가 런타임에서만 실패해 설정 없이 떴고, 빌드 green이 그것을 가렸다.\
같은 구조: 런타임 JDK 버전에 따라 구현을 고르는 멀티릴리스 소스셋은 로컬의 낮은 JDK로는 재현조차 안 됨 → 빌드가 `--release N` 플래그만 쓰므로 더 높은 JDK toolchain으로 해당 소스셋 테스트 태스크를 실행.

### 변형 D — 컨텍스트 일부만 올리는 웹 테스트
① 문제 코드
```java
mvc = MockMvcBuilders.standaloneSetup(new Controller(useCase)).build();   // advice·AOP·필터 없음
ObjectMapper om = new ObjectMapper();            // JSR310 미등록 → Instant 직렬화 예외
response.getCookie("token");                     // mock은 Set-Cookie 헤더를 파싱 안 함 → null
```
② 고친 코드
```java
mvc = MockMvcBuilders.standaloneSetup(new Controller(useCase))
        .setControllerAdvice(new ExceptionAdvice()).build();   // advice 경유 정책이면
ObjectMapper om = new ObjectMapper().findAndRegisterModules();
assertThat(response.getHeader("Set-Cookie")).contains("token=");
// 권한(AOP)은 전체 컨텍스트 / 필터 체인 통합 테스트에서 검증
```
무엇이 깨졌나: 테스트가 통과해도 권한 검증·에러 직렬화가 실제로 동작하는지는 알 수 없었다.

### 변형 E — 실행 모드·클라이언트가 다름
① 문제 코드
```python
# 헤드리스 모드에서만 실측한 규칙
is_prompt = entry.role == "user" and isinstance(entry.content, str)   # 대화형은 [{type:"text"}] 배열
```
```sh
curl "http://host/ask?q=한글"              # 비ASCII 원바이트 그대로 → 400
```
② 고친 코드
```python
def is_prompt(entry):                      # 문자열·text 배열 모두 인정, tool_result 배열은 제외
    return entry.role == "user" and extract_text(entry.content) is not None
# 실제 대화형 세션 로그로 재확인
```
```sh
curl -G "http://host/ask" --data-urlencode "q=한글"   # 브라우저와 같은 인코딩
```
무엇이 깨졌나: 한 모드·한 도구에서 본 결과를 다른 모드·실제 클라이언트로 일반화했다.\
같은 구조: 헤드리스 브라우저는 `(hover:hover)`가 false라 hover 변형이 적용 안 됨 → 빌드 CSS에 규칙 존재 확인 + `focus-within` 쌍으로 대체 검증, 실브라우저 확인은 사람에게.

## 검증 기록
- 2026-09-24: 출처 원문 대조(Claude 초안) — 근거는 작업 log

## 방안 비교

기본 방안(위 변형 A~E)은 "검증 환경을 실행 환경에 맞추거나(실 DB·실 세션·런타임 이미지), 더블이 재현하는 것만 단언한다"이다. 같은 원리에 다른 방안이 쓰인 사례:

### 방안 1 — 컴파일 OK ≠ 기동 OK: 기동까지 스모크
```java
public interface ItemRepository extends JpaRepository<Item, Long> {
    @Query("select i from Item i where i.createdAt > :t")   // 필드는 createdDate — 호출처 없음
    List<Item> recent(Instant t);                          // 그래도 빈 생성 시 검증 → 기동 실패
}
// 교정: 필드명 수정 + 커밋 전 "컴파일"이 아니라 "애플리케이션 기동"까지 스모크
@DataJpaTest @AutoConfigureTestDatabase(replace = NONE) @ActiveProfiles("test")
@Import(QueryConfig.class)              // 슬라이스는 @Configuration을 읽지 않음
class RepositorySmokeTest { /* 컨텍스트가 뜨는지 + 쿼리 1회 실행 */ }
// 생성자 투영(Projections.constructor) 인자 수 불일치는 쿼리 실행 때만 드러남 → 실행까지 해야 잡힘
// 컴파일러는 첫 에러에서 멈출 수 있음 → 정적 스캔으로 선발굴 후 반복 컴파일
```

| 방안 | 전제 | 비용 | 실패 모드 | 맞는 조건 |
|------|------|------|-----------|-----------|
| 기본: 실행 환경을 재현한 검증(실 DB IT·런타임 이미지·실 세션) | 차이 나는 동작이 검증 대상이다 | 컨테이너·실행 시간 | 재현 범위 밖의 차이는 여전히 숨음 | 스키마·방언·런타임 로드·모드별 포맷 |
| 1. 기동까지 스모크 | 결함이 기동 시 검증 단계에 걸린다 | 기동 1회 | 실행 시에만 평가되는 결함(투영 불일치)은 통과 | 대규모 리팩터링 후·"빌드만 되는" 코드 |

**결론**: 두 방안은 층이 다르다.\
기동 스모크는 싸고 빈 생성 시점의 결함(JPQL·와이어링)을 넓게 잡으므로 **먼저** 돌린다.\
스키마·방언·런타임 환경 차이가 검증 대상이면 기동만으로는 부족하고, **그 차이를 재현한 환경**(실 DB 컨테이너·런타임 이미지)에서 실행해야 한다.
