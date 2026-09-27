# csharp/syntax/15 — 접근 한정자와 어셈블리 경계 — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단은 **.NET SDK 10.0.401** · 런타임 **10.0.12** · 타겟 **`net10.0`** ·
> **linux-x64** 에서 실제로 돌려 얻은 것이다(2026-09-26). Java 대비는 **javac 21.0.5** 다.\
> 진단은 **`-preferreduilang:en-US`** 로 영어로 고정했다.\
> ★★★ **어셈블리를 둘 만들었다** — `liba.dll`(라이브러리)과 `appb.dll`(참조하는 쪽).\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 손으로 옮긴 줄은 없다.
> **읽는 법** — **진단 문구**와 `CS0281` 에 박힌 **어셈블리 버전·`PublicKeyToken` 표기**는 흔들리는 칸이다.\
> 근거로 쓰는 것은 **어느 멤버가 막히고 어느 멤버가 통과했나 · 진단 코드와 `(행,열)` ·
> `cc exit` · `FieldAttributes` 의 이름** 이다.\
> ★★★ **4번에서는 진단 문구가 원인을 안 가리킨다** — 그래서 거기서는 **`cc exit` 만 근거로 썼다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **넷이다** — `Outsider` 에서 셋, `Heir` 에서 하나

**출력**

```text
===== 소스: cs15b-vault.cs =====
public class Vault {
    public              int Pub      = 1;
    protected           int Prot     = 2;
    internal            int Intl     = 3;
    protected internal  int ProtIntl = 4;
    private protected   int PrivProt = 5;
    private             int Priv     = 6;

    public string Read() => $"{Pub}{Prot}{Intl}{ProtIntl}{PrivProt}{Priv}";
}
===== 소스: cs15b-same.cs =====
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
===== csc -target:library -out:liba.dll cs15b-vault.cs cs15b-same.cs 2>&1 | sort (cc exit=1) =====
cs15b-same.cs(18,13): error CS0122: 'Vault.Priv' is inaccessible due to its protection level
cs15b-same.cs(4,15): error CS0122: 'Vault.Prot' is inaccessible due to its protection level
cs15b-same.cs(7,15): error CS0122: 'Vault.PrivProt' is inaccessible due to its protection level
cs15b-same.cs(8,15): error CS0122: 'Vault.Priv' is inaccessible due to its protection level
```

**왜 그런가**

- ★★★ **같은 어셈블리 · 파생 아님**(`Outsider`) — **`Prot`·`PrivProt`·`Priv` 셋이 막힌다.**\
  `Pub`·`Intl`·`ProtIntl` 은 통과했다. ★ **같은 어셈블리 안에서는 `internal` 이 `public` 과 구분이 안 된다.**
- ★★★ **같은 어셈블리 · 파생**(`Heir`) — **`Priv` 하나만 막힌다**(18행).\
  `Prot` 과 `PrivProt` 이 여기서 열렸다 — **상속 축이 붙었기 때문**이다.
- ★★ **갈리는 필드 둘은 `Prot` 과 `PrivProt` 이다.** 나머지 넷은 두 클래스에서 같은 결과다.
- ★★ **진단 코드가 전부 `CS0122`** 다 — 「보호 수준 때문에 접근할 수 없다」.\
  ★★★ **이 코드가 「이름은 보인다」는 뜻**이라는 것이 2번에서 결정적이 된다.
- ★ 에러 네 건이고 `cc exit=1` 이다.

### 2. ★★★ **`CS0122` 가 `CS1061`/`CS0103` 으로 바뀐다** — 「막힘」이 「없음」이 된다

**출력**

```text
===== 소스: cs15b-other.cs =====
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
===== csc -target:library -out:liba.dll cs15b-vault.cs (cc exit=0) =====
===== csc -r:liba.dll -out:appb.dll cs15b-other.cs 2>&1 | sort (cc exit=1) =====
cs15b-other.cs(15,13): error CS0103: The name 'Intl' does not exist in the current context
cs15b-other.cs(17,13): error CS0122: 'Vault.PrivProt' is inaccessible due to its protection level
cs15b-other.cs(18,13): error CS0103: The name 'Priv' does not exist in the current context
cs15b-other.cs(4,15): error CS0122: 'Vault.Prot' is inaccessible due to its protection level
cs15b-other.cs(5,15): error CS1061: 'Vault' does not contain a definition for 'Intl' and no accessible extension method 'Intl' accepting a first argument of type 'Vault' could be found (are you missing a using directive or an assembly reference?)
cs15b-other.cs(6,15): error CS0122: 'Vault.ProtIntl' is inaccessible due to its protection level
cs15b-other.cs(7,15): error CS0122: 'Vault.PrivProt' is inaccessible due to its protection level
cs15b-other.cs(8,15): error CS1061: 'Vault' does not contain a definition for 'Priv' and no accessible extension method 'Priv' accepting a first argument of type 'Vault' could be found (are you missing a using directive or an assembly reference?)
```

