from simpleeval import simple_eval

def calculator_tool(expression: str):
    try:
        result = simple_eval(
            expression
        )
        return result
    except Exception as e:
        raise Exception(
            f"Calculation failed: {e}"
        )