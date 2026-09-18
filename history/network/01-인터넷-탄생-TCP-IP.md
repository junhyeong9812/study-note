# 인터넷의 탄생과 TCP/IP (1969~1983)

> 원본: `~/project/network-history/01-인터넷-탄생-TCP-IP.md` — 이 문서는 그 내용을 초보자용으로 다시 쓴 것이다(2026-09-18).\
> 연도·인명·논문명·기관명·RFC 번호·인용문은 원문 그대로다.\
> ASCII 도식 3개와 「한눈에」의 우편 비유, 용어 블록의 「예:」, 「용어 풀이」는 원문에 없는 보충이다.

## 한눈에 — 쉽게 말하면

원문이 제목 아래에 적은 한 줄 요약은 이것이다.

> 인터넷은 어느 날 발명된 것이 아니라, "서로 다른 네트워크를 어떻게 하나로 잇는가"라는 문제를 10여 년에 걸쳐 풀어 가며 만들어졌다. 그 출발점이 ARPANET(1969)이고, 핵심 해법이 TCP/IP(1974~)이며, 그것이 진짜 표준이 된 날이 1983년 1월 1일이다. 이 문서는 그 흐름을 "언제·왜"의 순서로 정리한다.

이 문서가 쓰는 비유는 하나뿐이고 끝까지 같다 — **전화 통화가 회선 교환, 우편이 패킷 교환**이다.\
그리고 "우체국은 배달만 하고, 빠진 편지를 다시 부치는 건 보낸 사람과 받는 사람"이 단대단 원칙이다.

- 1960년대의 통신은 **전화식**뿐이었다 — 이야기하는 내내 선 하나를 통째로 붙잡는다.\
  그런데 컴퓨터끼리의 대화는 몰렸다 끊겼다 해서, 붙잡아 둔 선이 대부분 놀았다.
- 그래서 **우편식**으로 바꿨다 — 내용을 조각내고 조각마다 주소를 붙여 각자 빠른 길로 보내고, 도착지에서 합친다.\
  이것이 ARPANET(1969)이 "실제로 작동한다"고 증명한 패킷 교환이다.
- 다음 문제는 **우체국이 여러 개**라는 것이었다 — 나라마다 우편 규칙이 다르면 국경을 넘을 수 없다.\
  이것이 원문이 말하는 "서로 다른 네트워크를 어떻게 하나로 잇는가"다.
- 답은 **공통 겉봉투**였다 — 각 망은 손대지 않고, 그 위에 어디서나 통하는 규격 하나를 얹었다.\
  그것이 TCP/IP(1974~)이고, 모두가 그것만 쓰기로 한 날이 1983년 1월 1일이다.

> **프로토콜(protocol)** — 두 기계가 말이 통하게 하려고 미리 정해 둔 절차와 형식.\
> 예: 봉투에 받는 사람·보내는 사람을 어디에 적을지 온 나라가 같은 규칙을 쓰는 것과 같다.

## 시대 정보

원문의 「시대 정보」 절을 그대로 옮긴 것이다.

- 기간: 1969년(ARPANET 첫 통신) ~ 1983년(TCP/IP 전면 전환)
- 주도 기관: 미국 국방부 산하 ARPA(후일 DARPA)
- 핵심 인물: Leonard Kleinrock, Vinton Cerf, Robert Kahn, Jonathan Postel, Steve Crocker
- 핵심 산출물: 패킷 교환 방식, NCP, TCP/IP 프로토콜군, RFC 문서 문화

## 시대적 배경

*(이 편의 「시대 배경」에 해당한다)*

1960년대 컴퓨터는 비싸고 희소했으며, 각 연구소가 제각기 다른 기종을 썼다.\
한 대의 값비싼 컴퓨터를 멀리 떨어진 연구자들이 나눠 쓰려면 기계들을 연결해야 했는데, 당시 통신은 전화망이 대표하는 **회선 교환** 방식뿐이었다.

