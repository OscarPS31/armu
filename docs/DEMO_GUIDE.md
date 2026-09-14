# ARMU — Guía de Demo MVP

## Objetivo

Mostrar el flujo completo del backend ARMU en una sola ejecución.

La demo enseña:

- opciones disponibles
- preferencias del usuario
- menú semanal
- carrito y costo
- comparación entre supermercados

## Demo estándar

Desde la raíz del proyecto:

    python scripts/demo_mvp.py

Configuración por defecto:

- Walmart
- 2 personas
- presupuesto de 1200 MXN
- gustos: chicken vegetables
- sin restricciones alimentarias

## Demo vegetariana

    python scripts/demo_mvp.py --gustos "vegetables beans" --presupuesto 1000 --cadena Walmart --restriccion vegetariano

## Demo vegana

    python scripts/demo_mvp.py --gustos "beans vegetables" --presupuesto 1000 --cadena Chedraui --restriccion vegano

## Demo vegana y sin gluten

    python scripts/demo_mvp.py --gustos "beans vegetables" --presupuesto 1000 --cadena Chedraui --restriccion vegano --restriccion sin_gluten

## Cambiar número de personas

    python scripts/demo_mvp.py --personas 4

## Obtener salida JSON

    python scripts/demo_mvp.py --json

Esto es útil para revisar el contrato que consumiría un frontend.

## Flujo mostrado

1. GET /opciones
2. POST /recomendacion
3. Mostrar menú semanal
4. Mostrar carrito
5. Tomar la primera receta
6. GET /comparar-precios/{id_receta}
7. Mostrar supermercado más barato y ahorro

## Nota importante

Los precios representan costos proporcionales de los
ingredientes usados por las recetas.

No representan necesariamente el costo completo de comprar
todos los paquetes comerciales en tienda.

Las restricciones alimentarias actuales son heurísticas MVP
y no constituyen certificación para alergias o celiaquía.

## Comando recomendado para presentación

    python scripts/demo_mvp.py

Antes de presentar:

    python -m pytest -q

La demo debe ejecutarse desde la raíz del repositorio ARMU.
