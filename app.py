import streamlit as st
import pandas as pd
import sympy
from sympy.logic.boolalg import truth_table, to_nnf, to_dnf, simplify_logic
from sympy.parsing.sympy_parser import parse_expr
import re

# --- UI Setup with Name & Scholar Number ---
st.set_page_config(page_title="Boolean Simplifier", layout="wide")

col1, col2 = st.columns([3, 1])
with col1:
    st.title("Boolean Expression Simplifier")
    st.markdown("**(Algebraic Breakdown & Quine-McCluskey)**")
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

def sympy_to_custom(sympy_expr):
    s = str(sympy_expr)
    s = s.replace('&', '.')
    s = s.replace('|', '+')
    s = re.sub(r'~([A-Za-z0-9_]+)', r"\1'", s)
    s = re.sub(r'~\((.*?)\)', r"(\1)'", s)
    return s

def simplify_expression(minterms, bits, var_names, skip_step1_header=False):
    if not minterms:
        st.success("**Final Reduced Expression:** 0 (Always False)")
        return
        
    if len(minterms) == 2**bits:
        st.success("**Final Reduced Expression:** 1 (Always True)")
        return
        
    if not skip_step1_header:
        st.header("Step 1: Grouping by 1s")
        st.info("First, we convert everything to binary and group them by the number of 1s. This sets us up for the redundancy checks.")

    groups = {}
    for m in minterms:
        bin_val = get_binary(m, bits)
        ones = bin_val.count('1')
        if ones not in groups:
            groups[ones] = []
        groups[ones].append({ 'm': [m], 'bin': bin_val, 'matched': False })
    
    step1_data = []
    for k in sorted(groups.keys()):
        for item in groups[k]:
            step1_data.append({"Group (1s)": k, "Minterm": str(item['m'][0]), "Binary": item['bin'], "Algebraic Term": bin_to_var(item['bin'], var_names)})
    st.table(pd.DataFrame(step1_data))

    # Step 2: Tabular Pairing
    st.header("Step 2: Hunting for Redundancy")
    st.info("Here's where the magic happens. We compare adjacent groups to find terms that only differ by one variable, knocking that variable out using the Redundancy Theorem ( **XY + XY' = X** ).")
    
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
                            
                            term1_str = bin_to_var(t1['bin'], var_names)
                            term2_str = bin_to_var(t2['bin'], var_names)
                            res_str = bin_to_var(res, var_names)
                            theorem_str = f"{term1_str} + {term2_str}  ➔  {res_str}"
                            
                            step_data.append({
                                "Matched Minterms": str(combined_m), 
                                "Binary Result": res, 
                                "Redundancy Theorem Applied": theorem_str
                            })
        
        for k in keys:
            for t in current_groups[k]:
                if not t['matched'] and t['bin'] not in [x['bin'] for x in all_pi]:
                    all_pi.append(t)
                    
        if matched_any_in_step:
            st.subheader(f"Pass #{step}")
            if step_data:
                st.table(pd.DataFrame(step_data))
            current_groups = new_groups
            step += 1
        else:
            st.success("No more redundancies found! We've successfully isolated the Prime Implicants.")
            break

    # Step 3: Prime Implicant Chart
    st.header("Step 3: The Prime Implicant Chart")
    st.info("Time to filter out the noise. We plot our Prime Implicants on a chart to see which ones are absolutely essential (EPIs) to cover our minterms, and we drop the redundant ones.")
    
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
    pi_df.insert(0, "Prime Implicant (Algebraic)", [bin_to_var(pi['bin'], var_names) for pi in all_pi])
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

    # Final Output Greedy Selection
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
    st.header("The Final Breakdown")
    st.write(f"**Prime Implicants State (All):** {', '.join([bin_to_var(pi['bin'], var_names) for pi in all_pi])}")