**왜 그런가**

- ★★★ **`Intl` 과 `Priv` 의 진단 코드가 바뀌었다.**
  - 1번에서는 **`CS0122`**(「보호 수준 때문에 접근 불가」) 였는데
  - 여기서는 **`CS1061`**(`v.Intl` — 「그런 정의가 **없다**」) 과 **`CS0103`**(`Intl` — 「그런 **이름이 없다**」) 이다.
- ★★★ **이것이 이 주제에서 가장 중요한 관찰이다.** 다른 어셈블리에서 `internal` 멤버는\
  **「보이는데 막힌 것」이 아니라 「아예 존재하지 않는 것」으로 보인다.**\
  컴파일러가 참조 어셈블리의 메타데이터를 읽을 때 **그 멤버를 후보에서 통째로 뺀다.**\
  ★★ **「확장 메서드도 못 찾았다」는 문구까지 붙는 것**이 증거다 — 이름 해석이 **완전히 실패한 경로**를 탔다.
- ★★★ **`Prot`·`ProtIntl`·`PrivProt` 은 여전히 `CS0122` 다** — **이름은 보인다.**\
  `public` 타입의 `protected` 계열 멤버는 **메타데이터에 남아 있어야** 파생 클래스가 쓸 수 있다.
- ★★★ **`HeirB`(다른 어셈블리 · 파생)에서 `ProtIntl` 이 통과했다** — 15행에 `Intl` 에러만 있고 16행이 없다.\
  `protected internal` 은 **`OR` 이라 상속 축만 맞아도 열린다.**
- ★★★ **같은 자리에서 `PrivProt` 은 막혔다**(17행 `CS0122`).\
  `private protected` 는 **`AND` 라 어셈블리 축까지 맞아야** 한다.\
  ★ **이 한 줄이 두 낱말을 가르는 가장 짧은 증거**다.
- ★ 에러가 여덟 건으로 늘었다(1번은 넷).

### 3. ★★★ **`internal` 과 `protected internal` 을 뚫는다** — `cc exit` 가 1 에서 0 으로

**출력**

```text
===== 소스: cs15b-vault.cs =====
public class Vault {
    public              int Pub      = 1;
    protected           int Prot     = 2;
    internal            int Intl     = 3;
    protected internal  int ProtIntl = 4;
    private protected   int PrivProt = 5;
    private             int Priv     = 6;

    public string Read() => $"{Pub}{Prot}{Intl}{ProtIntl}{PrivProt}{Priv}";
}
===== 소스: cs15b-ivt.cs =====
using System.Runtime.CompilerServices;
[assembly: InternalsVisibleTo("appb")]
===== 소스: cs15b-friend.cs =====
using System;
class Friend {                          // 친구 어셈블리 · 파생 아님
    public static string Touch(Vault v) => $"{v.Pub} {v.Intl} {v.ProtIntl}";
}
class Program { static void Main() => Console.WriteLine(Friend.Touch(new Vault())); }
===== csc -target:library -out:libnoivt.dll cs15b-vault.cs && csc -r:libnoivt.dll -out:appb.dll cs15b-friend.cs (cc exit=1) =====
cs15b-friend.cs(3,57): error CS1061: 'Vault' does not contain a definition for 'Intl' and no accessible extension method 'Intl' accepting a first argument of type 'Vault' could be found (are you missing a using directive or an assembly reference?)
cs15b-friend.cs(3,66): error CS0122: 'Vault.ProtIntl' is inaccessible due to its protection level
===== csc -target:library -out:liba.dll cs15b-vault.cs cs15b-ivt.cs && csc -r:liba.dll -out:appb.dll cs15b-friend.cs && dotnet appb.dll (cc exit=0 · run exit=0) =====
1 3 4
```

```text
===== 소스: cs15b-pp.cs =====
class StrangerPP    { void Touch(Vault v) { _ = v.PrivProt; } }   // 친구 어셈블리 · 파생 아님
class Program { static void Main() { } }
===== 소스: cs15b-ppheir.cs =====
class HeirPP : Vault { void Touch() { _ = PrivProt; } }           // 친구 어셈블리 · 파생
class Program { static void Main() { } }
===== csc -r:liba.dll -out:appb.dll cs15b-pp.cs (cc exit=1) =====
cs15b-pp.cs(1,51): error CS0281: Friend access was granted by 'liba, Version=0.0.0.0, Culture=neutral, PublicKeyToken=null', but the public key of the output assembly ('') does not match that specified by the InternalsVisibleTo attribute in the granting assembly.
===== csc -r:liba.dll -out:appb.dll cs15b-ppheir.cs (cc exit=0) =====
```

**왜 그런가**

- ★★★ **위 판은 `cc exit=1`, 아래 판은 `cc exit=0` 이고 `1 3 4` 가 찍혔다.**\
  같은 소스가 **`InternalsVisibleTo` 한 줄로** 갈렸다.
