# streamlit_app.py — launch with:  streamlit run streamlit_app.py
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

# ── Page config ───────────────────────────────────────────────────────────
st.set_page_config(page_title="Paintings Explorer", layout="wide")

# ── Background Image ──────────────────────────────────────────────────────
page_bg_img = """
<style>
/* Background of entire app */
[data-testid="stAppViewContainer"] {
    background-image: url("https://upload.wikimedia.org/wikipedia/commons/thumb/e/ea/Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg/800px-Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg");
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
}

/* Transparent header */
[data-testid="stHeader"] {
    background: rgba(0,0,0,0);
}

/* Sidebar background */
[data-testid="stSidebar"] {
    background-color: rgba(0,0,0,0.85);
}

/* Sidebar texts */
[data-testid="stSidebar"] * {
    color: #f0f0f0;
}

/* Fix dropdown text inside sidebar */
[data-baseweb="select"] > div {
    color: #f0f0f0;
}

/* Fix button text */
button[kind="secondary"] > div {
    color: #000000 !important; /* Make "Run Query" button text black */
    font-weight: bold;
}

/* Fix text inputs / textarea text color */
textarea, input, select {
    color: #000000 !important; /* Black typing text */
}

/* General text on main page */
h1, h2, h3, h4, h5, h6, p, label, div, span, th, td {
    color: #ffffff;
}
</style>
"""



st.markdown(page_bg_img, unsafe_allow_html=True)

# ── UI ───────────────────────────────────────────────────────────────────
st.title("🎨 Paintings Database Explorer")

page = st.sidebar.selectbox(
    "Select a page",
    (
        "🛠 SQL Playground + Tables",
        "🌎 Artists by Country",
        "🎨 Top 20 Styles",
        "📈 Price vs Canvas Area",
    ),
)

# 1 ── SQL Playground + Table Counts
if page == "🛠 SQL Playground + Tables":
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
                    nums = df.select_dtypes("number")
                    if nums.shape[1] >= 2:
                        x, y = nums.columns[:2]
                        st.plotly_chart(
                            px.scatter(df, x=x, y=y, title=f"{x} vs {y}"),
                            use_container_width=True,
                        )
            except Exception as e:
                st.error(f"Query failed: {e}")

    st.markdown("---")
    st.subheader("📋 Tables in Database (with Row Counts)")
    
    tables_df = run_query("""
        SELECT relname AS table_name, n_live_tup AS row_count
        FROM   pg_stat_user_tables
        ORDER  BY table_name;
    """)
    st.dataframe(tables_df)

# 2 ── Artists by Country
elif page == "🌎 Artists by Country":
    st.subheader("🌎 Number of Artists by Nationality")
    df = run_query("""
        SELECT nationality, COUNT(*) AS artist_count
        FROM   artist
        WHERE  nationality IS NOT NULL
        GROUP  BY nationality
        ORDER  BY artist_count DESC
        LIMIT  20;
    """)
    fig = px.bar(df, x="nationality", y="artist_count", title="Top 20 Countries by Number of Artists")
    st.plotly_chart(fig, use_container_width=True)

# 3 ── Top 20 Styles
elif page == "🎨 Top 20 Styles":
    st.subheader("🎨 Most Popular Painting Styles")
    df = run_query("""
        SELECT style, COUNT(*) AS style_count
        FROM   work
        WHERE  style IS NOT NULL
        GROUP  BY style
        ORDER  BY style_count DESC
        LIMIT  20;
    """)
    fig = px.bar(df, x="style", y="style_count", title="Top 20 Styles")
    st.plotly_chart(fig, use_container_width=True)

# 4 ── Price vs Canvas Area
elif page == "📈 Price vs Canvas Area":
    st.subheader("📈 Sale Price vs Canvas Area")
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
        labels=dict(area="Canvas Area (width × height)", sale_price="Sale Price"),
        height=600,
    )
    st.plotly_chart(fig, use_container_width=True)
