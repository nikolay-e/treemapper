import pytest

from tests.utils import DiffTestCase, DiffTestRunner

JAVA_TEST_CASES = [
    DiffTestCase(
        name="java_autowired_service",
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
        must_include=["UserService.java", "findAll", "save"],
        commit_message="Add findAll and save methods",
    ),
    DiffTestCase(
        name="java_entity_relations",
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
        must_include=["Order.java", "totalAmount", "status"],
        commit_message="Add totalAmount and status to Order",
    ),
    DiffTestCase(
        name="java_implements_interface",
        initial_files={
            "src/main/java/com/example/PaymentProcessor.java": """package com.example;

public interface PaymentProcessor {
    boolean process(Payment payment);
    void refund(String transactionId);
}
""",
            "src/main/java/com/example/StripeProcessor.java": """package com.example;

public class StripeProcessor implements PaymentProcessor {
    @Override
    public boolean process(Payment payment) {
        return true;
    }

    @Override
    public void refund(String transactionId) {
        // Stripe refund logic
    }
}
""",
        },
        changed_files={
            "src/main/java/com/example/PaymentProcessor.java": """package com.example;

public interface PaymentProcessor {
    boolean process(Payment payment);
    void refund(String transactionId);
    PaymentStatus getStatus(String transactionId);
}
""",
        },
        must_include=["PaymentProcessor.java", "getStatus"],
        commit_message="Add getStatus method to interface",
    ),
    DiffTestCase(
        name="java_extends_base_class",
        initial_files={
            "src/main/java/com/example/BaseEntity.java": """package com.example;

import javax.persistence.*;
import java.time.LocalDateTime;

@MappedSuperclass
public abstract class BaseEntity {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    public Long getId() { return id; }
    public LocalDateTime getCreatedAt() { return createdAt; }
}
""",
            "src/main/java/com/example/Product.java": """package com.example;

import javax.persistence.*;

@Entity
public class Product extends BaseEntity {
    private String name;
    private Double price;
}
""",
        },
        changed_files={
            "src/main/java/com/example/BaseEntity.java": """package com.example;

import javax.persistence.*;
import java.time.LocalDateTime;

@MappedSuperclass
public abstract class BaseEntity {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
    }

    public Long getId() { return id; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public LocalDateTime getUpdatedAt() { return updatedAt; }
}
""",
        },
        must_include=["BaseEntity.java", "updatedAt", "onUpdate"],
        commit_message="Add updatedAt field with PreUpdate",
    ),
    DiffTestCase(
        name="java_override_method",
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
        must_include=["Dog.java", "breed", "eat"],
        commit_message="Add breed and override eat method",
    ),
    DiffTestCase(
        name="java_pom_dependency",
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
        commit_message="Add JPA and PostgreSQL dependencies",
    ),
    DiffTestCase(
        name="java_gradle_plugin",
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
        commit_message="Add jacoco plugin and actuator",
    ),
    DiffTestCase(
        name="java_application_properties",
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
        commit_message="Add Redis configuration",
    ),
    DiffTestCase(
        name="java_rest_controller_dto",
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
        must_include=["UserDto.java", "email", "@Email"],
        commit_message="Add email and validation to UserDto",
    ),
    DiffTestCase(
        name="java_transactional",
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
        must_include=["OrderService.java", "Propagation.REQUIRED", "getOrder"],
        commit_message="Add transaction configuration and getOrder",
    ),
    DiffTestCase(
        name="java_scheduled",
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
        must_include=["ScheduledTasks.java", "dailyReport", "cron"],
        commit_message="Add dailyReport scheduled task",
    ),
    DiffTestCase(
        name="java_kafka_listener",
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
        must_include=["KafkaConsumer.java", "Acknowledgment", "processMessage"],
        commit_message="Add acknowledgment and error handling",
    ),
    DiffTestCase(
        name="java_builder_pattern",
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
            "src/main/java/com/example/UserService.java": """package com.example;

public class UserService {
    public User createUser(String name, String email) {
        return User.builder()
            .name(name)
            .email(email)
            .age(0)
            .build();
    }
}
""",
        },
        must_include=["User.java", "Builder", "builder()"],
        commit_message="Add builder pattern to User",
    ),
    DiffTestCase(
        name="java_factory_pattern",
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
            "src/main/java/com/example/SmsNotification.java": """package com.example;

public class SmsNotification implements Notification {
    @Override
    public void send(String message) {
        System.out.println("SMS: " + message);
    }
}
""",
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
            "src/main/java/com/example/PushNotification.java": """package com.example;

public class PushNotification implements Notification {
    @Override
    public void send(String message) {
        System.out.println("Push: " + message);
    }
}
""",
        },
        must_include=["NotificationFactory.java", "create"],
        commit_message="Add factory pattern for notifications",
    ),
    DiffTestCase(
        name="java_singleton_pattern",
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
        must_include=["Config.java", "getInstance", "volatile"],
        commit_message="Convert Config to singleton",
    ),
    DiffTestCase(
        name="java_observer_pattern",
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
            "src/main/java/com/example/UserEventHandler.java": """package com.example;

public class UserEventHandler implements EventListener {
    @Override
    public void onEvent(Event event) {
        System.out.println("User event: " + event.getType());
    }
}
""",
        },
        must_include=["EventBus.java", "subscribe", "publish"],
        commit_message="Add observer pattern with EventBus",
    ),
    DiffTestCase(
        name="java_strategy_pattern",
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
        must_include=["PaymentProcessor.java", "PaymentStrategy", "setStrategy"],
        commit_message="Refactor to strategy pattern",
    ),
    DiffTestCase(
        name="java_custom_exception",
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
        must_include=["ServiceException.java", "errorCode"],
        commit_message="Add custom exception hierarchy",
    ),
    DiffTestCase(
        name="java_generic_repository",
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
        must_include=["Repository.java", "Entity<ID>"],
        commit_message="Add generic repository pattern",
    ),
    DiffTestCase(
        name="java_streams_api",
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
        must_include=["DataProcessor.java", "stream()", "groupByDepartment"],
        commit_message="Refactor to use Streams API",
    ),
    DiffTestCase(
        name="java_completable_future",
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
            "src/main/java/com/example/ApiClient.java": """package com.example;

import java.util.concurrent.CompletableFuture;

public class ApiClient {
    private final AsyncService asyncService;

    public ApiClient(AsyncService asyncService) {
        this.asyncService = asyncService;
    }

    public CompletableFuture<String> callApi() {
        return asyncService.fetchAndProcess();
    }
}
""",
        },
        must_include=["AsyncService.java", "CompletableFuture", "thenCompose"],
        commit_message="Add CompletableFuture async patterns",
    ),
]

