---
name: Code Migration Patterns
description: Migration patterns for transforming codebases across languages, frameworks, and architectures - supporting framework upgrades, cross-language migration, architecture decoupling, type system migration, and database modernization
---

# Code Migration Skill

This skill provides comprehensive migration patterns for three categories: **Framework Upgrades**, **Cross-Language Migration**, and **Architecture Transformation**.

## Migration Categories

### 1. Framework/Package Upgrades (Project 1)
Upgrade dependencies while maintaining functionality and adding test coverage.

### 2. Cross-Language Migration (Project 2, 3)
Translate code from one language to another (Python→Go, JS→TypeScript, etc.).

### 3. Architecture Transformation (Project 2)
Restructure applications (MVC→Decoupled, Monolith→Microservices).

### 4. Type System Migration (Project 3)
Migrate from weakly-typed to strongly-typed languages.

### 5. Database Modernization (Project 3)
Convert ORM/query builders to RAW SQL with proper testing.

---

## Category 1: Framework Upgrade Patterns

### Pattern: Dependency Version Upgrade

**Before (Old Version):**
```python
# requirements.txt
flask==1.1.2
sqlalchemy==1.3.20
pytest==5.4.3

# app.py
from flask import Flask, jsonify
app = Flask(__name__)

@app.route('/api/data')
def get_data():
    return jsonify({'status': 'ok'})
```

**Migration Steps:**
1. Check breaking changes in changelog
2. Update version constraints
3. Run tests to identify incompatibilities
4. Update deprecated API calls
5. Add new tests for new features

**After (New Version):**
```python
# requirements.txt
flask==3.0.0
sqlalchemy==2.0.23
pytest==8.0.0

# app.py  
from flask import Flask, jsonify
app = Flask(__name__)

@app.route('/api/data')
def get_data():
    # Updated for Flask 3.x compatibility
    return jsonify({'status': 'ok'})

# tests/test_api.py (NEW TEST)
def test_get_data():
    client = app.test_client()
    response = client.get('/api/data')
    assert response.status_code == 200
    assert response.json == {'status': 'ok'}
```

**Metrics:**
- Dependencies upgraded: 3
- Breaking changes handled: 2
- Test coverage added: 15%

### Pattern: Test Generation for Uncovered Code

**Before (No Tests):**
```python
def calculate_discount(price, customer_type):
    if customer_type == 'premium':
        return price * 0.80
    elif customer_type == 'regular':
        return price * 0.95
    return price
```

**After (With Tests):**
```python
# Original function unchanged
def calculate_discount(price, customer_type):
    if customer_type == 'premium':
        return price * 0.80
    elif customer_type == 'regular':
        return price * 0.95
    return price

# tests/test_discount.py (NEW)
import pytest

def test_premium_discount():
    assert calculate_discount(100, 'premium') == 80.0

def test_regular_discount():
    assert calculate_discount(100, 'regular') == 95.0

def test_no_discount():
    assert calculate_discount(100, 'guest') == 100.0

def test_edge_case_zero_price():
    assert calculate_discount(0, 'premium') == 0.0
```

**Metrics:**
- Test coverage: 0% → 100%
- Edge cases covered: 4

---

## Category 2: Cross-Language Migration Patterns

### Pattern: Python → Go (Basic Syntax)

**Python Code:**
```python
def process_users(users):
    result = []
    for user in users:
        if user.is_active and user.age >= 18:
            result.append({
                'name': user.name,
                'email': user.email,
            })
    return result
```

**Go Code:**
```go
type User struct {
    Name     string
    Email    string
    Age      int
    IsActive bool
}

type UserInfo struct {
    Name  string `json:"name"`
    Email string `json:"email"`
}

func ProcessUsers(users []User) []UserInfo {
    result := make([]UserInfo, 0)
    for _, user := range users {
        if user.IsActive && user.Age >= 18 {
            result = append(result, UserInfo{
                Name:  user.Name,
                Email: user.Email,
            })
        }
    }
    return result
}
```

**Key Translations:**
- `def` → `func`
- `for x in list` → `for _, x := range list`
- `if condition:` → `if condition {`
- `dict` → `struct`
- Type annotations required in Go

### Pattern: Python Flask → Go Fiber (API Endpoint)

**Python Flask:**
```python
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Not found'}), 404
    return jsonify({
        'id': user.id,
        'name': user.name,
    })
```

