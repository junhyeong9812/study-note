# 메모리 관리 — 스택 프레임·가상 메모리·페이징·힙 (컴퓨터사이언스 부트캠프 with 파이썬 ch.9)

> 원고: computer_science repo의 따라 친 노트를 구조만 잡아 이관(2026-09-05). 내용 보강 없음 — 원문 유지, 오탈자만 교정.

## 목차

| 원본 파일 | 절 |
|-----------|-----|
| `chapter9-2.py` | 1. 메모리 계층 / 2. 캐시와 지역성 |
| `chapter9-1.md` | 3. 함수 호출과 스택 프레임 — 전체 흐름 |
| `chapter9-3.py` | 4. 가상 주소 공간과 4개 세그먼트 / 5. 스택 프레임 — 어셈블리 관점 / 6. 가상 메모리와 멀티태스킹 / 7. MMU / 8. 페이징 기법 / 9. 페이지 테이블 / 10. 요구 페이징 / 11. 페이지 폴트와 다이나믹 힙 / 12. TLB |
| `chapter9-2.md` | 13. 세그먼테이션과 페이징 |
| `chapter9.md` | 14. 자바/파이썬 힙 구조와 메모리 계층 요약 |
| `chapter9-3.md` | 15. 대용량 데이터 조회와 메모리 — 스트리밍·DTO 평탄화 |
| `chapter9.py` | 16. 엔디언 — 바이트 저장 순서 |

## 1. 메모리 계층

출처: `computer_science/chapter/chapter9/chapter9-2.py`

컴퓨터에는 다양한 종류의 메모리가 존재한다.
CPU 안에도 메모리가 들어 있다. 바로 레지스터.
또한 우리가 익숙한 RAM과 하드디스크가 존재.
CPU와 메인 메모리 사이에는 캐시하는 메모리도 존재.

메모리의 존재 이유는 속도와 비용 때문이다.
CPU 안에 있는 레지스터는 메모리 중 가장 빠르지만 용량은 작다.
가장 빠른 메모리인 레지스터를 모든 메모리에 쓰면 컴퓨터 성능이 어마무시하게 좋아지지만 비용이 엄청 비싸지기 때문에,
이러한 이유로 적당선의 가격과 하드웨어 구동의 요소들로 인해 오늘날 메모리 계층 구조인
레지스터 <-> 캐시 <-> 메모리 <-> 하드디스크가 존재.
레지스터로 가까워질수록 속도는 올라가지만 용량은 작아진다.
즉 데이터가 하드디스크에 있다면 모든 메모리·캐시·레지스터를 거쳐 CPU로 도달하게 된다.
이때 지역성이라는 개념으로 인해 이렇게 해도 느리지 않고 오히려 메모리 계층 구조로 인해 기능 향상을 이뤘다.
오늘날 캐시는 CPU 안에 들어 있다.
캐시에도 L1과 L2 등 숫자가 낮을수록 속도가 빠르고 용량은 작다.

## 2. 캐시와 지역성

출처: `computer_science/chapter/chapter9/chapter9-2.py`

캐시가 없던 시절에는 CPU가 데이터를 요청하면 데이터를 메모리에서 레지스터로 바로 가져왔다.
CPU가 레지스터에서 데이터를 가져올 때 1사이클이면 걸리는 반면 메인 메모리에서 가져올 때는 20\~100사이클이 걸린다.
CPU의 처리 속도가 빨라지면서 데이터 요청할 때마다 메모리에서 데이터를 가져오는 이 시간이 매우 부담스러워졌다.
연산 속도가 아무리 빨라도 연산이 필요한 데이터가 레지스터에 도착하지 않으면 도착할 때까지 기다려야 한다.
이때 캐시가 등장한 것.
캐시는 레지스터와 메인 메모리 사이에 존재한다.
CPU가 데이터를 요청하면 메인 메모리에서 해당 데이터만 가져오는 것이 아니라
데이터와 함께 인접 데이터로 이뤄진 메모리 블록을 캐시로 가져오고 캐시에서 해당 데이터만 레지스터로 전송.
이때 요청 데이터와 인접 데이터로 이뤄진 메모리 블록을 캐시행이라 하는데 64\~128바이트 정도이다.
이때 CPU가 다른 데이터를 요청 시 우선 캐시 히트로 캐시에서 확인 후 없으면 캐시 미스로 메모리에서 가져와야 한다.
캐시에서 데이터를 읽어올 때는 3사이클이 걸린다.
메인 메모리에서 데이터를 가져오는 것보다 훨씬 빠르다.
CPU가 데이터를 요청했을 때 캐시 히트가 많아지면 빨라지는 것.

하지만 이때 문제가 생긴다.
데이터가 캐시 블록 단위 내에 모여 있도록 인접 메모리 공간에 저장되어야 빠른 거지 않나? 그런데 데이터가 모일 확률은?
이를 해결하는 것이 지역성이라는 원리이다.

지역성의 원리라는 개념이 존재 — 데이터 접근이 같은 메모리 공간이나 인접한 메모리 공간에서 자주 일어난다는 의미.
지역성에는 시간적 지역성과 공간적 지역성이 존재한다.

시간적 지역성은 특정 데이터에 한 번 접근했을 때 곧 다시 그 데이터에 접근할 가능성.
공간적 지역성은 이번에 접근할 데이터는 이전 데이터 근처에 있을 확률이 높다는 것.
코드로 보면

```python
li = [1, 2, 3, 4, 5]
res = 0
for e in li:
    res += e
```

이때 res라는 변수 데이터는 리스트의 모든 요소를 가져와 더할 때 데이터에 접근하는데, 시간 지역성이다.
for문의 e는 리스트를 순회하면서 매번 바로 옆의 데이터를 가져온다. 이를 공간 지역성이라 한다.

예제의 리스트 li는 요소로 1\~5 상수 객체를 갖기 때문에 공간 지역성이 적용되었지만,
사실 파이썬의 리스트는 C언어의 배열처럼 요소가 메모리 공간에 연속적이지 않으므로 공간 지역성이 적용되지 않는다.
이는 파이썬 인터널에 대한 내용.

즉 캐시 히트가 잘 일어나도록 지역성을 고려해 작성한 코드를 캐시 프렌들리 코드라고 한다.
하지만 지역성까지 고려하여 코드를 작성하는 프로그래머는 많지 않다.
프로그래밍을 할 때 의식적으로 고려하지 않아도 코드의 많은 부분이 지역성이 적용된다.
지역성의 예로 든 코드만 봐도 지역성을 신경 써서 작성한 코드가 아니다.
그리고 프로그램이 실행되면서 필요한 데이터가 모여 있을 확률? 매우 높다.
실제 캐시에 필요한 데이터가 존재할 확률은 90% 이상이며 이 정도 확률이면 캐시를 사용한다.

그렇다면 캐시 프렌들리 설계를 하는 경우에는 — 많지 않다.
이유는
1. 추상화 수준이 높다: 자바·파이썬은 메모리를 직접 제어하지 않는다.
2. 가비지 컬렉터: 객체 위치가 수시로 바뀐다.
3. 최적화 우선순위: 대부분 병목은 I/O, 네트워크, 알고리즘에서 발생.
4. 생산성 vs 성능: 이런 최적화는 코드 복잡도를 크게 높임.

그래도 고려할 경우
1. 게임 개발/고성능 시뮬
2. 대용량 처리 -> numpy의 np.array 사용으로 연속 메모리 사용
3. 행렬 순회 방향 — 열 우선 순회는 캐시 미스가 많으며 행 우선 순회는 캐시 프렌들리하다.

