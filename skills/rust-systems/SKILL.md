---
name: rust-systems
description: Rust systems programming patterns including ownership, traits, async runtime, error handling, and unsafe guidelines
---

# Rust Systems

## Ownership and Borrowing

```rust
fn process_data(data: &[u8]) -> Vec<u8> {
    data.iter().map(|b| b.wrapping_add(1)).collect()
}

fn modify_in_place(data: &mut Vec<u8>) {
    data.retain(|b| *b != 0);
    data.sort_unstable();
}

fn take_ownership(data: Vec<u8>) -> Vec<u8> {
    let mut result = data;
    result.push(0xFF);
    result
}

fn main() {
    let data = vec![1, 2, 3, 0, 4];
    let processed = process_data(&data);     // borrow: data still usable
    let mut owned = take_ownership(data);     // move: data no longer usable
    modify_in_place(&mut owned);              // mutable borrow
}
```

Prefer borrowing (`&T`, `&mut T`) over ownership transfer. Use `Clone` only when necessary.

## Error Handling

```rust
use thiserror::Error;

#[derive(Error, Debug)]
pub enum AppError {
    #[error("database error: {0}")]
    Database(#[from] sqlx::Error),

    #[error("not found: {resource} with id {id}")]
    NotFound { resource: &'static str, id: String },

    #[error("validation failed: {0}")]
    Validation(String),
}

type Result<T> = std::result::Result<T, AppError>;

async fn get_user(pool: &PgPool, id: &str) -> Result<User> {
    sqlx::query_as::<_, User>("SELECT * FROM users WHERE id = $1")
        .bind(id)
        .fetch_optional(pool)
        .await?
        .ok_or_else(|| AppError::NotFound {
            resource: "User",
            id: id.to_string(),
        })
}
```

Use `thiserror` for library errors, `anyhow` for application-level errors. Avoid `.unwrap()` in production code.

## Traits and Generics

```rust
trait Repository {
    type Item;
    type Error;

    async fn find_by_id(&self, id: &str) -> std::result::Result<Option<Self::Item>, Self::Error>;
    async fn save(&self, item: &Self::Item) -> std::result::Result<(), Self::Error>;
}

struct PgUserRepo {
    pool: PgPool,
}

impl Repository for PgUserRepo {
    type Item = User;
    type Error = AppError;

    async fn find_by_id(&self, id: &str) -> Result<Option<User>> {
        let user = sqlx::query_as::<_, User>("SELECT * FROM users WHERE id = $1")
            .bind(id)
            .fetch_optional(&self.pool)
            .await?;
        Ok(user)
    }

    async fn save(&self, user: &User) -> Result<()> {
        sqlx::query("INSERT INTO users (id, name, email) VALUES ($1, $2, $3)")
            .bind(&user.id)
            .bind(&user.name)
            .bind(&user.email)
            .execute(&self.pool)
            .await?;
        Ok(())
    }
}
```

## Async Patterns

```rust
use tokio::sync::Semaphore;
use futures::stream::{self, StreamExt};

async fn fetch_all(urls: Vec<String>, max_concurrent: usize) -> Vec<Result<String>> {
    let semaphore = Arc::new(Semaphore::new(max_concurrent));

    stream::iter(urls)
        .map(|url| {
            let sem = semaphore.clone();
            async move {
                let _permit = sem.acquire().await.unwrap();
                reqwest::get(&url).await?.text().await.map_err(Into::into)
            }
        })
        .buffer_unordered(max_concurrent)
        .collect()
        .await
}

async fn graceful_shutdown(handle: tokio::runtime::Handle) {
    let ctrl_c = tokio::signal::ctrl_c();
    ctrl_c.await.expect("Failed to listen for Ctrl+C");
    handle.shutdown_timeout(std::time::Duration::from_secs(30));
}
```

## Builder Pattern

```rust
pub struct ServerConfig {
    host: String,
    port: u16,
    workers: usize,
    tls: bool,
}

pub struct ServerConfigBuilder {
    host: String,
    port: u16,
    workers: usize,
    tls: bool,
}

impl ServerConfigBuilder {
    pub fn new() -> Self {
        Self { host: "0.0.0.0".into(), port: 8080, workers: 4, tls: false }
    }

    pub fn host(mut self, host: impl Into<String>) -> Self { self.host = host.into(); self }
    pub fn port(mut self, port: u16) -> Self { self.port = port; self }
    pub fn workers(mut self, n: usize) -> Self { self.workers = n; self }
    pub fn tls(mut self, enabled: bool) -> Self { self.tls = enabled; self }

    pub fn build(self) -> ServerConfig {
        ServerConfig { host: self.host, port: self.port, workers: self.workers, tls: self.tls }
    }
}
```

## Anti-Patterns

- Using `.unwrap()` or `.expect()` in library code
- Cloning data unnecessarily instead of borrowing
- Holding a `MutexGuard` across `.await` points (causes deadlocks)
- Using `Arc<Mutex<Vec<T>>>` when a channel would be more appropriate
- Writing `unsafe` without documenting invariants
- Not using `#[must_use]` on Result-returning functions

## Checklist

- [ ] Error types defined with `thiserror` and `?` operator used for propagation
- [ ] No `.unwrap()` in production paths
- [ ] Ownership model minimizes cloning
- [ ] Async code uses bounded concurrency (semaphores or `buffer_unordered`)
- [ ] Traits used for abstraction and testability
- [ ] `unsafe` blocks have documented safety invariants
- [ ] Builder pattern used for complex configuration structs
- [ ] Clippy lints enabled and warnings addressed
