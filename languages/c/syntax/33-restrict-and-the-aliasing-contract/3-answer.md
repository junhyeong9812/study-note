# c/syntax/33 — `restrict` 와 앨리어싱 계약: 「**겹치지 않는다는 약속 — 지키는 것은 호출자다**」 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단은 **gcc (Ubuntu 13.3.0-6ubuntu2\~24.04.1) 13.3.0** 과
> **clang 18.1.3** · x86-64 Linux · glibc 에서 실제로 돌려 얻은 것이다. 기본은 `-std=c17 -Wall -Wextra -pedantic`.\
> 소스는 `s33a.c`\~`s33e.c` · `s33x.cpp`·`s33x2.cpp` 이고, 블록은 **전부 캡처 파일에서 조립**했다(손으로 옮긴 출력이 없다).\
> ★★ **판 격자** — 1·2번은 컴파일러 2 × `-O0`/`-O2`, 3·4번은 × `-O0`/`-O1`/`-O2`, 5번은 × sanitizer 2 × `-O0`/`-O2`.
> ★★★ **본체 창은 `-O2` 어셈블리.** ★★★ **3·4번의 값은 UB 의 한 판 결과**다 — 관찰로 읽는다.
> ★★★ **시간은 재지 않았다** — 「`restrict` 는 빠르다」는 이 문서의 주장이 아니다.
> ★★ **흔들리는 칸 / 안 흔들리는 칸**
>
> | 흔들린다(근거로 쓰지 않는다) | 안 흔들린다(근거로 쓴다) |
> |---|---|
> | ASan 리포트의 `==PID==` · 스택 줄의 주소 | ★★★ **어셈블리 전부** · 로드 수 격자 · 위반 호출의 값(이 판) · sanitizer 격자의 리포트 줄 수와 `run exit` · 리포트 이름과 `파일:줄` |
>
> ★★ **정규화 규칙 = 기본 둘(주소 · PID)뿐** — 위 표의 「흔들린다」와 같은 목록이다.

## 이 파일이 다시 싣는 소스

★ 5·7번의 sanitizer 리포트는 **소스 줄을 끼워 보여 주지 않는다** — 그래서 그 리포트를 낸 소스를 여기 한 번 더 싣는다(질문 파일의 것과 같다).

```c
/* s33b1.c */
int twice_read(const int *p, int *q) {
    int a = *p;
    *q = 0;
    int b = *p;
    return a + b;
}

int twice_read_r(const int *restrict p, int *restrict q) {
    int a = *p;
    *q = 0;
    int b = *p;
    return a + b;
}

void copy_plain(int *d, const int *s, int n) {
    for (int i = 0; i < n; i++) d[i] = s[i];
}

void copy_restrict(int *restrict d, const int *restrict s, int n) {
    for (int i = 0; i < n; i++) d[i] = s[i];
}
```

```c
/* s33b2.c */
#include <stdio.h>

int  twice_read(const int *p, int *q);
int  twice_read_r(const int *restrict p, int *restrict q);
void copy_plain(int *d, const int *s, int n);
void copy_restrict(int *restrict d, const int *restrict s, int n);

static void show(const char *tag, const int *a) {
    printf("%-14s", tag);
    for (int i = 0; i < 8; i++) printf(" %d", a[i]);
    printf("\n");
}

int main(void) {
    setvbuf(stdout, NULL, _IONBF, 0);
    int x = 7, *p = &x, *q = &x;           /* 두 포인터가 같은 x */
    printf("twice_read   (p, q) = %d\n", twice_read(p, q));
    x = 7;
    printf("twice_read_r (p, q) = %d\n", twice_read_r(p, q));

    int a[8], b[8];
    for (int i = 0; i < 8; i++) a[i] = b[i] = i;
    copy_plain(a + 1, a, 7);               /* 목적지가 원본보다 한 칸 뒤 */
    copy_restrict(b + 1, b, 7);
    show("copy_plain", a);
    show("copy_restrict", b);
    return 0;
}
```

```c
/* s33e.c */
#include <stdio.h>
#include <string.h>

static char a[64] = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyz";
static char b[64] = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyz";

int main(int argc, char **argv) {
    (void)argv;
    size_t n = 30 + (size_t)argc;          /* 컴파일러가 크기를 모르게 — 31 */
    memmove(a + 2, a, n);
    memcpy(b + 2, b, n);                   /* 겹친다 */
    printf("memmove : %s\n", a);
    printf("memcpy  : %s\n", b);
    printf("same?   : %s\n", strcmp(a, b) == 0 ? "yes" : "no");
    return 0;
}
```

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. `*p` 를 읽는 명령 — **`restrict` 없이 2 번 · 붙이면 `-O2` 에서 1 번(`add eax, eax`) · `-O0` 은 둘 다 2 번** ★★★

