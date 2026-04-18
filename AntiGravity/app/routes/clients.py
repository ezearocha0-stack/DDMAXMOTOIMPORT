from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.extensions import db
from app.models.entities import Clientes
from sqlalchemy import or_
from app.routes.auth import admin_required

clients_bp = Blueprint('clients', __name__, url_prefix='/clients')

@clients_bp.route('/')
def list_clients():
    search = request.args.get('search', '')
    query = Clientes.query
    if search:
        query = query.filter(or_(
            Clientes.nombre.ilike(f'%{search}%'),
            Clientes.documento.ilike(f'%{search}%')
        ))
    
    # Paginación o simple all() por ahora
    clientes = query.order_by(Clientes.id.desc()).all()
    return render_template('clients/list.html', clientes=clientes, search=search)

@clients_bp.route('/create', methods=['GET', 'POST'])
def create_client():
    if request.method == 'POST':
        tipo = request.form.get('tipo')
        nombre = request.form.get('nombre')
        documento = request.form.get('documento')
        telefono = request.form.get('telefono')
        direccion = request.form.get('direccion')
        
        nombre_garante = request.form.get('nombre_garante')
        documento_garante = request.form.get('documento_garante')
        telefono_garante = request.form.get('telefono_garante')
        direccion_garante = request.form.get('direccion_garante')

        # Validación básica
        if not nombre or not documento or not tipo:
            flash('Tipo, Nombre y Documento son obligatorios.', 'danger')
            return redirect(url_for('clients.create_client'))

        # Verificar si el documento ya existe
        existing = Clientes.query.filter_by(documento=documento).first()
        if existing:
            flash(f'Ya existe un cliente con el documento {documento}.', 'danger')
            return redirect(url_for('clients.create_client'))

        nuevo_cliente = Clientes(
            tipo=tipo,
            nombre=nombre,
            documento=documento,
            telefono=telefono,
            direccion=direccion,
            nombre_garante=nombre_garante,
            documento_garante=documento_garante,
            telefono_garante=telefono_garante,
            direccion_garante=direccion_garante
        )
        
        try:
            db.session.add(nuevo_cliente)
            db.session.commit()
            flash('Cliente creado exitosamente.', 'success')
            return redirect(url_for('clients.list_clients'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear el cliente: {str(e)}', 'danger')

    return render_template('clients/form.html', cliente=None)

@clients_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_client(id):
    cliente = db.session.get(Clientes, id)
    if not cliente:
        flash('Cliente no encontrado.', 'danger')
        return redirect(url_for('clients.list_clients'))

    if request.method == 'POST':
        cliente.tipo = request.form.get('tipo')
        cliente.nombre = request.form.get('nombre')
        
        nuevo_documento = request.form.get('documento')
        
        # Verificar que el documento sea único si cambió
        if nuevo_documento != cliente.documento:
            existing = Clientes.query.filter_by(documento=nuevo_documento).first()
            if existing:
                flash(f'Ya existe otro cliente con el documento {nuevo_documento}.', 'danger')
                return redirect(url_for('clients.edit_client', id=id))
        
        cliente.documento = nuevo_documento
        cliente.telefono = request.form.get('telefono')
        cliente.direccion = request.form.get('direccion')
        
        cliente.nombre_garante = request.form.get('nombre_garante')
        cliente.documento_garante = request.form.get('documento_garante')
        cliente.telefono_garante = request.form.get('telefono_garante')
        cliente.direccion_garante = request.form.get('direccion_garante')

        try:
            db.session.commit()
            flash('Cliente actualizado exitosamente.', 'success')
            return redirect(url_for('clients.list_clients'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el cliente: {str(e)}', 'danger')

    return render_template('clients/form.html', cliente=cliente)

@clients_bp.route('/delete/<int:id>', methods=['POST'])
@admin_required
def delete_client(id):
    cliente = db.session.get(Clientes, id)
    if not cliente:
        flash('Cliente no encontrado.', 'danger')
        return redirect(url_for('clients.list_clients'))
        
    try:
        db.session.delete(cliente)
        db.session.commit()
        flash('Cliente eliminado exitosamente.', 'success')
    except Exception as e:
        db.session.rollback()
        # usualmente falla debido a restricciones de clave foránea si el cliente tiene facturas
        flash(f'No se puede eliminar el cliente. Es posible que tenga transacciones asociadas.', 'danger')

    return redirect(url_for('clients.list_clients'))

@clients_bp.route('/profile/<int:id>')
def profile_client(id):
    cliente = db.session.get(Clientes, id)
    if not cliente:
        flash('Cliente no encontrado.', 'danger')
        return redirect(url_for('clients.list_clients'))
        
    return render_template('clients/profile.html', cliente=cliente)
