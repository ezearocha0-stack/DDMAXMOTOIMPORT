from app.models.auth import Roles, Permisos, RolPermisos, Usuarios, Auditoria
from app.models.entities import Clientes, Proveedores, CategoriasProducto, Productos, Motocicletas
from app.models.transactions import Compras, DetalleCompra, Facturas, DetalleFactura, Devoluciones
from app.models.finance import CuentasPorCobrar, Cuotas, Pagos, CuentasPorPagar, CuotasPorPagar, PagosProveedor

# Esto permite que importar `app.models` cargue todos los modelos para create_all()
