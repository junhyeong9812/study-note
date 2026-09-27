# csharp/syntax/23 — 튜플과 해체(deconstruction) — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단·IL·할당 바이트는 **.NET SDK 10.0.401** · 런타임 **10.0.12** · 타겟 **`net10.0`** ·
> **linux-x64** 에서 실제로 돌려 얻은 것이다(2026-09-26).\
> 진단은 **`-preferreduilang:en-US`** 로 영어로 고정했다.\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 손으로 옮긴 줄은 없다.\
> ★ 진단을 싣는 블록은 전부 **그 진단을 낸 소스를 같은 블록 안에** 다시 싣는다(`===== 소스: … =====`).
> **읽는 법** — **진단 문구·예외 메시지·IL 오프셋 폭**은 흔들리는 칸이다.\
> 근거로 쓰는 것은 **리플렉션이 보여 준 이름 · 옵코드와 부른 멤버 · 진단 코드 · 예외 타입 · 네 판에서 갈린 줄 수** 다.

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ 필드는 **`Item1`·`Item2`**(가변) — 이름 `Id,Name` 은 **반환값 특성에만**

**출력**

```text
===== 소스: cs23b-refl.cs =====
using System;
using System.Reflection;
using System.Runtime.CompilerServices;
public static class Api {
    public static (int Id, string Name) Find() => (1, "kim");
}
class Program {
    static void Main() {
        var t = Api.Find();
        Type vt = t.GetType();
        Console.WriteLine($"[1] 타입        : {vt}");
        Console.WriteLine($"[2] IsValueType : {vt.IsValueType}");
        foreach (var f in vt.GetFields())
            Console.WriteLine($"[3] 필드        : {f.Name} ({f.FieldType.Name}) IsInitOnly={f.IsInitOnly}");
        Console.WriteLine($"[4] 속성 수     : {vt.GetProperties().Length}");
        var attr = typeof(Api).GetMethod("Find")!.ReturnParameter.GetCustomAttribute<TupleElementNamesAttribute>();
        Console.WriteLine($"[5] 반환값 특성 : {(attr is null ? "없음" : string.Join(",", attr.TransformNames))}");
        Type rt = Tuple.Create(1, "kim").GetType();
        Console.WriteLine($"[6] Tuple.Create: {rt} IsValueType={rt.IsValueType} 필드 {rt.GetFields().Length} · 속성 {rt.GetProperties().Length}");
        var big = (1, 2, 3, 4, 5, 6, 7, 8, 9);
        Console.WriteLine($"[7] 원소 9개    : {big.GetType()}");
        Console.WriteLine($"[8] big.Item9 = {big.Item9} · big.Rest.Item2 = {big.Rest.Item2} · big.Rest = {big.Rest}");
    }
}
===== csc -nullable:enable -out:ex.dll cs23b-refl.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] 타입        : System.ValueTuple`2[System.Int32,System.String]
[2] IsValueType : True
[3] 필드        : Item1 (Int32) IsInitOnly=False
[3] 필드        : Item2 (String) IsInitOnly=False
[4] 속성 수     : 0
[5] 반환값 특성 : Id,Name
[6] Tuple.Create: System.Tuple`2[System.Int32,System.String] IsValueType=False 필드 0 · 속성 2
[7] 원소 9개    : System.ValueTuple`8[System.Int32,System.Int32,System.Int32,System.Int32,System.Int32,System.Int32,System.Int32,System.ValueTuple`2[System.Int32,System.Int32]]
[8] big.Item9 = 9 · big.Rest.Item2 = 9 · big.Rest = (8, 9)
```

**왜 그런가**

- ★★★ **`[3]` `Item1 (Int32)`·`Item2 (String)` · `IsInitOnly=False`** — 이름은 컴파일 때 기본 이름으로 바뀌었고, 필드는 **`readonly` 가 아니다**(가변 구조체).
- ★★★ **`[5]` `Find()` 의 반환값 `TupleElementNamesAttribute` 가 `Id,Name`** — 이름은 **값이 아니라 메서드 서명**에 산다.
- ★★ **`[6]` 옛 `Tuple` 은 참조 타입 · 필드 0 · 속성 2** — 새 `ValueTuple` 과 정반대다.
- ★★ **`[7]` ``ValueTuple`8[Int32 ×7, ValueTuple`2[…]]``** · **`[8]` `Item9` 는 `Rest.Item2`** — 8번째 칸 `Rest` 에 나머지가 중첩된다.

