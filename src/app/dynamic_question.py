# app/dynamic_questions.py
import random

# --- Define Your Question Generator Functions ---

def generate_dec_to_hex():
    """
    Generates a decimal-to-hexadecimal conversion question.
    Returns a dictionary with the question value and the correct answer.
    """
    question_value = random.randint(1, 65535)
    # format(number, '04x') pads with zeros to 4 digits and converts to lowercase hex
    answer_value = format(question_value, '04x')
    print(answer_value)

    return {
        "question": str(question_value),
        "answer": answer_value
    }

def generate_simple_math():
    """Generates a simple addition problem."""
    a = random.randint(5, 50)
    b = random.randint(5, 50)
    
    return {
        "question": f"{a} + {b}",
        "answer": str(a + b)
    }

# --- Create a "Function Registry" ---
# This dictionary maps the string name from the YAML file to the actual Python function.
# This is the core of the dispatcher pattern.
QUESTION_GENERATORS = {
    "generate_dec_to_hex": generate_dec_to_hex,
    "generate_simple_math": generate_simple_math,
}

def generate_question(function_name):
    """
    Looks up and executes a question generator function by its name.
    """
    if function_name in QUESTION_GENERATORS:
        generator_func = QUESTION_GENERATORS[function_name]
        return generator_func()
    else:
        # Return None or raise an error if the function name is not found
        print(f"Error: Dynamic question function '{function_name}' not found.")
        return None