- ★★★ **뚫린 멤버는 `Intl`(internal)과 `ProtIntl`(protected internal) 둘**이다.\
  찍힌 세 숫자 `1 3 4` 가 각각 `Pub`·`Intl`·`ProtIntl` 이다 — **선언만 통과한 게 아니라 값이 읽혔다.**
- ★★★ **`private protected` 는 파생이어야 열린다.**\
  `StrangerPP`(파생 아님) → **`cc exit=1`** · `HeirPP`(파생) → **`cc exit=0`**.\
  즉 **친구 어셈블리가 `AND` 의 「어셈블리」 조건을 만족시키고**, 「파생」 조건은 여전히 필요하다.
- ★★★ **막힌 쪽의 진단이 `CS0281` 이고 문구가 「공개 키가 안 맞는다」고 말한다.**\
  그런데 ★★★ **이 판에서 두 어셈블리 모두 `PublicKeyToken=null` 이다** — 문구 안에 그렇게 찍혀 있다.\
  ★★★ **즉 문구가 실제 원인을 가리키지 않는다.** 실제 원인은 **파생이 아니라는 것**이다.
- ★★★ **그래서 여기서는 문구를 근거로 쓰지 않았다.** 근거는 **같은 어트리뷰트·같은 두 어셈블리에서\
  파생 여부 하나만 바꿨더니 `cc exit` 가 0 과 1 로 갈렸다**는 사실이다.\
  ★ 지침의 「진단 문구는 흔들리는 칸」이 **문구가 아예 틀릴 수도 있다**는 형태로 나온 자리다.
- ★ **어셈블리 이름으로 지목한다** — `-out:appb.dll` 이므로 이름이 `appb` 다.\
  강력한 이름으로 서명한 어셈블리라면 **공개 키까지** 적어야 하는데, **그 판은 안 던졌다.**

### 4. ★★ **최상위 타입은 `internal`, 중첩 타입과 멤버는 `private`**

**출력**

```text
===== 소스: cs15b-def.cs =====
class TopDefault { public int N = 1; }              // 최상위 타입 — 한정자 없음
public class Wrapper {
    class NestedDefault { }                         // 중첩 타입 — 한정자 없음
    int memberDefault = 2;                          // 멤버 — 한정자 없음
    public string Show() => $"{memberDefault} {new NestedDefault()}";
}
===== 소스: cs15b-defuse.cs =====
class Probe {
    void Touch(Wrapper w) { _ = w.memberDefault; }
    void MakeTop()        { _ = new TopDefault();  }
}
class Program { static void Main() { } }
===== csc -target:library -out:libdef.dll cs15b-def.cs (cc exit=0) =====
===== csc -target:library -out:same.dll cs15b-def.cs cs15b-defuse.cs (cc exit=1) =====
cs15b-defuse.cs(2,35): error CS0122: 'Wrapper.memberDefault' is inaccessible due to its protection level
===== csc -r:libdef.dll -out:ex.dll cs15b-defuse.cs 2>&1 | sort (cc exit=1) =====
cs15b-defuse.cs(2,35): error CS1061: 'Wrapper' does not contain a definition for 'memberDefault' and no accessible extension method 'memberDefault' accepting a first argument of type 'Wrapper' could be found (are you missing a using directive or an assembly reference?)
cs15b-defuse.cs(3,37): error CS0122: 'TopDefault' is inaccessible due to its protection level
```

```text
===== 소스: cs15b-nested.cs =====
public class Wrapper {
    class NestedDefault { }
    public NestedDefault Leak() => new NestedDefault();
}
===== csc -target:library -out:libn.dll cs15b-nested.cs (cc exit=1) =====
cs15b-nested.cs(3,26): error CS0050: Inconsistent accessibility: return type 'Wrapper.NestedDefault' is less accessible than method 'Wrapper.Leak()'
```

**왜 그런가**

- ★★★ **같은 어셈블리 판에서 에러 한 건** — `memberDefault` 만 `CS0122` 다.\
  **`new TopDefault()` 는 조용하다** → 최상위 타입의 기본값은 `private` 이 아니다.
- ★★★ **다른 어셈블리 판에서 두 건** — 늘어난 한 건이 **`TopDefault` 의 `CS0122`** 다.\
  → 최상위 타입의 기본값은 **`internal`** 이다.\
  ★ 이때 `memberDefault` 쪽은 **`CS1061`** 로 바뀐다 — 2번의 규칙이 여기서도 그대로 돈다.
- ★★★ **중첩 타입의 기본값은 이 블록이 아니라 `cs15b-nested.cs` 가 증명한다.**\
  `public NestedDefault Leak()` 이 **`CS0050`** 으로 막혔다 — 컴파일러가\
  「`Wrapper.NestedDefault` 가 `Wrapper.Leak()` 보다 **덜 접근 가능하다**」고 말한다.\
  ★ 한정자를 안 적은 중첩 타입이 `public` 메서드보다 좁다는 뜻이고, **그 값이 `private`** 이다.