### 2. ★★★ **`True` · `True` · `False` · `True`** — `==` 는 **원소별 `==`**, `CS8123` 는 **경고**

**출력**

```text
===== 소스: cs23b-eq.cs =====
using System;
class Money {
    public int Won;
    public Money(int w) => Won = w;
    public override bool Equals(object? o) => o is Money m && m.Won == Won;   // == 는 그대로 둔다
    public override int GetHashCode() => Won;
}
public static class Probe {
    public static bool Eq((int, string) a, (int, string) b) => a == b;
}
class Program {
    static void Main() {
        var a = (Id: 1, Name: "kim");
        (int Key, string Label) b = (1, "kim");
        Console.WriteLine($"[1] a == b       : {a == b}");
        Console.WriteLine($"[2] a.Equals(b)  : {a.Equals(b)}");
        var m1 = (new Money(100), 1);
        var m2 = (new Money(100), 1);
        Console.WriteLine($"[3] m1 == m2     : {m1 == m2}");
        Console.WriteLine($"[4] m1.Equals(m2): {m1.Equals(m2)}");
        Il.Dump(typeof(Probe), "Eq");
    }
}
===== csc -nullable:enable -r:il.dll -out:ex.dll cs23b-eq.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] a == b       : True
[2] a.Equals(b)  : True
[3] m1 == m2     : False
[4] m1.Equals(m2): True
--- Probe.Eq ---
  .locals [0] System.ValueTuple<System.Int32,System.String>
  .locals [1] System.ValueTuple<System.Int32,System.String>
  IL_0000: ldarg.0
  IL_0001: stloc.0
  IL_0002: ldarg.1
  IL_0003: stloc.1
  IL_0004: ldloc.0
  IL_0005: ldfld System.ValueTuple<System.Int32,System.String>::Item1
  IL_000a: ldloc.1
  IL_000b: ldfld System.ValueTuple<System.Int32,System.String>::Item1
  IL_0010: bne.un.s IL_0025
  IL_0012: ldloc.0
  IL_0013: ldfld System.ValueTuple<System.Int32,System.String>::Item2
  IL_0018: ldloc.1
  IL_0019: ldfld System.ValueTuple<System.Int32,System.String>::Item2
  IL_001e: call System.String::op_Equality
  IL_0023: br.s IL_0026
  IL_0025: ldc.i4.0
  IL_0026: ret
===== 소스: cs23b-names.cs =====
class Program {
    static void Main() {
        (int Id, string Name) t = (Key: 1, Label: "kim");     // 이름이 다른 튜플 리터럴을 대입
        var s = (Id: 1, Name: "kim");
        System.Console.WriteLine(t.Id + s.Id);
    }
}
===== csc -out:ex.dll cs23b-names.cs 2>&1 | sort (cc exit=0) =====
cs23b-names.cs(3,36): warning CS8123: The tuple element name 'Key' is ignored because a different name or no name is specified by the target type '(int Id, string Name)'.
cs23b-names.cs(3,44): warning CS8123: The tuple element name 'Label' is ignored because a different name or no name is specified by the target type '(int Id, string Name)'.
```

**왜 그런가**

- ★★★ **`[1]` 이름이 달라도 `True`** — 대입과 `==` 는 이름을 안 본다.
- ★★★ **IL — `ldfld Item1` 둘 → `bne.un.s`, `ldfld Item2` 둘 → `call System.String::op_Equality`.** `ValueTuple` 의 메서드가 아니라 **원소 타입의 `==`** 를 컴파일러가 풀어 썼다.
- ★★★ **`[3]` `False` · `[4]` `True`** — 원소 `Money` 는 `Equals` 만 고쳤으니 `==` 는 **참조 비교**([19번](../19-equality-equals-gethashcode-operator/) (3)). `ValueTuple.Equals` 는 원소의 **`Equals`** 를 부른다.
- ★★ **둘째 소스는 컴파일된다** — **`CS8123` 경고 둘**(「`Key`·`Label` 이름은 무시된다」).

