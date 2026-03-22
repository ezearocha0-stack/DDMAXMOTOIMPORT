from flask import Blueprint, render_template, request, flash, redirect, url_for
from app.extensions import db
from app.models.finance import MovimientosCaja
from flask_login import login_required

cash_movements_bp = Blueprint('cash_movements', __name__, url_prefix='/cash')

@cash_movements_bp.route('/')
@login_required
def list_movements():
    movimientos = MovimientosCaja.query.order_by(MovimientosCaja.fecha.desc()).all()
    # Calcular balance actual 
    # (En un futuro balance inicial podríase setear, por ahora sumamos todos los ingresos y restamos egresos)
    balance = sum([m.monto if m.tipo_movimiento == 'ingreso' else -m.monto for m in movimientos])
    return render_template('cash_movements/list.html', movimientos=movimientos, balance=balance)