파이썬은 NumPy나, 자바는 Primitive 배열이나 Valhalla 값 기대를 활용.

## 3. 함수 호출과 스택 프레임 — 전체 흐름

출처: `computer_science/chapter/chapter9/chapter9-1.md`

함수 동작에 대한 전체 흐름 정리

```c
int adder(int a, int b, int n) {
    int c = a * n;
    int d = b * n;
    int e = c + d;
    return e;
}
int main(void) {
    int a = 10;
    int b = 20;
    int n = 2;
    int res = adder(a, b, n);
    return 0;
}
```

```
1. main에서 인자 준비
n -> b -> a 순서로 스택에 push 역순
이때 처음 레지스터에 복사 후 push를 통해 스택에 데이터 적재

2. call adder
- 돌아올 주소(return address)를 스택에 push
- EIP가 ADDER로 점프

3. adder 진입
- 이전 ebp를 스택에 저장 (main의 프레임 포인터)
- ebp = esp (새 프레임 기준점)
- esp -= N (지역변수 공간 확보)

4. adder 실행
- 지역변수 c,d,e 사용
- 결과 EAX에 저장

5. adder 종료
- esp = ebp (지역변수 공간 해제)
- pop ebp (이전 프레임 포인터 복구)
- ret (return address로 점프)

6. main으로 복귀
- esp += 12 (인자 3개 해제, cdecl 규약)
- EAX에서 반환값을 꺼내서 res에 저장
```

스택 상태 그림

```
함수 호출 전 (main)          adder 실행 중
┌─────────────┐             ┌─────────────┐
│     ...     │             │     ...     │
├─────────────┤             ├─────────────┤
│      a      │             │      a      │
├─────────────┤             ├─────────────┤
│      b      │             │      b      │
├─────────────┤             ├─────────────┤
│      n      │             │      n      │
├─────────────┤             ├─────────────┤
│             │             │ return addr │ ← call이 push
│             │             ├─────────────┤
│             │             │  old ebp    │ ← adder가 push
│             │             ├─────────────┤ ← ebp (새 기준)
│             │             │      c      │
│             │             ├─────────────┤
│             │             │      d      │
│             │             ├─────────────┤
│             │             │      e      │
└─────────────┘             └─────────────┘ ← esp
```

핵심 요약

```
인자 전달: 스택 (push)
반환값 전달: EAX 레지스터
프레임 관리: ebp/esp 조작
복귀 주소: call이 스택에 push, ret이 pop해서 점프
```

내가 놓친 흐름 정리

```
1. call adder
- 돌아올 주소를 스택에 push
- EIP가 adder 위치로 점프 (EIP는 adder 시작 주소)

2. adder 진입
- push ebp (main의 ebp를 스택에 저장)
- mov ebp, esp (ebp를 현재 esp로 설정 -> 새 프레임 기준)
- sub esp, N (지역변수 공간 확보)

3. adder 연산
- 지역변수 사용하여 계산
- 결과를 EAX에 저장

4. adder 종료
- mov esp, ebp (esp를 ebp로 복원 -> 지역변수 공간 해제)
- pop ebp (스택에서 꺼내서 ebp 복원 -> main의 프레임 기준으로)
- ret (스택에서 return address pop -> EIP로 점프)

5. main 복귀
- add esp, 12 (인자 공간 해제)
- mov res, eax (반환값 저장)
```

레지스터 역할: EIP — 현재 실행 중인 인스트럭션 주소 / ESP — 스택의 맨 위 (항상 변동) / EBP — 현재 스택 프레임의 기준점 (함수 내에서 고정) / EAX — 반환값 저장

```
ESP: 스택 맨 위를 따라다님 (push/pop마다 변동)
EBP: 프레임 기준점 (함수 내에서 고정, 지역변수 접근에 사용)

"main 스택으로 돌아간다" = ebp를 복원한다
"공간 해제" = esp를 이동한다
```

```
adder 실행 중:
                     ┌─────────────┐
                     │      n      │
                     ├─────────────┤
                     │      b      │
                     ├─────────────┤
                     │      a      │
                     ├─────────────┤
                     │ return addr │
                     ├─────────────┤
                     │  old ebp ───┼──→ main의 프레임 기준
         ebp ──────→ ├─────────────┤
                     │      c      │
                     ├─────────────┤
                     │      d      │
                     ├─────────────┤
         esp ──────→ │      e      │
                     └─────────────┘

종료 시:
1. esp = ebp (c, d, e 공간 무효화)
2. pop ebp (old ebp 꺼내서 ebp에 넣음 → main 기준 복원)
3. ret (return addr 꺼내서 EIP로 → main으로 점프)
```

## 4. 가상 주소 공간과 4개 세그먼트

출처: `computer_science/chapter/chapter9/chapter9-3.py`

프로그램을 더블클릭해 실행하면 하드디스크에 있던 프로그램이 메인 메모리에 올라오면서 프로세스를 생성하고, 32비트 운영체제라면 실행되는 순간 4GB 메모리를 할당받는다.
이 메모리가 실제 메인 메모리의 실제 4기가는 아니지만 프로세스는 실제 4기가를 할당받은 것처럼 사용.

이때 할당받은 4GB 중 2GB는 운영체제가 담당하는데 이를 커널 영역이라 한다.
나머지 2GB는 실제 프로그램이 담당하는 유저 영역이다.
유저 영역은 다시 CODE, DATA, STACK, HEAP 세그먼트로 나뉜다.
코드 / 데이터 / 힙 / 스택 — 이렇게 구조를 가지고 있으며 가장 낮은 주소의 코드부터 가장 높은 주소의 스택까지 위 순서대로 위에서 아래로 내려간다.
이때 힙은 아래로 세그먼트가 확장하고 스택은 위로 세그먼트를 확장한다.

1. 코드 세그먼트
코드 세그먼트는 프로그램의 인스트럭션이 저장되는 공간.
즉 우리가 작성한 함수나 클래스 정의 코드는 인스트럭션으로 변환되어 하드에 저장되어 있다가 프로세스가 실행되면 가상 주소 공간의 코드 세그먼트로 올라온다.
함수를 호출하면 프로그램 카운터가 인스트럭션 메모리 주소를 가리키며 함수를 실행.

2. 데이터 세그먼트
데이터 세그먼트는 전역 변수가 저장되는 공간이다.
전역 변수는 프로세스가 실행될 때 데이터 세그먼트에 올라가고(static) 프로세스가 종료될 때 소멸한다.
즉 프로그램이 실행되는 동안 계속 있으며 프로그래머가 생성이나 소멸을 결정할 수 없다.

코드 세그먼트와 데이터 세그먼트의 특징은 프로세스가 실행되기 전에 이미 그 크기를 알 수 있다는 점으로,
함수 인스트럭션이나 전역 변수는 런타임에 사라지지 않고 프로그램을 만들 때 컴파일러에 의해 이미 분석이 끝나기 때문이다.
리눅스에서는 size 명령어를 통해 text(코드 세그먼트), data(데이터 세그먼트)를 알 수 있다.
bss는 데이터 세그먼트에 포함되는 값.
bss란 Block Started by Symbol.
BSS는 초기화되지 않은 전역 변수와 정적 변수가 저장되는 메모리 영역.
DATA 영역: 초기화된 전역/정적 변수 — 실행 파일에 실제 값이 저장됨.
BSS 영역: 초기화되지 않은 전역/정적 변수 — 실행 파일에 "크기 정보"만 저장됨.