### 3. ★★ 전부 해체된다 — **`Deconstruct` 이름**이 열쇠다

**출력**

```text
===== 소스: cs23b-decon.cs =====
using System;
static class VersionExt {
    public static void Deconstruct(this Version v, out int major, out int minor) { major = v.Major; minor = v.Minor; }
}
class Pt {
    public int X, Y;
    public Pt(int x, int y) { X = x; Y = y; }
    public void Deconstruct(out int x, out int y) { Console.WriteLine("    Pt.Deconstruct 불림"); x = X; y = Y; }
}
record Person(string Name, int Age);
class Program {
    static (int Min, int Max) MinMax(int[] xs) => (Math.Min(xs[0], xs[^1]), Math.Max(xs[0], xs[^1]));
    static void Main() {
        var (lo, hi) = MinMax(new[] { 7, 3 });
        Console.WriteLine($"[1] lo={lo} hi={hi}");
        var (major, minor) = new Version(10, 2);
        Console.WriteLine($"[2] major={major} minor={minor}");
        var (x, _) = new Pt(4, 5);
        Console.WriteLine($"[3] x={x}");
        var (name, age) = new Person("kim", 30);
        Console.WriteLine($"[4] name={name} age={age}");
        int a = 1, b = 2;
        (a, b) = (b, a);
        Console.WriteLine($"[5] a={a} b={b}");
        Console.WriteLine($"[6] {(new Pt(0, 3) is (0, var y) ? $"y={y}" : "아님")}");
    }
}
===== csc -out:ex.dll cs23b-decon.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] lo=3 hi=7
[2] major=10 minor=2
    Pt.Deconstruct 불림
[3] x=4
[4] name=kim age=30
[5] a=2 b=1
    Pt.Deconstruct 불림
[6] y=3
```

**왜 그런가**

- ★★★ **`[2]` `major=10 minor=2`** — **확장 메서드 `Deconstruct(this Version, out int, out int)`** 가 해체를 열었다. 인터페이스·상속이 필요 없다.
- ★ **`[3]` 앞에 `Pt.Deconstruct 불림`** — `_` 로 버린 원소가 있어도 **메서드 호출은 일어난다.** `[6]` 의 위치 패턴 앞에도 한 줄.
- ★ **`[4]` record 는 생성된 `Deconstruct`**([18번](../18-record-value-equality-and-with/)) · **`[5]` `a=2 b=1`**(교환).

### 4. ★★ **`List`·`Dictionary` 줄만 `CS1612`** — 배열은 된다 · 복사본을 고치면 **원본 그대로**

**출력**

```text
===== 소스: cs23b-mut.cs =====
using System.Collections.Generic;
class Program {
    static void Main() {
        var arr  = new[] { (Id: 1, Name: "kim") };
        var list = new List<(int Id, string Name)> { (1, "kim") };
        var dict = new Dictionary<string, (int Id, string Name)> { ["k"] = (1, "kim") };
        arr[0].Id = 9;                // 배열 원소
        list[0].Id = 9;               // List 인덱서가 돌려준 값
        dict["k"].Id = 9;             // Dictionary 인덱서가 돌려준 값
    }
}
===== csc -out:ex.dll cs23b-mut.cs 2>&1 | sort (cc exit=1) =====
cs23b-mut.cs(8,9): error CS1612: Cannot modify the return value of 'List<(int Id, string Name)>.this[int]' because it is not a variable
cs23b-mut.cs(9,9): error CS1612: Cannot modify the return value of 'Dictionary<string, (int Id, string Name)>.this[string]' because it is not a variable
===== 소스: cs23b-mut2.cs =====
using System;
using System.Collections.Generic;
class Program {
    static void Main() {
        var arr  = new[] { (Id: 1, Name: "kim") };
        var list = new List<(int Id, string Name)> { (1, "kim") };
        arr[0].Id = 9;
        var copy = list[0];
        copy.Id = 9;
        Console.WriteLine($"[1] arr[0]  = {arr[0]}");
        Console.WriteLine($"[2] list[0] = {list[0]} · copy = {copy}");
    }
}
===== csc -out:ex.dll cs23b-mut2.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] arr[0]  = (9, kim)
[2] list[0] = (1, kim) · copy = (9, kim)
```

