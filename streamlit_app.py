# streamlit_app.py  ── launch with:  streamlit run streamlit_app.py
import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px

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
        "SQL Playground",    # 👈 move SQL Playground first
        "Artists",
        "Museums",
        "Works by Style",
        "Price-vs-Size",
    ),
)

# 1 ── SQL Playground (read-only SELECTs)
if page == "SQL Playground":
    st.subheader("🛠 Ad-hoc SQL Playground (SELECT-only)")

    default = "SELECT * FROM artist LIMIT 10;"
    user_sql = st.text_area("Enter a SELECT statement:", default, height=160)

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

                    # quick numeric scatter if ≥2 numeric columns
                    nums = df.select_dtypes("number")
                    if nums.shape[1] >= 2:
                        x, y = nums.columns[:2]
                        st.plotly_chart(
                            px.scatter(df, x=x, y=y, title=f"{x} vs {y}"),
                            use_container_width=True,
                        )
            except Exception as e:
                st.error(f"Query failed: {e}")

# 2 ── Artists table
elif page == "Artists":
    df = run_query("""
        SELECT artist_id, last_name, first_name,
               nationality, style, birth, death
        FROM   artist
        ORDER  BY last_name
    """)
    st.subheader(f"👨‍🎨 Artists ({len(df)} rows)")
    st.dataframe(df)

# 3 ── Museums (+ location)
elif page == "Museums":
    df = run_query("""
        SELECT m.museum_id, m.name,
               pc.city, pc.state, pc.country,
               m.url
        FROM   museum m
        LEFT JOIN postalcode pc USING (postal)
        ORDER  BY country, state, city
    """)
    st.subheader(f"🏛 Museums ({len(df)} rows)")
    st.dataframe(df.set_index("museum_id"))

# 4 ── Top 20 styles (bar chart)
elif page == "Works by Style":
    df = run_query("""
        SELECT style, COUNT(*) AS works
        FROM   work
        WHERE  style IS NOT NULL
        GROUP  BY style
        ORDER  BY works DESC
        LIMIT  20
    """)
    st.subheader(f"🎨 Top 20 Styles ({len(df)} styles)")
    fig = px.bar(df, x="style", y="works", title="Top 20 Styles")
    st.plotly_chart(fig, use_container_width=True)

# 5 ── Price vs canvas area (scatter)
elif page == "Price-vs-Size":
    df = run_query("""
        SELECT cs.width * cs.height AS area,
               ps.sale_price,
               w.style
        FROM   product_size ps
        JOIN   canvas_size cs USING (size_id)
        JOIN   work         w  USING (work_id)
        WHERE  ps.sale_price IS NOT NULL
    """)
    st.subheader(f"🖼 Price vs Size ({len(df)} rows)")
    fig = px.scatter(
        df,
        x="area",
        y="sale_price",
        color="style",
        labels=dict(area="Canvas area (width × height)", sale_price="Sale price"),
        height=600,
    )
    st.plotly_chart(fig, use_container_width=True)