3. 스택 세그먼트
스택 세그먼트는 지역 변수가 저장되는 공간이다.
지역 변수가 저장된다는 것은 함수를 호출했을 때 그 스택 프레임이 스택 세그먼트에 생성되는 것을 의미한다.
함수가 호출되면 그 함수의 스택 프레임이 스택 세그먼트에 생기고,
함수 실행 도중 다른 함수를 호출하면 다시 호출된 함수의 스택 프레임이 호출한 함수의 스택 프레임 위에 쌓인다.
기본적으로 이렇게 쌓일 수 있는 프레임은 1MB로 할당되며 이걸 넘기면 스택 오버플로우 오류가 발생한다.
(해당 프레임 값은 사용자가 정할 수 있다. 할당하지 않으면 1MB.)

4. 힙 세그먼트
힙 세그먼트는 프로그래머가 자유롭게 메모리를 할당하고 해제할 수 있는 공간.
함수 호출이 끝나면 스택 프레임이 사라지면서 해제되는 지역 변수와 달리, 힙 세그먼트에 할당한 메모리는 해제하지 않는 한 메모리 공간에 계속 남아 있는다.
이렇게 힙 세그먼트에 할당하면 해제하지 않는 이상 계속 남아 있어서 메모리 누수가 생길 수 있으며,
스택과 달리 늘어날 수 있는 최대 크기가 정해져 있지 않다.

예제 C++ 코드를 보자.

```c
#include <iostream>

//code
int add(int a, int b) {
    return a + b;
}

int subtract(int a, int b) {
    return a - b;
}

// Data
int global_x = 10;

int main(void) {
    //STACK
    int local_x = 20;

    //HEAP
    int * heap_x = (int*)malloc(sizeof(int));
    *heap_x = 30;
    free(heap_x);

    return 0;
}
```

이걸 보며 보자.
add()라는 함수를 정의하였다.
함수 정의는 컴파일을 거치면서 인스트럭션이 되고, 이 인스트럭션은 프로세스가 실행되면 코드 세그먼트에 올라간다.
전역 변수로 선언된 global_x는 데이터 세그먼트에 가며,
local_x는 지역 변수라 스택 세그먼트에 스택 프레임이 생성된다.

malloc은 힙 세그먼트에 4바이트의 메모리를 할당하는 코드이며, 메모리 해제하는 코드가 free이다.
이처럼 힙 세그먼트를 사용하면 메모리 할당과 해제 시점을 프로그래머가 정할 수 있다.
할당 메모리를 해제하지 않으면 메모리 주소값을 참조나 리턴으로 전달하면 어디서든 접근이 가능해진다.
하지만 이러한 단점으로는 메모리가 들어갈 만한 충분한 공간을 찾는데, 이때 메모리 공간이 부족하면 찾을 때까지 검색을 하고,
이러한 이유로 힙 세그먼트 할당 함수는 느리다.
메모리 할당 위치를 단번에 알 수 있는 stack에 비해 느리며,
성능을 고려할 때 힙을 반드시 사용해야 하는 게 아니라면 스택을 쓰는 게 맞다.
또한 할당과 해제가 잦아 메모리의 빈 공간이 잘게 나눠질 수 있다.
총합은 충분하지만 관련 데이터가 모이지 못하고 멀리 떨어져서 저장되며 이를 메모리 단편화라 한다.
이렇게 되면 지역성 원리가 적용되지 않아 캐시 미스 확률이 올라간다.
그뿐만 아니라 페이지 폴트가 발생해 성능을 약화시킨다.
또한 이때 free를 안 하고 해당 함수를 나가면 프로그램 종료 전까지 해당 메모리에 대한 누수가 쌓이게 된다.

## 5. 스택 프레임 — 어셈블리 관점

출처: `computer_science/chapter/chapter9/chapter9-3.py`

스택 포인터(stack pointer)와 프레임 포인터(frame pointer),
위 두 개를 이용하여 스택 프레임을 할당하고 해제하는 과정.

호출 규약이란 함수가 호출될 때 스택에 인자를 할당하거나 해제하는 주체가 함수를 호출한 쪽인지 호출된 함수인지 정해 놓는 것.
우리가 볼 예제에서는 인자의 할당과 해제를 함수를 호출한 쪽에서 담당한다.
예제 코드를 보면

```c
#include <stdio.h>

int adder(int a, int b, int n) {
    int c = a * n;
    int d = b * n;
    int e = c + d;
    return e;
}
int main(void) {
    int a = 10;
    int b = 20;
    int n = 2;
    int res = adder(a, b, n);
    return 0;
}
```

위 코드에서 스택 프레임에 지역 변수가 쌓이는 방식은 n -> b -> a로 쌓이고 c -> d -> e로 쌓인다.
이때 esp(extended stack pointer)는 스택 세그먼트의 맨 위를 가리키는 스택 포인터 레지스터이다.
앞에 위치한 extended는 16비트에서 32비트로 넘어오면서 붙은 것.

이때 main 순서를 보면 `mov eax, dword ptr [n]`을 통해 n을 eax에 넣고
`push eax`는 실제 범용 레지스터의 데이터를 스택에 쌓는 명령어이다.
이때 스택 프레임에 쌓을 때 범용 레지스터에 값을 복사하고 이후 push로 스택에 할당한다.

그 후 `call _adder (0381109h)` —
call func는 함수 호출이 끝나고 돌아올 주소 값을 스택에 쌓고 함수의 인스트럭션이 있는 곳으로 점프하는 명령어이다.
인자의 할당을 함수를 호출한 쪽인 caller에서 담당.
다음 행에서 adder 함수를 호출하며 call한다.

이때 돌아올 주소는 레지스터 중 프로그램 카운터(PC)에서 온다.
함수가 호출되면 프로그램 카운터가 함수 인스트럭션이 있는 곳을 가리키므로, 함수 호출이 끝난 다음 이어서 실행할 인스트럭션을 어딘가 저장해 둬야 돌아올 수 있기 때문이다.
이를 인텔 계열에서는 인스트럭션 포인터라 한다.

이때 ebp(extended base pointer)는 프레임 포인터라는 레지스터이다.
베이스 포인터인 이유는 인텔 계열에서 프로그램 카운터를 instruction pointer라 부르는 것처럼 이름을 붙인 것.
프레임 포인터는 스택 프레임의 기준이 된다. 그래서 프레임 포인터이다.
스택 프레임에 있는 지역 변수에 접근할 때도 프레임 포인터를 이용한다.
이때 우선 ebp 값을 스택에 저장하고, 이 ebp 값은 main 스택 프레임의 프레임 포인터를 가리킨다.
함수 호출이 끝난 다음 다시 main 스택 프레임의 기준을 가리켜야 하므로 스택에 저장해 둔다.
그다음 행에 스택 포인터 값을 프레임 포인터에 대입하여 기준이 adder 스택 프레임이 된다.

이때 `sub A, B`를 사용하여 A에서 B를 빼고 다시 A에 저장하고,
스택 포인터 esp에서 일정 메모리를 빼서 나머지 지역 변수 공간을 확보하는데, 이때 뺄셈을 하는 걸 알 수 있다.
빼는 이유는 스택의 위쪽은 낮은 주소이고 아래쪽은 높은 주소이기 때문이다.
또한 스택은 위쪽으로 확장된다.
스택에 데이터를 쌓는다는 것은 스택 포인터가 가리키는 주소가 점점 낮아진다는 것을 의미하며,
스택 포인터가 낮은 주소를 가리키려면 뺄셈을 하면 된다.
지역 변수 공간 확보를 하기 위해서 계속 빼면서 공간을 확보하는 것.

