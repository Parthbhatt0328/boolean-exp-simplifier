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
            target = expr_str[start:idx]
            expr_str = expr_str[:start] + '~' + target + expr_str[idx+1:]
        else:
            expr_str = expr_str[:idx] + expr_str[idx+1:]
    return expr_str

def simplify_expression(minterms, bits, var_names):
    if not minterms:
        st.success("**Final Reduced Expression:** 0 (Always False)")
        return
        
    if len(minterms) == 2**bits:
        st.success("**Final Reduced Expression:** 1 (Always True)")
        return
    
    groups = {}
    
    # Step 1: Initial Grouping
    for m in minterms:
        bin_val = get_binary(m, bits)
        ones = bin_val.count('1')
        if ones not in groups:
            groups[ones] = []
        groups[ones].append({ 'm': [m], 'bin': bin_val, 'matched': False })
    
    st.header("Step 1: Binary Grouping")
    step1_data = []
    for k in sorted(groups.keys()):
        for item in groups[k]:
            step1_data.append({"Group (1s)": k, "Minterm": str(item['m'][0]), "Binary": item['bin']})
    st.table(pd.DataFrame(step1_data))

    # Step 2: Step-by-Step Pairing
    st.header("Step 2: Tabular Pairing")
    all_pi = []
    current_groups = groups
    step = 1

    while True:
        new_groups = {}
        matched_any_in_step = False
        keys = sorted(current_groups.keys())
        step_data = []
        
        for i in range(len(keys) - 1):
            group1 = current_groups[keys[i]]
            group2 = current_groups[keys[i+1]]
            
            for t1 in group1:
                for t2 in group2:
                    res = compare_terms(t1['bin'], t2['bin'])
                    if res:
                        t1['matched'] = True
                        t2['matched'] = True
                        matched_any_in_step = True
                        ones = res.count('1')
                        if ones not in new_groups:
                            new_groups[ones] = []
                        
                        combined_m = sorted(list(set(t1['m'] + t2['m'])))
                        if not any(x['bin'] == res for x in new_groups[ones]):
                            new_groups[ones].append({'m': combined_m, 'bin': res, 'matched': False})
                            step_data.append({"Matched Minterms": str(combined_m), "New Binary": res})
        
        for k in keys:
            for t in current_groups[k]:
                if not t['matched'] and t['bin'] not in [x['bin'] for x in all_pi]:
                    all_pi.append(t)
                    
        if matched_any_in_step:
            st.subheader(f"Pairing Iteration {step}")
            if step_data:
                st.table(pd.DataFrame(step_data))
            current_groups = new_groups
            step += 1
        else:
            break

    # Step 3: Prime Implicant Chart
    st.header("Step 3: Prime Implicant Chart")
    pi_chart = {m: [] for m in minterms}
    pi_df_data = {}
    
    for m in minterms:
        pi_df_data[str(m)] = []
        for pi in all_pi:
            if m in pi['m']:
                pi_df_data[str(m)].append("X")
                pi_chart[m].append(pi['bin'])
            else:
                pi_df_data[str(m)].append("")
                
    pi_df = pd.DataFrame(pi_df_data)
    pi_df.insert(0, "Prime Implicant (Binary)", [pi['bin'] for pi in all_pi])
    st.table(pi_df)

    # Find Essential Prime Implicants (EPIs)
    epis = []
    covered_minterms = set()
    for m, pis in pi_chart.items():
        if len(pis) == 1:
            if pis[0] not in epis:
                epis.append(pis[0])
            for pi in all_pi:
                if pi['bin'] == pis[0]:
                    for cov_m in pi['m']:
                        covered_minterms.add(cov_m)
                        
    # Find Non-Essential Prime Implicants (NEPIs)
    nepis = [pi['bin'] for pi in all_pi if pi['bin'] not in epis]

    # Step 4: Final Output
    final_pis = list(epis)
    remaining_minterms = set(minterms) - covered_minterms
    remaining_all_pis = [pi for pi in all_pi if pi['bin'] not in epis]
    
    while remaining_minterms:
        best_pi = None
        best_cover = set()
        for pi in remaining_all_pis:
            cover = set(pi['m']) & remaining_minterms
            if len(cover) > len(best_cover):
                best_cover = cover
                best_pi = pi
        if best_pi:
            final_pis.append(best_pi['bin'])
            remaining_minterms -= best_cover
            remaining_all_pis.remove(best_pi)

    st.markdown("---")
    st.header("Step 4: Result Categorization")
    st.info(f"**All Prime Implicants:** {', '.join([bin_to_var(pi['bin'], var_names) for pi in all_pi])}")
    st.success(f"**Essential Prime Implicants:** {', '.join([bin_to_var(e, var_names) for e in epis]) if epis else 'None'}")
    st.warning(f"**Non-Essential Prime Implicants:** {', '.join([bin_to_var(n, var_names) for n in nepis]) if nepis else 'None'}")
    
    final_expression = " + ".join([bin_to_var(pi, var_names) for pi in final_pis])
    st.markdown("### 🏆 Final Minimal Boolean Expression:")
    st.error(f"**{final_expression}**")


