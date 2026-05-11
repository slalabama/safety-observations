from app.database import engine
import sqlalchemy as sa

with engine.connect() as conn:
    conn.execute(sa.text("ALTER TABLE employees ADD COLUMN role VARCHAR DEFAULT 'basic'"))
    conn.commit()
    print('Role column added!')

with engine.connect() as conn:
    result = conn.execute(sa.text("PRAGMA table_info(employees)"))
    cols = [row[1] for row in result]
    print('Columns now:', cols)

with engine.connect() as conn:
    conn.execute(sa.text("UPDATE employees SET role = 'admin' WHERE badge = '00854'"))
    conn.commit()
    print('Charles set to admin!')
