# csharp/syntax/15 — 접근 한정자와 어셈블리 경계 — 질문

> 복습은 항상 이 파일에서 시작한다. **맨기억으로 답을 시도**하고,
> 막히면 [2-summary.md](2-summary.md)를 힌트로, 최후에만 [3-answer.md](3-answer.md)를 연다.
> 정답까지 봤던 질문은 아래 복습 기록에 "틀림"으로 표시한다.
> 이 주제의 질문은 「**어느 멤버가 막히나**」가 절반이고 「**진단 코드가 무엇으로 바뀌나**」가 나머지 절반이다.
> **환경** — .NET SDK 10.0.401 · 런타임 10.0.12 · `net10.0` · linux-x64 ·
> Roslyn `csc` 를 직접 부른다 · `-preferreduilang:en-US` · Java 대비는 **javac 21.0.5**.
> ★★★ **어셈블리를 둘 만들어 던졌다** — `liba.dll`(라이브러리)과 `appb.dll`(참조하는 쪽).
> **한 파일로는 물을 수 없는 유일한 주제**다.
> ★★★ **본체 창은 ② 진단 격자다.** 같은 소스를 **같은 어셈블리에 넣었을 때와 다른 어셈블리에서 참조할 때**
> 진단이 달라지는 것이 이 주제의 답이다.
> ★★ **짝이 되는 창은 ③ 리플렉션**(2번) — C# 낱말로는 못 읽히는 **`OR`/`AND`** 를 메타데이터가 적어 준다.
> ★ **「부적용인 창」이 둘 있다** — **① IL 덤프**와 **④ 할당 바이트.**
> 접근 한정자는 **멤버 본문을 한 글자도 안 바꾼다.** **「안 쟀다」가 아니라 「잴 것이 없다」다.**
> 선행 — [12번](../12-class-fields-constructors-this-base/)(클래스 문법)·[13번](../13-properties-init-required-field/)(접근자 접근성).
> 이어지는 것 — [16번](../16-inheritance-virtual-override-abstract-sealed-new/)(`protected` 를 설계로 쓰는 법).
> 대비 — Java 갈래 목록([`java/syntax/README.md`](../../../java/syntax/README.md))의 **10번**([`10-access-modifiers/`](../../../java/syntax/10-access-modifiers/)).

## 질문

<!-- 질문 하나 = "?" 하나 = 한 줄. 유형: (예측) / (왜) / (경계) / (연결) -->

### 1. ★★★ 같은 어셈블리에서 막히는 멤버는 몇이나 되나 (예측)

```csharp
// cs15b-vault.cs
public class Vault {
    public              int Pub      = 1;
    protected           int Prot     = 2;
    internal            int Intl     = 3;
    protected internal  int ProtIntl = 4;
    private protected   int PrivProt = 5;
    private             int Priv     = 6;

    public string Read() => $"{Pub}{Prot}{Intl}{ProtIntl}{PrivProt}{Priv}";
}
```

```csharp
// cs15b-same.cs
class Outsider {            // 같은 어셈블리 · 파생 아님
    void Touch(Vault v) {
        _ = v.Pub;
        _ = v.Prot;
        _ = v.Intl;
        _ = v.ProtIntl;
        _ = v.PrivProt;
        _ = v.Priv;
    }
}
class Heir : Vault {        // 같은 어셈블리 · 파생
    void Touch() {
        _ = Pub;
        _ = Prot;
        _ = Intl;
        _ = ProtIntl;
        _ = PrivProt;
        _ = Priv;
    }
}
```

- **에러가 몇 건** 나고 **어느 필드**에 붙는가 — 두 클래스에서 각각?
- ★★ 진단 코드는 **한 가지인가 여러 가지인가**?
- ★ `Outsider` 와 `Heir` 에서 갈리는 필드 **둘**은 무엇인가?

### 2. ★★★ 같은 소스를 다른 어셈블리에서 참조하면 (예측)

```csharp
// cs15b-other.cs
class OutsiderB {           // 다른 어셈블리 · 파생 아님
    void Touch(Vault v) {
        _ = v.Pub;
        _ = v.Prot;
        _ = v.Intl;
        _ = v.ProtIntl;
        _ = v.PrivProt;
        _ = v.Priv;
    }
}
class HeirB : Vault {       // 다른 어셈블리 · 파생
    void Touch() {
        _ = Pub;
        _ = Prot;
        _ = Intl;
        _ = ProtIntl;
        _ = PrivProt;
        _ = Priv;
    }
}
class Program { static void Main() { } }
```

- **에러가 몇 건** 나는가 — 1번보다 늘었는가?
- ★★★ `Intl` 과 `Priv` 의 진단 코드가 **1번과 같은가 다른가** — 다르다면 무엇이 달라지는 뜻인가?
- ★★★ `ProtIntl` 은 `HeirB`(파생)에서 통과하는가?
- ★★★ `PrivProt` 은 `HeirB`(파생)에서 통과하는가 — 둘이 갈린다면 왜인가?

### 3. ★★★ `InternalsVisibleTo` 는 무엇을 뚫나 (예측)

```csharp
// cs15b-ivt.cs
using System.Runtime.CompilerServices;
[assembly: InternalsVisibleTo("appb")]
```

```csharp
// cs15b-friend.cs
using System;
class Friend {                          // 친구 어셈블리 · 파생 아님
    public static string Touch(Vault v) => $"{v.Pub} {v.Intl} {v.ProtIntl}";
}
class Program { static void Main() => Console.WriteLine(Friend.Touch(new Vault())); }
```

