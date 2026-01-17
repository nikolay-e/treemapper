import pytest

from tests.utils import DiffTestCase, DiffTestRunner

CPP_MEMORY_CASES = [
    DiffTestCase(
        name="cpp_241_function_pointer",
        initial_files={
            "handlers.h": """#pragma once
void onSuccess(int code);
void onError(int code);
// garbage_marker_12345 - this should not appear in context
""",
            "handlers.cpp": """#include "handlers.h"
#include <iostream>

void onSuccess(int code) {
    std::cout << "Success: " << code << std::endl;
}

void onError(int code) {
    std::cerr << "Error: " << code << std::endl;
}
""",
            "main.cpp": """#include <iostream>
int main() { return 0; }
""",
        },
        changed_files={
            "main.cpp": """#include "handlers.h"

void execute(void (*callback)(int), int value) {
    callback(value);
}

int main() {
    void (*handler)(int) = onSuccess;
    execute(handler, 200);
    return 0;
}
""",
        },
        must_include=["execute", "handler", "onSuccess"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add function pointer usage",
    ),
    DiffTestCase(
        name="cpp_242_pointer_arithmetic",
        initial_files={
            "string_utils.h": """#pragma once
#include <cstring>

inline size_t safe_strlen(const char* str) {
    if (!str) return 0;
    return strlen(str);
}
// unused_marker_67890 - not relevant
""",
            "parser.cpp": """#include <iostream>
int main() { return 0; }
""",
        },
        changed_files={
            "parser.cpp": """#include "string_utils.h"

void parse(const char* str) {
    size_t len = safe_strlen(str);
    char* end = const_cast<char*>(str) + len;
    while (str < end) {
        str++;
    }
}
""",
        },
        must_include=["parse", "safe_strlen"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add pointer arithmetic",
    ),
    DiffTestCase(
        name="cpp_243_malloc_free",
        initial_files={
            "memory.h": """#pragma once
#include <cstdlib>
#include <cstddef>

inline void* safe_malloc(size_t size) {
    void* ptr = malloc(size);
    if (!ptr && size > 0) {
        abort();
    }
    return ptr;
}
// garbage_marker_12345 - irrelevant content
""",
            "array.c": """#include <stdio.h>
int main() { return 0; }
""",
        },
        changed_files={
            "array.c": """#include "memory.h"

int* create_array(size_t n) {
    int* arr = (int*)safe_malloc(n * sizeof(int));
    for (size_t i = 0; i < n; i++) {
        arr[i] = 0;
    }
    return arr;
}

void destroy_array(int* arr) {
    free(arr);
}
""",
        },
        must_include=["create_array", "safe_malloc"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add malloc/free",
    ),
    DiffTestCase(
        name="cpp_244_new_delete",
        initial_files={
            "user.h": """#pragma once
#include <string>

class User {
public:
    std::string name;
    User(const std::string& n) : name(n) {}
    ~User() {}
};
// unused_marker_67890
""",
            "main.cpp": """int main() { return 0; }
""",
        },
        changed_files={
            "main.cpp": """#include "user.h"

User* createUser(const std::string& name) {
    User* user = new User(name);
    return user;
}

void deleteUser(User* user) {
    delete user;
}

int main() {
    User* u = createUser("John");
    deleteUser(u);
    return 0;
}
""",
        },
        must_include=["createUser", "deleteUser", "User"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add new/delete",
    ),
    DiffTestCase(
        name="cpp_245_unique_ptr",
        initial_files={
            "resource.h": """#pragma once
#include <string>

class Resource {
public:
    std::string id;
    Resource(const std::string& id) : id(id) {}
    void use() {}
};
// garbage_marker_12345
""",
            "manager.cpp": """#include <iostream>
int main() { return 0; }
""",
        },
        changed_files={
            "manager.cpp": """#include "resource.h"
#include <memory>

class ResourceManager {
public:
    std::unique_ptr<Resource> acquire(const std::string& id) {
        return std::make_unique<Resource>(id);
    }

    void process() {
        auto res = acquire("resource-1");
        res->use();
    }
};
""",
        },
        must_include=["ResourceManager", "acquire", "unique_ptr"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add unique_ptr usage",
    ),
    DiffTestCase(
        name="cpp_246_shared_ptr",
        initial_files={
            "data.h": """#pragma once

struct Data {
    int value;
    Data(int v) : value(v) {}
};
// unused_marker_67890
""",
            "cache.cpp": """#include <iostream>
int main() { return 0; }
""",
        },
        changed_files={
            "cache.cpp": """#include "data.h"
#include <memory>
#include <unordered_map>
#include <string>

class Cache {
    std::unordered_map<std::string, std::shared_ptr<Data>> store;

public:
    std::shared_ptr<Data> get(const std::string& key) {
        if (store.count(key)) {
            return store[key];
        }
        auto data = std::make_shared<Data>(0);
        store[key] = data;
        return data;
    }
};
""",
        },
        must_include=["Cache", "shared_ptr", "Data"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add shared_ptr usage",
    ),
    DiffTestCase(
        name="cpp_247_weak_ptr",
        initial_files={
            "node.h": """#pragma once
#include <memory>
#include <vector>

class Node {
public:
    int value;
    std::weak_ptr<Node> parent;
    std::vector<std::shared_ptr<Node>> children;

    Node(int v) : value(v) {}
};
// garbage_marker_12345
""",
            "tree.cpp": """#include <iostream>
int main() { return 0; }
""",
        },
        changed_files={
            "tree.cpp": """#include "node.h"

class Tree {
    std::shared_ptr<Node> root;

public:
    void addChild(std::shared_ptr<Node> parent, int value) {
        auto child = std::make_shared<Node>(value);
        child->parent = parent;
        parent->children.push_back(child);
    }

    std::shared_ptr<Node> getParent(std::shared_ptr<Node> node) {
        return node->parent.lock();
    }
};
""",
        },
        must_include=["Tree", "addChild", "getParent", "weak_ptr"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add weak_ptr usage",
    ),
    DiffTestCase(
        name="cpp_248_move_semantics",
        initial_files={
            "buffer.h": """#pragma once
#include <cstddef>
#include <utility>

class Buffer {
    char* data_;
    size_t size_;

public:
    Buffer(size_t size) : data_(new char[size]), size_(size) {}
    ~Buffer() { delete[] data_; }

    Buffer(Buffer&& other) noexcept
        : data_(other.data_), size_(other.size_) {
        other.data_ = nullptr;
        other.size_ = 0;
    }

    Buffer& operator=(Buffer&& other) noexcept {
        if (this != &other) {
            delete[] data_;
            data_ = other.data_;
            size_ = other.size_;
            other.data_ = nullptr;
            other.size_ = 0;
        }
        return *this;
    }

    Buffer(const Buffer&) = delete;
    Buffer& operator=(const Buffer&) = delete;
};
// unused_marker_67890
""",
            "processor.cpp": """#include <iostream>
int main() { return 0; }
""",
        },
        changed_files={
            "processor.cpp": """#include "buffer.h"
#include <utility>

Buffer createBuffer(size_t size) {
    Buffer buf(size);
    return buf;
}

void processBuffer(Buffer buf) {
    // Process buffer
}

int main() {
    Buffer b = createBuffer(1024);
    processBuffer(std::move(b));
    return 0;
}
""",
        },
        must_include=["createBuffer", "processBuffer", "move"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add move semantics",
    ),
    DiffTestCase(
        name="cpp_249_raii",
        initial_files={
            "mutex.h": """#pragma once

class Mutex {
public:
    void lock() {}
    void unlock() {}
};
// garbage_marker_12345
""",
            "guard.cpp": """#include <iostream>
int main() { return 0; }
""",
        },
        changed_files={
            "guard.cpp": """#include "mutex.h"

class LockGuard {
    Mutex& mutex_;

public:
    explicit LockGuard(Mutex& m) : mutex_(m) {
        mutex_.lock();
    }

    ~LockGuard() {
        mutex_.unlock();
    }

    LockGuard(const LockGuard&) = delete;
    LockGuard& operator=(const LockGuard&) = delete;
};

void criticalSection(Mutex& m) {
    LockGuard guard(m);
    // Protected code
}
""",
        },
        must_include=["LockGuard", "criticalSection", "Mutex"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add RAII pattern",
    ),
    DiffTestCase(
        name="cpp_250_placement_new",
        initial_files={
            "object.h": """#pragma once
#include <string>

class Object {
public:
    std::string name;
    Object(const std::string& n) : name(n) {}
    ~Object() {}
};
// unused_marker_67890
""",
            "pool.cpp": """#include <iostream>
int main() { return 0; }
""",
        },
        changed_files={
            "pool.cpp": """#include "object.h"
#include <new>
#include <cstdlib>
#include <cstdint>

class ObjectPool {
    alignas(Object) char buffer[sizeof(Object) * 10];
    size_t used = 0;

public:
    Object* allocate(const std::string& name) {
        if (used >= 10) return nullptr;
        void* ptr = buffer + sizeof(Object) * used;
        Object* obj = new (ptr) Object(name);
        used++;
        return obj;
    }

    void deallocate(Object* obj) {
        obj->~Object();
    }
};
""",
        },
        must_include=["ObjectPool", "allocate", "Object"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add placement new",
    ),
]


CPP_CAST_CASES = [
    DiffTestCase(
        name="cpp_251_reinterpret_cast",
        initial_files={
            "packet.h": """#pragma once
#include <cstdint>

struct Packet {
    uint32_t type;
    uint32_t length;
    char data[256];
};
// garbage_marker_12345
""",
            "serializer.cpp": """#include <iostream>
int main() { return 0; }
""",
        },
        changed_files={
            "serializer.cpp": """#include "packet.h"
#include <cstring>

void serialize(const Packet& pkt, char* buffer) {
    auto* bytes = reinterpret_cast<const char*>(&pkt);
    std::memcpy(buffer, bytes, sizeof(Packet));
}

Packet deserialize(const char* buffer) {
    Packet pkt;
    auto* bytes = reinterpret_cast<char*>(&pkt);
    std::memcpy(bytes, buffer, sizeof(Packet));
    return pkt;
}
""",
        },
        must_include=["serialize", "deserialize", "reinterpret_cast"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add reinterpret_cast",
    ),
    DiffTestCase(
        name="cpp_252_static_cast",
        initial_files={
            "hierarchy.h": """#pragma once

class Base {
public:
    virtual ~Base() = default;
    virtual void process() {}
};

class Derived : public Base {
public:
    void process() override {}
    void special() {}
};
// unused_marker_67890
""",
            "handler.cpp": """#include <iostream>
int main() { return 0; }
""",
        },
        changed_files={
            "handler.cpp": """#include "hierarchy.h"

void handleDerived(Base* base) {
    auto* derived = static_cast<Derived*>(base);
    derived->special();
}

int main() {
    Derived d;
    handleDerived(&d);
    return 0;
}
""",
        },
        must_include=["handleDerived", "static_cast", "Derived"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add static_cast",
    ),
    DiffTestCase(
        name="cpp_253_dynamic_cast",
        initial_files={
            "shapes.h": """#pragma once

class Shape {
public:
    virtual ~Shape() = default;
    virtual void draw() = 0;
};

class Circle : public Shape {
public:
    void draw() override {}
    double radius() { return 1.0; }
};

class Rectangle : public Shape {
public:
    void draw() override {}
    double width() { return 1.0; }
};
// garbage_marker_12345
""",
            "renderer.cpp": """#include <iostream>
int main() { return 0; }
""",
        },
        changed_files={
            "renderer.cpp": """#include "shapes.h"
#include <iostream>

void render(Shape* shape) {
    if (auto* circle = dynamic_cast<Circle*>(shape)) {
        std::cout << "Circle radius: " << circle->radius() << std::endl;
    } else if (auto* rect = dynamic_cast<Rectangle*>(shape)) {
        std::cout << "Rectangle width: " << rect->width() << std::endl;
    }
}
""",
        },
        must_include=["render", "dynamic_cast", "Circle", "Rectangle"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add dynamic_cast",
    ),
    DiffTestCase(
        name="cpp_254_const_cast",
        initial_files={
            "legacy.h": """#pragma once

void legacyModify(char* str);
// unused_marker_67890
""",
            "legacy.cpp": """#include "legacy.h"

void legacyModify(char* str) {
    // Old API that doesn't modify but isn't const-correct
}
""",
            "adapter.cpp": """#include <iostream>
int main() { return 0; }
""",
        },
        changed_files={
            "adapter.cpp": """#include "legacy.h"

void process(const char* str) {
    legacyModify(const_cast<char*>(str));
}
""",
        },
        must_include=["process", "const_cast", "legacyModify"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add const_cast",
    ),
]


CPP_LOWLEVEL_CASES = [
    DiffTestCase(
        name="cpp_255_volatile",
        initial_files={
            "hardware.h": """#pragma once
#include <cstdint>

struct HardwareRegister {
    volatile uint32_t status;
    volatile uint32_t control;
    volatile uint32_t data;
};
// garbage_marker_12345
""",
            "driver.cpp": """#include <iostream>
int main() { return 0; }
""",
        },
        changed_files={
            "driver.cpp": """#include "hardware.h"

class Driver {
    HardwareRegister* reg;

public:
    Driver(HardwareRegister* r) : reg(r) {}

    void waitReady() {
        while (!(reg->status & 0x1)) {
            // Busy wait - volatile prevents optimization
        }
    }

    void write(uint32_t value) {
        reg->data = value;
        reg->control = 0x1;
    }
};
""",
        },
        must_include=["Driver", "waitReady", "HardwareRegister"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add volatile usage",
    ),
    DiffTestCase(
        name="cpp_256_bit_manipulation",
        initial_files={
            "flags.h": """#pragma once
#include <cstdint>

constexpr uint32_t FLAG_ENABLED = 0;
constexpr uint32_t FLAG_VISIBLE = 1;
constexpr uint32_t FLAG_ACTIVE = 2;
// unused_marker_67890
""",
            "state.cpp": """#include <iostream>
int main() { return 0; }
""",
        },
        changed_files={
            "state.cpp": """#include "flags.h"

class State {
    uint32_t flags = 0;

public:
    void enable() { flags |= (1 << FLAG_ENABLED); }
    void disable() { flags &= ~(1 << FLAG_ENABLED); }
    bool isEnabled() const { return flags & (1 << FLAG_ENABLED); }

    void setVisible(bool v) {
        if (v) flags |= (1 << FLAG_VISIBLE);
        else flags &= ~(1 << FLAG_VISIBLE);
    }
};
""",
        },
        must_include=["State", "enable", "FLAG_ENABLED"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add bit manipulation",
    ),
    DiffTestCase(
        name="cpp_257_union",
        initial_files={
            "types.h": """#pragma once
#include <cstdint>

enum class ValueType { INT, FLOAT, STRING };
// garbage_marker_12345
""",
            "variant.cpp": """#include <iostream>
int main() { return 0; }
""",
        },
        changed_files={
            "variant.cpp": """#include "types.h"
#include <string>
#include <cstring>

union Value {
    int32_t i;
    float f;
    char s[32];
};

struct Variant {
    ValueType type;
    Value value;

    int32_t asInt() const {
        if (type == ValueType::INT) return value.i;
        return 0;
    }

    float asFloat() const {
        if (type == ValueType::FLOAT) return value.f;
        return 0.0f;
    }
};
""",
        },
        must_include=["Variant", "Value", "ValueType"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add union usage",
    ),
    DiffTestCase(
        name="cpp_258_struct_packing",
        initial_files={
            "protocol.h": """#pragma once
#include <cstdint>

#pragma pack(push, 1)
struct PacketHeader {
    uint8_t version;
    uint8_t type;
    uint16_t length;
    uint32_t sequence;
};
#pragma pack(pop)
// unused_marker_67890
""",
            "network.cpp": """#include <iostream>
int main() { return 0; }
""",
        },
        changed_files={
            "network.cpp": """#include "protocol.h"
#include <cstring>

void sendPacket(const void* data, size_t len) {
    PacketHeader header;
    header.version = 1;
    header.type = 0;
    header.length = static_cast<uint16_t>(len);
    header.sequence = 0;

    char buffer[sizeof(PacketHeader) + 1024];
    std::memcpy(buffer, &header, sizeof(header));
    std::memcpy(buffer + sizeof(header), data, len);
}
""",
        },
        must_include=["sendPacket", "PacketHeader"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add struct packing",
    ),
    DiffTestCase(
        name="cpp_259_memory_alignment",
        initial_files={
            "simd.h": """#pragma once

void multiplyVectors(const float* a, const float* b, float* result, int n);
// garbage_marker_12345
""",
            "compute.cpp": """#include <iostream>
int main() { return 0; }
""",
        },
        changed_files={
            "compute.cpp": """#include "simd.h"

class AlignedBuffer {
    alignas(16) float data[4];

public:
    float* get() { return data; }

    void process(const float* input) {
        for (int i = 0; i < 4; i++) {
            data[i] = input[i] * 2.0f;
        }
    }
};

void compute() {
    AlignedBuffer a, b, result;
    multiplyVectors(a.get(), b.get(), result.get(), 4);
}
""",
        },
        must_include=["AlignedBuffer", "compute", "alignas"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add memory alignment",
    ),
]


CPP_TEMPLATE_CASES = [
    DiffTestCase(
        name="cpp_261_class_template",
        initial_files={
            "container.h": """#pragma once
#include <vector>

template<typename T>
class Container {
    std::vector<T> items;

public:
    void add(const T& item) { items.push_back(item); }
    T& get(size_t index) { return items[index]; }
    size_t size() const { return items.size(); }
};
// unused_marker_67890
""",
            "main.cpp": """#include <iostream>
int main() { return 0; }
""",
        },
        changed_files={
            "main.cpp": """#include "container.h"
#include <string>

int main() {
    Container<int> intContainer;
    intContainer.add(42);

    Container<std::string> strContainer;
    strContainer.add("hello");

    return 0;
}
""",
        },
        must_include=["Container", "intContainer", "strContainer"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add template instantiation",
    ),
    DiffTestCase(
        name="cpp_262_function_template",
        initial_files={
            "algorithm.h": """#pragma once

template<typename T>
T maxValue(T a, T b) {
    return (a > b) ? a : b;
}

template<typename T>
T minValue(T a, T b) {
    return (a < b) ? a : b;
}
// garbage_marker_12345
""",
            "math.cpp": """#include <iostream>
int main() { return 0; }
""",
        },
        changed_files={
            "math.cpp": """#include "algorithm.h"

int computeRange(int a, int b, int c) {
    int maximum = maxValue(maxValue(a, b), c);
    int minimum = minValue(minValue(a, b), c);
    return maximum - minimum;
}
""",
        },
        must_include=["computeRange", "maxValue", "minValue"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add function template usage",
    ),
    DiffTestCase(
        name="cpp_263_template_specialization",
        initial_files={
            "serializer.h": """#pragma once
#include <string>
#include <sstream>

template<typename T>
struct Serializer {
    static std::string serialize(const T& value) {
        std::ostringstream oss;
        oss << value;
        return oss.str();
    }
};

template<>
struct Serializer<bool> {
    static std::string serialize(bool value) {
        return value ? "true" : "false";
    }
};
// unused_marker_67890
""",
            "formatter.cpp": """#include <iostream>
int main() { return 0; }
""",
        },
        changed_files={
            "formatter.cpp": """#include "serializer.h"

std::string format(int n, bool flag) {
    return Serializer<int>::serialize(n) + " " + Serializer<bool>::serialize(flag);
}
""",
        },
        must_include=["format", "Serializer"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add template specialization usage",
    ),
    DiffTestCase(
        name="cpp_264_partial_specialization",
        initial_files={
            "ptr_traits.h": """#pragma once

template<typename T>
struct PtrTraits {
    using element_type = T;
    static constexpr bool is_pointer = false;
};

template<typename T>
struct PtrTraits<T*> {
    using element_type = T;
    static constexpr bool is_pointer = true;
};
// garbage_marker_12345
""",
            "checker.cpp": """#include <iostream>
int main() { return 0; }
""",
        },
        changed_files={
            "checker.cpp": """#include "ptr_traits.h"
#include <iostream>

template<typename T>
void checkType() {
    if constexpr (PtrTraits<T>::is_pointer) {
        std::cout << "Pointer type" << std::endl;
    } else {
        std::cout << "Value type" << std::endl;
    }
}

int main() {
    checkType<int>();
    checkType<int*>();
    return 0;
}
""",
        },
        must_include=["checkType", "PtrTraits"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add partial specialization usage",
    ),
    DiffTestCase(
        name="cpp_265_sfinae",
        initial_files={
            "type_check.h": """#pragma once
#include <type_traits>

template<typename T, typename = void>
struct has_size : std::false_type {};

template<typename T>
struct has_size<T, std::void_t<decltype(std::declval<T>().size())>> : std::true_type {};
// unused_marker_67890
""",
            "printer.cpp": """#include <iostream>
int main() { return 0; }
""",
        },
        changed_files={
            "printer.cpp": """#include "type_check.h"
#include <vector>
#include <string>

template<typename T>
std::enable_if_t<has_size<T>::value, void> printInfo(const T& container) {
    std::cout << "Size: " << container.size() << std::endl;
}

int main() {
    std::vector<int> v{1, 2, 3};
    printInfo(v);
    return 0;
}
""",
        },
        must_include=["printInfo", "has_size"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add SFINAE usage",
    ),
    DiffTestCase(
        name="cpp_266_concepts",
        initial_files={
            "concepts.h": """#pragma once
#include <concepts>

template<typename T>
concept Numeric = std::integral<T> || std::floating_point<T>;

template<Numeric T>
T square(T value) {
    return value * value;
}
// garbage_marker_12345
""",
            "calc.cpp": """#include <iostream>
int main() { return 0; }
""",
        },
        changed_files={
            "calc.cpp": """#include "concepts.h"

double compute(int i, double d) {
    return square(i) + square(d);
}
""",
        },
        must_include=["compute", "square"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add concepts usage",
    ),
    DiffTestCase(
        name="cpp_267_variadic_template",
        initial_files={
            "logger.h": """#pragma once
#include <iostream>
#include <sstream>

template<typename... Args>
void log(Args... args) {
    std::ostringstream oss;
    ((oss << args << " "), ...);
    std::cout << oss.str() << std::endl;
}
// unused_marker_67890
""",
            "app.cpp": """#include <iostream>
int main() { return 0; }
""",
        },
        changed_files={
            "app.cpp": """#include "logger.h"

void process() {
    log("Starting", "process", 42, 3.14);
    log("Done");
}
""",
        },
        must_include=["process", "log"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add variadic template usage",
    ),
    DiffTestCase(
        name="cpp_268_fold_expression",
        initial_files={
            "sum.h": """#pragma once

template<typename... Args>
auto sum(Args... args) {
    return (args + ...);
}

template<typename... Args>
auto product(Args... args) {
    return (args * ...);
}
// garbage_marker_12345
""",
            "math.cpp": """#include <iostream>
int main() { return 0; }
""",
        },
        changed_files={
            "math.cpp": """#include "sum.h"

int main() {
    auto s = sum(1, 2, 3, 4, 5);
    auto p = product(1, 2, 3, 4);
    return 0;
}
""",
        },
        must_include=["sum", "product"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add fold expression usage",
    ),
]


CPP_OOP_CASES = [
    DiffTestCase(
        name="cpp_269_virtual_function",
        initial_files={
            "drawable.h": """#pragma once

class Drawable {
public:
    virtual ~Drawable() = default;
    virtual void draw() = 0;
    virtual void resize(int w, int h) = 0;
};
// unused_marker_67890
""",
            "widget.cpp": """#include <iostream>
int main() { return 0; }
""",
        },
        changed_files={
            "widget.cpp": """#include "drawable.h"
#include <iostream>

class Button : public Drawable {
public:
    void draw() override {
        std::cout << "Drawing button" << std::endl;
    }

    void resize(int w, int h) override {
        std::cout << "Resizing to " << w << "x" << h << std::endl;
    }
};
""",
        },
        must_include=["Button", "draw", "Drawable"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add virtual function implementation",
    ),
    DiffTestCase(
        name="cpp_270_override_specifier",
        initial_files={
            "base.h": """#pragma once
#include <string>

class Base {
public:
    virtual ~Base() = default;
    virtual std::string name() const { return "Base"; }
    virtual void process() {}
};
// garbage_marker_12345
""",
            "derived.cpp": """#include <iostream>
int main() { return 0; }
""",
        },
        changed_files={
            "derived.cpp": """#include "base.h"

class Derived : public Base {
public:
    std::string name() const override { return "Derived"; }
    void process() override {
        // Custom processing
    }
};
""",
        },
        must_include=["Derived", "override", "Base"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add override specifier",
    ),
    DiffTestCase(
        name="cpp_271_final_specifier",
        initial_files={
            "node.h": """#pragma once
#include <string>

class Node {
public:
    virtual ~Node() = default;
    virtual std::string type() const { return "Node"; }
};
// unused_marker_67890
""",
            "leaf.cpp": """#include <iostream>
int main() { return 0; }
""",
        },
        changed_files={
            "leaf.cpp": """#include "node.h"

class Leaf final : public Node {
public:
    std::string type() const override { return "Leaf"; }
    void processLeaf() {}
};
""",
        },
        must_include=["Leaf", "final", "Node"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add final specifier",
    ),
    DiffTestCase(
        name="cpp_272_multiple_inheritance",
        initial_files={
            "interfaces.h": """#pragma once

class Drawable {
public:
    virtual ~Drawable() = default;
    virtual void draw() = 0;
};

class Clickable {
public:
    virtual ~Clickable() = default;
    virtual void onClick() = 0;
};
// garbage_marker_12345
""",
            "widget.cpp": """#include <iostream>
int main() { return 0; }
""",
        },
        changed_files={
            "widget.cpp": """#include "interfaces.h"
#include <iostream>

class Widget : public Drawable, public Clickable {
public:
    void draw() override {
        std::cout << "Drawing widget" << std::endl;
    }

    void onClick() override {
        std::cout << "Widget clicked" << std::endl;
    }
};
""",
        },
        must_include=["Widget", "Drawable", "Clickable"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add multiple inheritance",
    ),
    DiffTestCase(
        name="cpp_273_virtual_inheritance",
        initial_files={
            "base.h": """#pragma once
#include <string>

class Base {
public:
    std::string name;
    virtual ~Base() = default;
};

class Left : virtual public Base {
public:
    void leftMethod() {}
};

class Right : virtual public Base {
public:
    void rightMethod() {}
};
// unused_marker_67890
""",
            "diamond.cpp": """#include <iostream>
int main() { return 0; }
""",
        },
        changed_files={
            "diamond.cpp": """#include "base.h"

class Diamond : public Left, public Right {
public:
    void process() {
        name = "Diamond";
        leftMethod();
        rightMethod();
    }
};
""",
        },
        must_include=["Diamond", "Left", "Right"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add virtual inheritance",
    ),
    DiffTestCase(
        name="cpp_274_constructor_delegation",
        initial_files={
            "user.h": """#pragma once
#include <string>

class User {
    std::string name_;
    int age_;
    bool active_;

public:
    User(std::string name, int age, bool active)
        : name_(std::move(name)), age_(age), active_(active) {}

    User(std::string name, int age) : User(name, age, true) {}

    User(std::string name) : User(name, 0, true) {}
};
// garbage_marker_12345
""",
            "factory.cpp": """#include <iostream>
int main() { return 0; }
""",
        },
        changed_files={
            "factory.cpp": """#include "user.h"

User createDefaultUser() {
    return User("Guest");
}

User createUser(const std::string& name) {
    return User(name, 18);
}
""",
        },
        must_include=["createDefaultUser", "createUser", "User"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add constructor delegation usage",
    ),
    DiffTestCase(
        name="cpp_277_friend_function",
        initial_files={
            "person.h": """#pragma once
#include <string>
#include <ostream>

class Person {
    std::string name_;
    int age_;

public:
    Person(std::string name, int age) : name_(std::move(name)), age_(age) {}

    friend std::ostream& operator<<(std::ostream& os, const Person& p);
    friend bool operator==(const Person& a, const Person& b);
};
// unused_marker_67890
""",
            "person.cpp": """#include <iostream>
int main() { return 0; }
""",
        },
        changed_files={
            "person.cpp": """#include "person.h"

std::ostream& operator<<(std::ostream& os, const Person& p) {
    return os << p.name_ << " (" << p.age_ << ")";
}

bool operator==(const Person& a, const Person& b) {
    return a.name_ == b.name_ && a.age_ == b.age_;
}
""",
        },
        must_include=["operator<<", "operator==", "Person"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add friend function",
    ),
    DiffTestCase(
        name="cpp_278_operator_overloading",
        initial_files={
            "vector2d.h": """#pragma once

class Vector2D {
public:
    double x, y;

    Vector2D(double x = 0, double y = 0) : x(x), y(y) {}

    Vector2D operator+(const Vector2D& other) const {
        return Vector2D(x + other.x, y + other.y);
    }

    Vector2D operator-(const Vector2D& other) const {
        return Vector2D(x - other.x, y - other.y);
    }

    Vector2D operator*(double scalar) const {
        return Vector2D(x * scalar, y * scalar);
    }

    Vector2D& operator+=(const Vector2D& other) {
        x += other.x;
        y += other.y;
        return *this;
    }
};
// garbage_marker_12345
""",
            "physics.cpp": """#include <iostream>
int main() { return 0; }
""",
        },
        changed_files={
            "physics.cpp": """#include "vector2d.h"

Vector2D computePosition(Vector2D pos, Vector2D vel, double dt) {
    return pos + vel * dt;
}

void simulate() {
    Vector2D position(0, 0);
    Vector2D velocity(1, 2);
    position += velocity * 0.1;
}
""",
        },
        must_include=["computePosition", "simulate", "Vector2D"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add operator overloading usage",
    ),
    DiffTestCase(
        name="cpp_280_namespace",
        initial_files={
            "utils.h": """#pragma once
#include <string>

namespace myapp::utils {

std::string trim(const std::string& s);
std::string toUpper(const std::string& s);

}
// unused_marker_67890
""",
            "utils.cpp": """#include "utils.h"
#include <algorithm>
#include <cctype>

namespace myapp::utils {

std::string trim(const std::string& s) {
    size_t start = s.find_first_not_of(" \\t\\n");
    size_t end = s.find_last_not_of(" \\t\\n");
    return (start == std::string::npos) ? "" : s.substr(start, end - start + 1);
}

std::string toUpper(const std::string& s) {
    std::string result = s;
    std::transform(result.begin(), result.end(), result.begin(), ::toupper);
    return result;
}

}
""",
            "app.cpp": """#include <iostream>
int main() { return 0; }
""",
        },
        changed_files={
            "app.cpp": """#include "utils.h"
#include <iostream>

using myapp::utils::trim;
using myapp::utils::toUpper;

int main() {
    std::string input = "  Hello World  ";
    std::cout << toUpper(trim(input)) << std::endl;
    return 0;
}
""",
        },
        must_include=["trim", "toUpper", "myapp::utils"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add namespace usage",
    ),
]


ALL_CPP_CASES = CPP_MEMORY_CASES + CPP_CAST_CASES + CPP_LOWLEVEL_CASES + CPP_TEMPLATE_CASES + CPP_OOP_CASES


@pytest.fixture
def diff_test_runner(tmp_path):
    return DiffTestRunner(tmp_path)


@pytest.mark.parametrize("case", ALL_CPP_CASES, ids=lambda c: c.name)
def test_cpp_diff_context(diff_test_runner: DiffTestRunner, case: DiffTestCase):
    context = diff_test_runner.run_test_case(case)
    diff_test_runner.verify_assertions(context, case)
