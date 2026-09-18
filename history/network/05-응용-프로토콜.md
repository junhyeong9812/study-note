# 응용 계층 프로토콜의 역사

> 원본: `~/project/network-history/05-응용-프로토콜.md` — 이 문서는 그 내용을 초보자용으로 다시 쓴 것이다(2026-09-18).\
> 연도·인명·논문명·RFC 번호·포트 번호·표준명·코드블록·표는 원문 그대로다.\
> ASCII 도식 12개와 「한눈에」의 비유, 용어 블록의 「예:」, 「용어 풀이」는 원문에 없는 보충이다.

## 한눈에 — 쉽게 말하면

> 사람이 읽는 텍스트 명령으로 시작해, 암호화·구조화된 원격 호출과 실시간 양방향 통신으로 진화해 온 응용 계층(OSI 7계층 / TCP-IP 응용 계층)의 변천사. "언제, 왜 등장했고, 무엇을 대체했는가"를 축으로 정리한다.

**응용 계층 프로토콜은 "두 프로그램이 주고받을 말의 규칙"이다.**

이 문서 전체에서 비유는 하나로 고정한다 — **주문서 양식**이다.

- 처음에는 **손으로 쓴 주문서**였다.\
  사람이 그대로 읽고 쓸 수 있는 글자로 "이거 주세요"라고 적었다.
- 그런데 **주문서가 그대로 다 보였다.**\
  비밀번호까지 적혀 있는데 배달 경로의 누구나 읽을 수 있었다. 그래서 암호 봉인을 씌웠다.
- 다음에는 **주문서에 무엇을 적을지**가 문제였다.\
  "이 함수를 실행해 줘"로 적을지, "이 물건을 주세요"로 적을지를 두고 왕복했다.
- 그리고 **주문서를 매번 다시 보내는 게** 낭비였다.\
  가게가 먼저 연락할 길이 없어서 계속 되물어야 했다. 그래서 통화선을 열어 두게 했다.
- 마지막으로 **양식 자체를 줄였다.**\
  사람이 읽을 필요 없는 주문이라면 글자 대신 번호만 적는 편이 작고 빠르다.

핵심 패턴은 원문 마지막 단락의 문장이다.

> **새 프로토콜은 옛것을 완전히 지우기보다 새로운 제약(보안·실시간·저전력·고성능)이 생길 때마다 그 문맥에 최적화된 한 겹을 더한다.**

```text
네 번의 패러다임 전환 — 각 전환이 푼 문제

텍스트 시대 (1969~)   사람이 직접 타이핑할 수 있는 ASCII 명령
   |
   | 문제: 명령도 비밀번호도 평문이라 그대로 새어 나간다
   v
보안 시대 (1995~)     SSH — 암호화·강한 인증을 기본값으로
   |
   | 문제: 이기종 시스템을 통합하고 방화벽을 넘어야 한다
   v
웹/원격호출 시대 (2000~)  SOAP -> REST, XML -> JSON
   |
   | 문제: 서버가 먼저 보낼 길이 없어 계속 되묻는다
   v
실시간 시대 (2011~)   WebSocket, SSE, MQTT — 서버 푸시·양방향
   |
   | 문제: 텍스트 직렬화의 파싱 비용과 장황함이 부담이 된다
   v
효율 시대 (2015~)     gRPC, HTTP/2, protobuf — 이진 직렬화
```

그림 해설 — 박스 없는 각 줄이 **한 시대**이고, 세로줄 옆 한 줄이 **그 시대가 마주한 문제**다.\
문제 문장은 전부 원문이 각 시대의 「왜」로 적은 것을 옮긴 것이다.

> **응용 계층(application layer)** — 프로그램끼리 주고받는 메시지의 뜻을 정하는 맨 위 계층.\
> 예: 원문 표현대로 전송 계층이 "바이트를 안전하게 옮기는" 문제를 풀면, 응용 계층은 "그 바이트가 무엇을 의미하는가"를 정한다.

> **프로토콜(protocol)** — 두 프로그램이 말이 통하게 하려고 미리 정해 둔 절차와 형식.\
> 예: `HELO` 다음에 `MAIL FROM`이 오고, 상대는 `250 OK`로 답한다는 약속이 그것이다.

## 개요

응용 계층 프로토콜은 TCP(또는 UDP) 위에서 **애플리케이션끼리 주고받는 메시지의 약속**이다.

전송 계층(TCP/IP)이 "바이트를 안전하게 옮기는" 문제를 풀었다면, 응용 계층은 "그 바이트가 무엇을 의미하는가"를 정한다.

이 계층의 역사는 크게 네 번의 패러다임 전환을 거쳤다.

```
1969 ───────── 1995 ──────── 2000 ─────────── 2011 ───────── 2015 ──────▶
  │              │              │                │              │
  │ 텍스트 시대   │ 보안 시대     │ 웹/원격호출 시대 │ 실시간 시대    │ 효율 시대
  │ Telnet/FTP   │ SSH가 평문    │ SOAP→REST,     │ WebSocket,    │ gRPC,
  │ SMTP/NNTP    │ 프로토콜 대체  │ XML→JSON       │ SSE, MQTT     │ HTTP/2,
  │ (사람이 읽는  │ (암호화 기본) │ (자원·표현 중심)│ (양방향 푸시)  │ protobuf
  │  명령줄)      │              │                │              │ (이진 직렬화)
  ▼              ▼              ▼                ▼              ▼
```

원문의 표를 그대로 옮긴 것이다 — 연도·대표 프로토콜은 여기서 확인하면 된다.

| 시대 | 핵심 변화 | 대표 프로토콜 | 무엇을 풀었나 |
|------|-----------|---------------|----------------|
| **텍스트 시대** (1969~) | 사람이 직접 타이핑할 수 있는 ASCII 명령 | Telnet, FTP, SMTP, POP/IMAP, NNTP | 이기종 호스트 간 상호운용 |
| **보안 시대** (1995~) | 평문 → 암호화·강한 인증 | SSH | 도청·자격증명 탈취 |
| **웹/원격호출 시대** (2000~) | RPC → 자원 지향(REST), XML → JSON | SOAP, REST | 방화벽·이기종 통합·웹 생태계 |
| **실시간 시대** (2011~) | 요청-응답 → 서버 푸시·양방향 | WebSocket, SSE, MQTT | 지연·폴링 비용·IoT |
| **효율 시대** (2015~) | 텍스트 직렬화 → 이진·계약 우선 | gRPC, protobuf | 마이크로서비스 성능·스키마 |

---

## 1. 텍스트 프로토콜 시대 — 사람이 읽는 명령줄 (1969~1990년대)

ARPANET 초기의 응용 프로토콜은 모두 **사람이 터미널에서 직접 타이핑할 수 있는 ASCII 텍스트 명령**으로 설계되었다.

호스트마다 운영체제와 문자 인코딩이 제각각이던 시절, "줄 단위 텍스트 + 명령어/응답코드"라는 단순한 규약이 이기종 상호운용의 최소 공통분모였기 때문이다.

