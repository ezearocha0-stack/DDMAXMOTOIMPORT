from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.extensions import db
from app.models.entities import Motocicletas, Productos, CategoriasProducto
from sqlalchemy import or_
from decimal import Decimal
from sqlalchemy.orm import joinedload
from app.routes.auth import admin_required

inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')

def _get_or_create_motorcycle_category():
    categoria = CategoriasProducto.query.filter_by(nombre='Motocicletas').first()
    if not categoria:
        categoria = CategoriasProducto(nombre='Motocicletas', descripcion='Vehículos de dos ruedas motorizados')
        db.session.add(categoria)
        db.session.commit()
    return categoria

@inventory_bp.route('/')
def list_motorcycles():
    search = request.args.get('search', '')
    query = Motocicletas.query
    if search:
        query = query.filter(or_(
            Motocicletas.marca.ilike(f'%{search}%'),
            Motocicletas.modelo.ilike(f'%{search}%'),
            Motocicletas.vin.ilike(f'%{search}%')
        ))
    
    motocicletas = query.options(joinedload(Motocicletas.producto)).order_by(Motocicletas.id.desc()).all()
    return render_template('inventory/list.html', motocicletas=motocicletas, search=search)

@inventory_bp.route('/create', methods=['GET', 'POST'])
def create_motorcycle():
    if request.method == 'POST':
        marca = request.form.get('marca')
        modelo = request.form.get('modelo')
        año = request.form.get('año')
        color = request.form.get('color')
        tipo_motor = request.form.get('tipo_motor')
        vin = request.form.get('vin')
        precio_raw = request.form.get('precio', '').strip()
        estado = request.form.get('estado', 'en inventario')
        
        if not marca or not modelo or not vin or not precio_raw:
            flash('Marca, Modelo, VIN y Precio son obligatorios.', 'danger')
            return redirect(url_for('inventory.create_motorcycle'))

        # limpiar formato
        precio_limpio = precio_raw.replace('$', '').replace(',', '')
        
        try:
            precio_final = Decimal(precio_limpio)
        except Exception:
            flash('Precio final debe ser un número válido.', 'danger')
            return redirect(url_for('inventory.create_motorcycle'))

        categoria = _get_or_create_motorcycle_category()

        try:
            # Crear Producto primero
            producto = Productos(
                nombre=f"{marca} {modelo} ({año})",
                categoria_id=categoria.id,
                precio=precio_final,
                estado='disponible'
            )
            db.session.add(producto)
            db.session.flush() # obtener id

            # Parse year safely
            try:
                año_val = int(año) if año else 0
            except ValueError:
                db.session.rollback()
                flash("El año debe ser un número válido.", "danger")
                return redirect(url_for('inventory.create_motorcycle'))

            # Crear Motocicleta
            motocicleta = Motocicletas(
                producto_id=producto.id,
                vin=vin,
                marca=marca,
                modelo=modelo,
                año=año_val,
                color=color,
                tipo_motor=tipo_motor,
                estado=estado
            )
            db.session.add(motocicleta)
            db.session.commit()
            
            flash('Motocicleta agregada al inventario exitosamente.', 'success')
            return redirect(url_for('inventory.list_motorcycles'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear la motocicleta: {str(e)}', 'danger')

    return render_template('inventory/form.html', motocicleta=None)

@inventory_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_motorcycle(id):
    motocicleta = db.session.get(Motocicletas, id)
    if not motocicleta:
        flash('Motocicleta no encontrada en el inventario.', 'danger')
        return redirect(url_for('inventory.list_motorcycles'))

    if request.method == 'POST':
        marca = request.form.get('marca')
        modelo = request.form.get('modelo')
        año = request.form.get('año')
        color = request.form.get('color')
        tipo_motor = request.form.get('tipo_motor')
        nuevo_vin = request.form.get('vin')
        precio_raw = request.form.get('precio', '').strip()
        estado = request.form.get('estado')

        if nuevo_vin != motocicleta.vin:
            existing = Motocicletas.query.filter_by(vin=nuevo_vin).first()
            if existing:
                flash(f'Ya existe otra motocicleta con el VIN {nuevo_vin}.', 'danger')
                return redirect(url_for('inventory.edit_motorcycle', id=id))
        
        if not precio_raw:
            flash('El precio es requerido', 'danger')
            return redirect(url_for('inventory.edit_motorcycle', id=id))
            
        precio_limpio = precio_raw.replace('$', '').replace(',', '')
        try:
            precio_final = Decimal(precio_limpio)
        except Exception:
            flash('Precio final debe ser un número válido.', 'danger')
            return redirect(url_for('inventory.edit_motorcycle', id=id))

        try:
            # Parse year safely
            try:
                año_val = int(año) if año else 0
            except ValueError:
                flash("El año debe ser un número válido.", "danger")
                return redirect(url_for('inventory.edit_motorcycle', id=id))
                
            # Actualizar Motocicleta
            motocicleta.marca = marca
            motocicleta.modelo = modelo
            motocicleta.año = año_val
            motocicleta.color = color
            motocicleta.tipo_motor = tipo_motor
            motocicleta.vin = nuevo_vin
            motocicleta.estado = estado
            
            # Actualizar Producto asociado
            if motocicleta.producto:
                motocicleta.producto.nombre = f"{marca} {modelo} ({año})"
                motocicleta.producto.precio = precio_final
                
                # Sincronizar estado del producto y la motocicleta de forma básica
                if estado == 'vendida':
                    motocicleta.producto.estado = 'agotado'
                else:
                    motocicleta.producto.estado = 'disponible'

            db.session.commit()
            flash('Motocicleta actualizada exitosamente.', 'success')
            return redirect(url_for('inventory.list_motorcycles'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar la motocicleta: {str(e)}', 'danger')

    return render_template('inventory/form.html', motocicleta=motocicleta)

@inventory_bp.route('/delete/<int:id>', methods=['POST'])
@admin_required
def delete_motorcycle(id):
    motocicleta = db.session.get(Motocicletas, id)
    if not motocicleta:
        flash('Motocicleta no encontrada.', 'danger')
        return redirect(url_for('inventory.list_motorcycles'))
        
    try:
        producto = motocicleta.producto
        db.session.delete(motocicleta)
        
        # Opcional: Eliminar el producto asociado si corresponde
        if producto:
            db.session.delete(producto)
            
        db.session.commit()
        flash('Motocicleta eliminada del inventario.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'No se puede eliminar la motocicleta. Es posible que esté asociada a ventas o facturas.', 'danger')

    return redirect(url_for('inventory.list_motorcycles'))

@inventory_bp.route('/detail/<int:id>')
def detail_motorcycle(id):
    motocicleta = db.session.get(Motocicletas, id)
    if not motocicleta:
        flash('Motocicleta no encontrada.', 'danger')
        return redirect(url_for('inventory.list_motorcycles'))
        
    return render_template('inventory/detail.html', motocicleta=motocicleta)

# --- GENERAL PRODUCTS ROUTES ---

@inventory_bp.route('/products')
def list_products():
    search = request.args.get('search', '')
    estado = request.args.get('estado', 'disponibles')
    
    query = Productos.query.outerjoin(Motocicletas).filter(Motocicletas.id == None)
    
    if estado == 'disponibles':
        query = query.filter(Productos.estado == 'disponible')
    elif estado == 'agotados':
        query = query.filter(Productos.estado == 'agotado')
    
    if search:
        query = query.filter(Productos.nombre.ilike(f'%{search}%'))
        
    productos = query.options(joinedload(Productos.categoria)).order_by(Productos.id.desc()).all()
    return render_template('inventory/products_list.html', productos=productos, search=search, estado_actual=estado)

@inventory_bp.route('/products/create', methods=['GET', 'POST'])
def create_product():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        categoria_id = request.form.get('categoria_id')
        costo = request.form.get('costo')
        precio_raw = request.form.get('precio', '').strip()
        itbis = request.form.get('itbis', '0')
        stock = request.form.get('stock', '0')
        estado = request.form.get('estado', 'disponible')

        if not nombre or not categoria_id or not precio_raw:
            flash('Nombre, Categoría y Precio son obligatorios.', 'danger')
            return redirect(url_for('inventory.create_product'))

        precio_limpio = precio_raw.replace('$', '').replace(',', '')
        try:
            precio_val = Decimal(precio_limpio)
            stock_val = int(stock)
            estado_calc = 'disponible' if stock_val > 0 else 'agotado'
                
            producto = Productos(
                nombre=nombre,
                categoria_id=int(categoria_id),
                precio=precio_val,
                stock=stock_val,
                estado=estado_calc
            )
            db.session.add(producto)
            db.session.commit()
            
            flash('Producto general agregado al inventario exitosamente.', 'success')
            return redirect(url_for('inventory.list_products'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear el producto (Verifique que el precio sea numérico): {str(e)}', 'danger')

    categorias = CategoriasProducto.query.all()
    return render_template('inventory/products_form.html', producto=None, categorias=categorias)

@inventory_bp.route('/products/edit/<int:id>', methods=['GET', 'POST'])
def edit_product(id):
    producto = db.session.get(Productos, id)
    if not producto or producto.motocicleta:
        flash('Producto general no encontrado.', 'danger')
        return redirect(url_for('inventory.list_products'))

    if request.method == 'POST':
        nombre = request.form.get('nombre')
        categoria_id = request.form.get('categoria_id')
        costo = request.form.get('costo')
        precio_raw = request.form.get('precio', '').strip()
        itbis = request.form.get('itbis', '0')
        stock = request.form.get('stock', '0')
        estado = request.form.get('estado')
        
        
        if not precio_raw:
            flash('El precio es requerido', 'danger')
            return redirect(url_for('inventory.list_products'))
            
        precio_limpio = precio_raw.replace('$', '').replace(',', '')
        try:
            producto.nombre = nombre
            producto.categoria_id = int(categoria_id)
            producto.precio = Decimal(precio_limpio)
            producto.stock = int(stock)
            producto.estado = 'disponible' if producto.stock > 0 else 'agotado'
            db.session.commit()
            flash('Producto actualizado exitosamente.', 'success')
            return redirect(url_for('inventory.list_products'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el producto (Verifique que el precio sea numérico): {str(e)}', 'danger')

    categorias = CategoriasProducto.query.all()
    return render_template('inventory/products_form.html', producto=producto, categorias=categorias)

@inventory_bp.route('/products/delete/<int:id>', methods=['POST'])
@admin_required
def delete_product(id):
    producto = db.session.get(Productos, id)
    if not producto or producto.motocicleta:
        flash('Producto general no encontrado.', 'danger')
        return redirect(url_for('inventory.list_products'))
        
    try:
        db.session.delete(producto)
        db.session.commit()
        flash('Producto general eliminado.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'No se puede eliminar el producto. Es posible que esté asociado a ventas o facturas.', 'danger')

    return redirect(url_for('inventory.list_products'))

@inventory_bp.route('/products/detail/<int:id>')
def detail_product(id):
    producto = db.session.get(Productos, id)
    if not producto or producto.motocicleta:
        flash('Producto no encontrado.', 'danger')
        return redirect(url_for('inventory.list_products'))
        
    return render_template('inventory/products_detail.html', producto=producto)
