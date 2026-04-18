from datetime import datetime
from app.extensions import db

class Clientes(db.Model):
    __tablename__ = 'clientes'
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(20), nullable=False) # fisico, juridico
    nombre = db.Column(db.String(150), nullable=False)
    documento = db.Column(db.String(50), unique=True, nullable=False)
    telefono = db.Column(db.String(20))
    direccion = db.Column(db.String(255))
    
    # Datos del garante
    nombre_garante = db.Column(db.String(150))
    documento_garante = db.Column(db.String(50))
    telefono_garante = db.Column(db.String(20))
    direccion_garante = db.Column(db.String(255))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Proveedores(db.Model):
    __tablename__ = 'proveedores'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), unique=True, nullable=False)
    rnc = db.Column(db.String(50))
    telefono = db.Column(db.String(20))
    direccion = db.Column(db.String(255))
    contacto = db.Column(db.String(100))
    estado = db.Column(db.String(20), default='activo')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class CategoriasProducto(db.Model):
    __tablename__ = 'categorias_producto'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    descripcion = db.Column(db.String(255))
    
    productos = db.relationship('Productos', backref='categoria', lazy=True)

class Productos(db.Model):
    __tablename__ = 'productos'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias_producto.id'), nullable=False)
    precio = db.Column(db.Numeric(10, 2), nullable=False)
    stock = db.Column(db.Integer, default=0)
    estado = db.Column(db.String(20), default='disponible')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    motocicleta = db.relationship('Motocicletas', backref='producto', uselist=False)

class Motocicletas(db.Model):
    __tablename__ = 'motocicletas'
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey('productos.id'), nullable=False)
    vin = db.Column(db.String(50), unique=True, nullable=False)
    marca = db.Column(db.String(100), nullable=False)
    modelo = db.Column(db.String(100), nullable=False)
    año = db.Column(db.Integer, nullable=False)
    color = db.Column(db.String(50))
    tipo_motor = db.Column(db.String(100))
    estado = db.Column(db.String(20), default='en inventario')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
