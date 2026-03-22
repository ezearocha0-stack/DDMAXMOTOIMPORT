from app import create_app
from app.extensions import db
from app.models.auth import Roles, Usuarios
import os

app = create_app()

def init_database():
    with app.app_context():
        # Crear base de datos y tablas
        db.create_all()
        print("Tablas creadas exitosamente.")

        # Verificar si existe el rol administrador
        admin_rol = Roles.query.filter_by(nombre='Administrador').first()
        if not admin_rol:
            admin_rol = Roles(nombre='Administrador', descripcion='Acceso total al sistema')
            db.session.add(admin_rol)
            db.session.commit()
            print("Rol 'Administrador' creado.")

        # Verificar si existe el usuario administrador
        admin_user = Usuarios.query.filter_by(usuario='admin').first()
        if not admin_user:
            admin_user = Usuarios(
                usuario='admin',
                rol_id=admin_rol.id,
                nombre='Administrador del Sistema',
                estado='activo'
            )
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            db.session.commit()
            print("Usuario 'admin' creado con contraseña 'admin123'.")

if __name__ == '__main__':
    init_database()