이 설계 철학(NVT, Network Virtual Terminal)은 이후 SMTP·FTP·HTTP까지 이어진 **텍스트 기반 요청/응답 프로토콜 계보**의 출발점이 되었다.

```text
이 시대 프로토콜의 공통 모양

  보내는 쪽 :  대문자 명령어 한 줄            (사람이 그대로 타이핑할 수 있다)
  받는 쪽   :  숫자 응답코드 + 사람이 읽는 설명

  예를 들면
     C: MAIL FROM:<alice@example.org>
     S: 250 OK

  숫자 응답코드의 뜻 (원문: HTTP가 그대로 물려받았다)
     2xx  성공
     3xx  추가 입력이 필요함
     4xx / 5xx  오류
```

> **ASCII** — 영문자·숫자·기호를 숫자로 대응시킨 오래된 문자 인코딩.\
> 예: 이 시대의 명령은 전부 ASCII 텍스트라 사람이 터미널에서 그대로 타이핑할 수 있었다.

> **NVT(Network Virtual Terminal)** — 서로 다른 호스트가 공통으로 가정하는 가상의 터미널.\
> 예: 원문 표현대로 이 설계 철학이 SMTP·FTP·HTTP까지 이어지는 텍스트 프로토콜 계보의 출발점이 되었다.

> **응답코드(response code)** — 결과를 숫자로 알리는 값.\
> 예: 위 도식처럼 2xx는 성공, 3xx는 추가 입력, 4xx/5xx는 오류다 — 원문이 적은 대로 HTTP가 이 규약을 그대로 물려받았다.

### Telnet — 원격 터미널 (RFC 854, 1983)

- **언제**: 1969년 ARPANET 초기 명세(RFC 15)에서 출발해, 1983년 5월 RFC 854(J. Postel, J. Reynolds)로 표준이 정리되었다.
- **왜**: 멀리 떨어진 호스트의 터미널에 로그인해 명령을 실행하기 위해.\
  양쪽이 합의하는 가상 터미널(NVT) 위에서 옵션을 협상(`WILL`/`WONT`/`DO`/`DONT`)하는 구조다.
- **무엇을 대체했나**: 기관마다 제각각이던 원격 접속 방식을 표준 하나로 통일했다. 포트 23.

```text
Telnet의 옵션 협상 — 네 단어로 합의한다

  한쪽 :  WILL  "내가 이 옵션을 쓰겠다"
  상대 :  DO    "그렇게 해라"          또는  DONT  "하지 마라"

  한쪽 :  DO    "네가 이 옵션을 써라"
  상대 :  WILL  "그러겠다"             또는  WONT  "안 하겠다"

  ⇒ 양쪽이 합의하는 가상 터미널(NVT) 위에서 이 협상이 오간다
```

원문은 네 단어를 이름만 열거한다 — 각 단어의 뜻과 요청·응답 짝 구조는 원문에 없는 보충이다(RFC 854).

#### 대가는 무엇인가

모든 통신이 **평문**이다.

비밀번호조차 네트워크에 그대로 흘러, 1990년대 패킷 스니핑이 보편화되자 치명적 약점이 되었다(→ §2 SSH).

### FTP — 파일 전송 (RFC 959, 1985)

- **언제**: 1971년 RFC 114에서 시작해, 1985년 10월 RFC 959로 오늘날까지 쓰이는 형태가 확정되었다.
- **왜**: 호스트 간 파일을 신뢰성 있게 전송하기 위해.\
  특징은 **제어 연결(포트 21)과 데이터 연결(포트 20)을 분리**한 점이다.\
  명령(`USER`, `PASS`, `RETR`, `STOR`)은 제어 채널로, 실제 파일은 별도 데이터 채널로 흐른다.
- **무엇을 대체했나**: 임시방편적 파일 복사 방식을 표준화.\
  액티브/패시브 모드, ASCII/바이너리 전송 타입 같은 개념을 정립했다.

```text
FTP는 연결을 둘로 나눈다

  클라이언트 ══ 제어 연결 (포트 21) ══▶ 서버     USER · PASS · RETR · STOR
  클라이언트 ══ 데이터 연결 (포트 20) ══▶ 서버    실제 파일 내용

  ⇒ 명령과 데이터가 서로 다른 연결로 흐른다
```

> **제어 연결 / 데이터 연결** — 명령을 주고받는 통로와 실제 파일이 흐르는 통로를 따로 두는 구조.\
> 예: FTP에서 제어는 포트 21, 데이터는 포트 20이다.

#### 대가는 무엇인가

역시 평문이며, 이중 연결 구조가 NAT·방화벽과 충돌이 잦다.

훗날 SFTP(SSH 기반)·SCP·HTTPS에 자리를 내준다.

### SMTP — 메일 전송 (RFC 821, 1982)

- **언제**: 1982년 8월 RFC 821(Jon Postel).\
  이전의 FTP 기반 메일 전송과 Mail Box Protocol을 대체하며 **인터넷 이메일의 표준 전송 프로토콜**이 되었다.
- **왜**: 메일 서버 간(MTA↔MTA) 메시지를 "밀어 넣는(push)" 단순한 텍스트 대화로 표준화하기 위해.\
  명령은 `HELO`/`MAIL FROM`/`RCPT TO`/`DATA` 네 단어면 충분했다.
- **무엇을 대체했나**: 산발적인 메일 교환 방식을 통일.\
  이후 RFC 5321(2008)로 갱신되며 ESMTP(`EHLO`, 인증, TLS 협상)가 더해졌다.

```
# SMTP 세션 예시 (S=서버, C=클라이언트) — 모든 명령이 사람이 읽는 텍스트
S: 220 mail.example.com ESMTP ready
C: EHLO client.example.org
S: 250-mail.example.com
S: 250 STARTTLS
C: MAIL FROM:<alice@example.org>
S: 250 OK
C: RCPT TO:<bob@example.com>
S: 250 OK
C: DATA
S: 354 Start mail input; end with <CRLF>.<CRLF>
C: Subject: Hello
C:
C: Hi Bob.
C: .
S: 250 OK queued as 12345
```

> **MTA(Mail Transfer Agent)** — 메일을 서버에서 서버로 옮기는 프로그램.\
> 예: SMTP는 원문 표현대로 메일 서버 간(MTA↔MTA) 메시지를 "밀어 넣는(push)" 단순한 텍스트 대화다.

SMTP는 "보내기" 전용이다.\
**받은 메일을 사용자 단말이 가져오는** 문제는 POP/IMAP이 맡았다.

### POP과 IMAP — 메일 수신 (POP3: RFC 1939, 1996 / IMAP4rev1: RFC 3501, 2003)

- **POP3(Post Office Protocol)**: 서버에 도착한 메일을 **클라이언트로 내려받고 서버에서는 지운다**는 모델.\
  단순하고 저장 공간이 비쌌던 시절에 적합했다. RFC 1939(1996)로 안정화.
