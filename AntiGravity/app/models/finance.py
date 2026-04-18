from datetime import datetime
from app.extensions import db

class CuentasPorCobrar(db.Model):
    __tablename__ = 'cuentas_por_cobrar'
    id = db.Column(db.Integer, primary_key=True)
    factura_id = db.Column(db.Integer, db.ForeignKey('facturas.id'), nullable=False)
    monto_total = db.Column(db.Numeric(12, 2), nullable=False)
    saldo = db.Column(db.Numeric(12, 2), nullable=False)
    estado = db.Column(db.String(20), default='pendiente') # pendiente, pagado, atrasado
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    cuotas = db.relationship('Cuotas', backref='cuenta', lazy=True)
    pagos = db.relationship('Pagos', backref='cuenta', lazy=True)

class Cuotas(db.Model):
    __tablename__ = 'cuotas'
    id = db.Column(db.Integer, primary_key=True)
    cuenta_id = db.Column(db.Integer, db.ForeignKey('cuentas_por_cobrar.id'), nullable=False)
    numero_cuota = db.Column(db.Integer, nullable=False)
    fecha_vencimiento = db.Column(db.Date, nullable=False)
    monto = db.Column(db.Numeric(10, 2), nullable=False)
    mora = db.Column(db.Numeric(10, 2), default=0)
    monto_pagado = db.Column(db.Numeric(10, 2), default=0)
    estado = db.Column(db.String(20), default='pendiente') # pendiente, pagada, atrasada

class Pagos(db.Model):
    __tablename__ = 'pagos'
    id = db.Column(db.Integer, primary_key=True)
    cuenta_id = db.Column(db.Integer, db.ForeignKey('cuentas_por_cobrar.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    monto = db.Column(db.Numeric(12, 2), nullable=False)
    descuento_aplicado = db.Column(db.Numeric(10, 2), default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    usuario = db.relationship('Usuarios')



class CuentasPorPagar(db.Model):
    __tablename__ = 'cuentas_por_pagar'
    id = db.Column(db.Integer, primary_key=True)
    compra_id = db.Column(db.Integer, db.ForeignKey('compras.id'), nullable=False)
    proveedor_id = db.Column(db.Integer, db.ForeignKey('proveedores.id'), nullable=False)
    monto_total = db.Column(db.Numeric(12, 2), nullable=False)
    saldo = db.Column(db.Numeric(12, 2), nullable=False)
    estado = db.Column(db.String(20), default='pendiente') # pendiente, parcial, pagada
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    proveedor = db.relationship('Proveedores', backref='cuentas_por_pagar')
    compra = db.relationship('Compras', backref='cuenta_por_pagar', uselist=False)
    cuotas = db.relationship('CuotasPorPagar', backref='cuenta', lazy=True)

class CuotasPorPagar(db.Model):
    __tablename__ = 'cuotas_por_pagar'
    id = db.Column(db.Integer, primary_key=True)
    cuenta_pagar_id = db.Column(db.Integer, db.ForeignKey('cuentas_por_pagar.id'), nullable=False)
    numero_cuota = db.Column(db.Integer, nullable=False)
    fecha_vencimiento = db.Column(db.Date, nullable=False)
    monto = db.Column(db.Numeric(10, 2), nullable=False)
    mora = db.Column(db.Numeric(10, 2), default=0)
    monto_pagado = db.Column(db.Numeric(10, 2), default=0)
    estado = db.Column(db.String(20), default='pendiente') # pendiente, pagada, atrasada, parcial

class PagosProveedor(db.Model):
    __tablename__ = 'pagos_proveedor'
    id = db.Column(db.Integer, primary_key=True)
    cuenta_pagar_id = db.Column(db.Integer, db.ForeignKey('cuentas_por_pagar.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    monto = db.Column(db.Numeric(12, 2), nullable=False)
    referencia = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    cuenta = db.relationship('CuentasPorPagar', backref='pagos', lazy=True)
    usuario = db.relationship('Usuarios')
