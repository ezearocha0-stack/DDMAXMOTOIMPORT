from flask import Blueprint, render_template
from flask_login import login_required

from app.models.entities import Motocicletas, Clientes, Productos
from app.models.transactions import Facturas
from app.models.finance import CuentasPorCobrar
from app.extensions import db
from sqlalchemy import func
from datetime import date, datetime, timedelta

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def dashboard():
    # 1. Total ventas hoy
    hoy = date.today()
    from app.models.transactions import Devoluciones
    
    ventas_hoy_brutas = db.session.query(func.sum(Facturas.total)).filter(
        db.func.date(Facturas.fecha) == hoy,
        Facturas.estado != 'anulada'
    ).scalar() or 0.0
    
    devs_hoy = db.session.query(func.sum(Devoluciones.monto_devuelto)).join(Facturas).filter(
        db.func.date(Facturas.fecha) == hoy,
        Facturas.estado != 'anulada'
    ).scalar() or 0.0
    
    ventas_hoy = float(ventas_hoy_brutas) - float(devs_hoy)
    
    # 2. Total ventas este mes
    mes_inicio = datetime.combine(hoy.replace(day=1), datetime.min.time())
    if hoy.month == 12:
        mes_fin = datetime(hoy.year + 1, 1, 1) - timedelta(days=1)
    else:
        mes_fin = datetime(hoy.year, hoy.month + 1, 1) - timedelta(days=1)
    mes_fin = datetime.combine(mes_fin, datetime.max.time())
    
    ventas_mes_brutas = db.session.query(func.sum(Facturas.total)).filter(
        Facturas.fecha >= mes_inicio,
        Facturas.fecha <= mes_fin,
        Facturas.estado != 'anulada'
    ).scalar() or 0.0
    
    devs_mes = db.session.query(func.sum(Devoluciones.monto_devuelto)).join(Facturas).filter(
        Facturas.fecha >= mes_inicio,
        Facturas.fecha <= mes_fin,
        Facturas.estado != 'anulada'
    ).scalar() or 0.0
    
    ventas_mes = float(ventas_mes_brutas) - float(devs_mes)
    
    # 3. Pending receivables
    cuentas_cobrar_query = db.session.query(func.sum(CuentasPorCobrar.saldo)).filter(
        CuentasPorCobrar.estado == 'pendiente'
    ).scalar()
    cuentas_cobrar_total = cuentas_cobrar_query if cuentas_cobrar_query else 0.0
    
    # 4. Inventory items (count of products)
    items_inventario = Productos.query.filter_by(estado='disponible').count()
    
    # 5. Low stock products (stock <= 2)
    baja_existencia = Productos.query.filter(
        Productos.estado == 'disponible',
        Productos.stock <= 2
    ).order_by(Productos.stock.asc()).all()
    
    # Extra: Total de clientes
    clientes_total = Clientes.query.count()
    
    # 6. Gráfico de Ventas (Últimos 6 meses)
    chart_labels = []
    chart_data = []
    meses_nombres = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    
    # Obtener los últimos 6 meses (incluyendo el actual)
    for i in range(5, -1, -1):
        target_month = hoy.month - i
        target_year = hoy.year
        if target_month <= 0:
            target_month += 12
            target_year -= 1
            
        chart_labels.append(f"{meses_nombres[target_month - 1]} {target_year}")
        
        # Calcular inicio y fin del mes objetivo
        inicio_obj = datetime(target_year, target_month, 1)
        if target_month == 12:
            fin_obj = datetime(target_year + 1, 1, 1) - timedelta(days=1)
        else:
            fin_obj = datetime(target_year, target_month + 1, 1) - timedelta(days=1)
        fin_obj = datetime.combine(fin_obj, datetime.max.time())
        
        ventas_mes_obj_bruto = db.session.query(func.sum(Facturas.total)).filter(
            Facturas.fecha >= inicio_obj,
            Facturas.fecha <= fin_obj,
            Facturas.estado != 'anulada'
        ).scalar() or 0.0
        
        devs_mes_obj = db.session.query(func.sum(Devoluciones.monto_devuelto)).join(Facturas).filter(
            Facturas.fecha >= inicio_obj,
            Facturas.fecha <= fin_obj,
            Facturas.estado != 'anulada'
        ).scalar() or 0.0
        
        ventas_mes_obj = float(ventas_mes_obj_bruto) - float(devs_mes_obj)
        
        chart_data.append(float(ventas_mes_obj))
    
    # Últimas 5 facturas
    actividades = Facturas.query.order_by(Facturas.fecha.desc()).limit(5).all()

    stats = {
        'ventas_hoy': ventas_hoy,
        'ventas_mes': ventas_mes,
        'items_inventario': items_inventario,
        'clientes_total': clientes_total,
        'cuentas_cobrar_total': cuentas_cobrar_total,
        'baja_existencia': baja_existencia
    }
    
    return render_template('dashboard.html', stats=stats, actividades=actividades, chart_labels=chart_labels, chart_data=chart_data)