이렇게 쌓인 스택이 해제가 되려면 이때 ebp 값을 esp에 대입하여 중간 남은 메모리를 해제하고,
이후 다른 함수 호출할 때 스택 포인터가 가리키는 곳부터 스택 프레임이 생기므로 이전 데이터를 덮어 씌우기 때문이다.
어셈블리 코드의 마지막 행은 스택 프레임 해제를 마무리하는 단계로,
이때도 데이터를 직접 삭제하는 게 아니라 스택 포인터를 인자가 차지했던 메모리만큼 더해서 해제한다.
스택에 할당할 때 스택 포인터에서 일정 메모리를 빼서 낮은 주소로 옮겼으므로,
반대로 스택에서 메모리를 해제할 때는 덧셈을 통해 스택 포인터를 높은 주소로 옮긴다.
이때 호출 규약이 cdecl이어서 함수 인자의 해제를 함수를 호출한 쪽 caller에서 담당한다.

## 6. 가상 메모리와 멀티태스킹

출처: `computer_science/chapter/chapter9/chapter9-3.py`

오늘날 운영체제는 대부분 멀티태스킹이 가능하다. 왜 가능할까?
앞서 프로세스를 실행하면 한 프로세스당 4GB를 할당한다.
이 말은 용량이 4GB인 컴퓨터에서 단 하나의 프로세스만 실행할 수 있다는 것.
하지만 그렇지 않다. 왜일까?

프로세스는 메인 메모리에서 데이터를 가져온다.
이때 용량이 큰 하드에서 가져오면 좋겠지만 이러면 너무 느리다.
메인 메모리에서 데이터를 가져올 때는 20\~100사이클인 반면 하드는 500,000\~5,000,000사이클이 걸린다.
하지만 하드에도 저장 기능이 있으므로 하드도 메인 메모리처럼 사용하면 좋겠다는 아이디어에서 나온 게 가상 메모리이다.
가상 메모리란 메인 메모리를 확장하기 위해 페이지 파일로 불리는 하드디스크의 일정 부분을 메인 메모리처럼 사용하는 것으로,
메인 메모리 RAM과 하드디스크의 페이지 파일을 합쳐 물리 메모리라 한다.

이때 가상 메모리 관리 기법은 가상 주소 공간을 쪼개는 기준에 따라 세그먼테이션 기법과 페이징 기법으로 나눌 수 있으며,
오늘날 운영체제는 대부분 두 가지를 함께 사용한다.

## 7. MMU

출처: `computer_science/chapter/chapter9/chapter9-3.py`

프로세스에 주어지는 메모리 공간을 가상 주소 공간(virtual address space)이라 한다.
가상 주소 공간의 메모리 주소를 논리 주소(logical address)라고 하고, 메인 메모리의 메모리 주소를 물리 주소(physical address)라고 한다.
프로세스를 실행하려면 실제로 데이터와 코드를 올릴 물리 메모리가 필요하다.
이를 위해 논리 주소를 물리 주소로 변환해 메인 메모리를 사용해야 하는데 이때 필요한 하드웨어가 MMU이다.
MMU(Memory Management Unit)는 논리 주소를 물리 주소로 런타임에 대응시키는 하드웨어로,
과거에는 따로 존재했지만 지금은 CPU 내부에 있다.

## 8. 페이징 기법 — 페이지와 오프셋

출처: `computer_science/chapter/chapter9/chapter9-3.py`

페이징 기법에서는 가상 주소 공간과 메인 메모리를 일정 크기로 나누어 다룬다.
가상 주소 공간부터 설명하면, 가상 주소 공간을 일정한 크기로 쪼개는데 이 쪼개진 한 부분을 페이지라 한다.
페이지 크기는 시스템마다 다른데 보통 1\~8KB이며 32비트 시스템에서는 4096, 즉 4KB이다.
페이지의 개수는 2의 20승.
이러한 20개의 비트를 페이지 넘버라 하는데 VPN이라는 가상 페이지 넘버라 부르기도 한다.
페이지 크기가 4096일 경우 페이지 안에 있는 바이트 하나를 가리키려면 비트가 12개 필요.
페이지 안에서 특정 바이트를 가리키는 이 비트를 오프셋이라 한다.

페이지 넘버와 오프셋을 더하면 논리 주소가 된다.
이 논리 주소는 CPU가 요청하는 주소로 프로그램 카운터에 저장된다.

예시로 10진수로 —
가상 주소 공간 2000바이트, 페이지 크기 100바이트, 프로그램 카운터 값 234, 페이지 수 20, 오프셋 두 자릿수 10진수(0\~99).
전체 2000바이트에서 페이지 넘버는 0\~99바이트: 0, 100\~199바이트: 1로 쭉 간다.
이때 백의 자릿수가 페이지 넘버와 같다.
오프셋은 페이지 넘버가 가리키는 페이지의 첫 주소부터 실제 가리키는 주소까지의 거리이다.
프로그램 카운터 234에서 페이지 넘버가 2며 오프셋이 34라는 의미로 234번 바이트를 가리킨다.
이 규칙은 2진수도 동일하다.

결국 32비트 시스템에서 메모리 주소를 표현할 때 32비트를 사용합니다.
페이지 개수가 2^20개, 페이지 넘버를 나타내는 비트는 20비트이며,
페이지 크기는 4KB이기에 오프셋은 12비트이다.
이 둘을 합치면 가상 주소 공간 하나의 주소값이 된다.

## 9. 페이지 테이블

출처: `computer_science/chapter/chapter9/chapter9-3.py`

메인 메모리도 가상 주소 공간과 같은 크기로 나눠진다.
쪼개진 부분 하나를 페이지 프레임이라 부르며,
메인 메모리의 프레임이 가상 주소 공간의 페이지와 크기가 같은 이유는 실제로 존재하지 않는 페이지를 실제로 존재하는 프레임에 할당하기 위함이다.
프레임 개수를 구하는 방법과 프레임 안에서의 오프셋의 의미는 페이지와 같습니다.
프레임 순서를 나타내는 비트를 프레임 넘버라 부르고 물리 페이지 주소라고도 부른다.

페이지 테이블은 어떤 프로세스의 페이지 넘버(VPN), 상응하는 프레임 넘버(PPN) 그리고 상태 등을 저장하는 테이블이다.
모든 프로세스는 저마다 페이지 테이블이 있다.
페이지 테이블은 메모리에 저장되며, CPU에는 페이지 테이블의 시작 주소를 가리키는 PTBR이라는 레지스터가 있다.

가상 주소 공간의 페이지는 실제로 존재하지 않는 가상의 메모리 공간이다.
페이지 테이블에 VPN 형태로만 남아 있다.
실제로 존재하는 메모리는 프레임이다.
프레임은 메인 메모리에 있으며, 페이지는 페이지 테이블을 통해 프레임으로 대응되어야만 실제 메모리를 사용 가능.
그래서 페이지 테이블은 가상 메모리 구현의 요체라 볼 수 있다.
이때 프레임 위치가 하드인지 메모리인지 나타내는 유효 비트가 존재하고, 메인 메모리에 있으면 1 아니면 0을 나타낸다.

