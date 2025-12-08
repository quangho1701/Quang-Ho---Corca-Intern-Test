# Equation Solver - Technical Documentation

A production-ready mathematical equation solver API with intelligent parsing, robust error handling, and security-first design.

---

## 🏗️ Architecture

**Stack**: Python/Flask backend + React/Vite frontend (fully Dockerized)

```
┌─────────────────┐      HTTP/JSON      ┌─────────────────┐
│   Frontend      │ ←─────────────────→ │    Backend      │
│  React + Vite   │    localhost:8000   │  Flask + SymPy  │
│ localhost:5173  │                     │                 │
└─────────────────┘                     └─────────────────┘
```

**Communication**: Cross-origin requests enabled via `flask-cors`, with JSON payloads for equations.

**Containerization**: Docker Compose orchestrates both services with hot-reload for development.

---

## 🎯 Key Engineering Features

### 1. **User-Centric Parsing: Implicit Multiplication**

**Problem**: Users naturally write math as they would on paper (e.g., `2x` instead of `2*x`), but parsers require explicit operators.

**Solution**: We use SymPy's `implicit_multiplication_application` transformation.

```python
transformations = (
    standard_transformations +
    (implicit_multiplication_application,) +
    (convert_xor,)  # Bonus: ^ becomes **
)
```

**Examples**:
| User Input | Parsed As | Result |
|------------|-----------|--------|
| `2x + 4 = 10` | `2*x + 4 = 10` | `x = 3` |
| `3(x+2) = 15` | `3*(x+2) = 15` | `x = 3` |
| `xy = 10` | `x*y = 10` | Solves for `x` or `y` |
| `x^2` | `x**2` | Exponentiation |

**Why It Matters**: Reduces friction for non-technical users. No "syntax errors" for natural math notation.

---

### 2. **Robust Solving: The "Smart Fallback" Strategy**

**Problem**: Some equations (e.g., `abs(x) = 5`) fail when SymPy treats variables as complex by default. However, other equations *need* complex roots (e.g., `x^2 + 1 = 0`).

**Solution**: Two-attempt fallback strategy with graceful degradation.

#### Algorithm:
```python
def try_solve(equation_or_expr, var):
    # Attempt 1: Solve with default (complex-allowed) symbols
    try:
        solutions = solve(equation_or_expr, var)
        return solutions, None
    except Exception as e:
        first_error = e
    
    # Attempt 2: Retry with real=True assumption
    try:
        real_var = symbols(str(var), real=True)
        real_eq = equation_or_expr.subs(var, real_var)
        solutions = solve(real_eq, real_var)
        return solutions, None
    except Exception as e:
        return None, first_error or e
```

#### Test Cases:

| Equation | Attempt 1 (Complex) | Attempt 2 (Real) | Final Result |
|----------|---------------------|------------------|--------------|
| `abs(x) = 5` | ❌ Fails (infinite set) | ✅ Succeeds | `x = -5, x = 5` |
| `x^2 + 1 = 0` | ✅ Succeeds | N/A | `x = -I, x = I` (complex roots) |
| `x^3 = 27` | ✅ Succeeds | N/A | `x = 3` (+ 2 complex roots) |

**Why It Matters**: Users get correct answers for both real-constrained (abs, sqrt) and complex-enabled equations without needing to specify domain manually.

---

### 3. **Security: `parse_expr` vs. `eval()`**

**⚠️ The Danger of `eval()`**:

Python's built-in `eval()` executes **arbitrary code**, allowing attackers to:
- Delete files: `eval("__import__('os').system('rm -rf /')")`
- Exfiltrate data: `eval("open('/etc/passwd').read()")`
- Execute malicious payloads

**✅ Our Solution: `sympy.parse_expr()`**

SymPy's parser is a **mathematical sandbox**:
- ✅ Only recognizes math symbols (`+`, `-`, `*`, `/`, `^`, variables, functions like `sin`, `abs`)
- ❌ Cannot execute system commands
- ❌ Cannot access files or modules
- ❌ Cannot run arbitrary Python code

**Security Test Cases** (all return `400 Bad Request`):
```python
"import os"                          # Blocked
"__import__('os').system('ls')"     # Blocked
"eval('2+2')"                       # Blocked
```

**Code Implementation**:
```python
# ⚠️ NEVER USE THIS (insecure):
# result = eval(user_input)

# ✅ USE THIS (secure):
from sympy.parsing.sympy_parser import parse_expr
expression = parse_expr(user_input, transformations=transformations)
```

