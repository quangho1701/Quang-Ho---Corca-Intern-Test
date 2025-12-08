# Quang Ho - Corca Intern Test

A production-ready mathematical equation solver featuring intelligent parsing, robust error handling, and security-first design.

---

## 🚀 Quick Start

```bash
docker-compose up --build
```

Then open:
- **Frontend UI**: [http://localhost:5173](http://localhost:5173)
- **Backend API**: [http://localhost:8000](http://localhost:8000)

---

## ✨ Highlights

This solver goes beyond basic implementation with three key engineering features:

1. **User-Centric Parsing** - Type `2x` instead of `2*x`, just like on paper
2. **Smart Fallback Strategy** - Handles edge cases like `abs(x) = 5` while preserving complex roots
3. **Security-First Design** - Uses `sympy.parse_expr()` instead of unsafe `eval()`

**For complete technical details, test instructions, and interview talking points, see:**

**📖 [TESTING.md](./TESTING.md)** ← Full feature documentation

---

## 🧪 Running Tests

```bash
# Make sure the app is running first
docker-compose up --build

# In a new terminal, run the test suite
python test_api.py
```

The test suite covers 18 scenarios across 6 categories: standard math, implicit multiplication, complex roots, smart fallback edge cases, error handling, and security injection attempts.

---

## 🛠️ Stack

- **Backend**: Flask + SymPy (Python)
- **Frontend**: React + TypeScript + Vite
- **Styling**: TailwindCSS
- **Container**: Docker + Docker Compose

---

## 📡 API Example

**POST** `/solve`

```json
{
  "equation": "2x + 4 = 10"
}
```

**Response**:
```json
{
  "result": "x = 3"
}
```

---

## 📚 Additional Resources

- **[TESTING.md](./TESTING.md)** - Complete technical documentation
- **[test_api.py](./test_api.py)** - Automated test suite

---

Built with ❤️ for Corca Engineering Interview
