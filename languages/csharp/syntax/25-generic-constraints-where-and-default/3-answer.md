# csharp/syntax/25 — 제네릭 제약 `where` 와 `default(T)` — 정답

> 복습 시 이 파일은 **최후에만** 연다. 정답을 봤으면 닫고 자기 말로 한 번 재산출한다.
> 이 파일의 모든 출력·진단·IL·할당 바이트는 **.NET SDK 10.0.401** · 런타임 **10.0.12** · 타겟 **`net10.0`** ·
> **linux-x64** 에서 실제로 돌려 얻은 것이다(2026-09-26).\
> 진단은 **`-preferreduilang:en-US`** 로 영어로 고정했다.\
> ★ 블록은 캡처 스크립트가 파일로 받아 조립기가 끼워 넣은 것이다 — 손으로 옮긴 줄은 없다.\
> ★ 진단을 싣는 블록은 전부 **그 진단을 낸 소스를 같은 블록 안에** 다시 싣는다(`===== 소스: … =====`).
> **읽는 법** — 근거로 쓰는 것은 **진단 코드 · `(행,열)` · 옵코드 · 리플렉션 플래그 · 예외 타입 · 스크립트가 센 칸 수** 다.
> ★★★ **이 문서는 시간을 재지 않았다.**

## 정답

<!-- 1-question.md 의 번호·문구와 1:1 대응. 질문 하나 = A 하나. -->

### 1. ★★★ **막힘 47 · 경고만 4 · 통과 29** — `int?` 는 **`New` 만** 통과

**출력**

