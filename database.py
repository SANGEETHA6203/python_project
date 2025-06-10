from sqlalchemy import create_engine, text
import pandas as pd

host = "localhost"
port = 3306
user = "root"
password = "12345"
database = "salesdb"

connection_str = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
engine = create_engine(connection_str)

def get_sales_data():
    query = "SELECT * FROM sales"
    df = pd.read_sql(query, engine)
    return df

def insert_sale(date, product, quantity, price, customer_name, location):
    with engine.connect() as conn:
        stmt = text("""
            INSERT INTO sales (date, product, quantity, price, customer_name, location)
            VALUES (:date, :product, :quantity, :price, :customer_name, :location)
        """)
        conn.execute(stmt, {
            'date': date,
            'product': product,
            'quantity': quantity,
            'price': price,
            'customer_name': customer_name,
            'location': location
        })
        conn.commit()