**출력**

```text
===== *p 를 읽는 명령 수 — 함수 4 × 컴파일러 2 × 최적화 2 (exit=0) =====
함수             | gcc -O0   | gcc -O2   | clang -O0 | clang -O2
twice_read       | 2 번      | 2 번      | 2 번      | 2 번     
twice_read_r     | 2 번      | 1 번      | 2 번      | 1 번     
restrict_p_only  | 2 번      | 1 번      | 2 번      | 1 번     
restrict_q_only  | 2 번      | 1 번      | 2 번      | 1 번     
(칸 = 그 함수에서 [rdi] 또는 [rax] 를 32비트 레지스터로 읽는 명령 수 — *p 를 메모리에서 읽은 횟수)
```

```text
===== gcc -std=c17 -O2 -S -masm=intel -fno-asynchronous-unwind-tables s33a.c -o - | grep -v -E '^[[:space:]]+\.|^[0-9]+:$' | expand (cc exit=0) =====
twice_read:
        endbr64
        mov     eax, DWORD PTR [rdi]
        mov     DWORD PTR [rsi], 0
        add     eax, DWORD PTR [rdi]
        ret
twice_read_r:
        endbr64
        mov     eax, DWORD PTR [rdi]
        mov     DWORD PTR [rsi], 0
        add     eax, eax
        ret
restrict_p_only:
        endbr64
        mov     eax, DWORD PTR [rdi]
        mov     DWORD PTR [rsi], 0
        add     eax, eax
        ret
restrict_q_only:
        endbr64
        mov     eax, DWORD PTR [rdi]
        mov     DWORD PTR [rsi], 0
        add     eax, eax
        ret
```

```text
===== clang -std=c17 -O2 -S -masm=intel -fno-asynchronous-unwind-tables s33a.c -o - | grep -v -E '^[[:space:]]+\.|^[0-9]+:$' | expand (cc exit=0) =====
twice_read:                             # @twice_read
# %bb.0:
        mov     eax, dword ptr [rdi]
        mov     dword ptr [rsi], 0
        add     eax, dword ptr [rdi]
        ret
.Lfunc_end0:
                                        # -- End function
twice_read_r:                           # @twice_read_r
# %bb.0:
        mov     eax, dword ptr [rdi]
        mov     dword ptr [rsi], 0
        add     eax, eax
        ret
.Lfunc_end1:
                                        # -- End function
restrict_p_only:                        # @restrict_p_only
# %bb.0:
        mov     eax, dword ptr [rdi]
        mov     dword ptr [rsi], 0
        add     eax, eax
        ret
.Lfunc_end2:
                                        # -- End function
restrict_q_only:                        # @restrict_q_only
# %bb.0:
        mov     eax, dword ptr [rdi]
        mov     dword ptr [rsi], 0
        add     eax, eax
        ret
.Lfunc_end3:
                                        # -- End function
```

**왜 그런가**

- ★★★ **`twice_read` 는 `*q = 0` 이 `*p` 를 바꿀 수 있어서 다시 읽는다** — 31편과 같다.
- ★★★ **`twice_read_r` 은 「`*q` 는 `*p` 와 다른 객체」를 믿어도 된다** — 겹친다면 **이미 UB** 이기 때문이다. 그래서 처음 읽은 `eax` 를 **`add eax, eax`** 로 두 번 쓴다. **두 컴파일러 같은 모양**이다.
- ★★ **`-O0` 은 네 함수 다 2 번** — `restrict` 는 **최적화의 허락**이지 명령이 아니다.
- ★★★ **「빨라졌다」는 적지 않는다** — 센 것은 **명령 수**다. 시간은 **재지 않았다.**

### 2. 한쪽만 — **둘 다 1 번 · `-std=c89` 는 에러** ★★

**출력**

```text
===== restrict 라는 낱말 — 판 4 (-pedantic -c s33a.c) (exit=0) =====
gcc    -std=c89  cc exit=1 · 에러 3
gcc    -std=c99  cc exit=0 · 에러 0
gcc    -std=c17  cc exit=0 · 에러 0
gcc    -std=c2x  cc exit=0 · 에러 0
clang  -std=c89  cc exit=1 · 에러 10
clang  -std=c99  cc exit=0 · 에러 0
clang  -std=c17  cc exit=0 · 에러 0
clang  -std=c2x  cc exit=0 · 에러 0
```

**왜 그런가**