```text
===== 소스: cs25b-grid.cs =====
using System;
abstract class Shape { }
struct Pt { public int X; public Pt(int x) { X = x; } }
static class K {
    public static void Class<T>()     where T : class { }
    public static void ClassQ<T>()    where T : class? { }
    public static void Struct<T>()    where T : struct { }
    public static void NotNull<T>()   where T : notnull { }
    public static void Unmanaged<T>() where T : unmanaged { }
    public static void New<T>()       where T : new() { }
    public static void IComp<T>()     where T : IComparable { }
    public static void Base<T>()      where T : Shape { }
    public static void Enum<T>()      where T : System.Enum { }
    public static void Deleg<T>()     where T : Delegate { }
}
class Program {
    static void Main() {
        K.Class<int>(); K.Class<int?>(); K.Class<string>(); K.Class<string?>(); K.Class<Shape>(); K.Class<Pt>(); K.Class<DayOfWeek>(); K.Class<Action>();
        K.ClassQ<int>(); K.ClassQ<int?>(); K.ClassQ<string>(); K.ClassQ<string?>(); K.ClassQ<Shape>(); K.ClassQ<Pt>(); K.ClassQ<DayOfWeek>(); K.ClassQ<Action>();
        K.Struct<int>(); K.Struct<int?>(); K.Struct<string>(); K.Struct<string?>(); K.Struct<Shape>(); K.Struct<Pt>(); K.Struct<DayOfWeek>(); K.Struct<Action>();
        K.NotNull<int>(); K.NotNull<int?>(); K.NotNull<string>(); K.NotNull<string?>(); K.NotNull<Shape>(); K.NotNull<Pt>(); K.NotNull<DayOfWeek>(); K.NotNull<Action>();
        K.Unmanaged<int>(); K.Unmanaged<int?>(); K.Unmanaged<string>(); K.Unmanaged<string?>(); K.Unmanaged<Shape>(); K.Unmanaged<Pt>(); K.Unmanaged<DayOfWeek>(); K.Unmanaged<Action>();
        K.New<int>(); K.New<int?>(); K.New<string>(); K.New<string?>(); K.New<Shape>(); K.New<Pt>(); K.New<DayOfWeek>(); K.New<Action>();
        K.IComp<int>(); K.IComp<int?>(); K.IComp<string>(); K.IComp<string?>(); K.IComp<Shape>(); K.IComp<Pt>(); K.IComp<DayOfWeek>(); K.IComp<Action>();
        K.Base<int>(); K.Base<int?>(); K.Base<string>(); K.Base<string?>(); K.Base<Shape>(); K.Base<Pt>(); K.Base<DayOfWeek>(); K.Base<Action>();
        K.Enum<int>(); K.Enum<int?>(); K.Enum<string>(); K.Enum<string?>(); K.Enum<Shape>(); K.Enum<Pt>(); K.Enum<DayOfWeek>(); K.Enum<Action>();
        K.Deleg<int>(); K.Deleg<int?>(); K.Deleg<string>(); K.Deleg<string?>(); K.Deleg<Shape>(); K.Deleg<Pt>(); K.Deleg<DayOfWeek>(); K.Deleg<Action>();
    }
}
===== csc -nullable:enable -out:ex.dll cs25b-grid.cs 2>&1 | sort | awk '!s[$3]++' | sort -k3,3 (cc exit=1) =====
cs25b-grid.cs(23,124): error CS0310: 'Action' must be a non-abstract type with a public parameterless constructor in order to use it as parameter 'T' in the generic type or method 'K.New<T>()'
cs25b-grid.cs(24,138): error CS0311: The type 'System.Action' cannot be used as type parameter 'T' in the generic type or method 'K.IComp<T>()'. There is no implicit reference conversion from 'System.Action' to 'System.IComparable'.
cs25b-grid.cs(25,26): error CS0312: The type 'int?' cannot be used as type parameter 'T' in the generic type or method 'K.Base<T>()'. The nullable type 'int?' does not satisfy the constraint of 'Shape'.
cs25b-grid.cs(24,27): error CS0313: The type 'int?' cannot be used as type parameter 'T' in the generic type or method 'K.IComp<T>()'. The nullable type 'int?' does not satisfy the constraint of 'System.IComparable'. Nullable types can not satisfy any interface constraints.
cs25b-grid.cs(24,101): error CS0315: The type 'Pt' cannot be used as type parameter 'T' in the generic type or method 'K.IComp<T>()'. There is no boxing conversion from 'Pt' to 'System.IComparable'.
cs25b-grid.cs(18,101): error CS0452: The type 'Pt' must be a reference type in order to use it as parameter 'T' in the generic type or method 'K.Class<T>()'
cs25b-grid.cs(20,145): error CS0453: The type 'Action' must be a non-nullable value type in order to use it as parameter 'T' in the generic type or method 'K.Struct<T>()'
cs25b-grid.cs(22,166): error CS8377: The type 'Action' must be a non-nullable value type, along with all fields at any level of nesting, in order to use it as parameter 'T' in the generic type or method 'K.Unmanaged<T>()'
cs25b-grid.cs(24,61): warning CS8631: The type 'string?' cannot be used as type parameter 'T' in the generic type or method 'K.IComp<T>()'. Nullability of type argument 'string?' doesn't match constraint type 'System.IComparable'.
cs25b-grid.cs(18,61): warning CS8634: The type 'string?' cannot be used as type parameter 'T' in the generic type or method 'K.Class<T>()'. Nullability of type argument 'string?' doesn't match 'class' constraint.
cs25b-grid.cs(21,27): warning CS8714: The type 'int?' cannot be used as type parameter 'T' in the generic type or method 'K.NotNull<T>()'. Nullability of type argument 'int?' doesn't match 'notnull' constraint.
===== 격자 — 위 컴파일의 진단 전부를 (제약, 인자) 칸으로 되돌린 표 =====
제약 \ 인자     int             int?            string          string?         Shape           Pt              DayOfWeek       Action
Class       CS0452          CS0452          ok              CS8634(w)       ok              CS0452          CS0452          ok
ClassQ      CS0452          CS0452          ok              ok              ok              CS0452          CS0452          ok
Struct      ok              CS0453          CS0453          CS0453          CS0453          ok              ok              CS0453
NotNull     ok              CS8714(w)       ok              CS8714(w)       ok              ok              ok              ok
Unmanaged   ok              CS8377          CS8377          CS8377          CS8377          ok              ok              CS8377
New         ok              ok              CS0310          CS0310          CS0310          ok              ok              CS0310
IComp       ok              CS0313          ok              CS8631(w)       CS0311          CS0315          ok              CS0311
Base        CS0315          CS0312          CS0311          CS0311          ok              CS0315          CS0315          CS0311
Enum        CS0315          CS0312          CS0311          CS0311          CS0311          CS0315          ok              CS0311
Deleg       CS0315          CS0312          CS0311          CS0311          CS0311          CS0315          CS0315          ok
막힌 칸(에러) 47 / 80 · 경고만 난 칸 4 / 80 · 통과 칸 29 / 80
```

