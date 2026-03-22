import pytest
from playwright.sync_api import Page, expect
import os

# Configuración básica
BASE_URL = os.environ.get('BASE_URL', 'http://127.0.0.1:5000')

# ==========================================
# RUTINA 1: Autenticación y Dashboard
# ==========================================
def test_login_and_dashboard(page: Page):
    """Prueba el acceso al sistema y la carga correcta del panel principal."""
    # 1. Navegar a la pantalla de login (con reintentos automáticos de Playwright)
    page.goto(f"{BASE_URL}/login")
    
    # 2. Verificar que los elementos existan
    expect(page.locator("h2:has-text('Iniciar Sesión')")).to_be_visible()
    
    # 3. Llenar formulario (Asegúrate de cambiar 'admin' y '123' por tus credenciales locales)
    page.fill('input[name="usuario"]', 'admin')
    page.fill('input[name="password"]', '123') # Cambiar según tu BD local de pruebas
    page.click('button[type="submit"]')
    
    # 4. Verificar redirección al dashboard y evitar errores 500
    expect(page).to_have_url(f"{BASE_URL}/")
    expect(page.locator("text='Dashboard'")).to_be_visible()
    expect(page.locator(".alert-danger")).not_to_be_visible() # Que no haya errores flash

# ==========================================
# RUTINA 2: Ciclo de Ventas (Facturación)
# ==========================================
def test_create_sale(page: Page):
    """Abre el formulario de factura y valida que los componentes dinámicos existan."""
    # Autenticar rápido
    page.goto(f"{BASE_URL}/login")
    page.fill('input[name="usuario"]', 'admin')
    page.fill('input[name="password"]', '123')
    page.click('button[type="submit"]')
    
    # Ir a crear venta
    page.goto(f"{BASE_URL}/sales/create")
    
    # Verificar elementos vitales (Botones que no abren o errores 500)
    expect(page.locator('select[name="cliente_id"]')).to_be_visible()
    expect(page.locator('text="Agregar Producto"')).to_be_visible()
    
    # Validar cambio de tipo de pago (Crédito despliega Meses)
    page.select_option('select[name="tipo"]', label='Al Crédito')
    expect(page.locator('input[name="meses_credito"]')).to_be_visible()
    
    page.select_option('select[name="tipo"]', label='Al Contado')
    expect(page.locator('input[name="meses_credito"]')).not_to_be_visible()

# ==========================================
# RUTINA 3: Cuentas por Cobrar y Pagos
# ==========================================
def test_receivables_and_payment_flow(page: Page):
    """Navega a las cuentas, entra a un detalle y abre el formulario inteligente de pago."""
    # Autenticar
    page.goto(f"{BASE_URL}/login")
    page.fill('input[name="usuario"]', 'admin')
    page.fill('input[name="password"]', '123')
    page.click('button[type="submit"]')
    
    # Ir a panel de Cuentas por Cobrar
    page.goto(f"{BASE_URL}/accounts/")
    expect(page.locator('h2:has-text("Cuentas por Cobrar")')).to_be_visible()
    
    # Buscar el primer botón "Detalle" de la tabla (si existe alguna cuenta)
    detail_button = page.locator('a.btn-outline-primary:has-text("Detalle")').first
    
    if detail_button.is_visible():
        # Clic para entrar al detalle (Valida que el link no esté roto)
        detail_button.click()
        expect(page.locator('h2:has-text("Detalle de Cuenta")')).to_be_visible()
        
        # Probar el botón de Registrar Pago
        payment_button = page.locator('a:has-text("Registrar Pago")')
        if payment_button.is_visible():
            payment_button.click()
            
            # Validar que la nueva interfaz de pago cargue sin error 500
            expect(page.locator('text="Información de la Cuenta"')).to_be_visible()
            expect(page.locator('input[name="monto"]')).to_be_visible()