논리 주소에 대응하는 물리 주소는 페이지 넘버를 프레임 넘버로 대체하고 논리 주소의 오프셋과 합쳐서 구할 수 있다.

이때 MMU의 내부 동작을 보면 PTBR에 저장된 페이지 테이블의 시작 주소를 참조,
이제 프로그램 카운터에서 VPN 비트 상위 20비트를 참조한다.
페이지 테이블에서 페이지 넘버(VPN)를 찾고 이에 상응하는 프레임 넘버(PPN)를 가져와
프로그램 카운터의 오프셋 하위 12비트와 합쳐 물리 주소를 만든다.
이 물리 주소를 또 다른 레지스터인 MAR(Memory Address Register)에 저장한 다음,
CPU는 이 레지스터의 주소값을 읽어와 메인 메모리에서 인스트럭션을 가져오고(fetch) 실행한다.

```
PTBR → 페이지 테이블 시작 주소로 테이블 조회
VPN → 인덱스로 사용해서 해당 엔트리에서 PPN 찾기
PPN + Offset → 결합(concatenate)해서 물리 주소 생성
물리 주소 → 실제 메모리에서 데이터/instruction 가져옴
```

## 10. 요구 페이징

출처: `computer_science/chapter/chapter9/chapter9-3.py`

가상 메모리는 요구 페이징으로 구현한다.
요구 페이징이란 프로세스를 실행할 때 모든 페이지를 프레임에 매핑하는 게 아니라 필요한 페이지만 메인 메모리에 올리는 것.
즉 프로세스가 처음 실행될 때 운영체제는 페이지 테이블을 메인 메모리에 만들고,
실행에 필요할 것 같은 페이지만 먼저 프레임에 매핑한다.
이러한 방식을 프리페어링이라 부른다.

즉 페이지 테이블에서 페이지와 프레임을 매핑할 때 메인 메모리에 올라와야 하는 페이지의 코드를 하드디스크에서 가져와 프레임을 생성하고 페이지와 매핑한다.
매핑한 페이지는 페이지 테이블의 유효 비트를 1로 바꾸며,
아직 필요하지 않아 프레임에 매핑하지 않은 페이지는 하드디스크에 있는 페이지의 위치로 초기화하고 유효 비트를 0으로 한다.
이후 CPU가 페이지 요청 시 프레임 매핑한 상태가 아니라면 빈 프레임에 페이지를 매핑한다.

## 11. 페이지 폴트와 다이나믹 힙

출처: `computer_science/chapter/chapter9/chapter9-3.py`

페이지 폴트(page fault)란 CPU가 요청한 페이지가 메인 메모리에 없을 때 발생한다.
이는 유효 비트를 확인하면 알 수 있는데, 유효 비트가 0이면 메인 메모리에 존재하지 않는 것이다.
페이지 폴트가 발생하면 해당 페이지를 하드에서 가져와 빈 프레임에 할당하면 된다.

이때 메인 메모리에 빈 프레임이 없다면 어떻게 할까?
이때 페이지 교체 알고리즘에 의해 메인 메모리에 있는 페이지를 하드로 내리고 요청된 페이지를 메인 메모리에 올린다.
이때 하드로 가는 페이지를 희생 페이지(victim page), 페이지를 메인 메모리로 올리는 것을 페이지인(page-in)이라고 한다.

중요한 점은 페이지 폴트가 자주 일어나면 성능 감소이며,
페이지 폴트가 일어날 확률을 줄이려면 지역성을 고려하면서 해야 되고,
연결 리스트 자료구조 사용 시 메모리 단편화가 심하게 발생해 관련 데이터가 흩어지면 페이지 폴트가 빈번하게 일어나 성능이 떨어진다.
이때는 자료 형태를 배열로 변경하면 해결할 수 있지만,
배열을 사용하기 어렵다면 다이나믹 힙을 이용하여 단편화를 없애고 지역성을 좋게 만들 수 있다.
다이나믹 힙은 프로세스에 기본적으로 할당되는 디폴트 힙 외에 프로그래머가 따로 할당해 만든 힙이다.

이때 배열처럼 수나 배치가 아닌, 메모리 할당을 격리시켜 단편화를 제어하는 게 목적인 다이나믹 힙 —
관련 데이터를 같은 커스텀 힙에만 할당,
다른 데이터와 섞이지 않는다.
결과적으로 같은 페이지에 모일 확률 업.

기본 힙은 공용 주차장, 다이나믹 힙은 전용 주차장.
배열: 애초에 연속된 메모리.
다이나믹 힙: 연결 리스트지만 흩어지는 걸 최소화.

자바나 파이썬 같은 상위 언어에서의 페이지 폴트 —
공통점으로는 프로그래머가 직접 제어가 불가능.
OS가 알아서 처리하기에 프로그래머는 신경 쓰지 않는다.
하지만 이때 포인터로 연결된 자료형은 메모리 점프가 심하며,
연속된 메모리를 사용하여 지역성을 올려 성능 저하를 막아야 한다.

다이나믹 힙 관점에서, 자바는 직접 만들지 않는다.
자바는 단일 힙 구조이며 모든 객체가 JVM Heap에 할당된다.
대신 JVM이 자동으로 최적화를 한다.

```
┌─────────────────┐
│ Eden Space      │ ← 새 객체 (높은 지역성)
├─────────────────┤
│ Survivor Space  │
├─────────────────┤
│ Old Generation  │ ← 오래된 객체
└─────────────────┘
가비지 컬렉터가 객체 수명에 따라 자동 분리 -> 유사한 효과
```

파이썬은 프로그래머가 힙을 여러 개 만들 수 없다.
파이썬 메모리에서는

```
Python Memory
┌──────────────────┐
│ Object Arena     │ ← 작은 객체들 풀링
├──────────────────┤
│ Large Objects    │ ← 큰 객체 별도 관리
└──────────────────┘
```

이렇게 두 개의 분류만 한다.

실무 관점에서 본다면

```java
// ❌ 나쁜 예: 연결 리스트
LinkedList<Data> list = new LinkedList<>();
for(Data d : list) {  // 각 노드 접근 시 페이지 폴트 가능
    process(d);
}

// ✅ 좋은 예: ArrayList
ArrayList<Data> list = new ArrayList<>();
for(Data d : list) {  // 연속 메모리, 캐시 친화적
    process(d);
}

// ✅ 더 좋은 예: 배열
Data[] array = new Data[1000];
for(Data d : array) {  // 최고의 지역성
    process(d);
}
```

파이썬에서의 성능 개선으로는

```python
# ❌ 나쁜 예
class Node:
    def __init__(self, data):
        self.data = data
        self.next = None

# ✅ 좋은 예
data = [1, 2, 3, 4, 5]  # 리스트 (내부는 배열)

# ✅ 더 좋은 예: NumPy (C로 구현된 연속 메모리)
import numpy as np
data = np.array([1, 2, 3, 4, 5])
```

자바에서 메모리 지역성 개선:

```java
// 객체 풀링 패턴 (유사 효과)
class ObjectPool {
    private ArrayList<MyObject> pool;  // 미리 생성

    public ObjectPool(int size) {
        pool = new ArrayList<>(size);
        for(int i = 0; i < size; i++) {
            pool.add(new MyObject());  // 한번에 생성 → 가까이 위치
        }
    }
}
```

