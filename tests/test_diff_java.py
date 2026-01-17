import pytest

from tests.utils import DiffTestCase, DiffTestRunner

JAVA_BASIC_CASES = [
    DiffTestCase(
        name="java_001_class_method_added",
        initial_files={
            "src/main/java/com/example/Calculator.java": """package com.example;

public class Calculator {
    public int add(int a, int b) {
        return a + b;
    }
}
""",
            "src/main/java/com/example/Main.java": """package com.example;

public class Main {
    public static void main(String[] args) {
        Calculator calc = new Calculator();
        System.out.println(calc.add(1, 2));
    }
}
""",
        },
        changed_files={
            "src/main/java/com/example/Calculator.java": """package com.example;

public class Calculator {
    public int add(int a, int b) {
        return a + b;
    }

    public int multiply(int a, int b) {
        return a * b;
    }

    public int subtract(int a, int b) {
        return a - b;
    }
}
""",
        },
        must_include=["multiply", "subtract", "Calculator"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add multiply and subtract methods",
    ),
    DiffTestCase(
        name="java_002_interface_implementation",
        initial_files={
            "src/main/java/com/example/PaymentProcessor.java": """package com.example;

public interface PaymentProcessor {
    boolean process(double amount);
    void refund(String transactionId);
}
""",
            "src/main/java/com/example/StripeProcessor.java": """package com.example;

public class StripeProcessor implements PaymentProcessor {
    @Override
    public boolean process(double amount) {
        return true;
    }

    @Override
    public void refund(String transactionId) {
    }
}
""",
        },
        changed_files={
            "src/main/java/com/example/PaymentProcessor.java": """package com.example;

public interface PaymentProcessor {
    boolean process(double amount);
    void refund(String transactionId);
    PaymentStatus getStatus(String transactionId);
}
""",
        },
        must_include=["interface PaymentProcessor", "getStatus"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add getStatus method to interface",
    ),
    DiffTestCase(
        name="java_003_extends_base_class",
        initial_files={
            "src/main/java/com/example/BaseEntity.java": """package com.example;

import java.time.LocalDateTime;

public abstract class BaseEntity {
    private Long id;
    private LocalDateTime createdAt;

    public Long getId() { return id; }
    public LocalDateTime getCreatedAt() { return createdAt; }
}
""",
            "src/main/java/com/example/Product.java": """package com.example;

public class Product extends BaseEntity {
    private String name;
    private Double price;
}
""",
        },
        changed_files={
            "src/main/java/com/example/BaseEntity.java": """package com.example;

import java.time.LocalDateTime;

public abstract class BaseEntity {
    private Long id;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;

    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
    }

    public Long getId() { return id; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public LocalDateTime getUpdatedAt() { return updatedAt; }
}
""",
        },
        must_include=["BaseEntity", "updatedAt", "onUpdate"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add updatedAt field with onUpdate",
    ),
    DiffTestCase(
        name="java_004_override_method",
        initial_files={
            "src/main/java/com/example/Animal.java": """package com.example;

public abstract class Animal {
    protected String name;

    public abstract String speak();

    public void eat() {
        System.out.println(name + " is eating");
    }
}
""",
            "src/main/java/com/example/Dog.java": """package com.example;

public class Dog extends Animal {
    public Dog(String name) {
        this.name = name;
    }

    @Override
    public String speak() {
        return "Woof!";
    }
}
""",
        },
        changed_files={
            "src/main/java/com/example/Dog.java": """package com.example;

public class Dog extends Animal {
    private String breed;

    public Dog(String name, String breed) {
        this.name = name;
        this.breed = breed;
    }

    @Override
    public String speak() {
        return "Woof! I'm a " + breed;
    }

    @Override
    public void eat() {
        System.out.println(name + " the " + breed + " is eating");
    }
}
""",
        },
        must_include=["Dog", "breed", "@Override"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add breed and override eat method",
    ),
]


JAVA_SPRING_CASES = [
    DiffTestCase(
        name="java_011_autowired_service",
        initial_files={
            "src/main/java/com/example/UserService.java": """package com.example;

import org.springframework.stereotype.Service;

@Service
public class UserService {
    public User findById(Long id) {
        return new User(id, "John");
    }
}
""",
            "src/main/java/com/example/UserController.java": """package com.example;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/users")
public class UserController {

    @Autowired
    private UserService userService;

    @GetMapping("/{id}")
    public User getUser(@PathVariable Long id) {
        return userService.findById(id);
    }
}
""",
        },
        changed_files={
            "src/main/java/com/example/UserService.java": """package com.example;

import org.springframework.stereotype.Service;
import java.util.List;

@Service
public class UserService {
    public User findById(Long id) {
        return new User(id, "John");
    }

    public List<User> findAll() {
        return List.of(new User(1L, "John"), new User(2L, "Jane"));
    }

    public User save(User user) {
        return user;
    }
}
""",
        },
        must_include=["@Service", "UserService", "findAll", "save"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add findAll and save methods",
    ),
    DiffTestCase(
        name="java_012_entity_relations",
        initial_files={
            "src/main/java/com/example/Order.java": """package com.example;

import javax.persistence.*;
import java.util.List;

@Entity
@Table(name = "orders")
public class Order {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne
    @JoinColumn(name = "customer_id")
    private Customer customer;

    @OneToMany(mappedBy = "order", cascade = CascadeType.ALL)
    private List<OrderItem> items;
}
""",
            "src/main/java/com/example/Customer.java": """package com.example;

import javax.persistence.*;
import java.util.List;

@Entity
@Table(name = "customers")
public class Customer {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String name;

    @OneToMany(mappedBy = "customer")
    private List<Order> orders;
}
""",
        },
        changed_files={
            "src/main/java/com/example/Order.java": """package com.example;

import javax.persistence.*;
import java.util.List;
import java.math.BigDecimal;

@Entity
@Table(name = "orders")
public class Order {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne
    @JoinColumn(name = "customer_id")
    private Customer customer;

    @OneToMany(mappedBy = "order", cascade = CascadeType.ALL)
    private List<OrderItem> items;

    @Column(name = "total_amount")
    private BigDecimal totalAmount;

    @Enumerated(EnumType.STRING)
    private OrderStatus status;
}
""",
        },
        must_include=["@Entity", "Order", "totalAmount", "status"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add totalAmount and status to Order",
    ),
    DiffTestCase(
        name="java_013_rest_controller_dto",
        initial_files={
            "src/main/java/com/example/dto/UserDto.java": """package com.example.dto;

public class UserDto {
    private Long id;
    private String name;

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
}
""",
            "src/main/java/com/example/UserController.java": """package com.example;

import com.example.dto.UserDto;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/users")
public class UserController {
    @GetMapping("/{id}")
    public UserDto getUser(@PathVariable Long id) {
        UserDto dto = new UserDto();
        dto.setId(id);
        dto.setName("User");
        return dto;
    }
}
""",
        },
        changed_files={
            "src/main/java/com/example/dto/UserDto.java": """package com.example.dto;

import javax.validation.constraints.*;

public class UserDto {
    private Long id;

    @NotBlank
    @Size(min = 2, max = 100)
    private String name;

    @Email
    private String email;

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }
}
""",
        },
        must_include=["UserDto", "@NotBlank", "@Email", "email"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add email and validation to UserDto",
    ),
    DiffTestCase(
        name="java_014_transactional",
        initial_files={
            "src/main/java/com/example/OrderService.java": """package com.example;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class OrderService {
    @Transactional
    public Order createOrder(Order order) {
        return orderRepository.save(order);
    }
}
""",
        },
        changed_files={
            "src/main/java/com/example/OrderService.java": """package com.example;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Isolation;

@Service
public class OrderService {
    @Transactional(
        propagation = Propagation.REQUIRED,
        isolation = Isolation.READ_COMMITTED,
        rollbackFor = Exception.class
    )
    public Order createOrder(Order order) {
        Order saved = orderRepository.save(order);
        inventoryService.updateStock(order.getItems());
        return saved;
    }

    @Transactional(readOnly = true)
    public Order getOrder(Long id) {
        return orderRepository.findById(id).orElse(null);
    }
}
""",
        },
        must_include=["@Transactional", "OrderService", "getOrder"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add transaction configuration and getOrder",
    ),
    DiffTestCase(
        name="java_015_scheduled",
        initial_files={
            "src/main/java/com/example/ScheduledTasks.java": """package com.example;

import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Component
public class ScheduledTasks {
    @Scheduled(fixedRate = 60000)
    public void cleanupTask() {
        System.out.println("Running cleanup");
    }
}
""",
        },
        changed_files={
            "src/main/java/com/example/ScheduledTasks.java": """package com.example;

import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Component
public class ScheduledTasks {
    private static final Logger logger = LoggerFactory.getLogger(ScheduledTasks.class);

    @Scheduled(fixedRate = 60000)
    public void cleanupTask() {
        logger.info("Running cleanup");
    }

    @Scheduled(cron = "0 0 2 * * ?")
    public void dailyReport() {
        logger.info("Generating daily report");
    }
}
""",
        },
        must_include=["@Scheduled", "dailyReport", "cron"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add dailyReport scheduled task",
    ),
    DiffTestCase(
        name="java_016_kafka_listener",
        initial_files={
            "src/main/java/com/example/KafkaConsumer.java": """package com.example;

import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

@Component
public class KafkaConsumer {
    @KafkaListener(topics = "orders")
    public void listen(String message) {
        System.out.println("Received: " + message);
    }
}
""",
            "src/main/java/com/example/KafkaProducer.java": """package com.example;

import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;

@Component
public class KafkaProducer {
    private final KafkaTemplate<String, String> kafkaTemplate;

    public KafkaProducer(KafkaTemplate<String, String> kafkaTemplate) {
        this.kafkaTemplate = kafkaTemplate;
    }

    public void send(String message) {
        kafkaTemplate.send("orders", message);
    }
}
""",
        },
        changed_files={
            "src/main/java/com/example/KafkaConsumer.java": """package com.example;

import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.support.Acknowledgment;
import org.springframework.stereotype.Component;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Component
public class KafkaConsumer {
    private static final Logger logger = LoggerFactory.getLogger(KafkaConsumer.class);

    @KafkaListener(topics = "orders", groupId = "order-processor")
    public void listen(String message, Acknowledgment ack) {
        try {
            processMessage(message);
            ack.acknowledge();
        } catch (Exception e) {
            logger.error("Failed to process message", e);
        }
    }

    private void processMessage(String message) {
        logger.info("Processing: {}", message);
    }
}
""",
        },
        must_include=["@KafkaListener", "KafkaConsumer", "Acknowledgment"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add acknowledgment and error handling",
    ),
]


JAVA_PATTERNS_CASES = [
    DiffTestCase(
        name="java_021_builder_pattern",
        initial_files={
            "src/main/java/com/example/User.java": """package com.example;

public class User {
    private final String name;
    private final String email;

    public User(String name, String email) {
        this.name = name;
        this.email = email;
    }

    public String getName() { return name; }
    public String getEmail() { return email; }
}
""",
        },
        changed_files={
            "src/main/java/com/example/User.java": """package com.example;

public class User {
    private final String name;
    private final String email;
    private final int age;
    private final String address;

    private User(Builder builder) {
        this.name = builder.name;
        this.email = builder.email;
        this.age = builder.age;
        this.address = builder.address;
    }

    public String getName() { return name; }
    public String getEmail() { return email; }
    public int getAge() { return age; }
    public String getAddress() { return address; }

    public static Builder builder() {
        return new Builder();
    }

    public static class Builder {
        private String name;
        private String email;
        private int age;
        private String address;

        public Builder name(String name) {
            this.name = name;
            return this;
        }

        public Builder email(String email) {
            this.email = email;
            return this;
        }

        public Builder age(int age) {
            this.age = age;
            return this;
        }

        public Builder address(String address) {
            this.address = address;
            return this;
        }

        public User build() {
            return new User(this);
        }
    }
}
""",
        },
        must_include=["Builder", "builder()", "build()"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add builder pattern to User",
    ),
    DiffTestCase(
        name="java_022_factory_pattern",
        initial_files={
            "src/main/java/com/example/Notification.java": """package com.example;

public interface Notification {
    void send(String message);
}
""",
            "src/main/java/com/example/EmailNotification.java": """package com.example;

public class EmailNotification implements Notification {
    @Override
    public void send(String message) {
        System.out.println("Email: " + message);
    }
}
""",
        },
        changed_files={
            "src/main/java/com/example/NotificationFactory.java": """package com.example;

public class NotificationFactory {
    public enum Type {
        EMAIL, SMS, PUSH
    }

    public static Notification create(Type type) {
        return switch (type) {
            case EMAIL -> new EmailNotification();
            case SMS -> new SmsNotification();
            case PUSH -> new PushNotification();
        };
    }
}
""",
            "src/main/java/com/example/SmsNotification.java": """package com.example;

public class SmsNotification implements Notification {
    @Override
    public void send(String message) {
        System.out.println("SMS: " + message);
    }
}
""",
            "src/main/java/com/example/PushNotification.java": """package com.example;

public class PushNotification implements Notification {
    @Override
    public void send(String message) {
        System.out.println("Push: " + message);
    }
}
""",
        },
        must_include=["NotificationFactory", "create"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add factory pattern for notifications",
    ),
    DiffTestCase(
        name="java_023_singleton_pattern",
        initial_files={
            "src/main/java/com/example/Config.java": """package com.example;

public class Config {
    private String value;

    public Config() {
        this.value = "default";
    }

    public String getValue() {
        return value;
    }
}
""",
        },
        changed_files={
            "src/main/java/com/example/Config.java": """package com.example;

public class Config {
    private static volatile Config instance;
    private final String value;

    private Config() {
        this.value = System.getenv().getOrDefault("CONFIG", "default");
    }

    public static Config getInstance() {
        if (instance == null) {
            synchronized (Config.class) {
                if (instance == null) {
                    instance = new Config();
                }
            }
        }
        return instance;
    }

    public String getValue() {
        return value;
    }
}
""",
            "src/main/java/com/example/AppContext.java": """package com.example;

public class AppContext {
    public void initialize() {
        Config config = Config.getInstance();
        System.out.println("Config: " + config.getValue());
    }
}
""",
        },
        must_include=["getInstance()", "volatile", "synchronized"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Convert Config to singleton",
    ),
    DiffTestCase(
        name="java_024_observer_pattern",
        initial_files={
            "src/main/java/com/example/Event.java": """package com.example;

public class Event {
    private final String type;
    private final Object data;

    public Event(String type, Object data) {
        this.type = type;
        this.data = data;
    }

    public String getType() { return type; }
    public Object getData() { return data; }
}
""",
        },
        changed_files={
            "src/main/java/com/example/EventListener.java": """package com.example;

@FunctionalInterface
public interface EventListener {
    void onEvent(Event event);
}
""",
            "src/main/java/com/example/EventBus.java": """package com.example;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class EventBus {
    private final Map<String, List<EventListener>> listeners = new HashMap<>();

    public void subscribe(String eventType, EventListener listener) {
        listeners.computeIfAbsent(eventType, k -> new ArrayList<>()).add(listener);
    }

    public void unsubscribe(String eventType, EventListener listener) {
        List<EventListener> list = listeners.get(eventType);
        if (list != null) {
            list.remove(listener);
        }
    }

    public void publish(Event event) {
        List<EventListener> list = listeners.get(event.getType());
        if (list != null) {
            for (EventListener listener : list) {
                listener.onEvent(event);
            }
        }
    }
}
""",
        },
        must_include=["EventBus", "subscribe", "publish"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add observer pattern with EventBus",
    ),
    DiffTestCase(
        name="java_025_strategy_pattern",
        initial_files={
            "src/main/java/com/example/PaymentProcessor.java": """package com.example;

public class PaymentProcessor {
    public void process(String type, double amount) {
        if ("credit".equals(type)) {
            System.out.println("Credit: " + amount);
        } else if ("debit".equals(type)) {
            System.out.println("Debit: " + amount);
        }
    }
}
""",
        },
        changed_files={
            "src/main/java/com/example/PaymentStrategy.java": """package com.example;

public interface PaymentStrategy {
    void pay(double amount);
    boolean validate(double amount);
}
""",
            "src/main/java/com/example/CreditCardPayment.java": """package com.example;

public class CreditCardPayment implements PaymentStrategy {
    private final String cardNumber;

    public CreditCardPayment(String cardNumber) {
        this.cardNumber = cardNumber;
    }

    @Override
    public void pay(double amount) {
        System.out.println("Credit card " + cardNumber + ": " + amount);
    }

    @Override
    public boolean validate(double amount) {
        return amount > 0 && amount < 10000;
    }
}
""",
            "src/main/java/com/example/PaymentProcessor.java": """package com.example;

public class PaymentProcessor {
    private PaymentStrategy strategy;

    public void setStrategy(PaymentStrategy strategy) {
        this.strategy = strategy;
    }

    public void process(double amount) {
        if (strategy.validate(amount)) {
            strategy.pay(amount);
        } else {
            throw new IllegalArgumentException("Invalid amount");
        }
    }
}
""",
        },
        must_include=["PaymentStrategy", "setStrategy"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Refactor to strategy pattern",
    ),
]


JAVA_ADVANCED_CASES = [
    DiffTestCase(
        name="java_031_custom_exception",
        initial_files={
            "src/main/java/com/example/Service.java": """package com.example;

public class Service {
    public void process(String input) {
        if (input == null) {
            throw new RuntimeException("Input is null");
        }
    }
}
""",
        },
        changed_files={
            "src/main/java/com/example/ServiceException.java": """package com.example;

public class ServiceException extends RuntimeException {
    private final String errorCode;

    public ServiceException(String message, String errorCode) {
        super(message);
        this.errorCode = errorCode;
    }

    public ServiceException(String message, String errorCode, Throwable cause) {
        super(message, cause);
        this.errorCode = errorCode;
    }

    public String getErrorCode() {
        return errorCode;
    }
}
""",
            "src/main/java/com/example/ValidationException.java": """package com.example;

public class ValidationException extends ServiceException {
    public ValidationException(String message) {
        super(message, "VALIDATION_ERROR");
    }
}
""",
            "src/main/java/com/example/Service.java": """package com.example;

public class Service {
    public void process(String input) {
        if (input == null) {
            throw new ValidationException("Input cannot be null");
        }
        if (input.isEmpty()) {
            throw new ValidationException("Input cannot be empty");
        }
    }
}
""",
        },
        must_include=["ServiceException", "ValidationException", "errorCode"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add custom exception hierarchy",
    ),
    DiffTestCase(
        name="java_032_generic_repository",
        initial_files={
            "src/main/java/com/example/UserRepository.java": """package com.example;

import java.util.HashMap;
import java.util.Map;

public class UserRepository {
    private final Map<Long, User> storage = new HashMap<>();

    public void save(User user) {
        storage.put(user.getId(), user);
    }

    public User findById(Long id) {
        return storage.get(id);
    }
}
""",
        },
        changed_files={
            "src/main/java/com/example/Entity.java": """package com.example;

public interface Entity<ID> {
    ID getId();
}
""",
            "src/main/java/com/example/Repository.java": """package com.example;

import java.util.List;
import java.util.Optional;

public interface Repository<T extends Entity<ID>, ID> {
    void save(T entity);
    Optional<T> findById(ID id);
    List<T> findAll();
    void delete(ID id);
}
""",
            "src/main/java/com/example/InMemoryRepository.java": """package com.example;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

public class InMemoryRepository<T extends Entity<ID>, ID> implements Repository<T, ID> {
    private final Map<ID, T> storage = new HashMap<>();

    @Override
    public void save(T entity) {
        storage.put(entity.getId(), entity);
    }

    @Override
    public Optional<T> findById(ID id) {
        return Optional.ofNullable(storage.get(id));
    }

    @Override
    public List<T> findAll() {
        return new ArrayList<>(storage.values());
    }

    @Override
    public void delete(ID id) {
        storage.remove(id);
    }
}
""",
        },
        must_include=["Repository", "Entity", "Generic"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add generic repository pattern",
    ),
    DiffTestCase(
        name="java_033_custom_annotation",
        initial_files={
            "src/main/java/com/example/Validator.java": """package com.example;

public class Validator {
    public boolean validate(Object obj) {
        return obj != null;
    }
}
""",
        },
        changed_files={
            "src/main/java/com/example/NotNull.java": """package com.example;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

@Retention(RetentionPolicy.RUNTIME)
@Target({ElementType.FIELD, ElementType.PARAMETER})
public @interface NotNull {
    String message() default "Value cannot be null";
}
""",
            "src/main/java/com/example/Size.java": """package com.example;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.FIELD)
public @interface Size {
    int min() default 0;
    int max() default Integer.MAX_VALUE;
    String message() default "Size out of bounds";
}
""",
            "src/main/java/com/example/Validator.java": """package com.example;

import java.lang.reflect.Field;

public class Validator {
    public void validate(Object obj) throws ValidationException {
        for (Field field : obj.getClass().getDeclaredFields()) {
            field.setAccessible(true);
            try {
                Object value = field.get(obj);
                if (field.isAnnotationPresent(NotNull.class) && value == null) {
                    NotNull ann = field.getAnnotation(NotNull.class);
                    throw new ValidationException(ann.message());
                }
                if (field.isAnnotationPresent(Size.class) && value instanceof String s) {
                    Size size = field.getAnnotation(Size.class);
                    if (s.length() < size.min() || s.length() > size.max()) {
                        throw new ValidationException(size.message());
                    }
                }
            } catch (IllegalAccessException e) {
                throw new RuntimeException(e);
            }
        }
    }
}
""",
        },
        must_include=["@interface NotNull", "@Retention", "isAnnotationPresent"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add custom validation annotations",
    ),
    DiffTestCase(
        name="java_034_streams_api",
        initial_files={
            "src/main/java/com/example/DataProcessor.java": """package com.example;

import java.util.ArrayList;
import java.util.List;

public class DataProcessor {
    public List<String> filterActive(List<User> users) {
        List<String> result = new ArrayList<>();
        for (User user : users) {
            if (user.isActive()) {
                result.add(user.getName());
            }
        }
        return result;
    }
}
""",
        },
        changed_files={
            "src/main/java/com/example/DataProcessor.java": """package com.example;

import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

public class DataProcessor {
    public List<String> filterActive(List<User> users) {
        return users.stream()
            .filter(User::isActive)
            .map(User::getName)
            .sorted()
            .toList();
    }

    public Map<String, List<User>> groupByDepartment(List<User> users) {
        return users.stream()
            .collect(Collectors.groupingBy(User::getDepartment));
    }

    public double averageAge(List<User> users) {
        return users.stream()
            .mapToInt(User::getAge)
            .average()
            .orElse(0.0);
    }

    public List<User> topNByScore(List<User> users, int n) {
        return users.stream()
            .sorted(Comparator.comparingDouble(User::getScore).reversed())
            .limit(n)
            .toList();
    }
}
""",
            "src/main/java/com/example/User.java": """package com.example;

public class User {
    private String name;
    private boolean active;
    private String department;
    private int age;
    private double score;

    public String getName() { return name; }
    public boolean isActive() { return active; }
    public String getDepartment() { return department; }
    public int getAge() { return age; }
    public double getScore() { return score; }
}
""",
        },
        must_include=["stream()", "Collectors", "groupByDepartment"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Refactor to use Streams API",
    ),
    DiffTestCase(
        name="java_035_completable_future",
        initial_files={
            "src/main/java/com/example/AsyncService.java": """package com.example;

public class AsyncService {
    public String fetchData() {
        return "data";
    }
}
""",
        },
        changed_files={
            "src/main/java/com/example/AsyncService.java": """package com.example;

import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class AsyncService {
    private final ExecutorService executor = Executors.newFixedThreadPool(4);

    public CompletableFuture<String> fetchData() {
        return CompletableFuture.supplyAsync(() -> {
            simulateDelay();
            return "data";
        }, executor);
    }

    public CompletableFuture<String> processData(String input) {
        return CompletableFuture.supplyAsync(() -> {
            simulateDelay();
            return input.toUpperCase();
        }, executor);
    }

    public CompletableFuture<String> fetchAndProcess() {
        return fetchData()
            .thenCompose(this::processData)
            .exceptionally(ex -> "error: " + ex.getMessage());
    }

    public CompletableFuture<String> fetchMultiple() {
        CompletableFuture<String> f1 = fetchData();
        CompletableFuture<String> f2 = fetchData();

        return CompletableFuture.allOf(f1, f2)
            .thenApply(v -> f1.join() + "," + f2.join());
    }

    private void simulateDelay() {
        try {
            Thread.sleep(100);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    public void shutdown() {
        executor.shutdown();
    }
}
""",
        },
        must_include=["CompletableFuture", "thenCompose", "supplyAsync"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add CompletableFuture async patterns",
    ),
]


JAVA_BUILD_CASES = [
    DiffTestCase(
        name="java_041_pom_dependency",
        initial_files={
            "pom.xml": """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>myapp</artifactId>
    <version>1.0.0</version>

    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
            <version>3.0.0</version>
        </dependency>
    </dependencies>
</project>
""",
            "src/main/java/com/example/Application.java": """package com.example;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}
""",
        },
        changed_files={
            "pom.xml": """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>myapp</artifactId>
    <version>1.0.0</version>

    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
            <version>3.0.0</version>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-jpa</artifactId>
            <version>3.0.0</version>
        </dependency>
        <dependency>
            <groupId>org.postgresql</groupId>
            <artifactId>postgresql</artifactId>
            <version>42.5.0</version>
        </dependency>
    </dependencies>
</project>
""",
        },
        must_include=["pom.xml", "spring-boot-starter-data-jpa", "postgresql"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add JPA and PostgreSQL dependencies",
    ),
    DiffTestCase(
        name="java_042_gradle_plugin",
        initial_files={
            "build.gradle": """plugins {
    id 'java'
    id 'org.springframework.boot' version '3.0.0'
}

dependencies {
    implementation 'org.springframework.boot:spring-boot-starter-web'
}
""",
        },
        changed_files={
            "build.gradle": """plugins {
    id 'java'
    id 'org.springframework.boot' version '3.0.0'
    id 'io.spring.dependency-management' version '1.1.0'
    id 'jacoco'
}

dependencies {
    implementation 'org.springframework.boot:spring-boot-starter-web'
    implementation 'org.springframework.boot:spring-boot-starter-actuator'
    testImplementation 'org.springframework.boot:spring-boot-starter-test'
}

jacoco {
    toolVersion = "0.8.8"
}
""",
        },
        must_include=["build.gradle", "jacoco", "actuator"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add jacoco plugin and actuator",
    ),
    DiffTestCase(
        name="java_043_application_properties",
        initial_files={
            "src/main/resources/application.properties": """server.port=8080
spring.datasource.url=jdbc:postgresql://localhost/db
""",
            "src/main/java/com/example/Config.java": """package com.example;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

@Component
public class Config {
    @Value("${server.port}")
    private int port;

    public int getPort() { return port; }
}
""",
        },
        changed_files={
            "src/main/resources/application.properties": """server.port=8080
spring.datasource.url=jdbc:postgresql://localhost/db
spring.cache.type=redis
spring.redis.host=localhost
spring.redis.port=6379
""",
        },
        must_include=["application.properties", "redis"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add Redis configuration",
    ),
]


JAVA_KOTLIN_CASES = [
    DiffTestCase(
        name="java_051_kotlin_suspend_fun",
        initial_files={
            "src/main/kotlin/com/example/UserService.kt": """package com.example

class UserService(private val repository: UserRepository) {
    suspend fun getUser(id: Long): User? {
        return repository.findById(id)
    }
}
""",
            "src/main/kotlin/com/example/UserController.kt": """package com.example

import kotlinx.coroutines.runBlocking

class UserController(private val service: UserService) {
    fun getUser(id: Long): User? = runBlocking {
        service.getUser(id)
    }
}
""",
        },
        changed_files={
            "src/main/kotlin/com/example/UserService.kt": """package com.example

import kotlinx.coroutines.delay

class UserService(private val repository: UserRepository) {
    suspend fun getUser(id: Long): User? {
        return repository.findById(id)
    }

    suspend fun getUserWithRetry(id: Long, retries: Int = 3): User? {
        repeat(retries) { attempt ->
            try {
                return repository.findById(id)
            } catch (e: Exception) {
                delay(1000L * (attempt + 1))
            }
        }
        return null
    }
}
""",
        },
        must_include=["suspend fun", "getUserWithRetry", "delay"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add getUserWithRetry with coroutine delay",
    ),
    DiffTestCase(
        name="java_052_kotlin_data_class",
        initial_files={
            "src/main/kotlin/com/example/User.kt": """package com.example

data class User(
    val id: Long,
    val name: String
)
""",
            "src/main/kotlin/com/example/UserMapper.kt": """package com.example

object UserMapper {
    fun toDto(user: User): UserDto = UserDto(user.id, user.name)
}

data class UserDto(val id: Long, val name: String)
""",
        },
        changed_files={
            "src/main/kotlin/com/example/User.kt": """package com.example

data class User(
    val id: Long,
    val name: String,
    val email: String,
    val active: Boolean = true
)
""",
        },
        must_include=["data class User", "email", "active"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add email and active fields to User",
    ),
    DiffTestCase(
        name="java_053_kotlin_sealed_class",
        initial_files={
            "src/main/kotlin/com/example/Result.kt": """package com.example

sealed class Result<out T> {
    data class Success<T>(val data: T) : Result<T>()
    data class Error(val message: String) : Result<Nothing>()
}
""",
            "src/main/kotlin/com/example/Handler.kt": """package com.example

fun handleResult(result: Result<String>) {
    when (result) {
        is Result.Success -> println(result.data)
        is Result.Error -> println(result.message)
    }
}
""",
        },
        changed_files={
            "src/main/kotlin/com/example/Result.kt": """package com.example

sealed class Result<out T> {
    data class Success<T>(val data: T) : Result<T>()
    data class Error(val message: String, val cause: Throwable? = null) : Result<Nothing>()
    data object Loading : Result<Nothing>()
    data object Empty : Result<Nothing>()
}
""",
        },
        must_include=["sealed class Result", "Loading", "Empty"],
        must_not_include=["garbage_marker_12345", "unused_marker_67890"],
        commit_message="Add Loading and Empty states to sealed class",
    ),
]


ALL_JAVA_CASES = (
    JAVA_BASIC_CASES + JAVA_SPRING_CASES + JAVA_PATTERNS_CASES + JAVA_ADVANCED_CASES + JAVA_BUILD_CASES + JAVA_KOTLIN_CASES
)


@pytest.mark.parametrize("case", ALL_JAVA_CASES, ids=lambda c: c.name)
def test_java_diff_context(diff_test_runner: DiffTestRunner, case: DiffTestCase):
    context = diff_test_runner.run_test_case(case)
    diff_test_runner.verify_assertions(context, case)