- ★★★ **`restrict_p_only` · `restrict_q_only` 모두 `-O2` 에서 1 번**이다(1번 격자의 아래 두 줄).
- ★★ **형식 정의가 「고쳐지는 객체의 다른 모든 접근」을 묶는다** — `p` 만 `restrict` 여도, `*q = 0` 이 `*p` 의 객체를 고친다면 그 접근(`q` 는 `p` 에 기반하지 않는다)이 **이미 약속 위반**이다. `q` 만 `restrict` 인 경우도 **`*q` 가 고치는 객체를 `p` 로 읽는 것**이 위반이다.
- ★ **C89 에는 `restrict` 가 없다** — 두 컴파일러 다 `cc exit=1`. **C99 부터**다.

### 3. 같은 `x` — **`twice_read` 는 여섯 벌 `7` · `twice_read_r` 은 `-O0` `7` · `-O1`/`-O2` `14`** ★★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O2 s33b1.c s33b2.c -o x ; ./x (cc exit=0 · run exit=0) =====
twice_read   (p, q) = 7
twice_read_r (p, q) = 14
copy_plain     0 0 0 0 0 0 0 0
copy_restrict  0 0 1 2 3 4 5 6
```

```text
===== 약속을 어긴 호출 — 같은 x 를 두 포인터로 · 겹치는 두 배열 (두 파일 모두 -std=c17 -Wall -Wextra -pedantic + 최적화 수준) (exit=0) =====
--- gcc -O0
twice_read   (p, q) = 7
twice_read_r (p, q) = 7
copy_plain     0 0 0 0 0 0 0 0
copy_restrict  0 0 0 0 0 0 0 0
--- gcc -O1
twice_read   (p, q) = 7
twice_read_r (p, q) = 14
copy_plain     0 0 0 0 0 0 0 0
copy_restrict  0 0 0 0 0 0 0 0
--- gcc -O2
twice_read   (p, q) = 7
twice_read_r (p, q) = 14
copy_plain     0 0 0 0 0 0 0 0
copy_restrict  0 0 1 2 3 4 5 6
--- clang -O0
twice_read   (p, q) = 7
twice_read_r (p, q) = 7
copy_plain     0 0 0 0 0 0 0 0
copy_restrict  0 0 0 0 0 0 0 0
--- clang -O1
twice_read   (p, q) = 7
twice_read_r (p, q) = 14
copy_plain     0 0 0 0 0 0 0 0
copy_restrict  0 0 1 2 3 4 5 6
--- clang -O2
twice_read   (p, q) = 7
twice_read_r (p, q) = 14
copy_plain     0 0 0 0 0 0 0 0
copy_restrict  0 0 1 2 3 4 5 6
```

**왜 그런가**

- ★★★ **`twice_read` 는 UB 가 아니다** — `restrict` 가 없으니 겹쳐도 합법이고, **`7 + 0 = 7`** 이 옳은 답이다.
- ★★★ **`twice_read_r(p, q)` 는 UB 다** — 판단의 근거는 **값이 아니라 규칙**이다(`*q = 0` 이 `p` 로 읽는 객체를 고쳤고, `q` 는 `p` 에 기반하지 않는다).
- ★★ **`14` 는 1번의 번역 그대로다** — 처음 읽은 `7` 을 두 번 더했다.
- ★★★ **「`-O0` 이면 안전하다」는 틀린 말이다** — UB 의 값이 판마다 갈린다는 것은 **어떤 판도 기준이 아니라는 뜻**이다. 여기에는 처방이 없다.

### 4. 겹치는 복사 — **`copy_plain` 은 여섯 벌 `0 0 0 …` · `copy_restrict` 는 `memcpy` 로 바뀐 판에서 `0 0 1 2 3 4 5 6`** ★★★

**출력**

```text
===== 약속을 어긴 호출 — 같은 x 를 두 포인터로 · 겹치는 두 배열 (두 파일 모두 -std=c17 -Wall -Wextra -pedantic + 최적화 수준) (exit=0) =====
--- gcc -O0
twice_read   (p, q) = 7
twice_read_r (p, q) = 7
copy_plain     0 0 0 0 0 0 0 0
copy_restrict  0 0 0 0 0 0 0 0
--- gcc -O1
twice_read   (p, q) = 7
twice_read_r (p, q) = 14
copy_plain     0 0 0 0 0 0 0 0
copy_restrict  0 0 0 0 0 0 0 0
--- gcc -O2
twice_read   (p, q) = 7
twice_read_r (p, q) = 14
copy_plain     0 0 0 0 0 0 0 0
copy_restrict  0 0 1 2 3 4 5 6
--- clang -O0
twice_read   (p, q) = 7
twice_read_r (p, q) = 7
copy_plain     0 0 0 0 0 0 0 0
copy_restrict  0 0 0 0 0 0 0 0
--- clang -O1
twice_read   (p, q) = 7
twice_read_r (p, q) = 14
copy_plain     0 0 0 0 0 0 0 0
copy_restrict  0 0 1 2 3 4 5 6
--- clang -O2
twice_read   (p, q) = 7
twice_read_r (p, q) = 14
copy_plain     0 0 0 0 0 0 0 0
copy_restrict  0 0 1 2 3 4 5 6
```

```text
===== gcc -std=c17 -O2 -S -masm=intel -fno-asynchronous-unwind-tables s33b1.c -o - | grep -v -E '^[[:space:]]+\.|^[0-9]+:$' | expand | sed -n '/^copy_restrict:/,$p' (cc exit=0) =====
copy_restrict:
        endbr64
        test    edx, edx
        jle     .L8
        mov     edx, edx
        sal     rdx, 2
        jmp     memcpy@PLT