- ★★ **왜 자리마다 다른가** — 타입은 **파일 안에서 혼자 쓰이는 일이 없고**(적어도 같은 어셈블리가 쓴다),\
  멤버는 **혼자 쓰이는 것이 기본**이다. ★ 「타입은 건물 안, 멤버는 방 안」으로 읽어라.

### 5. ★★ **둘이다** — 반환은 `CS0050`, 매개변수는 `CS0051`

**출력**

```text
===== 소스: cs15b-expose.cs =====
internal class Secret { }
public class Door {
    public   Secret Give() => new Secret();
    public   void   Take(Secret s) { }
    internal Secret Ok()   => new Secret();
}
===== csc -target:library -out:libexp.dll cs15b-expose.cs 2>&1 | sort (cc exit=1) =====
cs15b-expose.cs(3,21): error CS0050: Inconsistent accessibility: return type 'Secret' is less accessible than method 'Door.Give()'
cs15b-expose.cs(4,21): error CS0051: Inconsistent accessibility: parameter type 'Secret' is less accessible than method 'Door.Take(Secret)'
```

**왜 그런가**

- ★★★ **`CS0050`** — `public Secret Give()` 의 **반환 타입**이 메서드보다 좁다.
- ★★★ **`CS0051`** — `public void Take(Secret s)` 의 **매개변수 타입**이 메서드보다 좁다.\
  ★ **코드가 갈려 있다** — 어느 자리에서 샜는지 코드만 보고 안다.
- ★★ **조용히 통과한 것은 `internal Secret Ok()` 다.** 메서드도 `internal` 이라 일관성이 맞는다.\
  **에러가 세 메서드 중 둘에만 난 것**이 그 증거다.
- ★★ **왜 이 규칙이 필요한가** — 돌려받은 값의 **타입 이름을 쓸 수 없으면** 그 메서드가 쓸모가 없다.\
  ★ `var` 로 받으면 되지 않나 싶지만, **그 타입의 멤버를 부르는 순간 다시 막힌다** —\
  `Secret` 의 멤버들도 그 어셈블리 밖에서는 2번의 `CS1061` 을 맞는다.\
  ★★ 즉 **이 규칙은 「쓸 수 없는 API 를 선언하지 못하게」 하는 것**이다.

### 6. ★ **접근 한정자가 아니다** — `CS0246` 이 그 증거다

**출력**

```text
===== 소스: cs15b-file1.cs =====
file class Hidden { public int N = 11; }
public class GateOne { public int Peek() => new Hidden().N; }
===== 소스: cs15b-file2.cs =====
file class Hidden { public int N = 22; }
public class GateTwo { public int Peek() => new Hidden().N; }
===== 소스: cs15b-file3.cs =====
public class Intruder { public int Peek() => new Hidden().N; }
===== csc -target:library -out:libfile.dll cs15b-file1.cs cs15b-file2.cs (cc exit=0) =====
===== csc -target:library -out:libfile.dll cs15b-file1.cs cs15b-file2.cs cs15b-file3.cs (cc exit=1) =====
cs15b-file3.cs(1,50): error CS0246: The type or namespace name 'Hidden' could not be found (are you missing a using directive or an assembly reference?)
```

**왜 그런가**

- ★★★ **같은 이름의 `file class Hidden` 둘이 한 어셈블리에 공존한다**(`cc exit=0`).\
  값이 11 과 22 로 **다른 타입**인데 이름 충돌이 안 난다.
- ★★★ **다른 파일에서 쓰면 `CS0246`**(「그런 타입이나 이름 공간이 없다」).\
  ★★★ **`CS0122`(보호 수준) 가 아니다.**
- ★★★ **그래서 `file` 은 접근성 축이 아니라 이름 범위 축이다.**\
  「보이는데 막혔다」가 아니라 「**그 파일 밖에서는 이름 자체가 존재하지 않는다**」이다.\
  ★ 2번의 `internal` 이 다른 어셈블리에서 `CS1061` 로 사라지는 것과 **성격이 같다** — 다만 단위가 **파일**이다.
```text
   접근성 축(여섯 한정자)          이름 범위 축(file)
   ─────────────────────          ─────────────────────
   「보이나?」                     「그 이름이 있나?」
   막히면 CS0122                   없으면 CS0246
        │                               │
        └── 같은 어셈블리 안에서만 의미   └── 같은 파일 안에서만 의미

   file class Hidden { … }   ← File1.cs   값 11
   file class Hidden { … }   ← File2.cs   값 22   ★ 이름이 같아도 충돌 안 함
   class Intruder { new Hidden() }  ← File3.cs   ✕ CS0246

   ★ 그래서 file 을 여섯 한정자와 나란히 외우면 안 된다.
```
- ★★ **무엇을 위한 것인가** — 소스 생성기(source generator)용이다.\
  생성기가 만든 도우미 타입이 **사용자 코드나 다른 생성기와 이름이 겹치는 것**을 막는다.
