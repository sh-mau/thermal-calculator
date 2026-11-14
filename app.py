import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import CoolProp.CoolProp as CP

st.set_page_config(page_title="Thermal Calculator", layout="wide")
st.title("Thermal Calculator")


# ---------- Yordamchi funksiyalar ----------
def calculate_enthalpy(p_bar, t_C):
    return CP.PropsSI("H", "P", p_bar * 1e5, "T", t_C + 273.15, "Water") / 1000


def hs_diagram(pressure_bar, temperature_K, fluid="Water"):
    P = pressure_bar * 1e5

    h_pt = CP.PropsSI("H", "P", P, "T", temperature_K, fluid) / 1000
    s_pt = CP.PropsSI("S", "P", P, "T", temperature_K, fluid) / 1000

    fig, ax = plt.subplots(figsize=(9, 7))

    T_min = CP.PropsSI("Ttriple", fluid) + 1
    T_crit = CP.PropsSI("Tcrit", fluid)
    T_sat = np.linspace(T_min, T_crit - 0.01, 300)

    s_liq = [CP.PropsSI("S", "T", T, "Q", 0, fluid) / 1000 for T in T_sat]
    h_liq = [CP.PropsSI("H", "T", T, "Q", 0, fluid) / 1000 for T in T_sat]
    s_vap = [CP.PropsSI("S", "T", T, "Q", 1, fluid) / 1000 for T in T_sat]
    h_vap = [CP.PropsSI("H", "T", T, "Q", 1, fluid) / 1000 for T in T_sat]

    ax.plot(s_liq, h_liq, "b-", linewidth=2, label="Saturated liquid")
    ax.plot(s_vap, h_vap, "r-", linewidth=2, label="Saturated vapor")

    for p_bar in [0.1, 1, 10, 50, 100]:
        Pp = p_bar * 1e5
        T_s = CP.PropsSI("T", "P", Pp, "Q", 0, fluid)

        s_line, h_line = [], []

        for T in np.linspace(T_min, T_s - 0.01, 40):
            s_line.append(CP.PropsSI("S", "P", Pp, "T", T, fluid) / 1000)
            h_line.append(CP.PropsSI("H", "P", Pp, "T", T, fluid) / 1000)

        for q in np.linspace(0, 1, 20):
            s_line.append(CP.PropsSI("S", "P", Pp, "Q", q, fluid) / 1000)
            h_line.append(CP.PropsSI("H", "P", Pp, "Q", q, fluid) / 1000)

        for T in np.linspace(T_s + 0.01, 1100, 60):
            s_line.append(CP.PropsSI("S", "P", Pp, "T", T, fluid) / 1000)
            h_line.append(CP.PropsSI("H", "P", Pp, "T", T, fluid) / 1000)

        ax.plot(s_line, h_line, "gray", linewidth=0.8)
        ax.text(s_line[-1], h_line[-1], f"{p_bar} bar", fontsize=8)

    ax.plot(s_pt, h_pt, "ko", markersize=10,
            label=f"State: {pressure_bar} bar, {temperature_K:.1f} K")
    ax.annotate(f"h={h_pt:.1f}\ns={s_pt:.3f}", (s_pt, h_pt),
                textcoords="offset points", xytext=(10, -25))

    ax.set_xlabel("Entropy s (kJ/kg·K)")
    ax.set_ylabel("Enthalpy h (kJ/kg)")
    ax.set_title("H-S (Mollier) diagram of Water")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()

    return fig, h_pt, s_pt


def steam_water_inputs(prefix):
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("High pressure")
        m_hp = st.number_input("HP mass flow (kg/s)", min_value=0.0, value=10.0, key=f"{prefix}_m_hp")
        p_hw = st.number_input("HP water pressure (bar)", value=100.0, key=f"{prefix}_p_hw")
        t_hw = st.number_input("HP water temp (°C)", value=100.0, key=f"{prefix}_t_hw")
        p_hs = st.number_input("HP steam pressure (bar)", value=100.0, key=f"{prefix}_p_hs")
        t_hs = st.number_input("HP steam temp (°C)", value=500.0, key=f"{prefix}_t_hs")
    with col2:
        st.subheader("Low pressure")
        m_lp = st.number_input("LP mass flow (kg/s)", min_value=0.0, value=5.0, key=f"{prefix}_m_lp")
        p_lw = st.number_input("LP water pressure (bar)", value=10.0, key=f"{prefix}_p_lw")
        t_lw = st.number_input("LP water temp (°C)", value=100.0, key=f"{prefix}_t_lw")
        p_ls = st.number_input("LP steam pressure (bar)", value=10.0, key=f"{prefix}_p_ls")
        t_ls = st.number_input("LP steam temp (°C)", value=250.0, key=f"{prefix}_t_ls")
    return m_hp, p_hw, t_hw, p_hs, t_hs, m_lp, p_lw, t_lw, p_ls, t_ls


