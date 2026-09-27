# CS 기본기 주제 지도 — 리스트업 (2026-09-27, L0 리서치)

> 목적: study-note `cs/`에 추가할 CS 기본기 주제를 영역별로 리스트업. 네트워크는 신설.
> 방식: 기존 `cs/` 구조 조사 + 딥리서치 워커 3개(네트워크 / CS 전반 커리큘럼 / 소프트웨어 공학) 결과 종합.
> 상태: **후보 목록 — 착수(폴더 생성·문서 작성)는 주제별로 별도 결정.** `[?]` = 원문 미확인, 노트 작성 시 재확인.

## 0. 공통 설계 원칙 — "지식 + 어디서 무엇이 깨지면 어떻게 되나"

- 각 주제 노트 끝에 **「장애 시나리오」 절**: 현상 → 애플리케이션에서 보이는 형태(에러코드·증상) → 원인 → 대처.
  근거: TCP/IP Illustrated가 이상 상황을 프로토콜 설명 안(13·14·17장)에서 다룬다 — 별도 카테고리로 떼지 않는다.
- 영역마다 **역색인 1편**(증상 → 원인): 예) 네트워크 `ECONNRESET/EPIPE/ETIMEDOUT/...` 에러 사전.
- 영역마다 **실사건 1편**: OS=Mars Pathfinder priority inversion, 영속성=fsyncgate(2018), DB=write skew,
  분산=GitHub 2018-10-21 split-brain·Cloudflare 2017 윤초·metastable failure, 통계=SRM.
- 한국 면접 레포(gyoogle·JaeYeopHan·VSFe·WooVictory)는 장애 시나리오를 거의 다루지 않는다 → 이 노트의 차별점.

## 1. 현재 cs/ 보유 현황 (갭 판단 기준)

| 영역 | 보유 | 갭 |
|---|---|---|
| 자료구조·알고리즘 | algorithm 30·data-structure 35 | 계산 이론(오토마타·NP) 정도 |
| 하드웨어·데이터 표현 | foundations(게이트→ISA, 진수·IEEE754·유니코드) | 링킹·로딩, 예외적 제어흐름 |
| OS | 가상메모리·페이징·TLB, 프로세스/스레드·스케줄링·락 기초 | **동기화 심화·데드락·시스템콜·시그널·IPC·파일시스템·I/O 모델·fsync·컨테이너** |
| 네트워크 | 없음(resp-protocol만) | **전부** |
| DB | LSM·파티셔닝/샤딩·clickhouse·postgres-rls | **관계모델·SQL·인덱스·트랜잭션·격리수준·MVCC·WAL·복구·복제** |
| 분산 | 운영패턴 19(retry~CRDT)·논리시계·리더선출 | **장애 모델·일관성 모델·CAP/PACELC·quorum·2PC·합의(Raft)·물리시계** |
| 보안 | HMAC·SHA256·JWKS·OIDC | 암호 기초 체계·TLS/PKI·위협모델·시큐어코딩(인젝션)·접근제어 |
| 소프트웨어 공학 | SOLID·클린코드·GoF·애자일·DDD basic/advanced·아키텍처 스타일·개발표준 | **테스트 전반·모듈 설계 원리·리팩토링 스멜·DDD 전략설계·품질속성·전달(CI/CD)** |
| 데이터 분석·통계 | 없음 | **전부** |

## 2. 네트워크 (신설 — `cs/network/` 제안)

학습 순서 = 지도 → 아래 계층부터 → 종합. 각 항목 뒤 `⚠`는 그 노트의 장애 시나리오 절.

**N0. 지도 그리기**
- OSI 7계층 vs TCP/IP 4계층, 계층별 프로토콜·PDU(세그먼트/패킷/프레임) 매핑
- 캡슐화·디캡슐화 — 헤더가 붙고 벗겨지는 과정(각 계층 헤더 필드)
- 지연 4요소(처리·큐잉·전송·전파), 대역폭 vs 지연, BDP
- 근거: Kurose 1장, HPBN 1장