- **IMAP(Internet Message Access Protocol)**: Mark Crispin이 1986년 설계, RFC 3501(IMAP4rev1, 2003)로 정착.\
  메일을 **서버에 그대로 두고 폴더·플래그·검색을 서버에서 관리**한다.\
  여러 기기에서 같은 메일함을 일관되게 보는 다중 단말 시대(스마트폰·웹메일)에 들어맞아 POP를 사실상 밀어냈다.
- **대체 관계**: POP "다운로드 후 삭제" → IMAP "서버 동기화".\
  멀티 디바이스 환경이 승부를 갈랐다.

```text
메일이 어디에 남는가 — 대립축은 "다운로드 후 삭제" vs "서버 동기화"

POP3  다운로드 후 삭제
   [서버] ──내려받는다──▶ [PC]
   [서버]  (지운다)
   ⇒ 저장 공간이 비쌌던 시절에 적합했다

IMAP  서버 동기화
   [서버]  메일 · 폴더 · 플래그 · 검색을 서버가 관리
      ├──▶ [PC]
      ├──▶ [스마트폰]        여러 기기가 같은 메일함을 일관되게 본다
      └──▶ [웹메일]
```

### NNTP — Usenet 뉴스 (RFC 977, 1986)

- **언제**: 1986년 3월 RFC 977(Brian Kantor, Phil Lapsley). 2006년 RFC 3977로 갱신.
- **왜**: Usenet 기사를 호스트 간에 효율적으로 배포하기 위해.\
  그전까지는 전화선 기반 **UUCP의 store-and-forward**(저장 후 전달) 방식이었다.
- **무엇을 대체했나**: UUCP를 대체해 TCP/IP 위에서 거의 실시간으로 뉴스를 주고받게 했다. 포트 119.\
  pub/sub·메시지 ID·중복 제거 같은 개념의 초기 사례로, 분산 메시지 배포의 원형이다.

```text
대립축은 "전화선 기반 저장 후 전달" vs "TCP/IP 위 거의 실시간"

UUCP  store-and-forward (전화선 기반)
   [호스트] ─저장─▶ (전화 연결될 때까지 기다림) ─전달─▶ [호스트] ─저장─▶ ...

NNTP  TCP/IP 위
   [호스트] ──────────────────────────────────▶ [호스트]
            거의 실시간으로 뉴스를 주고받는다
```

> **store-and-forward(저장 후 전달)** — 일단 받아서 보관했다가 다음 구간이 열리면 넘기는 방식.\
> 예: 원문 표현대로 UUCP는 전화선 기반이라 이 방식이었고, NNTP가 TCP/IP 위에서 이를 대체했다.

> **pub/sub(발행-구독)** — 보내는 쪽이 받는 쪽을 직접 지정하지 않고, 주제를 기준으로 느슨하게 이어지는 방식.\
> 예: 원문이 NNTP를 "pub/sub·메시지 ID·중복 제거 같은 개념의 초기 사례"로 든다 — 뒤의 MQTT(§4)가 같은 발상이다.

> **이 시대의 공통 DNA**: ① 줄 단위 ASCII 텍스트, ② 사람이 읽는 명령어 + 숫자 응답코드(2xx 성공, 3xx 추가 입력, 4xx/5xx 오류 — HTTP가 그대로 물려받았다), ③ **암호화 부재**. 이 마지막 항목이 다음 시대의 방아쇠가 된다.

---

## 2. 보안의 도입 — SSH가 평문 프로토콜을 대체하다 (1995)

### SSH (Secure Shell)

- **언제**: 1995년, 핀란드 헬싱키 공과대학의 연구원 **Tatu Ylönen**이 설계. 같은 해 7월 프리웨어로 공개했다.\
  표준화된 SSH-2는 2006년 RFC 4251(아키텍처)·RFC 4253(전송 계층) 등으로 정리되었다.
- **왜**: 직접적 계기는 **교내 네트워크에서 발생한 비밀번호 스니핑 공격**이었다.\
  Telnet·rlogin·FTP·rsh가 자격증명을 평문으로 흘리는 한, 같은 네트워크의 누구나 패킷을 엿보면 로그인할 수 있었다.
- **무엇을 대체했나**: Ylönen이 명시한 목표 그대로 **Telnet·rlogin·rsh·(평문)FTP를 대체**했다.\
  강한 서버 인증, 키 교환, 전 구간 암호화, 무결성 검증을 기본 제공한다.\
  공개 1년이 안 돼 전 세계 사용자 2만 명으로 퍼졌고, 오늘날 원격 접속의 사실상 표준이 되었다.

```text
같은 로그인, 같은 네트워크 — 대립축은 "평문" vs "전 구간 암호화"

Telnet · rlogin · rsh · (평문)FTP
   사용자 ──"PASS mypassword"(글자 그대로)──▶ 서버
                    ▲
             같은 네트워크의 누구나 패킷을 엿보면 로그인할 수 있었다

SSH
   사용자 ──[키 교환 → 전 구간 암호화 → 무결성 검증]──▶ 서버
                    ▲
             강한 서버 인증까지 기본 제공한다
```

> **스니핑(sniffing)** — 오가는 패킷을 몰래 들여다보는 것.\
> 예: 원문이 적은 SSH의 직접적 계기가 "교내 네트워크에서 발생한 비밀번호 스니핑 공격"이다.

> **자격증명(credential)** — 로그인에 쓰이는 아이디·비밀번호·키 같은 증명 수단.\
> 예: Telnet은 이 자격증명을 평문으로 흘렸다.

```
# SSH-2의 계층 구조 (RFC 4251)
┌─────────────────────────────────────────────┐
│  Connection Layer (RFC 4254)                 │  ← 채널 다중화: shell, SFTP, 포트포워딩
├─────────────────────────────────────────────┤
│  User Authentication Layer (RFC 4252)        │  ← 공개키 / 비밀번호 / 호스트 기반 인증
├─────────────────────────────────────────────┤
│  Transport Layer (RFC 4253)                  │  ← 키 교환·서버 인증·암호화·무결성
├─────────────────────────────────────────────┤
│  TCP/IP                                      │
└─────────────────────────────────────────────┘
```

SSH의 **채널 다중화** 설계 덕분에 하나의 암호화 연결 위에서 원격 셸뿐 아니라 **SFTP(보안 파일 전송)·포트 포워딩·터널링**이 가능해졌다.

```text
채널 다중화 — 암호화 연결 하나 위에 여러 용도를 얹는다

   사용자 ══ 하나의 암호화 연결 ══▶ 서버
              ├─ 원격 셸
              ├─ SFTP (보안 파일 전송)
              ├─ 포트 포워딩
              └─ 터널링
```

결과적으로 SSH는 단일 프로토콜이 아니라 "안전한 통로"라는 플랫폼이 되어, FTP·Telnet 시대의 평문 도구 묶음을 통째로 흡수했다.

> **채널 다중화(multiplexing)** — 연결 하나 안에 여러 개의 논리적 통로를 두는 것.\
> 예: 위 도식처럼 SSH 연결 하나 위에서 셸·SFTP·포트 포워딩이 동시에 돈다.

