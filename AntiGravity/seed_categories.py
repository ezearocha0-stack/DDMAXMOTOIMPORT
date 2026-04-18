from app import create_app
from app.extensions import db
from app.models.entities import CategoriasProducto

def seed_categories():
    app = create_app()
    with app.app_context():
        # Insert categories if they don't exist
        nuevas_categorias = [
            {'nombre': 'Cascos', 'descripcion': 'Cascos de seguridad integral, abiertos y cerrados'},
            {'nombre': 'Repuestos', 'descripcion': 'Piezas mecánicas y de chasis (Bujías, Gomas, Cadena)'},
            {'nombre': 'Accesorios', 'descripcion': 'Guantes, impermeables, baúles y espejos'},
            {'nombre': 'Lubricantes', 'descripcion': 'Aceites de motor, líquido de frenos y refrigerantes'},
            {'nombre': 'Electrónica', 'descripcion': 'Baterías, faros LED, intermitentes y alarmas'}
        ]

        count = 0
        for cat in nuevas_categorias:
            existe = CategoriasProducto.query.filter_by(nombre=cat['nombre']).first()
            if not existe:
                nueva = CategoriasProducto(nombre=cat['nombre'], descripcion=cat['descripcion'])
                db.session.add(nueva)
                count += 1
                
        if count > 0:
            db.session.commit()
            print(f"✅ Se han insertado {count} categorías generales correctamente.")
        else:
            print("ℹ️ Las categorías ya estaban registradas.")

if __name__ == '__main__':
    seed_categories()