**N1. 링크 계층**
- Ethernet 프레임·MAC 주소, 허브 vs 스위치
- 스위치 자가학습·MAC 테이블·플러딩, VLAN(개관)
- ARP ⚠ ARP 캐시 stale, gratuitous ARP·IP 충돌
- MTU 개념

**N2. 네트워크 계층**
- IPv4/IPv6 주소, 서브넷·CIDR, 사설 IP
- 라우터 동작: 라우팅 테이블·최장 접두사 매칭·기본 게이트웨이·TTL
- 라우팅 프로토콜 개관(정적/OSPF/BGP) — 선택
- ICMP(ping·traceroute), DHCP
- IP 단편화·PMTUD ⚠ PMTUD 블랙홀(작은 요청은 되고 큰 응답·TLS 인증서 전송에서 hang — VPN/터널)
- NAT ⚠ NAT/LB idle timeout으로 조용히 끊김(예: AWS NAT GW 350s → 재사용 시 RST)

**N3. 전송 계층 — UDP**
- 헤더·무연결·다중화/역다중화(포트), 사용처(DNS·QUIC·스트리밍)

**N4. 전송 계층 — TCP (장애 노트의 중심)**
- 4.1 연결 수립: 3-way handshake, SYN 큐·accept 큐(listen backlog)
  ⚠ 포트 닫힘=RST=`ECONNREFUSED` / 방화벽 drop=SYN 재전송 후 `ETIMEDOUT` / accept 큐 가득=서버 로그 없이 connect 지연·SYN flood
- 4.2 신뢰성: 시퀀스·ACK·RTO·fast retransmit·SACK
  ⚠ 상대가 사라져도 write는 성공(커널 버퍼) → 한참 뒤 `ETIMEDOUT` → `TCP_USER_TIMEOUT` / 손실·재정렬 = 에러 없는 꼬리지연
- 4.3 흐름 제어: 수신 윈도우·zero window
- 4.4 혼잡 제어: slow start·AIMD·CUBIC·BBR 개관
- 4.5 연결 종료: 4-way handshake·상태 다이어그램, FIN vs RST
  ⚠ **"TCP 통신 도중 끊기면?"** 의 본체:
  - FIN(정상) → read가 0(EOF) / RST(강제) → `ECONNRESET`
  - 닫힌 소켓에 write → `EPIPE`·SIGPIPE(프로세스 종료 가능)
  - half-open(상대 재부팅·케이블 단절) → 보낼 게 없으면 영원히 살아 보임, read 무한대기
  - TIME_WAIT 누적 → 임시 포트 고갈 `EADDRNOTAVAIL` / CLOSE_WAIT 누적 → 앱의 close 누락 → fd 고갈 `EMFILE`
- 4.6 keepalive — 기본 7200s가 NAT/LB timeout보다 길어 무용한 경우
- 4.7 Nagle × delayed ACK — 요청당 ~40ms 고정 지연, `TCP_NODELAY`
- 4.8 **에러 코드 사전(역색인)**: ECONNRESET·EPIPE·ETIMEDOUT·ECONNREFUSED·EADDRNOTAVAIL·EMFILE

**N5. 소켓과 커널 경로 — "프로세스가 NIC로 나가는 길"**
- 소켓 syscall 흐름(socket/bind/listen/accept/connect/send/recv/close), 송수신 버퍼, fd
- 송신: 소켓 → TCP/IP 스택 → qdisc → 드라이버 → NIC(DMA)
- 수신: NIC → DMA → IRQ → NAPI/softirq → IP → TCP → 소켓 버퍼 → 프로세스
- 블로킹/논블로킹·동기/비동기·I/O 멀티플렉싱(select/poll/epoll) — OS 영역과 공유
- **패킷의 여정 종합편**: 프로세스 → 소켓 → 커널 → NIC → 스위치(MAC) → 라우터(IP) → … → 수신측 역방향 디캡슐화
- 근거: packagecloud 커널 네트워크 스택 2부작, Beej, 『성공과 실패를 결정하는 1%의 네트워크 원리』

