import streamlit as st
import pandas as pd

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

def simplify_expression(minterms):
    if not minterms:
        return
    
    bits = len(bin(max(minterms))) - 2
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
                        # Avoid duplicates
                        if not any(x['bin'] == res for x in new_groups[ones]):
                            new_groups[ones].append({'m': combined_m, 'bin': res, 'matched': False})
                            step_data.append({"Matched Minterms": str(combined_m), "New Binary": res})
        
        # Collect unmatched terms as Prime Implicants
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
    pi_chart = {}
    for m in minterms:
        pi_chart[str(m)] = []
        for pi in all_pi:
            if m in pi['m']:
                pi_chart[str(m)].append("X")
            else:
                pi_chart[str(m)].append("")
                
    pi_df = pd.DataFrame(pi_chart)
    pi_df.insert(0, "Prime Implicant (Binary)", [pi['bin'] for pi in all_pi])
    st.table(pi_df)

    # Note: Extracting minimal equation from PIs mathematically requires Petrick's method.
    # For display purposes, we output the raw Prime Implicants list.
    st.success(f"**Identified Prime Implicants:** {', '.join([pi['bin'] for pi in all_pi])}")
    st.info("Variables represented by bits (e.g., '0' = A', '1' = A, '-' = eliminated).")

# --- Dashboard Input ---
st.markdown("---")
minterm_input = st.text_input("Enter Minterms separated by commas (e.g., 0, 1, 3, 7, 8, 10):", "0, 1, 3, 7, 8, 10")
if st.button("Calculate Minimal Expression", type="primary"):
    try:
        minterms_list = [int(x.strip()) for x in minterm_input.split(',') if x.strip()]
        minterms_list = sorted(list(set(minterms_list)))
        simplify_expression(minterms_list)
    except ValueError:
        st.error("Invalid input. Please enter numbers only.")