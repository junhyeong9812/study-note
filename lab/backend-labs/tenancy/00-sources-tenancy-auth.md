# 근거자료 목록 (Lab 10 ~ 17: Multi-tenancy & AuthN/AuthZ)

신뢰도 표시: **A** 공식 문서·표준·논문 / **B** 기업 기술블로그·컨퍼런스 / **C** 개인 블로그·포럼 (가설로만 사용)

## 10. Tenant Isolation Lab

| 신뢰도 | 자료 | 핵심 내용 |
|-------|------|---------|
| A | [AWS Guidance for Multi-Tenant Architectures](https://docs.aws.amazon.com/solutions/multi-tenant-architectures-on-aws/) | Silo(DB) · Bridge(스키마) · Pool(RLS) 정의와 비용·격리 트레이드오프 |
| A | [AWS SaaS Tenant Isolation Strategies 백서](https://docs.aws.amazon.com/pdfs/whitepapers/latest/saas-tenant-isolation-strategies/saas-tenant-isolation-strategies.pdf) | Silo의 장점(노이지 네이버 없음, 비용 추적 용이) |
| A | [AWS Bridge Model](https://docs.aws.amazon.com/whitepapers/latest/saas-tenant-isolation-strategies/the-bridge-model.html) | 계층별로 Silo·Pool을 섞는 하이브리드 |
| C | [RLS 벤치마크 (pgbench, 100만 행)](https://dev.to/sameer_hassan/multi-tenant-database-architecture-row-level-security-rls-postgresql-isolation-24oe) | 복합 인덱스 시 처리량 차이 2% 미만 |
| C | [RLS in Go 벤치마크](https://dev.to/__8fa66572/postgresql-rls-in-go-architecting-secure-multi-tenancy-4ifm) | 집계 약 2.4배, ILIKE 약 6배 느려짐 |
| C | [RLS Without the Performance Tax](https://dev.to/software_mvp-factory/postgresql-row-level-security-without-the-performance-tax-436g) | 정책 작성에 따라 인덱스 스캔이 순차 스캔으로 바뀌는 문제 |

## 11. Noisy Neighbor Lab

| 신뢰도 | 자료 | 핵심 내용 |
|-------|------|---------|
| A | [Azure Noisy Neighbor Antipattern](https://learn.microsoft.com/en-us/azure/architecture/antipatterns/noisy-neighbor) | 문제 정의, 합산 피크 문제 |
| A | [Azure Noisy Neighbor (완화책)](https://learn.microsoft.com/en-gb/azure/architecture/antipatterns/noisy-neighbor/noisy-neighbor) | 쿼터·스로틀링, 샤드·스탬프, 예약 용량 |
| B | [Shopify: A Pods Architecture](https://shopify.engineering/a-pods-architecture-to-allow-shopify-to-scale) | shop_id 기반 완전 격리 pod |
| B | [InfoQ: How Shopify Powers Online Commerce](https://www.infoq.com/news/2017/10/shopify-commerce) | 체크아웃 스로틀로 같은 샤드 보호 |
| B | [Shopify: MySQL Shard Balancing](https://shopify.engineering/mysql-database-shard-balancing-terabyte-scale) | 무중단 상점 샤드 이전 |
| A | [Okta Rate Limits (토큰별 50%)](https://developer.okta.com/docs/reference/rl-global-other-endpoints/) | 토큰 하나가 한도 전체를 독점하지 못하게 제한 |

## 12. Tenant Provisioning & Migration Lab

| 신뢰도 | 자료 | 핵심 내용 |
|-------|------|---------|
| B | [Citus: Lessons learned from Postgres schema sharding](https://www.citusdata.com/blog/2016/12/18/schema-sharding-lessons/) | 수천 테넌트에서 DDL이 수 시간으로 증가 |
| A | [Ecto: Multi tenancy with query prefixes](https://hexdocs.pm/ecto/multi-tenancy-with-query-prefixes.md) | 수만 테넌트 마이그레이션 비용 경고 |
| C | [Schema-per-tenant migrations in Go](https://dev.to/yusufihsangorgel/schema-per-tenant-migrations-in-go-why-the-ledger-lives-inside-each-schema-12n7) | 스키마별 버전 원장 + 스키마별 락 |
| C | [PostgreSQL Multitenancy Without RLS](https://dev.to/software_mvp-factory/postgresql-multitenancy-without-row-level-security-526p) | 전략별 테넌트 수 한계 추정 |
| B | [Shopify: MySQL Shard Balancing](https://shopify.engineering/mysql-database-shard-balancing-terabyte-scale) | 테넌트 무중단 이전 |

## 13. Tenant-aware Cache & Search Lab

| 신뢰도 | 자료 | 핵심 내용 |
|-------|------|---------|
| B | [Elastic: Indexing Strategy in Multi-Tenant Applications](https://www.elastic.co/blog/found-multi-tenancy) | 샤드 고정 메모리, 전체 샤드 조회 문제, tenant 라우팅 |
| B | [ePages: Multitenancy and Elasticsearch](https://developer.epages.com/blog/tech-stories/multitenancy-and-elasticsearch) | 인덱스 폭증 계산 예시 |
| C | [Elastic 포럼: Custom routing above shard count](https://discuss.elastic.co/t/custom-routing-above-shard-count/34028) | 라우팅 충돌 시 필터 필수 |
| B | [BigData Boutique: Multi-tenancy with ES/OpenSearch](https://bigdataboutique.com/blog/multi-tenancy-with-elasticsearch-and-opensearch-c1047b) | 권장 샤드 크기 10~50GB |
| C | [Elastic 포럼: 하이브리드 인덱스](https://discuss.elastic.co/t/multy-tenany-elasticsearch/347832) | 대형 테넌트만 전용 인덱스로 분리 |

## 14. Token Lifecycle Lab

| 신뢰도 | 자료 | 핵심 내용 |
|-------|------|---------|
| A | [RFC 9700: OAuth 2.0 Security BCP](https://ftp.nic.ad.jp/rfc/rfc9700.pdf) | 리프레시 토큰 보호, 탈취 토큰 오용 방지 |
| B | [WorkOS: RFC 9700 요약](https://workos.com/blog/oauth-best-practices) | 토큰 재사용 방지, 권한 최소화 |
| A | [IETF Draft: OAuth Roadmap](https://www.ietf.org/ietf-ftp/internet-drafts/draft-chen-oauth-roadmap-01.html) | RFC 8705(mTLS), RFC 9449(DPoP), 리프레시 토큰 순환 |
| A | [IETF OAuth WG 메일링](https://mailarchive.ietf.org/arch/msg/oauth/M8pK9Z4VYKW5jNtMwqNPi_Ram9g/) | 순환의 운영 부담 논의 |
| C | [Gravitee: Refresh Token Rotation](https://gravitee.io/corpus/gen-1403/oauth/oauth-refresh-token-rotation-and-replay-detection-strategies.html) | 재사용 감지 시 계열 전체 폐기 |
| A | [Okta Rate Limits (사용자별)](https://developer.okta.com/docs/reference/rl2-limits) | 사용자별 토큰 요청 초당 4회 |

## 15. Authorization Model Lab

| 신뢰도 | 자료 | 핵심 내용 |
|-------|------|---------|
| A | [Zanzibar (USENIX ATC '19)](https://www.usenix.org/conference/atc19/presentation/pang) | 수조 ACL, 초당 수백만 요청, p95 10ms 미만 |
| A | [Zanzibar (Google Research)](https://research.google/pubs/pub48190/) | 외부 일관성 (인과 순서 보장) |
| A | [Zanzibar 발표 슬라이드](https://www.usenix.net/sites/default/files/conference/protected-files/atc19_slides_pang.pdf) | p99.9 100ms 미만, Check·Read·Write 피크 QPS |
| B | [Packt: Zanzibar 요약](https://hub.packtpub.com/google-researchers-present-zanzibar-a-global-authorization-system-it-scales-trillions-of-access-control-lists-and-millions-of-authorization-requests-per-second/amp/) | 검색 결과당 수십~수백 번 체크 |

## 16. Cross-tenant AuthZ Lab

| 신뢰도 | 자료 | 핵심 내용 |
|-------|------|---------|
| A | [OWASP API Security Project](https://owasp.org/projects/api-security-project) | 2023년 1위 BOLA |
| B | [Palo Alto: OWASP API Top 10 2023](https://www.paloaltonetworks.com/blog/cloud-security/demystifying-api-security) | 전체 목록과 BOLA 예시 |
| B | [SecureLayer7: 2019 → 2023 변화](https://securelayer7.net/learn/api-security/owasp-api-top-10) | 접근 제어가 인증보다 앞 순위로 |
| B | [Indusface: BOLA](https://www.indusface.com/learning/owasp-api-top-10-broken-object-level-authorization/) | 권한 결함 유형 |
| B | [Radware: OWASP API Top 10](https://www.radware.com/cyberpedia/application-security/owasp-api-security-top-10) | 속성 수준 권한 조작 예시 |

## 17. SSO & Service Auth Lab

| 신뢰도 | 자료 | 핵심 내용 |
|-------|------|---------|
| A | [Okta: Additional Rate Limits](https://developer.okta.com/docs/reference/rl2-limits) | 사용자별 인증 초당 4회, 사용자당 5초 20회 |
| A | [Okta: Client-based Rate Limits](https://developer.okta.com/docs/reference/rl2-client-based/) | 클라이언트별 분당 60회, 앱별 50% |
| A | [Okta: Concurrent Limits](https://developer.okta.com/docs/reference/rl-additional-limits) | 동시 트랜잭션 75개 |
| A | [Okta: Rate Limits Overview](https://developer.okta.com/docs/reference/rate-limits/) | 버킷 구조, 비정렬 60초 주기 |
| A | [IETF Draft: OAuth Roadmap](https://www.ietf.org/ietf-ftp/internet-drafts/draft-chen-oauth-roadmap-01.html) | RFC 8705 mTLS, RFC 9449 DPoP |

## 참고: 공개 자료가 없어 제안값으로 둔 항목

| Lab | 제안값 | 도출 방식 |
|-----|-------|---------|
| 10 | 테넌트 1,000개, 상위 1%가 데이터 50% | SaaS 일반적 편중 가정 |
| 11 | 테넌트당 20 RPS, 폭주 50배 | 실험 설계값 |
| 12 | 테넌트 1,000 / 5,000개 | 블로그의 전략별 한계 추정 구간을 걸치도록 설정 |
| 14 | 갱신 약 1,100 req/s | 세션 100만 ÷ TTL 900초 |
| 15 | 체크:변경 약 170:1 | Zanzibar Check 피크 ÷ Write 피크 |
| 17 | 로그인 약 170/s | 10만 명 ÷ 600초 |
