# cs/resp-protocol — RESP: Redis 유선 프로토콜 — 정리 (힌트)

> 복습 시 이 파일은 **질문에 막혔을 때만** 연다. 먼저 읽고 답하면 인출이 아니라 받아쓰기다.
> 원고는 deploy-study-note/docs/cs/RESP.md(2026-09 프로젝트 작업 중 정리) — 이관하며 이 자리로 옮겼다.
> 기준 소스는 코드다: ci-cd `internal/shared/logger.go`의 `respArray` + 소켓 쓰기.

## 한 줄

RESP(REdis Serialization Protocol)는 **클라이언트와 Redis가 TCP 위에서 주고받는
텍스트 규격**이다. "명령을 어떻게 바이트로 적어 보내고, 응답을 어떻게 읽는가"의 약속.

## 왜 알아야 했나

ci-cd 서버(Go)가 로그 규약(XADD 한 명령)을 지키려는데, 그 하나를 위해 redis 클라이언트
라이브러리를 통째로 들이는 건 과잉이었다. 프로토콜을 보니 — 그냥 줄 단위 텍스트였다.

## 형태 — 다섯 가지 타입, 첫 글자가 타입표시

```
+OK\r\n                단순 문자열 (성공 응답)
-ERR unknown\r\n       에러
:42\r\n                정수
$5\r\nhello\r\n        벌크 문자열 — $길이 먼저, 그 다음 내용 (바이너리도 안전)
*3\r\n...              배열 — *개수 먼저, 이어서 요소들
```

**명령 = 문자열 배열**이다. `XADD logs * level info line hi`는:

```
*8\r\n                 ← 요소 8개짜리 배열
$4\r\nXADD\r\n         ← 각 요소는 $길이 + 내용
$4\r\nlogs\r\n
$6\r\nMAXLEN\r\n
$1\r\n~\r\n
$5\r\n10000\r\n
$1\r\n*\r\n
$5\r\nlevel\r\n ...
```

이 문자열을 TCP 소켓에 쓰면 끝. 응답은 `$19\r\n1787...-0\r\n`(생성된 엔트리 id).

## 우리 구현 (ci-cd internal/shared/logger.go)

```go
func respArray(parts ...string) string {
    result := fmt.Sprintf("*%d\r\n", len(parts))
    for _, part := range parts {
        result += fmt.Sprintf("$%d\r\n%s\r\n", len(part), part)
    }
    return result
}
// net.DialTimeout → connection.Write(respArray("XADD", ...)) → 끝
```

- **$길이 방식의 의미**: 내용에 개행·한글·무엇이 들어도 길이만 맞으면 안전
  (구분자 파싱이 아니라 길이 파싱 — 이스케이프 지옥이 없다).
- 응답은 읽기만 하고 버린다 — 로그는 best-effort(실패 무해 규약)라서.

## 언제 라이브러리를 쓰나

명령 몇 개·단방향이면 직접 쓰기가 더 싸다. 반대로 **커넥션 풀·재연결·파이프라이닝·
pub/sub 구독** 같은 상태 관리가 필요해지는 순간 라이브러리(예: go-redis)가 맞다 —
프로토콜이 아니라 그 위의 운영이 어려운 부분이기 때문.

## 곁가지

- RESP는 사람이 `telnet`으로도 칠 수 있을 만큼 단순한 게 설계 목표였다(디버깅 용이).
- RESP3(Redis 6+)는 맵·불리언 등 타입을 늘렸지만, RESP2 명령은 그대로 통한다 —
  우리가 쓴 것도 RESP2.

## 핵심 문장

- RESP = TCP 위 텍스트 규격. 첫 글자가 타입(`+ - : $ *`).
- 명령은 벌크 문자열들의 배열(`*N` + `$len\r\n내용`).
- 길이 파싱이라 이스케이프가 없다 → 개행·한글·바이너리 안전.
- 명령 몇 개·단방향이면 직접 짜기가 싸고, 풀·재연결·pub/sub이 필요해지면 라이브러리.