**왜 그런가**

- ★★★ **스크립트가 진단의 `(행,열)` 을 칸으로 되돌려 셌다** — 마지막 줄 `막힌 칸(에러) 47 / 80 · 경고만 난 칸 4 / 80 · 통과 칸 29 / 80`.
- ★★★ **`int?` 행** — `Struct` `CS0453` · `Unmanaged` `CS8377` · `IComp` `CS0313` 인데 **`New` 는 `ok`** — `Nullable<int>` 는 공개 기본 생성자가 있는 구조체다. `struct` 제약만 「**널 불가**」를 따로 요구한다.
- ★★ **`string?` 이 경고로 떨어지는 칸** — `Class`(`CS8634`) · `IComp`(`CS8631`) · `NotNull`(`CS8714`). **`ClassQ` 는 `ok`** — `class?` 는 널 허용 참조 타입을 받으라는 뜻이다.
- ★★ **`CS0311` 은 참조 타입인데 암시적 참조 변환이 없는 것, `CS0315` 는 값 타입인데 박싱 변환이 없는 것** — 같은 「인터페이스를 안 구현한다」가 **인자의 종류로** 코드가 갈린다. `int?` 는 따로 `CS0312`(기반 클래스)·`CS0313`(인터페이스).

### 2. ★★★ **전부 0 인 비트** — `default(Pz).X` 는 **0**, `new Pz()`·`Make<Pz>()` 는 **7**

**출력**

```text
===== 소스: cs25b-default.cs =====
using System;
using System.Globalization;
struct Pt { public int X; public string? Name; public Pt(int x) { X = x; Name = "set"; } }
struct Pz { public int X; public Pz() { X = 7; } }
static class G {
    public static T Def<T>() => default!;
    public static T Make<T>() where T : new() => new T();
    public static string Show<T>(T v) => v is null ? "null" : Convert.ToString(v, CultureInfo.InvariantCulture)!;
}
class Program {
    static void Main() {
        Console.WriteLine($"[1] Def<int>()        = {G.Show(G.Def<int>())}");
        Console.WriteLine($"[2] Def<int?>()       = {G.Show(G.Def<int?>())}");
        Console.WriteLine($"[3] Def<string>()     = {G.Show(G.Def<string>())}");
        Console.WriteLine($"[4] Def<bool>()       = {G.Show(G.Def<bool>())}");
        Console.WriteLine($"[5] Def<double>()     = {G.Show(G.Def<double>())}");
        Console.WriteLine($"[6] Def<DateTime>()   = {G.Def<DateTime>().ToString("o", CultureInfo.InvariantCulture)}");
        Console.WriteLine($"[7] Def<DayOfWeek>()  = {G.Show(G.Def<DayOfWeek>())}");
        var p = G.Def<Pt>();
        Console.WriteLine($"[8] Def<Pt>()         = X={p.X} Name={G.Show(p.Name)}");
        Console.WriteLine($"[9] Def<(int,string)>() = {G.Def<(int, string)>()}");
        Console.WriteLine($"[10] Def<Pz>().X      = {G.Def<Pz>().X}");
        Console.WriteLine($"[11] Make<Pz>().X     = {G.Make<Pz>().X}");
        Console.WriteLine($"[12] default(Pz).X    = {default(Pz).X} · new Pz().X = {new Pz().X}");
    }
}
===== csc -nullable:enable -out:ex.dll cs25b-default.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] Def<int>()        = 0
[2] Def<int?>()       = null
[3] Def<string>()     = null
[4] Def<bool>()       = False
[5] Def<double>()     = 0
[6] Def<DateTime>()   = 0001-01-01T00:00:00.0000000
[7] Def<DayOfWeek>()  = Sunday
[8] Def<Pt>()         = X=0 Name=null
[9] Def<(int,string)>() = (0, )
[10] Def<Pz>().X      = 0
[11] Make<Pz>().X     = 7
[12] default(Pz).X    = 0 · new Pz().X = 7
```