def steam_water_power(m_hp, p_hw, t_hw, p_hs, t_hs, m_lp, p_lw, t_lw, p_ls, t_ls):
    if m_hp <= 0 or m_lp <= 0:
        raise ValueError("Mass flow rate must be positive!")

    h_hw = calculate_enthalpy(p_hw, t_hw)
    h_hs = calculate_enthalpy(p_hs, t_hs)
    h_lw = calculate_enthalpy(p_lw, t_lw)
    h_ls = calculate_enthalpy(p_ls, t_ls)

    if h_hs <= h_hw:
        raise ValueError("HP steam enthalpy must exceed water enthalpy.")
    if h_ls <= h_lw:
        raise ValueError("LP steam enthalpy must exceed water enthalpy.")

    q_hp = m_hp * (h_hs - h_hw)
    q_lp = m_lp * (h_ls - h_lw)
    return q_hp, q_lp


def gas_inputs(prefix):
    m_gas = st.number_input("Exhaust gas mass flow rate (kg/s)", min_value=0.0, value=100.0, key=f"{prefix}_m_gas")
    cp_gas = st.number_input("Specific heat capacity of gas (kJ/(kg·K))", min_value=0.0, value=1.1, key=f"{prefix}_cp_gas")
    t_in_gas = st.number_input("Gas inlet temperature (°C)", value=600.0, key=f"{prefix}_t_in_gas")
    t_out_gas = st.number_input("Gas outlet temperature (°C)", value=150.0, key=f"{prefix}_t_out_gas")
    return m_gas, cp_gas, t_in_gas, t_out_gas


def gas_power(m_gas, cp_gas, t_in_gas, t_out_gas):
    if m_gas <= 0 or cp_gas <= 0:
        raise ValueError("Mass flow and Cp must be positive!")
    if t_out_gas > t_in_gas:
        raise ValueError("Gas outlet temperature cannot exceed inlet temperature!")
    return cp_gas * m_gas * (t_in_gas - t_out_gas)


# ---------- Asosiy yorliqlar ----------
tab_heat, tab_hs, tab_hrsg, tab_gt = st.tabs([
    "Heat power",
    "H-S diagram",
    "HRSG",
    "Gas Turbine",
])

# ---------- 1. Heat power ----------
with tab_heat:
    m = st.number_input("Mass flow rate (kg/s)", min_value=0.0, value=1.0, key="h_m")
    cp = st.number_input("Specific heat capacity (kJ/(kg·K))", min_value=0.0, value=4.18, key="h_cp")
    t_in = st.number_input("Inlet temperature (°C)", value=20.0, key="h_tin")
    t_out = st.number_input("Outlet temperature (°C)", value=80.0, key="h_tout")

    if st.button("Calculate", key="calc_heat"):
        if m <= 0 or cp <= 0:
            st.error("Mass flow and Cp must be positive!")
        else:
            q_kW = cp * m * abs(t_out - t_in)
            if t_out > t_in:
                process = "HEATING"
            elif t_in > t_out:
                process = "COOLING"
            else:
                process = "No heat exchange"
            st.subheader(f"Process: {process}")
            st.caption("Q = Cp · m · ΔT")
            st.metric("Heat power", f"{q_kW:.2f} kW")
            st.metric("Heat power", f"{q_kW / 1000:.2f} MW")

# ---------- 2. H-S diagram ----------
with tab_hs:
    p = st.number_input("Pressure (bar)", min_value=0.01, value=10.0, key="hs_p")
    t = st.number_input("Temperature (°C)", value=300.0, key="hs_t")

    if st.button("Plot", key="calc_hs"):
        try:
            fig, h, s = hs_diagram(p, t + 273.15)
            st.pyplot(fig)
            st.write(f"**Enthalpy:** {h:.2f} kJ/kg")
            st.write(f"**Entropy:** {s:.4f} kJ/(kg·K)")
        except ValueError as e:
            st.error(f"Error: {e}")

