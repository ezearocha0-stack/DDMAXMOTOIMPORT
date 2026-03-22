from flask import Blueprint, render_template, request
from app.extensions import db
from app.models.transactions import Facturas
from flask_login import login_required
from datetime import datetime, date, timedelta
from sqlalchemy import func

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

@reports_bp.route('/sales')
@login_required
def sales_report():
    # Obtener filtros de fecha
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    # Manejo de fechas para filtros
    today = date.today()
    if start_date_str and end_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    else:
        # Por defecto muestra el último mes
        end_date = today
        start_date = today.replace(day=1) # Primer día del mes
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
    # Extend end_date to include the full day
    end_date_datetime = datetime.combine(end_date, datetime.max.time())
    start_date_datetime = datetime.combine(start_date, datetime.min.time())

    # Query Base (Con filtro de fechas opcional)
    query_facturas = Facturas.query.filter(
        Facturas.fecha >= start_date_datetime,
        Facturas.fecha <= end_date_datetime
    )
    
    facturas_filtradas = query_facturas.order_by(Facturas.fecha.desc()).all()
    
    # Cálculos globales
    
    # Ventas de HOY
    hoy_inicio = datetime.combine(today, datetime.min.time())
    hoy_fin = datetime.combine(today, datetime.max.time())
    ventas_hoy = db.session.query(func.sum(Facturas.total)).filter(
        Facturas.fecha >= hoy_inicio,
        Facturas.fecha <= hoy_fin
    ).scalar() or 0.0

    # Ventas del MES ACTUAL
    mes_inicio = datetime.combine(today.replace(day=1), datetime.min.time())
    
    # Mover al siguiente mes para obtener el último día del mes actual 
    # (Un pequeño truco de datetime)
    if today.month == 12:
        mes_fin = datetime(today.year + 1, 1, 1) - timedelta(days=1)
    else:
        mes_fin = datetime(today.year, today.month + 1, 1) - timedelta(days=1)
    mes_fin = datetime.combine(mes_fin, datetime.max.time())
    
    ventas_mes = db.session.query(func.sum(Facturas.total)).filter(
        Facturas.fecha >= mes_inicio,
        Facturas.fecha <= mes_fin
    ).scalar() or 0.0

    # Total de Ventas en el rango seleccionado
    total_filtrado = sum(f.total for f in facturas_filtradas)
    cantidad_facturas = len(facturas_filtradas)

    return render_template(
        'reports/sales.html',
        facturas=facturas_filtradas,
        ventas_hoy=ventas_hoy,
        ventas_mes=ventas_mes,
        total_filtrado=total_filtrado,
        cantidad_facturas=cantidad_facturas,
        start_date=start_date_str,
        end_date=end_date_str
    )

@reports_bp.route('/inventory')
@login_required
def inventory_report():
    from app.models.entities import Productos
    
    # Solo traemos los disponibles
    productos = Productos.query.filter_by(estado='disponible').all()
    
    # Calcular el valor para cada producto y ordenar
    inventario_valorado = []
    total_inventario = 0.0
    
    for p in productos:
        valor_total = float(p.stock) * float(p.costo)
        inventario_valorado.append({
            'producto': p,
            'valor_total': valor_total
        })
        total_inventario += valor_total
        
    # Ordenar por el que tiene más valor (de mayor a menor)
    inventario_valorado.sort(key=lambda x: x['valor_total'], reverse=True)
    
    return render_template(
        'reports/inventory.html',
        inventario_valorado=inventario_valorado,
        total_inventario=total_inventario
    )