> **시대 전환의 교훈**: 1세대 텍스트 프로토콜은 *상호운용*을 위해 단순함을 택했고, 그 단순함이 곧 *보안 부재*였다. SSH는 "암호화는 선택이 아니라 기본값"이라는 원칙을 응용 계층에 각인시켰고, 이는 훗날 HTTPS 전면화·TLS 의무화로 이어진다.

---

## 3. 원격 호출의 진화 — RPC에서 gRPC까지 (1984~2015)

"네트워크 너머의 함수를 마치 로컬 함수처럼 호출한다"는 아이디어, 즉 **RPC(Remote Procedure Call)** 는 응용 계층의 또 다른 큰 줄기다.

이 줄기는 *분산 객체*(RPC/SOAP) → *자원 지향*(REST) → *고성능 계약 우선*(gRPC)으로 30년에 걸쳐 진자 운동을 했다.

```
1984        1988         1998/2000      2000          2015
Birrell &   Sun RPC      XML-RPC →      REST          gRPC
Nelson      (RFC 1057)   SOAP           (Fielding     (Google,
(개념·논문)  (이진 RPC)    (XML/HTTP)     박사논문)      HTTP/2+protobuf)
   │            │            │              │              │
   └─ "원격을   └─ 언어 중립  └─ 방화벽     └─ "RPC를     └─ "REST의 텍스트
      로컬처럼"     IDL+XDR      통과(80포트)    버리고 웹을     오버헤드를 버리고
                                 무거운 XML       그대로 쓰자"    RPC로 회귀"
```

> **RPC(Remote Procedure Call)** — 네트워크 너머의 함수를 마치 로컬 함수처럼 호출하는 방식.\
> 예: 원문 표현 그대로 "네트워크 너머의 함수를 마치 로컬 함수처럼 호출한다"는 아이디어다.

### RPC의 기원 (1984) — Sun RPC (RFC 1057, 1988)

- **개념**: 1984년 Birrell과 Nelson이 Xerox PARC에서 *Implementing Remote Procedure Calls* 논문으로 정식화.\
  클라이언트의 **스텁(stub)** 이 인자를 직렬화(marshalling)해 보내고, 서버 스텁이 풀어서 실제 함수를 호출한다.
- **Sun RPC(ONC RPC)**: 1988년 RFC 1057, 1995년 RFC 1831로 표준화.\
  **XDR**(eXternal Data Representation)로 데이터를 언어 중립적으로 인코딩하고, IDL로 인터페이스를 기술했다.\
  NFS(네트워크 파일 시스템)의 기반이 되었다.

```text
스텁이 하는 일 — 원격 호출을 로컬 호출처럼 보이게 한다

  클라이언트 코드                                     서버 코드
      |  getUser(42)  를 평범하게 호출                     ▲ 실제 함수 실행
      v                                                   |
  [클라이언트 스텁]                                  [서버 스텁]
      |  인자를 직렬화(marshalling)                        ▲ 풀어서 인자 복원
      └──────────────── 네트워크 ────────────────────────┘
```

> **스텁(stub)** — 원격 호출을 대신 처리해 주는 얇은 대리 함수.\
> 예: 위 도식처럼 클라이언트 스텁이 인자를 직렬화해 보내고, 서버 스텁이 풀어서 실제 함수를 호출한다.

> **직렬화(serialization) / 마샬링(marshalling)** — 메모리 안의 값을 네트워크로 보낼 수 있는 바이트 나열로 바꾸는 것.\
> 예: `42`라는 정수를 그대로 보낼 수는 없으니, 약속된 형식의 바이트로 바꿔 보낸다.

> **IDL(인터페이스 기술 언어)** — "이 서비스에는 어떤 함수가 있고 인자가 무엇인가"를 언어 중립적으로 적어 두는 문법.\
> 예: Sun RPC는 IDL로 인터페이스를 기술했고, 뒤의 gRPC는 `.proto`가 그 역할을 한다.

#### 대가는 무엇인가

이진 포맷에 자체 포트·portmapper가 필요해 **방화벽 통과가 어렵고**, 언어/플랫폼 결합이 강했다.

### SOAP (1998 XML-RPC → 2000 SOAP 1.1 → 2003 SOAP 1.2)

- **언제**: 1998년 6월 Dave Winer가 **XML-RPC**를 먼저 출시(Frontier 5.1).\
  같은 설계가 Microsoft 내부에서 SOAP으로 발전해 1999년 9월 IETF에 제출, **SOAP 1.1은 2000년 5월 8일 W3C Note**, **SOAP 1.2는 2003년 6월 24일 W3C 권고안**이 되었다.
- **왜**: 기업 환경에서 **HTTP(80포트)를 타고 방화벽을 통과하는 표준 RPC**가 필요했다.\
  XML로 메시지를 감싸(Envelope/Header/Body) 언어·플랫폼 중립성을 확보하고, WSDL(인터페이스 기술)·WS-* 표준군(보안·트랜잭션)으로 엔터프라이즈 요구를 충족했다.
- **무엇을 대체했나**: 플랫폼 종속적인 이진 RPC(CORBA·DCOM·Sun RPC)를 "HTTP+XML"로 대체.\
  (SOAP 1.2부터 "Simple Object Access Protocol"이라는 약어 풀이 자체를 폐기.)

```text
방화벽 앞에서 갈린 두 방식 — 대립축은 "자체 포트" vs "HTTP(80포트)"

이진 RPC (CORBA · DCOM · Sun RPC)
   호출 ──▶ [방화벽]  자체 포트 · portmapper가 필요하다 → 통과가 어렵다

SOAP
   호출 ──▶ [방화벽]  HTTP(80포트)를 탄다 → 통과한다
             |
             └─ 메시지는 XML 봉투(Envelope / Header / Body)로 감싼다
```

```xml
<!-- SOAP 요청: 한 번의 호출에 이만큼의 봉투가 필요했다 -->
<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope">
  <soap:Body>
    <getUser xmlns="http://example.com/users">
      <userId>42</userId>
    </getUser>
  </soap:Body>
</soap:Envelope>
```

> **봉투(Envelope)** — SOAP이 메시지를 감싸는 바깥 XML 구조. 안에 Header와 Body가 들어간다.\
> 예: 위 XML 블록 그대로 `<soap:Envelope>` 안에 `<soap:Body>`가 들어 있다.

> **WSDL** — SOAP 서비스의 인터페이스를 기술하는 문서 형식.\
> 예: 원문 표현대로 WSDL(인터페이스 기술)과 WS-* 표준군(보안·트랜잭션)이 엔터프라이즈 요구를 충족했다.

#### 대가는 무엇인가

XML 봉투가 **장황하고 무겁다.**

파싱 비용이 크고, WS-* 스택의 복잡도가 개발자를 짓눌렀다.

### REST (2000) — 무엇을 어떻게가 아니라 "무엇을"

- **언제**: 2000년, **Roy Fielding**의 UC Irvine 박사학위 논문 *Architectural Styles and the Design of Network-based Software Architectures* 5장에서 정의.\
  Fielding은 HTTP/1.1 명세 공동 저자이기도 했다.