KOTLIN_TEST_CASES = [
    DiffTestCase(
        name="kotlin_suspend_fun",
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
        must_include=["UserService.kt", "getUserWithRetry", "delay"],
        commit_message="Add getUserWithRetry with coroutine delay",
    ),
    DiffTestCase(
        name="kotlin_data_class",
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
        must_include=["User.kt", "email", "active"],
        commit_message="Add email and active fields to User",
    ),
    DiffTestCase(
        name="kotlin_sealed_class",
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
        must_include=["Result.kt", "Loading", "Empty"],
        commit_message="Add Loading and Empty states to sealed class",
    ),
]

SCALA_TEST_CASES = [
    DiffTestCase(
        name="scala_case_class",
        initial_files={
            "User.scala": """case class User(name: String, age: Int) {
  def isAdult: Boolean = age >= 18
}

object User {
  def apply(name: String): User = User(name, 0)
}
""",
            "UserService.scala": """// Initial
class UserService {}
""",
        },
        changed_files={
            "UserService.scala": """class UserService {
  def createUser(name: String, age: Int): User = {
    User(name, age)
  }

  def copyWithNewAge(user: User, newAge: Int): User = {
    user.copy(age = newAge)
  }

  def compareUsers(u1: User, u2: User): Boolean = {
    u1 == u2
  }
}
""",
        },
        must_include=["UserService.scala", "createUser", "copyWithNewAge"],
        commit_message="Add case class usage",
    ),
    DiffTestCase(
        name="scala_trait_mixin",
        initial_files={
            "Logging.scala": """trait Logging {
  def log(message: String): Unit = println(s"[LOG] $message")
  def debug(message: String): Unit = println(s"[DEBUG] $message")
}
""",
            "Metrics.scala": """trait Metrics {
  def recordMetric(name: String, value: Double): Unit = {
    println(s"Metric: $name = $value")
  }
}
""",
            "Service.scala": """// Initial
class Service {}
""",
        },
        changed_files={
            "Service.scala": """class Service extends Logging with Metrics {
  def process(data: String): Unit = {
    log(s"Processing: $data")
    recordMetric("process_count", 1.0)
    debug("Process complete")
  }
}
""",
        },
        must_include=["Service.scala", "extends Logging with Metrics"],
        commit_message="Add trait mixin",
    ),
    DiffTestCase(
        name="scala_object_singleton",
        initial_files={
            "Config.scala": """object Config {
  val timeout: Int = 30
  val maxRetries: Int = 3
  val baseUrl: String = "https://api.example.com"

  def getFullUrl(path: String): String = s"$baseUrl$path"
}
""",
            "ApiClient.scala": """// Initial
class ApiClient {}
""",
        },
        changed_files={
            "ApiClient.scala": """class ApiClient {
  def fetch(path: String): String = {
    val url = Config.getFullUrl(path)
    val timeout = Config.timeout
    s"Fetching $url with timeout $timeout"
  }

  def retry(action: => String): String = {
    var attempts = 0
    while (attempts < Config.maxRetries) {
      attempts += 1
    }
    action
  }
}
""",
        },
        must_include=["ApiClient.scala", "Config.getFullUrl", "Config.maxRetries"],
        commit_message="Add object singleton usage",
    ),
    DiffTestCase(
        name="scala_for_comprehension",
        initial_files={
            "Repository.scala": """case class User(id: String, name: String)
case class Order(id: String, userId: String, total: Double)

class Repository {
  def getUser(id: String): Option[User] = Some(User(id, "John"))
  def getOrders(user: User): Option[List[Order]] = Some(List(Order("o1", user.id, 100.0)))
}
""",
            "OrderService.scala": """// Initial
class OrderService {}
""",
        },
        changed_files={
            "OrderService.scala": """class OrderService(repo: Repository) {
  def getUserOrders(userId: String): Option[List[Order]] = {
    for {
      user <- repo.getUser(userId)
      orders <- repo.getOrders(user)
    } yield orders
  }

  def getTotalForUser(userId: String): Option[Double] = {
    for {
      user <- repo.getUser(userId)
      orders <- repo.getOrders(user)
      total = orders.map(_.total).sum
    } yield total
  }
}
""",
        },
        must_include=["OrderService.scala", "for {", "yield"],
        commit_message="Add for comprehension",
    ),
    DiffTestCase(
        name="scala_pattern_matching",
        initial_files={
            "User.scala": """case class User(name: String, age: Int, email: Option[String])
""",
            "UserValidator.scala": """// Initial
class UserValidator {}
""",
        },
        changed_files={
            "UserValidator.scala": """class UserValidator {
  def validate(user: User): String = user match {
    case User(name, _, _) if name.isEmpty =>
      "Name cannot be empty"
    case User(_, age, _) if age < 0 =>
      "Age cannot be negative"
    case User(name, age, Some(email)) if email.contains("@") =>
      s"Valid user: $name, $age, $email"
    case User(name, age, None) =>
      s"Valid user without email: $name, $age"
    case _ =>
      "Invalid user"
  }

  def extractEmail(user: User): String = user match {
    case User(_, _, Some(email)) => email
    case User(name, _, None) => s"$name@default.com"
  }
}
""",
        },
        must_include=["UserValidator.scala", "match", "case User"],
        commit_message="Add pattern matching",
    ),
    DiffTestCase(
        name="scala_partial_function",
        initial_files={
            "Event.scala": """sealed trait Event
case class UserCreated(name: String) extends Event
case class UserDeleted(id: String) extends Event
case class OrderPlaced(orderId: String, amount: Double) extends Event
""",
            "EventHandler.scala": """// Initial
class EventHandler {}
""",
        },
        changed_files={
            "EventHandler.scala": """class EventHandler {
  val userHandler: PartialFunction[Event, String] = {
    case UserCreated(name) => s"Created user: $name"
    case UserDeleted(id) => s"Deleted user: $id"
  }

  val orderHandler: PartialFunction[Event, String] = {
    case OrderPlaced(id, amount) => s"Order $id: $$$amount"
  }

  val combinedHandler: PartialFunction[Event, String] =
    userHandler orElse orderHandler

  def handle(event: Event): Option[String] = {
    combinedHandler.lift(event)
  }
}
""",
        },
        must_include=["EventHandler.scala", "PartialFunction", "orElse"],
        commit_message="Add partial function",
    ),
    DiffTestCase(
        name="scala_future",
        initial_files={
            "ExpensiveComputation.scala": """object ExpensiveComputation {
  def compute(input: Int): Int = {
    Thread.sleep(100)
    input * 2
  }

  def computeString(input: String): String = {
    Thread.sleep(100)
    input.toUpperCase
  }
}
""",
            "AsyncProcessor.scala": """// Initial
class AsyncProcessor {}
""",
        },
        changed_files={
            "AsyncProcessor.scala": """import scala.concurrent.{Future, ExecutionContext}
import scala.concurrent.ExecutionContext.Implicits.global

class AsyncProcessor {
  def processAsync(input: Int): Future[Int] = Future {
    ExpensiveComputation.compute(input)
  }

  def processMany(inputs: List[Int]): Future[List[Int]] = {
    Future.sequence(inputs.map(i => Future(ExpensiveComputation.compute(i))))
  }

  def processCombined(a: Int, b: String): Future[(Int, String)] = {
    for {
      resultA <- Future(ExpensiveComputation.compute(a))
      resultB <- Future(ExpensiveComputation.computeString(b))
    } yield (resultA, resultB)
  }
}
""",
        },
        must_include=["AsyncProcessor.scala", "Future", "Future.sequence"],
        commit_message="Add Future usage",
    ),
    DiffTestCase(
        name="scala_akka_actor",
        initial_files={
            "Messages.scala": """sealed trait UserMessage
case class CreateUser(name: String) extends UserMessage
case class DeleteUser(id: String) extends UserMessage
case class GetUser(id: String) extends UserMessage
case class UserCreated(id: String, name: String)
""",
            "UserActor.scala": """// Initial
class UserActor {}
""",
        },
        changed_files={
            "UserActor.scala": """import akka.actor.{Actor, ActorLogging, Props}

class UserActor extends Actor with ActorLogging {
  private var users: Map[String, String] = Map.empty

  def receive: Receive = {
    case CreateUser(name) =>
      val id = java.util.UUID.randomUUID().toString
      users = users + (id -> name)
      log.info(s"Created user $id: $name")
      sender() ! UserCreated(id, name)

    case DeleteUser(id) =>
      users = users - id
      log.info(s"Deleted user $id")

    case GetUser(id) =>
      sender() ! users.get(id)
  }
}

object UserActor {
  def props: Props = Props[UserActor]()
}
""",
        },
        must_include=["UserActor.scala", "Actor", "receive: Receive"],
        commit_message="Add Akka actor",
    ),
    DiffTestCase(
        name="scala_play_controller",
        initial_files={
            "routes": """GET     /users/:id        controllers.UserController.getUser(id: Long)
POST    /users            controllers.UserController.createUser()
DELETE  /users/:id        controllers.UserController.deleteUser(id: Long)
""",
            "UserController.scala": """// Initial
class UserController {}
""",
        },
        changed_files={
            "UserController.scala": """import play.api.mvc._
import play.api.libs.json._
import scala.concurrent.{ExecutionContext, Future}

case class User(id: Long, name: String)

class UserController(cc: ControllerComponents)(implicit ec: ExecutionContext)
    extends AbstractController(cc) {

  implicit val userFormat: Format[User] = Json.format[User]

  def getUser(id: Long): Action[AnyContent] = Action.async {
    Future.successful(Ok(Json.toJson(User(id, "John"))))
  }

  def createUser(): Action[JsValue] = Action.async(parse.json) { request =>
    request.body.validate[User].fold(
      errors => Future.successful(BadRequest(Json.obj("error" -> "Invalid JSON"))),
      user => Future.successful(Created(Json.toJson(user)))
    )
  }

  def deleteUser(id: Long): Action[AnyContent] = Action.async {
    Future.successful(NoContent)
  }
}
""",
        },
        must_include=["UserController.scala", "AbstractController", "Action.async"],
        commit_message="Add Play controller",
    ),
    DiffTestCase(
        name="scala_slick_query",
        initial_files={
            "Tables.scala": """import slick.jdbc.PostgresProfile.api._

case class User(id: Long, name: String, age: Int, active: Boolean)

class Users(tag: Tag) extends Table[User](tag, "users") {
  def id = column[Long]("id", O.PrimaryKey, O.AutoInc)
  def name = column[String]("name")
  def age = column[Int]("age")
  def active = column[Boolean]("active")
  def * = (id, name, age, active).mapTo[User]
}

object Tables {
  val users = TableQuery[Users]
}
""",
            "UserRepository.scala": """// Initial
class UserRepository {}
""",
        },
        changed_files={
            "UserRepository.scala": """import slick.jdbc.PostgresProfile.api._
import scala.concurrent.Future

class UserRepository(db: Database) {
  import Tables._

  def findAdults(): Future[Seq[User]] = {
    db.run(users.filter(_.age >= 18).result)
  }

  def findActive(): Future[Seq[User]] = {
    db.run(users.filter(_.active === true).result)
  }

  def findByName(name: String): Future[Option[User]] = {
    db.run(users.filter(_.name === name).result.headOption)
  }

  def countByAge(minAge: Int): Future[Int] = {
    db.run(users.filter(_.age >= minAge).length.result)
  }
}
""",
        },
        must_include=["UserRepository.scala", "db.run", "filter"],
        commit_message="Add Slick query",
    ),
    DiffTestCase(
        name="scala_cats_effect",
        initial_files={
            "Database.scala": """import cats.effect.IO

object Database {
  def connect(): IO[Unit] = IO(println("Connected"))
  def disconnect(): IO[Unit] = IO(println("Disconnected"))
  def query(sql: String): IO[List[String]] = IO(List("result1", "result2"))
}
""",
            "Program.scala": """// Initial
object Program {}
""",
        },
        changed_files={
            "Program.scala": """import cats.effect.{IO, IOApp, ExitCode}
import cats.syntax.all._

object Program extends IOApp {
  def program: IO[Unit] = for {
    _ <- Database.connect()
    results <- Database.query("SELECT * FROM users")
    _ <- IO(results.foreach(println))
    _ <- Database.disconnect()
  } yield ()

  def run(args: List[String]): IO[ExitCode] = {
    program.as(ExitCode.Success)
  }
}
""",
        },
        must_include=["Program.scala", "IOApp", "for {"],
        commit_message="Add Cats Effect IO",
    ),
]