**왜 그런가**

- ★★★ **줄 8·9 `CS1612`** — 인덱서의 반환값은 **복사본**이라 「변수가 아니다」. 고쳐 봐야 버려지니 컴파일러가 막았다.
- ★★ **줄 7 배열은 진단 없음** — 배열 원소는 **변수 자리 그 자체**다.
- ★★ **`[1]` `arr[0] = (9, kim)` · `[2]` `list[0] = (1, kim) · copy = (9, kim)`** — 값 타입 복사([01번](../01-value-types-and-reference-types/)).

### 5. ★★★ 튜플은 **그대로 돈다**, record 는 **`MissingMethodException`** — 다시 컴파일하면 **`CS1061` 넷**

**출력**

```text
===== 소스: cs23b-lib1.cs =====
using System.Collections.Generic;
public record User(int Id, string Name);
public static class Repo {
    public static (int Id, string Name) Find() => (1, "kim");
    public static List<(int Id, string Name)> All() => new() { (1, "kim"), (2, "lee") };
    public static User FindUser() => new(1, "kim");
}
===== 소스: cs23b-app.cs =====
using System;
class Program {
    static void Main() {
        var t = Repo.Find();
        Console.WriteLine($"[1] t.Id={t.Id} t.Name={t.Name}");
        foreach (var r in Repo.All()) Console.WriteLine($"[2] r.Id={r.Id}");
        try { dynamic d = Repo.Find(); Console.WriteLine($"[3] d.Id={d.Id}"); }
        catch (Exception e) { Console.WriteLine($"[3] {e.GetType().Name} : {e.Message}"); }
        try { Console.WriteLine($"[4] user.Id={ReadUser()}"); }
        catch (Exception e) { Console.WriteLine($"[4] {e.GetType().Name} : {e.Message}"); }
    }
    static int ReadUser() => Repo.FindUser().Id;
}
===== csc -target:library -out:Repo.dll cs23b-lib1.cs && csc -r:Repo.dll -out:app.dll cs23b-app.cs && dotnet app.dll (cc exit=0 · run exit=0) =====
[1] t.Id=1 t.Name=kim
[2] r.Id=1
[2] r.Id=2
[3] RuntimeBinderException : 'System.ValueTuple<int,string>' does not contain a definition for 'Id'
[4] user.Id=1
===== 소스: cs23b-lib2.cs =====
using System.Collections.Generic;
public record User(int Key, string Label);                 // 이름만 바꿨다
public static class Repo {
    public static (int Key, string Label) Find() => (1, "kim");                     // 이름만 바꿨다
    public static List<(int Key, string Label)> All() => new() { (1, "kim"), (2, "lee") };
    public static User FindUser() => new(1, "kim");
}
===== csc -target:library -out:Repo.dll cs23b-lib2.cs && dotnet app.dll    # app.dll 은 다시 컴파일하지 않았다 (cc exit=0 · run exit=0) =====
[1] t.Id=1 t.Name=kim
[2] r.Id=1
[2] r.Id=2
[3] RuntimeBinderException : 'System.ValueTuple<int,string>' does not contain a definition for 'Id'
[4] MissingMethodException : Method not found: 'Int32 User.get_Id()'.
===== csc -r:Repo.dll -out:app2.dll cs23b-app.cs 2>&1 | sort (cc exit=1) =====
cs23b-app.cs(12,46): error CS1061: 'User' does not contain a definition for 'Id' and no accessible extension method 'Id' accepting a first argument of type 'User' could be found (are you missing a using directive or an assembly reference?)
cs23b-app.cs(5,41): error CS1061: '(int Key, string Label)' does not contain a definition for 'Id' and no accessible extension method 'Id' accepting a first argument of type '(int Key, string Label)' could be found (are you missing a using directive or an assembly reference?)
cs23b-app.cs(5,55): error CS1061: '(int Key, string Label)' does not contain a definition for 'Name' and no accessible extension method 'Name' accepting a first argument of type '(int Key, string Label)' could be found (are you missing a using directive or an assembly reference?)
cs23b-app.cs(6,71): error CS1061: '(int Key, string Label)' does not contain a definition for 'Id' and no accessible extension method 'Id' accepting a first argument of type '(int Key, string Label)' could be found (are you missing a using directive or an assembly reference?)
```