# ---------- 3. HRSG ----------
with tab_hrsg:
    sub_a, sub_b, sub_c = st.tabs([
        "A. Steam/Water",
        "B. Gas",
        "C. Efficiency",
    ])

    # A. Steam/water
    with sub_a:
        vals_a = steam_water_inputs("ha")

        if st.button("Calculate", key="calc_ha"):
            try:
                q_hp, q_lp = steam_water_power(*vals_a)
                q_tot = q_hp + q_lp

                c1, c2, c3 = st.columns(3)
                c1.metric("LP heat power", f"{q_lp / 1000:.2f} MW")
                c2.metric("HP heat power", f"{q_hp / 1000:.2f} MW")
                c3.metric("Total", f"{q_tot / 1000:.2f} MW")
            except ValueError as e:
                st.error(f"Input error: {e}")
            except Exception as e:
                st.error(f"Calculation error: {e}")

    # B. Gas
    with sub_b:
        st.subheader("Exhaust gas side")
        vals_b = gas_inputs("hb")

        if st.button("Calculate", key="calc_hb"):
            try:
                q_gas = gas_power(*vals_b)
                st.caption("Q = Cp · m · ΔT")
                if q_gas == 0:
                    st.info("No heat exchange happened.")
                c1, c2 = st.columns(2)
                c1.metric("Gas heat power", f"{q_gas:.2f} kW")
                c2.metric("Gas heat power", f"{q_gas / 1000:.2f} MW")
            except ValueError as e:
                st.error(f"Input error: {e}")

    # C. Efficiency
    with sub_c:
        st.subheader("Exhaust gas side")
        gas_vals_c = gas_inputs("hc")
        st.divider()
        st.subheader("Steam/water side")
        sw_vals_c = steam_water_inputs("hc")

        if st.button("Calculate", key="calc_hc"):
            try:
                q_gas = gas_power(*gas_vals_c)
                if q_gas <= 0:
                    raise ValueError("Gas heat power must be greater than zero to calculate efficiency.")

                q_hp, q_lp = steam_water_power(*sw_vals_c)
                q_tot = q_hp + q_lp

                eta = q_tot / q_gas * 100
                loss = q_gas - q_tot

                if eta > 100:
                    st.warning("Efficiency is above 100%. Steam/water side absorbs more heat "
                               "than the gas gives. Please check your inputs.")

                r1, r2, r3 = st.columns(3)
                r1.metric("Gas heat power", f"{q_gas / 1000:.2f} MW")
                r2.metric("HP heat power", f"{q_hp / 1000:.2f} MW")
                r3.metric("LP heat power", f"{q_lp / 1000:.2f} MW")

                r4, r5, r6 = st.columns(3)
                r4.metric("Total steam/water power", f"{q_tot / 1000:.2f} MW")
                r5.metric("Efficiency (direct method)", f"{eta:.2f} %")
                r6.metric("Total heat loss", f"{loss / 1000:.2f} MW")
            except ValueError as e:
                st.error(f"Input error: {e}")
            except Exception as e:
                st.error(f"Calculation error: {e}")

# ---------- 4. Gas Turbine ----------
with tab_gt:
    gt_a, gt_b = st.tabs([
        "A. Electrical efficiency (Real)",
        "B. Idealized thermal efficiency",
    ])

    with gt_a:
        gas_flow = st.number_input("Fuel gas flow (Sm³/h)", min_value=0.0, value=20000.0, key="gt_flow")
        gas_density = st.number_input("Fuel gas density (kg/Sm³)", min_value=0.0, value=0.75, format="%.3f", key="gt_dens")
        LHV = st.number_input("Lower heating value (MJ/kg)", min_value=0.0, value=47.0, key="gt_lhv")
        GT = st.number_input("GT electrical output (MW)", min_value=0.0, value=80.0, key="gt_out")

        if st.button("Calculate", key="calc_gt"):
            try:
                if gas_flow <= 0 or gas_density <= 0 or LHV <= 0 or GT <= 0:
                    raise ValueError("All values must be positive!")

                m_f = (gas_flow * gas_density) / 3600      # kg/s
                Q_in = m_f * LHV                           # MW
                eta_e = (GT / Q_in) * 100                  # %

                if eta_e > 100:
                    st.warning("Efficiency is above 100%. Please check your inputs.")

                heat_rate = 3600 / (eta_e / 100)           # kJ/kWh

                c1, c2 = st.columns(2)
                c1.metric("Fuel mass flow", f"{m_f:.2f} kg/s")
                c2.metric("Fuel heat power", f"{Q_in:.2f} MW")
                c3, c4 = st.columns(2)
                c3.metric("Electrical efficiency", f"{eta_e:.2f} %")
                c4.metric("Heat rate", f"{heat_rate:.2f} kJ/kWh")
            except ValueError as e:
                st.error(f"Input error: {e}")
            except Exception as e:
                st.error(f"Calculation error: {e}")

    with gt_b:
        st.info("Gas Turbine idealized thermal efficiency calculator coming soon.")
