# architecture 인덱스

Spring Security의 동작을 호출 흐름 단위로 위에서 아래로 따라가는 지도다. 흐름 하나가 폴더 하나이고, 그 안에서는 폴더 하나가 메서드 하나다. 각 README는 위치, 실제 코드, 그 코드의 아스키 워크플로우, 결과가 쓰이는 곳 순서로 되어 있고, 설명 안의 메서드 이름을 누르면 그 메서드 폴더로 들어간다.

기준 커밋: spring-security `main` [`26b6b2a84f`](https://github.com/spring-projects/spring-security/tree/26b6b2a84fa8fa26991ca0f57282720b48db9f91) (2026-09-18). 모든 줄 번호는 이 커밋 기준이다.

| 흐름 | 진입점 | 내용 |
|------|--------|------|
| [filter-chain](filter-chain/README.md) | `FilterChainProxy.doFilter` | 서블릿 필터 하나가 체인을 골라 보안 필터들을 태우기까지. 이 지도의 척추다. 메서드 폴더 4개와 SPI 4종 |
| [security-context](security-context/README.md) | `SecurityContextHolderFilter.doFilter` | "지금 누가 요청했는가"가 ThreadLocal에 얹히고 지워지기까지. 읽기와 쓰기가 갈라진 구조. 메서드 폴더 3개와 SPI 3종 |
| [form-login](form-login/README.md) | `AbstractAuthenticationProcessingFilter.doFilter` | POST /login이 사용자 조회와 비밀번호 대조를 거쳐 인증이 되기까지. 책임이 네 겹으로 나뉜다. 메서드 폴더 7개와 SPI 4종 |
| [authorization](authorization/README.md) | `AuthorizationFilter.doFilter` | 설정이 자료구조가 되고 첫 매칭 규칙이 통과 여부를 정하기까지. 메서드 폴더 4개와 SPI 3종 |
| [exception-translation](exception-translation/README.md) | `ExceptionTranslationFilter.doFilter` | 같은 접근 거부가 신뢰 수준에 따라 로그인 요구와 403으로 갈리는 자리. 메서드 폴더 3개와 SPI 3종 |
| [csrf](csrf/README.md) | `CsrfFilter.doFilterInternal` | 토큰이 두 값으로 존재하고 매번 다르게 나가는 방어. 메서드 폴더 3개와 SPI 3종 |
| [logout](logout/README.md) | `LogoutFilter.doFilter` | 핸들러들이 줄지어 세션과 컨텍스트를 정리하기까지. 인증을 만드는 흐름의 반대편. 메서드 폴더 3개와 SPI 2종 |
| [config-dsl](config-dsl/README.md) | `HttpSecurity.build` (빌드 시점) | DSL 한 줄이 설정자가 되고, init/configure/performBuild를 거쳐 체인 하나로 조립되기까지. 메서드 폴더 4개와 SPI 2종 |
| [filter-registration](filter-registration/README.md) | `WebSecurityConfiguration.springSecurityFilterChain` (빌드 시점) | 체인들이 FilterChainProxy로 묶여 서블릿 컨테이너에 등록되기까지. 메서드 폴더 3개와 SPI 2종 |
| [method-security](method-security/README.md) | `AuthorizationManagerBeforeMethodInterceptor.invoke` | @PreAuthorize가 AOP 프록시를 통해 평가되기까지. 웹 인가와 같은 계약을 메서드 호출에 적용한다. 메서드 폴더 4개와 SPI 2종 |
| [reactive-filter-chain](reactive-filter-chain/README.md) | `WebFilterChainProxy.filter` | 필터 체인의 WebFlux 판. 설계를 거의 그대로 옮겼다. 메서드 폴더 2개와 SPI 3종 |
| [reactive-context](reactive-context/README.md) | `ReactorContextWebFilter.filter` | 보안 컨텍스트의 WebFlux 판. ThreadLocal을 못 써 구조가 정말 다르다. 메서드 폴더 3개와 SPI 1종 |
| [oauth2-resource-server](oauth2-resource-server/README.md) | `BearerTokenAuthenticationFilter.doFilterInternal` | Bearer JWT가 서명·클레임 검증을 거쳐 인증이 되기까지. 사용자를 조회하지 않는다. 메서드 폴더 3개와 SPI 2종 |
| [oauth2-login](oauth2-login/README.md) | `OAuth2AuthorizationRequestRedirectFilter` / `OAuth2LoginAuthenticationFilter` | "구글로 로그인"이 리다이렉트와 콜백 두 번의 요청으로 처리되기까지. 메서드 폴더 2개와 SPI 2종 |

읽는 순서는 위에서 아래다. 필터 체인이 척추이고 나머지 서블릿 흐름은 그 위의 칸 하나씩이다. 보안 컨텍스트가 인증과 인가를 잇고, 폼 로그인이 그것을 채우면 인가가 그것을 읽는다. 예외 변환은 인가가 던진 거부를 응답으로 바꾸므로 인가 다음에 읽는다. CSRF와 로그아웃은 체인의 다른 칸이라 독립적으로 읽어도 된다.

설정 DSL과 필터 등록은 런타임 경로가 아니라 **기동 시점의 조립 과정**이라 뒤에 두었다. 앞의 일곱 흐름에서 본 필터들이 어디서 어떤 순서로 목록에 들어갔는지가 여기서 드러나므로, 서블릿 흐름을 먼저 읽고 오면 훨씬 잘 붙는다.

메서드 보안은 필터가 아니라 AOP 프록시를 쓰므로 Spring Framework의 [AOP 프록시](../../spring-framework/architecture/aop-proxy/README.md) 흐름과 함께 읽으면 좋다. 리액티브 두 흐름은 각각 서블릿 판과 나란히 놓고 보도록 썼다 — 필터 체인 쪽은 이름까지 대응하지만, 컨텍스트 쪽은 `ThreadLocal`을 쓸 수 없어 구조 자체가 다르다. OAuth2 둘은 폼 로그인과 같은 매니저 위에 다른 프로바이더를 끼운 갈래다.

지금까지 14개 흐름, 112개 문서를 그렸다. 다루지 않은 갈래는 각 흐름의 "다루지 않는 것" 절에 적어 두었다. 큰 것으로는 세션 관리와 동시 세션 제어, remember-me, CORS와 보안 헤더, WebAuthn/패스키, SAML2, ACL, 메시징·RSocket 보안, 불투명 토큰 introspection이 남아 있다.