---

## 🧪 Testing

### Quick Start
```bash
# 1. Start the application
docker-compose up --build

# 2. Run the test suite (in a new terminal)
python test_api.py
```

### Test Coverage

| Category | Tests | Coverage |
|----------|-------|----------|
| **Standard Math** | Linear, quadratic, cubic equations | ✅ |
| **Implicit Multiplication** | `2x`, `3(x+2)`, `xy` | ✅ |
| **Complex/Roots** | `x^3 = 27`, `x^2 + 1 = 0` | ✅ |
| **Smart Fallback** | `abs(x) = 5`, `abs(x-3) = 2` | ✅ |
| **Error Handling** | `2++2`, empty input, multiple `=` | ✅ |
| **Security** | Code injection attempts | ✅ |

### Sample Test Output
```
══════════════════════════════════════════════════════════════════════
🧪 EQUATION SOLVER API TEST SUITE
══════════════════════════════════════════════════════════════════════
Testing endpoint: http://localhost:8000/solve

══════════════════════════════════════════════════════════════════════
📁 Standard Math
══════════════════════════════════════════════════════════════════════
✅ PASS | Linear equation with fraction result
         ✓ x = 3
✅ PASS | Quadratic equation (two solutions)
         ✓ {'result': 'x = -2, x = 2'}

══════════════════════════════════════════════════════════════════════
📁 Smart Fallback
══════════════════════════════════════════════════════════════════════
✅ PASS | Absolute value equation (smart fallback)
         ✓ {'result': 'x = -5, x = 5'}

══════════════════════════════════════════════════════════════════════
📁 Security
══════════════════════════════════════════════════════════════════════
✅ PASS | Code injection attempt: import
         ✓ {'error': 'Invalid equation syntax...'}
```

---

## 🚀 Running the Application

### With Docker (Recommended)
```bash
# Build and start both frontend and backend
docker-compose up --build

# Access the application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
```

### Manually (Development)

**Backend**:
```bash
cd backend
pip install -r requirements.txt
python app.py
# Runs on http://localhost:8000
```

**Frontend**:
```bash
cd frontend
npm install
npm run dev
# Runs on http://localhost:5173
```

---

## 📡 API Reference

### `POST /solve`

**Request**:
```json
{
  "equation": "2x + 4 = 10"
}
```

**Success Response** (200 OK):
```json
{
  "result": "x = 3"
}
```

**Error Response** (400 Bad Request):
```json
{
  "error": "Invalid equation syntax: unexpected EOF while parsing"
}
```

### `GET /solve?equation=2x+4=10`

Also supported for convenience (URL-encoded equation).

---

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React 18 + TypeScript | UI with type safety |
| **Build Tool** | Vite | Fast dev server & HMR |
| **Styling** | TailwindCSS | Utility-first CSS |
| **Backend** | Flask 2.0+ | Lightweight Python web framework |
| **Math Engine** | SymPy 1.12+ | Symbolic mathematics |
| **CORS** | flask-cors | Cross-origin request handling |
| **Container** | Docker + Docker Compose | Reproducible environments |

---

## 🎓 Interview Talking Points

### "Why Implicit Multiplication?"
> "Users shouldn't need to know programming syntax to solve math problems. We use SymPy's transformation pipeline to parse `2x` as `2*x` automatically, just like they'd write on paper."

### "Explain the Smart Fallback Strategy"
> "Some equations like `abs(x) = 5` fail with complex symbols because the solution set would be infinite in the complex plane. Our solver attempts complex-mode first for equations like `x^2 + 1 = 0` that need it, then falls back to real-only mode if it detects ambiguity. This gives users the best of both worlds without requiring them to specify domains."

### "Why parse_expr instead of eval?"
> "Security. `eval()` executes arbitrary Python code—attackers could delete files or exfiltrate data. `parse_expr()` is a mathematical sandbox that only understands math, not system commands. We never trust user input."

---

## 📝 Future Enhancements

- [ ] Multi-variable equation systems (e.g., `2x + y = 10, x - y = 2`)
- [ ] Equation plotting/visualization
- [ ] Step-by-step solution explanations
- [ ] LaTeX rendering for prettier output
- [ ] User accounts and equation history

---

## 📄 License

MIT License - See LICENSE file for details.

---

**Built with ❤️ for robust, user-friendly mathematical computing.**