**왜 그런가**

- ★★★ **첫 판** — `[1]` `t.Id=1 t.Name=kim` · `[2]` 두 줄 · **`[3]` `RuntimeBinderException`** · `[4]` `user.Id=1`. **다른 어셈블리의 컴파일러는 이름을 되살렸다**(반환값 특성). `dynamic` 은 **특성을 안 보니** 처음부터 실패한다.
- ★★★ **바꿔 끼운 판** — 튜플 `[1]`·`[2]` 는 **그대로**(앱 IL 에는 `Item1` 만 박혔다) · **record `[4]` 는 `Method not found: 'Int32 User.get_Id()'`**.
- ★★ **다시 컴파일** — **`CS1061` 넷**(튜플 셋 · record 하나). 소스 호환은 둘 다 깨진다.

### 6. ★★ 튜플 JSON 은 **`{}`** — 에러도 경고도 없다

**출력**

```text
===== 소스: cs23b-json.cs =====
using System;
using System.Text.Json;
record User(int Id, string Name);
class Program {
    static void Main() {
        (int Id, string Name) t = (1, "kim");
        var u = new User(1, "kim");
        Console.WriteLine($"[1] 튜플 ToString   : {t}");
        Console.WriteLine($"[2] record ToString : {u}");
        Console.WriteLine($"[3] 튜플 JSON       : {JsonSerializer.Serialize(t)}");
        Console.WriteLine($"[4] record JSON     : {JsonSerializer.Serialize(u)}");
        Console.WriteLine($"[5] 튜플 JSON(필드 포함) : {JsonSerializer.Serialize(t, new JsonSerializerOptions { IncludeFields = true })}");
        object o = t;
        Console.WriteLine($"[6] object 로 올린 뒤 : {o.GetType().GetField("Item1")?.GetValue(o)} · Id 필드 {(o.GetType().GetField("Id") is null ? "없음" : "있음")}");
    }
}
===== csc -out:ex.dll cs23b-json.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] 튜플 ToString   : (1, kim)
[2] record ToString : User { Id = 1, Name = kim }
[3] 튜플 JSON       : {}
[4] record JSON     : {"Id":1,"Name":"kim"}
[5] 튜플 JSON(필드 포함) : {"Item1":1,"Item2":"kim"}
[6] object 로 올린 뒤 : 1 · Id 필드 없음
```

**왜 그런가**

- ★★★ **`[3]` `{}`** — `System.Text.Json` 은 기본으로 **공개 속성**만 본다. 튜플 원소는 **필드**다(1번 `[4]` 속성 0개). **조용한 실패**다.
- ★★ **`[5]` 필드를 켜도 `Item1`·`Item2`** — 이름은 끝내 안 나온다.
- ★★ **`[2]`·`[4]` record 는 이름째** · **`[6]` `object` 로 올린 값에는 `Id` 필드가 없다.**

### 7. ★★ 값 튜플·`record struct` **0**, `Tuple<>`·`record class` **24000** — 갈린 줄 **0 / 4**

**출력**

