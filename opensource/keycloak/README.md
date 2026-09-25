# Keycloak - 동작 구조 분석

이 폴더는 Keycloak(Java, Quarkus 기반)의 동작 구조를 소스 기준으로 정리하는 자리다. OIDC/OAuth2 인가 서버가 로그인을 받아 토큰을 발급하고 세션을 관리하는 쪽을 맡는다. [spring-security의 resource-server 지도](../spring-security/architecture/oauth2-resource-server)가 토큰을 **받아서 검증하는** 쪽이라면, 이 폴더는 토큰을 **만들어 내주는** 쪽이다.

전체 도구 목록과 진행 순서는 [도구 동작 구조 분석 로드맵](../../docs/tool-analysis-roadmap.md)에 있다.

## 읽는 기준

공식 가이드는 이미 한국어로 완역해 두었으므로 그것을 지도로 쓰고, 주장은 소스로 확인한다.

- 소스: [keycloak/keycloak](https://github.com/keycloak/keycloak) 태그 `26.6.2` ([`0a402f777f`](https://github.com/keycloak/keycloak/tree/0a402f777f8985eccbb07556e96d9b386275e048), 2026-05-19). 로컬 클론 `~/project/keycloak`
- 공식 가이드 한국어 완역: [junhyeong9812/keycloak-analyze](https://github.com/junhyeong9812/keycloak-analyze) (같은 26.6.2 기준, 78편). 로컬 `~/project/keycloak-analyze`
- 번역과 소스가 같은 버전이라 가이드의 설명을 해당 코드 위치로 곧바로 대조할 수 있다

## 개념 교차표에서 맡는 칸

로드맵의 개념 교차표 가운데 이 도구가 채우는 축이다.

- 인증·인가: OIDC 인가 코드 플로우, 토큰 발급과 서명
- 확장 구조: SPI(Provider/ProviderFactory)로 저장소·인증기를 끼워 넣는 방식
- 분산 상태: 세션과 캐시(Infinispan)
