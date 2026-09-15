# ARMU — Integración Streamlit

## Estado

Streamlit está conectado al backend real de recomendaciones.

## Arquitectura

La aplicación Streamlit consume directamente la capa de
servicios Python porque frontend y backend viven actualmente
en el mismo repositorio y proceso.

Esto evita necesitar levantar un servidor FastAPI adicional
para la demo de Streamlit.

Los endpoints FastAPI siguen disponibles para futuros clientes
web o móviles.

## Flujo principal

1. El usuario selecciona gustos.
2. Define presupuesto.
3. Define número de personas.
4. Selecciona supermercado.
5. Selecciona restricciones.
6. Streamlit llama al recomendador.
7. Se muestran 7 recetas.
8. Se muestra el carrito estimado.
9. El usuario puede comparar una receta entre las 3 cadenas.

## Componentes

- app.py
- armu/streamlit_backend.py
- api/services/recommendation.py
- api/services/price_comparison.py
- api/services/options.py

## Ejecutar

Desde la raíz del proyecto:

    streamlit run app.py

## Pestañas

### Plan semanal

Usa el nuevo backend de ARMU.

### Carrito por ingredientes

Conserva el flujo original basado en NutriPlanMatcher.

## Importante

Los precios representan costos proporcionales a las cantidades
utilizadas en las recetas.

Las restricciones alimentarias actuales son heurísticas MVP
y no constituyen certificación médica.
