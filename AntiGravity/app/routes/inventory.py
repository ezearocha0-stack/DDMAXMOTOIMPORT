from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.extensions import db
from app.models.entities import Motocicletas, Productos, CategoriasProducto
from sqlalchemy import or_
from decimal import Decimal

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
    
    motocicletas = query.order_by(Motocicletas.id.desc()).all()
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
        costo = request.form.get('costo')
        ganancia = request.form.get('ganancia')
        itbis_porcentaje = request.form.get('itbis_porcentaje', '0')
        estado = request.form.get('estado', 'en inventario')

        if not marca or not modelo or not vin or not ganancia or not costo:
            flash('Marca, Modelo, VIN, Costo y Ganancia son obligatorios.', 'danger')
            return redirect(url_for('inventory.create_motorcycle'))

        # Verificar si existe el VIN
        existing = Motocicletas.query.filter_by(vin=vin).first()
        if existing:
            flash(f'Ya existe una motocicleta con el VIN {vin}.', 'danger')
            return redirect(url_for('inventory.create_motorcycle'))

        try:
            costo_val = Decimal(costo)
            ganancia_val = Decimal(ganancia)
            porcentaje_val = Decimal(itbis_porcentaje)
            
            # 1. precio base de venta = precio de compra + ganancia deseada
            precio_base = costo_val + ganancia_val
            
            # 2. monto ITBIS = precio base de venta * (ITBIS / 100)
            itbis_val = precio_base * (porcentaje_val / Decimal('100.0'))
            
            # 3. precio final de venta (El que usará ventas)
            precio_final = precio_base + itbis_val
        except Exception:
            flash('Costo, Ganancia e ITBIS deben ser números válidos.', 'danger')
            return redirect(url_for('inventory.create_motorcycle'))

        categoria = _get_or_create_motorcycle_category()

        try:
            # Crear Producto primero
            producto = Productos(
                nombre=f"{marca} {modelo} ({año})",
                categoria_id=categoria.id,
                costo=costo_val,
                precio=precio_final,
                itbis=itbis_val,
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
        costo = request.form.get('costo')
        ganancia = request.form.get('ganancia')
        itbis_porcentaje = request.form.get('itbis_porcentaje', '0')
        estado = request.form.get('estado')

        if nuevo_vin != motocicleta.vin:
            existing = Motocicletas.query.filter_by(vin=nuevo_vin).first()
            if existing:
                flash(f'Ya existe otra motocicleta con el VIN {nuevo_vin}.', 'danger')
                return redirect(url_for('inventory.edit_motorcycle', id=id))
        
        try:
            costo_val = Decimal(costo) if costo else Decimal('0.0')
            ganancia_val = Decimal(ganancia)
            porcentaje_val = Decimal(itbis_porcentaje)
            
            # 1. precio base de venta = precio de compra + ganancia deseada
            precio_base = costo_val + ganancia_val
            
            # 2. monto ITBIS = precio base de venta * (ITBIS / 100)
            itbis_val = precio_base * (porcentaje_val / Decimal('100.0'))
            
            # 3. precio final de venta (El que usará ventas)
            precio_final = precio_base + itbis_val
        except Exception:
            flash('Costo, Ganancia e ITBIS deben ser números válidos.', 'danger')
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
                motocicleta.producto.costo = costo_val
                motocicleta.producto.precio = precio_final
                motocicleta.producto.itbis = itbis_val
                
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