- ★ 그래서 **여섯 한정자와 나란히 외우면 안 된다.**

### 7. ★★ **`private protected` 가 좁다** — `AND` 이기 때문

**출력**

```text
===== 소스: cs15b-meta.cs =====
using System;
using System.Reflection;
public class Vault2 {
    public              int Pub      = 1;
    protected           int Prot     = 2;
    internal            int Intl     = 3;
    protected internal  int ProtIntl = 4;
    private protected   int PrivProt = 5;
    private             int Priv     = 6;
}
class Program {
    static void Main() {
        Console.WriteLine($"{"C# 에 쓴 것",-20} {"IL 속성",-14} {"IsAssembly",-11} {"IsFamily",-9} {"IsFamilyOrAssembly",-19} IsFamilyAndAssembly");
        foreach (var f in typeof(Vault2).GetFields(BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Instance)) {
            var a = f.Attributes & FieldAttributes.FieldAccessMask;
            Console.WriteLine($"{f.Name,-20} {a,-14} {f.IsAssembly,-11} {f.IsFamily,-9} {f.IsFamilyOrAssembly,-19} {f.IsFamilyAndAssembly}");
        }
    }
}
===== csc -out:ex.dll cs15b-meta.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
cs15b-meta.cs(9,29): warning CS0414: The field 'Vault2.Priv' is assigned but its value is never used
C# 에 쓴 것             IL 속성          IsAssembly  IsFamily  IsFamilyOrAssembly  IsFamilyAndAssembly
Pub                  Public         False       False     False               False
Prot                 Family         False       True      False               False
Intl                 Assembly       True        False     False               False
ProtIntl             FamORAssem     False       False     True                False
PrivProt             FamANDAssem    False       False     False               True
Priv                 Private        False       False     False               False
```

**왜 그런가**

- ★★★ **`protected internal` → `FamORAssem`** · **`private protected` → `FamANDAssem`**.\
  **`OR` 은 합집합이라 넓고 `AND` 는 교집합이라 좁다.**\
  ★★★ **C# 낱말만 보고는 절대 안 읽히는데 메타데이터 이름은 한 글자로 가른다.**
- ★★★ **리플렉션 속성 이름도 그대로다** — `IsFamilyOrAssembly` 와 `IsFamilyAndAssembly` 가\
  각각 `ProtIntl` 과 `PrivProt` 에서만 `True` 다.
- ★★★ **`internal` 의 메타데이터 이름은 `Assembly` 다.**\
  C# 낱말 `internal` 은 「안쪽」으로만 읽혀 **무엇의 안쪽인지**를 안 말하는데,\
  메타데이터는 **「어셈블리」라고 단위를 못 박는다.** ★ **그래서 더 정확하다.**
- ★★★ **`internal` 과 `protected` 는 넓고 좁음을 못 정한다** — 서로 **다른 축**이다.\
  `Assembly` 와 `Family` 는 **겹치는 부분도 있고 어느 쪽도 상대를 포함하지 않는다.**\
  ★ 그 둘을 `OR` 로 묶은 것이 `FamORAssem`, `AND` 로 묶은 것이 `FamANDAssem` 이다.

```text
                        ┌──────── Family(집안 = 파생) ────────┐
                        │                                     │
   ┌────────────────────┼─────────────────────────┐           │
   │ Assembly           │   FamANDAssem           │           │
   │ (건물 = 어셈블리)   │   private protected     │  Family   │
   │                    │   ★ 교집합 — 좁다        │  protected│
   │  internal          │                         │           │
   └────────────────────┼─────────────────────────┘           │
                        └─────────────────────────────────────┘
   두 원을 합친 것 = FamORAssem = protected internal  ★ 합집합 — 넓다
   두 원 밖 전부    = public          두 원 안 어디도 아님 = private

   ★★★ internal 과 protected 는 서로 포함하지 않는다 — 넓고 좁음을 못 정한다.
```
- ★ **외우는 법** — `protected internal` 은 두 낱말을 **더하는 것**,\
  `private protected` 는 `private` 이 앞에 있어 **깎는 것**.
- ★ `Priv` 에 `CS0414` 경고가 같이 났다 — 안 쓰는 private 필드다. **그것도 출력이다.**

> ★★★ **이것이 「창을 바꿔 답한 것」이다**(규칙 18-B 의 제5의 상태).\
> 「어느 쪽이 넓은가」를 ② 진단으로 물으면 **격자를 여섯 칸 다 던져야** 알 수 있는데\
> ③ 리플렉션은 **한 줄로 답한다.**\
> ★ 바꾼 창이 못 보는 것도 적어 둔다 — **메타데이터는 「누가 볼 수 있나」를 말하지 「지금 이 호출이 되나」를 말하지 않는다.**\
> 그래서 1번·2번이 따로 필요하다.

### 8. ★★ 세 축 전수 격자

**출력** — 아래 표의 모든 칸은 **1\~3번 블록에서 읽은 것**이고 추측한 칸이 없다.

