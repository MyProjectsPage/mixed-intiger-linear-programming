import streamlit as st
import pulp
import pandas as pd

# -------------------------------------------------------------------
# Streamlit Page Config
# -------------------------------------------------------------------
st.set_page_config(
    page_title="Warehouse Shipping Optimizer",
    layout="wide",  # 👈 full-width layout
    initial_sidebar_state="collapsed"
)

# -------------------------------------------------------------------
# App Title and Intro
# -------------------------------------------------------------------
st.markdown("""
# 🏭 Warehouse Shipping Optimization (MILP)

Use this tool to find the **lowest-cost shipping plan** between multiple warehouses and customers.
It uses **Mixed Integer Linear Programming (MILP)** to calculate the optimal solution.

---
""")

# -------------------------------------------------------------------
# Create Tabs
# -------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🚚 Warehouses",
    "👥 Customers",
    "💰 Shipping Costs",
    "📊 Optimization Results",
    "ℹ️ About"
])

# -------------------------------------------------------------------
# Tab 1 – Warehouses
# -------------------------------------------------------------------
with tab1:
    st.subheader("🏗 Define Warehouses")
    n_warehouses = st.number_input("Number of Warehouses", min_value=1, max_value=10, value=2)
    
    warehouses = []
    capacity = {}
    
    cols = st.columns(2)
    for i in range(n_warehouses):
        with cols[i % 2]:
            w_name = st.text_input(f"Warehouse {i+1} Name", value=f"W{i+1}", key=f"wname_{i}")
            w_cap = st.number_input(f"{w_name} Capacity", min_value=0, value=100, key=f"wcap_{i}")
        warehouses.append(w_name)
        capacity[w_name] = w_cap

# -------------------------------------------------------------------
# Tab 2 – Customers
# -------------------------------------------------------------------
with tab2:
    st.subheader("👥 Define Customers")
    n_customers = st.number_input("Number of Customers", min_value=1, max_value=10, value=2)
    
    customers = []
    demand = {}
    
    cols = st.columns(2)
    for i in range(n_customers):
        with cols[i % 2]:
            c_name = st.text_input(f"Customer {i+1} Name", value=f"C{i+1}", key=f"cname_{i}")
            c_dem = st.number_input(f"{c_name} Demand", min_value=0, value=80, key=f"cdem_{i}")
        customers.append(c_name)
        demand[c_name] = c_dem

# -------------------------------------------------------------------
# Tab 3 – Shipping Costs
# -------------------------------------------------------------------
with tab3:
    st.subheader("💰 Shipping Cost Matrix")
    st.write("Enter the shipping cost **per unit** from each warehouse to each customer.")

    # Initialize dataframe for editable cost matrix
    cost_df = pd.DataFrame(4, index=warehouses, columns=customers)
    edited_df = st.data_editor(
        cost_df,
        use_container_width=True,
        num_rows="dynamic",
        key="cost_editor"
    )

    costs = {(w, c): float(edited_df.loc[w, c]) for w in warehouses for c in customers}

# -------------------------------------------------------------------
# Tab 4 – Optimization Results
# -------------------------------------------------------------------
with tab4:
    st.subheader("📊 Optimization Results")
    st.write("Click **Optimize** to compute the lowest-cost shipping plan.")

    st.markdown("---")

    if st.button("🚀 Optimize", use_container_width=True):
        try:
            # Create optimization problem
            prob = pulp.LpProblem("Warehouse_Shipping_MILP", pulp.LpMinimize)

            # Decision variables: units shipped from w → c
            x = pulp.LpVariable.dicts("x", (warehouses, customers), lowBound=0, cat="Integer")

            # Objective: minimize total cost
            prob += pulp.lpSum(costs[(w, c)] * x[w][c] for w in warehouses for c in customers)

            # Supply constraints
            for w in warehouses:
                prob += pulp.lpSum(x[w][c] for c in customers) <= capacity[w]

            # Demand constraints
            for c in customers:
                prob += pulp.lpSum(x[w][c] for w in warehouses) == demand[c]

            # Solve model
            solver = pulp.PULP_CBC_CMD(msg=False)
            prob.solve(solver)

            status = pulp.LpStatus[prob.status]
            st.success(f"✅ Optimization Status: {status}")

            if status == "Optimal":
                result_data = []
                for w in warehouses:
                    for c in customers:
                        shipped = int(pulp.value(x[w][c]))
                        if shipped > 0:
                            result_data.append({
                                "Warehouse": w,
                                "Customer": c,
                                "Units Shipped": shipped,
                                "Unit Cost": costs[(w, c)],
                                "Total Cost": shipped * costs[(w, c)]
                            })

                result_df = pd.DataFrame(result_data)
                total_cost = pulp.value(prob.objective)

                # Show results side by side
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.dataframe(result_df, use_container_width=True, hide_index=True)
                with col2:
                    st.metric("💵 Minimum Total Cost", f"${total_cost:,.2f}")

            else:
                st.warning("Solver did not find an optimal solution.")
        except Exception as e:
            st.error(f"⚠️ Error: {str(e)}")

# -------------------------------------------------------------------
# Tab 5 – About
# -------------------------------------------------------------------
with tab5:
    st.markdown("## About")
    st.markdown("Developer: Chadee Fouad - MyWorkDropBox@gmail.com  \nDevelopment Date: Oct. 2025.") 
    st.markdown("[Click here to visit my website](https://myprojectspage.github.io/index.html)")
    st.write()



# -------------------------------------------------------------------
# Footer
# -------------------------------------------------------------------
st.markdown("""
---
✅ *Tip:* You can change warehouse capacities, customer demand, and shipping costs in the tabs above,  
then click **Optimize** again to instantly recompute the optimal shipping plan.
""")