**N6. DNS**
- 재귀·반복 질의, 루트/TLD/권한 서버, 레코드(A/AAAA/CNAME/MX/NS/TXT), TTL·캐시 계층
- ⚠ 캐시 stale(페일오버 후 죽은 IP로 접속 — JVM DNS 캐시), 부정 캐시(NXDOMAIN)

**N7. 암호 기초 → TLS/HTTPS 인증서**
- 대칭키·공개키·해시·MAC·전자서명·키 교환(ECDHE)·전방 비밀성 (기존 foundations/security와 연결)
- TLS 1.3 핸드셰이크(1-RTT·0-RTT), TLS 1.2와 차이, SNI, ALPN
- X.509 인증서 구조, 체인 검증(리프→중간→루트, RFC 5280), 루트 스토어
- 폐기 확인: CRL·OCSP·OCSP stapling / Certificate Transparency
- 최근 변화: Let's Encrypt OCSP 종료(2025-08) · CA/B SC-081 인증서 수명 단축(2026-03 200일 → 2029 47일)
- ⚠ 만료·중간 인증서 체인 누락("브라우저는 되는데 서버 간 호출만 실패")·SNI/호스트명 불일치·clock skew·OCSP 응답기 장애 — badssl.com으로 재현

**N8. HTTP**
- HTTP 의미론(메서드·상태코드·헤더·멱등성), 쿠키·세션, 캐싱(RFC 9111)
- HTTP/1.1 keep-alive·파이프라이닝 한계 → HTTP/2 다중화(TCP HoL) → HTTP/3·QUIC(스트림 독립·연결 마이그레이션)
- WebSocket·SSE
- ⚠ 커넥션 풀 stale 연결(서버 idle close와 재사용 경합 → "socket hang up"·502), 프록시/LB timeout 불일치

**N9. 종합·인프라**
- "URL 입력 후 일어나는 일" 전 구간
- 로드밸런서 L4 vs L7, 리버스 프록시, 방화벽, CDN
- 진단 도구: `ss`·`tcpdump`/Wireshark·`curl -v`·`openssl s_client`·`dig`·`mtr`·`ip route`

근거 교재: Kurose&Ross 9판(2025) · Tanenbaum 6판 · Stevens TCP/IP Illustrated Vol.1 2판 · HPBN(hpbn.co) · Beej · RFC 9293(TCP)·8446(TLS1.3)·5280(X.509)·9110~9114(HTTP)·9000(QUIC)
장애 근거: Cloudflare 블로그(SYN 처리·"When TCP sockets refuse to die"·CLOSE_WAIT·IP fragmentation), Bernat(TIME_WAIT), AWS NAT GW 문서
`[?]` Linux 기본값 수치(tcp_retries2≈15분, SYN 재시도≈2분)·RFC 5382 NAT timeout은 kernel ip-sysctl·RFC 원문 재확인.

## 3. 운영체제 심화 (`cs/os/` 신설 또는 foundations 확장)

