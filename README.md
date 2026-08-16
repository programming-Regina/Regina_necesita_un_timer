# Regina Necesita un Timer

Un timer de escritorio hecho en Python + Tkinter, diseñado para un problema muy concreto: el hiperfoco no sabe cuándo parar, y la procrastinación no sabe cuándo empezar.

La historia completa está en [mi posteo de LinkedIn](https://lnkd.in/p/d5JCRfPJ). Acá va la parte técnica, para quien esté aprendiendo a construir timers en Python.


<p align="center">
<img width="355" height="537" alt="timer" src="https://github.com/user-attachments/assets/33913cf4-bc6f-4fdd-ac54-7aef0bab058d" />
</p>

---

## ¿Qué hace?

Tiene dos modos de trabajo y un sistema de recordatorios de agua y postura que funciona de manera independiente.

### 1. Modo "Tiempo mínimo"

Fijás un mínimo de minutos de trabajo. Cuando se cumple, el timer no te obliga a parar: solo avisa "MÍNIMO CUMPLIDO — podés seguir si querés". La idea es eliminar la negociación mental de *¿trabajo cinco minutos más o hago otra cosa?*. Una vez que arrancaste, hay un mínimo concreto que cumplir; después, la decisión vuelve a ser tuya.

### 2. Modo "Ciclos"

Alterna bloques de trabajo y descanso un número determinado de veces. Es parecido al Pomodoro, pero configurable: elegís los minutos de trabajo, los minutos de descanso y la cantidad de ciclos. Ataca el problema inverso al anterior: no conseguir parar, en vez de no conseguir empezar. Cuando termina un bloque de trabajo arranca el descanso automáticamente, y viceversa.

### 3. Recordatorio de agua y postura

Corre de manera independiente del timer principal. Se configura para que aparezca cada tantos minutos, y el aviso ("HIDRATARSE · CORREGIR POSTURA") no toca el tiempo de trabajo ni de descanso: aparece, ocupa la etiqueta de estado cinco segundos, y desaparece.

Sigue funcionando aunque el timer principal ya haya terminado. Es a propósito: si el modo "Tiempo mínimo" termina y decidís seguir trabajando, podés entrar en hiperfoco exactamente igual que antes — el cuerpo no sabe que el timer terminó. El recordatorio se pausa cuando pausás el timer, y se desactiva poniendo el intervalo en `0`.

---

## Conceptos de Python que están en juego

### `time.monotonic()`, no `time.time()`

El timer no cuenta "ticks" asumiendo que cada llamada a `_tick()` representa exactamente 100 ms. En cada actualización calcula cuánto tiempo real transcurrió:

```python
now = time.monotonic()
elapsed = now - self.last_tick
self.last_tick = now
self.remaining -= elapsed
```

`after(100, ...)` de Tkinter no garantiza que pasen exactamente 100 ms entre una llamada y la siguiente — el sistema puede demorarse por carga de CPU u otra actividad del event loop. Si simplemente hiciéramos `self.remaining -= 0.1` en cada tick, el timer se iría atrasando con cualquier demora. Midiendo el tiempo real transcurrido, el cálculo no depende de cuántas veces consiguió ejecutarse el callback. Además, a diferencia de `time.time()`, `time.monotonic()` no retrocede ni se ve afectado por cambios en la hora del sistema — está pensado específicamente para medir intervalos.

### `after()` como loop no bloqueante

Tkinter trabaja con un event loop, y `self.after(100, self._tick)` significa "cuando pasen unos 100 ms, ejecutá `_tick()`". Al final de `_tick()` se programa la siguiente ejecución con la misma línea. No usamos `while True: ... time.sleep(0.1)` porque eso bloquearía el hilo principal y la interfaz dejaría de responder. Tampoco es recursión tradicional: cada ejecución del callback termina, y es Tkinter quien agenda la siguiente.

### Dos relojes independientes con `after()`

El timer principal y el recordatorio tienen mecanismos de actualización separados: `_tick()` para uno, `_reminder_tick()` para el otro, cada uno con sus propias variables de estado (`reminder_active`, `next_reminder`, `last_reminder_tick`, `reminder_job`). Por eso pueden desincronizarse a propósito: el timer puede terminar y el recordatorio seguir activo, o el timer puede estar pausado sin que el recordatorio lo esté. Es una forma simple de manejar dos procesos temporales dentro del mismo event loop sin threads.

### Máquina de estados básica

El modo "Ciclos" es una pequeña máquina de estados: fase (`work` / `rest`) más el número de ciclo actual. `_phase_finished()` concentra las transiciones:

```python
if self.phase == "work":
    self.phase = "rest"
else:
    if self.cycle_no >= self.cycles.get():
        ...  # se terminaron los ciclos
    else:
        self.cycle_no += 1
        self.phase = "work"
```

Pensarlo así evita que la lógica de fases termine siendo una maraña de `if` sueltos.

### Canvas y trigonometría básica

El dial se dibuja con `Canvas.create_arc()`. Primero se calcula qué fracción del tiempo queda, se convierte en grados y se dibuja el arco:

```python
frac = self.remaining / self.total_seconds
extent = 360 * frac
self.canvas.create_arc(..., start=90, extent=-extent, ...)
```

Las marcas alrededor del dial usan trigonometría básica para ubicar puntos sobre un círculo:

```python
ang = math.radians(i * 6 - 90)
x = cx + math.cos(ang) * r
y = cy + math.sin(ang) * r
```

`math.sin()`, `math.cos()` y `math.radians()` aplicados a una interfaz gráfica, sin vueltas.

---

## Una decisión de diseño

Tiempo mínimo y Ciclos parecen resolver lo mismo, pero no: el primero responde a "no consigo empezar" poniendo una barrera mínima sin decidir cuándo termino de trabajar; el segundo responde a "si empiezo, no sé cuándo parar" con límites externos de trabajo y descanso. El recordatorio de agua/postura ataca un tercer problema —"aunque esté trabajando bien, me puedo olvidar de que tengo un cuerpo"— y por eso no está atado al final del timer.

La idea de fondo: externalizar decisiones y señales que la atención suele perder de vista.

---

## Interfaz visual

El dial usa tres colores para el trabajo (verde con más de la mitad del tiempo, amarillo por debajo de la mitad, rojo sobre el final) y una paleta distinta para el descanso, para que el cambio de estado sea evidente de un vistazo. La ventana queda siempre por encima de las demás (`always on top`), pensada como referencia visual periférica sin tener que cambiar de aplicación.

El aviso de agua/postura usa contraste fuerte a propósito: cinco segundos de atención corporal, sin ventana emergente, sin pausar el trabajo ni tocar el tiempo del timer.

Y cuando termina un descanso aparece un monstruo bailando. No tiene ninguna justificación técnica. Es Mang.

---

## Valores predeterminados

```text
Tiempo mínimo: 25 minutos
Trabajo:       45 minutos
Descanso:      10 minutos
Ciclos:        3
Agua/postura:  cada 60 minutos
```

Son valores iniciales configurables, no una recomendación de productividad.

---

## Cómo correrlo

Requiere Windows y Python 3. Usa `tkinter` (parte de la instalación estándar en Windows) y `winsound` para los avisos sonoros.

```bash
python regina_timer_v03_2.py
```

O con un `.bat` de doble clic, para no dejar la consola abierta:

```bat
@echo off
start "" pythonw "%~dp0regina_timer_v03_2.py"
```

## Limitaciones

Pensado para Windows por `winsound`. La parte gráfica es Tkinter y podría portarse a otros sistemas, pero habría que reemplazar el sonido y revisar el comportamiento de la interfaz en cada plataforma. No tiene base de datos, cuentas, sincronización, estadísticas ni historial — a propósito.

---

## Por qué existe

Es un experimento chico alrededor de una pregunta real: ¿qué pasa cuando la atención no gestiona bien el tiempo? La respuesta no es necesariamente más disciplina. A veces es sacar ciertas decisiones de la cabeza y convertirlas en señales externas — para empezar, para parar, para descansar, para tomar agua, para corregir la postura. El objetivo no es controlar cuánto trabajás; es reducir lo que tenés que recordar mientras lo hacés.

## ¿Por qué "Regina Timer"?

Porque lo hice para mí. Y porque, después de años trabajando con tecnología, terminé programando una aplicación para que me recuerde tomar agua. La informática alcanzó un nuevo nivel de sofisticación. 😅

---

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Perfil-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/regina-molares/)
