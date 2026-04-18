from app import create_app
from app.extensions import db
from datetime import datetime
from werkzeug.security import generate_password_hash

# Modelos
from app.models.auth import Usuarios, Roles, Auditoria
from app.models.entities import CategoriasProducto, Productos, Motocicletas, Clientes, Proveedores
from app.models.transactions import Compras, DetalleCompra, Facturas, DetalleFactura, Devoluciones
from app.models.finance import CuentasPorCobrar, CuentasPorPagar, Cuotas, Pagos, CuotasPorPagar, PagosProveedor

app = create_app()

def wipe_and_reset():
    with app.app_context():
        print("🚨 INICIANDO WIPE DE DATOS (FASE 1) 🚨")
        
        try:
            # Orden estricto según Foreign Keys (Bottom-Up)
            print("1. Borrando Auditoría...")
            db.session.query(Auditoria).delete()
            
            print("2. Borrando Detalle Factura y Devoluciones...")
            db.session.query(DetalleFactura).delete()
            db.session.query(Devoluciones).delete()
            
            print("3. Borrando Cuotas y Pagos Clientes...")
            db.session.query(Cuotas).delete()
            db.session.query(Pagos).delete()
            
            print("4. Borrando Cuentas por Cobrar...")
            db.session.query(CuentasPorCobrar).delete()
            
            print("5. Borrando Facturas...")
            db.session.query(Facturas).delete()
            
            print("6. Borrando Detalle Compra y Pagos Proveedor...")
            db.session.query(DetalleCompra).delete()
            db.session.query(PagosProveedor).delete()
            
            print("7. Borrando Cuotas por Pagar...")
            db.session.query(CuotasPorPagar).delete()
            
            print("8. Borrando Cuentas por Pagar...")
            db.session.query(CuentasPorPagar).delete()
            
            print("9. Borrando Compras...")
            db.session.query(Compras).delete()
            
            print("10. Borrando Motocicletas...")
            db.session.query(Motocicletas).delete()
            
            print("11. Borrando Productos...")
            db.session.query(Productos).delete()
            
            print("12. Borrando Proveedores...")
            db.session.query(Proveedores).delete()
            
            print("13. Borrando Clientes...")
            db.session.query(Clientes).delete()

            # Confirmar purga transaccional
            db.session.commit()
            print("✅ LIMPIEZA TRANSACCIONAL EXITOSA.")

            print("\n⚙️ PREPARANDO DATOS BASE (FASE 2) ⚙️")
            # Asegurar Roles
            rol_admin = Roles.query.filter_by(nombre='ADMIN').first()
            if not rol_admin:
                rol_admin = Roles(nombre='ADMIN', descripcion='Acceso Total')
                db.session.add(rol_admin)
                
            rol_emp = Roles.query.filter_by(nombre='EMPLEADO').first()
            if not rol_emp:
                rol_emp = Roles(nombre='EMPLEADO', descripcion='Acceso Operativo Limitado')
                db.session.add(rol_emp)
                
            db.session.commit()

            # Asegurar Usuarios
            u_admin = Usuarios.query.filter_by(usuario='admin').first()
            if not u_admin:
                u_admin = Usuarios(usuario='admin', password_hash=generate_password_hash('admin123'), rol_id=rol_admin.id, nombre='Admin Principal', estado='activo')
                db.session.add(u_admin)
            
            u_emp = Usuarios.query.filter_by(usuario='empleado').first()
            if not u_emp:
                u_emp = Usuarios(usuario='empleado', password_hash=generate_password_hash('vendedor123'), rol_id=rol_emp.id, nombre='Vendedor Demo', estado='activo')
                db.session.add(u_emp)

            # Asegurar Categoría Base
            cat_motos = CategoriasProducto.query.filter_by(nombre='Motocicletas').first()
            if not cat_motos:
                cat_motos = CategoriasProducto(nombre='Motocicletas')
                db.session.add(cat_motos)

            # Parche Base para Pruebas: Un Cliente Genérico y Un Proveedor
            cli = Clientes.query.filter_by(documento='000000000').first()
            if not cli:
                cli = Clientes(tipo='fisico', nombre='Cliente Mostrador Principal', documento='000000000', telefono='N/A')
                db.session.add(cli)
                
            prov = Proveedores.query.filter_by(rnc='00000').first()
            if not prov:
                prov = Proveedores(nombre='Proveedor Raíz de Fabrica', rnc='00000', telefono='N/A', contacto='N/A')
                db.session.add(prov)

            db.session.commit()
            print("✅ ENTORNO BASE CARGADO.")
            print("Sistema purgado y listo para las pruebas de AntiGravity.")

        except Exception as e:
            db.session.rollback()
            print(f"❌ ERROR FATAL DURANTE WIPING: {str(e)}")

if __name__ == '__main__':
    wipe_and_reset()
