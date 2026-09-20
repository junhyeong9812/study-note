# 렌더 루프

[스케줄링](../scheduling/README.md)이 부른 `performWorkOnRoot` 가 **fiber 트리를 훑어 작업 중인 트리를 완성하기까지**다.

이 흐름의 핵심은 셋이다. **트리를 내려갔다 올라오고**, **양보할 수 있고**, **`throw` 를 제어 흐름으로 쓴다.** 마지막 것이 특히 낯설다 — 컴포넌트가 서스펜드하면 예외를 던지고, work loop 를 감싼 `catch` 가 그것을 잡아 상태로 바꾼 뒤 **같은 루프로 되돌아간다.**

기준 커밋: react `main` [`68631c0453`](https://github.com/facebook/react/tree/68631c0453b08e2c7c96a40910f4c91db1f66d5a). 줄 번호는 별도 표기가 없으면 `ReactFiberWorkLoop.js` 기준이다.

## 전체 그림

```text
 [01] performWorkOnRoot                            L1123
      +-- 이미 렌더·커밋 중이면 => **throw**          L1128
      +-- shouldTimeSlice 를 정한다                   L1154
      +-- [02] renderRootConcurrent 또는 renderRootSync  L1165
      +-- do {                                        L1171  재시도 루프
      |     RootInProgress 면 => break (양보)          L1194
      |     스토어가 어긋났으면 => 동기로 다시 => continue  L1229
      |     RootErrored 면 => 복구 시도 => continue     L1269
      |     RootFatalErrored 면 => break                L1294
      |     그 외 => finishConcurrentRender             L1299
      +-- } while (true)                              L1308
      +-- ensureRootIsScheduled(root)                 L1310  <- 흐름 2 로 돌아간다

 [02] renderRootSync L2604 / renderRootConcurrent L2760
      outer: do {
        try {
          서스펜션 상태를 보고 처리한다
          work loop 를 돌린다
        } catch (thrownValue) {
          [05] handleThrow(root, thrownValue)
        }
      } while (true)

      work loop 안에서
        [03] performUnitOfWork  내려간다
        [04] completeUnitOfWork 올라간다
```

```text
 두 함수가 방향이 반대다

 performUnitOfWork   beginWork 를 부르고 자식으로 내려간다
                     자식이 없으면 completeUnitOfWork 로 넘긴다

 completeUnitOfWork  completeWork 를 부르고
                     형제가 있으면 형제로, 없으면 부모로 올라간다

 둘이 합쳐 깊이 우선 순회가 된다
 그리고 루트까지 올라오면 RootCompleted 를 세운다 (L3409-3411)
```

```text
 throw 가 제어 흐름이다

 컴포넌트가 서스펜드하면 예외를 던진다
 그런데 그 값은 진짜 예외가 아니라 센티널이다

   SuspenseException / SuspenseActionException

 실제 thenable 은 getSuspendedThenable() 로 따로 꺼낸다 (L2313)
 주석이 그 역사적 이유를 적는다 (L2308-2312)
   use 가 생기기 전에는 thenable 을 던지는 것이 서스펜션 API 였다

 handleThrow 는 다시 던지지 않는다
 상태를 세우고 돌아가면 do-while 이 try 로 되돌아가
 switch 가 그 상태를 보고 처리한다
```

```text
 work loop 가 셋인데 하나는 죽어 있다

 workLoopSync                  L2753  양보 검사가 없다
 workLoopConcurrent            L3037  시간 기반 (25ms / 5ms)
 workLoopConcurrentByScheduler L3054  shouldYield() 기반

 가운데 것은 enableThrottledScheduling 이 필요한데
 그 플래그가 **모든 빌드에서 false** 다 (ReactFeatureFlags L73)
 호출처도 L2996 하나뿐이라 실제로는 안 돈다

 그래서 concurrent 렌더는 shouldYield() 기반으로 돈다
 다만 act 안에서는 workLoopSync 를 쓴다 (L2988-2994)
```

```text
 이 흐름은 스스로 다시 스케줄한다

 L1310  ensureRootIsScheduled(root)

 렌더가 양보했든 끝났든 이 줄이 돈다
 그래서 흐름 2 로 돌아가 다음 태스크를 정한다

 즉 흐름 2 와 3 이 고리를 이룬다
```

## 어디로 이어지는가

```text
 [beginWork]   컴포넌트 타입별로 자식을 만든다
 [completeWork] 호스트 인스턴스를 만들고 효과를 모은다
 [커밋]         finishConcurrentRender 뒤의 일이다
```

## 단계

1. [performWorkOnRoot](01_performWorkOnRoot/README.md)가 루프 모드를 정하고 재시도를 관리한다.
2. [renderRoot](02_renderRoot/README.md)가 work loop 를 try 로 감싸고 돌린다.
3. [performUnitOfWork](03_performUnitOfWork/README.md)가 내려간다.
4. [completeUnitOfWork](04_completeUnitOfWork/README.md)가 올라온다.
5. [handleThrow](05_handleThrow/README.md)가 던져진 값을 상태로 바꾼다.

## 결과가 쓰이는 곳

```text
 workInProgress
      --> 다음에 처리할 fiber 다
      --> null 이 되면 work loop 가 끝난다

 workInProgressRootExitStatus
      --> [01] 의 do-while 이 이것으로 다음 행동을 정한다
      --> RootCompleted 는 completeUnitOfWork 가 세운다
      --> RootFatalErrored 는 handleThrow 가 세운다

 root.current.alternate
      --> 작업 중인 트리의 뿌리다
      --> 커밋이 끝나면 root.current 가 이쪽으로 넘어간다

 ensureRootIsScheduled
      --> 남은 일이 있으면 다음 태스크가 걸린다
```

## 다루지 않는 것

`beginWork` 가 컴포넌트 타입별로 하는 일, `completeWork` 가 호스트 인스턴스를 만드는 과정, `finishConcurrentRender` 이후의 커밋 경로, `prepareFreshStack` 의 스택 초기화, `throwAndUnwindWorkLoop` 와 `unwindUnitOfWork` 의 되감기, `recoverFromConcurrentError` 의 에러 복구, lane 계산과 `shouldYield` 의 구현은 같은 뼈대의 곁가지라 요약만 했다. 서스펜션 상태와 종료 상태는 [spi](spi/README.md)에 모았다.

## 하위 메서드

- [01 performWorkOnRoot](01_performWorkOnRoot/README.md)
- [02 renderRoot](02_renderRoot/README.md)
- [03 performUnitOfWork](03_performUnitOfWork/README.md)
- [04 completeUnitOfWork](04_completeUnitOfWork/README.md)
- [05 handleThrow](05_handleThrow/README.md)
- [spi](spi/README.md) — 서스펜션 상태와 종료 상태
