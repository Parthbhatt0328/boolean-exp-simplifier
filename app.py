import streamlit as st
import pandas as pd
import sympy
from sympy.logic.boolalg import truth_table
from sympy.parsing.sympy_parser import parse_expr
import re

# --- UI Setup with Name & Scholar Number ---
st.set_page_config(page_title="Boolean Simplifier", layout="wide")

col1, col2 = st.columns([3, 1])
with col1:
    st.title("Boolean Expression Simplifier")
    st.markdown("**(Quine-McCluskey Tabular Method)**")
with col2:
    st.markdown(
        """
        <div style='text-align: right; background-color: #f0f2f6; padding: 10px; border-radius: 5px; color: #000;'>
            <strong>PARTH BHATT</strong><br>
            Scholar No: 25114011310
        </div>
        """, 
        unsafe_allow_html=True
    )

# --- Helper Functions ---
def get_binary(num, bits):
    return format(num, f'0{bits}b')

def compare_terms(a, b):
    diff = 0
    idx = -1
    for i in range(len(a)):
        if a[i] != b[i]:
            diff += 1
            idx = i
    if diff == 1:
        return a[:idx] + '-' + a[idx+1:]
    return None

def bin_to_var(binary_str, var_names):
    """Converts binary '01-1' into variables using ' for NOT and . for AND"""
    res = []
    for i, bit in enumerate(binary_str):
        if bit == '0':
            res.append(f"{var_names[i]}'")
        elif bit == '1':
            res.append(var_names[i])
    if not res:
        return "1" 
    return ".".join(res) 

def parse_custom_boolean(expr_str):
    """Converts custom syntax (A'.B + C) into SymPy syntax (~A & B | C)"""
    expr_str = expr_str.replace('+', '|')
    expr_str = expr_str.replace('.', '&')
    
    while "'" in expr_str:
        idx = expr_str.find("'")
        if expr_str[idx-1].isalnum():
            start = idx - 1
            while start >= 0 and expr_str[start].isalnum():
                start -= 1
            start += 1
            target = expr_str[start:idx]
            expr_str = expr_str[:start] + '~' + target + expr_str[idx+1:]
        elif expr_str[idx-1] == ')':
            count = 1
            start = idx - 2
            while start >= 0 and count > 0:
                if expr_str[start] == ')': count += 1
                elif expr_str[start] == '(': count -= 1
                start -= 1
            start += 1
            target = expr_str[start:idx