.L8:
        ret
```

```text
===== clang -std=c17 -O2 -S -masm=intel -fno-asynchronous-unwind-tables s33b1.c -o - | grep -v -E '^[[:space:]]+\.|^[0-9]+:$' | expand | sed -n '/^copy_restrict:/,/End function/p' (cc exit=0) =====
copy_restrict:                          # @copy_restrict
# %bb.0:
        test    edx, edx
        jle     .LBB3_1
# %bb.2:
        mov     edx, edx
        shl     rdx, 2
        jmp     memcpy@PLT                      # TAILCALL
.LBB3_1:
        ret
.Lfunc_end3:
                                        # -- End function
```

```text
===== gcc -std=c17 -O2 -S -masm=intel -fno-asynchronous-unwind-tables s33b1.c -o - | grep -v -E '^[[:space:]]+\.|^[0-9]+:$' | expand | sed -n '/^copy_plain:/,/^copy_restrict:/p' (cc exit=0) =====
copy_plain:
        endbr64
        test    edx, edx
        jle     .L4
        movsx   rdx, edx
        xor     eax, eax
        lea     rcx, 0[0+rdx*4]
.L6:
        mov     edx, DWORD PTR [rsi+rax]
        mov     DWORD PTR [rdi+rax], edx
        add     rax, 4
        cmp     rax, rcx
        jne     .L6
.L4:
        ret
copy_restrict:
```

**왜 그런가**

- ★★★ **`copy_plain` 의 `0 0 0 …` 이 C 의 뜻**이다 — 앞에서부터 한 칸씩 `d[i] = s[i]` 를 하면 `a[0]` 이 끝까지 번진다.
- ★★★ **`copy_restrict` 는 `-O2` 에서 루프가 없다** — 두 컴파일러 다 **`jmp memcpy`**. 겹치지 않는다고 믿으니 **통째 복사**로 바꿨다.
- ★★ **`0 0 1 2 3 4 5 6` 은 `memmove(b + 1, b, …)` 의 결과와 같다** — 이 glibc 의 `memcpy` 가 겹침을 **그렇게 처리한** 관찰이다(7번 격자). **표준의 성질이 아니라 이 라이브러리 판의 성질**이다.
- ★★ **gcc `-O1` 은 `0 0 0 …`** 이다 — 그 판은 루프를 안 바꿨다. **같은 UB 가 판마다 다른 얼굴**이다.

### 5. sanitizer 격자 — **답한 칸 1 / 8 · 그것도 `memcpy` 를 본 것** ★★

**출력**

```text
===== sanitizer 탐침 — 컴파일러 2 × sanitizer 2 × 최적화 2 (s33b1.c + s33b2.c) (exit=0) =====
gcc    address    -O0  run exit=0   리포트 0줄 | 
        twice_read   (p, q) = 7
        twice_read_r (p, q) = 7
        copy_plain     0 0 0 0 0 0 0 0
        copy_restrict  0 0 0 0 0 0 0 0
gcc    address    -O2  run exit=0   리포트 0줄 | 
        twice_read   (p, q) = 7
        twice_read_r (p, q) = 14
        copy_plain     0 0 0 0 0 0 0 0
        copy_restrict  0 0 0 0 0 0 0 0
gcc    undefined  -O0  run exit=0   리포트 0줄 | 
        twice_read   (p, q) = 7
        twice_read_r (p, q) = 7
        copy_plain     0 0 0 0 0 0 0 0
        copy_restrict  0 0 0 0 0 0 0 0
gcc    undefined  -O2  run exit=0   리포트 0줄 | 
        twice_read   (p, q) = 7
        twice_read_r (p, q) = 14
        copy_plain     0 0 0 0 0 0 0 0
        copy_restrict  0 0 0 0 0 0 0 0
clang  address    -O0  run exit=0   리포트 0줄 | 
        twice_read   (p, q) = 7
        twice_read_r (p, q) = 7
        copy_plain     0 0 0 0 0 0 0 0
        copy_restrict  0 0 0 0 0 0 0 0
clang  address    -O2  run exit=1   리포트 1줄 | ERROR: AddressSanitizer: memcpy-param-overlap
        twice_read   (p, q) = 7
        twice_read_r (p, q) = 14
