from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required

cash_movements_bp = Blueprint('cash_movements', __name__, url_prefix='/cash')

@cash_movements_bp.route('/')
@login_required
def list_movements():
    flash('El módulo de Movimientos de Caja ha sido deshabilitado como parte de la migración.', 'warning')
    return redirect(url_for('main.dashboard'))
