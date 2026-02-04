---
name: springboot-patterns
description: Spring Boot patterns including JPA repositories, REST controllers, layered services, and configuration
---

# Spring Boot Patterns

## Layered Architecture

```
src/main/java/com/example/app/
  config/          # @Configuration beans
  controller/      # @RestController (thin, delegates to service)
  service/         # @Service (business logic)
  repository/      # @Repository (data access via JPA)
  model/
    entity/        # @Entity JPA classes
    dto/           # Request/response DTOs
    mapper/        # MapStruct or manual mapping
  exception/       # @ControllerAdvice, custom exceptions
  security/        # SecurityFilterChain, JWT filters
```

Controllers handle HTTP concerns. Services contain business logic. Repositories handle persistence.

## REST Controller

```java
@RestController
@RequestMapping("/api/v1/orders")
@RequiredArgsConstructor
public class OrderController {

    private final OrderService orderService;

    @GetMapping
    public Page<OrderResponse> list(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        return orderService.findAll(PageRequest.of(page, size));
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public OrderResponse create(@Valid @RequestBody CreateOrderRequest request) {
        return orderService.create(request);
    }

    @GetMapping("/{id}")
    public OrderResponse getById(@PathVariable UUID id) {
        return orderService.findById(id);
    }
}
```

## JPA Entity and Repository

```java
@Entity
@Table(name = "orders")
@Getter @Setter @NoArgsConstructor
public class Order {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "customer_id", nullable = false)
    private Customer customer;

    @OneToMany(mappedBy = "order", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<OrderItem> items = new ArrayList<>();

    @Enumerated(EnumType.STRING)
    private OrderStatus status = OrderStatus.PENDING;

    @CreationTimestamp
    private Instant createdAt;
}

public interface OrderRepository extends JpaRepository<Order, UUID> {
    @Query("SELECT o FROM Order o JOIN FETCH o.items WHERE o.customer.id = :customerId")
    List<Order> findByCustomerWithItems(@Param("customerId") UUID customerId);

    @EntityGraph(attributePaths = {"customer", "items"})
    Optional<Order> findWithDetailsById(UUID id);
}
```

## Service Layer

```java
@Service
@Transactional(readOnly = true)
@RequiredArgsConstructor
public class OrderService {

    private final OrderRepository orderRepository;
    private final OrderMapper orderMapper;
    private final EventPublisher eventPublisher;

    public OrderResponse findById(UUID id) {
        Order order = orderRepository.findWithDetailsById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Order", id));
        return orderMapper.toResponse(order);
    }

    @Transactional
    public OrderResponse create(CreateOrderRequest request) {
        Order order = orderMapper.toEntity(request);
        order = orderRepository.save(order);
        eventPublisher.publish(new OrderCreatedEvent(order.getId()));
        return orderMapper.toResponse(order);
    }
}
```

## Global Exception Handler

```java
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(ResourceNotFoundException.class)
    @ResponseStatus(HttpStatus.NOT_FOUND)
    public ProblemDetail handleNotFound(ResourceNotFoundException ex) {
        return ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, ex.getMessage());
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public ProblemDetail handleValidation(MethodArgumentNotValidException ex) {
        ProblemDetail detail = ProblemDetail.forStatus(HttpStatus.BAD_REQUEST);
        Map<String, String> errors = ex.getFieldErrors().stream()
                .collect(Collectors.toMap(FieldError::getField, FieldError::getDefaultMessage));
        detail.setProperty("errors", errors);
        return detail;
    }
}
```

## Anti-Patterns

- Injecting repositories directly into controllers (bypassing service layer)
- Using `FetchType.EAGER` on entity relationships by default
- Returning JPA entities directly from controllers instead of DTOs
- Missing `@Transactional(readOnly = true)` on read-only service methods
- Catching generic `Exception` instead of specific types
- Hardcoding configuration values instead of using `@Value` or `@ConfigurationProperties`

## Checklist

- [ ] Controllers are thin and delegate to services
- [ ] All JPA relationships use `FetchType.LAZY` by default
- [ ] DTOs used for request/response, never raw entities
- [ ] `@Transactional` applied at service level with correct read/write scoping
- [ ] Validation annotations (`@Valid`, `@NotNull`, `@Size`) on request DTOs
- [ ] Global exception handler returns `ProblemDetail` (RFC 7807)
- [ ] Entity graphs or `JOIN FETCH` used to avoid N+1 queries
- [ ] Integration tests use `@SpringBootTest` with test containers