- **왜**: REST는 새 프로토콜이 아니라 **HTTP를 원래 설계 의도대로 쓰자는 아키텍처 스타일**이다.\
  동사(메서드)를 새로 만들지 말고 HTTP가 이미 가진 `GET/POST/PUT/DELETE`를 쓰고, 모든 것을 **자원(URI)** 으로 모델링하며, 상태를 서버에 두지 말고(stateless) 표현(JSON/XML)을 주고받는다.
- **무엇을 대체했나**: SOAP의 무거운 봉투와 WS-* 복잡도를 걷어냈다.\
  `POST /getUserById`(RPC식)가 아니라 `GET /users/42`(자원식)로 사고를 전환시켰고, 캐시·URL·HTTP 상태코드 같은 웹 인프라를 공짜로 활용하게 했다.
- **결정적 동력**: 곧이어 **JSON**(§5)이 XML을 밀어내며, REST+JSON은 2000년대 후반 웹/모바일 API의 사실상 표준이 되었다.

```
SOAP (동작 중심)                REST (자원 중심)
POST /getUser     ─────────▶    GET    /users/42        조회
POST /createUser  ─────────▶    POST   /users           생성
POST /updateUser  ─────────▶    PUT    /users/42        수정
POST /deleteUser  ─────────▶    DELETE /users/42        삭제
(봉투+동사 이름)                 (HTTP 메서드 + URI)
```

> **자원(resource) / URI** — 다루려는 대상 하나하나와, 그것을 가리키는 주소.\
> 예: 위 블록의 `/users/42`가 "42번 사용자"라는 자원을 가리키는 URI다.

> **stateless(무상태)** — 서버가 이전 요청의 상태를 기억하지 않고, 요청 하나하나를 독립적으로 처리하는 성질.\
> 예: 원문 표현대로 "상태를 서버에 두지 말고" 표현(JSON/XML)을 주고받는다.

### gRPC (2015) — RPC로의 회귀, 그러나 이진으로

- **언제**: 2015년 Google이 발표.\
  사내 RPC 시스템(Stubby)을 오픈소스화한 것으로, 2017년 CNCF에 합류했다.
- **왜**: 마이크로서비스가 폭증하면서 **서비스 간 내부 통신**에는 REST+JSON의 텍스트 파싱 비용·장황함이 부담이 되었다.\
  gRPC는 두 가지 신기술 위에 섰다 — **HTTP/2**(2015 표준화, 다중화·헤더 압축·서버 스트리밍)와 **Protocol Buffers**(이진 직렬화·스키마/IDL).
- **무엇을 대체했나**: *내부* 서비스 통신에서 REST를 대체(외부 공개 API는 여전히 REST가 우세).\
  RPC 모델로 회귀했지만, Sun RPC 시절의 방화벽·플랫폼 문제는 HTTP/2와 코드 생성으로 해결했다.\
  `.proto` 한 파일에서 다국어 클라이언트/서버 스텁을 자동 생성한다.
- **킬러 기능**: HTTP/2 기반의 **양방향 스트리밍**(단일 요청-응답을 넘어선다)과, JSON 대비 작은 페이로드·빠른 파싱.

```protobuf
// gRPC는 .proto 계약(IDL)에서 출발한다 — 계약 우선(contract-first)
service UserService {
  rpc GetUser (UserRequest) returns (User);                  // 단항(unary)
  rpc ListUsers (UserRequest) returns (stream User);         // 서버 스트리밍
  rpc Chat (stream Message) returns (stream Message);        // 양방향 스트리밍
}
message UserRequest { int32 user_id = 1; }
message User { int32 id = 1; string name = 2; }
```

> **계약 우선(contract-first)** — 먼저 인터페이스 정의 파일을 쓰고, 거기서 양쪽 코드를 생성하는 방식.\
> 예: 위 블록의 `.proto` 한 파일에서 다국어 클라이언트/서버 스텁을 자동 생성한다.

> **양방향 스트리밍(bidirectional streaming)** — 한 호출 안에서 양쪽이 계속 메시지를 주고받는 것.\
> 예: 위 블록의 `rpc Chat (stream Message) returns (stream Message)`가 그 선언이다.

> **진자 운동의 의미**: RPC(함수 호출 추상화) → REST(자원·웹 친화) → gRPC(다시 RPC, 단 이진·스트리밍). 각 전환은 "무엇을 대체"했다기보다 **다른 문맥에 최적화**했다. 오늘날은 *외부 공개 API=REST, 내부 고성능=gRPC, 레거시 엔터프라이즈=SOAP*가 공존한다.

---

## 4. 실시간 통신 — 요청-응답을 넘어 (2011~)

HTTP의 근본 모델은 **클라이언트가 묻고 서버가 답하는** 단방향 요청-응답이다.

채팅·주식 시세·알림처럼 **서버가 먼저 보내야 하는** 시나리오에서는, 과거에 짧은 폴링(short polling)·롱 폴링·Comet 같은 우회책으로 버텼다.

2010년대 들어 이를 프로토콜 차원에서 푸는 세 갈래가 표준화되었다.

> **폴링(polling)** — 서버가 먼저 보낼 길이 없어, 클라이언트가 주기적으로 되묻는 방식.\
> 예: 새 메시지가 없어도 "새 거 있나요?"를 계속 물어봐야 하므로 지연과 낭비가 크다.

### WebSocket (RFC 6455, 2011) — 완전한 양방향

- **언제**: 2011년 RFC 6455로 IETF 표준화(HTML5 노력의 일부).
- **왜**: 브라우저와 서버 간 **하나의 지속 연결 위에서 전이중(full-duplex)** 통신을 하기 위해.\
  HTTP `Upgrade` 핸드셰이크로 시작해 TCP 연결을 WebSocket 프레임 채널로 전환한다(포트 80/443 그대로 사용 → 방화벽 친화적).
- **무엇을 대체했나**: 롱 폴링·Comet 같은 폴링 기반 우회책을 대체.\
  채팅·게임·협업 편집·실시간 대시보드의 표준 기반이 되었다.

```text
대립축은 "주기적 재요청" vs "하나의 지속 연결"

폴링 기반 우회책 (롱 폴링 · Comet)
   클라 ──"새 거 있나요?"──▶ 서버
   클라 ──"새 거 있나요?"──▶ 서버      매번 다시 물어야 한다
   클라 ──"새 거 있나요?"──▶ 서버

WebSocket
   클라 ── HTTP Upgrade 핸드셰이크 ──▶ 서버
   클라 ◀═══ 하나의 지속 연결 위에서 전이중 ═══▶ 서버
             포트 80/443을 그대로 쓴다 → 방화벽 친화적
```

> **전이중(full-duplex)** — 양쪽이 동시에 보내고 받을 수 있는 통신.\
> 예: 원문 표현대로 WebSocket은 "하나의 지속 연결 위에서 전이중" 통신을 한다.

> **Upgrade 핸드셰이크** — HTTP로 시작한 연결을 다른 프로토콜로 전환해 달라고 요청하는 절차.\
> 예: 아래 블록처럼 `Upgrade: websocket`을 보내면 서버가 `101 Switching Protocols`로 답한다.