clang  undefined  -O0  run exit=0   리포트 0줄 | 
        twice_read   (p, q) = 7
        twice_read_r (p, q) = 7
        copy_plain     0 0 0 0 0 0 0 0
        copy_restrict  0 0 0 0 0 0 0 0
clang  undefined  -O2  run exit=0   리포트 0줄 | 
        twice_read   (p, q) = 7
        twice_read_r (p, q) = 7
        copy_plain     0 0 0 0 0 0 0 0
        copy_restrict  0 0 0 0 0 0 0 0
답한 칸 1 / 8
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -O2 -g -fsanitize=address -ffile-prefix-map="$PWD"=. s33b1.c s33b2.c -o x && ./x 2>&1 >/dev/null | grep -oE '^==[0-9]+==ERROR: AddressSanitizer: [a-z-]+|^ +#1 .*|^SUMMARY: AddressSanitizer: [a-z-]+' (exit=1) =====
==487774==ERROR: AddressSanitizer: memcpy-param-overlap
    #1 0x63f49b4d1d9f in copy_restrict s33b1.c:20:38
SUMMARY: AddressSanitizer: memcpy-param-overlap
```

```text
===== sanitizer 를 켜면 copy_restrict 의 번역이 바뀌나 — 컴파일러 2 × sanitizer 3 (-std=c17 -O2 -S) (exit=0) =====
컴파일러 sanitizer (-O2)  | copy_restrict 몸통에서 memcpy 가 나오는 줄
gcc      (없음)           | 1 줄
gcc      address          | 0 줄
gcc      undefined        | 0 줄
clang    (없음)           | 1 줄
clang    address          | 2 줄
clang    undefined        | 0 줄
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -O2 -fsanitize=undefined s33b1.c s33b2.c -o x ; ./x (cc exit=0 · run exit=0) =====
twice_read   (p, q) = 7
twice_read_r (p, q) = 7
copy_plain     0 0 0 0 0 0 0 0
copy_restrict  0 0 0 0 0 0 0 0
```

**왜 그런가**

- ★★★ **리포트를 낸 칸은 clang `-O2` ASan 하나** — **`memcpy-param-overlap`**, `#1` 이 `copy_restrict s33b1.c:20:38`.
- ★★★ **`restrict` 를 본 것이 아니다** — 4번에서 루프가 `memcpy` 가 됐고, ASan 은 **`memcpy` 호출을 가로채 겹침을 잰다.** `twice_read_r` 은 **여덟 칸 전부 침묵**이다.
- ★★ **gcc ASan 이 침묵한 이유** — 어셈블리 격자에서 **`gcc address` 의 `memcpy` 줄이 0** 이다. ASan 을 켜자 그 판은 루프를 `memcpy` 로 **안 바꿨다.** UBSan 을 켜면 **두 컴파일러 다 0 줄**이다.
- ★★ **clang UBSan `-O2` 의 `7`** — sanitizer 없는 clang `-O2` 는 `14` 였다. **플래그 하나로 값이 바뀌었으니 번역이 바뀐 것**이다. **sanitizer 판에서 값이 맞았다는 것은 아무것도 증명하지 않는다.**
- ★ 이것은 **「창을 바꿔 답한」 제5의 상태**다 — 답한 것은 `restrict` 검사기가 아니라 **컴파일러가 우연히 연 `memcpy` 창**이다.

### 6. 컴파일러 경고 — **gcc 는 `by_address` 만(`-Wrestrict`) · clang 0 · 셋 다 `cc exit=0`** ★★