> **회선 교환(circuit switching)** — 두 지점 사이에 통화 내내 독점 회선 하나를 통째로 잡아 두는 방식.\
> 예: 전화가 연결돼 있는 동안에는 아무 말도 하지 않는 순간에도 그 선을 다른 사람이 못 쓴다.

회선 교환은 사람의 음성 통화처럼 길게 끊김 없이 흐르는 트래픽에는 맞는다.\
하지만 컴퓨터 통신처럼 짧은 데이터가 몰렸다 멈췄다 하는("버스티한") 트래픽에는, 회선을 잡아 두는 동안 대부분 놀게 되어 지독히 비효율적이었다.

> **버스티(bursty)** — 데이터가 한꺼번에 몰렸다가 한동안 아무것도 안 오는 식으로 들쭉날쭉한 성질.\
> 예(원문에 없는 예): 한 줄 타이핑해 보내고 몇 초 생각하다 또 한 줄 보내는 터미널 접속이 그렇다.

또한 ARPA에는 냉전기 특유의 동기도 있었다.\
중앙 교환국 하나가 끊기면 통신 전체가 마비되는 회선 교환과 달리, 일부 노드가 사라져도 우회 경로로 데이터가 흐르는 **분산·생존성 있는 네트워크**가 필요하다는 발상이 패킷 교환 연구(Paul Baran, Donald Davies, Leonard Kleinrock)에 깔려 있었다.

두 방식을 나란히 놓으면 이렇다.

```text
회선 교환 (전화망)                      패킷 교환 (ARPANET)
+---------------------------+           +---------------------------+
| 통화 내내 회선 하나를     |           | 데이터를 작은 조각으로    |
| 통째로 잡아 둔다          |           | 잘라 각각 주소를 붙인다   |
| 컴퓨터 통신에서는         |           | 같은 회선을 여러 통신이   |
| 잡아 둔 선이 대부분 논다  |           | 나눠 쓸 수 있다           |
| 중앙 교환국 하나가 끊기면 |           | 노드 하나가 사라져도      |
| 통신 전체가 마비된다      |           | 우회 경로로 흐른다        |
+---------------------------+           +---------------------------+
```

- 대립축은 두 개다. 위의 두 쌍은 **회선을 미리 통째로 예약하느냐, 필요할 때 동적으로 할당해 나눠 쓰느냐**(원문 「ARPANET과 패킷 교환」 절), 맨 아래 한 쌍은 **생존성**(원문 「시대적 배경」 절)이다.\
  셋째 줄의 "컴퓨터 통신에서는"은 원문을 그대로 따른 것이다 — 원문은 음성 통화에는 회선 교환이 "맞다"고 하고, 선이 노는 것은 버스티한 컴퓨터 통신일 때라고 적었다.

## 주요 변화

*(이 편의 「무엇이 바뀌었나」에 해당한다)*

### ARPANET과 패킷 교환 (1969)

**언제** — 1969년 9월 BBN이 첫 IMP(Interface Message Processor)를 납품했고, 10월 29일 UCLA의 Kleinrock 연구실에서 SRI(스탠퍼드연구소)로 최초의 노드 간 패킷 메시지가 전송되었다.\
연말까지 UCLA, SRI, UC Santa Barbara, 유타대학교 4개 노드가 연결되었다.

**왜** — 회선 교환의 비효율과 단일 장애점을 피하기 위해 **패킷 교환**을 채택했다.

> **패킷 교환(packet switching)** — 데이터를 통째로 한 회선에 흘려보내는 대신, 출발지·목적지 주소가 붙은 작은 조각(패킷)으로 잘게 나눠 보내는 방식.\
> 예: 두꺼운 책을 통째로 부치는 대신 한 장씩 봉투에 주소를 적어 부치고, 받는 쪽에서 쪽번호대로 다시 묶는 것과 같다.

각 패킷은 그때그때 가장 빠른 경로를 독립적으로 찾아가고, 도착지에서 다시 조립된다.\
회선을 미리 통째로 예약(preallocation)하는 대신 필요할 때 동적으로 할당(dynamic allocation)하므로 같은 회선을 여러 통신이 나눠 쓸 수 있어 비용이 낮았다.\
회선 교환이 지배하던 시대에 ARPANET은 "패킷 교환이 실제로 작동한다"는 것을 처음으로 증명했다.