```
# WebSocket 핸드셰이크: HTTP로 시작해 프로토콜을 "업그레이드"한다
C: GET /chat HTTP/1.1
C: Host: example.com
C: Upgrade: websocket
C: Connection: Upgrade
C: Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
C: Sec-WebSocket-Version: 13
S: HTTP/1.1 101 Switching Protocols
S: Upgrade: websocket
S: Connection: Upgrade
S: Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
# 이후로는 양방향 프레임 교환 (요청-응답 모델 탈피)
```

### SSE (Server-Sent Events) — 가벼운 단방향 푸시

- **언제**: HTML5의 일부로 표준화(W3C / WHATWG), 브라우저의 `EventSource` API로 노출.
- **왜**: 모든 실시간 시나리오가 양방향을 필요로 하진 않는다.\
  알림·피드·진행률처럼 **서버→클라이언트 단방향**이면 충분할 때, **표준 HTTP 위에서** 텍스트 이벤트 스트림(`text/event-stream`)을 흘려보낸다.
- **무엇을 대체했나(보완)**: WebSocket의 대안.\
  자동 재연결·이벤트 ID·HTTP 인프라(프록시·인증) 호환이 장점이라, "서버가 보내기만 하면 되는" 경우 WebSocket보다 단순하다.\
  WebSocket과 경쟁이라기보다 **용도 분담**이다.

```
WebSocket  ◀═══════▶  양방향, 이진/텍스트 프레임, Upgrade 필요   (채팅·게임)
SSE        ◀──────    단방향(서버→클라), 텍스트, 순수 HTTP        (알림·피드)
폴링        ──○──○──   주기적 재요청, 지연·낭비 큼               (레거시 우회)
```

### MQTT (1999 / OASIS 2014) — IoT를 위한 경량 pub/sub

- **언제**: **1999년**, IBM의 **Andy Stanford-Clark**와 Arcom(현 Eurotech)의 **Arlen Nipper**가 발명.\
  2010년 로열티 프리 공개, **2014년 OASIS 표준**(MQTT 3.1.1, 10월 29일), 이후 ISO/IEC 20922.
- **왜**: 원래 **사막의 송유관 센서 데이터를 위성 링크로 SCADA 시스템에 보내는** 문제에서 출발했다.\
  대역폭이 좁고 비싸며 연결이 불안정한 환경 — 곧 IoT의 조건이다.\
  그래서 헤더가 **2바이트로 시작하는 극도로 경량한 이진 프로토콜**, 그리고 직접 연결 대신 **브로커 기반 pub/sub**을 택했다.
- **무엇을 대체했나**: 무겁고 요청-응답 중심인 HTTP를, 저전력·저대역폭 IoT 영역에서 대체.\
  발행자(센서)와 구독자(서버)가 **토픽**으로 느슨하게 결합되고, **QoS 0/1/2**(전달 보증 수준)와 Last Will(연결 끊김 통지)로 불안정한 네트워크를 견딘다.

```
        publish "sensor/temp" = 23.5
센서A ──────────────┐
                    ▼
센서B ──▶  ┌──────────────────┐  subscribe "sensor/#"
           │   MQTT Broker     │ ──────────────▶  서버/대시보드
센서C ──▶  └──────────────────┘ ──────────────▶  모바일 앱
        (발행자와 구독자는 서로를 모른다 — 토픽으로만 결합)
```

> **브로커(broker)** — 발행자와 구독자 사이에서 메시지를 중계하는 서버.\
> 예: 위 블록의 MQTT Broker가 그것이다 — 발행자와 구독자는 서로를 모르고 토픽으로만 결합된다.

> **QoS(전달 보증 수준)** — 메시지를 얼마나 확실히 전달할지 정하는 등급.\
> 예: MQTT는 QoS 0/1/2를 두어, 불안정한 네트워크에서 전달 보증 수준을 고를 수 있게 한다.

> NNTP(§1)의 pub/sub 아이디어가 30년 뒤 IoT 문맥에서 극단적 경량화로 부활한 셈이다. 메시지 배포라는 문제의식은 같고, 제약(대역폭·전력)이 설계를 다시 빚었다.

---

## 5. 직렬화 포맷의 변천 — XML에서 protobuf로

프로토콜이 "대화의 규칙"이라면, 직렬화 포맷은 "그 안에 담기는 데이터의 표현"이다.

위의 모든 흐름(SOAP·REST·gRPC) 밑바닥에는 직렬화 포맷의 세대교체가 깔려 있다.

```text
세 세대가 무엇을 바꿨나

XML (1998)       SGML을 단순화한 자기 기술적 구조화 데이터
   |
   | 문제: 장황하다 — 닫는 태그·네임스페이스·속성으로 페이로드가 부풀고 파싱이 무겁다
   v
JSON (2006)      브라우저가 별도 파서 없이 곧바로 다루는 경량 포맷
   |
   | 문제: 텍스트라 파싱이 느리고 크기가 크다
   v
protobuf (2008)  스키마를 먼저 정의하고 필드를 숫자 태그로 인코딩한 이진 포맷
```

### XML (W3C 권고, 1998) — 구조의 시대

- **언제**: 1998년 2월 10일 XML 1.0이 W3C 권고안.
- **왜**: SGML을 단순화해 **사람도 기계도 읽는 자기 기술적(self-describing) 구조화 데이터**를 만들기 위해.\
  스키마(XSD)·네임스페이스·검증·변환(XSLT)까지 갖춘 강력한 생태계를 이뤘고, SOAP·RSS·설정 파일의 토대가 되었다.

> **자기 기술적(self-describing)** — 데이터 자체가 각 값이 무엇인지 이름을 달고 있는 성질.\
> 예: `<name>Alice</name>`은 값 옆에 그것이 이름이라는 설명이 붙어 있다.

> **스키마(schema)** — 데이터가 어떤 필드와 타입으로 이뤄져야 하는지 정해 둔 규격.\
> 예: XML은 XSD, protobuf는 `.proto` 파일이 그 역할을 한다.

#### 대가는 무엇인가

**장황하다.**

닫는 태그·네임스페이스·속성으로 페이로드가 부풀고, 파싱(DOM/SAX)이 무겁다.\
모바일·AJAX 시대의 가벼움 요구와 충돌했다.

### JSON (RFC 4627, 2006 → RFC 8259, 2017) — 가벼움의 시대

- **언제**: **Douglas Crockford**가 2001년경 JavaScript 객체 리터럴의 부분집합으로 정리, **2006년 7월 RFC 4627**, **2017년 RFC 8259**(및 ECMA-404)로 표준화.
- **왜**: AJAX와 자바스크립트 웹의 부상으로, **브라우저가 별도 파서 없이 곧바로 다루는** 경량 포맷이 필요했다.\
  객체(`{}`)·배열(`[]`)·기본 타입만으로 구성돼 XML보다 훨씬 간결하고 파싱이 빠르다.