```text
===== 소스: cs23b-alloc.cs =====
using System;
record class RC(int A, int B);
record struct RS(int A, int B);
class Program {
    static (int A, int B) VT(int i)          => (i, i + 1);
    static Tuple<int, int> T(int i)          => Tuple.Create(i, i + 1);
    static RC C(int i)                       => new(i, i + 1);
    static RS S(int i)                       => new(i, i + 1);
    static long M(Action a) {
        for (int i = 0; i < 200; i++) a();
        var b = GC.GetAllocatedBytesForCurrentThread();
        a();
        return GC.GetAllocatedBytesForCurrentThread() - b;
    }
    static void Main() {
        long sink = 0;
        Console.WriteLine($"[1] (int, int) 값 튜플     1000번 : {M(() => { for (int i = 0; i < 1000; i++) sink += VT(i).B; })} 바이트");
        Console.WriteLine($"[2] Tuple<int, int>       1000번 : {M(() => { for (int i = 0; i < 1000; i++) sink += T(i).Item2; })} 바이트");
        Console.WriteLine($"[3] record class          1000번 : {M(() => { for (int i = 0; i < 1000; i++) sink += C(i).B; })} 바이트");
        Console.WriteLine($"[4] record struct         1000번 : {M(() => { for (int i = 0; i < 1000; i++) sink += S(i).B; })} 바이트");
        GC.KeepAlive(sink);
    }
}
===== csc -out:ex.dll cs23b-alloc.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] (int, int) 값 튜플     1000번 : 0 바이트
[2] Tuple<int, int>       1000번 : 24000 바이트
[3] record class          1000번 : 24000 바이트
[4] record struct         1000번 : 0 바이트
===== csc -out:ex.dll cs23b-alloc.cs && DOTNET_TieredCompilation=0 dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] (int, int) 값 튜플     1000번 : 0 바이트
[2] Tuple<int, int>       1000번 : 24000 바이트
[3] record class          1000번 : 24000 바이트
[4] record struct         1000번 : 0 바이트
===== csc -optimize -out:exo.dll cs23b-alloc.cs && dotnet exo.dll (cc exit=0 · run exit=0) =====
[1] (int, int) 값 튜플     1000번 : 0 바이트
[2] Tuple<int, int>       1000번 : 24000 바이트
[3] record class          1000번 : 24000 바이트
[4] record struct         1000번 : 0 바이트
===== csc -optimize -out:exo.dll cs23b-alloc.cs && DOTNET_TieredCompilation=0 dotnet exo.dll (cc exit=0 · run exit=0) =====
[1] (int, int) 값 튜플     1000번 : 0 바이트
[2] Tuple<int, int>       1000번 : 24000 바이트
[3] record class          1000번 : 24000 바이트
[4] record struct         1000번 : 0 바이트
===== 네 판 대조 — 「바이트」 줄마다 네 판의 값이 같은가 =====
네 판에서 갈린 줄 0 / 4
```

**왜 그런가**

- ★★★ **값 타입 둘은 0, 참조 타입 둘은 24000**(1000번) — 네 판이 다 같았다.
- ★★★ **「가벼움」은 튜플만의 것이 아니다** — `record struct` 도 0 이다. 튜플을 고르는 이유는 **가벼움이 아니라 「이름 없는 임시 묶음」** 이어야 한다.

### 8. ★★★ 공개 API · 직렬화 · 이름이 계약인 곳 → **record**

- ★★★ **공개 API 의 문제는 「이름이 사라진다」가 아니다**(5번 — 컴파일러는 되살린다). **런타임에 이름을 찾는 모든 것**(JSON `{}` · `dynamic` · 리플렉션)이 못 본다는 것이다(6번).
- ★★ **이름이 바뀔 수 있는 데이터에서는 튜플이 더 위험하다** — 옛 앱이 **조용히** 돈다. 이름의 **뜻**이 바뀌었어도(`Id` → `Key`) 옛 앱은 모른 채 `Item1` 을 읽는다. record 는 **시끄럽게** 깨져서 알 수 있다.
- ★ **튜플이 맞는 자리** — **private·지역 범위의 여러 값 반환**, 받자마자 해체하는 곳.

### 9. ★★ 값에는 **원래 이름이 없어서** — 다른 어셈블리·`dynamic`·JSON 으로 **창을 바꿨다**

