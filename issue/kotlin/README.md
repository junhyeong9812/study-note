# kotlin — Kotlin/JVM·Spring 이슈 패턴

backend(Kotlin + Spring Boot)에서 뿌리내린 이슈. 언어(JVM 기본값)와 프레임워크(Spring·Jackson) 층을 나눈다.

| 하위 | 무엇 | 패턴 |
|------|------|------|
| (언어레벨) [charset-and-length-defaults](charset-and-length-defaults/) | JVM/프레임워크의 "사람용 기본값"이 바이트를 왜곡 — ISO-8859-1 인코딩·`String.length`(문자 vs 바이트) | be2 |
| [spring/](spring/) | Spring·Jackson·아키텍처 | 직렬화 누출 · DIP 포트소유 · 경로 트래버설+데이터 실태 · graceful degradation |