- **무엇을 대체했나**: 웹 API의 데이터 포맷에서 XML을 대체.\
  REST의 부상과 맞물려 **REST+JSON**이 2010년대 웹/모바일 API의 표준이 되었다.

```
XML (1998)                          JSON (2006)
<user>                              {
  <id>42</id>                         "id": 42,
  <name>Alice</name>                  "name": "Alice",
  <roles>                             "roles": ["admin", "user"]
    <role>admin</role>              }
    <role>user</role>
  </roles>                          # 같은 데이터, 훨씬 적은 바이트
</user>
```

### Protocol Buffers (Google, 오픈소스 2008) — 효율의 시대

- **언제**: Google이 사내에서 쓰던 이진 직렬화 포맷을 **2008년 오픈소스로 공개**.\
  2015년 gRPC의 기본 직렬화로 채택되며 널리 퍼졌다.
- **왜**: JSON·XML은 **텍스트**라 파싱이 느리고 크기가 크다.\
  protobuf는 **스키마(`.proto`)를 먼저 정의**하고, 필드를 이름이 아닌 **숫자 태그**로 인코딩해 이진으로 압축한다.\
  같은 데이터를 JSON 대비 훨씬 작게, 빠르게 직렬화한다.
- **무엇을 대체했나(보완)**: 사람이 읽을 필요가 없는 **서비스 간 내부 통신**에서 JSON을 대체.

> **숫자 태그(field number)** — 필드를 이름 대신 번호로 표시하는 방식.\
> 예: 앞의 `.proto` 블록에서 `int32 user_id = 1;`의 `1`이 그 번호다 — 전송할 때는 이름 대신 이 번호가 나간다.

#### 대가는 무엇인가

사람이 읽기 어렵고 스키마 없이는 해석 불가하다.

그래서 **공개 API의 디버깅 친화적 영역은 여전히 JSON** 차지다.

```
직렬화 포맷의 트레이드오프
                  사람 가독성    크기/속도      스키마
XML    (1998)        ◐          느림·큼        강함(XSD)
JSON   (2006)        ●          중간           약함(옵션)
protobuf(2008)       ○          빠름·작음      강제(.proto)
                  └─ 외부 공개·디버깅      내부 고성능 통신 ─┘
```

> **순환하는 역사**: 텍스트(읽기 쉬움) ↔ 이진(효율) 사이를 응용 계층은 계속 오간다. 초기 텍스트 프로토콜(§1)이 상호운용을 위해 텍스트를 택했고, JSON이 가독성으로 XML을 이겼지만, 성능이 중요한 내부에서는 다시 이진(protobuf)으로 회귀했다. "정답"은 없고 **문맥(외부/내부, 가독성/성능)** 이 포맷을 정한다.

---

## 영향과 의의

*(이 편의 「왜 그렇게 갔나」에 해당한다)*

응용 계층 프로토콜의 역사는 몇 가지 반복되는 긴장의 기록이다.

1. **단순함 ↔ 보안**: 1세대 텍스트 프로토콜은 상호운용을 위해 평문을 택했고, 그 단순함이 곧 취약점이었다.\
   SSH가 "암호화는 기본값"을 각인시킨 뒤 TLS·HTTPS 전면화로 이어졌다.
2. **추상화 ↔ 효율**: RPC는 원격을 로컬처럼 보이게 추상화했고(SOAP), REST는 웹 인프라를 그대로 쓰는 자원 모델로 단순화했으며, gRPC는 성능을 위해 다시 이진 RPC로 돌아왔다.\
   진자는 한 방향으로만 가지 않는다.
3. **요청-응답 ↔ 푸시/스트리밍**: HTTP의 단방향 모델을 WebSocket(양방향)·SSE(단방향 푸시)·MQTT(pub/sub)가 각자의 문맥에서 보완했다.
4. **가독성 ↔ 압축**: XML→JSON→protobuf의 흐름은 텍스트와 이진 사이의 영원한 트레이드오프를 보여준다.

## 남긴 것 — 오늘 우리가 쓰는 것

원문의 「영향과 의의」가 적은, 오늘 한 시스템 안에서 **공존**하는 세대들이다.

- 메일은 여전히 **SMTP/IMAP**으로 오간다.
- 서버 접속은 **SSH**로 한다.
- 외부 API는 **REST+JSON**으로 한다.
- 내부 마이크로서비스는 **gRPC+protobuf**로 통신한다.
- 실시간 알림은 **WebSocket/SSE**로 보낸다.
- IoT 센서는 **MQTT**로 통신한다.

새 프로토콜은 옛것을 완전히 지우기보다 **새로운 제약(보안·실시간·저전력·고성능)이 생길 때마다 그 문맥에 최적화된 한 겹을 더한다.**\
이것이 응용 계층 50여 년의 진화 방식이다.

## 용어 풀이