**핵심 장치** — **IMP**라는 별도의 소형 컴퓨터였다.\
값비싼 메인프레임(호스트)에 통신 부담을 지우지 않고, 각 노드 앞단에 통신 전담 장치(오늘날 라우터의 조상)를 두어 패킷 라우팅을 맡겼다.\
호스트는 "통신은 IMP에 맡기고 나는 계산만 한다"는 역할 분리가 처음부터 있었다.

### NCP — ARPANET 전용 첫 프로토콜 (1970~1972)

**언제** — 1970년경 설계, 1971~1972년 ARPANET 호스트에 배포.

**왜** — 패킷이 물리적으로 오간다고 해서 두 호스트가 "대화"할 수 있는 것은 아니다.\
어느 호스트와 연결을 맺고, 데이터를 순서대로 주고받고, 흐름을 제어하는 **공통 규약**이 필요했다.

> **NCP(Network Control Program/Protocol)** — 호스트 사이에 양방향 연결을 세워 주는, ARPANET 위에서 도는 첫 호스트 간 프로토콜.\
> 예: 우편망은 깔렸는데 "받았다고 답하고, 몇 번째 편지인지 세고, 너무 빨리 보내지 말라"는 약속이 없던 상태에, 그 약속을 처음 정해 준 것이 NCP다.

원문이 적은 근본적 한계는 이렇다.

- **ARPANET 단일 네트워크 전용**으로 설계되어 서로 다른 네트워크를 잇는 능력(internetworking)이 전혀 없었다.
- 신뢰성 있는 전달을 하부의 ARPANET/IMP에 의존했다.
- 주소가 **8비트(256개)** 에 불과해 확장에도 한계가 뚜렷했다.

원문은 이 절을 이렇게 맺는다.

> 즉 NCP는 "하나의 네트워크 안"은 풀었지만 "여러 네트워크 사이"는 풀지 못했다.

### TCP/IP — 네트워크의 네트워크 (1974)

**언제** — 1974년 5월, Vinton Cerf와 Robert Kahn이 IEEE Transactions on Communications에 논문 **"A Protocol for Packet Network Intercommunication"** 을 발표하며 TCP(Transmission Control Protocol)를 제시했다.\
같은 해 12월에는 Cerf, Yogen Dalal, Carl Sunshine이 이를 RFC 675로 명세화했다(여기서 "internet"이라는 용어가 쓰였다).

**왜** — 1970년대 초가 되자 ARPANET 말고도 여러 네트워크(무선 패킷망 PRNET, 위성망 SATNET 등)가 생겼는데, 저마다 하드웨어와 프로토콜이 달라 서로 통신할 수 없었다.\
Kahn은 DARPA에서 이 **Internetting**(네트워크 간 연결) 문제를 제기했고, NCP 설계에 참여했던 Cerf와 1973년 봄부터 함께 해법을 설계했다.

**핵심 발상**은 **단대단 원칙(end-to-end principle)** 이었다.

> **단대단 원칙(end-to-end principle)** — 중간의 네트워크들은 패킷을 "최선을 다해(best-effort)" 전달만 하고, 신뢰성(손실·순서·중복·재전송 처리)은 양 끝의 호스트가 책임진다는 원칙.\
> 예: 우체국은 배달만 하고, 편지가 빠졌는지 세어 다시 부치는 일은 보낸 사람과 받는 사람이 한다.

그래야 성질이 제각각인 네트워크들을 손대지 않고도 하나로 묶을 수 있다.\
또 각 네트워크의 경계에는 **게이트웨이(gateway, 오늘날 라우터)** 를 두어 서로 다른 망 사이에서 패킷을 중계하게 했다.\
이로써 "네트워크들의 네트워크", 곧 인터넷의 구조가 제시되었다.