- **이 어트리뷰트가 없을 때와 있을 때** `cc exit` 가 어떻게 갈리는가?
- ★★★ 뚫린 멤버는 **무엇과 무엇**인가 — 찍히는 세 숫자는?
- ★★ `private protected` 는 친구 어셈블리에서 **파생이면** 통과하는가, **파생이 아니면** 통과하는가?
- ★★★ 막힌 쪽의 진단 문구가 **공개 키**를 말하는데, 이 판에서 두 어셈블리의 `PublicKeyToken` 은 무엇인가?

### 4. ★★ 한정자를 안 적으면 세 자리가 각각 무엇이 되나 (예측)

```csharp
// cs15b-def.cs
class TopDefault { public int N = 1; }              // 최상위 타입 — 한정자 없음
public class Wrapper {
    class NestedDefault { }                         // 중첩 타입 — 한정자 없음
    int memberDefault = 2;                          // 멤버 — 한정자 없음
    public string Show() => $"{memberDefault} {new NestedDefault()}";
}
```

```csharp
// cs15b-defuse.cs
class Probe {
    void Touch(Wrapper w) { _ = w.memberDefault; }
    void MakeTop()        { _ = new TopDefault();  }
}
class Program { static void Main() { } }
```

- **같은 어셈블리** 판에서 에러가 **몇 건** 나고 어디에 붙는가?
- ★★★ **다른 어셈블리** 판에서는 몇 건인가 — 늘어난 한 건은 무엇인가?
- ★★★ **최상위 타입 · 중첩 타입 · 멤버**의 기본값을 각각 댈 수 있는가?
- ★ 중첩 타입의 기본값은 이 블록이 아니라 **어느 블록**이 증명하는가?

### 5. ★★ 좁은 것을 넓은 곳에 노출하면 (예측)

```csharp
// cs15b-expose.cs
internal class Secret { }
public class Door {
    public   Secret Give() => new Secret();
    public   void   Take(Secret s) { }
    internal Secret Ok()   => new Secret();
}
```

- **에러가 몇 건** 나는가 — 메서드는 셋인데?
- ★★ 반환 타입일 때와 매개변수일 때 **진단 코드가 다른가**?
- ★ 조용히 통과한 메서드는 무엇이고 왜인가?
- ★★ 이 규칙이 **왜 필요한가** — `var` 로 받으면 되지 않나?

### 6. ★ `file` 한정자(C# 11)는 접근 한정자인가 (예측)

```csharp
// cs15b-file1.cs
file class Hidden { public int N = 11; }
public class GateOne { public int Peek() => new Hidden().N; }
```

```csharp
// cs15b-file3.cs
public class Intruder { public int Peek() => new Hidden().N; }
```

- 같은 이름의 `file class` 둘이 **한 어셈블리에 공존**하는가?
- ★★★ 다른 파일에서 쓰면 진단 코드가 무엇인가 — **`CS0122` 인가 아닌가**?
- ★★ 그 코드가 말하는 것은 **「막혔다」인가 「없다」인가** — 그래서 `file` 은 어느 축인가?

### 7. ★★ `protected internal` 과 `private protected` 를 한 글자로 가르기 (경계)

- 둘 중 **어느 쪽이 넓은가** — C# 낱말만 보고 답할 수 있는가?
- ★★★ **메타데이터에 적히는 이름**은 각각 무엇인가?
- ★ `internal` 의 메타데이터 이름은 무엇이고, 그것이 왜 C# 낱말보다 정확한가?
- ★ `internal` 과 `protected` 중 **어느 쪽이 더 넓은가**?

### 8. ★★ 세 축 전수 격자를 그릴 수 있나 (경계)

- **같은 어셈블리 / 다른 어셈블리 / 친구 어셈블리** × **파생 / 파생 아님** 여섯 칸에
  여섯 한정자를 넣어 표를 채울 수 있는가?
- ★★★ `protected internal` 행과 `private protected` 행이 **처음 갈리는 칸**은 어디인가?
- ★ `protected` 행은 **어느 축을 안 타는가**?

### 9. ★★★ Java 와 어디가 갈리나 (연결)

```java
// Vault.java
package vault;
public class Vault {
    public    int pub  = 1;
    protected int prot = 2;
              int pkg  = 3;
    private   int priv = 4;
}
```

- Java 는 단계가 **몇 개**인가 — C# 과 개수가 같은가?
- ★★★ **멤버 기본값**이 두 언어에서 각각 무엇인가 — 정반대인가?
- ★★★ Java 의 `protected` 는 **같은 패키지의 파생 아닌 클래스**에 열리는가 — C# 은?
- ★★ **package 와 어셈블리**가 자르는 단위가 어떻게 다른가 — 그래서 **뚫는 방법**이 왜 다른가?
- ★ C# 에만 있는 칸 **둘**은 무엇인가?

### 10. 다른 주제와 잇기 (연결)

- **접근자 접근성**(`{ get; private set; }`)의 정본은 몇 번 주제인가?
- ★★ **`protected` 를 설계로 쓰는 법**과 **`virtual` 의 짝**은 몇 번 주제인가?
- **명시적 인터페이스 구현이 `private` 인 것**은 몇 번 주제인가?
- ★ C++ 에는 왜 이 주제의 **절반이 아예 없는가**?

## 복습 기록

| 날짜 | 결과 | 틀린 질문 | 다음 복습 |
|------|------|-----------|-----------|
| | | | |
