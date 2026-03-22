from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.extensions import db
from app.models.entities import Proveedores
from sqlalchemy import or_

suppliers_bp = Blueprint('suppliers', __name__, url_prefix='/suppliers')

@suppliers_bp.route('/')
def list_suppliers():
    search = request.args.get('search', '')
    query = Proveedores.query
    if search:
        query = query.filter(or_(
            Proveedores.nombre.ilike(f'%{search}%'),
            Proveedores.rnc.ilike(f'%{search}%'),
            Proveedores.contacto.ilike(f'%{search}%')
        ))
    
    proveedores = query.order_by(Proveedores.id.desc()).all()
    return render_template('suppliers/list.html', proveedores=proveedores, search=search)

@suppliers_bp.route('/create', methods=['GET', 'POST'])
def create_supplier():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        rnc = request.form.get('rnc')
        telefono = request.form.get('telefono')
        direccion = request.form.get('direccion')
        contacto = request.form.get('contacto')
        estado = request.form.get('estado', 'activo')

        if not nombre:
            flash('El nombre del proveedor es obligatorio.', 'danger')
            return redirect(url_for('suppliers.create_supplier'))

        if rnc:
            existing = Proveedores.query.filter_by(rnc=rnc).first()
            if existing:
                flash(f'Ya existe un proveedor con el RNC {rnc}.', 'danger')
                return redirect(url_for('suppliers.create_supplier'))

        nuevo_proveedor = Proveedores(
            nombre=nombre,
            rnc=rnc,
            telefono=telefono,
            direccion=direccion,
            contacto=contacto,
            estado=estado
        )
        
        try:
            db.session.add(nuevo_proveedor)
            db.session.commit()
            flash('Proveedor registrado exitosamente.', 'success')
            return redirect(url_for('suppliers.list_suppliers'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar el proveedor: {str(e)}', 'danger')

    return render_template('suppliers/form.html', proveedor=None)

@suppliers_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_supplier(id):
    proveedor = db.session.get(Proveedores, id)
    if not proveedor:
        flash('Proveedor no encontrado.', 'danger')
        return redirect(url_for('suppliers.list_suppliers'))

    if request.method == 'POST':
        proveedor.nombre = request.form.get('nombre')
        nuevo_rnc = request.form.get('rnc')
        
        if nuevo_rnc and nuevo_rnc != proveedor.rnc:
            existing = Proveedores.query.filter_by(rnc=nuevo_rnc).first()
            if existing:
                flash(f'Ya existe otro proveedor con el RNC {nuevo_rnc}.', 'danger')
                return redirect(url_for('suppliers.edit_supplier', id=id))
        
        proveedor.rnc = nuevo_rnc
        proveedor.telefono = request.form.get('telefono')
        proveedor.direccion = request.form.get('direccion')
        proveedor.contacto = request.form.get('contacto')
        proveedor.estado = request.form.get('estado', 'activo')

        try:
            db.session.commit()
            flash('Proveedor actualizado exitosamente.', 'success')
            return redirect(url_for('suppliers.list_suppliers'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el proveedor: {str(e)}', 'danger')

    return render_template('suppliers/form.html', proveedor=proveedor)

@suppliers_bp.route('/deactivate/<int:id>', methods=['POST'])
def deactivate_supplier(id):
    proveedor = db.session.get(Proveedores, id)
    if not proveedor:
        flash('Proveedor no encontrado.', 'danger')
        return redirect(url_for('suppliers.list_suppliers'))
        
    try:
        if proveedor.estado == 'activo':
            proveedor.estado = 'inactivo'
            flash('Proveedor desactivado exitosamente. Ya no aparecerá en nuevas compras.', 'success')
        else:
            proveedor.estado = 'activo'
            flash('Proveedor reactivado exitosamente.', 'success')
            
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'Error al cambiar el estado del proveedor: {str(e)}', 'danger')

    return redirect(url_for('suppliers.list_suppliers'))