- 커널/유저 모드·시스템콜·인터럽트·트랩 ⚠ 시스템콜 비용·컨텍스트 스위치 폭증
- 예외적 제어흐름·시그널(CS:APP 8장) ⚠ SIGPIPE, 좀비·고아 프로세스
- 동기화 심화: 뮤텍스·세마포어·조건변수·모니터·스핀락·원자연산·메모리 배리어
- 동시성 버그: 경쟁 조건·원자성 위반·순서 위반 ⚠ 데드락 4조건(예방·회피·탐지)·기아·**priority inversion(Mars Pathfinder)**·라이브락
- IPC: 파이프·공유메모리·메시지 큐·소켓
- 페이지 교체(LRU·Clock)·스래싱(기존 systems/thrashing 연결)·OOM killer
- 파일시스템: inode·파일 디스크립터·디렉터리·VFS·저널링·FFS/LFS·SSD ⚠ crash consistency·torn write
- 영속성과 fsync ⚠ **fsyncgate** — fsync EIO 후 재시도 성공 위장으로 조용한 유실
- I/O 모델: 블로킹/논블로킹·동기/비동기·select/poll/epoll·io_uring·mmap·zero-copy
- 링킹·로딩(정적/동적 라이브러리)
- 가상화·컨테이너: 하이퍼바이저·namespace·cgroup
- 근거: OSTEP(가상화·동시성·영속성 3파트) · CS:APP 7~12장 · VSFe OS 문서

## 4. 데이터베이스 이론 (`cs/database/` 신설)

- 관계 모델·관계 대수·키·정규화(1~BCNF) ⚠ 삽입/갱신/삭제 이상
- SQL: 조인·집계·서브쿼리·윈도 함수
- 스토리지: 페이지·슬롯·버퍼 풀 / 인덱스: B+Tree·해시·커버링·복합 인덱스(기존 LSM과 대비) ⚠ 인덱스 안 타는 쿼리·N+1
- 쿼리 처리: 조인 알고리즘(NL/해시/머지)·옵티마이저·실행계획 읽기
- 트랜잭션·ACID, 격리수준 ⚠ dirty read·non-repeatable·phantom·**lost update·write skew(SI가 허용)**
- 동시성 제어: 2PL·데드락·MVCC·OCC
- 로깅·복구: WAL·체크포인트·ARIES
- 복제: 리더-팔로워·동기/비동기·복제 지연 ⚠ read-your-writes 위반
- 근거: CMU 15-445 · DDIA 3·5·7장 · Berenson 외 1995(격리수준 비판)

## 5. 분산 시스템 이론 (`systems/` 확장 또는 `cs/distributed/`)

- 시스템 모델: 네트워크 장애·부분 실패·장애 모델(crash/비잔틴)·FLP `[?]`
- 시간: 물리 시계·NTP·clock skew ⚠ Cloudflare 2017 윤초(음수 시간차 panic) / 논리 시계(기존 ops 14 연결)
- 일관성 모델: 선형화·순차·인과·최종 일관성
- CAP·PACELC
- 복제·quorum(R+W>N)
- 분산 트랜잭션: 2PC ⚠ 코디네이터 장애 블로킹 (기존 saga·outbox와 대비)
- 합의: Paxos·Raft ⚠ **split-brain(GitHub 2018-10-21)**
- 캐시 일관성(Memcache@FB), BFT 개관
- ⚠ metastable failure·재시도 폭풍(기존 ops 01·09 연결)
- 근거: DDIA 8·9장 · MIT 6.5840

## 6. 보안 기초 (foundations/security 확장)

- 암호 체계 정리(대칭/비대칭/해시/MAC/서명/KDF) — 기존 HMAC·SHA256 흡수
- TLS/PKI → 네트워크 N7과 공유(한쪽에만 본문, 다른 쪽은 링크)
- 인증 vs 인가, 세션·토큰(기존 JWKS·OIDC 연결), 접근제어(RBAC/ABAC)
- 웹 보안: SOP·CORS·XSS·CSRF·SQL 인젝션·SSRF (OWASP Top 10)
- 위협 모델링(STRIDE), 시큐어 코딩·메모리 안전성

## 7. 시스템 성능·신뢰성 공통 (소형)

- 지연 숫자(Latency numbers)·지역성·AMAT·꼬리 지연(p99)
- 측정·벤치마크 방법론 ⚠ 평균의 함정·coordinated omission `[?]`
- fault·error·failure 구분, 가용성 계산(9의 개수)·MTBF/MTTR, ECC·CRC·RAID·체크섬

