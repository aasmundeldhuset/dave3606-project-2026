import psycopg

conn = psycopg.connect(
    host="localhost",
    port=9876,
    dbname="lego-db",
    user="lego",
    password="bricks",
)

cur = conn.cursor()
cur.execute(
    """
    create table lego_set(
        id text not null primary key,
        name text not null,
        year int null,
        category text null,
        preview_image_url text null
    );
    """
)
cur.execute(
    """
    create table lego_brick(
        brick_id text not null primary key SERIAL,
        brick_type_id text not null,
        color_id int not null,
        name text not null,
        preview_image_url text null
    );
    """
)
cur.execute(
    """
    create table lego_inventory(
        inventory_id text not null primary key SERIAL,
        set_id text not null foreign key,
        brick_type_id text not null foreign key,
        color_id int not null,
        count int not null
    );
    """
)
cur.close()
conn.commit()
conn.close()
