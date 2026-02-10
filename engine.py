def tokenize(expr: str):
    tokens = []
    i = 0
    n = len(expr)

    def is_op(ch): return ch in "+-*/^()"

    while i < n:
        ch = expr[i]

        if ch.isspace():
            i += 1
            continue

        if ch.isdigit() or ch == ".":
            start = i
            dot_count = 0
            while i < n and (expr[i].isdigit() or expr[i] == "."):
                if expr[i] == ".":
                    dot_count += 1
                    if dot_count > 1:
                        raise ValueError("عدد عشري غير صحيح")
                i += 1
            tokens.append(float(expr[start:i]))
            continue

        if is_op(ch):
            tokens.append(ch)
            i += 1
            continue

        raise ValueError("رمز غير مسموح")

    return tokens


def to_rpn(tokens):
    prec = {"+": 1, "-": 1, "*": 2, "/": 2, "^": 3}
    right_assoc = {"^"}
    output = []
    stack = []

    def is_op(t): return t in prec

    for t in tokens:
        if isinstance(t, float):
            output.append(t)
            continue

        if t == "(":
            stack.append(t)
            continue

        if t == ")":
            while stack and stack[-1] != "(":
                output.append(stack.pop())
            if not stack:
                raise ValueError("أقواس غير متوازنة")
            stack.pop()
            continue

        if is_op(t):
            while stack and stack[-1] in prec:
                top = stack[-1]
                if (prec[top] > prec[t]) or (prec[top] == prec[t] and t not in right_assoc):
                    output.append(stack.pop())
                else:
                    break
            stack.append(t)
            continue

        raise ValueError("صيغة غير صحيحة")

    while stack:
        if stack[-1] in ("(", ")"):
            raise ValueError("أقواس غير متوازنة")
        output.append(stack.pop())

    return output


def eval_rpn(rpn):
    stack = []
    for t in rpn:
        if isinstance(t, float):
            stack.append(t)
            continue

        if t in "+-*/^":
            if len(stack) < 2:
                raise ValueError("صيغة غير صحيحة")
            b = stack.pop()
            a = stack.pop()

            if t == "+":
                stack.append(a + b)
            elif t == "-":
                stack.append(a - b)
            elif t == "*":
                stack.append(a * b)
            elif t == "/":
                if b == 0:
                    raise ZeroDivisionError("لا يمكن القسمة على صفر")
                stack.append(a / b)
            elif t == "^":
                stack.append(a ** b)
            continue

        raise ValueError("صيغة غير صحيحة")

    if len(stack) != 1:
        raise ValueError("صيغة غير صحيحة")
    return stack[0]


def safe_calculate(expr: str) -> float:
    expr = expr.strip()
    if not expr:
        raise ValueError("اكتب عملية أولاً")

    normalized = []
    prev = None
    for ch in expr:
        if ch == "-" and (prev is None or prev in "+-*/^("):
            normalized.append("0")
        normalized.append(ch)
        if not ch.isspace():
            prev = ch

    expr2 = "".join(normalized)
    tokens = tokenize(expr2)
    rpn = to_rpn(tokens)
    return eval_rpn(rpn)