## 8. 소프트웨어 공학 (engineering·domain-modeling 확장)

**설계 원리**
- 모듈 설계: 정보 은닉·결합도/응집도·Ousterhout 깊은 모듈·복잡도 3증상(변경 증폭·인지 부하·unknown unknowns)
- 리팩토링: Fowler 2판 스멜 24개 + 카탈로그 (기존 clean-code와 겹침 확인)
- 컴포넌트 원칙(REP/CCP/CRP·ADP/SDP/SAP) + 헥사고날·어니언·클린 비교 (기존 architecture-styles 확인)
- ⚠ Shotgun Surgery·Speculative Generality·과설계

**DDD 전략 설계 (기존 basic/advanced 보강)**
- 바운디드 컨텍스트·유비쿼터스 언어·서브도메인(Core/Supporting/Generic)
- 컨텍스트 맵 패턴(Partnership·Shared Kernel·Customer/Supplier·Conformist·ACL·OHS·Published Language·Separate Ways·Big Ball of Mud)
- Vernon Aggregate 4규칙 / Supple Design 8패턴 / Event Storming
- ⚠ 빈약한 도메인 모델·거대 Aggregate·ACL 부재로 모델 오염·공유 DB·분산 모놀리스

**테스트 (갭 최대)**
- 테스트 피라미드 ⚠ 아이스크림 콘
- 테스트 더블 5종(Dummy/Fake/Stub/Spy/Mock), 고전파 vs 런던파, 좋은 테스트 4기둥(Khorikov)
- TDD(Canon TDD) ⚠ 기대값에 계산값 붙여넣기
- 계약 테스트(Pact)·속성 기반 테스트·뮤테이션 테스트 ⚠ 커버리지 맹신·과도한 mock

**품질·요구사항·전달**
- 품질 속성 ISO 25010:2023(9특성), 기술부채 4사분면, 요구사항 공학(29148)
- 브랜칭 전략(git-flow vs trunk-based)·CI/CD·DORA 5지표·코드 리뷰 기준(Google eng-practices)
- 관측성(OTel: 트레이스·메트릭·로그), 12-factor
- API 설계 원칙 일반론: REST 성숙도·멱등성(Idempotency-Key)·버저닝·하위호환 (기존 api-design 사례 6개의 이론편)

뼈대: SWEBOK v4 18 KA(Architecture·Operations·Security 신설) — `cs/` 전체 지도 페이지로.

## 9. 데이터 분석·통계 (`cs/data-analysis/` 신설)

- 데이터 종류·표본추출·편향 ⚠ 표본 편향·생존자 편향
- 기술통계(중심경향·산포·분위수)·EDA
- 확률·분포(정규·이항·포아송)·중심극한정리
- 추정·신뢰구간, 가설검정(p-value·검정력) ⚠ 다중비교·p-hacking·peeking
- 상관 vs 인과 ⚠ Simpson's paradox
- 회귀(선형·로지스틱)
- A/B 실험설계 ⚠ SRM(Sample Ratio Mismatch)·가드레일 지표
- SQL 분석(윈도 함수·코호트·퍼널), 시계열 기초
- 시각화 원칙 ⚠ 비례 잉크 위반·잘린 축·3D
- 근거: OpenIntro Statistics 4판 · Think Stats 2e · Kohavi『Trustworthy Online Controlled Experiments』· Wilke『Fundamentals of Data Visualization』

## 10. 후순위 (필요 시)

- CS 수학: 이산수학·확률·선형대수 (MIT 6.042)
- 계산 이론: 오토마타·형식언어·NP-완전
- PL 이론: 타입 시스템·함수형·메모리 모델·GC

## 11. 권장 착수 순서

저장된 우선순위(기본기 → 도메인 → api/ops)와 이번 요청(네트워크 우선)을 합친 안.