**왜 그런가**

- ★★★ **`0` · `null` · `null` · `False` · `0` · `0001-01-01T00:00:00.0000000` · `Sunday` · `X=0 Name=null` · `(0, )`** — 타입이 무엇이든 **0 으로 채운 칸**을 그 타입으로 읽은 값이다. `[8]` 의 **생성자는 불리지 않았다**(`Name=null`).
- ★★★ **`[10]` `0` · `[11]` `7` · `[12]` `0 · 7`** — `default` 는 **생성자를 안 부르고**, `new Pz()` 와 `new T()`(→ `Activator`) 는 **매개변수 없는 생성자를 부른다.** 구조체에서 둘이 갈리는 자리다.

### 3. ★★ **`initobj T`** — `new T()` 는 제약과 무관하게 **`Activator::CreateInstance<T>`**

**출력**

```text
===== 소스: cs25b-il.cs =====
using System;
public static class G {
    public static T Def<T>() => default!;
    public static T NewAny<T>() where T : new() => new T();
    public static T NewStruct<T>() where T : struct => new T();
    public static T NewClass<T>() where T : class, new() => new T();
}
class Program {
    static void Main() {
        foreach (var n in new[] { "Def", "NewAny", "NewStruct", "NewClass" }) Il.Dump(typeof(G), n);
    }
}
===== csc -r:il.dll -out:ex.dll cs25b-il.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
--- G.Def ---
  .locals [0] T
  IL_0000: ldloca.s 0
  IL_0002: initobj T
  IL_0008: ldloc.0
  IL_0009: ret
--- G.NewAny ---
  IL_0000: call System.Activator::CreateInstance<T>
  IL_0005: ret
--- G.NewStruct ---
  IL_0000: call System.Activator::CreateInstance<T>
  IL_0005: ret
--- G.NewClass ---
  IL_0000: call System.Activator::CreateInstance<T>
  IL_0005: ret
===== csc -optimize -r:il.dll -out:exo.dll cs25b-il.cs && dotnet exo.dll (cc exit=0 · run exit=0) =====
--- G.Def ---
  .locals [0] T
  IL_0000: ldloca.s 0
  IL_0002: initobj T
  IL_0008: ldloc.0
  IL_0009: ret
--- G.NewAny ---
  IL_0000: call System.Activator::CreateInstance<T>
  IL_0005: ret
--- G.NewStruct ---
  IL_0000: call System.Activator::CreateInstance<T>
  IL_0005: ret
--- G.NewClass ---
  IL_0000: call System.Activator::CreateInstance<T>
  IL_0005: ret
```

**왜 그런가**

- ★★★ **`Def` 는 `initobj T`** — 지역 변수 칸을 0 으로 채운다.
- ★★★ **`NewAny`·`NewStruct`·`NewClass` 가 한 글자도 같다** — `struct` 제약이어도 `initobj` 로 바꾸지 않는다. 구조체에도 생성자가 있을 수 있어서다(2번 `Pz`). `-optimize` 판도 같다.

### 4. ★★ **`InvalidOperationException`** 대 **`TargetInvocationException`**(안에 원래 예외)

**출력**

