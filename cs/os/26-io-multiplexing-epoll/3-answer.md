# os/26-io-multiplexing-epoll — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-30). 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 정답

### 1. select·poll이 느린 이유

- 앱: 호출마다 감시 목록 전체(비트맵·배열)를 만들어 넘긴다. 돌아오면 전체를 다시 훑어 준비된 fd를 찾는다.
- 커널: 넘겨받은 목록 전체를 복사하고, fd마다 준비 여부를 검사하고, 결과 전체를 다시 복사해 준다.
- 준비된 것이 1개여도 비용은 감시 수 N에 비례한다(O(n)).
- 로컬 재현(예시, 리눅스 7.0): 준비된 fd 1개 기준 poll은 N=1000에서 약 87µs, N=10000에서 약 4.5ms였다. epoll_wait는 N과 무관하게 1µs 미만이었다.

### 2. FD_SETSIZE 1024

- **glibc 한계**다. 커널은 고정 한계가 없지만, glibc가 `fd_set`을 1024비트 고정 타입으로 정의하고 `FD_*` 매크로도 그 한계로 동작한다(select(2) BUGS).
- 1024 이상에 `FD_SET`하면 **정의되지 않은 동작**이다(select(2) NOTES).
  - `_FORTIFY_SOURCE` 빌드: `*** bit out of range 0 - FD_SETSIZE on fd_set ***: terminated`로 abort, exit 134(로컬 재현).
  - 보호 없는 빌드: 아무 에러 없이 스택의 다른 값을 덮을 수 있다.
- `ulimit -n`은 fd를 **더 많이 열게** 해 줄 뿐이다. 번호가 1024를 넘는 순간 오히려 이 문제가 드러난다. 해결은 poll·epoll로 바꾸는 것이다.

### 3. epoll 내부

```text
  eventpoll 객체
  ├─ 관심 목록: 레드블랙 트리 (키 = fd + open file description)
  └─ 준비 목록: 이중 연결 리스트

  epoll_ctl(ADD, fd 9)  -> 트리에 항목 추가 + 소켓 9의 대기 큐에 ep_poll_callback 등록
  패킷 도착             -> 커널이 소켓 9 수신 버퍼에 넣고 대기 큐를 깨움
                        -> ep_poll_callback이 fd 9 항목을 준비 목록 꼬리에 붙임
                        -> epoll_wait에서 잠든 스레드를 깨움
  epoll_wait            -> 준비 목록에서 꺼내 사용자 배열에 복사해 반환
```

- 근거: fs/eventpoll.c 개요 주석, `struct rb_root_cached rbr`, `rdllist`.

### 4. LT vs ET — 1KB 남은 상태

- **레벨 트리거**: 즉시 다시 "준비됨"을 돌려준다. 읽을 데이터가 남은 상태이기 때문이다.
- **엣지 트리거**: 알림이 없다. 2KB 도착이라는 변화는 첫 `epoll_wait`에서 소비됐다. 새 데이터가 와야 다시 알린다. 상대가 응답을 기다리며 아무것도 안 보내면 영원히 기다린다(epoll(7) "probably hang").
- 로컬 재현(예시, 리눅스 7.0): LT `wait2=1`, ET `wait2=0`. ET에서 1B가 새로 오자 알림이 오고 남은 1024B + 1B = 1025B를 한 번에 읽었다.
- 구현 차이: `epoll_wait`가 이벤트를 돌려줄 때 LT 항목은 준비 목록에 **다시 넣고**, ET 항목은 넣지 않는다(fs/eventpoll.c "re-queueing items in level-triggered mode", `!(epi->event.events & EPOLLET)` 분기).

### 5. ET 사용 규칙과 부작용

- 규칙(epoll(7))
  1. fd를 **논블로킹**으로 둔다. 안 그러면 "끝까지 읽기"의 마지막 read가 스레드를 재운다.
  2. `read`/`write`가 **`EAGAIN`을 돌려준 뒤에만** 다시 기다린다.