| 한정자 | 같은 어셈블리<br>파생 아님 | 같은 어셈블리<br>파생 | 다른 어셈블리<br>파생 아님 | 다른 어셈블리<br>파생 | 친구 어셈블리<br>파생 아님 | 친구 어셈블리<br>파생 |
|---|---|---|---|---|---|---|
| `public` | ○ 1번 | ○ 1번 | ○ 2번 | ○ 2번 | ○ 3번 | ○ |
| `protected internal` | ○ 1번 | ○ 1번 | ✕ `CS0122` 2번 | ★ **○** 2번 | ★ **○** 3번 | ○ |
| `protected` | ✕ `CS0122` 1번 | ○ 1번 | ✕ `CS0122` 2번 | ○ 2번 | ✕ `CS0122` 3번 | ○ |
| `internal` | ○ 1번 | ○ 1번 | ✕ `CS1061` 2번 | ✕ `CS0103` 2번 | ★ **○** 3번 | ○ |
| `private protected` | ✕ `CS0122` 1번 | ○ 1번 | ✕ `CS0122` 2번 | ★ **✕ `CS0122`** 2번 | ✕ `CS0281` 3번 | ★ **○** 3번 |
| `private` | ✕ `CS0122` 1번 | ✕ `CS0122` 1번 | ✕ `CS1061` 2번 | ✕ `CS0103` 2번 | ✕ 3번 | ✕ |

**왜 그런가**

- ★★★ **`protected internal` 과 `private protected` 가 처음 갈리는 칸은 「다른 어셈블리 · 파생」이다.**\
  앞의 네 칸(같은 어셈블리 두 칸 · 다른 어셈블리 파생 아님)에서는 **결과가 같다.**\
  ★ **그 칸 하나를 안 던지면 두 낱말을 못 가른다** — 그래서 어셈블리를 둘 만들어야 했다.
- ★★★ **`protected` 행은 어셈블리 축을 안 탄다** — 같은/다른/친구 어느 쪽이든 **파생이면 ○, 아니면 ✕** 다.
- ★★ **`internal` 행과 `private` 행은 다른 어셈블리에서 진단 코드가 같다** — 둘 다 「없는 것」이다.\
  ★ 갈리는 곳은 **같은 어셈블리 칸**과 **친구 어셈블리 칸**이다.
- ★ **친구 어셈블리 · 파생 열은 셋만 실측했다**(`private protected` 는 3번에서, 나머지는 위 열들에서 따라온다).\
  ★★ **`public`·`protected`·`protected internal` 의 「친구 · 파생」 칸은 던지지 않았다** —\
  친구 관계가 `internal` 축만 건드리므로 **다른 어셈블리 · 파생 칸과 같아야** 하지만, **그 칸은 관찰이 아니라 추론이다.**

### 9. ★★★ **네 단계 · 기본값이 정반대 · `protected` 의 뜻이 다르다**

**출력**

```text
===== 소스: jsrc/vault/Vault.java =====
package vault;
public class Vault {
    public    int pub  = 1;
    protected int prot = 2;
              int pkg  = 3;
    private   int priv = 4;
}
===== 소스: jsrc/vault/Neighbor.java =====
package vault;
public class Neighbor {          // 같은 패키지 · 파생 아님
    void touch(Vault v) {
        int a = v.pub;
        int b = v.prot;
        int c = v.pkg;
        int d = v.priv;
    }
}
===== 소스: jsrc/other/Heir.java =====
package other;
import vault.Vault;
public class Heir extends Vault {   // 다른 패키지 · 파생
    void touch() {
        int a = pub;
        int b = prot;
        int c = pkg;
        int d = priv;
    }
}
===== 소스: jsrc/other/Stranger.java =====
package other;
import vault.Vault;
public class Stranger {             // 다른 패키지 · 파생 아님
    void touch(Vault v) {
        int a = v.pub;
        int b = v.prot;
        int c = v.pkg;
        int d = v.priv;
    }
}
===== javac -d jout jsrc/vault/Vault.java jsrc/vault/Neighbor.java jsrc/other/Heir.java jsrc/other/Stranger.java (cc exit=1) =====
jsrc/vault/Neighbor.java:7: error: priv has private access in Vault
        int d = v.priv;
                 ^
jsrc/other/Heir.java:7: error: pkg is not public in Vault; cannot be accessed from outside package
        int c = pkg;
                ^
jsrc/other/Heir.java:8: error: priv has private access in Vault
        int d = priv;
                ^
jsrc/other/Stranger.java:6: error: prot has protected access in Vault
        int b = v.prot;
                 ^
jsrc/other/Stranger.java:7: error: pkg is not public in Vault; cannot be accessed from outside package
        int c = v.pkg;
                 ^
jsrc/other/Stranger.java:8: error: priv has private access in Vault
        int d = v.priv;
                 ^
6 errors
```

**왜 그런가**

- ★★★ **Java 는 네 단계다** — `public` · `protected` · **한정자 없음(package-private)** · `private`.\
  **C# 의 여섯과 개수부터 다르다.**