**출력**

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O2 -c s33d.c -o /dev/null (cc exit=0) =====
s33d.c: In function ‘by_address’:
s33d.c:5:29: warning: passing argument 2 to ‘restrict’-qualified parameter aliases with argument 1 [-Wrestrict]
    5 |     return twice_read_r(&x, &x);
      |                         ~~  ^~
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 -c s33d.c -o /dev/null (cc exit=0) =====
s33d.c: In function ‘by_address’:
s33d.c:5:29: warning: passing argument 2 to ‘restrict’-qualified parameter aliases with argument 1 [-Wrestrict]
    5 |     return twice_read_r(&x, &x);
      |                         ~~  ^~
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -O2 -c s33d.c -o /dev/null (cc exit=0) =====
```

**왜 그런가**

- ★★★ **gcc 의 `-Wrestrict` 는 글자로 같은 인자만 본다** — `&x, &x`. **`p` 와 `q` 가 둘 다 `&x`** 인 `by_variables` 는 경고 0건이다. `-O0` 에서도 같다.
- ★★ **clang 은 두 함수 다 0건** — 이 판의 clang 에는 대응하는 경고가 없다(`-Wall -Wextra -pedantic`).
- ★ **경고여도 `cc exit=0`** — 빌드는 통과한다.

### 7. `memcpy` / `memmove` — **서명의 `__restrict` 가 「겹치면 UB」를 적는다 · 이 glibc 는 같은 글자 · ASan 은 둘 다 잡는다** ★★

**출력**

```text
===== grep -n -A1 -E '^extern void \*(memcpy|memmove) ' /usr/include/string.h | expand (exit=0) =====
43:extern void *memcpy (void *__restrict __dest, const void *__restrict __src,
44-                  size_t __n) __THROW __nonnull ((1, 2));
--
47:extern void *memmove (void *__dest, const void *__src, size_t __n)
48-     __THROW __nonnull ((1, 2));
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O2 s33e.c -o x ; ./x (cc exit=0 · run exit=0) =====
memmove : ABABCDEFGHIJKLMNOPQRSTUVWXYZ01234789abcdefghijklmnopqrstuvwxyz
memcpy  : ABABCDEFGHIJKLMNOPQRSTUVWXYZ01234789abcdefghijklmnopqrstuvwxyz
same?   : yes
```

```text
===== 겹치는 영역에 memmove 와 memcpy — 컴파일러 2 × 최적화 2 (exit=0) =====
--- gcc -O0 (경고 0)
memmove : ABABCDEFGHIJKLMNOPQRSTUVWXYZ01234789abcdefghijklmnopqrstuvwxyz
memcpy  : ABABCDEFGHIJKLMNOPQRSTUVWXYZ01234789abcdefghijklmnopqrstuvwxyz
same?   : yes
--- gcc -O2 (경고 0)
memmove : ABABCDEFGHIJKLMNOPQRSTUVWXYZ01234789abcdefghijklmnopqrstuvwxyz
memcpy  : ABABCDEFGHIJKLMNOPQRSTUVWXYZ01234789abcdefghijklmnopqrstuvwxyz
same?   : yes
--- clang -O0 (경고 0)
memmove : ABABCDEFGHIJKLMNOPQRSTUVWXYZ01234789abcdefghijklmnopqrstuvwxyz
memcpy  : ABABCDEFGHIJKLMNOPQRSTUVWXYZ01234789abcdefghijklmnopqrstuvwxyz
same?   : yes
--- clang -O2 (경고 0)
memmove : ABABCDEFGHIJKLMNOPQRSTUVWXYZ01234789abcdefghijklmnopqrstuvwxyz
memcpy  : ABABCDEFGHIJKLMNOPQRSTUVWXYZ01234789abcdefghijklmnopqrstuvwxyz
same?   : yes
```

```text
===== gcc -std=c17 -Wall -Wextra -pedantic -O0 -g -fsanitize=address -ffile-prefix-map="$PWD"=. s33e.c -o x && ./x 2>&1 >/dev/null | grep -oE '^==[0-9]+==ERROR: AddressSanitizer: [a-z-]+|^ +#1 .*|^SUMMARY: AddressSanitizer: [a-z-]+' (exit=1) =====
==487989==ERROR: AddressSanitizer: memcpy-param-overlap
    #1 0x5cc438b9d288 in main s33e.c:11
SUMMARY: AddressSanitizer: memcpy-param-overlap
```

```text
===== clang -std=c17 -Wall -Wextra -pedantic -O0 -g -fsanitize=address -ffile-prefix-map="$PWD"=. s33e.c -o x && ./x 2>&1 >/dev/null | grep -oE '^==[0-9]+==ERROR: AddressSanitizer: [a-z-]+|^ +#1 .*|^SUMMARY: AddressSanitizer: [a-z-]+' (exit=1) =====
==487994==ERROR: AddressSanitizer: memcpy-param-overlap
    #1 0x59d16745a77f in main s33e.c:11:5
SUMMARY: AddressSanitizer: memcpy-param-overlap
```

**왜 그런가**

- ★★★ **`memcpy` 의 두 포인터에만 `__restrict`** 가 있다 — 「두 영역이 겹치지 않는다」를 **서명이 요구**한다. 표준 문장도 **겹치면 UB** 다. `memmove` 는 **약속이 없고**, 겹쳐도 임시 배열을 거친 것처럼 복사한다.
- ★★ **이 glibc 판에서는 겹친 `memcpy` 가 `memmove` 와 같았다**(네 벌 `same? : yes`) — **관찰**이다. 다른 libc 에서 같다는 근거가 없다.
- ★★ **ASan 은 두 컴파일러 다 `memcpy-param-overlap`** 으로 잡는다(`s33e.c:11`).

### 8. C++ — **`restrict` 는 에러 · `__restrict__` 는 `-pedantic` 에서도 조용하다** ★

**출력**

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic -c s33x.cpp -o /dev/null (cc exit=1) =====
s33x.cpp:1:38: error: expected ‘,’ or ‘...’ before ‘p’
    1 | int twice_read_r(const int *restrict p, int *restrict q) {
      |                                      ^
s33x.cpp: In function ‘int twice_read_r(const int*)’:
s33x.cpp:2:14: error: ‘p’ was not declared in this scope
    2 |     int a = *p;
      |              ^
s33x.cpp:3:6: error: ‘q’ was not declared in this scope
    3 |     *q = 0;
      |      ^
s33x.cpp:1:29: warning: unused parameter ‘restrict’ [-Wunused-parameter]
    1 | int twice_read_r(const int *restrict p, int *restrict q) {
      |                  ~~~~~~~~~~~^~~~~~~~
```