- ★★ 1번 `[3]` 이 보여 주듯 **값의 타입은 ``ValueTuple`2[Int32,String]`` 뿐**이다 — 「경계를 넘나」를 물을 **대상이 값에 없다.** 이름은 **메서드 서명의 특성**에 있다.
- ★★ 그래서 **「이름을 불러 볼 주체」를 바꿨다** — 다른 어셈블리의 **컴파일러**(부를 수 있다) · **런타임 바인더**(`dynamic` — 못 부른다) · **직렬화기**(못 본다).\
  ★ 이 창이 못 보는 것 — **다른 리플렉션 기반 도구**(ORM·다른 직렬화기)는 안 던졌다.

### 10. 잇기

- ★★★ **`Deconstruct` 생성** — [18번](../18-record-value-equality-and-with/) (1).
- ★★ **`Equals` 만 고친 클래스의 `==` 는 참조 비교** — [19번](../19-equality-equals-gethashcode-operator/) (3).
- ★ **위치 패턴의 `Deconstruct` 1회** — [21번](../21-pattern-matching-type-property-relational-list/) (4).

## 실행 검증

| 무엇 | 몇 번·어디서 | 결과 |
|---|---|---|
| `cs23b-refl.cs` 리플렉션 | csc 1회 · 실행 1회 | ★★★ `Item1`·`Item2`(가변) · 이름은 반환값 특성 · `Rest` 중첩 |
| `cs23b-eq.cs` · `cs23b-names.cs` | csc 2회 · 실행 1회 | ★★★ 이름 무관 `True` · 원소별 `==` IL · `Money` `False`/`True` · `CS8123` ×2 |
| `cs23b-decon.cs` 해체 | csc 1회 · 실행 1회 | ★★★ 확장 `Deconstruct` 로 `Version` 해체 · 버린 원소도 호출 |
| `cs23b-mut.cs` · `cs23b-mut2.cs` | csc 2회 · 실행 1회 | `CS1612` ×2 · 배열은 됨 · 복사본 |
| `cs23b-lib1/lib2/app.cs` 어셈블리 둘 | csc 4회 · 실행 2회 | ★★★ 이름 되살림 · `dynamic` 실패 · 튜플은 그대로 · record 는 `MissingMethodException` · `CS1061` ×4 |
| `cs23b-json.cs` 직렬화 | csc 1회 · 실행 1회 | ★★★ 튜플 `{}` · record 이름째 |
| `cs23b-alloc.cs` | **2×2 판 격자** | ★★★ 0 · 24000 · 24000 · 0 · **갈린 줄 0 / 4** |
| `cs23b-form.cs` 형태 | csc 1회 · 실행 1회 | `3개 평균 6` · 정렬 해체 · `(3, 4)` |

**구현 의존 항목** — 다음은 **이 판(.NET SDK 10.0.401 · 런타임 10.0.12)에서만** 그렇다.

- ★★ **`System.Text.Json` 의 기본(속성만)** · **`RuntimeBinderException` 문구** · **할당 바이트 값**.

**언어가 보장하는 것**(구현이 바뀌어도 같다)

- **튜플은 `ValueTuple` · 이름은 런타임에 없다 · 대입과 `==` 는 이름을 안 본다 · `==` 는 원소별 `==`**.
- **해체는 `Deconstruct`(확장 포함)를 찾는다** · **8개부터 `Rest`**(BCL 타입 모양).

**안 돌려 본 것 / 못 잰 것 / 잴 것이 없는 것**

- **안 돌려 본 것** — ★ **튜플 `==` 의 평가 순서(부작용)** · ★ **C# 12 튜플 별칭** · ★ **ORM·다른 직렬화기** · ★ **Java 쪽**(튜플이 없어 대비만).
- **못 잰 것** — ★★ **시간** — 한 줄도 안 쟀다.
- **잴 것이 없는 것** — 없다. 네 창을 다 썼다.

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★ **6번** — 직렬화기 기본값이 바뀌면 `{}` 가 달라진다.
- ★★ **5번** — 런타임 바인더가 특성을 읽게 되면 `[3]` 이 바뀐다(그럴 계획은 확인하지 않았다).
- ★ **1·2·3번** — 명세가 정한 것이라 바뀔 일이 없다.
