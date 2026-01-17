import pytest

from tests.utils import DiffTestCase, DiffTestRunner

CSHARP_NAMESPACE_CASES = [
    DiffTestCase(
        name="csharp_281_using_namespace",
        initial_files={
            "Utilities/StringHelper.cs": """namespace MyApp.Utilities;

public static class StringHelper
{
    public static string Capitalize(string input)
    {
        if (string.IsNullOrEmpty(input)) return input;
        return char.ToUpper(input[0]) + input.Substring(1);
    }

    public static string Reverse(string input)
    {
        char[] chars = input.ToCharArray();
        Array.Reverse(chars);
        return new string(chars);
    }
}
// garbage_marker_12345 - this should not appear in context
""",
            "Program.cs": """using System;

class Program
{
    static void Main() { }
}
""",
        },
        changed_files={
            "Program.cs": """using System;
using MyApp.Utilities;

class Program
{
    static void Main()
    {
        var result = StringHelper.Capitalize("hello");
        Console.WriteLine(result);
    }
}
""",
        },
        must_include=["StringHelper", "Capitalize"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add using namespace",
    ),
    DiffTestCase(
        name="csharp_282_partial_class",
        initial_files={
            "Models/User.cs": """namespace MyApp.Models;

public partial class User
{
    public int Id { get; set; }
    public string Name { get; set; }
}
// unused_marker_67890
""",
            "Models/User.Validation.cs": """namespace MyApp.Models;

public partial class User
{
    public bool IsValid()
    {
        return !string.IsNullOrEmpty(Name);
    }
}
""",
            "Services/UserService.cs": """namespace MyApp.Services;

public class UserService { }
""",
        },
        changed_files={
            "Services/UserService.cs": """using MyApp.Models;

namespace MyApp.Services;

public class UserService
{
    public bool ValidateUser(User user)
    {
        return user.IsValid();
    }
}
""",
        },
        must_include=["UserService", "ValidateUser", "User"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add partial class usage",
    ),
]


CSHARP_ASYNC_CASES = [
    DiffTestCase(
        name="csharp_283_async_await",
        initial_files={
            "Services/DataService.cs": """namespace MyApp.Services;

public class DataService
{
    public async Task<string> FetchDataAsync(string url)
    {
        await Task.Delay(100);
        return "data from " + url;
    }
}
// garbage_marker_12345
""",
            "Program.cs": """using System;

class Program
{
    static void Main() { }
}
""",
        },
        changed_files={
            "Program.cs": """using System;
using System.Threading.Tasks;
using MyApp.Services;

class Program
{
    static async Task Main()
    {
        var service = new DataService();
        var data = await service.FetchDataAsync("http://example.com");
        Console.WriteLine(data);
    }
}
""",
        },
        must_include=["DataService", "FetchDataAsync"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add async/await usage",
    ),
    DiffTestCase(
        name="csharp_284_task_run",
        initial_files={
            "Services/ComputeService.cs": """namespace MyApp.Services;

public class ComputeService
{
    public int HeavyComputation(int input)
    {
        int result = 0;
        for (int i = 0; i < 1000000; i++)
        {
            result += input;
        }
        return result;
    }
}
// unused_marker_67890
""",
            "Program.cs": """using System;

class Program
{
    static void Main() { }
}
""",
        },
        changed_files={
            "Program.cs": """using System;
using System.Threading.Tasks;
using MyApp.Services;

class Program
{
    static async Task Main()
    {
        var service = new ComputeService();
        var result = await Task.Run(() => service.HeavyComputation(42));
        Console.WriteLine(result);
    }
}
""",
        },
        must_include=["ComputeService", "HeavyComputation"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add Task.Run usage",
    ),
    DiffTestCase(
        name="csharp_285_cancellation_token",
        initial_files={
            "Services/DownloadService.cs": """using System.Threading;

namespace MyApp.Services;

public class DownloadService
{
    public async Task<byte[]> DownloadAsync(string url, CancellationToken cancellationToken)
    {
        await Task.Delay(1000, cancellationToken);
        return new byte[100];
    }
}
// garbage_marker_12345
""",
            "Program.cs": """using System;

class Program
{
    static void Main() { }
}
""",
        },
        changed_files={
            "Program.cs": """using System;
using System.Threading;
using System.Threading.Tasks;
using MyApp.Services;

class Program
{
    static async Task Main()
    {
        var cts = new CancellationTokenSource(TimeSpan.FromSeconds(5));
        var service = new DownloadService();

        try
        {
            var data = await service.DownloadAsync("http://example.com", cts.Token);
            Console.WriteLine($"Downloaded {data.Length} bytes");
        }
        catch (OperationCanceledException)
        {
            Console.WriteLine("Download cancelled");
        }
    }
}
""",
        },
        must_include=["DownloadService", "DownloadAsync", "CancellationToken"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add cancellation token usage",
    ),
]


CSHARP_INTERFACE_CASES = [
    DiffTestCase(
        name="csharp_286_interface_implementation",
        initial_files={
            "Interfaces/IRepository.cs": """namespace MyApp.Interfaces;

public interface IRepository<T>
{
    T GetById(int id);
    void Save(T entity);
    void Delete(int id);
}
// unused_marker_67890
""",
            "Repositories/UserRepository.cs": """namespace MyApp.Repositories;

public class UserRepository { }
""",
        },
        changed_files={
            "Repositories/UserRepository.cs": """using MyApp.Interfaces;
using MyApp.Models;

namespace MyApp.Repositories;

public class UserRepository : IRepository<User>
{
    private readonly Dictionary<int, User> _users = new();

    public User GetById(int id) => _users.GetValueOrDefault(id);

    public void Save(User entity) => _users[entity.Id] = entity;

    public void Delete(int id) => _users.Remove(id);
}
""",
        },
        must_include=["UserRepository", "IRepository"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add interface implementation",
    ),
    DiffTestCase(
        name="csharp_287_explicit_interface",
        initial_files={
            "Interfaces/ILogger.cs": """namespace MyApp.Interfaces;

public interface ILogger
{
    void Log(string message);
}

public interface IDetailedLogger
{
    void Log(string message, string level);
}
// garbage_marker_12345
""",
            "Services/ConsoleLogger.cs": """namespace MyApp.Services;

public class ConsoleLogger { }
""",
        },
        changed_files={
            "Services/ConsoleLogger.cs": """using MyApp.Interfaces;

namespace MyApp.Services;

public class ConsoleLogger : ILogger, IDetailedLogger
{
    void ILogger.Log(string message)
    {
        Console.WriteLine(message);
    }

    void IDetailedLogger.Log(string message, string level)
    {
        Console.WriteLine($"[{level}] {message}");
    }
}
""",
        },
        must_include=["ConsoleLogger", "ILogger", "IDetailedLogger"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add explicit interface implementation",
    ),
    DiffTestCase(
        name="csharp_288_default_interface",
        initial_files={
            "Interfaces/IProcessor.cs": """namespace MyApp.Interfaces;

public interface IProcessor
{
    void Process(string data);

    void ProcessBatch(string[] items)
    {
        foreach (var item in items)
        {
            Process(item);
        }
    }
}
// unused_marker_67890
""",
            "Services/DataProcessor.cs": """namespace MyApp.Services;

public class DataProcessor { }
""",
        },
        changed_files={
            "Services/DataProcessor.cs": """using MyApp.Interfaces;

namespace MyApp.Services;

public class DataProcessor : IProcessor
{
    public void Process(string data)
    {
        Console.WriteLine($"Processing: {data}");
    }

    public void Run(string[] items)
    {
        IProcessor processor = this;
        processor.ProcessBatch(items);
    }
}
""",
        },
        must_include=["DataProcessor", "IProcessor", "ProcessBatch"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add default interface method usage",
    ),
]


CSHARP_GENERICS_CASES = [
    DiffTestCase(
        name="csharp_289_generic_class",
        initial_files={
            "Collections/Cache.cs": """namespace MyApp.Collections;

public class Cache<TKey, TValue> where TKey : notnull
{
    private readonly Dictionary<TKey, TValue> _cache = new();

    public void Set(TKey key, TValue value) => _cache[key] = value;

    public TValue? Get(TKey key) =>
        _cache.TryGetValue(key, out var value) ? value : default;

    public bool Contains(TKey key) => _cache.ContainsKey(key);
}
// garbage_marker_12345
""",
            "Services/CacheService.cs": """namespace MyApp.Services;

public class CacheService { }
""",
        },
        changed_files={
            "Services/CacheService.cs": """using MyApp.Collections;
using MyApp.Models;

namespace MyApp.Services;

public class CacheService
{
    private readonly Cache<string, User> _userCache = new();

    public void CacheUser(string key, User user)
    {
        _userCache.Set(key, user);
    }

    public User? GetCachedUser(string key)
    {
        return _userCache.Get(key);
    }
}
""",
        },
        must_include=["CacheService", "Cache"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add generic class usage",
    ),
    DiffTestCase(
        name="csharp_290_generic_constraints",
        initial_files={
            "Services/Factory.cs": """namespace MyApp.Services;

public class Factory
{
    public static T Create<T>() where T : class, new()
    {
        return new T();
    }

    public static T CreateWithInit<T>(Action<T> initializer) where T : class, new()
    {
        var instance = new T();
        initializer(instance);
        return instance;
    }
}
// unused_marker_67890
""",
            "Program.cs": """using System;

class Program
{
    static void Main() { }
}
""",
        },
        changed_files={
            "Program.cs": """using System;
using MyApp.Services;
using MyApp.Models;

class Program
{
    static void Main()
    {
        var user = Factory.Create<User>();
        var initializedUser = Factory.CreateWithInit<User>(u => u.Name = "John");
    }
}
""",
        },
        must_include=["Factory", "Create"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add generic constraints usage",
    ),
    DiffTestCase(
        name="csharp_291_generic_method",
        initial_files={
            "Services/Serializer.cs": """using System.Text.Json;

namespace MyApp.Services;

public static class Serializer
{
    public static string ToJson<T>(T obj)
    {
        return JsonSerializer.Serialize(obj);
    }

    public static T? FromJson<T>(string json)
    {
        return JsonSerializer.Deserialize<T>(json);
    }
}
// garbage_marker_12345
""",
            "Program.cs": """using System;

class Program
{
    static void Main() { }
}
""",
        },
        changed_files={
            "Program.cs": """using System;
using MyApp.Services;
using MyApp.Models;

class Program
{
    static void Main()
    {
        var user = new User { Id = 1, Name = "John" };
        var json = Serializer.ToJson(user);
        var restored = Serializer.FromJson<User>(json);
    }
}
""",
        },
        must_include=["Serializer", "ToJson", "FromJson"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add generic method usage",
    ),
]


CSHARP_LINQ_CASES = [
    DiffTestCase(
        name="csharp_292_linq_query",
        initial_files={
            "Models/Product.cs": """namespace MyApp.Models;

public class Product
{
    public int Id { get; set; }
    public string Name { get; set; }
    public decimal Price { get; set; }
    public string Category { get; set; }
}
// unused_marker_67890
""",
            "Services/ProductService.cs": """namespace MyApp.Services;

public class ProductService { }
""",
        },
        changed_files={
            "Services/ProductService.cs": """using MyApp.Models;

namespace MyApp.Services;

public class ProductService
{
    private readonly List<Product> _products = new();

    public IEnumerable<Product> GetExpensiveProducts(decimal minPrice)
    {
        return from p in _products
               where p.Price >= minPrice
               orderby p.Price descending
               select p;
    }

    public IEnumerable<IGrouping<string, Product>> GroupByCategory()
    {
        return from p in _products
               group p by p.Category;
    }
}
""",
        },
        must_include=["ProductService", "GetExpensiveProducts", "Product"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add LINQ query syntax",
    ),
    DiffTestCase(
        name="csharp_293_linq_method",
        initial_files={
            "Models/Order.cs": """namespace MyApp.Models;

public class Order
{
    public int Id { get; set; }
    public int CustomerId { get; set; }
    public decimal Total { get; set; }
    public DateTime Date { get; set; }
}
// garbage_marker_12345
""",
            "Services/OrderService.cs": """namespace MyApp.Services;

public class OrderService { }
""",
        },
        changed_files={
            "Services/OrderService.cs": """using MyApp.Models;

namespace MyApp.Services;

public class OrderService
{
    private readonly List<Order> _orders = new();

    public IEnumerable<Order> GetRecentOrders(int days)
    {
        return _orders
            .Where(o => o.Date >= DateTime.Now.AddDays(-days))
            .OrderByDescending(o => o.Date)
            .Take(10);
    }

    public decimal GetTotalRevenue()
    {
        return _orders.Sum(o => o.Total);
    }

    public Dictionary<int, decimal> GetCustomerTotals()
    {
        return _orders
            .GroupBy(o => o.CustomerId)
            .ToDictionary(g => g.Key, g => g.Sum(o => o.Total));
    }
}
""",
        },
        must_include=["OrderService", "GetRecentOrders", "Order"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add LINQ method syntax",
    ),
]


CSHARP_DELEGATE_CASES = [
    DiffTestCase(
        name="csharp_294_delegate_event",
        initial_files={
            "Events/OrderEventArgs.cs": """namespace MyApp.Events;

public class OrderEventArgs : EventArgs
{
    public int OrderId { get; }
    public string Status { get; }

    public OrderEventArgs(int orderId, string status)
    {
        OrderId = orderId;
        Status = status;
    }
}
// unused_marker_67890
""",
            "Services/OrderProcessor.cs": """namespace MyApp.Services;

public class OrderProcessor { }
""",
        },
        changed_files={
            "Services/OrderProcessor.cs": """using MyApp.Events;

namespace MyApp.Services;

public class OrderProcessor
{
    public event EventHandler<OrderEventArgs>? OrderProcessed;

    public void ProcessOrder(int orderId)
    {
        // Process order...
        OnOrderProcessed(new OrderEventArgs(orderId, "Completed"));
    }

    protected virtual void OnOrderProcessed(OrderEventArgs e)
    {
        OrderProcessed?.Invoke(this, e);
    }
}
""",
        },
        must_include=["OrderProcessor", "OrderEventArgs", "OrderProcessed"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add delegate event usage",
    ),
    DiffTestCase(
        name="csharp_295_func_action",
        initial_files={
            "Services/Pipeline.cs": """namespace MyApp.Services;

public class Pipeline<T>
{
    private readonly List<Func<T, T>> _steps = new();

    public Pipeline<T> AddStep(Func<T, T> step)
    {
        _steps.Add(step);
        return this;
    }

    public T Execute(T input)
    {
        return _steps.Aggregate(input, (current, step) => step(current));
    }
}
// garbage_marker_12345
""",
            "Program.cs": """using System;

class Program
{
    static void Main() { }
}
""",
        },
        changed_files={
            "Program.cs": """using System;
using MyApp.Services;

class Program
{
    static void Main()
    {
        var pipeline = new Pipeline<string>()
            .AddStep(s => s.Trim())
            .AddStep(s => s.ToUpper())
            .AddStep(s => $"[{s}]");

        var result = pipeline.Execute("  hello world  ");
        Console.WriteLine(result);
    }
}
""",
        },
        must_include=["Pipeline", "AddStep", "Execute"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add Func/Action usage",
    ),
    DiffTestCase(
        name="csharp_296_lambda_expression",
        initial_files={
            "Services/Validator.cs": """namespace MyApp.Services;

public class Validator<T>
{
    private readonly List<Func<T, bool>> _rules = new();

    public Validator<T> AddRule(Func<T, bool> rule)
    {
        _rules.Add(rule);
        return this;
    }

    public bool Validate(T item)
    {
        return _rules.All(rule => rule(item));
    }
}
// unused_marker_67890
""",
            "Program.cs": """using System;

class Program
{
    static void Main() { }
}
""",
        },
        changed_files={
            "Program.cs": """using System;
using MyApp.Services;
using MyApp.Models;

class Program
{
    static void Main()
    {
        var validator = new Validator<User>()
            .AddRule(u => !string.IsNullOrEmpty(u.Name))
            .AddRule(u => u.Id > 0)
            .AddRule(u => u.Name.Length <= 100);

        var user = new User { Id = 1, Name = "John" };
        var isValid = validator.Validate(user);
    }
}
""",
        },
        must_include=["Validator", "AddRule", "Validate"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add lambda expression usage",
    ),
]


CSHARP_ATTRIBUTE_CASES = [
    DiffTestCase(
        name="csharp_297_custom_attribute",
        initial_files={
            "Attributes/ValidateAttribute.cs": """namespace MyApp.Attributes;

[AttributeUsage(AttributeTargets.Property)]
public class ValidateAttribute : Attribute
{
    public bool Required { get; set; }
    public int MaxLength { get; set; } = int.MaxValue;
    public int MinLength { get; set; } = 0;
}
// garbage_marker_12345
""",
            "Models/Customer.cs": """namespace MyApp.Models;

public class Customer { }
""",
        },
        changed_files={
            "Models/Customer.cs": """using MyApp.Attributes;

namespace MyApp.Models;

public class Customer
{
    public int Id { get; set; }

    [Validate(Required = true, MaxLength = 100)]
    public string Name { get; set; }

    [Validate(Required = true, MinLength = 5)]
    public string Email { get; set; }
}
""",
        },
        must_include=["Customer", "ValidateAttribute", "Validate"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add custom attribute usage",
    ),
    DiffTestCase(
        name="csharp_298_reflection_attribute",
        initial_files={
            "Attributes/RouteAttribute.cs": """namespace MyApp.Attributes;

[AttributeUsage(AttributeTargets.Method)]
public class RouteAttribute : Attribute
{
    public string Path { get; }

    public RouteAttribute(string path)
    {
        Path = path;
    }
}
// unused_marker_67890
""",
            "Services/Router.cs": """namespace MyApp.Services;

public class Router { }
""",
        },
        changed_files={
            "Services/Router.cs": """using System.Reflection;
using MyApp.Attributes;

namespace MyApp.Services;

public class Router
{
    public Dictionary<string, MethodInfo> BuildRoutes(Type controllerType)
    {
        var routes = new Dictionary<string, MethodInfo>();

        foreach (var method in controllerType.GetMethods())
        {
            var attr = method.GetCustomAttribute<RouteAttribute>();
            if (attr != null)
            {
                routes[attr.Path] = method;
            }
        }

        return routes;
    }
}
""",
        },
        must_include=["Router", "BuildRoutes", "RouteAttribute"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add reflection attribute usage",
    ),
]


CSHARP_EXTENSION_CASES = [
    DiffTestCase(
        name="csharp_299_extension_method",
        initial_files={
            "Extensions/StringExtensions.cs": """namespace MyApp.Extensions;

public static class StringExtensions
{
    public static bool IsNullOrWhiteSpace(this string? value)
    {
        return string.IsNullOrWhiteSpace(value);
    }

    public static string Truncate(this string value, int maxLength)
    {
        return value.Length <= maxLength ? value : value.Substring(0, maxLength) + "...";
    }

    public static string ToSlug(this string value)
    {
        return value.ToLower().Replace(" ", "-");
    }
}
// garbage_marker_12345
""",
            "Program.cs": """using System;

class Program
{
    static void Main() { }
}
""",
        },
        changed_files={
            "Program.cs": """using System;
using MyApp.Extensions;

class Program
{
    static void Main()
    {
        string title = "Hello World From CSharp";
        var slug = title.ToSlug();
        var truncated = title.Truncate(10);
        Console.WriteLine($"{slug} - {truncated}");
    }
}
""",
        },
        must_include=["StringExtensions", "ToSlug", "Truncate"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add extension method usage",
    ),
    DiffTestCase(
        name="csharp_300_enumerable_extension",
        initial_files={
            "Extensions/EnumerableExtensions.cs": """namespace MyApp.Extensions;

public static class EnumerableExtensions
{
    public static IEnumerable<T> WhereNotNull<T>(this IEnumerable<T?> source) where T : class
    {
        return source.Where(x => x != null)!;
    }

    public static IEnumerable<IEnumerable<T>> Batch<T>(this IEnumerable<T> source, int size)
    {
        var batch = new List<T>(size);
        foreach (var item in source)
        {
            batch.Add(item);
            if (batch.Count == size)
            {
                yield return batch;
                batch = new List<T>(size);
            }
        }
        if (batch.Count > 0)
            yield return batch;
    }
}
// unused_marker_67890
""",
            "Services/BatchProcessor.cs": """namespace MyApp.Services;

public class BatchProcessor { }
""",
        },
        changed_files={
            "Services/BatchProcessor.cs": """using MyApp.Extensions;
using MyApp.Models;

namespace MyApp.Services;

public class BatchProcessor
{
    public void ProcessUsers(IEnumerable<User?> users)
    {
        var validUsers = users.WhereNotNull();

        foreach (var batch in validUsers.Batch(100))
        {
            ProcessBatch(batch);
        }
    }

    private void ProcessBatch(IEnumerable<User> batch)
    {
        foreach (var user in batch)
        {
            Console.WriteLine(user.Name);
        }
    }
}
""",
        },
        must_include=["BatchProcessor", "EnumerableExtensions", "WhereNotNull", "Batch"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add enumerable extension usage",
    ),
]


CSHARP_RECORD_CASES = [
    DiffTestCase(
        name="csharp_301_record_type",
        initial_files={
            "Models/PersonRecord.cs": """namespace MyApp.Models;

public record Person(string FirstName, string LastName, int Age)
{
    public string FullName => $"{FirstName} {LastName}";
}

public record Address(string Street, string City, string Country);
// garbage_marker_12345
""",
            "Services/PersonService.cs": """namespace MyApp.Services;

public class PersonService { }
""",
        },
        changed_files={
            "Services/PersonService.cs": """using MyApp.Models;

namespace MyApp.Services;

public class PersonService
{
    public Person CreatePerson(string first, string last, int age)
    {
        return new Person(first, last, age);
    }

    public Person UpdateAge(Person person, int newAge)
    {
        return person with { Age = newAge };
    }

    public bool AreEqual(Person p1, Person p2)
    {
        return p1 == p2;
    }
}
""",
        },
        must_include=["PersonService", "Person", "CreatePerson"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add record type usage",
    ),
]


CSHARP_PATTERN_CASES = [
    DiffTestCase(
        name="csharp_302_pattern_matching",
        initial_files={
            "Models/Shape.cs": """namespace MyApp.Models;

public abstract class Shape { }

public class Circle : Shape
{
    public double Radius { get; set; }
}

public class Rectangle : Shape
{
    public double Width { get; set; }
    public double Height { get; set; }
}

public class Triangle : Shape
{
    public double Base { get; set; }
    public double Height { get; set; }
}
// unused_marker_67890
""",
            "Services/AreaCalculator.cs": """namespace MyApp.Services;

public class AreaCalculator { }
""",
        },
        changed_files={
            "Services/AreaCalculator.cs": """using MyApp.Models;

namespace MyApp.Services;

public class AreaCalculator
{
    public double Calculate(Shape shape)
    {
        return shape switch
        {
            Circle c => Math.PI * c.Radius * c.Radius,
            Rectangle r => r.Width * r.Height,
            Triangle t => 0.5 * t.Base * t.Height,
            _ => throw new ArgumentException("Unknown shape")
        };
    }
}
""",
        },
        must_include=["AreaCalculator", "Calculate", "Circle", "Rectangle", "Triangle"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add pattern matching usage",
    ),
    DiffTestCase(
        name="csharp_303_property_pattern",
        initial_files={
            "Models/Request.cs": """namespace MyApp.Models;

public class Request
{
    public string Method { get; set; }
    public string Path { get; set; }
    public bool IsAuthenticated { get; set; }
    public string? UserId { get; set; }
}
// garbage_marker_12345
""",
            "Services/RequestHandler.cs": """namespace MyApp.Services;

public class RequestHandler { }
""",
        },
        changed_files={
            "Services/RequestHandler.cs": """using MyApp.Models;

namespace MyApp.Services;

public class RequestHandler
{
    public string Route(Request request)
    {
        return request switch
        {
            { Method: "GET", Path: "/" } => "Home",
            { Method: "GET", Path: "/api", IsAuthenticated: true } => "API",
            { Method: "POST", IsAuthenticated: true, UserId: not null } => "Authorized Post",
            { IsAuthenticated: false } => "Unauthorized",
            _ => "Not Found"
        };
    }
}
""",
        },
        must_include=["RequestHandler", "Route", "Request"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add property pattern usage",
    ),
]


CSHARP_NULLABLE_CASES = [
    DiffTestCase(
        name="csharp_304_nullable_reference",
        initial_files={
            "Models/Configuration.cs": """namespace MyApp.Models;

public class Configuration
{
    public string? ConnectionString { get; set; }
    public int? Port { get; set; }
    public string Environment { get; set; } = "Development";
}
// unused_marker_67890
""",
            "Services/ConfigService.cs": """namespace MyApp.Services;

public class ConfigService { }
""",
        },
        changed_files={
            "Services/ConfigService.cs": """using MyApp.Models;

namespace MyApp.Services;

public class ConfigService
{
    private readonly Configuration _config;

    public ConfigService(Configuration config)
    {
        _config = config;
    }

    public string GetConnectionString()
    {
        return _config.ConnectionString
            ?? throw new InvalidOperationException("Connection string not configured");
    }

    public int GetPort()
    {
        return _config.Port ?? 8080;
    }
}
""",
        },
        must_include=["ConfigService", "Configuration", "GetConnectionString"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add nullable reference usage",
    ),
]


CSHARP_DISPOSE_CASES = [
    DiffTestCase(
        name="csharp_305_idisposable",
        initial_files={
            "Resources/FileResource.cs": """namespace MyApp.Resources;

public class FileResource : IDisposable
{
    private readonly StreamWriter _writer;
    private bool _disposed;

    public FileResource(string path)
    {
        _writer = new StreamWriter(path);
    }

    public void Write(string content)
    {
        ObjectDisposedException.ThrowIf(_disposed, this);
        _writer.Write(content);
    }

    public void Dispose()
    {
        if (!_disposed)
        {
            _writer.Dispose();
            _disposed = true;
        }
    }
}
// garbage_marker_12345
""",
            "Services/FileService.cs": """namespace MyApp.Services;

public class FileService { }
""",
        },
        changed_files={
            "Services/FileService.cs": """using MyApp.Resources;

namespace MyApp.Services;

public class FileService
{
    public void WriteToFile(string path, string content)
    {
        using var resource = new FileResource(path);
        resource.Write(content);
    }

    public void WriteMultiple(string path, string[] lines)
    {
        using (var resource = new FileResource(path))
        {
            foreach (var line in lines)
            {
                resource.Write(line);
            }
        }
    }
}
""",
        },
        must_include=["FileService", "FileResource", "WriteToFile"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add IDisposable usage",
    ),
    DiffTestCase(
        name="csharp_306_async_disposable",
        initial_files={
            "Resources/AsyncResource.cs": """namespace MyApp.Resources;

public class AsyncResource : IAsyncDisposable
{
    private readonly HttpClient _client;

    public AsyncResource()
    {
        _client = new HttpClient();
    }

    public async Task<string> FetchAsync(string url)
    {
        return await _client.GetStringAsync(url);
    }

    public async ValueTask DisposeAsync()
    {
        _client.Dispose();
        await Task.CompletedTask;
    }
}
// unused_marker_67890
""",
            "Services/AsyncService.cs": """namespace MyApp.Services;

public class AsyncService { }
""",
        },
        changed_files={
            "Services/AsyncService.cs": """using MyApp.Resources;

namespace MyApp.Services;

public class AsyncService
{
    public async Task<string> FetchDataAsync(string url)
    {
        await using var resource = new AsyncResource();
        return await resource.FetchAsync(url);
    }
}
""",
        },
        must_include=["AsyncService", "AsyncResource", "FetchDataAsync"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add IAsyncDisposable usage",
    ),
]


ALL_CSHARP_CASES = (
    CSHARP_NAMESPACE_CASES
    + CSHARP_ASYNC_CASES
    + CSHARP_INTERFACE_CASES
    + CSHARP_GENERICS_CASES
    + CSHARP_LINQ_CASES
    + CSHARP_DELEGATE_CASES
    + CSHARP_ATTRIBUTE_CASES
    + CSHARP_EXTENSION_CASES
    + CSHARP_RECORD_CASES
    + CSHARP_PATTERN_CASES
    + CSHARP_NULLABLE_CASES
    + CSHARP_DISPOSE_CASES
)


@pytest.fixture
def diff_test_runner(tmp_path):
    return DiffTestRunner(tmp_path)


@pytest.mark.parametrize("case", ALL_CSHARP_CASES, ids=lambda c: c.name)
def test_csharp_diff_context(diff_test_runner: DiffTestRunner, case: DiffTestCase):
    context = diff_test_runner.run_test_case(case)
    diff_test_runner.verify_assertions(context, case)
