from datetime import datetime
from app.extensions import db

class Compras(db.Model):
    __tablename__ = 'compras'
    id = db.Column(db.Integer, primary_key=True)
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedores.id'), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    tipo = db.Column(db.String(20), nullable=False, server_default='contado') # contado, credito
    costo_total = db.Column(db.Numeric(12, 2), nullable=False)
    pago_inicial = db.Column(db.Numeric(12, 2), default=0)
    metodo_pago = db.Column(db.String(50))
    estado = db.Column(db.String(20), default='pendiente') # pendiente, anulada, pagada, parcial
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    proveedor = db.relationship('Proveedores', backref='compras')
    detalles = db.relationship('DetalleCompra', backref='compra', lazy=True)

class DetalleCompra(db.Model):
    __tablename__ = 'detalle_compra'
    id = db.Column(db.Integer, primary_key=True)
    compra_id = db.Column(db.Integer, db.ForeignKey('compras.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    costo_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    
    producto = db.relationship('Productos')

class Facturas(db.Model):
    __tablename__ = 'facturas'
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    tipo = db.Column(db.String(20), nullable=False) # contado, credito
    subtotal = db.Column(db.Numeric(12, 2), nullable=False)
    descuento = db.Column(db.Numeric(12, 2), default=0)
    total = db.Column(db.Numeric(12, 2), nullable=False)
    pago_inicial = db.Column(db.Numeric(12, 2), default=0)
    metodo_pago = db.Column(db.String(50))
    estado = db.Column(db.String(20), default='pagada')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    cliente = db.relationship('Clientes', backref='facturas')
    usuario = db.relationship('Usuarios', backref='facturas_generadas')
    detalles = db.relationship('DetalleFactura', backref='factura', lazy=True)
    cuenta_por_cobrar = db.relationship('CuentasPorCobrar', backref='factura', uselist=False)

class DetalleFactura(db.Model):
    __tablename__ = 'detalle_factura'
    id = db.Column(db.Integer, primary_key=True)
    factura_id = db.Column(db.Integer, db.ForeignKey('facturas.id'), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    descuento = db.Column(db.Numeric(10, 2), default=0)
    
    producto = db.relationship('Productos')

class Devoluciones(db.Model):
    __tablename__ = 'devoluciones'
    id = db.Column(db.Integer, primary_key=True)
    factura_id = db.Column(db.Integer, db.ForeignKey('facturas.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    motivo = db.Column(db.String(255), nullable=False)
    monto_devuelto = db.Column(db.Numeric(12, 2), nullable=False)
    
    factura = db.relationship('Facturas', backref='devoluciones')
    usuario = db.relationship('Usuarios')