```text
===== clang++ -std=c++17 -Wall -Wextra -pedantic -c s33x.cpp -o /dev/null (cc exit=1) =====
s33x.cpp:1:38: error: expected ')'
    1 | int twice_read_r(const int *restrict p, int *restrict q) {
      |                                      ^
s33x.cpp:1:17: note: to match this '('
    1 | int twice_read_r(const int *restrict p, int *restrict q) {
      |                 ^
s33x.cpp:2:14: error: use of undeclared identifier 'p'
    2 |     int a = *p;
      |              ^
s33x.cpp:3:6: error: use of undeclared identifier 'q'
    3 |     *q = 0;
      |      ^
s33x.cpp:4:17: error: use of undeclared identifier 'p'
    4 |     return a + *p;
      |                 ^
s33x.cpp:1:29: warning: unused parameter 'restrict' [-Wunused-parameter]
    1 | int twice_read_r(const int *restrict p, int *restrict q) {
      |                             ^
1 warning and 4 errors generated.
```

```text
===== g++ -std=c++17 -Wall -Wextra -pedantic -c s33x2.cpp -o /dev/null (cc exit=0) =====
```

```text
===== clang++ -std=c++17 -Wall -Wextra -pedantic -c s33x2.cpp -o /dev/null (cc exit=0) =====
```

```text
===== g++ -std=c++17 -O2 -S -masm=intel -fno-asynchronous-unwind-tables s33x2.cpp -o - | grep -v -E '^[[:space:]]+\.|^[0-9]+:$' | expand (cc exit=0) =====
_Z12twice_read_rPKiPi:
.LFB0:
        endbr64
        mov     eax, DWORD PTR [rdi]
        mov     DWORD PTR [rsi], 0
        add     eax, eax
        ret
.LFE0:
```

**왜 그런가**

- ★★ **C++17 에 `restrict` 키워드는 없다** — g++ 는 그것을 **매개변수 이름**으로 읽어 `p` 가 선언되지 않았다고 했고, 둘 다 `cc exit=1`.
- ★ **`__restrict__` 는 구현 확장**이라 `-pedantic` 이 문제 삼지 않는다 — 두 컴파일러 `cc exit=0` · 경고 0. 번역도 C 와 같다(`add eax, eax`).

### 9. 한정자 세 개 ★★

**왜 그런가**

- ★★★ **`const`** — 「**내가** 이 경로로 안 고친다」(31편). **`volatile`** — 「**컴파일러는** 이 접근을 지우거나 합치지 마라」(32편). **`restrict`** — 「**부르는 쪽은** 이 객체를 다른 경로로 건드리지 않게 넘긴다」.
- ★★ **31편의 `twice_read` 가 두 번 읽은 이유** — `const` 는 **남의 쓰기를 막지 않는다.** `restrict` 는 **남의 쓰기가 있으면 UB** 로 만들어 다시 읽을 필요를 없앴다.
- ★ **방향** — `volatile` 은 로드를 **남긴다(늘린다)**, `restrict` 는 로드를 **없앨 수 있게** 한다.

### 10. 다섯 층 — **UB 가 본체 · 표준은 두 줄 · 조건부 표준·미명시는 비었다** ★★★

**왜 그런가**

- **표준** — `restrict` 의 형식 정의 · **지워도 뜻이 같다** · `memcpy` 겹침 UB · `memmove` · C99 부터.
- **조건부 표준** — 해당 없음.
- **구현 정의** — `__restrict__` 확장 · 명령 선택(`add eax, eax` · `jmp memcpy`) · `-Wrestrict` 의 유무와 범위.
- **미명시** — 이 편이 던진 것 중에는 없음.
- **UB** — 약속을 어긴 모든 접근 · 겹친 `memcpy`.
- ★★★ **「지워도 뜻이 같다」** — 적격한 프로그램에서는 `restrict` 가 **아무 차이도 만들지 않는다.** 차이는 **어긴 프로그램에서만** 난다. 그래서 이 주제의 모든 흥미로운 출력은 **UB 칸**에 있다.
- ★★ **침묵** — 표준: 「빠진 `restrict`」를 말하는 도구 없음 · 구현 정의: clang 경고 없음 · UB: **탐침 8칸 중 1칸**, `twice_read_r` 은 **전부 침묵** · sanitizer 가 **증상을 지운 칸**.
- ★★ **「종료 코드 0인데 ill-formed」 새 항목은 없다** — 위반은 전부 **적격한 프로그램의 실행 문제**다. 대신 **「종료 코드 0인데 UB」가 셋**이다(`twice_read_r(p,q)` · `copy_restrict` · 겹친 `memcpy`).

