import sqlite3
import os

def migrate_db():
    db_path = os.path.join('instance', 'motocicletas.db')
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. Update Compras
        try:
            cursor.execute("ALTER TABLE compras ADD COLUMN pago_inicial NUMERIC(12, 2) DEFAULT 0")
            cursor.execute("ALTER TABLE compras ADD COLUMN metodo_pago VARCHAR(50)")
            cursor.execute("ALTER TABLE compras ADD COLUMN estado VARCHAR(20) DEFAULT 'activa'")
            print("Successfully updated 'compras' table.")
        except sqlite3.OperationalError as e:
            print(f"Update compras skipped or error: {e}")

        # 2. Update CuentasPorPagar
        try:
            cursor.execute("ALTER TABLE cuentas_por_pagar RENAME COLUMN total TO monto_total")
            cursor.execute("ALTER TABLE cuentas_por_pagar RENAME COLUMN saldo_pendiente TO saldo")
            cursor.execute("ALTER TABLE cuentas_por_pagar RENAME COLUMN fecha TO created_at")
            print("Successfully renamed columns in 'cuentas_por_pagar'.")
        except sqlite3.OperationalError as e:
            print(f"Update cuentas_por_pagar skipped or error: {e}")

        # 3. Update PagosProveedores to pagos_proveedor
        try:
            cursor.execute("ALTER TABLE pagos_proveedores RENAME TO pagos_proveedor")
            cursor.execute("ALTER TABLE pagos_proveedor RENAME COLUMN cuenta_id TO cuenta_pagar_id")
            cursor.execute("ALTER TABLE pagos_proveedor ADD COLUMN referencia VARCHAR(255)")
            cursor.execute("ALTER TABLE pagos_proveedor ADD COLUMN created_at DATETIME")
            print("Successfully updated and renamed 'pagos_proveedores'.")
        except sqlite3.OperationalError as e:
            print(f"Update pagos_proveedor skipped or error: {e}")

        # 4. Create CuotasPorPagar
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS cuotas_por_pagar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cuenta_pagar_id INTEGER NOT NULL,
            numero_cuota INTEGER NOT NULL,
            fecha_vencimiento DATE NOT NULL,
            monto NUMERIC(10, 2) NOT NULL,
            mora NUMERIC(10, 2) DEFAULT 0,
            monto_pagado NUMERIC(10, 2) DEFAULT 0,
            estado VARCHAR(20) DEFAULT 'pendiente',
            FOREIGN KEY (cuenta_pagar_id) REFERENCES cuentas_por_pagar(id)
        )
        """)
        print("Successfully created 'cuotas_por_pagar'.")

        conn.commit()
        print("Migration complete!")
    except Exception as e:
        print(f"Critical Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_db()
