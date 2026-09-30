# os/34-zero-copy-and-io-uring — 정답

> 복습 시 이 파일은 **최후에만** 연다.
> ⚠️ 이 정답은 Claude 초안(2026-09-30). 본인 검수 후 이 줄을 `✅ 검수 완료(날짜)`로 바꾼다.

## 정답

### 1. read + write의 네 번 복사

```text
  ① 디스크 --DMA--> 페이지 캐시
  ② 페이지 캐시 --CPU--> 사용자 버퍼          (read)
  ③ 사용자 버퍼 --CPU--> 소켓 버퍼            (write)
  ④ 소켓 버퍼 --DMA--> NIC
  모드 전환: read·write 각각 진입·복귀 = 4번
```

- DMA 복사는 장치가 하므로 CPU 시간이 거의 안 든다.
- 아까운 것은 ②·③ **CPU 복사**다. 앱은 데이터를 보지도 고치지도 않는데 CPU 시간·메모리 대역폭·캐시를 쓴다(Linux Journal 2003).

### 2. 방식별 CPU 복사

| 방식 | CPU 복사 | 비고 |
|---|---|---|
| read + write | 2 | 기준 |
| mmap + write | 1 | 페이지 캐시를 사용자 공간과 공유해 ②가 사라짐. `write`의 ③은 남음 |
| sendfile, gather 미지원 NIC | 1 | 페이지 캐시 → 소켓 버퍼 복사가 커널 안에서 1번. 사용자 공간 왕복·모드 전환은 줄어든다 |
| sendfile, gather 지원 NIC | 0 | 소켓 버퍼에 위치·길이만 붙이고 NIC가 페이지 캐시에서 직접 DMA |

- mmap 방식의 위험: 매핑한 파일을 다른 프로세스가 잘라내면 없어진 페이지를 건드리게 된다. 앱이 매핑을 직접 읽으면 **SIGBUS**로 프로세스가 죽는다(기본 동작). `write`에 넘긴 경우 Linux Journal(2003)은 SIGBUS라 적었지만, 리눅스 7.0 로컬 재현에서는 `write`가 `-1 EFAULT`를 돌려줬다.

### 3. sendfile의 경계

- `in_fd`: mmap 비슷한 동작을 지원하는 파일이어야 한다. **소켓은 안 된다**(sendfile(2)).
- `out_fd`: 리눅스 2.6.33 전에는 소켓만, 그 뒤로는 아무 파일이나 된다. 5.12부터 `out_fd`가 파이프면 내부적으로 splice가 된다.
- 한 번 호출로 최대 `0x7ffff000`(2,147,479,552)바이트까지 보낸다. 그리고 요청보다 적게 보낼 수 있다. 3GB는 한 번에 안 된다. 반환값만큼 오프셋을 전진시키며 반복해야 한다.

### 4. TLS와 zero-copy

- TLS는 평문이 아니라 **암호화된 레코드**를 보낸다. 누군가 데이터를 읽어 암호화해야 한다. 사용자 공간 TLS(OpenSSL 기본)면 데이터를 사용자 공간으로 올려 암호화한 뒤 다시 소켓에 쓴다. 파일 → 소켓 직행인 sendfile을 쓸 수 없다.
- **kTLS**가 되찾는 것: 사용자 공간 왕복. 키를 커널 소켓에 넘기면 `sendfile`이 파일 데이터를 TLS 레코드(최대 2^14바이트)로 보낸다(커널 문서 networking/tls). OpenSSL 3.0 `SSL_sendfile`, nginx 1.21.4+가 이 경로를 쓴다.
- 못 되찾는 것: **암호화 CPU 패스**. 커널이 데이터를 읽어 암호화한다.
- 진짜 zero-copy: NIC TLS **오프로드** + `TLS_TX_ZEROCOPY_RO`. NIC가 암호화하고 커널 안 복사도 없앤다. 대신 전송이 끝날 때까지 원본이 바뀌면 원 전송과 재전송이 다른 데이터가 될 수 있다(커널 문서 경고).

### 5. io_uring 링

```text
  SQ(제출): 앱 = 생산자, tail을 올림 / 커널 = 소비자, head를 올림
  CQ(완료): 커널 = 생산자, tail을 올림 / 앱 = 소비자, head를 올림
  링과 SQE 배열은 mmap으로 공유
```