**Go Fiber:**
```go
package main

import (
    "github.com/gofiber/fiber/v2"
    "strconv"
)

type User struct {
    ID   int    `json:"id"`
    Name string `json:"name"`
}

func setupRoutes(app *fiber.App) {
    app.Get("/api/users/:user_id", getUser)
}

func getUser(c *fiber.Ctx) error {
    userID, err := strconv.Atoi(c.Params("user_id"))
    if err != nil {
        return c.Status(400).JSON(fiber.Map{
            "error": "Invalid user ID",
        })
    }
    
    user, err := findUserByID(userID)
    if err != nil {
        return c.Status(404).JSON(fiber.Map{
            "error": "Not found",
        })
    }
    
    return c.JSON(user)
}
```

**Key Translations:**
- Flask decorator → Fiber route registration
- `jsonify()` → `c.JSON()`
- Error handling explicit in Go
- Type-safe parameters

### Pattern: JavaScript → TypeScript (Type Annotations)

**JavaScript:**
```javascript
function calculateTotal(items) {
    return items.reduce((sum, item) => {
        return sum + (item.price * item.quantity);
    }, 0);
}

const cart = [
    { name: 'Apple', price: 1.50, quantity: 3 },
    { name: 'Bread', price: 2.00, quantity: 1 }
];
```

**TypeScript:**
```typescript
interface CartItem {
    name: string;
    price: number;
    quantity: number;
}

function calculateTotal(items: CartItem[]): number {
    return items.reduce((sum: number, item: CartItem) => {
        return sum + (item.price * item.quantity);
    }, 0);
}

const cart: CartItem[] = [
    { name: 'Apple', price: 1.50, quantity: 3 },
    { name: 'Bread', price: 2.00, quantity: 1 }
];
```

**Key Translations:**
- Add interface definitions
- Add type annotations to parameters
- Add return type annotations
- Type-safe array declarations

---

## Category 3: Architecture Transformation Patterns

### Pattern: MVC → Decoupled API + SPA

**Before (MVC - Backend Renders HTML):**
```python
# views.py (Flask)
@app.route('/products')
def product_list():
    products = Product.query.all()
    return render_template('products.html', products=products)

# templates/products.html
<html>
<body>
    {% for product in products %}
        <div class="product">
            <h3>{{ product.name }}</h3>
            <p>${{ product.price }}</p>
        </div>
    {% endfor %}
</body>
</html>
```

**After (Decoupled - API + React):**
```python
# api/products.py (Backend API)
@app.route('/api/products')
def get_products():
    products = Product.query.all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'price': p.price
    } for p in products])
```

```jsx
// frontend/ProductList.jsx (React)
import React, { useState, useEffect } from 'react';

function ProductList() {
    const [products, setProducts] = useState([]);
    
    useEffect(() => {
        fetch('/api/products')
            .then(res => res.json())
            .then(data => setProducts(data));
    }, []);
    
    return (
        <div>
            {products.map(product => (
                <div key={product.id} className="product">
                    <h3>{product.name}</h3>
                    <p>${product.price}</p>
                </div>
            ))}
        </div>
    );
}
```

**Transformation Steps:**
1. Extract data endpoints from view functions
2. Convert templates to API responses
3. Create frontend components
4. Implement API client calls
5. Handle state management

**Metrics:**
- Backend complexity reduced: 40%
- Frontend reusability increased: 300%
- API endpoints created: 15

---

## Category 4: Type System Migration

### Pattern: Weak Typing → Strong Typing

**JavaScript (Weak Typing):**
```javascript
function createOrder(userId, items, shippingAddress) {
    const total = items.reduce((sum, item) => 
        sum + item.price * item.quantity, 0);
    
    return {
        userId: userId,
        items: items,
        total: total,
        shippingAddress: shippingAddress,
        createdAt: new Date()
    };
}
```

**TypeScript (Strong Typing):**
```typescript
interface OrderItem {
    productId: string;
    price: number;
    quantity: number;
}

interface Address {
    street: string;
    city: string;
    zipCode: string;
}

interface Order {
    userId: string;
    items: OrderItem[];
    total: number;
    shippingAddress: Address;
    createdAt: Date;
}

function createOrder(
    userId: string,
    items: OrderItem[],
    shippingAddress: Address
): Order {
    const total: number = items.reduce((sum, item) => 
        sum + item.price * item.quantity, 0);
    
    return {
        userId,
        items,
        total,
        shippingAddress,
        createdAt: new Date()
    };
}
```

