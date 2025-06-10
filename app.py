import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
import plotly.express as px
from datetime import datetime
from prophet import Prophet
from database import get_sales_data, insert_sale

# Authentication
names = ["Admin User", "Sales User"]
usernames = ["admin", "sales"]


passwords = ['mypassword']  # Plaintext passwords
hasher = stauth.Hasher()    # Instantiate with no arguments
hashed_passwords= stauth.Hasher(passwords).generate()[0] # Generate hashes


authenticator = stauth.Authenticate(names, usernames, hashed_passwords,
                                    "root", "12345", cookie_expiry_days=30)

name, auth_status, username = authenticator.login("Login", "sidebar")
if auth_status is False:
    st.error("Username/password is incorrect")
elif auth_status is None:
    st.warning("Please enter your username and password")
elif auth_status:
    authenticator.logout("Logout", "sidebar")
    st.sidebar.success(f"Welcome, {name}")

    st.set_page_config(page_title="Smart Sales Dashboard", layout="centered")
    st.title("📊 Smart Sales Dashboard")

    auto_refresh = st.checkbox("Auto-refresh every 10 seconds")
    if auto_refresh:
        st.experimental_rerun()

    df = get_sales_data()
    df['date'] = pd.to_datetime(df['date'])

    with st.sidebar:
        st.header("🔍 Filters")
        selected_products = st.multiselect("Select Products", options=df['product'].unique())
        selected_locations = st.multiselect("Select Locations", options=df['location'].unique())
        date_range = st.date_input("Select Date Range", [df['date'].min(), df['date'].max()])

    if selected_products:
        df = df[df['product'].isin(selected_products)]
    if selected_locations:
        df = df[df['location'].isin(selected_locations)]
    df = df[(df['date'] >= pd.to_datetime(date_range[0])) & (df['date'] <= pd.to_datetime(date_range[1]))]

    total_sales = (df['price'] * df['quantity']).sum()
    total_orders = df.shape[0]
    avg_order_value = total_sales / total_orders if total_orders else 0
    unique_customers = df['customer_name'].nunique()

    st.markdown("### 🔹 Key Performance Indicators")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Sales ($)", f"{total_sales:,.2f}")
    col2.metric("Total Orders", total_orders)
    col3.metric("Avg Order Value ($)", f"{avg_order_value:,.2f}")
    col4.metric("Unique Customers", unique_customers)

    daily_sales = df.groupby('date').apply(lambda x: (x['price'] * x['quantity']).sum()).reset_index(name='revenue')
    fig1 = px.line(daily_sales, x='date', y='revenue', title="📅 Daily Revenue")
    st.plotly_chart(fig1, use_container_width=True)

    top_products = df.groupby('product').apply(lambda x: (x['price'] * x['quantity']).sum()).sort_values(ascending=False).head(5).reset_index(name='revenue')
    fig2 = px.bar(top_products, x='product', y='revenue', title="🏆 Top 5 Products")
    st.plotly_chart(fig2, use_container_width=True)

    location_sales = df.groupby('location').apply(lambda x: (x['price'] * x['quantity']).sum()).reset_index(name='revenue')
    fig3 = px.pie(location_sales, values='revenue', names='location', title="📍 Sales by Location")
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown("---")
    st.markdown("### ➕ Add New Sale")
    with st.form("add_sale"):
        col1, col2, col3 = st.columns(3)
        with col1:
            date = st.date_input("Date", datetime.today())
            product = st.text_input("Product")
        with col2:
            quantity = st.number_input("Quantity", min_value=1, step=1)
            price = st.number_input("Price", min_value=0.0, step=0.01)
        with col3:
            customer_name = st.text_input("Customer Name")
            location = st.text_input("Location")
        submitted = st.form_submit_button("Submit Sale")
        if submitted:
            insert_sale(date, product, quantity, price, customer_name, location)
            st.success("✅ Sale added successfully!")
            st.experimental_rerun()

    # Forecasting
    st.markdown("---")
    st.markdown("### 🔮 30-Day Sales Forecast")
    df_forecast = df[['date', 'price']].rename(columns={'date': 'ds', 'price': 'y'})
    model = Prophet()
    model.fit(df_forecast)
    future = model.make_future_dataframe(periods=30)
    forecast = model.predict(future)
    fig_forecast = px.line(forecast, x='ds', y='yhat', title='📈 Forecasted Sales')
    st.plotly_chart(fig_forecast, use_container_width=True)