```text
단대단 원칙 — 중간 망은 전달만, 신뢰성은 양 끝

호스트 A                                                 호스트 B
   |                                                            ^
   |  ARPANET --[게이트웨이]-- PRNET --[게이트웨이]-- SATNET    |
   |     중간 망들은 최선을 다해(best-effort) 전달만 한다       |
   |                                                            |
   +-- 손실·순서·중복·재전송을 책임지는 것은 이 양 끝이다 ------+
```

- 가운데 가로줄이 패킷이 지나가는 길이고, 게이트웨이가 하는 일은 서로 다른 망 사이의 중계뿐이다.\
  바깥의 세로줄과 아래 가로줄이 신뢰성을 책임지는 구간이다 — 중간이 아니라 양 끝이다.\
  망 이름은 원문이 예로 든 것(ARPANET·PRNET·SATNET)을 그대로 썼다. 이 셋이 실제로 이 순서로 이어져 있었다는 뜻은 아니다.

### TCP와 IP의 분리 — 계층화 (1978)

**언제** — 1978년. 여러 버전을 거치며(TCP v1~v2, 1978년 봄 v3 분리를 거쳐) 1978년 9월 무렵 v4에서 분리가 안정화되었다.\
Jonathan Postel이 단일 프로토콜이던 "Transmission Control Program"을 두 개로 쪼갰다.

**왜** — 초기 TCP는 주소 지정·라우팅 같은 하위 기능과 신뢰성 있는 전달이라는 상위 기능을 한 덩어리로 묶고 있었다.\
Postel은 이를 **계층 원칙 위반**이라 지적했다 — "We are screwing up ... by violating the principle of layering".

> **계층화(layering)** — 한 덩어리로 묶여 있던 기능을 하는 일에 따라 층으로 나눠, 각 층이 자기 일만 맡게 하는 구조.\
> 예: "봉투에 주소를 써서 부치는 일"과 "빠진 편지를 다시 부치는 일"을 서로 다른 사람이 맡는 것과 같다.

- **IP(Internet Protocol):** 연결 없이(connectionless) 패킷을 주소만 보고 목적지로 보내는 일에만 집중한다. 신뢰성은 보장하지 않는다(best-effort).
- **TCP(Transmission Control Protocol):** IP 위에 얹혀, 연결을 세우고 순서·재전송·흐름 제어로 **신뢰성**을 책임진다.

```text
1978년 이전                       1978년 이후
+----------------------+          +----------------------+
| Transmission Control |          | TCP                  |
| Program              |          |  연결 수립           |
|                      |          |  순서 · 재전송       |
|  주소 지정 · 라우팅  |          |  흐름 제어 = 신뢰성  |
|  신뢰성 있는 전달    |          +----------------------+
|  ... 한 덩어리       |          | IP                   |
|                      |          |  주소만 보고 보낸다  |
|                      |          |  신뢰성은 보장 안 함 |
+----------------------+          +----------------------+
```

- 왼쪽 한 칸이 오른쪽에서 위아래 두 칸으로 갈라진 것이다 — 원문의 표현대로 한 덩어리였던 것을 두 개로 쪼갰다.\
  아래 칸(IP)은 주소만 보고 목적지로 보내고, 위 칸(TCP)이 신뢰성을 맡는다.

이 분리 덕분에 신뢰성이 필요 없는 용도는 IP 위에 가벼운 프로토콜(후일 UDP)을 따로 올릴 수 있게 되었고, 각 계층을 독립적으로 발전시킬 수 있게 되었다.\
이때 자리 잡은 것이 오늘날까지 인터넷의 토대인 **IPv4**이고, "TCP/IP"라는 한 쌍의 이름은 이 분리에서 비롯됐다.

### 1983년 1월 1일 — Flag Day, NCP를 끄다

**언제** — 1983년 1월 1일. 미 국방부는 1982년 3월 TCP/IP를 공식 표준으로 선언하고, 1983년 1월 1일을 전환 기한으로 못 박았다.\
그날을 기점으로 ARPANET에서 **NCP를 완전히 끄고 TCP/IP로 일제히 전환**했다.

