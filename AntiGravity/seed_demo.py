from app import create_app
from app.extensions import db
from datetime import datetime, timedelta
from decimal import Decimal
from werkzeug.security import generate_password_hash

# Modelos
from app.models.auth import Usuarios, Roles
from app.models.entities import CategoriasProducto, Productos, Motocicletas, Clientes, Proveedores
from app.models.transactions import Compras, DetalleCompra, Facturas, DetalleFactura, Devoluciones
from app.models.finance import CuentasPorCobrar, CuentasPorPagar, Cuotas, Pagos

app = create_app()

def run_seed():
    with app.app_context():
        print("🏍️  INICIANDO CARGA DE DATOS DEMO (SAFE MODE)...")
        
        # ==========================================
        # 1-2. ROLES Y USUARIOS
        # ==========================================
        print("\n[+] Configurando Roles y Usuarios...")
        rol_admin = Roles.query.filter_by(nombre='ADMIN').first()
        if not rol_admin:
            rol_admin = Roles(nombre='ADMIN', descripcion='Acceso Total')
            db.session.add(rol_admin)
            
        rol_emp = Roles.query.filter_by(nombre='EMPLEADO').first()
        if not rol_emp:
            rol_emp = Roles(nombre='EMPLEADO', descripcion='Acceso Operativo Limitado')
            db.session.add(rol_emp)
            
        db.session.commit()

        u_admin = Usuarios.query.filter_by(usuario='admin').first()
        if not u_admin:
            u_admin = Usuarios(usuario='admin', password_hash=generate_password_hash('admin123'), rol_id=rol_admin.id, nombre='Admin Principal', estado='activo')
            db.session.add(u_admin)
            
        u_emp = Usuarios.query.filter_by(usuario='empleado').first()
        if not u_emp:
            u_emp = Usuarios(usuario='empleado', password_hash=generate_password_hash('vendedor123'), rol_id=rol_emp.id, nombre='Vendedor Demo', estado='activo')
            db.session.add(u_emp)
            
        db.session.commit()

        # ==========================================
        # 3. CATEGORÍAS ÚTILES
        # ==========================================
        print("[+] Entrenando Categorías de Inventario...")
        cats = ['Motocicletas', 'Cascos', 'Repuestos', 'Accesorios', 'Lubricantes', 'Electrónica']
        cat_map = {}
        for c in cats:
            obj = CategoriasProducto.query.filter_by(nombre=c).first()
            if not obj:
                obj = CategoriasProducto(nombre=c)
                db.session.add(obj)
                db.session.commit()
            cat_map[c] = obj

        # ==========================================
        # 4-5. PROVEEDORES Y CLIENTES
        # ==========================================
        print("[+] Creando Perfiles Comerciales...")
        prov_demo = Proveedores.query.filter_by(rnc='101010101').first()
        if not prov_demo:
            prov_demo = Proveedores(nombre='MotoPartes Internacionales S.A.', rnc='101010101', telefono='809-555-1010', direccion='Av. Kennedy', contacto='Don Jhon')
            db.session.add(prov_demo)
            
        cli_demo1 = Clientes.query.filter_by(documento='402-1234567-8').first()
        if not cli_demo1:
            cli_demo1 = Clientes(tipo='fisico', nombre='Pedro Motero', documento='402-1234567-8', telefono='829-555-9090', direccion='Brisa del Este')
            db.session.add(cli_demo1)
            
        db.session.commit()

        # ==========================================
        # 6-7. PRODUCTOS Y MOTOCICLETAS
        # ==========================================
        print("[+] Aprovisionando el Almacén...")
        
        # Producto General (Casco)
        p_casco = Productos.query.filter_by(nombre='Casco Certificado DOT MT').first()
        if not p_casco:
            p_casco = Productos(nombre='Casco Certificado DOT MT', categoria_id=cat_map['Cascos'].id, precio=Decimal('4500.00'), estado='disponible')
            db.session.add(p_casco)
            
        db.session.commit()

        # Motos Disponibles
        vins = ['VIN-DEMO-001X', 'VIN-DEMO-002Y', 'VIN-DEMO-SOLD1']
        motos = []
        for v in vins:
            mt = Motocicletas.query.filter_by(vin=v).first()
            if not mt:
                p_moto = Productos(nombre=f"Super Soco {v[-4:]}", categoria_id=cat_map['Motocicletas'].id, precio=Decimal('85000.00'), estado='disponible')
                db.session.add(p_moto)
                db.session.flush()
                mt = Motocicletas(producto_id=p_moto.id, vin=v, marca='Soco', modelo='TC Max', año=2024, color='Negro', tipo_motor='Eléctrico', estado='en inventario')
                db.session.add(mt)
            motos.append(mt)
            
        db.session.commit()

        # Aseguramos que tenemos al menos un ID de moto para "vender"
        if len(motos) >= 3:
            moto_venta_credito = motos[1] # VIN-DEMO-002Y
            moto_venta_contado = motos[2] # VIN-DEMO-SOLD1
        else:
            moto_venta_credito = Motocicletas.query.first()
            moto_venta_contado = Motocicletas.query.first()


        # ==========================================
        # 8-10. COMPRAS Y CUENTAS POR PAGAR
        # ==========================================
        print("[+] Ejecutando Compras y Cuentas por Pagar...")
        
        if not Compras.query.filter_by(pago_inicial=Decimal('1500.00')).first(): # Evitar repetidos estúpidos
            # Compra Contado
            c_contado = Compras(proveedor_id=prov_demo.id, tipo='contado', costo_total=Decimal('3000.00'), pago_inicial=Decimal('3000.00'), metodo_pago='Transferencia', estado='pagada')
            db.session.add(c_contado)
            db.session.flush()
            db.session.add(DetalleCompra(compra_id=c_contado.id, producto_id=p_casco.id, cantidad=10, costo_unitario=Decimal('300.00')))
            
            # Compra Crédito
            c_credito = Compras(proveedor_id=prov_demo.id, tipo='credito', costo_total=Decimal('50000.00'), pago_inicial=Decimal('1500.00'), metodo_pago='Efectivo', estado='parcial')
            db.session.add(c_credito)
            db.session.flush()
            
            # Cuenta por Pagar Emulada
            cxp = CuentasPorPagar(proveedor_id=prov_demo.id, compra_id=c_credito.id, monto_total=Decimal('50000.00'), saldo=Decimal('48500.00'), estado='parcial')
            db.session.add(cxp)
            db.session.commit()

        # ==========================================
        # 11-13. VENTAS, CUENTAS POR COBRAR Y PAGOS
        # ==========================================
        print("[+] Facturando y Realizando Cobros...")
        if not Facturas.query.filter_by(pago_inicial=Decimal('15000.00')).first():
            
            # Venta Contado - Se lleva SOLD1
            moto_venta_contado.estado = 'vendida'
            moto_venta_contado.producto.estado = 'agotado'
            
            f_contado = Facturas(cliente_id=cli_demo1.id, usuario_id=u_admin.id, tipo='contado', subtotal=Decimal('85000.00'), descuento=0, total=Decimal('85000.00'), pago_inicial=Decimal('85000.00'), metodo_pago='Tarjeta', estado='pagada')
            db.session.add(f_contado)
            db.session.flush()
            db.session.add(DetalleFactura(factura_id=f_contado.id, producto_id=moto_venta_contado.producto_id, cantidad=1, precio_unitario=Decimal('85000.00'), descuento=0))

            # Venta Crédito - Llevando 002Y y un casco
            moto_venta_credito.estado = 'vendida'
            moto_venta_credito.producto.estado = 'agotado'
            
            f_cred = Facturas(cliente_id=cli_demo1.id, usuario_id=u_emp.id, tipo='credito', subtotal=Decimal('89500.00'), descuento=0, total=Decimal('89500.00'), pago_inicial=Decimal('15000.00'), metodo_pago='Efectivo', estado='pendiente')
            db.session.add(f_cred)
            db.session.flush()
            
            db.session.add(DetalleFactura(factura_id=f_cred.id, producto_id=moto_venta_credito.producto_id, cantidad=1, precio_unitario=Decimal('85000.00'), descuento=0))
            db.session.add(DetalleFactura(factura_id=f_cred.id, producto_id=p_casco.id, cantidad=1, precio_unitario=Decimal('4500.00'), descuento=0))

            # Cuenta por Cobrar e Iniciar un Pago
            cxc = CuentasPorCobrar(factura_id=f_cred.id, monto_total=Decimal('89500.00'), saldo=Decimal('74500.00'), estado='parcial')
            db.session.add(cxc)
            db.session.flush()
            f_cred.estado = 'parcial'

            # Cuotas
            for i in range(1, 4): # 3 cuotas
                cuota_monto = Decimal('24833.33')
                db.session.add(Cuotas(cuenta_id=cxc.id, numero_cuota=i, fecha_vencimiento=datetime.now().date() + timedelta(days=30*i), monto=cuota_monto, monto_pagado=0, estado='pendiente'))
            
            db.session.commit()
            
            # 14. Abono de un cliente (Simulamos un pago en una cuota)
            primer_cuota = Cuotas.query.filter_by(cuenta_id=cxc.id).first()
            pago = Pagos(cuenta_id=cxc.id, usuario_id=u_admin.id, monto=Decimal('10000.00'), fecha=datetime.now())
            db.session.add(pago)
            cxc.saldo -= Decimal('10000.00')
            primer_cuota.monto_pagado += Decimal('10000.00')
            primer_cuota.estado = 'parcial'
            db.session.commit()

            # ==========================================
            # 14. UNA DEVOLUCIÓN DE CONTADO
            # ==========================================
            dev = Devoluciones(factura_id=f_contado.id, usuario_id=u_admin.id, motivo='Motocicleta defectuosa retornada.', monto_devuelto=Decimal('85000.00'))
            f_contado.estado = 'anulada' 
            # Devuelve moto a inventario
            moto_venta_contado.estado = 'en inventario'
            moto_venta_contado.producto.estado = 'disponible'
            db.session.add(dev)
            db.session.commit()


        print("\n✨ ¡CARGA DEMO FINALIZADA! Sistema lito para exhibición corporativa.")

if __name__ == '__main__':
    run_seed()