CSHARP_TEST_CASES = [
    DiffTestCase(
        name="csharp_class_inheritance",
        initial_files={
            "Person.cs": """public class Person
{
    public string Name { get; set; }
    public int Age { get; set; }

    public Person(string name, int age)
    {
        Name = name;
        Age = age;
    }
}
""",
            "IWorker.cs": """public interface IWorker
{
    void Work();
    decimal GetSalary();
}
""",
            "Employee.cs": """// Initial
public class Employee { }
""",
        },
        changed_files={
            "Employee.cs": """public class Employee : Person, IWorker
{
    public string Department { get; set; }
    public decimal Salary { get; set; }

    public Employee(string name, int age, string department, decimal salary)
        : base(name, age)
    {
        Department = department;
        Salary = salary;
    }

    public void Work()
    {
        Console.WriteLine($"{Name} is working in {Department}");
    }

    public decimal GetSalary() => Salary;
}
""",
        },
        must_include=["Employee.cs", "Person, IWorker", "Work()"],
        commit_message="Add class inheritance",
    ),
    DiffTestCase(
        name="csharp_nullable_reference",
        initial_files={
            "User.cs": """public class User
{
    public int Id { get; set; }
    public string Name { get; set; }
}
""",
            "UserRepository.cs": """// Initial
class UserRepository { }
""",
        },
        changed_files={
            "UserRepository.cs": """using System.Collections.Generic;

class UserRepository
{
    private readonly Dictionary<int, User> _users = new();

    public User? FindUser(int id)
    {
        return _users.TryGetValue(id, out var user) ? user : null;
    }

    public void Save(User user)
    {
        _users[user.Id] = user;
    }

    public User GetOrCreate(int id, string name)
    {
        var user = FindUser(id);
        if (user is null)
        {
            user = new User { Id = id, Name = name };
            Save(user);
        }
        return user;
    }
}
""",
        },
        must_include=["UserRepository.cs", "User?", "is null"],
        commit_message="Add nullable reference",
    ),
    DiffTestCase(
        name="csharp_pattern_matching",
        initial_files={
            "User.cs": """public class User
{
    public string Name { get; set; }
    public int Age { get; set; }
    public bool IsActive { get; set; }
}
""",
            "Validator.cs": """// Initial
class Validator { }
""",
        },
        changed_files={
            "Validator.cs": """class Validator
{
    public string ValidateUser(object obj)
    {
        return obj switch
        {
            User { Age: < 18 } => "User is too young",
            User { IsActive: false } => "User is not active",
            User { Name: "" or null } => "User name is empty",
            User user => $"Valid user: {user.Name}",
            null => "Object is null",
            _ => "Unknown object"
        };
    }

    public bool IsAdult(object obj)
    {
        if (obj is User { Age: >= 18 } adult)
        {
            Console.WriteLine($"{adult.Name} is an adult");
            return true;
        }
        return false;
    }
}
""",
        },
        must_include=["Validator.cs", "switch", "User { Age:"],
        commit_message="Add pattern matching",
    ),
    DiffTestCase(
        name="csharp_record",
        initial_files={
            "Person.cs": """public record Person(string Name, int Age)
{
    public bool IsAdult => Age >= 18;
}

public record Employee(string Name, int Age, string Department) : Person(Name, Age);
""",
            "Program.cs": """// Initial
class Program { }
""",
        },
        changed_files={
            "Program.cs": """class Program
{
    static void Main()
    {
        var person = new Person("John", 30);
        var updated = person with { Age = 31 };

        var employee = new Employee("Jane", 25, "IT");

        Console.WriteLine(person == new Person("John", 30)); // true
        Console.WriteLine(employee.Department);
    }
}
""",
        },
        must_include=["Program.cs", "with { Age = 31 }"],
        commit_message="Add record usage",
    ),
    DiffTestCase(
        name="csharp_extension_method",
        initial_files={
            "StringExtensions.cs": """public static class StringExtensions
{
    public static bool IsValidEmail(this string s)
    {
        return !string.IsNullOrEmpty(s) && s.Contains("@") && s.Contains(".");
    }

    public static string Truncate(this string s, int maxLength)
    {
        if (string.IsNullOrEmpty(s) || s.Length <= maxLength)
            return s;
        return s.Substring(0, maxLength) + "...";
    }
}
""",
            "Validator.cs": """// Initial
class Validator { }
""",
        },
        changed_files={
            "Validator.cs": """class Validator
{
    public bool ValidateEmail(string email)
    {
        return email.IsValidEmail();
    }

    public string FormatMessage(string message)
    {
        return message.Truncate(100);
    }
}
""",
        },
        must_include=["Validator.cs", "IsValidEmail()", "Truncate(100)"],
        commit_message="Add extension method usage",
    ),
    DiffTestCase(
        name="csharp_linq",
        initial_files={
            "User.cs": """public class User
{
    public int Id { get; set; }
    public string Name { get; set; }
    public int Age { get; set; }
    public bool IsActive { get; set; }
}
""",
            "UserService.cs": """// Initial
class UserService { }
""",
        },
        changed_files={
            "UserService.cs": """using System.Collections.Generic;
using System.Linq;

class UserService
{
    private readonly List<User> _users;

    public UserService(List<User> users)
    {
        _users = users;
    }

    public IEnumerable<User> GetAdults()
    {
        return _users.Where(u => u.Age >= 18);
    }

    public IEnumerable<string> GetActiveUserNames()
    {
        return _users
            .Where(u => u.IsActive)
            .OrderBy(u => u.Name)
            .Select(u => u.Name);
    }

    public double AverageAge()
    {
        return _users.Average(u => u.Age);
    }
}
""",
        },
        must_include=["UserService.cs", "Where(", "Select("],
        commit_message="Add LINQ usage",
    ),
    DiffTestCase(
        name="csharp_async_await",
        initial_files={
            "User.cs": """public class User
{
    public int Id { get; set; }
    public string Name { get; set; }
}
""",
            "UserApi.cs": """// Initial
class UserApi { }
""",
        },
        changed_files={
            "UserApi.cs": """using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;

class UserApi
{
    private readonly HttpClient _client;

    public UserApi(HttpClient client)
    {
        _client = client;
    }

    public async Task<User> GetUserAsync(int id)
    {
        var response = await _client.GetAsync($"/api/users/{id}");
        response.EnsureSuccessStatusCode();

        var json = await response.Content.ReadAsStringAsync();
        return JsonSerializer.Deserialize<User>(json);
    }

    public async Task<IEnumerable<User>> GetAllUsersAsync()
    {
        var response = await _client.GetAsync("/api/users");
        var json = await response.Content.ReadAsStringAsync();
        return JsonSerializer.Deserialize<IEnumerable<User>>(json);
    }
}
""",
        },
        must_include=["UserApi.cs", "async Task<User>", "await"],
        commit_message="Add async/await",
    ),
    DiffTestCase(
        name="csharp_dependency_injection",
        initial_files={
            "IUserService.cs": """public interface IUserService
{
    User GetUser(int id);
    void CreateUser(User user);
}
""",
            "UserService.cs": """public class UserService : IUserService
{
    public User GetUser(int id)
    {
        return new User { Id = id, Name = "User" };
    }

    public void CreateUser(User user)
    {
        // Save user
    }
}
""",
            "Startup.cs": """// Initial
class Startup { }
""",
        },
        changed_files={
            "Startup.cs": """using Microsoft.Extensions.DependencyInjection;

class Startup
{
    public void ConfigureServices(IServiceCollection services)
    {
        services.AddScoped<IUserService, UserService>();
    }
}
""",
        },
        must_include=["Startup.cs", "AddScoped", "IUserService, UserService"],
        commit_message="Add dependency injection",
    ),
    DiffTestCase(
        name="csharp_attribute",
        initial_files={
            "User.cs": """public class User
{
    public int Id { get; set; }
    public string Name { get; set; }
}
""",
            "UsersController.cs": """// Initial
class UsersController { }
""",
        },
        changed_files={
            "UsersController.cs": """using Microsoft.AspNetCore.Mvc;

[ApiController]
[Route("api/[controller]")]
public class UsersController : ControllerBase
{
    [HttpGet("{id}")]
    public ActionResult<User> GetUser(int id)
    {
        return new User { Id = id, Name = "Test" };
    }

    [HttpPost]
    public ActionResult<User> CreateUser([FromBody] User user)
    {
        return CreatedAtAction(nameof(GetUser), new { id = user.Id }, user);
    }
}
""",
        },
        must_include=["UsersController.cs", "[ApiController]", "[HttpGet"],
        commit_message="Add attribute",
    ),
    DiffTestCase(
        name="csharp_entity_framework",
        initial_files={
            "User.cs": """public class User
{
    public int Id { get; set; }
    public string Name { get; set; }
    public string Email { get; set; }
}
""",
            "AppDbContext.cs": """// Initial
class AppDbContext { }
""",
        },
        changed_files={
            "AppDbContext.cs": """using Microsoft.EntityFrameworkCore;

public class AppDbContext : DbContext
{
    public DbSet<User> Users { get; set; }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<User>(entity =>
        {
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Email).IsRequired();
            entity.HasIndex(e => e.Email).IsUnique();
        });
    }
}
""",
        },
        must_include=["AppDbContext.cs", "DbContext", "OnModelCreating"],
        commit_message="Add Entity Framework",
    ),
    DiffTestCase(
        name="csharp_fluent_validation",
        initial_files={
            "UserDto.cs": """public class UserDto
{
    public string Name { get; set; }
    public string Email { get; set; }
    public int Age { get; set; }
}
""",
            "UserValidator.cs": """// Initial
class UserValidator { }
""",
        },
        changed_files={
            "UserValidator.cs": """using FluentValidation;

public class UserValidator : AbstractValidator<UserDto>
{
    public UserValidator()
    {
        RuleFor(x => x.Name)
            .NotEmpty()
            .MaximumLength(100);

        RuleFor(x => x.Email)
            .NotEmpty()
            .EmailAddress();

        RuleFor(x => x.Age)
            .GreaterThan(0)
            .LessThan(150);
    }
}
""",
        },
        must_include=["UserValidator.cs", "AbstractValidator", "RuleFor"],
        commit_message="Add FluentValidation",
    ),
    DiffTestCase(
        name="csharp_mediatr",
        initial_files={
            "CreateUser.cs": """using MediatR;

public class CreateUser : IRequest<User>
{
    public string Name { get; set; }
    public string Email { get; set; }
}
""",
            "CreateUserHandler.cs": """// Initial
class CreateUserHandler { }
""",
        },
        changed_files={
            "CreateUserHandler.cs": """using MediatR;
using System.Threading;
using System.Threading.Tasks;

public class CreateUserHandler : IRequestHandler<CreateUser, User>
{
    private readonly IUserRepository _repository;

    public CreateUserHandler(IUserRepository repository)
    {
        _repository = repository;
    }

    public async Task<User> Handle(CreateUser request, CancellationToken cancellationToken)
    {
        var user = new User
        {
            Name = request.Name,
            Email = request.Email
        };

        await _repository.AddAsync(user, cancellationToken);
        return user;
    }
}
""",
        },
        must_include=["CreateUserHandler.cs", "IRequestHandler", "Handle"],
        commit_message="Add MediatR handler",
    ),
]

