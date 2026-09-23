# cross-cutting — 언어 무관 시스템·네트워크 패턴

특정 언어/프레임워크가 아니라 **시스템 계층·네트워크·운영**에서 반복되는 이슈 패턴.
"프레임워크 코드가 시스템 계층의 기본값·경계에 부딪혀 터진" 교차 이슈가 여기 모인다.
계층별로 나눴고, 각 카드는 이번 배포에서 겪은 실제 이슈를 사례로 링크한다.

| 계층 | 무엇 | 패턴 |
|------|------|------|
| [reliability](reliability/) | 실패가 조용히 삼켜지는 것·자원 고갈 | silent-failure · resource-bounding |
| [network](network/) | 프로토콜·연결·프록시·서브넷 | chunked/Content-Length · 스트리밍 status · bind 주소 · 프록시 passthrough · 역터널 |
| [infra](infra/) | 플랫폼·툴(compose·git·nginx·배포) | compose 변수해석 · 상태 드리프트 · git 함정 · nginx 아군오사 |
| [security](security/) | 비밀·권한 | 시크릿 단일소유·최소권한 |

> 메타 태그(폴더를 가로지르는 주제): `silent-failure` · `resource-bounding` · `least-privilege`. 각 카드 본문에서 확인.
