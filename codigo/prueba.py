import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import mysql.connector

# Datos de productos disponibles
productos = {
    "chucherias": {"nombre": "Sabritas", "precio": 15.0, "cantidad": 50},
    "refresco": {"nombre": "Cocacola", "precio": 20.0, "cantidad": 100},
    "trago": {"nombre": "Cervezas alcohólicas", "precio": 50.0, "cantidad": 20},
}

# Conectar a la base de datos MySQL
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="ventasexpress"
)
cursor = conn.cursor()

# Crear tabla si no existe
cursor.execute('''CREATE TABLE IF NOT EXISTS inventario (
                  fecha DATE,
                  chucherias INT,
                  refresco INT,
                  trago INT)''')

# Crear tabla para usuarios si no existe
cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                  id INT AUTO_INCREMENT PRIMARY KEY,
                  username VARCHAR(50) UNIQUE NOT NULL,
                  password VARCHAR(50) NOT NULL)''')

# Insertar usuario "william" y contraseña "1234"
##cursor.execute("INSERT INTO usuarios (username, password) VALUES (%s, %s)", ("william", "1234"))
conn.commit()

class PuntoDeVenta(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Punto de Venta")
        self.geometry("500x400")
        self.configure(bg='blue')

        self.total = 0.0
        self.carrito = {}
        self.transacciones = []

        self.btn_ventas = tk.Button(self, text="Realizar Venta", command=self.abrir_ventana_ventas, state=tk.DISABLED)
        self.btn_ventas.pack(pady=10)

        self.btn_inventario = tk.Button(self, text="Ver Inventario", command=self.abrir_ventana_inventario, state=tk.DISABLED)
        self.btn_inventario.pack(pady=10)

        self.btn_reportes = tk.Button(self, text="Generar Reportes", command=self.abrir_ventana_reportes, state=tk.DISABLED)
        self.btn_reportes.pack(pady=10)

        self.btn_ingresos = tk.Button(self, text="Mostrar Inventario por Mes", command=self.mostrar_inventario, state=tk.DISABLED)
        self.btn_ingresos.pack(pady=10)

    def abrir_ventana_ventas(self):
        self.ventana_ventas = tk.Toplevel(self)
        self.ventana_ventas.title("Realizar Venta")

        # Botón de regreso en la esquina superior derecha
        btn_regreso = tk.Button(self.ventana_ventas, text="Regresar", command=self.ventana_ventas.destroy)
        btn_regreso.pack(anchor=tk.NE, padx=10, pady=10)

        self.label_subtotal = tk.Label(self.ventana_ventas, text=f"Subtotal: ${self.total:.2f}")
        self.label_subtotal.pack(pady=20, padx=10, side=tk.LEFT)

        label_ventas = tk.Label(self.ventana_ventas, text="Seleccione los productos:")
        label_ventas.pack(pady=20)

        self.productos_seleccionados = {}

        for producto, detalles in productos.items():
            frame_producto = tk.Frame(self.ventana_ventas)
            frame_producto.pack(pady=5)
            
            btn_producto = tk.Button(frame_producto, text=f"{detalles['nombre']} - ${detalles['precio']:.2f}", 
                                     command=lambda prod=producto: self.agregar_producto(prod, spinbox_cantidad.get()))
            btn_producto.pack(side=tk.LEFT)

            spinbox_cantidad = tk.Spinbox(frame_producto, from_=1, to=detalles['cantidad'], width=5)
            spinbox_cantidad.pack(side=tk.LEFT)

            # Desactivar el botón si no hay suficiente cantidad disponible
            if detalles['cantidad'] == 0:
                btn_producto.config(state=tk.DISABLED)

        self.lista_productos = tk.Listbox(self.ventana_ventas)
        self.lista_productos.pack(pady=20, padx=10, side=tk.LEFT)

        btn_ver_carrito = tk.Button(self.ventana_ventas, text="Ver Carrito", command=self.mostrar_carrito)
        btn_ver_carrito.pack(pady=10)

        btn_comprar = tk.Button(self.ventana_ventas, text="Comprar", command=self.generar_ticket)
        btn_comprar.pack(pady=10)

        tk.Label(self.ventana_ventas, text="Monto pagado:").pack(pady=5)
        self.entry_monto_pagado = tk.Entry(self.ventana_ventas)
        self.entry_monto_pagado.pack(pady=5)

    def agregar_producto(self, producto, cantidad):
        cantidad = int(cantidad)
        if producto in productos:
            if cantidad > productos[producto]["cantidad"]:
                messagebox.showwarning("Advertencia", f"No hay suficiente cantidad de {productos[producto]['nombre']} en el inventario.")
                return  # No agregar el producto al carrito si no hay suficiente cantidad disponible
            
            if producto in self.productos_seleccionados:
                self.productos_seleccionados[producto]["cantidad"] += cantidad
            else:
                self.productos_seleccionados[producto] = {"nombre": productos[producto]["nombre"], "precio": productos[producto]["precio"], "cantidad": cantidad}

            self.total += productos[producto]["precio"] * cantidad
            self.label_subtotal.config(text=f"Subtotal: ${self.total:.2f}")

            self.lista_productos.insert(tk.END, f"{productos[producto]['nombre']} x {cantidad}")

            # Actualizar la cantidad disponible en el inventario
            productos[producto]["cantidad"] -= cantidad

    def mostrar_carrito(self):
        mensaje = "Productos seleccionados:\n"
        for producto, detalles in self.productos_seleccionados.items():
            mensaje += f"{detalles['nombre']} - {detalles['cantidad']} unidades\n"
        messagebox.showinfo("Carrito", mensaje)

    def generar_ticket(self):
        monto_pagado = float(self.entry_monto_pagado.get())
        if monto_pagado < self.total:
            messagebox.showerror("Error", "El monto pagado es insuficiente")
        else:
            cambio = monto_pagado - self.total
            ahora = datetime.now()
            fecha_hora = ahora.strftime("%Y-%m-%d %H:%M:%S")

            for producto, detalles in self.productos_seleccionados.items():
                productos[producto]["cantidad"] -= detalles["cantidad"]

            transaccion = {
                "fecha_hora": fecha_hora,
                "monto_total": self.total,
                "cambio": cambio,
                "productos": self.productos_seleccionados
            }
            self.transacciones.append(transaccion)
            messagebox.showinfo("Compra realizada", f"Se entregó el cambio de ${cambio:.2f}\nTicket generado con éxito")
            self.limpiar_venta()
            self.entry_monto_pagado.delete(0, tk.END)

            # Actualizar base de datos de inventario
            self.actualizar_inventario_bd()

    def limpiar_venta(self):
        self.total = 0.0
        self.productos_seleccionados = {}
        self.label_subtotal.config(text=f"Subtotal: ${self.total:.2f}")
        self.lista_productos.delete(0, tk.END)

    def abrir_ventana_inventario(self):
        ventana_inventario = tk.Toplevel(self)
        ventana_inventario.title("Ver Inventario")

        # Botón de regreso en la esquina superior derecha
        btn_regreso = tk.Button(ventana_inventario, text="Regresar", command=ventana_inventario.destroy)
        btn_regreso.pack(anchor=tk.NE, padx=10, pady=10)

        def actualizar_inventario():
            for widget in ventana_inventario.winfo_children():
                widget.destroy()

            tk.Label(ventana_inventario, text="Nuevo Producto").pack(pady=10)
            
            tk.Label(ventana_inventario, text="Nombre:").pack()
            entry_nombre = tk.Entry(ventana_inventario)
            entry_nombre.pack()

            tk.Label(ventana_inventario, text="Precio:").pack()
            entry_precio = tk.Entry(ventana_inventario)
            entry_precio.pack()

            tk.Label(ventana_inventario, text="Cantidad:").pack()
            entry_cantidad = tk.Entry(ventana_inventario)
            entry_cantidad.pack()

            def agregar_nuevo_producto():
                nombre = entry_nombre.get()
                precio = float(entry_precio.get())
                cantidad = int(entry_cantidad.get())
                productos[nombre.lower()] = {"nombre": nombre, "precio": precio, "cantidad": cantidad}
                tk.Label(ventana_inventario, text=f"{nombre} - Precio: ${precio:.2f} - Cantidad: {cantidad}").pack()

                entry_nombre.delete(0, tk.END)
                entry_precio.delete(0, tk.END)
                entry_cantidad.delete(0, tk.END)
                
            tk.Button(ventana_inventario, text="Agregar", command=agregar_nuevo_producto).pack(pady=5)

            tk.Label(ventana_inventario, text="Eliminar Producto").pack(pady=10)
            tk.Label(ventana_inventario, text="Nombre:").pack()
            entry_nombre_eliminar = tk.Entry(ventana_inventario)
            entry_nombre_eliminar.pack()

            def quitar_producto():
                nombre = entry_nombre_eliminar.get().lower()
                if nombre in productos:
                    del productos[nombre]
                    actualizar_inventario()

            tk.Button(ventana_inventario, text="Eliminar", command=quitar_producto).pack(pady=5)

            tk.Label(ventana_inventario, text="Modificar Precio").pack(pady=10)
            tk.Label(ventana_inventario, text="Nombre:").pack()
            entry_nombre_modificar = tk.Entry(ventana_inventario)
            entry_nombre_modificar.pack()

            tk.Label(ventana_inventario, text="Nuevo Precio:").pack()
            entry_nuevo_precio = tk.Entry(ventana_inventario)
            entry_nuevo_precio.pack()

            def modificar_precio():
                nombre = entry_nombre_modificar.get().lower()
                nuevo_precio = float(entry_nuevo_precio.get())
                if nombre in productos:
                    productos[nombre]["precio"] = nuevo_precio
                    actualizar_inventario()

            tk.Button(ventana_inventario, text="Modificar", command=modificar_precio).pack(pady=5)

            tk.Label(ventana_inventario, text="Inventario Actual").pack(pady=10)
            for nombre, detalle in productos.items():
                tk.Label(ventana_inventario, text=f"{detalle['nombre']} - Precio: ${detalle['precio']:.2f} - Cantidad: {detalle['cantidad']}").pack()

        actualizar_inventario()

    def calcular_ingresos(self):
        # Filter out negative values
        ingresos = [transaccion['monto_total'] for transaccion in self.transacciones if transaccion['monto_total'] > 0]
        return ingresos

    def actualizar_inventario_bd(self):
        fecha_actual = datetime.now().strftime('%Y-%m')
        chucherias_cantidad = productos['chucherias']['cantidad']
        refresco_cantidad = productos['refresco']['cantidad']
        trago_cantidad = productos['trago']['cantidad']

        cursor.execute("INSERT INTO inventario (chucherias, refresco, trago, fecha) VALUES (%s, %s, %s, %s)",
                       (chucherias_cantidad, refresco_cantidad, trago_cantidad, fecha_actual))
        conn.commit()

    def mostrar_inventario(self):
        ventana_inventario = tk.Toplevel(self)
        ventana_inventario.title("Inventario por Mes")

        fecha_actual = datetime.now().strftime('%Y-%m')
        cursor.execute("SELECT fecha, chucherias, refresco, trago FROM inventario WHERE fecha=%s", (fecha_actual,))
        rows = cursor.fetchall()

        if not rows:
            messagebox.showwarning("Advertencia", "No hay datos de inventario para el mes actual.")
            return

        fechas = [row[0] for row in rows]
        chucherias = [row[1] for row in rows]
        refresco = [row[2] for row in rows]
        trago = [row[3] for row in rows]

        plt.figure(figsize=(10, 6))
        barWidth = 0.25
        r1 = np.arange(len(chucherias))
        r2 = [x + barWidth for x in r1]
        r3 = [x + barWidth for x in r2]

        plt.bar(r1, chucherias, color='blue', width=barWidth, label='Chucherias')
        plt.bar(r2, refresco, color='green', width=barWidth, label='Refresco')
        plt.bar(r3, trago, color='red', width=barWidth, label='Trago')

        plt.xlabel('Mes', fontweight='bold')
        plt.ylabel('Cantidad', fontweight='bold')
        plt.title(f'Inventario para {fecha_actual}', fontweight='bold')
        plt.xticks([r + barWidth for r in range(len(chucherias))], fechas, rotation=45)
        plt.legend()
        
        # Asegurar que el eje y no empiece con números negativos
        plt.ylim(bottom=0)
        
        plt.tight_layout()
        plt.show()

    def abrir_ventana_reportes(self):
        ventana_reportes = tk.Toplevel(self)
        ventana_reportes.title("Generar Reportes")

        ingresos = self.calcular_ingresos()

        tk.Label(ventana_reportes, text=f"Ingresos totales: ${sum(ingresos):.2f}").pack(pady=20)
        tk.Label(ventana_reportes, text=f"Transacciones: {len(ingresos)}").pack(pady=10)
        tk.Label(ventana_reportes, text=f"Monto Promedio: ${sum(ingresos) / len(ingresos):.2f}").pack(pady=10)

        plt.figure(figsize=(10, 6))
        plt.bar(range(len(ingresos)), ingresos, color='blue')
        plt.xlabel('Transacciones')
        plt.ylabel('Monto Total ($)')
        plt.title('Ingresos por Transacción')
        plt.tight_layout()
        plt.show()

def verificar_usuario():
    usu = entry_usuario.get()
    contra = entry_contraseña.get()

    cursor.execute("SELECT * FROM usuarios WHERE username = %s AND password = %s", (usu, contra))
    if cursor.fetchone():
        messagebox.showinfo("Inicio de sesión", "Inicio de sesión exitoso")
        app.btn_ventas.config(state=tk.NORMAL)
        app.btn_inventario.config(state=tk.NORMAL)
        app.btn_reportes.config(state=tk.NORMAL)
        app.btn_ingresos.config(state=tk.NORMAL)
        root.configure(bg='red')
        root.destroy()
    else:
        messagebox.showerror("Error", "Usuario o contraseña incorrectos")

root = tk.Tk()
root.title("Inicio de sesión")
root.configure(bg='red')

label_usuario = tk.Label(root, text="Usuario:")
label_usuario.pack(pady=20)
entry_usuario = tk.Entry(root)
entry_usuario.pack(pady=10)

label_contraseña = tk.Label(root, text="Contraseña:")
label_contraseña.pack(pady=20)
entry_contraseña = tk.Entry(root, show="*")
entry_contraseña.pack(pady=10)

btn_inicio_sesion = tk.Button(root, text="Iniciar sesión", command=verificar_usuario)
btn_inicio_sesion.pack(pady=20)

app = PuntoDeVenta()

root.mainloop()