대용량 데이터 처리 시 LinkedList vs ArrayList 선택이 페이지 폴트 발생 횟수를 좌우함.
10만 건 조회: LinkedList → 수백 번의 페이지 폴트 / ArrayList → 수십 번의 페이지 폴트.
성능 차이: 10배 이상!

## 12. TLB (변환 색인 버퍼)

출처: `computer_science/chapter/chapter9/chapter9-3.py`

변환 색인 버퍼(Translation Lookaside Buffer, TLB)는 주소 변환 속도를 높이기 위한 일종의 캐시이다.
변환 색인 버퍼에는 최근에 사용된 페이지 테이블의 일부가 저장되어 있고,
MMU가 페이지 테이블에서 프레임 넘버를 읽어 와야 할 때 먼저 TLB에 해당 항목
(페이지 넘버와 그에 매핑되는 프레임 넘버, 즉 페이지 테이블의 일부)이 있는지 확인한다.
이를 TLB 히트라 한다.
메인 메모리에 있는 페이지 테이블에 접근할 필요가 없어 굉장히 빠르다.
즉 MMU에서 가져올 때 TLB에 넣고 그 후 프레임 넘버에서 가져오기에 (TLB 미스면) 느릴 수밖에 없다.

## 13. 세그먼테이션과 페이징

출처: `computer_science/chapter/chapter9/chapter9-2.md`

관련: [thrashing](../../systems/thrashing/)

### 세그먼테이션(Segmentation)

논리적 단위로 메모리를 분리.

```
프로세스 메모리
┌─────────────────┐
│ Code Segment    │ ← 실행 코드
├─────────────────┤
│ Data Segment    │ ← 전역 변수
├─────────────────┤
│ Stack Segment   │ ← 스택
├─────────────────┤
│ Heap Segment    │ ← 동적 할당
└─────────────────┘

각 세그먼트는 크기가 다름
```

장점

```
- 논리적으로 의미 있는 단위
- 세그먼트별 권한 설정 가능 (코드는 읽기 전용 등)
- 공유하기 쉬움 (라이브러리 코드 세그먼트 공유)
```

단점

```
- 가변 크기 → 외부 단편화 발생

물리 메모리:
[사용중][  빈공간  ][사용중][빈공간][사용중]
         ↑                   ↑
    5KB 비었는데         3KB 비었는데
    합치면 8KB인데 연속 8KB 할당 불가
```

### 페이징(Paging)

고정 크기(4KB)로 메모리 분리:

```
가상 메모리              물리 메모리
┌────────┐              ┌────────┐
│ Page 0 │─────────────→│ Frame 5│
├────────┤              ├────────┤
│ Page 1 │─────────────→│ Frame 2│
├────────┤              ├────────┤
│ Page 2 │─────────────→│ Frame 9│
└────────┘              └────────┘

모든 페이지가 같은 크기
```

장점

```
- 외부 단편화 없음 (고정 크기라 빈 공간 관리 쉬움)
- 메모리 할당/해제 단순
```

단점

```
- 내부 단편화 발생

요청: 5KB
할당: 8KB (페이지 2개)
낭비: 3KB

- 논리적 의미 없음 (코드와 데이터가 한 페이지에 섞일 수 있음)
- 세그먼트별 권한 설정 어려움
```

### 결합: Segmentation with Paging

둘이 합쳐서 사용:

```
가상 주소
┌──────────────┬────────────┬────────────┐
│ 세그먼트 번호 │ 페이지 번호 │ 오프셋     │
└──────────────┴────────────┴────────────┘

1단계: 세그먼트 테이블에서 해당 세그먼트의 페이지 테이블 찾기
2단계: 페이지 테이블에서 물리 프레임 찾기
3단계: 오프셋으로 최종 주소 계산
```

구조

```
세그먼트 테이블
        ┌───────────────────┐
Code  → │ Page Table 주소   │──→ [Page Table for Code]
        ├───────────────────┤
Data  → │ Page Table 주소   │──→ [Page Table for Data]
        ├───────────────────┤
Stack → │ Page Table 주소   │──→ [Page Table for Stack]
        └───────────────────┘

각 세그먼트가 자체 페이지 테이블을 가짐
```

장점 결합

```
세그먼테이션의 장점:
✓ 논리적 구분 (코드/데이터/스택)
✓ 세그먼트별 권한 설정
✓ 세그먼트 단위 공유

페이징의 장점:
✓ 외부 단편화 없음
✓ 효율적인 물리 메모리 관리
✓ 스왑 용이
```

단점 보완

```
세그먼테이션 단점 (외부 단편화):
→ 페이징으로 해결 (세그먼트 내부를 페이지로 나눔)

페이징 단점 (논리적 구분 없음):
→ 세그먼테이션으로 해결 (세그먼트로 논리 구분)
```

### 실제 예: x86 아키텍처

```
Intel x86:
- 세그먼트 레지스터 존재 (CS, DS, SS, ES)
- 각 세그먼트 내에서 페이징 적용

현대 OS (Linux, Windows):
- 세그먼테이션은 최소한으로 사용 (flat model)
- 실질적으로 페이징 위주
- 세그먼트는 권한 분리 용도로만 활용
```

Flat Model

```
현대 OS에서는:

모든 세그먼트가 같은 범위를 가리킴:
Code Segment:  0x00000000 ~ 0xFFFFFFFF
Data Segment:  0x00000000 ~ 0xFFFFFFFF
Stack Segment: 0x00000000 ~ 0xFFFFFFFF

실질적으로 세그먼테이션 효과 없음
페이징만으로 메모리 관리
단, 세그먼트 권한(읽기/쓰기/실행)은 활용
```

요약

```
과거: 세그먼테이션 + 페이징 결합
    → 논리적 구분 + 단편화 해결

현대: 페이징 중심 + 세그먼테이션은 권한용
    → 단순화 + 성능
```

## 14. 자바/파이썬 힙 구조와 메모리 계층 요약

출처: `computer_science/chapter/chapter9/chapter9.md`

### 1. 자바/파이썬 힙 구조

```
고수준 언어는 대부분의 데이터를 힙에 저장한다.

Stack                     Heap
┌─────────────┐          ┌─────────────────┐
│ 기본형 변수  │          │ 모든 객체       │
│ 참조(포인터) │─────────→│ (new로 생성된 것)│
└─────────────┘          └─────────────────┘

자바: 기본형(int, long)만 스택, 나머지 힙
파이썬: 전부 힙 (숫자도 객체)

장점: 메모리 안전, 개발 편의
단점: GC 오버헤드, 힙 할당이 스택보다 느리다.
```

### 2. 가상 메모리 & 페이징

```
프로그램은 가상 주소를 사용한다.
실제 물리 메모리와 1:1 대응이 아니다.

프로그램이 보는 주소          실제 물리 메모리
┌─────────────────┐          ┌─────────────────┐
│ 0x00001000 ─────┼─────────→│ 0x85AF2000      │
│ 0x00002000 ─────┼─────────→│ 0x12340000      │
│ 0x00003000 ─────┼─────────→│ (디스크)        │
└─────────────────┘          └─────────────────┘
    연속된 것처럼 보임           실제론 흩어져 있음

페이지: 가상 메모리 단위 (4KB)
프레임: 물리 메모리 단위 (4KB)
```

### 3. Page Table, TLB, 스왑