- ★★★ **멤버 기본값이 정반대다.**
  - **Java** — 한정자 없음은 **package-private**. `Neighbor`(같은 패키지, 파생 아님)가 **`pkg` 를 읽었다**.\
    그 클래스에서 에러가 **`priv` 하나뿐**인 것이 증거다.
  - **C#** — 한정자 없음은 **`private`**. 같은 어셈블리라도 못 본다(4번).
- ★★★ **`protected` 의 뜻이 다르다.**
  - **Java 의 `protected` 는 「파생 **또는** 같은 패키지」** — C# 의 `protected internal` 에 가깝다.\
    `Neighbor` 가 **`prot` 를 읽었다**(에러가 안 났다).
  - **C# 의 `protected` 는 파생만** — 1번에서 `Outsider` 가 `Prot` 에 막혔다.
  - ★★ **그래서 「Java 의 네 단계에 C# 의 여섯을 대응시키기」가 원리상 안 된다.**
- ★★★ **자르는 단위가 다르다.**
  - **package 는 이름 공간**이고 한 jar 에 여러 package 가 들어간다 — **배포 단위와 무관**하다.\
    ★ 다른 jar 가 같은 package 이름을 선언하면 뚫린다(split package). **이 판에서 그 실험은 안 던졌다.**
  - **어셈블리는 배포 단위**다. `internal` 은 **`.dll` 하나**로 잘리고,\
    뚫으려면 **선언한 쪽이 `InternalsVisibleTo` 로 허락**해야 한다(3번).\
    ★★★ **그래서 C# 쪽은 「허락하는 문」이고 Java 쪽은 「이름만 맞추면 되는 틈」이다.**
- ★★ **C# 에만 있는 칸 둘** — **`internal`**(건물만) 과 **`private protected`**(집안 `AND` 건물).\
  Java 에는 대응물이 없다.
- ★★ **Java 에만 있는 것** — `module-info.java` 의 `exports`(JPMS, Java 9).\
  ★★★ **이 판에서 안 던졌다** — 모듈 경로 설정이 따로 필요하다.
- ★ **재검증 방식이 다르다** — **javac 는 소스 줄과 `^` 캐럿을 끼워 준다.**\
  C# 진단은 **`(행,열)` 만** 준다. 그래서 C# 쪽은 **소스 배너를 같은 블록에 싣는 것**이 필수다.

### 10. 잇기

- **접근자 접근성**(`{ get; private set; }`)의 정본은 [13번](../13-properties-init-required-field/) (6)이다 — `CS0273`·`CS0274`·`CS0272`.
- ★★ **`protected` 를 설계로 쓰는 법**과 **`virtual` 의 짝**은 [16번](../16-inheritance-virtual-override-abstract-sealed-new/)이다.\
  ★ **접근성과 가상성은 독립 축**이다 — `public` 인데 비가상일 수 있고 `protected` 인데 가상일 수 있다.
- **명시적 인터페이스 구현이 `private` 인 것**은 [16번](../16-inheritance-virtual-override-abstract-sealed-new/) (8)이다.\
  ★ 이 주제의 여섯 한정자로는 설명이 안 되는 **일곱 번째 자리**다 — 한정자를 못 적는데 `private` 이 된다.
- ★ **C++ 에는 이 주제의 절반이 없다** — `public`/`protected`/`private` 셋뿐이고 **어셈블리 축이 아예 없다.**\
  대신 **`friend` 선언**이 있는데, 그것은 **타입 단위**라 `InternalsVisibleTo` 의 **어셈블리 단위**와 다르다.\
  C++ 갈래 목록([`cpp/syntax/README.md`](../../../cpp/syntax/README.md))의 **12번**([`12-class-basics-members-access-and-this/`](../../../cpp/syntax/12-class-basics-members-access-and-this/))이 그쪽 정본이다. **이 판에서 C++ 은 안 던졌다.**

## 실행 검증

| 무엇 | 몇 번·어디서 | 결과 |
|---|---|---|
| `cs15b-same.cs` 같은 어셈블리 | csc 1회(1어셈블리) | **`CS0122` 4건** — `Prot`·`PrivProt`·`Priv`(×2) |
| `cs15b-other.cs` 다른 어셈블리 | csc **2회**(liba → appb) | ★★★ **`CS1061`·`CS0103` 로 바뀐다** · 8건 |
| `cs15b-meta.cs` 메타데이터 이름 | csc 1회 | ★★★ **`FamORAssem`·`FamANDAssem`·`Assembly`** |
| `cs15b-ivt.cs` + `cs15b-friend.cs` | csc **4회**(IVT 없이/있고) | ★★★ **`cc exit` 1 → 0** · `1 3 4` |
| `cs15b-pp.cs`·`cs15b-ppheir.cs` | csc 2회 | ★★★ **파생 아님 `cc exit=1`(`CS0281`) · 파생 `cc exit=0`** |
| `cs15b-def.cs` + `cs15b-defuse.cs` | csc **3회** | 같은 어셈블리 1건 · 다른 어셈블리 2건 |
| `cs15b-nested.cs` 중첩 기본값 | csc 1회 | **`CS0050`** — 중첩 타입 기본값이 `private` |
| `cs15b-expose.cs` 일관성 | csc 1회 | **`CS0050` · `CS0051`** — `internal Ok()` 는 통과 |
| `cs15b-file1/2/3.cs` `file` | csc 2회 | ★★★ 같은 이름 공존 `cc exit=0` · 다른 파일은 **`CS0246`** |
| Java `Vault`·`Neighbor`·`Heir`·`Stranger` | javac 1회 | ★★★ **에러 6건** — `Neighbor` 는 `priv` 만 · `Heir` 는 `pkg`·`priv` |

