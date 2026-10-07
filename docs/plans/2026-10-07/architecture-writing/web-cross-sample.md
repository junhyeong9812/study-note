# 웹 독립 교차 표본 — 컴퓨터 구조 22편 (spec V5)

- 일시: 2026-10-07
- 대상: `cs/architecture/01`~`23`(17 없음) 22편의 `2-summary.md` — 사실 점검·판정·정합 뒤 현재 본문
- 방법: 편마다 URL·1차 출처가 붙은 주장 2~7개를 골라, 출처를 curl GET으로 직접 받아(HTML은 텍스트 추출, PDF는 `pdftotext`, OpenJDK 소스는 `raw.githubusercontent.com/openjdk/jdk21u`, Linux는 `torvalds/linux`) 원문 문장과 대조했다. 403이 난 곳(intel.com·stackoverflow.com·dev.mysql.com)은 Internet Archive 사본으로, Apple 문서(JS 렌더링)는 같은 문서의 공개 JSON(`developer.apple.com/tutorials/data/...json`)으로 읽었다. 요청에는 일반 UA 문자열만 썼다.
- 중복 회피: `docs/plans/2026-10-07/architecture-writing/log.md`는 사실 점검 웹 표본의 **건수**(12·12·12·13·12·9)와 지적 요지만 적고, 표본 목록은 남기지 않았다. 그래서 로그 요약에 나온 지적·정정 대상(Ariane '범위 검사'·FAA '동시에 켰다면'·cvttsd2si integer indefinite·Intel #AC·i386 cdecl 보존 레지스터·4바이트 정렬·AArch64 ThreadStackSize·binfmt 순서·Drepper 그림 6.11·평균 탐색 1/3·Nicely 발견 경위·Project Zero 변형 3·Spotify 서술·NUMA 기본 정책·blk-mq 큐 수 등)은 피하고, 같은 문서의 다른 문장을 골랐다.
- 결과: **90건 — 일치 90 · 불일치 0 · 확인 불가 0**. 관찰 2건(아래 '확인 불가·관찰 상세').
- 비고: 사실 점검 packet의 웹 표본 목록이 로그에 없어서, 이 표본 일부가 사실 점검 표본과 겹쳤을 수 있다(같은 문장인지 확인할 수 없음). 노트·로그는 읽기만 했고 저장소에 파일을 만들지 않았다.

| # | 노트 (:줄) | 주장 | 출처 | 원문 인용 | 판정 |
|---|---|---|---|---|---|
| 1 | 01 :81 | Java `int` 범위 −2,147,483,648~2,147,483,647 | JLS SE21 §4.2.1 | "int, from -2147483648 to 2147483647, inclusive" | 일치 |
| 2 | 01 :110 | C11은 부호 표현 세 가지를 모두 허용 | N1570 §6.2.6.2 | "(sign and magnitude) … (two's complement) … (ones' complement). Which of these applies is implementation-defined" | 일치 |
| 3 | 01 :111 | N2412: 넘침을 모듈로로 정의하는 것은 합의 못 함 | WG14 N2412 §1 | "Overflowing operations and out-of-range conversion are generally mapped to modulo operations … WG14 has not yet found consensus for these points" | 일치 |
| 4 | 01 :164 | gcc는 음수 `>>`를 부호 확장으로 정함 | GCC 매뉴얼 4.5 Integers | "Signed '>>' acts on negative numbers by sign extension." | 일치 |
| 5 | 02 :41 | 정수 연산자는 넘침을 알리지 않음 | JLS §4.2.2 | "The integer operators do not indicate overflow or underflow in any way." | 일치 |
| 6 | 02 :85 | 좁히기는 하위 n비트만 남기고 부호가 바뀔 수 있음 | JLS §5.1.3 | "simply discards all but the n lowest order bits … this may cause the sign of the resulting value to differ" | 일치 |
| 7 | 02 :88 | `E1 op= E2` = `E1 = (T)((E1) op (E2))`, E1은 한 번 평가 | JLS §15.26.2 | "is equivalent to E1 = (T) ((E1) op (E2)), where T is the type of E1, except that E1 is evaluated only once" | 일치 |
| 8 | 02 :115 | Python 정수는 임의 정밀도 | Python 문서 Built-in Types | "Integers have unlimited precision." | 일치 |
| 9 | 03 :42 | 바이어스 binary32 127, binary64 1023 | Goldberg 1991 | "uses a biased representation … the bias is 127 (for double precision it is 1023)" | 일치 |
| 10 | 03 :43 | 23비트 저장으로 24비트 정밀도(숨은 비트) | Goldberg 1991 | "it uses a hidden bit, so the significand is 24 bits (p = 24), even though it is encoded using only 23 bits" | 일치 |
| 11 | 03 :97 | 기본 반올림: 동률이면 끝 비트 0 쪽 = roundTiesToEven | JLS §15.4 | "if the two nearest representable values are equally near, then the value whose least significant bit is zero is chosen" / "corresponds to … roundTiesToEven" | 일치 |
| 12 | 03 :119 | `Math.min`·`max`는 −0.0을 +0.0보다 작게 봄 | JLS §15.20.1 | "the methods Math.min and Math.max treat negative zero as being strictly smaller than positive zero" | 일치 |
| 13 | 04 :92 | UTF-8에서 BOM은 순서 기능이 없고 `EF BB BF` | RFC 3629 §6 | "UTF-8 having a single-octet encoding unit, this last function is useless and the BOM will always appear as the octet sequence EF BB BF" | 일치 |
| 14 | 04 :109 | §10의 `2F C0 AE 2E 2F`, 2001년 웹 서버 공격 바이러스 | RFC 3629 §10 | "2F C0 AE 2E 2F. This last exploit has actually been used in a widespread virus attacking Web servers in 2001" | 일치 |
| 15 | 04 :239 | JDK 18부터 기본 UTF-8, COMPAT이면 JDK 17 이하 방식 | JEP 400 | Release 18 · "encoding=COMPAT), then the default charset will be the charset chosen by the algorithm in JDK 17 and earlier, based on the user's operating system, locale" | 일치 |
| 16 | 04 :242 | `utf8mb3`는 BMP만, 최대 3바이트, 폐기 예정 | MySQL 8.0 매뉴얼 12.9.2 (IA 사본) | "Supports BMP characters only … Requires a maximum of three bytes per multibyte character." "The utf8mb3 character set is deprecated." | 일치 |
| 17 | 05 :73 | UAX #29 rev. 49(Unicode 18.0)가 GB9c를 고침 | UAX #29 Modifications | "Revision 49 Reissued for Unicode 18.0.0. Rule GB9c: Change Rule GB9c …" | 일치 |
| 18 | 05 :73 | Java 21 문자 데이터는 Unicode 15.0 | Java 21 API `Character` | "Character information is based on the Unicode Standard, version 15.0." | 일치 |
| 19 | 05 :93 | PG `varchar(n)`은 n 글자, 넘는 부분이 공백뿐이면 잘림, 명시 캐스트도 잘림(SQL 표준) | PostgreSQL 17 §8.3 | "up to n characters (not bytes) … unless the excess characters are all spaces … if one explicitly casts … truncated to n characters … (This too is required by the SQL standard.)" | 일치 |
| 20 | 05 :155 | Highly Restrictive는 Latn+Kore 허용, Moderately도 라틴+키릴·그리스 불허 | UTS #39 rev.34 §5.2 | "Latin + Han + Hangul; or equivalently: Latn + Kore" / "Latin and any one other Recommended script, except Cyrillic, Greek" | 일치 |
| 21 | 05 :213 | PG 문자형은 NUL을 담지 못함 | PostgreSQL 17 §8.3 | "the character with code zero (sometimes called NUL) cannot be stored" | 일치 |
| 22 | 06 :46 | `man 3 byteorder` 인용문 | man7.org byteorder(3) | "On the i386 the host byte order is Least Significant Byte first, whereas the network byte order, as used on the Internet, is Most Significant Byte first." | 일치 |
| 23 | 06 :46 | 인터넷 헤더는 큰 자리부터 보냄 | RFC 791 부록 B | "When a multi-octet quantity is transmitted the most significant octet is transmitted first." | 일치 |
| 24 | 06 :251 | 구조체·멤버에 저장하면 패딩 바이트는 미지정 값 | N1570 §6.2.6.1 ¶6 | "the bytes of the object representation that correspond to any padding bytes take unspecified values" | 일치 |
| 25 | 07 :224 | `BigInteger.add(int[], int[])`는 32비트 조각을 아래부터 더하고 `sum >>> 32`를 넘김 | OpenJDK jdk21u `BigInteger.java` | `sum = (x[--xIndex] & LONG_MASK) + (y[--yIndex] & LONG_MASK) + (sum >>> 32);` | 일치 |
| 26 | 07 :265 | Spark에서 파일 크기 0 → 파일 누락 → "압축 해제 후 데이터 손실" 보고 | Dixit 외 arXiv:2102.11245 | "the database had missing files" / "the querying infrastructure reports critical data loss after decompression" | 일치 |
| 27 | 07 :268 | mercurial core, 수천 대당 몇 개 | Hochschild 외 HotOS 2021 | "we observe on the order of a few mercurial cores per several thousand machines" | 일치 |
| 28 | 07 :269 | 탐지 방법 셋(유휴 기계·주기 점검·운영 중 경량 테스트) | Dixit 외 §7 | "1 Opportunistic … machines in maintenance states" / "2 Periodic" / "3 Production Friendly" | 일치 |
| 29 | 08 :56 | 메타안정 출력은 VDD/2로 보이기 드물고 대개 0·1로 늦게 정해짐 | Ginosar 2011 | "the output will most likely be either 0 or 1, and as VA resolves, the output may (or may not) toggle at some later time" | 일치 |
| 30 | 08 :152 | 예: τ=10ps, T_W=20ps, F_C=1GHz, F_D=F_C/10 | Ginosar 2011 | "We estimate t = 10 ps, TW = 20 ps … and FC = 1 GHz. Let's assume that data changes every 10 clock cycles" | 일치 |
| 31 | 08 :250 | MTBF는 동기화기 수에 대략 반비례, 1,000개면 세 자릿수 큰 MTBF로 | Ginosar 2011 | "MTBF decreases roughly linearly with the number of synchronizers. Thus, if your system uses 1,000 synchronizers, you should be sure to design each one for MBTF at least three orders of magnitude higher" | 일치 |
| 32 | 08 :122 | TCP 종료 FIN-WAIT-1 → FIN-WAIT-2 → TIME-WAIT → CLOSED | RFC 9293 §3.3.2 그림 5 | 상태도: FIN WAIT-1 →(rcv ACK of FIN) FINWAIT-2 →(rcv FIN) TIME-WAIT →(Timeout=2MSL) CLOSED | 일치 |
| 33 | 09 :87 | x86-64 범용 레지스터 16개(ABI 3.2.1) | System V AMD64 ABI 0.99.6 §3.2.1 | "The AMD64 architecture provides 16 general purpose 64-bit registers." | 일치 |
| 34 | 09 :146 | 에뮬레이션 없이 arm64 호스트에서 amd64 컨테이너 불가 | Docker Multi-platform builds | "This is why you can't run a linux/amd64 container on an arm64 host (without using emulation)" | 일치 |
| 35 | 09 :249 | `kubernetes.io/arch`는 kubelet이 `runtime.GOARCH`로 채움 | Kubernetes Well-Known Labels | "The Kubelet populates this with runtime.GOARCH as defined by Go." | 일치 |
| 36 | 09 :255 | QEMU "much slower … compilation and compression", Rosetta "launch or run more slowly at times" | Docker 문서 · Apple Rosetta 문서(JSON) | "Emulation with QEMU can be much slower than native builds, especially for compute-heavy tasks like compilation and compression or decompression." / "translated apps launch or run more slowly at times" | 일치 |
| 37 | 10 :79 | red zone = `rsp` 아래 128바이트, 잎 함수가 프레임으로 씀 | SysV AMD64 ABI §3.2.2 | "The 128-byte area beyond the location pointed to by %rsp … leaf functions may use this area for their entire stack frame" | 일치 |
| 38 | 10 :79 | 커널은 red zone을 지키지 않아 `-mno-red-zone`(ABI A.2.2) | SysV AMD64 ABI §A.2.2 | "The Linux kernel does not honor the red zone … Kernel code should be compiled by GCC with the option -mno-red-zone." | 일치 |
| 39 | 10 :186 | JVM 스택 한도 초과 → `StackOverflowError` | JVMS SE21 §2.5.2 | "If the computation in a thread requires a larger Java Virtual Machine stack than is permitted, the Java Virtual Machine throws a StackOverflowError." | 일치 |
| 40 | 10 :304 | `-Xss` 기본 Linux/x64 1024 KB, Linux/Aarch64 2048 KB | Java 21 `java` 도구 문서 | "Linux/x64: 1024 KB Linux/Aarch64: 2048 KB" | 일치 |
| 41 | 11 :83 | 하드웨어 프리페처는 순차·일정 간격을 알아채고, 흩어진 접근은 예측 어려움 | Drepper 2007 §6.3.1 | "With contemporary hardware, strides are recognized as well" / "Currently prefetch units do not recognize non-linear access patterns." | 일치 |
| 42 | 11 :83 | 일부 최신 Intel Core의 DDP는 포인터 값을 보고 미리 가져오되 다시 따라가지 않음 | Intel "Data Dependent Prefetcher" (intel.com 403 → IA 사본) | "Some newer processors in the Intel® Core™ Processor Family support … (DDP)" / "DDP will not recursively dereference the memory contents of a data-dependent prefetched location" | 일치(관찰 1) |
| 43 | 11 :200 | CS:APP 6.6.2 "Rearranging Loops to Increase Spatial Locality" | CS:APP 3판 목차 PDF | "6.6.2 Rearranging Loops to Increase Spatial Locality 643" | 일치 |
| 44 | 12 :83 | 대부분 LRU, 연관도가 커지면 LRU 유지가 비싸 다른 전략 가능 | Drepper 2007 §3.3.5 | "Most caches evict the Least Recently Used (LRU) element first" / "maintaining the LRU list becomes more and more expensive and we might see different strategies adopted" | 일치 |
| 45 | 12 :150 | L3 조각을 문서화 안 된 complex addressing으로 고름, Sandy Bridge·Ivy Bridge·Haswell 대상 | Maurice 외 저자 PDF 초록 | "recent processors are using an undocumented technique called complex addressing" / "This set encompasses Sandy Bridge, Ivy Bridge and Haswell" | 일치(관찰 2) |
| 46 | 12 :151 | 2의 거듭제곱 마스킹이라 마스크 위 비트만 다른 해시는 항상 충돌 → `h ^ (h >>> 16)` | OpenJDK jdk21u `HashMap.java` | "sets of hashes that vary only in bits above the current mask will always collide" · `(h = key.hashCode()) ^ (h >>> 16)` | 일치 |
| 47 | 12 :215 | `RestrictContended` 기본 true, `ContendedPaddingWidth` 기본 128 | OpenJDK jdk21u `globals.hpp` | `product(intx, ContendedPaddingWidth, 128, …` · `product(bool, RestrictContended, true, "Restrict @Contended to trusted classes")` | 일치 |
| 48 | 13 :54 | Norvig 표: L1 0.5ns, 예측 실패 5ns, L2 7ns, 뮤텍스 25ns, 메모리 100ns, 탐색 8ms | Norvig "Teach Yourself Programming in Ten Years" | "fetch from L1 cache memory 0.5 nanosec … branch misprediction 5 … L2 7 … Mutex lock/unlock 25 … main memory 100 … (seek) 8,000,000 nanosec" | 일치 |
| 49 | 13 :55 | gist 제목 "~2012", "By Jeff Dean", "Originally by Peter Norvig", LLM 줄 추가 | jboner gist (raw) | "Latency Comparison Numbers (~2012)" / "By Jeff Dean" / "Originally by Peter Norvig" / "Local LLM, generate 1 token … (2026)" | 일치 |
| 50 | 13 :56 | Norvig vs gist: 탐색 8ms vs 10ms, 2KB 20µs vs 1KB 10µs | Norvig 글 · jboner gist | "send 2K bytes over 1Gbps network 20,000 nanosec" vs "Send 1K bytes over 1 Gbps network 10,000 ns" · "Disk seek 10,000,000 ns" | 일치 |
| 51 | 14 :77 | 현재 x86 명세는 "nearly identical to TSO" | JSR-133 Cookbook | "the current specs are nearly identical to TSO" | 일치 |
| 52 | 14 :119 | WC 모드 StoreStore `sfence`, SSE2 streaming LoadLoad `lfence` | JSR-133 Cookbook Notes | "StoreStore barriers ("sfence") are needed with WriteCombining (WC) caching mode" / "SSE2 extensions require LoadLoad "lfence" only only in connection with these streaming instructions" | 일치 |
| 53 | 14 :120 | Cookbook ARM 행은 "Version 7+", 마지막 수정 2011 | JSR-133 Cookbook | "arm Version 7+" / "Last modified: Tue Mar 22 07:11:36 EDT 2011" | 일치 |
| 54 | 14 :180 | `Assembler::membar` "We only have to handle StoreLoad", locked add가 cpuid보다 빠름 | OpenJDK jdk21u `assembler_x86.cpp` | "// We only have to handle StoreLoad … "locked" instructions which suffice as barriers, and are much faster than the alternative of using cpuid instruction. We use here a locked add [esp-C],0." | 일치 |
| 55 | 14 :243 | DCL 선언문이 Symantec JIT 예를 듦, JDK5+ volatile로 해결 | "Double-Checked Locking is Broken" Declaration | "When run on a system using the Symantec JIT, it doesn't work." / "As of JDK5 … Fixing Double-Checked Locking using Volatile" | 일치 |
| 56 | 15 :46 | Z270 예: 그래픽은 CPU 가까이 PCIe, DMI로 I/O 칩, NIC·NVMe는 PCIe, 디스크 eSATA, 키보드·마우스 USB | OSTEP 36.1 | "Intel's Z270 Chipset … connects to an I/O chip via Intel's proprietary DMI … hard drives … eSATA … USB … keyboard and mouse" / "via PCIe … network interface … NVMe" | 일치 |
| 57 | 15 :47 | 계층을 두는 이유는 물리와 비용, 빠른 버스일수록 짧음 | OSTEP 36.1 | "Put simply: physics, and cost. The faster a bus is, the shorter it must be" | 일치 |
| 58 | 15 :79 | 인터럽트 홍수로 livelock, [MR96] | OSTEP 36.4 | "a flood of interrupts may overload a system and lead it to livelock [MR96]" | 일치 |
| 59 | 16 :38 | 정착 시간만 0.5~2ms | OSTEP 37.3 | "The settling time is often quite significant, e.g., 0.5 to 2 ms" | 일치 |
| 60 | 16 :116 | OS가 몇 개(예: 16)를 골라 내리고 드라이브가 SPTF로 처리 | OSTEP 37.5 | "picks what it thinks the best few requests are (say 16) and issues them all to disk; the disk then uses … (SPTF) order" | 일치 |
| 61 | 16 :117 | 33·8·34 요청이면 33·34를 하나로 합침 | OSTEP 37.5 | "requests to read blocks 33, then 8, then 34 … the scheduler should merge the requests for blocks 33 and 34" | 일치 |
| 62 | 18 :176 | JLS §15.25는 고른 쪽만 평가한다고 정함 | JLS §15.25 | "The chosen operand expression is then evaluated" | 일치 |
| 63 | 18 :231 | Stack Overflow 정렬 배열 질문(2012) | stackoverflow.com/questions/11227809 (403 → IA 사본) | "Why is processing a sorted array faster than processing an unsorted array?" · "asked Jun 27, 2012" | 일치 |
| 64 | 19 :56 | Haswell ROB 192 μop, i7-4650U에서 188개 명령까지 동작 | Kocher 외 §II-B·IV | "on the Haswell microarchitecture, the reorder buffer has sufficient space for 192 micro-ops" / "On a Haswell i7-4650U … works with up to 188 simple instructions" | 일치 |
| 65 | 19 :114 | Meltdown 3.2~503 KB/s, Intel·Exynos M1 성공, 다른 ARM·AMD 실패 | Lipp 외 | "3.2 KB/s to 503 KB/s" / "on different Intel CPUs and a Samsung Exynos M1 processor, we did not manage to mount Meltdown on other ARM cores nor on AMD" | 일치 |
| 66 | 19 :134 | 변형 1 완화는 공격 경로를 다 막는다는 보장 없음 | 커널 문서 hw-vuln/spectre | "there is no guarantee that all possible attack vectors for Spectre variant 1 are covered" | 일치 |
| 67 | 19 :161 | 초당 5만 syscall에서 약 2%, 10MB 넘으면 1%→7%, PCID 4.14 | Gregg 2018-02-09 | "At 50k syscalls/sec per CPU the overhead may be 2%" / "more than 10 Mbytes … turn a 1% overhead … into a 7% overhead" / "pcid, fully available in Linux 4.14" | 일치 |
| 68 | 19 :162 | `mitigations=off` 문구 | 커널 매개변수 문서 | "This improves system performance, but it may also expose users to several CPU vulnerabilities." | 일치 |
| 69 | 20 :44 | 옵션 없는 `nproc`는 현재 프로세스가 쓸 수 있는 수, cgroup 제한 아래 더 작을 수 있음 | GNU Coreutils `nproc` | "Print the number of processing units available to the current process, which may be less than the number of online processors" / "Linux cgroup version 2 CPU quotas may also limit" | 일치 |
| 70 | 20 :111 | AMD 문서의 4소켓 기계, 2-hop 읽기·쓰기 30%·49% 느림 | Drepper 2007 §5.4 | "AMD documents the NUMA cost of a four socket machine" / "2-hop reads and writes are 30% and 49% (respectively) slower than 0-hop reads" | 일치 |
| 71 | 20 :139 | `numa_balancing`은 주기적 언매핑으로 표본을 떠 자주 접근하는 노드로 옮김 | 커널 문서 sysctl/kernel | "the kernel samples what task thread is accessing memory by periodically unmapping pages and later trapping a page fault" / "Memory is moved automatically to nodes that access it often." | 일치 |
| 72 | 21 :57 | `-O2`도 루프 벡터화, `very-cheap`은 에필로그 없는 루프만 | GCC 13.3 Optimize-Options | "-ftree-loop-vectorize … enabled by default at -O2" / "'very-cheap' model only allows vectorization if the vector code would entirely replace the scalar code" | 일치 |
| 73 | 21 :109 | `-fassociative-math`는 결과를 바꿀 수 있어 ISO C·C++ 위반, `-ffast-math`가 켬 | GCC 13.3 Optimize-Options | "This violates the ISO C and C++ language standard by possibly changing computation result." · -ffast-math → -funsafe-math-optimizations → "Enables … -fassociative-math" | 일치 |
| 74 | 21 :132 | Java는 결합법칙 같은 대수 항등식으로 식을 바꿔 쓰지 못함 | JLS §15.7.3 | "may not take advantage of algebraic identities such as the associative law … unless it can be proven that the replacement expression is equivalent" | 일치 |
| 75 | 21 :151 | 32스레드 워프, 따르지 않는 스레드는 마스크로 꺼짐 | CUDA Programming Guide v13.4.2 §1.2.2.2 | "threads are organized into groups of 32 threads called warps" / "the threads which do not follow the branch will be masked off" | 일치 |
| 76 | 22 :73 | bash는 신호 N으로 죽으면 128+N | bash 매뉴얼 Exit Status | "Bash uses the value 128+N as the exit status." | 일치 |
| 77 | 22 :73 | POSIX는 "128보다 큰 값"만 요구 | POSIX.1-2024 XCU 2.8.2 | "the shell shall assign it an exit status greater than 128" | 일치 |
| 78 | 22 :90 | `ENOEXEC`: 인식 못 하는 형식·다른 아키텍처·그 밖의 형식 오류 | execve(2) | "An executable is not in a recognized format, is for the wrong architecture, or has some other format error" | 일치 |
| 79 | 22 :100 | Meta 사례 `Int(1.1^53)`이 0 | Dixit 외 §5 | "the computation of Int(1.1^53) = 0" | 일치 |
| 80 | 22 :101 | 마지막 비데몬 스레드면 JVM도 끝남(JLS §12.8) | JLS §12.8 Program Exit | "All of its non-daemon threads have terminated, and all of the shutdown hooks … have terminated." | 일치 |
| 81 | 22 :309 | 지우기 "a few milliseconds"(44.4), GC "expensive"(44.8) | OSTEP 44.4·44.8 | "erases are quite expensive, taking a few milliseconds typically" / "garbage collection can be expensive, requiring reading and rewriting of live data" | 일치 |
| 82 | 23 :144 | 변환 위험 변수 7개 중 4개만 보호, SRI 작업량 목표 80% | Ariane 501 보고서 2.2 | "operations involving seven variables were at risk … protection being added to four of the variables" / "a maximum workload target of 80% had been set for the SRI computer" | 일치 |
| 83 | 23 :187 | 세 정밀도 모두, "1 in 9 billion", 12번째 비트 = 4번째 유효 10진 숫자, "a few missing entries" | Intel 백서 §3 (IA 사본) | "can occur in all three operating precisions" / "1 in 9 billion randomly fed divide or remainder instructions" / "12th bit position … or in the 4th significant decimal digit" / "a few missing entries in a lookup table" | 일치 |
| 84 | 23 :189 | 평균 사용자 "once in 27,000 years" | Intel 백서 §7 (IA 사본) | "The average PC user is likely to encounter a failure once in 27,000 years" | 일치 |
| 85 | 23 :190 | 1994-12-20 전면 교체 발표, 1995-01-17 세전 4억 7,500만 달러 | Nicely FAQ 연표 (IA 사본) | "20 December … Intel announces plans for a total recall, replacement, and destruction" / "17 Jan 1995 Intel announces a pre-tax charge of 475 million dollars" | 일치 |
| 86 | 23 :307 | timeval·timespec 인터페이스는 "the tv_sec member overflows in year 2038 on 32-bit architectures" | 커널 문서 core-api/timekeeping | 같은 문구 그대로 | 일치 |
| 87 | 23 :308 | `typedef __s64 time64_t;` | torvalds/linux `include/linux/time64.h` | 8행 `typedef __s64 time64_t;` | 일치 |
| 88 | 23 :309 | glibc 2.34 NEWS(2021-08-02): `_TIME_BITS=64`, LFS 필요, Linux 전용, 커널 5.1 이상 | libc-alpha 2021-08 (IA 사본) | "Date: Mon Aug 2 … 2021" · "_TIME_BITS preprocessor macro set to 64 and is only supported when LFS (_FILE_OFFSET_BITS=64) … only enabled for Linux and the full support requires a minimum kernel version of 5.1" | 일치 |
| 89 | 23 :315 | 1970년부터 센 초, 32비트에서 부호 있는 32비트, 2038년 1월에 바닥 | LWN 643234 (2015-05-05) | "May 5, 2015" · "January 2038 when signed 32-bit time_t values … run out of bits and overflow" · "On 32-bit systems, that count is a signed 32-bit value" | 일치 |
| 90 | 23 :317 | `_TIME_BITS` 없으면 아키텍처 의존(i686·ARM 32비트), `=32`는 "stops working in the year 2038", 64면 "immune to the Y2038 problem", 5.1 위 64비트 syscall | glibc 매뉴얼 Feature Test Macros (IA 사본) | "defaults to 32 bits on some traditional architectures (i686, ARM)" / "32-bit time_t stops working in the year 2038" / "immune to the Y2038 problem" / "For Linux kernel version above 5.1 syscalls supporting 64-bit time are used" | 일치 |

편별 건수: 01 4 · 02 4 · 03 4 · 04 4 · 05 5 · 06 3 · 07 4 · 08 4 · 09 4 · 10 4 · 11 3 · 12 4 · 13 3 · 14 5 · 15 3 · 16 3 · 18 2 · 19 5 · 20 3 · 21 4 · 22 6 · 23 9 = 90.

## 불일치 상세

없음(0건).

## 확인 불가·관찰 상세

확인 불가는 0건이다. 판정에는 영향이 없는 관찰 2건:

- **관찰 1 — 11 :83 Intel DDP 문서가 출처 목록에 없음.** 본문은 "(Intel "Data Dependent Prefetcher" 문서)"라고만 적고, 11의 '교재·문서' 목록(약 295~297행)에는 이 문서도 URL도 없다. 주장 내용은 원문과 맞는다.
  - 원문(IA 사본): "Some newer processors in the Intel® Core™ Processor Family support a new hardware prefetcher feature that can be classified as a Data-Dependent Prefetcher (DDP)." / "DDP will not recursively dereference the memory contents of a data-dependent prefetched location"
  - 제안: 출처 목록에 `- Intel, "Data Dependent Prefetcher" (Software Security Guidance, Technical Documentation) <https://www.intel.com/content/www/us/en/developer/articles/technical/software-security-guidance/technical-documentation/data-dependent-prefetcher.html> (2026-10-07에 intel.com은 403이라 Internet Archive 사본으로 열람)` 한 줄을 추가.
- **관찰 2 — 12 :310 Maurice 외 학회명 `[?]`는 지금 표기가 맞다.** 저자 PDF 본문에 "RAID 2015"라는 표기는 없다. "RAID"는 참고문헌 한 줄("RAID'14")에만 나온다. 노트의 `[?]` 처리가 원문 상태와 맞으므로 고칠 것 없다.

## 실제 읽은 파일

- 노트(읽기만): `cs/architecture/{01..16,18..23}-*/2-summary.md`(주장 줄과 출처 절 — grep과 줄 단위 열람), `docs/plans/2026-10-07/architecture-writing/log.md` 전문(52행)
- 받은 원문(scratchpad `arch/web/`): jls4·5·12·15·17, jvms2, n1570.pdf, n2412.pdf, gccint, gccopt(13.3), pystd, pysys, goldberg, rfc3629, rfc791, rfc9293, jep400, tr29, tr39, pgchar, Character(Java 21), byteorder(3), execve(2), mysql-utf8mb3(IA), hochschild.pdf, dixit.pdf, BigInteger.java, HashMap.java, globals.hpp, assembler_x86.cpp(jdk21u), ginosar.pdf, topology, x86abi.pdf(0.99.6), abi386-4.pdf, docker-mp, k8s-labels, rosetta.json, java-man, maurice.pdf, cpumemory.pdf, ddp(IA), preface3e.pdf, norvig, jboner(raw), cookbook, dcl, ostep36·37·44.pdf, proc, spectre.pdf, meltdown.pdf, hwspectre, kparams, gregg, sysctl-kernel, nproc, cuda-pm(v13.4.2), bash Exit-Status, POSIX XCU ch.2, so(IA), time64.h, timekeeping, lwn 643234, glibc-ftm(IA), glibc234(IA), fdiv3·fdiv7(IA), nicely(IA), ariane5rep

## 실패한 출처(대체 경로로 해결)

- `stackoverflow.com/questions/11227809` — 403 → Internet Archive 사본
- `developer.apple.com/documentation/...rosetta...` — JS 렌더링이라 본문이 비어 있음 → 같은 문서의 JSON(`developer.apple.com/tutorials/data/documentation/apple-silicon/about-the-rosetta-translation-environment.json`)
- `intel.com` DDP 문서 — 403 → IA 사본
- `dev.mysql.com` utf8mb3 — 403 → IA 사본
- Intel FDIV 백서 목차(`.../fdiv/wp/`) IA 사본에는 절 링크가 없음 → 절 페이지 `3.htm`·`7.htm`의 IA 사본을 직접 열었다
