import functools
from sqlalchemy import event
from flask import has_request_context
from flask_login import current_user
from app.extensions import db
from app.models.auth import Auditoria
from datetime import datetime

def log_audit_action(mapper, connection, target, accion):
    try:
        tabla = target.__tablename__
        
        # Only log tables we care about
        if tabla not in ['clientes', 'productos', 'facturas', 'pagos', 'devoluciones', 'motocicletas']:
            return
            
        usuario_id = 1 # Admin fallback
        if has_request_context():
            if current_user and current_user.is_authenticated:
                usuario_id = current_user.id
                
        # To avoid unbounded recursions or locked sessions during insert,
        # we issue a raw SQL insert for the audit log via the active connection.
        
        # We need the ID. For 'insert', target.id might be None before commit,
        # but in 'after_insert' it should be populated if autoincrement DB fetched it.
        # Fallback to 0 if we can't get it.
        registro_id = getattr(target, 'id', 0) or 0
        
        connection.execute(
            Auditoria.__table__.insert().values(
                usuario_id=usuario_id,
                tabla=tabla,
                registro_id=registro_id,
                accion=accion,
                fecha=datetime.utcnow()
            )
        )
    except Exception as e:
        # Failsafe: do not block main transaction if audit logging fails
        print(f"Error logging audit: {e}")

def register_audit_listeners():
    from app.models.entities import Clientes, Productos, Motocicletas
    from app.models.transactions import Facturas, Devoluciones
    from app.models.finance import Pagos

    # We register for each table to avoid global event clutter
    models = [Clientes, Productos, Motocicletas, Facturas, Devoluciones, Pagos]

    for model in models:
        # Note: Using partials to pass 'accion' securely
        event.listen(model, 'after_insert', lambda m, c, t: log_audit_action(m, c, t, 'insertar'))
        event.listen(model, 'after_update', lambda m, c, t: log_audit_action(m, c, t, 'actualizar'))
        event.listen(model, 'after_delete', lambda m, c, t: log_audit_action(m, c, t, 'eliminar'))