```
메모리 접근 과정:

가상 주소 접근
      ↓
┌─────────────────────────────────────────────┐
│ TLB (하드웨어 캐시, 64~1024개)               │
│ 자주 쓰는 가상→물리 매핑 저장                │
│ 히트 → 바로 물리 주소                        │
│ 미스 → Page Table 조회                       │
└─────────────────────────────────────────────┘
      ↓ 미스 시
┌─────────────────────────────────────────────┐
│ Page Table (메모리에 존재, 배열 구조)         │
│ 가상 주소 상위 비트 = 인덱스 → O(1) 접근     │
│ 물리 메모리에 있음 → 물리 주소 반환          │
│ 디스크에 있음 → Page Fault 발생              │
└─────────────────────────────────────────────┘
      ↓ Page Fault 시
┌─────────────────────────────────────────────┐
│ 스왑 (Swap)                                  │
│ 1. 디스크에서 해당 페이지 로드               │
│ 2. 물리 메모리 부족하면 다른 페이지 내보냄   │
│ 3. LRU 등 알고리즘으로 스왑 대상 선정        │
└─────────────────────────────────────────────┘
      ↓
물리 주소 획득
      ↓
┌─────────────────────────────────────────────┐
│ CPU 캐시 (L1/L2/L3)                         │
│ 히트 → 데이터 바로 사용                      │
│ 미스 → RAM에서 가져옴                        │
└─────────────────────────────────────────────┘
```

OS 별도 관리:

```
Free Frame List: 비어있는 물리 프레임 목록 (연결 리스트)
LRU List: 스왑 후보 페이지 목록 (연결 리스트)
```

### 4. 하드웨어 병렬 비교 (CAM)

```
TLB는 CAM (Content Addressable Memory) 구조

일반 RAM: 인덱스 → 값 반환
CAM: 값 → 인덱스 반환 (내용으로 검색)

입력: 가상 페이지 번호

비교기 ─ [Page 0  | Frame 5] → 불일치
비교기 ─ [Page 7  | Frame 2] → 불일치
비교기 ─ [Page 15 | Frame 9] → 일치! ★
비교기 ─ [Page 99 | Frame 1] → 불일치

모든 비교기가 동시에 동작 → 1 클럭에 완료
```

### 5. 빅오 표기법의 한계

```
빅오 = 단일 스레드 순차 처리 가정

소프트웨어:
for (i = 0; i < N; i++) -> O(N)
    compare(arr[i])

하드웨어:
N개 비교기가 동시 동작 -> 1클럭 (O(1)?)

빅오가 적용 안되는 영역:
- 하드웨어 병렬 회로
- GPU병렬 처리
- SIMD 연산

대신 사용하는 지표:
- 클럭 사이클( cycles )
- 레이텐시(latency)
- 처리량 (throughput)
```

레이텐시 비교

```
TLB 히트:        1 cycle
L1 캐시:         4 cycles
L2 캐시:         12 cycles
L3 캐시:         40 cycles
RAM:             100+ cycles
디스크 (SSD):    수만 cycles
디스크 (HDD):    수백만 cycles
```

### 최종 요약

```
┌─────────────────────────────────────────────────────────┐
│ 고수준 언어 (자바/파이썬)                                │
│ - 힙 중심 메모리 사용                                    │
│ - GC가 관리                                             │
│ - 개발자는 메모리 직접 제어 안 함                        │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ OS (가상 메모리)                                        │
│ - 프로그램에게 연속된 메모리 환상 제공                   │
│ - 실제로는 페이지 단위로 흩어져 관리                     │
│ - 물리 메모리 부족 시 디스크로 스왑                      │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ 하드웨어 (CPU + 캐시)                                   │
│ - TLB: 주소 변환 캐싱 (CAM으로 병렬 비교)               │
│ - L1/L2/L3: 데이터 캐싱 (공간 지역성 활용)              │
│ - 빅오 개념 대신 클럭/레이턴시로 성능 측정               │
└─────────────────────────────────────────────────────────┘
```

## 15. 대용량 데이터 조회와 메모리 — 스트리밍·DTO 평탄화

출처: `computer_science/chapter/chapter9/chapter9-3.md`

### 데이터 조회 시 메모리 사용량 비교

```java
// 최악: 전체 로드 + JSON 변환 (2GB)
@GetMapping("/export-users")
public List<User> exportAllUsers() {
    List<User> users = userRepository.findAll(); // 1GB(객체)
    return users; // Spring이 Json 변환 1GB
}
//총 메모리: 2GB(객체 1GB + JSON 1GB)

// 나쁨 : 전체 로드 후 스트리밍 (1GB)
@GetMapping("/export-users")
public void exportAllUsers(HttpServletResponse response) {
    userRepository.findAll() // 여기서 이미 1GB 전체 로드!
        .stream()
        .forEach(user -> writeToResponse(user));
}
// 총 메모리: 1GB (findAll이 전체 로드)

// 좋음: DB 스트리밍 (~10MB)
@GetMapping("/export-users")
@Transactional(readOnly = true)
public void exportAllUsers(HttpServletResponse response) {
    userRepository.streamAll() //DB 커서 사용
        .forEach(user -> {
            writeToResponse(user);
            entityManager.detach(user);
        });
}
// 총 메모리: ~ 10MB (청크 단위로 처리)

// 페이징 반복 (1MB)
@GetMapping("/export-users")
public void exportAllUsers(HttpServletResponse response) {
    int page = 0;
    int size = 1000;
    Page<User> userPage;

    do {
        Pageable pageable = PageRequest.of(page, size);
        userPage = userRepository.findAll(pageable); // 1000개씩만

        userPage.forEach(user  -> writeToResponse(user));
        page++;
    } while (userPage.hasNext());
}
```

### Lazy Loading 프록시 vs DTO 평탄화

#### 1. Lazy Loading의 문제: 프록시 객체 구조

엔티티 구조

```java
@Entity
public class Order {
    @Id
    private Long id;
    private String orderNumber;

    @ManyToOne(fetch = FetchType.LAZY)
    private User user;

    @OneToMany(mappedBy = "order", fetch = FetchType.LAZY)
    private List<OrderItem> items; // 프록시 컬렉션
}

@Entity
public class OrderItem {
    @Id
    private Long id;
    private String productName;
    private Integer quantity;

    @ManyToOne(fetch = FetchType.LAZY)
    private Product product; //프록시 객체
```

Lazy Loading 시 메모리 구조

```java
@GetMapping("/orders/{userId}")
public List<Order> getOrders(@PathVariable Long userId) {
    List<Order> orders = orderRepository.findByUserId(userId);

    for (Order order : orders) {

    }
}
```

메모리 레이아웃

```
Memory Layout (흩어진 구조)
┌──────────────┐
│ Order 1      │ ──→ User (0x1000) ──→ Address (0x5000)
│ id: 1        │ ──→ items (0x2000) ──→ OrderItem 1 (0x3000) ──→ Product (0x6000)
└──────────────┘                      ──→ OrderItem 2 (0x4000) ──→ Product (0x7000)

┌──────────────┐
│ Order 2      │ ──→ User (0x8000)
│ id: 2        │ ──→ items (0x9000) ──→ OrderItem 3 (0xA000) ──→ Product (0xB000)
└──────────────┘
```

문제점:
1. 각 객체가 메모리에 흩어짐 -> 페이지 폴트 증가.
2. 포인터 추적 -> CPU 캐시 미스
3. N+1 쿼리 발생 -> DB 부하
4. Lazy 프록시 초기화 오버헤드

성능 문제 — Order 100개 조회 시:
- 쿼리 수: 1 (Order) + 100 (User) + 100 (Items) + 200 (Product) = 401번
- 메모리 접근: 각 연관 객체마다 포인터 역참조
- 페이지 폴트: 객체가 서로 다른 페이지에 있을 가능성 ↑