**구현 의존 항목** — 다음은 **이 판(.NET SDK 10.0.401 · Roslyn · javac 21.0.5)에서만** 그렇다.

- ★★★ **다른 어셈블리의 `internal` 이 `CS1061`/`CS0103` 으로 보이는 것** — 명세는 「접근 불가」만 정하고\
  **어떤 진단을 낼지는 정하지 않는다.** Roslyn 의 선택이다.
- ★★★ **`CS0281` 문구가 공개 키를 말하는 것** — **원인을 안 가리킨다.** 근거로 쓰지 않았다.
- ★★ **`CS0281` 문구에 박힌 어셈블리 버전과 `PublicKeyToken=null` 표기.**
- ★ **javac 의 에러 표기와 순서** · **진단 문구 전부**.

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- **여섯 한정자의 의미**와 **두 축(상속·어셈블리)**.
- **`protected internal` 이 합집합(`OR`)이고 `private protected` 가 교집합(`AND`)인** 것.
- **기본 접근성 세 가지** — 최상위 타입 `internal` · 중첩 타입 `private` · 멤버 `private`.
- **일관성 규칙** — 공개 표면에 더 좁은 타입을 쓸 수 없다(`CS0050`/`CS0051`).
- **`InternalsVisibleTo` 가 `internal` 과 `protected internal` 을 여는** 것, 그리고\
  **`private protected` 는 파생까지 돼야 열리는** 것.
- **`file` 타입이 그 파일 밖에서 이름째 사라지는** 것(C# 11).
- **`FamORAssem`·`FamANDAssem` 이라는 CLI 메타데이터 이름** — C# 이 아니라 **런타임 층의 보장**이다.

**안 돌려 본 것 / 못 잰 것 / 잴 것이 없는 것**

- **안 돌려 본 것** — ★★ **강력한 이름으로 서명한 어셈블리의 `InternalsVisibleTo`**(공개 키를 적는 판) ·\
  ★★ **Java 의 `module-info.java`/`exports`**(모듈 경로 설정이 따로 필요하다) ·\
  ★★ **Java 의 split package**(같은 package 이름을 두 jar 가 선언하는 것) ·\
  ★ **C++ 의 `friend` 선언**(이 판에서 C++ 은 안 던졌다) ·\
  ★ **`internal protected` 라는 순서**(같은 뜻으로 받는다고 알려져 있으나 안 던졌다) ·\
  ★ **`file` 타입을 부분 클래스·제네릭과 섞는 판** ·\
  ★ **8번 표의 「친구 어셈블리 · 파생」 열 중 셋**(`public`·`protected`·`protected internal`) — **추론이지 관찰이 아니다.**
- **못 잰 것** — ★ **「`internal` 을 많이 쓰면 JIT 이 더 최적화하나」.**\
  어셈블리 밖에서 재정의될 수 없다는 정보를 런타임이 쓸 수 있지만,\
  **그것을 관찰하려면 JIT 덤프가 필요하고 이 판에서는 안 만들었다.**
- ★ 「**부적용인 창**」 **둘** — **① IL 덤프**와 **④ 할당 바이트.**\
  접근 한정자는 **멤버 본문을 한 글자도 안 바꾼다.** `public int Pub` 과 `private int Priv` 의 `ldfld` 가 같다.\
  바뀌는 것은 **시그니처의 접근성 비트 하나**이고, 그것은 7번이 리플렉션으로 이미 찍는다.\
  ★★★ **「안 쟀다」가 아니라 「잴 것이 없다」다**(규칙 18-B).

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★ **3번의 `CS0281`** — Roslyn 이 진단을 고치면 **문구가 바뀌거나 다른 코드가 된다.**\
  ★ 이 문서는 그 경우에도 **결론이 안 흔들린다** — `cc exit` 만 근거로 썼기 때문이다.
- ★★ **2번의 `CS1061`/`CS0103`** — Roslyn 의 선택이라 바뀔 수 있다.
- ★ **1번·4번·5번·6번·7번** — **명세와 메타데이터가 정한 것이라 바뀔 일이 없다.** 바뀌면 그것이 뉴스다.