```text
===== 소스: cs25b-throw.cs =====
using System;
class Boom { public Boom() { throw new InvalidOperationException("ctor failed"); } }
static class G { public static T Make<T>() where T : new() => new T(); }
class Program {
    static void Main() {
        try { new Boom(); }
        catch (Exception e) { Console.WriteLine($"[1] new Boom()    → {e.GetType().FullName}: {e.Message}"); }
        try { G.Make<Boom>(); }
        catch (Exception e) {
            Console.WriteLine($"[2] Make<Boom>() → {e.GetType().FullName}: {e.Message}");
            Console.WriteLine($"    InnerException → {e.InnerException?.GetType().FullName}: {e.InnerException?.Message}");
        }
    }
}
===== csc -out:ex.dll cs25b-throw.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] new Boom()    → System.InvalidOperationException: ctor failed
[2] Make<Boom>() → System.Reflection.TargetInvocationException: Exception has been thrown by the target of an invocation.
    InnerException → System.InvalidOperationException: ctor failed
===== csc -optimize -out:exo.dll cs25b-throw.cs && DOTNET_TieredCompilation=0 dotnet exo.dll (cc exit=0 · run exit=0) =====
[1] new Boom()    → System.InvalidOperationException: ctor failed
[2] Make<Boom>() → System.Reflection.TargetInvocationException: Exception has been thrown by the target of an invocation.
    InnerException → System.InvalidOperationException: ctor failed
```

**왜 그런가**

- ★★★ **`[2]` 는 `System.Reflection.TargetInvocationException`** 이고 `InnerException` 이 `InvalidOperationException: ctor failed` 다 — `new T()` 가 **`Activator` 를 거치기** 때문이다(3번).
- ★ **`catch (InvalidOperationException)` 만으로는 못 잡는다.** 이 감싸기는 **이 판(BCL)의 관찰**이다 — 언어는 `new T()` 의 구현을 정하지 않는다.

### 5. ★★★ 플래그가 있는 제약은 **런타임도 막는다** — `ok` 는 **`Unmanaged<HasRef>` 와 `NotNull<String>`**

**출력**

```text
===== 소스: cs25b-refl.cs =====
using System;
using System.Linq;
struct HasRef { public string S; public HasRef(string s) { S = s; } }
abstract class Shape { }
static class G {
    public static string Class<T>()     where T : class => typeof(T).Name;
    public static string ClassQ<T>()    where T : class? => typeof(T).Name;
    public static string Struct<T>()    where T : struct => typeof(T).Name;
    public static string New<T>()       where T : new() => typeof(T).Name;
    public static string NotNull<T>()   where T : notnull => typeof(T).Name;
    public static string Unmanaged<T>() where T : unmanaged => typeof(T).Name;
    public static string IComp<T>()     where T : IComparable<T> => typeof(T).Name;
    public static string Enum<T>()      where T : System.Enum => typeof(T).Name;
}
class Program {
    static string Attrs(System.Collections.Generic.IList<System.Reflection.CustomAttributeData> xs) =>
        string.Join(",", xs.Select(a => a.AttributeType.Name.Replace("Attribute", "") + "(" + string.Join(",", a.ConstructorArguments.Select(x => x.Value)) + ")"));
    static void Try(string m, Type arg) {
        try { var r = typeof(G).GetMethod(m)!.MakeGenericMethod(arg).Invoke(null, null); Console.WriteLine($"   {m,-9}<{arg.Name,-11}> ok → {r}"); }
        catch (Exception e) { Console.WriteLine($"   {m,-9}<{arg.Name,-11}> {e.GetType().Name}"); }
    }
    static void Main() {
        Console.WriteLine($"[A] 제약이 메타데이터에 남은 모양 (클래스 G 의 특성=[{Attrs(typeof(G).GetCustomAttributesData())}])");
        foreach (var n in new[] { "Class", "ClassQ", "Struct", "New", "NotNull", "Unmanaged", "IComp", "Enum" }) {
            var mi = typeof(G).GetMethod(n)!;
            var t = mi.GetGenericArguments()[0];
            Console.WriteLine($"   {n,-9} 플래그={t.GenericParameterAttributes} · 타입=[{string.Join(",", t.GetGenericParameterConstraints().Select(c => c.Name))}] · T 특성=[{Attrs(t.GetCustomAttributesData())}] · 메서드 특성=[{Attrs(mi.GetCustomAttributesData())}]");
        }
        Console.WriteLine("[B] 컴파일러를 건너뛰고 MakeGenericMethod 로 어긴 인자를 넣으면");
        Try("Class", typeof(int)); Try("Struct", typeof(string)); Try("Struct", typeof(int?)); Try("New", typeof(Shape));
        Try("IComp", typeof(Shape)); Try("Enum", typeof(int)); Try("Unmanaged", typeof(string));
        Try("Unmanaged", typeof(HasRef)); Try("NotNull", typeof(string));
    }
}
===== csc -nullable:enable -out:ex.dll cs25b-refl.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[A] 제약이 메타데이터에 남은 모양 (클래스 G 의 특성=[NullableContext(1),Nullable(0)])
   Class     플래그=ReferenceTypeConstraint · 타입=[] · T 특성=[] · 메서드 특성=[]
   ClassQ    플래그=ReferenceTypeConstraint · 타입=[] · T 특성=[Nullable(2)] · 메서드 특성=[]
   Struct    플래그=NotNullableValueTypeConstraint, DefaultConstructorConstraint · 타입=[ValueType] · T 특성=[] · 메서드 특성=[NullableContext(0)]
   New       플래그=DefaultConstructorConstraint · 타입=[] · T 특성=[Nullable(2)] · 메서드 특성=[]
   NotNull   플래그=None · 타입=[] · T 특성=[] · 메서드 특성=[]
   Unmanaged 플래그=NotNullableValueTypeConstraint, DefaultConstructorConstraint · 타입=[ValueType] · T 특성=[IsUnmanaged()] · 메서드 특성=[NullableContext(0)]
   IComp     플래그=None · 타입=[IComparable`1] · T 특성=[Nullable(0)] · 메서드 특성=[]
   Enum      플래그=None · 타입=[Enum] · T 특성=[Nullable(0)] · 메서드 특성=[]
