import streamlit as st
import pulp
import pandas as pd
import plotly.graph_objects as go
import matplotlib 

# -------------------------------------------------------------------
# Page Config
# -------------------------------------------------------------------
st.set_page_config(page_title="Warehouse Shipping Optimizer", layout="wide")

st.title("🏭 Warehouse Shipping Optimization (MILP)")
st.write("""
This app finds the **lowest-cost shipping plan** between warehouses and customers.
Use the tabs below to set parameters, run optimization, and visualize results.
""")

# -------------------------------------------------------------------
# Tabs
# -------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🚚 Warehouses",
    "👥 Customers",
    "💰 Shipping Costs",
    "📊 Optimization Results",
    "📈 Visualization",
    "ℹ️ About"
])

# ---------------- Tab 1: Warehouses ----------------
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

# ---------------- Tab 2: Customers ----------------
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

# ---------------- Tab 3: Shipping Costs ----------------
with tab3:
    st.subheader("💰 Shipping Cost Matrix")
    st.write("Enter the shipping cost per unit from each warehouse to each customer.")
    cost_df = pd.DataFrame(4, index=warehouses, columns=customers)
    edited_df = st.data_editor(cost_df, use_container_width=True, num_rows="dynamic", key="cost_editor")
    costs = {(w, c): float(edited_df.loc[w, c]) for w in warehouses for c in customers}

# ---------------- Tab 4: Optimization ----------------
with tab4:
    st.subheader("📊 Optimization Results")
    st.write("Click **Optimize** to compute the lowest-cost shipping plan.")
    st.markdown("---")

    if st.button("🚀 Optimize", use_container_width=True):
        try:
            # Build MILP model
            prob = pulp.LpProblem("Warehouse_Shipping_MILP", pulp.LpMinimize)
            x = pulp.LpVariable.dicts("x", (warehouses, customers), lowBound=0, cat="Integer")

            # Objective
            prob += pulp.lpSum(costs[(w, c)] * x[w][c] for w in warehouses for c in customers)

            # Constraints
            for w in warehouses:
                prob += pulp.lpSum(x[w][c] for c in customers) <= capacity[w]
            for c in customers:
                prob += pulp.lpSum(x[w][c] for w in warehouses) == demand[c]

            # Solve
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

                col1, col2 = st.columns([2, 1])
                with col1:
                    st.dataframe(result_df, use_container_width=True, hide_index=True)
                with col2:
                    st.metric("💵 Minimum Total Cost", f"${total_cost:,.2f}")

                # Save results to session_state for visualization
                st.session_state['result_df'] = result_df

            else:
                st.warning("Solver did not find an optimal solution.")
        except Exception as e:
            st.error(f"⚠️ Error: {str(e)}")

# ---------------- Tab 5: Visualization ----------------
with tab5:
    st.subheader("📈 Shipping Flow Visualization")
    if 'result_df' in st.session_state and not st.session_state['result_df'].empty:
        df = st.session_state['result_df']

        # Sankey chart
        all_nodes = list(df['Warehouse'].unique()) + list(df['Customer'].unique())
        node_indices = {node: i for i, node in enumerate(all_nodes)}

        sankey_fig = go.Figure(go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=all_nodes,
                color="blue"
            ),
            link=dict(
                source=[node_indices[w] for w in df['Warehouse']],
                target=[node_indices[c] for c in df['Customer']],
                value=df['Units Shipped']
            )
        ))
        sankey_fig.update_layout(title_text="Warehouse → Customer Shipments", font_size=14)
        st.plotly_chart(sankey_fig, use_container_width=True)

        # Heatmap of total cost
        cost_matrix = df.pivot(index='Warehouse', columns='Customer', values='Total Cost').fillna(0)
        st.subheader("💰 Total Cost Heatmap")
        st.dataframe(cost_matrix.style.background_gradient(cmap="Reds"), use_container_width=True)

    else:
        st.info("Run the optimization first to see visualization.")

# ---------------- Tab 6: About ----------------
with tab6:
    st.subheader("ℹ️ About")
    st.markdown("""
    **Developer:** Chadee Fouad - MyWorkDropBox@gmail.com  
    **Development Date:** Nov. 2025  
    [Click here to visit my website](https://myprojectspage.github.io/index.html)
    """)
