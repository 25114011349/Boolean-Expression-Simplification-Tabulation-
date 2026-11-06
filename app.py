import streamlit as st
import pandas as pd


def get_bin(n, num_vars):
    return bin(n)[2:].zfill(num_vars)


def solve_qm(minterms, num_vars):
    groups = {}
    for m in minterms:
        b = get_bin(m, num_vars)
        ones = b.count('1')
        groups.setdefault(ones, []).append((b, {m}))

    prime_implicants = set()
    steps_log = []

    step_count = 1
    while groups:
        current_step_str = f"### Step {step_count}: Grouping by number of 1s\n"
        for ones in sorted(groups.keys()):
            terms_in_group = [f"{t[0]} (minterms: {list(t[1])})" for t in groups[ones]]
            current_step_str += f"- **Group {ones} (1s)**: " + ", ".join(terms_in_group) + "\n"
        steps_log.append(current_step_str)

        next_groups = {}
        matched = set()
        keys = sorted(groups.keys())

        for i in range(len(keys) - 1):
            g1 = groups[keys[i]]
            g2 = groups[keys[i + 1]]
            for t1 in g1:
                for t2 in g2:
                    diff = sum(c1 != c2 for c1, c2 in zip(t1[0], t2[0]))
                    if diff == 1:
                        new_b = "".join(c1 if c1 == c2 else '-' for c1, c2 in zip(t1[0], t2[0]))
                        new_m = t1[1].union(t2[1])
                        ones = new_b.count('1')
                        next_groups.setdefault(ones, [])
                        if not any(x[0] == new_b for x in next_groups[ones]):
                            next_groups[ones].append((new_b, new_m))
                        matched.add(t1[0])
                        matched.add(t2[0])

        for ones in groups:
            for t in groups[ones]:
                if t[0] not in matched:
                    prime_implicants.add((t[0], frozenset(t[1])))

        groups = next_groups
        step_count += 1

    return prime_implicants, steps_log


def binary_to_expression(bin_str, variables):
    """Converts a binary implicant string into a Boolean expression."""
    terms = []
    for i, char in enumerate(bin_str):
        if char == '1':
            terms.append(variables[i])
        elif char == '0':
            terms.append(f"{variables[i]}'")
    return "".join(terms) if terms else "1"


# --- Streamlit UI Setup ---
st.set_page_config(page_title="Boolean Simplification Dashboard", page_icon="⚡", layout="wide")

st.title("⚡ Boolean Expression Simplification Dashboard")
st.markdown(
    "A web-based dashboard implementing the **Quine-McCluskey Tabulation Method** for minimizing Boolean functions.")

with st.sidebar:
    st.header("Configuration")
    num_vars = st.slider("Number of Variables", min_value=2, max_value=6, value=4)
    default_vars = [chr(65 + i) for i in range(num_vars)]

    st.markdown(f"**Variable Names:** {', '.join(default_vars)}")

    minterms_input = st.text_input(
        "Enter Minterms (comma-separated):",
        value="4, 8, 10, 11, 12, 15",
        help="Example for 4 variables: 4, 8, 10, 11, 12, 15"
    )

    run_btn = st.button("Simplify Expression", type="primary")

if run_btn:
    try:
        minterms = [int(m.strip()) for m in minterms_input.split(",") if m.strip() != ""]
        max_limit = (2 ** num_vars) - 1

        invalid_minterms = [m for m in minterms if m > max_limit or m < 0]
        if invalid_minterms:
            st.error(
                f"Error: Minterms {invalid_minterms} are out of range for {num_vars} variables (0 to {max_limit}).")
        else:
            minterms = sorted(list(set(minterms)))
            st.success(f"Processing minterms: {minterms} with {num_vars} variables.")

            pis, steps_log = solve_qm(minterms, num_vars)

            col1, col2 = st.columns([1, 1])

            with col1:
                st.subheader("📋 Prime Implicants")
                if pis:
                    pi_data = []
                    for idx, pi in enumerate(pis):
                        expr = binary_to_expression(pi[0], default_vars)
                        pi_data.append({
                            "PI #": idx + 1,
                            "Binary Form": pi[0],
                            "Covered Minterms": sorted(list(pi[1])),
                            "Algebraic Term": expr
                        })
                    st.dataframe(pd.DataFrame(pi_data), use_container_width=True)
                else:
                    st.info("No prime implicants found.")

            with col2:
                st.subheader("✨ Simplified Result (SOP)")
                if pis:
                    expressions = [binary_to_expression(pi[0], default_vars) for pi in pis]
                    final_sop = " + ".join(expressions)
                    st.code(final_sop, language="text")
                else:
                    st.warning("Could not compute expression.")

            with st.expander("🔍 View Tabulation Steps & Details"):
                for step_text in steps_log:
                    st.markdown(step_text)
                    st.divider()

    except ValueError:
        st.error("Please enter a valid integer")

else:
    st.info(
        "Configure your variables and minterms in the sidebar, then click **Simplify Expression** to run the dashboard.")