[B] 컴파일러를 건너뛰고 MakeGenericMethod 로 어긴 인자를 넣으면
   Class    <Int32      > ArgumentException
   Struct   <String     > ArgumentException
   Struct   <Nullable`1 > ArgumentException
   New      <Shape      > ArgumentException
   IComp    <Shape      > ArgumentException
   Enum     <Int32      > ArgumentException
   Unmanaged<String     > ArgumentException
   Unmanaged<HasRef     > ok → HasRef
   NotNull  <String     > ok → String
```

**왜 그런가**

- ★★★ **`class` 와 `class?` 는 플래그가 같다**(`ReferenceTypeConstraint`) — 다른 것은 `Nullable(2)` 특성뿐. **`notnull` 은 플래그 `None`**.
- ★★★ **[B] 일곱 줄이 `ArgumentException`** — CLI 가 `MakeGenericMethod` 에서 **플래그와 타입 목록을 다시 검사**한다.
- ★★★ **`Unmanaged<HasRef>` 는 `ok`** — 런타임에 `unmanaged` 는 **`struct` 플래그**일 뿐이라 「참조 없음」을 안 본다. **`NotNull<String>` 도 `ok`** — 런타임에는 가를 정보가 없다.

### 6. ★★★ **`0` · `0` · `null` · `null` · `null`** — `[2]` 와 `[3]` 은 **값이 다르다**

**출력**