### 11. 경계 ★

**왜 그런가**

- **타입이 다른 포인터의 앨리어싱** — 목록의 **55번 주제**.
- **`const`** — [31번 형제](../31-const-and-pointer-const-placement/) · **`volatile`** — [32번 형제](../32-what-volatile-actually-guarantees/).
- ★ 이 주제가 책임지는 것 — ① **번역이 무엇으로 바뀌나**(로드 수 · `jmp memcpy`) ② **어기면 무엇이 나오나**(관찰 · 처방 없음) ③ **누가 지켜 주나**(거의 아무도 — 서명을 읽는 사람).

## 실행 검증

| 소스 | 무엇을 확인했나 | 몇 벌 돌렸나 |
|---|---|---|
| `s33a.c` | ★★★ `*p` 읽기 **2 → 1**(`-O2`) · 한쪽만 붙여도 1 · `-O0` 2 · C89 에러 | 어셈블리 `-O2` 2 · `-O0` 1 · 격자 4벌 × 4함수 · 판 4 × 2 |
| `s33b1.c`·`s33b2.c` | ★★★ `7`/`14` · `copy_plain` `0 …` · `copy_restrict` `jmp memcpy` 판에서 `0 0 1 2 …` · sanitizer **1 / 8** | 격자 6벌 · 실행 2 · 어셈블리 3 · sanitizer 8칸 · 번역 격자 6 |
| `s33d.c` | ★★ gcc `-Wrestrict` 는 글자로 같은 인자만 · clang 0 | 3 |
| `s33e.c` | ★★ 헤더 서명 · 이 glibc 에서 `same? : yes` · ASan 두 컴파일러 | 격자 4 · 실행 1 · ASan 2 |
| `s33x.cpp`·`s33x2.cpp` | ★ C++ `restrict` 에러 · `__restrict__` 조용 · 같은 번역 | 4 · 어셈블리 1 |

**재대조** — 제출 전 캡처를 처음부터 다시 돌려 `normalize-shaky.py`(기본 규칙만)로 대조했다. **흔들린 것은 ASan 의 PID 와 주소뿐**이어야 하고, 그랬다.

**구현 의존 항목** — 다음은 **이 환경에서만** 그렇다.

- ★★★ **1·4번 어셈블리** — 명령 선택과 「`memcpy` 로 바꾸나」는 컴파일러와 플래그의 것이다.
- ★★★ **3·4번의 값** — UB 의 이 판 결과다. 결론은 「**어긴 호출은 뜻이 없다**」까지다.
- ★★ **5번의 1칸** — 「이 판의 이 번역」이 `memcpy` 를 불렀기 때문에 열린 창이다.
- ★★ **7번의 `same? : yes`** — 이 glibc 의 관찰이다.
- ★ **6번의 경고 범위** — gcc 13 의 `-Wrestrict` 가 **보이는 범위**다.

**`restrict` 의 형식 정의 · 적격한 프로그램에서 지워도 뜻이 같다는 것 · 겹친 `memcpy` 가 UB 인 것 · C99 부터 키워드인 것은 구현 의존이 아니다.**\
어느 C 구현에서도 같다.

**안 돌려 본 것 / 못 잰 것**

- **안 돌려 본 것** — 블록 스코프 `restrict` 지역 포인터 · `int a[restrict 10]` · 벡터화된 `restrict` 루프(`memcpy` 변환을 막은 판) · `-fanalyzer`·`--analyze` 의 블록 캡처 · `-O3`.
- ★ **못 잰 것** — **시간**(규칙으로 안 쟀다) · 다른 libc 의 겹친 `memcpy`(이 머신에는 glibc 뿐).

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★★ **3·4·5번 격자** — 번역이 바뀌면 위반의 얼굴이 바뀐다. 특히 **sanitizer 판의 `memcpy` 변환 여부**.
- ★★ **6번** — clang 이 `-Wrestrict` 류를 들여올 수 있다.
- ★ **7번** — glibc 판이 오르면 겹친 `memcpy` 의 결과가 달라질 수 있다.
- **`restrict` 의 규칙 자체는 다시 돌릴 필요가 없다** — C99 이후 바뀐 적이 없다.
