from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models.auth import Usuarios
from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.rol.nombre.upper() not in ['ADMIN', 'ADMINISTRADOR']:
            flash('Acceso denegado. Se requiere nivel de administrador para esta acción.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def permission_required(modulo, accion):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            
            # Admin siempre tiene acceso
            if current_user.rol.nombre.upper() in ['ADMIN', 'ADMINISTRADOR']:
                return f(*args, **kwargs)
                
            # Buscar el permiso granulado en el rol
            tiene_permiso = False
            for rol_permiso in current_user.rol.permisos:
                if rol_permiso.permiso.modulo == modulo and rol_permiso.permiso.accion == accion:
                    tiene_permiso = True
                    break
                    
            if not tiene_permiso:
                flash(f'Acceso denegado. Se requiere el permiso: {modulo} -> {accion}', 'danger')
                return redirect(url_for('main.dashboard'))
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def has_permission(user, modulo, accion):
    if not user.is_authenticated:
        return False
    if user.rol.nombre.upper() in ['ADMIN', 'ADMINISTRADOR']:
        return True
    for rp in user.rol.permisos:
        if rp.permiso.modulo == modulo and rp.permiso.accion == accion:
            return True
    return False

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        password = request.form.get('password')
        
        user = Usuarios.query.filter_by(usuario=usuario).first()
        
        if user and user.check_password(password):
            if user.estado != 'activo':
                flash('Tu cuenta está inactiva. Contacta al administrador.', 'danger')
                return redirect(url_for('auth.login'))
                
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        else:
            flash('Usuario o contraseña incorrectos.', 'danger')
            
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión exitosamente.', 'success')
    return redirect(url_for('auth.login'))