```text
===== 소스: cs25b-tq.cs =====
using System;
static class F {
    public static T? Any<T>(bool hit, T v) => hit ? v : default;
    public static T? Val<T>(bool hit, T v) where T : struct => hit ? v : default;
    public static T? Val2<T>(bool hit, T v) where T : struct => hit ? v : default(T?);
    public static T? Ref<T>(bool hit, T v) where T : class => hit ? v : default;
}
class Program {
    static string S(object? o) => o is null ? "null" : o.ToString()!;
    static string Ret(string m) => typeof(F).GetMethod(m)!.MakeGenericMethod(typeof(int)).ReturnType.Name;
    static void Main() {
        Console.WriteLine($"[1] Any(false, 5)   = {S(F.Any(false, 5))} · Any<int> 반환 타입 {Ret("Any")}");
        Console.WriteLine($"[2] Val(false, 5)   = {S(F.Val(false, 5))} · Val<int> 반환 타입 {Ret("Val")}");
        Console.WriteLine($"[3] Val2(false, 5)  = {S(F.Val2(false, 5))} · Val2<int> 반환 타입 {Ret("Val2")}");
        Console.WriteLine($"[4] Any(false, \"a\") = {S(F.Any(false, "a"))}");
        Console.WriteLine($"[5] Ref(false, \"a\") = {S(F.Ref(false, "a"))}");
    }
}
===== csc -nullable:enable -out:ex.dll cs25b-tq.cs && dotnet ex.dll (cc exit=0 · run exit=0) =====
[1] Any(false, 5)   = 0 · Any<int> 반환 타입 Int32
[2] Val(false, 5)   = 0 · Val<int> 반환 타입 Nullable`1
[3] Val2(false, 5)  = null · Val2<int> 반환 타입 Nullable`1
[4] Any(false, "a") = null
[5] Ref(false, "a") = null
```

**왜 그런가**