# --- Dashboard Input Area ---
st.markdown("---")
st.subheader("Input Configuration")

input_type = st.radio("Choose Input Method:", ["Minterms", "Maxterms", "Boolean Expression"])
default_vars = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

if input_type in ["Minterms", "Maxterms"]:
    num_vars = st.number_input("Number of Variables (bits):", min_value=1, max_value=10, value=3)
    var_names = default_vars[:num_vars]
    
    max_val = (2**num_vars) - 1
    
    # Instructions and Examples
    st.markdown(f"**Instructions:** Enter a list of comma-separated numbers from **0 to {max_val}** (since you selected {num_vars} variables).")
    if input_type == "Minterms":
        st.markdown("**Example input:** `0, 1, 2, 5, 7`")
    else:
        st.markdown("**Example input:** `3, 4, 6`")
    
    user_input = st.text_input(
        f"Enter {input_type}:", 
        value="0, 1, 3, 7" if input_type == "Minterms" else "2, 4, 5", 
        help=f"Type comma-separated numbers between 0 and {max_val}.",
        placeholder=f"Example: 0, 2, {max_val}"
    )
    
    if st.button("Calculate Minimal Expression", type="primary"):
        if not user_input.strip():
            st.error(f"⚠️ Input is empty. Please enter some numbers (Example: 0, 1, {max_val}).")
        
        elif not re.match(r'^[\d,\s]+$', user_input):
            st.error("⚠️ Invalid format! Please enter ONLY numbers and commas. Letters or special characters are not allowed.")
        
        else:
            try:
                terms = [int(x.strip()) for x in user_input.split(',') if x.strip()]
                
                if any(t >= 2**num_vars for t in terms):
                    st.error(f"⚠️ Out of bounds! You selected {num_vars} variables, which means the maximum allowed number is {max_val}.")
                else:
                    if input_type == "Minterms":
                        minterms_list = sorted(list(set(terms)))
                    else: 
                        universal_set = set(range(2**num_vars))
                        minterms_list = sorted(list(universal_set - set(terms)))
                    
                    simplify_expression(minterms_list, num_vars, var_names)
            except ValueError:
                st.error("⚠️ Error processing numbers. Check for double commas or typos.")

elif input_type == "Boolean Expression":
    st.markdown("**Instructions:** Use `.` for AND, `+` for OR, and `'` for NOT.")
    st.markdown("**Example input:** `A'.B + C`")
    expr_input = st.text_input(
        "Enter Boolean Expression:", 
        value="A'.B + C",
        help="Use strictly these operators: ' (NOT), . (AND), + (OR)",
        placeholder="Example: (A'.B) + C'"
    )
    
    if st.button("Calculate Minimal Expression", type="primary"):
        if not expr_input.strip():
            st.error("⚠️ Expression is empty. Please enter a valid Boolean expression.")
        else:
            try:
                sympy_syntax = parse_custom_boolean(expr_input)
                expr = parse_expr(sympy_syntax)
                
                variables = sorted(list(expr.free_symbols), key=lambda x: str(x))
                var_names = [str(v) for v in variables]
                num_vars = len(var_names)
                
                if num_vars > 10:
                    st.error("⚠️ Too many variables! Please limit your expression to 10 unique variables.")
                else:
                    tt = truth_table(expr, variables)
                    minterms_list = []
                    for i, result in enumerate(tt):
                        if result[1]:
                            minterms_list.append(i)
                            
                    st.write(f"*Identified Variables:* {', '.join(var_names)} | *Generated Minterms:* {minterms_list}")
                    simplify_expression(minterms_list, num_vars, var_names)
            except Exception:
                st.error("⚠️ Invalid expression syntax! Make sure you only use your variables (A, B, C) and the allowed operators ( ' , . , + ). Example: A'.B + C")
