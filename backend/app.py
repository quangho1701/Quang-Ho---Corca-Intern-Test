#!/usr/bin/env python3
"""Flask API for solving mathematical equations using sympy."""

from __future__ import annotations

import os
from flask import Flask, jsonify, request
from flask_cors import CORS

# ============================================================================
# SECURITY NOTE:
# We use sympy's parse_expr() instead of Python's built-in eval() for
# parsing mathematical expressions. This is CRITICAL for security because:
#
# 1. eval() executes arbitrary Python code, allowing malicious inputs like:
#    - "__import__('os').system('rm -rf /')" (file system attacks)
#    - "open('/etc/passwd').read()" (data exfiltration)
#
# 2. parse_expr() is designed specifically for mathematical expressions:
#    - It only recognizes mathematical symbols and operators
#    - It cannot execute system commands or access files
#    - It provides a safe sandbox for parsing user input
#
# NEVER use eval() on untrusted user input in a production application.
# ============================================================================

from sympy import symbols, Eq, solve, sympify
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
    convert_xor,
)


def create_app() -> Flask:
    app = Flask(__name__)
    
    # Enable CORS for all routes - required for frontend (localhost:5173) 
    # to communicate with backend (localhost:8000) across different ports
    CORS(app)

    def solve_equation(equation_str: str) -> dict:
        """
        Parse and solve a mathematical equation string.
        
        Supports:
        - Equations with = sign: "2x + 4 = 10"
        - Expressions to simplify: "2x + 3x"
        - Implicit multiplication: "2x" -> "2*x", "3(x+1)" -> "3*(x+1)"
        - Fallback to real symbols for functions like abs() that require it
        
        Returns:
            dict with 'result' key on success, or 'error' key on failure
        """
        # Define transformations that enable implicit multiplication
        # This allows "2x" to be parsed as "2*x" and "3(x+1)" as "3*(x+1)"
        transformations = (
            standard_transformations +
            (implicit_multiplication_application,) +
            (convert_xor,)  # Converts ^ to ** for exponentiation
        )
        
        def try_solve(equation_or_expr, var, is_equation=True):
            """
            Attempt to solve with fallback to real symbols.
            
            Attempt 1: Try solving with default (complex) symbols.
            Attempt 2: If that fails, retry with real=True symbols.
            
            This handles edge cases like abs(x)=5 which require real assumptions,
            while preserving complex roots for equations that support them.
            """
            first_error = None
            
            # Attempt 1: Try with default (complex-allowed) symbols
            try:
                if is_equation:
                    solutions = solve(equation_or_expr, var)
                else:
                    solutions = solve(equation_or_expr, var)
                return solutions, None
            except Exception as e:
                first_error = e
            
            # Attempt 2: Retry with real=True assumption
            # This fixes cases like abs(x)=5 where sympy needs to know x is real
            try:
                var_name = str(var)
                real_var = symbols(var_name, real=True)
                
                # Substitute the real variable into the equation/expression
                if is_equation:
                    real_eq = equation_or_expr.subs(var, real_var)
                    solutions = solve(real_eq, real_var)
                else:
                    real_expr = equation_or_expr.subs(var, real_var)
                    solutions = solve(real_expr, real_var)
                
                return solutions, None
            except Exception as e:
                # Both attempts failed - return the original error
                return None, first_error or e
        
        # Check if this is an equation (contains '=') or an expression
        if '=' in equation_str:
            # Split into left-hand side and right-hand side
            parts = equation_str.split('=')
            if len(parts) != 2:
                return {"error": "Invalid equation: multiple '=' signs found"}
            
            lhs_str, rhs_str = parts[0].strip(), parts[1].strip()
            
            if not lhs_str or not rhs_str:
                return {"error": "Invalid equation: empty side detected"}
            
            # Parse both sides using safe parse_expr with implicit multiplication
            lhs = parse_expr(lhs_str, transformations=transformations)
            rhs = parse_expr(rhs_str, transformations=transformations)
            
            # Create the equation
            equation = Eq(lhs, rhs)
            
            # Auto-detect the variable(s) in the equation
            free_symbols = equation.free_symbols
            
            if not free_symbols:
                # No variables - check if it's a true/false statement
                if lhs == rhs:
                    return {"result": "True (identity)"}
                else:
                    return {"result": "False (contradiction)"}
            
            # Solve for the first variable (usually x or y)
            # Sort to get consistent results (alphabetically)
            var = sorted(free_symbols, key=str)[0]
            
            # Use fallback solver with real symbol retry
            solutions, error = try_solve(equation, var, is_equation=True)
            if error:
                return {"error": f"Could not solve equation: {str(error)}"}
            
        else:
            # No '=' sign - treat as expression to simplify or solve = 0
            expr = parse_expr(equation_str, transformations=transformations)
            
            free_symbols = expr.free_symbols
            
            if not free_symbols:
                # Pure numerical expression - evaluate it
                result = sympify(expr)
                return {"result": str(result)}
            
            # Solve expression = 0
            var = sorted(free_symbols, key=str)[0]
            
            # Use fallback solver with real symbol retry
            solutions, error = try_solve(expr, var, is_equation=False)
            if error:
                return {"error": f"Could not solve expression: {str(error)}"}
        
        # Format the solutions
        if not solutions:
            return {"result": "No solution"}
        elif len(solutions) == 1:
            return {"result": f"{var} = {solutions[0]}"}
        else:
            # Multiple solutions (e.g., quadratic equations)
            solution_strs = [f"{var} = {sol}" for sol in solutions]
            return {"result": ", ".join(solution_strs)}

    @app.route("/solve", methods=["GET", "POST", "OPTIONS"])
    def solve_route():
        """
        Endpoint to solve mathematical equations.
        
        GET: Pass equation as query parameter: /solve?equation=2x+4=10
        POST: Pass equation in JSON body: {"equation": "2x + 4 = 10"}
        """
        # Handle preflight CORS request
        if request.method == "OPTIONS":
            return jsonify({}), 200
        
        # Extract equation from request
        if request.method == "POST":
            data = request.get_json(silent=True)
            if not data:
                return jsonify({"error": "Invalid JSON payload"}), 400
            equation = data.get("equation", "").strip()
        else:
            equation = (request.args.get("equation") or "").strip()
        
        if not equation:
            return jsonify({"error": "Missing 'equation' parameter"}), 400
        
        # Wrap in try/except to handle ALL parsing/solving errors gracefully
        try:
            result = solve_equation(equation)
            
            if "error" in result:
                return jsonify(result), 400
            
            return jsonify(result), 200
            
        except (SyntaxError, ValueError, TypeError) as e:
            # Common parsing errors for invalid mathematical syntax
            return jsonify({
                "error": f"Invalid equation syntax: {str(e)}"
            }), 400
        except Exception as e:
            # Catch-all for any other sympy parsing/solving errors
            # This prevents 500 Internal Server Errors from reaching the client
            return jsonify({
                "error": f"Could not parse or solve equation: {str(e)}"
            }), 400

    @app.route("/", methods=["GET"])
    def root():
        return jsonify({
            "message": "Equation Solver API",
            "usage": {
                "GET": "/solve?equation=2x+4=10",
                "POST": "/solve with JSON body: {\"equation\": \"2x + 4 = 10\"}"
            },
            "examples": [
                "2x + 4 = 10",
                "x^2 - 4 = 0",
                "3(x + 2) = 15",
                "2x + 3y = 10"
            ]
        })

    return app


def run() -> None:
    port = int(os.environ.get("PORT", 8000))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=False)


if __name__ == "__main__":
    run()