- **응용 계층(application layer)** — 프로그램끼리 주고받는 메시지의 뜻을 정하는 계층.
- **프로토콜(protocol)** — 두 프로그램이 통신하려고 미리 정해 둔 절차와 형식.
- **ASCII** — 영문자·숫자·기호를 숫자로 대응시킨 문자 인코딩.
- **NVT(Network Virtual Terminal)** — 서로 다른 호스트가 공통으로 가정하는 가상 터미널. 텍스트 프로토콜 계보의 출발점.
- **응답코드** — 결과를 숫자로 알리는 값(2xx 성공, 3xx 추가 입력, 4xx/5xx 오류).
- **Telnet(RFC 854, 1983)** — 원격 터미널 로그인 프로토콜. 포트 23. `WILL`/`WONT`/`DO`/`DONT`로 옵션을 협상한다.
- **FTP(RFC 959, 1985)** — 파일 전송 프로토콜. 제어 연결은 포트 21, 데이터 연결은 포트 20.
- **SMTP(RFC 821, 1982 / RFC 5321, 2008)** — 메일 서버 간 전송 프로토콜. `HELO`·`MAIL FROM`·`RCPT TO`·`DATA`.
- **ESMTP** — RFC 5321로 갱신되며 더해진 확장(`EHLO`, 인증, TLS 협상).
- **MTA(Mail Transfer Agent)** — 메일을 서버에서 서버로 옮기는 프로그램.
- **POP3(RFC 1939, 1996)** — 메일을 내려받고 서버에서는 지우는 수신 프로토콜.
- **IMAP4rev1(RFC 3501, 2003)** — 메일을 서버에 두고 폴더·플래그·검색을 서버가 관리하는 수신 프로토콜. Mark Crispin이 1986년 설계.
- **NNTP(RFC 977, 1986 / RFC 3977, 2006)** — Usenet 뉴스 배포 프로토콜. 포트 119.
- **UUCP** — NNTP 이전의 전화선 기반 store-and-forward 방식.
- **pub/sub(발행-구독)** — 주제를 기준으로 발행자와 구독자가 느슨하게 이어지는 배포 방식.
- **SSH(1995, Tatu Ylönen / SSH-2: RFC 4251·4253, 2006)** — 암호화된 원격 접속 프로토콜. Telnet·rlogin·rsh·평문 FTP를 대체했다.
- **채널 다중화** — 하나의 암호화 연결 위에 셸·SFTP·포트 포워딩 등 여러 통로를 얹는 것.
- **SFTP / SCP** — SSH 위에서 도는 보안 파일 전송.
- **RPC(Remote Procedure Call)** — 네트워크 너머의 함수를 로컬 함수처럼 호출하는 방식. 1984년 Birrell·Nelson 논문.
- **스텁(stub)** — 원격 호출을 대신 처리하는 대리 함수. 인자를 직렬화해 보낸다.
- **직렬화 / 마샬링** — 메모리 안의 값을 네트워크로 보낼 바이트 나열로 바꾸는 것.
- **XDR** — Sun RPC가 데이터를 언어 중립적으로 인코딩하는 방식.
- **IDL(인터페이스 기술 언어)** — 서비스의 함수와 인자를 언어 중립적으로 적어 두는 문법.
- **Sun RPC(ONC RPC, RFC 1057·1831)** — NFS의 기반이 된 이진 RPC.
- **XML-RPC(1998, Dave Winer)** — SOAP의 전신. HTTP 위에 XML로 RPC를 실었다.
- **SOAP(1.1: 2000 / 1.2: 2003)** — XML 봉투(Envelope/Header/Body)로 감싼 HTTP 기반 RPC 표준.
- **WSDL / WS-*** — SOAP의 인터페이스 기술 문서 / 보안·트랜잭션 표준군.
- **REST(2000, Roy Fielding)** — HTTP를 설계 의도대로 쓰자는 아키텍처 스타일. 자원(URI) + HTTP 메서드.
- **stateless(무상태)** — 서버가 요청 사이의 상태를 기억하지 않는 성질.
- **gRPC(2015, Google)** — HTTP/2와 Protocol Buffers 위에 선 고성능 RPC. 2017년 CNCF 합류.
- **계약 우선(contract-first)** — 인터페이스 정의 파일에서 출발해 양쪽 코드를 생성하는 방식.
- **폴링(polling) / 롱 폴링 / Comet** — 서버 푸시가 없던 시절의 주기적 재요청 우회책.
- **WebSocket(RFC 6455, 2011)** — HTTP `Upgrade`로 시작해 전이중 프레임 채널로 전환하는 프로토콜. 포트 80/443.
- **전이중(full-duplex)** — 양쪽이 동시에 보내고 받을 수 있는 통신.
- **SSE(Server-Sent Events)** — 순수 HTTP 위의 서버→클라이언트 단방향 텍스트 이벤트 스트림. `EventSource` API.
- **MQTT(1999 / OASIS 2014)** — 헤더가 2바이트로 시작하는 경량 이진 pub/sub 프로토콜. Andy Stanford-Clark·Arlen Nipper.
- **브로커(broker)** — 발행자와 구독자 사이에서 메시지를 중계하는 서버.
- **토픽(topic)** — MQTT에서 발행자와 구독자를 느슨하게 잇는 주제 이름.
- **QoS 0/1/2** — MQTT의 전달 보증 수준.
- **Last Will** — MQTT의 연결 끊김 통지.
- **XML(W3C 권고, 1998)** — 자기 기술적 구조화 데이터 포맷. XSD·네임스페이스·XSLT 생태계.
- **JSON(RFC 4627, 2006 / RFC 8259, 2017)** — 객체·배열·기본 타입만의 경량 텍스트 포맷. Douglas Crockford.
- **Protocol Buffers(오픈소스 2008)** — 스키마를 먼저 정의하고 필드를 숫자 태그로 인코딩하는 이진 직렬화.
- **스키마(schema)** — 데이터가 어떤 필드와 타입으로 이뤄져야 하는지 정한 규격.

---

## 참고 출처

**텍스트 시대**
- [RFC 854: Telnet Protocol Specification (1983)](https://www.rfc-editor.org/rfc/rfc854.html)
- [RFC 959: File Transfer Protocol (1985)](https://datatracker.ietf.org/doc/rfc959/)
- [RFC 821: Simple Mail Transfer Protocol (1982)](https://www.rfc-editor.org/rfc/rfc821.html)
- [RFC 5321: Simple Mail Transfer Protocol (2008, SMTP 갱신)](https://datatracker.ietf.org/doc/html/rfc5321)
- [RFC 1939: Post Office Protocol - Version 3 (1996)](https://www.ietf.org/rfc/rfc1939.txt)
- [RFC 3501: Internet Message Access Protocol - Version 4rev1 (2003)](https://datatracker.ietf.org/doc/html/rfc3501)
- [RFC 977: Network News Transfer Protocol (1986)](https://www.rfc-editor.org/rfc/rfc977.html)
- [RFC 3977: Network News Transfer Protocol (2006)](https://datatracker.ietf.org/doc/html/rfc3977)

**보안 시대**
- [Secure Shell - Wikipedia (SSH 역사·Tatu Ylönen, 1995)](https://en.wikipedia.org/wiki/Secure_Shell)
- [RFC 4251: The Secure Shell (SSH) Protocol Architecture](https://datatracker.ietf.org/doc/html/rfc4251)
- [RFC 4253: The Secure Shell (SSH) Transport Layer Protocol](https://datatracker.ietf.org/doc/html/rfc4253)

**원격 호출**
- [RFC 1057: RPC: Remote Procedure Call Protocol Version 2 (Sun RPC, 1988)](https://www.rfc-editor.org/rfc/rfc1057.html)
- [RFC 1831: RPC: Remote Procedure Call Protocol Version 2 (ONC RPC, 1995)](https://www.rfc-editor.org/rfc/rfc1831.html)
- [SOAP - Wikipedia (XML-RPC 1998, SOAP 1.1 2000, SOAP 1.2 2003)](https://en.wikipedia.org/wiki/SOAP)
- [Roy Fielding, Architectural Styles... Ch.5 REST (2000)](https://www.ics.uci.edu/~fielding/pubs/dissertation/rest_arch_style.htm)
- [gRPC - Capital One Tech (gRPC 2015·HTTP/2·protobuf)](https://www.capitalone.com/tech/software-engineering/grpc-framework-for-microservices-communication/)

**실시간 통신**
- [RFC 6455: The WebSocket Protocol (2011)](https://datatracker.ietf.org/doc/html/rfc6455)
- [WebSocket vs SSE (websocket.org)](https://websocket.org/comparisons/sse/)
- [MQTT - Wikipedia (1999 Stanford-Clark·Nipper, OASIS 2014)](https://en.wikipedia.org/wiki/MQTT)
- [A Brief History of MQTT (Paessler)](https://blog.paessler.com/a-brief-history-of-mqtt)

**직렬화**
- [XML - Wikipedia (W3C 권고 1998)](https://en.wikipedia.org/wiki/XML)
- [RFC 4627: The application/json Media Type (2006)](https://www.rfc-editor.org/rfc/rfc4627.html)
- [RFC 8259: The JavaScript Object Notation (JSON) (2017)](https://www.rfc-editor.org/rfc/rfc8259.html)
- [Protocol Buffers (Google Developers)](https://protobuf.dev/)