**왜** — 두 프로토콜을 무한정 병행 지원할 수는 없었다. 그래서 "특정 날짜에 모두가 동시에 갈아탄다"는 **Flag Day** 방식을 택했다.

그날 이후 TCP/IP로 전환하지 않은 호스트는 ARPANET 접속을 잃었다.\
당시 호스트는 약 **400대**뿐이라 일괄 전환이 현실적으로 가능했다(1982년 말 며칠간은 NCP를 일부러 차단해 준비 상태를 시험하기도 했다).\
강제 기한이 없었다면 전환은 한없이 미뤄졌을 것이다.

이 사건은 흔히 **현대 인터넷의 탄생일**로 꼽힌다.\
이날부터 ARPANET은 "여러 네트워크를 잇는 공통 언어(TCP/IP)"를 쓰는 진짜 인터넷의 중핵이 되었기 때문이다.\
("Flag day"는 이후 전산 용어로 굳어, 호환을 깨고 모두가 한날에 갈아타야 하는 전환을 가리키게 되었다.)

### 인터넷 거버넌스 — RFC 문화와 IETF

**언제** — RFC는 1969년 4월 7일 Steve Crocker의 **RFC 1 "Host Software"** 에서 시작했고, **IETF(Internet Engineering Task Force)** 는 1986년 1월 첫 회의(21명 참석)로 출범했다.

**왜** — 표준을 누가 어떻게 정하느냐도 풀어야 할 문제였다.\
ARPANET 초기에 각 대학 대학원생들이 모인 비공식 모임 **NWG(Network Working Group)** 가 프로토콜을 의논했는데, Crocker는 자신들의 메모를 격식 있는 "표준 공표"가 아니라 누구나 의견을 보탤 수 있는 **"Request for Comments(의견 요청)"** 라는 겸손한 제목으로 냈다.\
권위가 아니라 토론으로 합의를 만든다는 이 태도가 이후 인터넷 표준 문화 전체의 성격을 결정했다.

> **RFC(Request for Comments, 의견 요청)** — 인터넷 표준이 발행되는 문서 형식이자 그 문화의 이름.\
> 예: 1969년 4월 7일 Steve Crocker가 낸 RFC 1의 제목은 "Host Software"였다.

이 정신을 한 문장으로 압축한 것이 MIT의 Dave Clark가 1992년 7월 IETF 회의 발표("A Cloudy Crystal Ball")에서 남긴 말이다:

> "우리는 왕도, 대통령도, 투표도 거부한다. 우리는 **대략적 합의와 돌아가는 코드**를 믿는다."
> ("We reject kings, presidents and voting. We believe in rough consensus and running code.")

즉 표준은 권위자의 명령이나 다수결이 아니라, ① 참여자들의 **대략적 합의(rough consensus)** 와 ② 실제로 **구현되어 돌아가는 코드(running code)** 로 검증한다는 원칙이다.\
명세를 종이 위에서 완벽히 만든 뒤 강제하는 것이 아니라, 일단 만들어 돌려 보고 작동하는 쪽으로 수렴하는 이 실용주의가 인터넷이 빠르고 분산적으로 진화할 수 있었던 문화적 토대가 되었다.

## 영향과 의의

*(이 편의 「남긴 것」에 해당한다)*

원문의 「영향과 의의」 절에 적힌 문장들이다.

- 1969~1983년의 흐름은 "값비싼 컴퓨터를 나눠 쓰기 위한 패킷 교환 실험"에서 출발해 "성질이 다른 네트워크들을 하나로 잇는 보편 규약"으로 도달한 여정이었다.
- **패킷 교환**은 통신의 기본 단위를 바꿨다.
- **NCP**는 단일 네트워크의 가능성과 한계를 동시에 보여 줬다.
- **TCP/IP**는 단대단 원칙과 계층화로 확장 가능한 인터넷의 골격을 세웠다.
- **1983년 Flag Day**는 그 골격을 실제 표준으로 굳혔다.
- 오늘날 우리가 쓰는 인터넷은 여전히 이때 정해진 **IP 위에 TCP/UDP를 얹는 구조**다.
- 표준은 여전히 **RFC로 발행**되고 **IETF**가 "rough consensus and running code"로 운영한다.
- 기술적 설계와 거버넌스 문화가 함께 인터넷의 DNA가 된 것이다.

