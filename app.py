import streamlit as st
import pandas as pd
import sympy
from sympy.logic.boolalg import truth_table
from sympy.parsing.sympy_parser import parse_expr

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

# --- Quine-McCluskey Helper Functions ---
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

def bin_to_var(binary_str):
    # Converts binary like '01-1' into 'A\'BC\'D'
    vars_list = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    res = []
    for i, bit in enumerate(binary_str):
        if bit == '0':
            res.append(f"{vars_list[i]}'")
        elif bit == '1':
            res.append(vars_list[i])
    if not res:
        return "1" # All dashes means it's always True
    return "".join(res)

def simplify_expression(minterms, bits):
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

    # Step 3: Prime Implicant Chart & EPIs
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

    # Step 4: Final Output (Greedy selection for remaining PIs)
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
    st.subheader("Results")
    st.info(f"**All Prime Implicants:** {', '.join([bin_to_var(pi['bin']) for pi in all_pi])}")
    st.info(f"**Essential Prime Implicants (EPIs):** {', '.join([bin_to_var(e) for e in epis]) if epis else 'None'}")
    
    final_expression = " + ".join([bin_to_var(pi) for pi in final_pis])
    st.success(f"**Final Minimal Boolean Expression:**  {final_expression}")

# --- Dashboard Input Area ---
st.markdown("---")
st.subheader("Input Configuration")

input_type = st.radio("Choose Input Method:", ["Minterms", "Maxterms", "Boolean Expression"])

if input_type in ["Minterms", "Maxterms"]:
    num_vars = st.number_input("Number of Variables (bits):", min_value=1, max_value=10, value=3)
    user_input = st.text_input(f"Enter {input_type} (comma-separated):", "0, 1, 3")
    
    if st.button("Calculate Minimal Expression", type="primary"):
        try:
            terms = [int(x.strip()) for x in user_input.split(',') if x.strip()]
            if any(t >= 2**num_vars for t in terms):
                st.error(f"Error: A term exceeds the maximum possible value ({2**num_vars - 1}) for {num_vars} variables.")
            else:
                if input_type == "Minterms":
                    minterms_list = sorted(list(set(terms)))
                else: # Maxterms
                    universal_set = set(range(2**num_vars))
                    minterms_list = sorted(list(universal_set - set(terms)))
                
                simplify_expression(minterms_list, num_vars)
        except ValueError:
            st.error("Invalid input. Please enter numbers only.")

elif input_type == "Boolean Expression":
    st.markdown("**Instructions:** Use `&` for AND, `|` for OR, and `~` for NOT. (Example: `(~A & B) | C`)")
    expr_input = st.text_input("Enter Boolean Expression:", "(~A & B) | C")
    
    if st.button("Calculate Minimal Expression", type="primary"):
        try:
            # Parse expression
            expr = parse_expr(expr_input)
            variables = sorted(list(expr.free_symbols), key=lambda x: x.name)
            num_vars = len(variables)
            
            # Generate Truth Table to extract minterms
            tt = truth_table(expr, variables)
            minterms_list = []
            for i, result in enumerate(tt):
                if result[1]: # If the expression evaluates to True
                    minterms_list.append(i)
                    
            st.write(f"*Parsed Variables:* {', '.join([v.name for v in variables])} | *Generated Minterms:* {minterms_list}")
            simplify_expression(minterms_list, num_vars)
        except Exception as e:
            st.error(f"Error parsing expression. Please check your syntax. (Details: {e})")
