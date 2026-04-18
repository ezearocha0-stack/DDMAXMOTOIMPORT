from app import create_app
from app.extensions import db
from app.models.auth import Usuarios, Roles

app = create_app()

with app.app_context():
    print("Verificando roles y usuarios base...")

    # Asegurar que existan los roles
    rol_admin = Roles.query.filter_by(nombre='ADMIN').first()
    if not rol_admin:
        rol_admin = Roles(nombre='ADMIN', descripcion='Acceso total al sistema')
        db.session.add(rol_admin)
        print("Rol ADMIN creado.")

    rol_empleado = Roles.query.filter_by(nombre='EMPLEADO').first()
    if not rol_empleado:
        rol_empleado = Roles(nombre='EMPLEADO', descripcion='Acceso limitado para ventas y gestión diaria')
        db.session.add(rol_empleado)
        print("Rol EMPLEADO creado.")
        
    db.session.commit()

    # Usuario ADMIN
    usuario_admin = Usuarios.query.filter_by(usuario='admin').first()
    if not usuario_admin:
        usuario_admin = Usuarios(
            usuario='admin',
            nombre='Administrador Principal',
            rol_id=rol_admin.id,
            estado='activo'
        )
        usuario_admin.set_password('admin123')
        db.session.add(usuario_admin)
        print("Usuario 'admin' creado exitosamente. Password: admin123")
    else:
        print("Usuario 'admin' ya existía.")

    # Usuario EMPLEADO
    usuario_empleado = Usuarios.query.filter_by(usuario='empleado').first()
    if not usuario_empleado:
        usuario_empleado = Usuarios(
            usuario='empleado',
            nombre='Empleado Mostrador',
            rol_id=rol_empleado.id,
            estado='activo'
        )
        usuario_empleado.set_password('empleado123')
        db.session.add(usuario_empleado)
        print("Usuario 'empleado' creado exitosamente. Password: empleado123")
    else:
        print("Usuario 'empleado' ya existía.")

    db.session.commit()
    print("¡Proceso finalizado!")