## 용어 풀이

- **회선 교환(circuit switching)** — 통화 내내 독점 회선 하나를 통째로 잡아 두는 방식.
- **패킷 교환(packet switching)** — 데이터를 주소 붙은 조각(패킷)으로 잘라 각자 경로를 찾아가게 하고 도착지에서 조립하는 방식.
- **IMP(Interface Message Processor)** — ARPANET 각 노드 앞단의 통신 전담 소형 컴퓨터. 오늘날 라우터의 조상.
- **NCP(Network Control Program/Protocol)** — ARPANET 위에서 돈 첫 호스트 간 프로토콜. 단일 네트워크 전용이었다.
- **internetworking / Internetting** — 서로 다른 네트워크를 잇는 능력 / Kahn이 DARPA에서 제기한 그 문제.
- **단대단 원칙(end-to-end principle)** — 중간 망은 best-effort(최선을 다하되 보장은 없음) 전달만, 신뢰성은 양 끝 호스트가 책임진다는 원칙.
- **게이트웨이(gateway)** — 서로 다른 망의 경계에서 패킷을 중계하는 장치. 오늘날 라우터.
- **계층화(layering)** — 기능을 층으로 나눠 각 층이 자기 일만 맡게 하는 구조.
- **IP / TCP / IPv4** — 주소만 보고 패킷을 보내는 층 / 그 위에서 연결·순서·재전송·흐름 제어로 신뢰성을 만드는 층 / 1978년 분리에서 자리 잡은 IP 버전.
- **Flag Day** — 호환을 깨고 모두가 한날에 갈아타야 하는 전환.
- **RFC / NWG / IETF** — 표준이 발행되는 문서 형식 / ARPANET 초기의 비공식 프로토콜 모임 / 1986년 1월 출범한 표준화 기구.
- **rough consensus and running code** — 대략적 합의와 돌아가는 코드. IETF의 운영 원칙.

## 참고 출처

- [Cerf & Kahn, "A Protocol for Packet Network Intercommunication" (1974) - cs.Princeton PDF](https://www.cs.princeton.edu/courses/archive/fall06/cos561/papers/cerf74.pdf)
- [Milestones: Inception of the ARPANET, 1969 - ETHW](https://ethw.org/Milestones:Inception_of_the_ARPANET,_1969)
- [Packet Switching - ETHW](https://ethw.org/Packet_Switching)
- [Milestones: Transmission Control Protocol (TCP) Enables the Internet, 1974 - ETHW](https://ethw.org/Milestones:Transmission_Control_Protocol_(TCP)_Enables_the_Internet,_1974)
- [Internet protocol suite - Wikipedia](https://en.wikipedia.org/wiki/Internet_protocol_suite)
- [Network Control Protocol (ARPANET) - Wikipedia](https://en.wikipedia.org/wiki/Network_Control_Protocol_(ARPANET))
- [Flag day (computing) - Wikipedia](https://en.wikipedia.org/wiki/Flag_day_(computing))
- [Final report on TCP/IP migration in 1983 - Internet Society](https://www.internetsociety.org/blog/2016/09/final-report-on-tcpip-migration-in-1983/)
- [RFC 1 "Host Software" - IETF](https://www.ietf.org/rfc/rfc1.html)
- [46 Years of RFCs - Internet Society](https://www.internetsociety.org/blog/2015/04/46-years-of-rfcs-celebrating-the-anniversary-of-rfc-1/)
- [Introduction to the IETF](https://www.ietf.org/about/introduction/)
- ["Rough Consensus and Running Code" and the Internet (Froomkin) - Duke CS PDF](https://courses.cs.duke.edu/common/compsci092/papers/govern/consensus.pdf)