- 링마다 쓰는 쪽이 하나, 읽는 쪽이 하나다(단일 생산자·단일 소비자). 생산자만 tail을, 소비자만 head를 쓴다. 그래서 두 쪽이 같은 변수를 동시에 고칠 일이 없어 락이 필요 없다.
- 대신 순서를 지켜야 한다. "항목을 다 쓴 뒤 tail 공개"(release), "tail을 읽은 뒤 항목 읽기"(acquire)를 메모리 배리어로 보장한다(Axboe 2019 §4.0, io_uring(7)).

### 6. 완료 순서와 짝짓기

- 그렇다. 완료는 제출 순서와 **무관하게** 올 수 있다(io_uring(7), Axboe §4.2). B가 캐시에 있고 A가 디스크를 기다리면 B가 먼저 끝난다.
- 앱은 SQE의 `user_data`에 요청 식별자(보통 요청 객체 포인터)를 넣는다. 커널은 이 값을 건드리지 않고 CQE에 그대로 복사한다. 앱은 CQE의 `user_data`로 원래 요청을 찾는다.

### 7. 시스템 콜 줄이기와 SQPOLL

- 기본 모드: 여러 SQE를 링에 쌓은 뒤 `io_uring_enter` **한 번**으로 제출한다. 같은 호출에서 `min_complete`만큼 완료를 기다릴 수도 있다. 완료는 CQ 공유 메모리를 직접 읽으므로 따로 시스템 콜이 필요 없다.
  - 로컬 재현: `io_uring_enter(3, 1, 1, IORING_ENTER_GETEVENTS, ...)` 한 번으로 제출 1 + 완료 1 대기를 했다.
- SQPOLL: 커널 스레드가 SQ를 폴링한다. 앱은 SQ에 쓰기만 하면 되고 제출용 시스템 콜도 없다. 한가하면 커널 스레드가 잠들고 `IORING_SQ_NEED_WAKEUP`을 세우니, 그때만 `io_uring_enter`로 깨운다.
- 권한 변화(io_uring_setup(2))
  - 5.11 전: 특권 필요.
  - 5.11: `CAP_SYS_NICE`면 비루트도 가능.
  - 5.13+: 특별한 권한 불필요.

### 8. 컨테이너에서 기동 실패

- `strace`: `io_uring_setup(...) = -1 EPERM (Operation not permitted)`.
- 원인 후보
  1. Docker 25.0+ 기본 seccomp 프로필이 `io_uring_*`를 막는다. 기본 동작이 errno 1(`EPERM`)이다(moby PR #46762). containerd 기본 프로필도 같다.
  2. 호스트 커널 6.6+에서 `kernel.io_uring_disabled`가 1(허용 그룹 밖) 또는 2(전부 금지)다.
  3. 조직 보안 정책·다른 샌드박스(SELinux, gVisor 등 [?])가 막는다.
- 대처: 대체 경로(epoll·스레드 풀)를 두고, 필요하면 해당 워크로드만 seccomp 예외를 합의한다.

### 9. Node가 조용히 느려짐

- 의심: libuv가 io_uring을 쓰려다 `EPERM`을 받고 **조용히 스레드 풀 경로로** 돌아갔다. 기능은 되니 에러 로그가 없다.
  - 로컬 재현: seccomp로 `io_uring_setup`만 막자 Node 18(libuv 1.48)이 `EPERM` 두 번 뒤에도 `readFile`을 정상 완료했다.
- 확인
  - `strace -f -e trace=io_uring_setup node app.js` → `EPERM`인지 본다.
  - `grep Seccomp /proc/<pid>/status`(2면 필터 적용), `cat /proc/sys/kernel/io_uring_disabled`.
- 주의: libuv 버전에 따라 io_uring 사용 범위가 다르다. 1.45에서 도입됐고, 1.49부터 SQPOLL 링은 기본 비활성이다(libuv ChangeLog). 파일 작업은 이 SQPOLL 링으로 가므로 1.49+에서는 io_uring 파일 I/O 자체가 기본 꺼짐이다(`src/unix/linux.c`의 `uv__iou_get_sqe`). 호스트와 컨테이너의 Node·libuv 버전도 같이 비교한다(`node -p process.versions.uv`).

### 10. 2GB 넘는 파일이 잘린다

- 원인: sendfile은 한 번에 최대 `0x7ffff000`(약 2GiB)바이트까지만 보낸다. 게다가 요청보다 적게 보낼 수 있다(sendfile(2)). 코드가 한 번 호출로 다 보냈다고 가정하고 연결을 닫았다.
- 수정: 오프셋을 전진시키며 남은 바이트가 0이 될 때까지 반복한다. 논블로킹 소켓이면 `EAGAIN`에서 `EPOLLOUT`을 기다렸다 이어서 보낸다. Java `transferTo`도 반환값만큼 위치를 옮기며 반복한다.