CPP_TEST_CASES = [
    DiffTestCase(
        name="cpp_function_pointer",
        initial_files={
            "handlers.h": """#pragma once
void onSuccess(int code);
void onError(int code);
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
        must_include=["main.cpp", "void (*callback)(int)", "execute"],
        commit_message="Add function pointer usage",
    ),
    DiffTestCase(
        name="cpp_unique_ptr",
        initial_files={
            "resource.h": """#pragma once
#include <string>

class Resource {
public:
    std::string id;
    Resource(const std::string& id) : id(id) {}
    void use() {}
};
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
        must_include=["manager.cpp", "unique_ptr", "make_unique"],
        commit_message="Add unique_ptr usage",
    ),
    DiffTestCase(
        name="cpp_shared_ptr",
        initial_files={
            "data.h": """#pragma once

struct Data {
    int value;
    Data(int v) : value(v) {}
};
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
        must_include=["cache.cpp", "shared_ptr", "make_shared"],
        commit_message="Add shared_ptr usage",
    ),
    DiffTestCase(
        name="cpp_move_semantics",
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
        must_include=["processor.cpp", "std::move", "createBuffer"],
        commit_message="Add move semantics",
    ),
    DiffTestCase(
        name="cpp_raii",
        initial_files={
            "mutex.h": """#pragma once

class Mutex {
public:
    void lock() {}
    void unlock() {}
};
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
        must_include=["guard.cpp", "LockGuard", "~LockGuard"],
        commit_message="Add RAII pattern",
    ),
    DiffTestCase(
        name="cpp_class_template",
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
        must_include=["main.cpp", "Container<int>", "Container<std::string>"],
        commit_message="Add template instantiation",
    ),
    DiffTestCase(
        name="cpp_variadic_template",
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
        must_include=["app.cpp", 'log("Starting"'],
        commit_message="Add variadic template usage",
    ),
    DiffTestCase(
        name="cpp_virtual_function",
        initial_files={
            "drawable.h": """#pragma once

class Drawable {
public:
    virtual ~Drawable() = default;
    virtual void draw() = 0;
    virtual void resize(int w, int h) = 0;
};
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
        must_include=["widget.cpp", "Button", "override"],
        commit_message="Add virtual function implementation",
    ),
    DiffTestCase(
        name="cpp_multiple_inheritance",
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
        must_include=["widget.cpp", "public Drawable, public Clickable"],
        commit_message="Add multiple inheritance",
    ),
    DiffTestCase(
        name="cpp_operator_overloading",
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
        must_include=["physics.cpp", "pos + vel * dt", "position +="],
        commit_message="Add operator overloading usage",
    ),
    DiffTestCase(
        name="cpp_namespace",
        initial_files={
            "utils.h": """#pragma once
#include <string>

namespace myapp::utils {

std::string trim(const std::string& s);
std::string toUpper(const std::string& s);

}
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
        must_include=["app.cpp", "myapp::utils", "trim(input)"],
        commit_message="Add namespace usage",
    ),
]

SWIFT_TEST_CASES = [
    DiffTestCase(
        name="swift_protocol_conformance",
        initial_files={
            "User.swift": """struct User: Codable, Equatable {
    let id: String
    let name: String
    let email: String
}
""",
            "UserService.swift": """// Initial
class UserService {}
""",
        },
        changed_files={
            "UserService.swift": """import Foundation

class UserService {
    func encode(user: User) throws -> Data {
        let encoder = JSONEncoder()
        return try encoder.encode(user)
    }

    func decode(data: Data) throws -> User {
        let decoder = JSONDecoder()
        return try decoder.decode(User.self, from: data)
    }
}
""",
        },
        must_include=["UserService.swift", "JSONEncoder", "JSONDecoder"],
        commit_message="Add protocol conformance usage",
    ),
    DiffTestCase(
        name="swift_extension",
        initial_files={
            "StringExtensions.swift": """extension String {
    func isValidEmail() -> Bool {
        let pattern = "[A-Z0-9a-z._%+-]+@[A-Za-z0-9.-]+\\\\.[A-Za-z]{2,}"
        return self.range(of: pattern, options: .regularExpression) != nil
    }

    var trimmed: String {
        trimmingCharacters(in: .whitespacesAndNewlines)
    }
}
""",
            "Validator.swift": """// Initial
struct Validator {}
""",
        },
        changed_files={
            "Validator.swift": """struct Validator {
    func validateEmail(_ email: String) -> Bool {
        return email.trimmed.isValidEmail()
    }
}
""",
        },
        must_include=["Validator.swift", "trimmed", "isValidEmail()"],
        commit_message="Add extension usage",
    ),
    DiffTestCase(
        name="swift_optional_binding",
        initial_files={
            "UserRepository.swift": """struct User {
    let id: String
    let name: String
}

class UserRepository {
    private var users: [String: User] = [:]

    func fetchUser(id: String) -> User? {
        return users[id]
    }

    func save(user: User) {
        users[user.id] = user
    }
}
""",
            "UserController.swift": """// Initial
class UserController {}
""",
        },
        changed_files={
            "UserController.swift": """class UserController {
    let repository = UserRepository()

    func showUser(id: String) -> String {
        if let user = repository.fetchUser(id: id) {
            return "User: \\(user.name)"
        } else {
            return "User not found"
        }
    }
}
""",
        },
        must_include=["UserController.swift", "if let user ="],
        commit_message="Add optional binding",
    ),
    DiffTestCase(
        name="swift_guard_statement",
        initial_files={
            "Response.swift": """struct Response {
    let data: Data?
    let error: Error?
    let statusCode: Int
}
""",
            "NetworkHandler.swift": """// Initial
struct NetworkHandler {}
""",
        },
        changed_files={
            "NetworkHandler.swift": """import Foundation

struct NetworkHandler {
    func handleResponse(_ response: Response) -> Data? {
        guard response.error == nil else {
            print("Error: \\(response.error!)")
            return nil
        }

        guard response.statusCode == 200 else {
            print("Invalid status: \\(response.statusCode)")
            return nil
        }

        guard let data = response.data else {
            print("No data")
            return nil
        }

        return data
    }
}
""",
        },
        must_include=["NetworkHandler.swift", "guard", "else {"],
        commit_message="Add guard statement",
    ),
    DiffTestCase(
        name="swift_result_type",
        initial_files={
            "APIError.swift": """enum APIError: Error {
    case networkError
    case invalidResponse
    case decodingError
}
""",
            "DataLoader.swift": """// Initial
struct DataLoader {}
""",
        },
        changed_files={
            "DataLoader.swift": """import Foundation

struct DataLoader {
    func load(from url: URL) -> Result<Data, APIError> {
        // Simulated loading
        guard let data = "test".data(using: .utf8) else {
            return .failure(.invalidResponse)
        }
        return .success(data)
    }

    func process(url: URL) {
        let result = load(from: url)
        switch result {
        case .success(let data):
            print("Loaded \\(data.count) bytes")
        case .failure(let error):
            print("Error: \\(error)")
        }
    }
}
""",
        },
        must_include=["DataLoader.swift", "Result<Data, APIError>", ".success", ".failure"],
        commit_message="Add result type",
    ),
    DiffTestCase(
        name="swift_async_await",
        initial_files={
            "User.swift": """struct User: Codable {
    let id: String
    let name: String
}
""",
            "UserAPI.swift": """// Initial
class UserAPI {}
""",
        },
        changed_files={
            "UserAPI.swift": """import Foundation

class UserAPI {
    func fetchUsers() async throws -> [User] {
        let url = URL(string: "https://api.example.com/users")!
        let (data, _) = try await URLSession.shared.data(from: url)
        return try JSONDecoder().decode([User].self, from: data)
    }

    func getUser(id: String) async throws -> User {
        let users = try await fetchUsers()
        guard let user = users.first(where: { $0.id == id }) else {
            throw NSError(domain: "UserAPI", code: 404)
        }
        return user
    }
}
""",
        },
        must_include=["UserAPI.swift", "async throws", "await"],
        commit_message="Add async/await",
    ),
    DiffTestCase(
        name="swift_actor",
        initial_files={
            "Item.swift": """struct Item: Identifiable {
    let id: String
    let name: String
}
""",
            "DataStore.swift": """// Initial
class DataStore {}
""",
        },
        changed_files={
            "DataStore.swift": """actor DataStore {
    private var items: [Item] = []

    func add(_ item: Item) {
        items.append(item)
    }

    func remove(id: String) {
        items.removeAll { $0.id == id }
    }

    func getAll() -> [Item] {
        return items
    }

    var count: Int {
        items.count
    }
}
""",
        },
        must_include=["DataStore.swift", "actor DataStore"],
        commit_message="Add actor",
    ),
    DiffTestCase(
        name="swift_swiftui_view",
        initial_files={
            "User.swift": """struct User: Identifiable {
    let id: String
    let name: String
    let email: String
}
""",
            "UserView.swift": """// Initial
import SwiftUI
struct UserView: View {
    var body: some View { Text("") }
}
""",
        },
        changed_files={
            "UserView.swift": """import SwiftUI

struct UserView: View {
    let user: User

    var body: some View {
        VStack(alignment: .leading) {
            Text(user.name)
                .font(.headline)
            Text(user.email)
                .font(.subheadline)
                .foregroundColor(.gray)
        }
    }
}
""",
        },
        must_include=["UserView.swift", "VStack", "Text(user.name)"],
        commit_message="Add SwiftUI view",
    ),
    DiffTestCase(
        name="swift_state",
        initial_files={
            "ContentView.swift": """// Initial
import SwiftUI
struct ContentView: View {
    var body: some View { Text("") }
}
""",
        },
        changed_files={
            "ContentView.swift": """import SwiftUI

struct ContentView: View {
    @State private var isLoading = false
    @State private var items: [String] = []

    var body: some View {
        VStack {
            if isLoading {
                ProgressView()
            } else {
                List(items, id: \\.self) { item in
                    Text(item)
                }
            }
            Button("Load") {
                isLoading = true
            }
        }
    }
}
""",
        },
        must_include=["ContentView.swift", "@State", "isLoading"],
        commit_message="Add @State",
    ),
    DiffTestCase(
        name="swift_observed_object",
        initial_files={
            "UserViewModel.swift": """import Combine

class UserViewModel: ObservableObject {
    @Published var name = ""
    @Published var email = ""
    @Published var isValid = false

    func validate() {
        isValid = !name.isEmpty && email.contains("@")
    }
}
""",
            "UserFormView.swift": """// Initial
import SwiftUI
struct UserFormView: View {
    var body: some View { Text("") }
}
""",
        },
        changed_files={
            "UserFormView.swift": """import SwiftUI

struct UserFormView: View {
    @ObservedObject var viewModel: UserViewModel

    var body: some View {
        Form {
            TextField("Name", text: $viewModel.name)
            TextField("Email", text: $viewModel.email)
            Button("Submit") {
                viewModel.validate()
            }
            .disabled(!viewModel.isValid)
        }
        .onChange(of: viewModel.name) { _ in viewModel.validate() }
        .onChange(of: viewModel.email) { _ in viewModel.validate() }
    }
}
""",
        },
        must_include=["UserFormView.swift", "@ObservedObject", "$viewModel.name"],
        commit_message="Add @ObservedObject",
    ),
    DiffTestCase(
        name="swift_environment_object",
        initial_files={
            "AppState.swift": """import Combine

class AppState: ObservableObject {
    @Published var currentUser: String?
    @Published var isLoggedIn = false

    func login(username: String) {
        currentUser = username
        isLoggedIn = true
    }

    func logout() {
        currentUser = nil
        isLoggedIn = false
    }
}
""",
            "ProfileView.swift": """// Initial
import SwiftUI
struct ProfileView: View {
    var body: some View { Text("") }
}
""",
        },
        changed_files={
            "ProfileView.swift": """import SwiftUI

struct ProfileView: View {
    @EnvironmentObject var appState: AppState

    var body: some View {
        VStack {
            if appState.isLoggedIn {
                Text("Welcome, \\(appState.currentUser ?? "")")
                Button("Logout") {
                    appState.logout()
                }
            } else {
                Text("Please log in")
            }
        }
    }
}
""",
        },
        must_include=["ProfileView.swift", "@EnvironmentObject", "appState.isLoggedIn"],
        commit_message="Add @EnvironmentObject",
    ),
    DiffTestCase(
        name="swift_codable",
        initial_files={
            "User.swift": """struct User: Codable {
    let id: String
    let name: String
    let email: String
}
""",
            "APIResponse.swift": """struct APIResponse<T: Codable>: Decodable {
    let data: T
    let status: String
    let timestamp: Date
}
""",
            "APIClient.swift": """// Initial
class APIClient {}
""",
        },
        changed_files={
            "APIClient.swift": """import Foundation

class APIClient {
    func fetchUsers(completion: @escaping (Result<APIResponse<[User]>, Error>) -> Void) {
        let url = URL(string: "https://api.example.com/users")!
        URLSession.shared.dataTask(with: url) { data, _, error in
            if let error = error {
                completion(.failure(error))
                return
            }
            guard let data = data else { return }
            do {
                let decoder = JSONDecoder()
                decoder.dateDecodingStrategy = .iso8601
                let response = try decoder.decode(APIResponse<[User]>.self, from: data)
                completion(.success(response))
            } catch {
                completion(.failure(error))
            }
        }.resume()
    }
}
""",
        },
        must_include=["APIClient.swift", "JSONDecoder", "APIResponse<[User]>"],
        commit_message="Add Codable decoding",
    ),
    DiffTestCase(
        name="swift_error_handling",
        initial_files={
            "AppError.swift": """enum AppError: Error {
    case networkError(String)
    case validationError(String)
    case notFound
    case unauthorized

    var localizedDescription: String {
        switch self {
        case .networkError(let message):
            return "Network error: \\(message)"
        case .validationError(let message):
            return "Validation error: \\(message)"
        case .notFound:
            return "Resource not found"
        case .unauthorized:
            return "Unauthorized access"
        }
    }
}
""",
            "UserService.swift": """// Initial
class UserService {}
""",
        },
        changed_files={
            "UserService.swift": """class UserService {
    func fetchUser(id: String) throws -> User {
        guard !id.isEmpty else {
            throw AppError.validationError("ID cannot be empty")
        }

        guard let user = findUser(id: id) else {
            throw AppError.notFound
        }

        return user
    }

    func handleError(_ error: AppError) {
        switch error {
        case .networkError(let msg):
            print("Network issue: \\(msg)")
        case .validationError(let msg):
            print("Invalid input: \\(msg)")
        case .notFound:
            print("User not found")
        case .unauthorized:
            print("Please login")
        }
    }

    private func findUser(id: String) -> User? {
        return nil
    }
}

struct User {
    let id: String
    let name: String
}
""",
        },
        must_include=["UserService.swift", "throw AppError", "handleError"],
        commit_message="Add error handling",
    ),
    DiffTestCase(
        name="swift_generic_constraint",
        initial_files={
            "Repository.swift": """protocol Repository {
    associatedtype Entity
    func save(_ entity: Entity)
    func find(id: String) -> Entity?
    func delete(id: String)
}
""",
            "CacheService.swift": """// Initial
class CacheService {}
""",
        },
        changed_files={
            "CacheService.swift": """class CacheService<T: Comparable & Hashable> {
    private var cache: [String: T] = [:]

    func store(_ value: T, forKey key: String) {
        cache[key] = value
    }

    func retrieve(forKey key: String) -> T? {
        return cache[key]
    }

    func process<U: Numeric>(_ items: [U]) -> U {
        return items.reduce(0, +)
    }

    func filter<C: Collection>(items: C, predicate: (C.Element) -> Bool) -> [C.Element] where C.Element: Comparable {
        return items.filter(predicate).sorted()
    }
}
""",
        },
        must_include=["CacheService.swift", "T: Comparable & Hashable", "where C.Element: Comparable"],
        commit_message="Add generic constraints",
    ),
]

COMPILED_LANG_TEST_CASES = (
    JAVA_TEST_CASES + KOTLIN_TEST_CASES + SCALA_TEST_CASES + CSHARP_TEST_CASES + CPP_TEST_CASES + SWIFT_TEST_CASES
)


@pytest.fixture
def diff_test_runner(tmp_path):
    return DiffTestRunner(tmp_path)


@pytest.mark.parametrize("case", COMPILED_LANG_TEST_CASES, ids=lambda c: c.name)
def test_compiled_language_cases(diff_test_runner: DiffTestRunner, case: DiffTestCase):
    context = diff_test_runner.run_test_case(case)
    diff_test_runner.verify_assertions(context, case)
