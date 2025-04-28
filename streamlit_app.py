# streamlit_app.py  ── launch with:  streamlit run streamlit_app.py

import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px

# ── Set Starry Night background ─────────────────────────────────────────
page_bg_img = """
<style>
[data-testid="stAppViewContainer"] {
    background: url("https://en.wikipedia.org/wiki/Wanderer_above_the_Sea_of_Fog#/media/File:Caspar_David_Friedrich_-_Wanderer_above_the_Sea_of_Fog.jpeg");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
}
</style>
"""
st.markdown(page_bg_img, unsafe_allow_html=True)

st.markdown(page_bg_img, unsafe_allow_html=True)


st.markdown(page_bg_img, unsafe_allow_html=True)

# ── DB credentials (using Streamlit secrets) ─────────────────────────────
DB = dict(
    host     = st.secrets["DB_HOST"],
    dbname   = st.secrets["DB_NAME"],
    user     = st.secrets["DB_USER"],
    password = st.secrets["DB_PASSWORD"],
    port     = st.secrets.get("DB_PORT", 5432),
)

@st.cache_data(show_spinner=False)
def run_query(sql_text, params=None):
    """Return a DataFrame for the given SELECT statement."""
    with psycopg2.connect(**DB) as conn:
        return pd.read_sql_query(sql_text, conn, params=params)

# ── UI ───────────────────────────────────────────────────────────────────
st.title("🎨 Paintings Database Explorer")

page = st.sidebar.selectbox(
    "Select a page",
    (
        "🛠 SQL Playground + Tables",
        "🎨 Top 20 Styles",
        "🖼 Price vs Size",
    ),
)

# 1 ── SQL Playground + Tables
if page == "🛠 SQL Playground + Tables":
    st.subheader("🛠 Ad-hoc SQL Playground (SELECT-only)")

    default_query = "SELECT * FROM artist LIMIT 10;"
    user_sql = st.text_area("Enter a SELECT statement:", default_query, height=160)

    if st.button("Run query"):
        sql_lower = user_sql.strip().lower()
        if not sql_lower.startswith("select"):
            st.warning("Only **SELECT** statements are allowed.")
        else:
            try:
                df = run_query(user_sql)
                if df.empty:
                    st.info("Query ran, but returned zero rows.")
                else:
                    st.success(f"Returned {len(df)} rows.")
                    st.dataframe(df)
                    
                    # quick numeric scatter if ≥2 numeric cols
                    nums = df.select_dtypes("number")
                    if nums.shape[1] >= 2:
                        x, y = nums.columns[:2]
                        st.plotly_chart(
                            px.scatter(df, x=x, y=y, title=f"{x} vs {y}"),
                            use_container_width=True,
                        )
            except Exception as e:
                st.error(f"Query failed: {e}")

    # Divider
    st.divider()

    # Show all tables + their counts
    st.subheader("📋 All Tables and Row Counts")

    try:
        tables_df = run_query("""
            SELECT relname AS table_name, n_live_tup AS row_count
            FROM pg_stat_user_tables
            ORDER BY table_name;
        """)
        st.dataframe(tables_df)
    except Exception as e:
        st.error(f"Failed to fetch table counts: {e}")

# 2 ── Top 20 Styles
elif page == "🎨 Top 20 Styles":
    st.subheader("🎨 Top 20 Painting Styles")

    df = run_query("""
        SELECT style, COUNT(*) AS works
        FROM   work
        WHERE  style IS NOT NULL
        GROUP  BY style
        ORDER  BY works DESC
        LIMIT  20
    """)
    fig = px.bar(df, x="style", y="works", title="Top 20 Styles")
    st.plotly_chart(fig, use_container_width=True)

# 3 ── Price vs Size
elif page == "🖼 Price vs Size":
    st.subheader("🖼 Price vs Canvas Area")

    df = run_query("""
        SELECT cs.width * cs.height AS area,
               ps.sale_price,
               w.style
        FROM   product_size ps
        JOIN   canvas_size cs USING (size_id)
        JOIN   work         w  USING (work_id)
        WHERE  ps.sale_price IS NOT NULL
    """)
    fig = px.scatter(
        df,
        x="area",
        y="sale_price",
        color="style",
        labels=dict(area="Canvas area (width × height)", sale_price="Sale price"),
        height=600,
    )
    st.plotly_chart(fig, use_container_width=True)
