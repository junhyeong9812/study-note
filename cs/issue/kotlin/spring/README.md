# kotlin/spring — Spring·Jackson·아키텍처 패턴

| 패턴 | 한 줄 | 사례 이슈 |
|------|-------|-----------|
| [serialization-contract-leak](serialization-contract-leak/) | data class를 Jackson 자동 직렬화에 맡기면 내부 필드명(camelCase)이 외부 API 계약으로 누출 → snake_case 명시 | be7 |
| [dip-port-ownership](dip-port-ownership/) | 전역 레이어가 응집을 해침 → 도메인우선 재편·DIP(usecase가 포트 소유·infra가 구현)·특성테스트 안전망 | be8 |
| [path-traversal-and-data-reality](path-traversal-and-data-reality/) | 원문 서빙의 경로 트래버설 차단 + "버그처럼 보이는 것의 절반은 데이터 실태"(0바이트 원본) | be3 |
| [graceful-degradation-fault-isolation](graceful-degradation-fault-isolation/) | 보조기능(rewrite·임베딩) 장애가 핵심(검색)을 인질·오염 못하게 — fault isolation·RRF·폴백 뱃지 | be4 |