**Key Improvements:**
- Type safety prevents runtime errors
- IDE autocomplete and type checking
- Self-documenting code
- Catch bugs at compile-time

---

## Category 5: Database Migration Patterns

### Pattern: ORM → RAW SQL Migration

**Before (SQLAlchemy ORM):**
```python
from sqlalchemy import select

# ORM query
users = session.query(User).filter(
    User.is_active == True,
    User.created_at >= '2024-01-01'
).order_by(User.name).all()
```

**After (RAW SQL with Tests):**
```python
# queries.py
GET_ACTIVE_USERS_SQL = """
SELECT id, name, email, created_at
FROM users
WHERE is_active = true
  AND created_at >= %s
ORDER BY name
"""

def get_active_users(conn, since_date):
    cursor = conn.cursor()
    cursor.execute(GET_ACTIVE_USERS_SQL, (since_date,))
    return cursor.fetchall()

# tests/test_queries.py
def test_get_active_users_sql():
    """Test RAW SQL query for active users"""
    # Setup test database
    conn = get_test_connection()
    
    # Insert test data
    conn.execute("""
        INSERT INTO users (name, email, is_active, created_at)
        VALUES 
            ('Alice', 'alice@example.com', true, '2024-02-01'),
            ('Bob', 'bob@example.com', true, '2023-12-01'),
            ('Charlie', 'charlie@example.com', false, '2024-03-01')
    """)
    
    # Test query
    results = get_active_users(conn, '2024-01-01')
    
    # Assertions
    assert len(results) == 1
    assert results[0]['name'] == 'Alice'
    assert results[0]['is_active'] == True
```

**Metrics:**
- Query performance: 2x faster (no ORM overhead)
- SQL test coverage: 100%
- Database-specific optimizations enabled

### Pattern: Query Builder → Direct SQL

**Before (Knex.js Query Builder):**
```javascript
const products = await knex('products')
    .select('*')
    .where('category', 'electronics')
    .andWhere('price', '<', 1000)
    .orderBy('price', 'asc');
```

**After (RAW SQL + Tests):**
```javascript
const GET_PRODUCTS_BY_CATEGORY_SQL = `
    SELECT id, name, price, category
    FROM products
    WHERE category = $1
      AND price < $2
    ORDER BY price ASC
`;

async function getProductsByCategory(pool, category, maxPrice) {
    const result = await pool.query(
        GET_PRODUCTS_BY_CATEGORY_SQL,
        [category, maxPrice]
    );
    return result.rows;
}

// tests/test_queries.test.js
test('get products by category returns correct results', async () => {
    // Setup
    await pool.query(`
        INSERT INTO products (name, price, category)
        VALUES 
            ('Laptop', 800, 'electronics'),
            ('Phone', 500, 'electronics'),
            ('Tablet', 1200, 'electronics')
    `);
    
    // Execute
    const products = await getProductsByCategory(pool, 'electronics', 1000);
    
    // Assert
    expect(products).toHaveLength(2);
    expect(products[0].name).toBe('Phone');
    expect(products[1].name).toBe('Laptop');
});
```

---

## Migration Best Practices

### 1. Framework Upgrades
- Read changelogs carefully
- Upgrade incrementally (not all at once)
- Test after each upgrade
- Maintain backward compatibility where possible

### 2. Cross-Language Migration
- Start with syntax translations
- Then translate idioms
- Preserve business logic exactly
- Add comprehensive tests

### 3. Architecture Transformation
- Extract APIs before UI changes
- Maintain dual support during transition
- Migrate incrementally (feature by feature)
- Monitor performance impact

### 4. Type System Migration
- Infer types from usage patterns
- Start with simple types, add complexity gradually
- Use strict mode in TypeScript
- Leverage IDE type checking

### 5. Database Migration
- Write SQL tests before converting
- Use parameterized queries (prevent SQL injection)
- Measure performance before/after
- Document all queries

## Success Metrics

- **Project 1**: 70% logical correctness, 30% test coverage
- **Project 2**: 50% backend migration, 50% frontend migration
- **Project 3**: 70% type migration, 30% SQL test coverage