1. **네트워크 N0~N4** — 요청의 본체. N4.5 "TCP 도중 끊기면"까지.
2. **네트워크 N5·OS I/O 모델** — 소켓·커널 경로는 OS와 맞물려 함께.
3. **네트워크 N6~N9 + 보안 암호 기초** — TLS/인증서.
4. **OS 심화** — 동기화·데드락·시스템콜·파일시스템·fsync.
5. **DB 이론** — 트랜잭션·격리수준 중심.
6. **분산 이론** — 기존 ops-patterns의 이론적 근거.
7. **소프트웨어 공학 갭** — 모듈 설계 → 테스트 → DDD 전략.
8. **데이터 분석·통계** — 독립 트랙, 병행 가능.
9. 후순위.

## 출처 (주요)

- CS2023: https://csed.acm.org/knowledge-areas/ · teachyourselfcs: https://teachyourselfcs.com/ · OSSU: https://github.com/ossu/computer-science
- OSTEP: https://pages.cs.wisc.edu/~remzi/OSTEP/ · CMU 15-445: https://15445.courses.cs.cmu.edu/fall2024/schedule.html · DDIA: https://dataintensive.net/ · MIT 6.5840: https://pdos.csail.mit.edu/6.824/schedule.html · CS:APP: https://csapp.cs.cmu.edu/
- Kurose&Ross: https://gaia.cs.umass.edu/kurose_ross/ · HPBN: https://hpbn.co/ · Beej: https://beej.us/guide/bgnet/ · RFC 9293: https://www.rfc-editor.org/rfc/rfc9293.html
- 커널 네트워크 스택: https://blog.packagecloud.io/monitoring-tuning-linux-networking-stack-receiving-data/ · what-happens-when: https://github.com/alex/what-happens-when
- Cloudflare: https://blog.cloudflare.com/when-tcp-sockets-refuse-to-die/ · https://blog.cloudflare.com/syn-packet-handling-in-the-wild/ · https://blog.cloudflare.com/this-is-strictly-a-violation-of-the-tcp-specification/ · https://blog.cloudflare.com/ip-fragmentation-is-broken/
- TIME_WAIT: https://vincent.bernat.ch/en/blog/2014-tcp-time-wait-state-linux · AWS NAT: https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateway-troubleshooting.html
- Let's Encrypt OCSP 종료: https://letsencrypt.org/2024/12/05/ending-ocsp · SC-081: https://cabforum.org/2025/04/11/ballot-sc081v3-introduce-schedule-of-reducing-validity-and-data-reuse-periods/ · badssl: https://badssl.com/
- fsyncgate: https://lwn.net/Articles/752063/ · Pathfinder: https://www.cs.unc.edu/~anderson/teach/comp790/papers/mars_pathfinder_long_version.html · GitHub 2018: https://github.blog/news-insights/company-news/oct21-post-incident-analysis/ · 윤초: https://blog.cloudflare.com/how-and-why-the-leap-second-affected-cloudflare-dns/ · metastable: https://sigops.org/s/conferences/hotos/2021/papers/hotos21-s11-bronson.pdf
- SWEBOK: https://www.computer.org/education/bodies-of-knowledge/software-engineering · DDD Reference: https://www.domainlanguage.com/wp-content/uploads/2016/05/DDD_Reference_2015-03.pdf · Canon TDD: https://newsletter.kentbeck.com/p/canon-tdd · Mocks aren't stubs: https://martinfowler.com/articles/mocksArentStubs.html · SWE at Google 13장: https://abseil.io/resources/swe-book/html/ch13.html · DORA: https://dora.dev/guides/dora-metrics/
- 면접 레포: https://github.com/gyoogle/tech-interview-for-developer · https://github.com/JaeYeopHan/Interview_Question_for_Beginner · https://github.com/VSFe/Tech-Interview
- 통계: https://www.openintro.org/book/os/ · https://greenteapress.com/thinkstats2/ · https://clauswilke.com/dataviz/