- 부작용: 한 연결이 계속 보내면 그 연결을 비우느라 다른 연결이 굶는다(starvation).
- 대처: 앱 쪽에 준비 목록을 두고, 각 연결에서 조금씩 처리한 뒤 준비 표시만 남기고 다음 연결로 돌아가며(round robin) 처리한다(epoll(7) "Possible pitfalls").

### 6. ET hang 확정 방법

- `ss -tn`(또는 `ss -tnp`)으로 멈춘 연결을 보면 **Recv-Q가 0이 아닌 채 그대로**다. 커널 수신 버퍼에 데이터가 있는데 앱이 안 읽고 있다.
- `strace -e trace=read,epoll_wait -p <pid>`에서 그 fd에 대한 `read`가 더 이상 없다. 다른 fd 이벤트는 정상이다.
- 코드에서 ET 등록(`EPOLLET`) 후 `EAGAIN`까지 읽지 않는 경로를 찾는다.

### 7. EPOLLOUT 바쁜 루프

- 원인: 소켓 송신 버퍼에 여유가 있으면 "쓰기 가능"은 거의 늘 참이다. LT는 참인 상태를 매번 알린다. 그래서 쓸 게 없어도 `epoll_wait`가 즉시 반환한다.
- 로컬 재현(예시, 리눅스 7.0): LT로 `EPOLLIN|EPOLLOUT`을 등록만 해 두니 1초에 약 330만 번 깨어났다.
- 규칙: 보낼 데이터가 남았을 때만 `EPOLLOUT`을 켜고, 다 보내면 `EPOLL_CTL_MOD`로 끈다. NIO의 `OP_WRITE`도 같다.

### 8. 닫은 fd로 오는 이벤트

- 관심 목록의 키는 fd 번호가 아니라 **(fd, open file description)** 이다. 항목은 그 open file description을 가리키는 **모든** fd가 닫혀야 빠진다(epoll(7) Q&A).
- `fork()`한 자식이나 라이브러리가 `dup()`한 복사본이 살아 있으면 `close(fd)`로는 안 빠진다. 이벤트는 등록 당시의 `data`(fd 번호)로 계속 온다. 그 번호가 새 연결에 재사용됐다면 엉뚱한 연결로 처리된다.
- 예방
  1. `close` 전에 `epoll_ctl(EPOLL_CTL_DEL)`을 한다.
  2. fd·epfd를 `*_CLOEXEC`로 만들어 exec된 자식에게 새지 않게 한다. 라이브러리의 숨은 dup·fork를 점검한다.

### 9. 여러 워커와 한 리슨 소켓

- 문제: 새 연결 하나에 모든 워커의 epfd가 깨어난다(기본 동작). 하나만 `accept`에 성공하고 나머지는 `EAGAIN`으로 헛걸음한다. thundering herd다.
- 해법
  1. `EPOLLEXCLUSIVE`(리눅스 4.5+): 같은 대상에 걸린 epfd 중 하나 이상만 깨운다(epoll_ctl(2)).
  2. `SO_REUSEPORT`(3.9+): 워커마다 별도 리슨 소켓을 같은 포트에 bind하고 커널이 연결을 나눠 준다(socket(7)).
- nginx는 이 둘이 있으면 `accept_mutex`가 필요 없다고 적고, 1.11.3부터 기본을 off로 바꿨다.

### 10. NIO와 Netty의 기본

- **Java NIO Selector**: 리눅스 OpenJDK는 `EPollSelectorProvider`를 쓰고, 등록에 `EPOLLET`을 붙이지 않는다 → **레벨 트리거**. 덜 읽어도 다음 `select()`에서 다시 알려 준다. 대신 `OP_WRITE`를 켜 둔 채 두면 7번의 바쁜 루프가 난다.
- **Netty epoll 전송**: 기본 **엣지 트리거**(`AbstractEpollChannel`의 `flags = Native.EPOLLET`). Netty가 내부에서 "끝까지 읽기"를 책임진다. `EpollMode.LEVEL_TRIGGERED`로 바꿀 수 있다.
- 의미: 직접 NIO 루프를 짤 때는 LT 규칙(관심 비트 끄고 켜기)을, 네이티브 epoll을 직접 쓸 때는 ET 규칙(`EAGAIN`까지)을 지켜야 한다.