#### 2. DTO 평탄화: 성능 개선

DTO 구조

```java
// 평탄한 구조의 DTO
public class OrderDashboardDto {
    // Order 정보
    private Long orderId;
    private String orderNumber;
    private LocalDateTime orderDate;

    // User 정보 (평탄화)
    private Long userId;
    private String userName;
    private String userEmail;

    // OrderItem 정보 (평탄화)
    private String itemNames;  // "상품A, 상품B, 상품C"
    private Integer totalQuantity;

    // Product 정보 (집계)
    private Integer totalPrice;

    // 생성자
    public OrderDashboardDto(Long orderId, String orderNumber,
                             LocalDateTime orderDate, Long userId,
                             String userName, String userEmail,
                             String itemNames, Integer totalQuantity,
                             Integer totalPrice) {
        this.orderId = orderId;
        this.orderNumber = orderNumber;
        this.orderDate = orderDate;
        this.userId = userId;
        this.userName = userName;
        this.userEmail = userEmail;
        this.itemNames = itemNames;
        this.totalQuantity = totalQuantity;
        this.totalPrice = totalPrice;
    }
}
```

DTO 프로젝션 쿼리

```java
public interface OrderRepository extends JpaRepository<Order, Long> {

    // JPQL로 한 방 쿼리 + DTO 직접 매핑
    @Query("SELECT new com.example.dto.OrderDashboardDto(" +
           "o.id, o.orderNumber, o.orderDate, " +
           "u.id, u.name, u.email, " +
           "GROUP_CONCAT(i.productName), SUM(i.quantity), SUM(i.price)) " +
           "FROM Order o " +
           "JOIN o.user u " +
           "JOIN o.items i " +
           "WHERE o.userId = :userId " +
           "GROUP BY o.id, o.orderNumber, o.orderDate, u.id, u.name, u.email")
    List<OrderDashboardDto> findOrderDashboard(@Param("userId") Long userId);
}
```

네이티브 쿼리

```java
@Query(value =
    "SELECT " +
    "o.id as orderId, " +
    "o.order_number as orderNumber, " +
    "o.order_date as orderDate, " +
    "u.id as userId, " +
    "u.name as userName, " +
    "u.email as userEmail, " +
    "GROUP_CONCAT(oi.product_name) as itemNames, " +
    "SUM(oi.quantity) as totalQuantity, " +
    "SUM(oi.price) as totalPrice " +
    "FROM orders o " +
    "JOIN users u ON o.user_id = u.id " +
    "JOIN order_items oi ON o.id = oi.order_id " +
    "WHERE o.user_id = :userId " +
    "GROUP BY o.id, o.order_number, o.order_date, u.id, u.name, u.email",
    nativeQuery = true)
List<OrderDashboardDto> findOrderDashboardNative(@Param("userId") Long userId);
```

평탄화된 메모리 구조

```
Memory Layout (연속된 구조)
┌────────────────────────────────────────────────────────┐
│ OrderDashboardDto 1                                    │
│ [orderId|orderNum|date|userId|userName|items|total...] │
└────────────────────────────────────────────────────────┘
┌────────────────────────────────────────────────────────┐
│ OrderDashboardDto 2                                    │
│ [orderId|orderNum|date|userId|userName|items|total...] │
└────────────────────────────────────────────────────────┘
┌────────────────────────────────────────────────────────┐
│ OrderDashboardDto 3                                    │
│ [orderId|orderNum|date|userId|userName|items|total...] │
└────────────────────────────────────────────────────────┘

장점:
1. 모든 데이터가 하나의 객체에 모임 → 포인터 역참조 불필요
2. 메모리 지역성 ↑ → CPU 캐시 효율 ↑
3. 단일 쿼리 → DB 왕복 최소화
4. 프록시 객체 없음 → 초기화 오버헤드 제거
```

#### 3. 성능 비교

Lazy Loading(엔티티)

```java
@GetMapping("/dashboard")
public List<Order> getDashboard(@PathVariable Long userId) {
    List<Order> orders = orderRepository.findByUserId(userId);

    for (Order order : orders) {
        order.getUser().getName();  // Lazy 로딩
        for (OrderItem item : order.getItems()) {  // Lazy 로딩
            item.getProduct().getName();  // Lazy 로딩
        }
    }
    return orders;
}

// 성능 지표 (100개 Order 기준)
// - 쿼리 수: 401번
// - 메모리 접근: ~1,000번 (포인터 역참조)
// - 응답 시간: ~2,000ms
// - 메모리: ~50MB (객체 그래프)
```

DTO 평탄화

```java
@GetMapping("/dashboard")
public List<OrderDashboardDto> getDashboard(@PathVariable Long userId) {
    return orderRepository.findOrderDashboard(userId);
}

// 성능 지표 (100개 Order 기준)
// - 쿼리 수: 1번
// - 메모리 접근: ~100번 (직접 접근)
// - 응답 시간: ~50ms
// - 메모리: ~5MB (평탄한 DTO)
```

추가 최적화 QueryDsl

```java
public List<OrderDashboardDto> findOrderDashboard(Long userId) {
    return queryFactory
        .select(Projections.constructor(OrderDashboardDto.class,
            order.id,
            order.orderNumber,
            order.orderDate,
            user.id,
            user.name,
            user.email,
            Expressions.stringTemplate(
                "GROUP_CONCAT({0})", orderItem.productName
            ),
            orderItem.quantity.sum(),
            orderItem.price.sum()
        ))
        .from(order)
        .join(order.user, user)
        .join(order.items, orderItem)
        .where(order.userId.eq(userId))
        .groupBy(order.id, order.orderNumber, order.orderDate,
                 user.id, user.name, user.email)
        .fetch();
}
```

핵심 요약

| 항목 | Lazy Loading (엔티티) | DTO 평탄화 |
|------|---------------------|-----------|
| **쿼리 수** | N+1 문제 (수백 번) | 1번 |
| **메모리 구조** | 흩어진 객체 그래프 | 연속된 평탄 구조 |
| **메모리 접근** | 포인터 역참조 다수 | 직접 접근 |
| **CPU 캐시** | 미스 빈번 | 히트율 높음 |
| **페이지 폴트** | 자주 발생 | 거의 없음 |
| **메모리 사용** | \~50MB | \~5MB |
| **응답 속도** | \~2,000ms | \~50ms |

## 16. 엔디언 — 바이트 저장 순서

출처: `computer_science/chapter/chapter9/chapter9.py`

컴퓨터에서 수를 어떻게 쓸지에 대한 약속 — 리틀 엔디언, 빅 엔디언.

```python
a = 0x01020304
print(a)
# 16909060
```

이때 16진수 2자리는 1바이트를 나타내고 4바이트에 저장된다.
각 바이트에 1, 2, 3, 4가 저장된다.
이때 1, 2, 3, 4를 순서대로 저장하는 것을 빅 엔디언,
반대로 4, 3, 2, 1로 역순대로 저장하는 것을 리틀 엔디언이라 한다.
즉 우리가 사용하는 방식을 빅 엔디언이라 한다.

to_bytes() 함수를 이용하면 위 방식을 확인할 수 있다.

```python
print(a.to_bytes(4, 'big'))
# b'\x01\x02\x03\x04'
print(a.to_bytes(4, 'little'))
# b'\x04\x03\x02\x01'
```
