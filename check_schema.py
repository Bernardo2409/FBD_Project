from persistence.session import create_connection

conn = create_connection()
cursor = conn.cursor()

# Check for Enfrenta table
print("="*60)
print("Looking for Enfrenta table...")
cursor.execute("""
    SELECT TABLE_NAME 
    FROM INFORMATION_SCHEMA.TABLES 
    WHERE TABLE_SCHEMA='FantasyChamp' 
    AND TABLE_NAME LIKE '%nfrenta%'
""")
tables = cursor.fetchall()
print(f"Tables found: {[t[0] for t in tables]}")
print()

# Check Jogo table structure
print("="*60)
print("Structure of Jogo table:")
cursor.execute("""
    SELECT COLUMN_NAME, DATA_TYPE
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA='FantasyChamp' 
    AND TABLE_NAME='Jogo'
    ORDER BY ORDINAL_POSITION
""")
cols = cursor.fetchall()
for c in cols:
    print(f"  {c[0]:20} {c[1]}")
print()

# Check if Enfrenta exists
cursor.execute("""
    SELECT TABLE_NAME 
    FROM INFORMATION_SCHEMA.TABLES 
    WHERE TABLE_SCHEMA='FantasyChamp' 
    AND TABLE_NAME='Enfrenta'
""")
enfrenta_exists = cursor.fetchone()

if enfrenta_exists:
    print("="*60)
    print("Structure of Enfrenta table:")
    cursor.execute("""
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA='FantasyChamp' 
        AND TABLE_NAME='Enfrenta'
        ORDER BY ORDINAL_POSITION
    """)
    cols = cursor.fetchall()
    for c in cols:
        print(f"  {c[0]:20} {c[1]}")
else:
    print("Enfrenta table DOES NOT EXIST!")

conn.close()
