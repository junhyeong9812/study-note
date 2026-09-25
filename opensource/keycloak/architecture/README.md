# Keycloak 아키텍처 지도

소스를 **직접 읽어서** 그리는 탑다운 지도다. 아직 흐름 문서가 없는 골격 상태다.

기준 태그: `26.6.2` [`0a402f777f`](https://github.com/keycloak/keycloak/tree/0a402f777f8985eccbb07556e96d9b386275e048) (2026-05-19). 모든 줄 번호는 이 태그 기준으로 쓴다.

이름에서 거꾸로 찾고 싶으면 [API 역인덱스](api-index.md)를 보면 된다. 상위: [Keycloak](../README.md)

## 흐름 후보

아래는 공식 가이드와 로드맵에서 뽑은 **후보**다. 소스를 읽고 진입점을 확인한 흐름만 `flows/` 아래 폴더로 만들고, 진입점 칸에 파일과 줄 번호를 적는다.

| 흐름 | 상태 | 진입점 |
|---|---|---|
| 서버 기동 (Quarkus build -> start) | 후보 | - |
| 인가 요청 (authorization endpoint) | 후보 | - |
| 로그인과 인증 플로우 실행 (authentication flow) | 후보 | - |
| 토큰 발급 (token endpoint, 코드 교환) | 후보 | - |
| 토큰 서명과 키 관리 | 후보 | - |
| 토큰 갱신과 세션 (user/client session) | 후보 | - |
| SPI 로딩 (Provider/ProviderFactory) | 후보 | - |
| 렐름 임포트 | 후보 | - |

## 구조

`structure/`(무엇이 있는가)와 `flows/`(무엇이 일어나는가)는 첫 문서를 쓸 때 만든다. 형식은 [Elasticsearch 아키텍처 지도](../../elasticsearch/architecture/README.md)를 따른다.