- ★★★ **`[1]` 제약 없는 `T?` 는 `int` 에서 `Int32`** — `Nullable` 이 아니므로 「없음」이 `0` 이다.
- ★★★ **`[2]` 반환 타입은 ``Nullable`1`` 인데 값은 `0`** — 조건식 `hit ? v : default` 에서 **`default` 의 타입이 `T`** 로 정해져 `0` 이 만들어진 뒤 감싸인다. **`[3]` `default(T?)`** 로 적어야 `null`.
- ★ **`[4]`·`[5]`** — 참조 타입의 `T?` 는 주석이라 어느 쪽이든 `null`.

### 7. ★★ **`CS0111`** — 그리고 **7.2 는 `CS0453`, 7.3 부터 `F(object)`**

- ★★★ **제약만 다른 두 `G<T>(T)` 는 `CS0111`** — 제약은 **서명의 일부가 아니다**(요약 (6)).
- ★★★ **7.2 는 `CS0453`**(제네릭 후보를 먼저 고르고 제약 위반으로 실패) · **7.3·latest 는 `F(object)`** — 7.3 부터 **제약을 어기는 후보를 먼저 거른다.** 「제약은 오버로드 해결에 안 참여한다」는 **7.2 까지의 사실**이다.

### 8. ★★ **`Enum`·`Delegate`·`unmanaged` 7.3 · `notnull` 8 · 제약 없는 `T?` 9** — `-langversion` 판 격자로

- ★★★ **한 소스를 7.2 · 7.3 · 8 · 9 로 던져 막힌 칸 8 / 20**(요약 (7)) — 진단 문구에 **요구 판이 박혀 나온다**(`… Please use language version 7.3 or greater.` · `'9.0' or greater`).
- ★ 같은 「기능 없음」이 **7.2 는 `CS8320`, 7.3 은 `CS8370`** 으로 번호가 다르다.

### 9. ★★★ **플래그가 있는 것은 ECMA-335 · 특성뿐인 것은 Roslyn**

- ★★★ **`class`·`struct`·`new()`·인터페이스·기반 클래스** — 메타데이터 **플래그·타입 목록**이고 **런타임이 다시 검사**한다(5번 [B]) → **CLI 명세**.
- ★★★ **`notnull`·`class?`** — 플래그가 없고 **`Nullable`/`NullableContext` 특성**뿐 → **컴파일러의 널 분석**. 그래서 위반이 **경고**다.
- ★★★ **`unmanaged`** — `struct` **플래그는 CLI 가 지키고**, 「참조를 안 품는다」는 **`IsUnmanaged` 특성**이라 **컴파일러만** 지킨다(`Unmanaged<HasRef>` 가 뒷문으로 통과).

### 10. ★ **더 할당하지 않았다** — 네 판에서 갈린 줄 **0 / 5** · 시간은 **안 쟀다**

- ★★ **`new Node()` 24000 · `G.Make<Node>()` 24000 · `Make<Pv>` 0 · `Def` 둘 다 0** — 2×2 판 격자에서 같았다(요약 (9)).
- ★ **「`new T()` 가 느리다」는 이 문서로 말할 수 없다** — 시간을 안 쟀다(규칙 4).

### 11. 잇기

- ★★ **`where T : class` 의 `==`** — [19번](../19-equality-equals-gethashcode-operator/) (3)(`box T` · `box T` · `ceq`).
- ★ **`Func<T>` 를 받는다** — 델리게이트의 정본은 [27번](../27-delegates-and-func-action/).

## 실행 검증

| 무엇 | 몇 번·어디서 | 결과 |
|---|---|---|
| `cs25b-grid.cs` 80칸 | csc 2회(격자·표본) | ★★★ **막힌 칸 47 / 80 · 경고만 4 · 통과 29** |
| `cs25b-default.cs` | csc 1회 · 실행 1회 | `default` 는 생성자 없이 0 · `Pz` 에서 `0` 대 `7` |
| `cs25b-il.cs` | csc 2회(기본 · `-optimize`) · 실행 2회 | `initobj T` · `Activator::CreateInstance<T>` ×3 |
| `cs25b-throw.cs` | csc 2회 · 실행 2회(기본 · `-optimize`+`TC=0`) | `TargetInvocationException`(안에 원래 예외) |
| `cs25b-refl.cs` | csc 1회 · 실행 1회 | 플래그 표 · 뒷문 9줄 중 `ok` 2 |
| `cs25b-sig.cs` · `cs25b-ovl.cs` | csc 1회 · csc 3회(7.2 · 7.3 · latest) · 실행 2회 | `CS0111` · 7.2 `CS0453` → 7.3 `F(object)` |
| `cs25b-ver.cs` | csc 8회(판 넷 × 2) | ★★ **막힌 칸 8 / 20** |
| `cs25b-tq.cs` | csc 1회 · 실행 1회 | `0` · `0` · `null` · `null` · `null` |
| `cs25b-alloc.cs` | **2×2 판 격자** | 24000 · 24000 · 0 · 0 · 0 · **갈린 줄 0 / 5** |
| `cs25b-form.cs` | csc 1회 · 실행 1회 | `9 · pear · 0 · DayOfWeek.Friday · 6` |

**구현 의존 항목** — 다음은 **이 판(.NET SDK 10.0.401 · 런타임 10.0.12)에서만** 그렇다.

- ★★ **`new T()` 가 `Activator.CreateInstance<T>`** — Roslyn · **생성자 예외 감싸기** — BCL · **특성 모양**(`Nullable(2)`·`IsUnmanaged`) — Roslyn · 할당 바이트.

**언어·CLI 가 보장하는 것**(구현이 바뀌어도 같다)

- **플래그·타입 제약의 런타임 검사**(ECMA-335) · **제약 위반은 컴파일 에러**(`notnull` 제외) · **`default(T)` 는 기본값** · **제약은 서명이 아니다.**

**안 돌려 본 것 / 못 잰 것 / 잴 것이 없는 것**

- **안 돌려 본 것** — ★ `allows ref struct` · `where T : default` · 정적 추상 멤버 제약 · NativeAOT 에서의 `new T()`.
- **못 잰 것** — ★★★ **시간**.
- **잴 것이 없는 것** — ★★ **`notnull`·`class?` 의 런타임 비용** — `string` 과 `string?` 이 런타임에 같은 타입이다([06번](../06-nullable-reference-types/)).

**버전이 올랐을 때 다시 돌려야 하는 것**

- ★★ **4번**(예외 감싸기)과 **3번**(`Activator` 경유) — 구현이다. Roslyn 이 `new T()` 를 다르게 내면 둘 다 움직인다.
- ★ **1번 격자** — 새 제약(예: `allows ref struct`)이 생기면 행을 늘려 다시.
